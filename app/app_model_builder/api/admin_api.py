import logging
import os
import time

from fastapi import Request

from app.app_common.app_status import get_status, set_status
from app.app_common.cache.model_cache import ModelListCache
from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import ActivityRepository, ModelRepository
from app.app_common.dtos.init_dtos import InitDTO
from app.app_integrators.youtube.yt_client import YouTubeClient
from app.app_model_approaches import load_approaches

logger = logging.getLogger("app.admin_api")


class AdminAPI:
    """Admin endpoints for model building, approach listing, and key validation."""

    def __init__(self) -> None:
        logger.info("AdminAPI.__init__ start")
        t0 = time.time()
        self.yt_client = YouTubeClient()
        self.model_cache = ModelListCache()
        key = os.environ.get("YOUTUBE_API_KEY", "")
        set_status("api_key_configured", bool(key) and key != "your_youtube_api_key_here")
        self._log_activity("Application started", "success")
        logger.info(f"AdminAPI.__init__ done in {time.time()-t0:.3f}s")

    def _log_activity(self, name: str, status: str = "info") -> None:
        try:
            session = SessionLocal()
            try:
                ActivityRepository(session).add(name=name, status=status)
            finally:
                session.close()
        except Exception:
            pass  # table may not exist on very first run

    def app_status(self) -> dict:
        logger.debug("app_status called")
        return get_status()

    def dashboard(self, request: Request) -> dict:
        t0 = time.time()
        logger.debug("dashboard called")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        page_size = max(1, min(page_size, 100))
        page = max(1, page)

        status = get_status()
        logger.debug(f"dashboard: got status in {time.time()-t0:.3f}s")
        try:
            session = SessionLocal()
            try:
                activities = ActivityRepository(session).list_paginated(page=page, page_size=page_size)
            finally:
                session.close()
        except Exception:
            activities = {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}
        logger.debug(f"dashboard: total {time.time()-t0:.3f}s")

        return {"status": status, "activities": activities}

    def list_activities(self, request: Request) -> dict:
        """Server-side paginated activity list — safe for 100K+ rows."""
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        # Clamp page_size to prevent abuse
        page_size = max(1, min(page_size, 100))
        page = max(1, page)

        try:
            session = SessionLocal()
            try:
                return ActivityRepository(session).list_paginated(page=page, page_size=page_size)
            finally:
                session.close()
        except Exception:
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 1}

    def api_key_status(self) -> dict:
        """Check whether YOUTUBE_API_KEY is configured in .env on the server."""
        key = os.environ.get("YOUTUBE_API_KEY", "")
        configured = bool(key) and key != "your_youtube_api_key_here"
        return {
            "configured": configured,
            "message": "API key is configured on the server." if configured
                       else "API key is NOT configured. Set YOUTUBE_API_KEY in .env on the server.",
        }

    def validate_key(self) -> dict:
        """Validate the YOUTUBE_API_KEY from .env against YouTube Data API."""
        result = self.yt_client.validate_api_key()
        return result

    def list_approaches(self) -> list:
        logger.debug("list_approaches called")
        return load_approaches()

    def list_models(self) -> list:
        session = SessionLocal()
        try:
            repo = ModelRepository(session)
            records = repo.list_models()
            return [r.to_dict() for r in records]
        finally:
            session.close()

    async def create_model(self, request: Request) -> dict:
        body = await request.json()
        model_name = body.get("model_name", "")
        approach_type = body.get("approach_type", "")
        input_criteria = body.get("input_criteria", {})
        user_id = body.get("user_id", "default")
        publish_as_latest = body.get("publish_as_latest", False)

        if not model_name or not approach_type:
            return {"status": "error", "message": "model_name and approach_type are required."}

        session = SessionLocal()
        try:
            repo = ModelRepository(session)
            record = repo.create_model(
                model_name=model_name,
                approach_type=approach_type,
                user_id=user_id,
                input_criteria=input_criteria,
            )

            # Create initial version
            repo.create_version(
                model_id=record.id,
                version=record.latest_version,
                input_criteria=input_criteria,
                model_location="",
            )

            # Invalidate cache so /models picks up new entry
            self.model_cache.invalidate()

            return {
                "status": "created",
                "model": record.to_dict(),
                "publish_as_latest": publish_as_latest,
            }
        finally:
            session.close()

    def get_model_versions(self, request: Request) -> list:
        model_id = int(request.path_params["model_id"])
        session = SessionLocal()
        try:
            repo = ModelRepository(session)
            versions = repo.get_versions(model_id)
            return [v.to_dict() for v in versions]
        finally:
            session.close()

    async def search_videos(self, request: Request) -> dict:
        """Search YouTube videos with optional date range, channel, and tags."""
        t0 = time.time()
        body = await request.json()
        query = body.get("query", "")
        max_results = min(int(body.get("max_results", 50)), 50)
        published_after = body.get("published_after")
        published_before = body.get("published_before")
        channel_id = body.get("channel_id", "")
        tags = body.get("tags", "")

        logger.info(f"search_videos: query='{query}' max={max_results} after={published_after} before={published_before} channel={channel_id} tags='{tags}'")

        if not query and not tags:
            logger.info("search_videos: empty query, returning 0 results")
            return {"videos": [], "total": 0}

        search_query = query
        if tags:
            search_query = f"{query} {tags}".strip()

        try:
            t1 = time.time()
            logger.info(f"search_videos: calling YouTube API with query='{search_query}'")
            videos = self.yt_client.get_videos(
                query=search_query,
                max_results=max_results,
                published_after=published_after,
                published_before=published_before,
                channel_id=channel_id if channel_id else None,
            )
            t2 = time.time()
            logger.info(f"search_videos: YouTube API returned {len(videos)} results in {t2-t1:.3f}s (total {t2-t0:.3f}s)")
            return {"videos": videos, "total": len(videos)}
        except Exception as e:
            logger.error(f"search_videos: error after {time.time()-t0:.3f}s — {e}")
            return {"videos": [], "total": 0, "error": str(e)}

    async def submit_build_request(self, request: Request) -> dict:
        """Submit a model build request with selected YouTube video resources."""
        body = await request.json()
        model_name = body.get("model_name", "")
        approach_type = body.get("approach_type", "")
        selected_videos = body.get("selected_videos", [])
        user_id = body.get("user_id", "default")
        publish_as_latest = body.get("publish_as_latest", False)

        if not model_name or not approach_type:
            return {"status": "error", "message": "model_name and approach_type are required."}
        if not selected_videos or len(selected_videos) > 25:
            return {"status": "error", "message": "Select between 1 and 25 videos."}

        session = SessionLocal()
        try:
            repo = ModelRepository(session)

            # Create or reuse model record
            record = repo.create_model(
                model_name=model_name,
                approach_type=approach_type,
                user_id=user_id,
                input_criteria={"video_count": len(selected_videos)},
            )

            # Build resource list
            resources = []
            for video in selected_videos:
                resources.append({
                    "resource_type": "youtube",
                    "resource_type_id": video.get("video_id", ""),
                    "metadata": {
                        "url": f"https://www.youtube.com/watch?v={video.get('video_id', '')}",
                        "title": video.get("title", ""),
                        "channel": video.get("channel", ""),
                        "thumbnail": video.get("thumbnail", ""),
                        "description": video.get("description", ""),
                    },
                })

            # Create model request with resources
            model_request = repo.create_request(
                model_id=record.id,
                resources=resources,
            )

            # Create initial version
            repo.create_version(
                model_id=record.id,
                version=record.latest_version,
                input_criteria={"video_count": len(selected_videos)},
                model_location="",
            )

            self.model_cache.invalidate()
            self._log_activity(f"Model '{model_name}' created ({approach_type}, {len(selected_videos)} videos)", "success")

            return {
                "status": "created",
                "model": record.to_dict(),
                "request": model_request.to_dict(),
                "publish_as_latest": publish_as_latest,
            }
        finally:
            session.close()


def initialize(dto: InitDTO) -> None:
    handler = AdminAPI()
    app = dto.app

    app.add_api_route("/admin/dashboard", endpoint=handler.dashboard, methods=["GET"])
    app.add_api_route("/admin/status", endpoint=handler.app_status, methods=["GET"])
    app.add_api_route("/admin/activities", endpoint=handler.list_activities, methods=["GET"])
    app.add_api_route("/admin/api-key/status", endpoint=handler.api_key_status, methods=["GET"])
    app.add_api_route("/admin/api-key/validate", endpoint=handler.validate_key, methods=["GET"])
    app.add_api_route("/admin/approaches", endpoint=handler.list_approaches, methods=["GET"])
    app.add_api_route("/admin/models", endpoint=handler.list_models, methods=["GET"])
    app.add_api_route("/admin/models/build", endpoint=handler.create_model, methods=["POST"])
    app.add_api_route("/admin/models/build-request", endpoint=handler.submit_build_request, methods=["POST"])
    app.add_api_route("/admin/models/{model_id}/versions", endpoint=handler.get_model_versions, methods=["GET"])
    app.add_api_route("/admin/videos/search", endpoint=handler.search_videos, methods=["POST"])
