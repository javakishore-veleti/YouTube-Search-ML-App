import json
import logging

from fastapi import Request

from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import QueueRepository
from app.app_common.dtos.init_dtos import InitDTO

logger = logging.getLogger(__name__)


class QueueAPI:
    """Endpoints for the model build queue."""

    def list_queue(self, request: Request) -> dict:
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        status_filter = request.query_params.get("status") or None
        page_size = max(1, min(page_size, 100))
        page = max(1, page)

        session = SessionLocal()
        try:
            return QueueRepository(session).list_paginated(page=page, page_size=page_size, status_filter=status_filter)
        finally:
            session.close()

    def get_queue_item(self, request: Request) -> dict:
        item_id = int(request.path_params["id"])
        session = SessionLocal()
        try:
            repo = QueueRepository(session)
            item = repo.get_by_id(item_id)
            if not item:
                return {"error": "Not found"}
            return item.to_dict()
        finally:
            session.close()

    async def submit_to_queue(self, request: Request) -> dict:
        body = await request.json()
        model_name = body.get("model_name", "")
        approach_type = body.get("approach_type", "")
        selected_videos = body.get("selected_videos", [])
        selected_sub_models = body.get("selected_sub_models", [])
        notes = body.get("notes", "")
        context_data = body.get("context_data", "{}")
        publish_as_latest = body.get("publish_as_latest", False)
        user_id = body.get("user_id", "default")

        if not model_name or not approach_type:
            return {"status": "error", "message": "model_name and approach_type are required."}
        if not selected_videos or len(selected_videos) > 25:
            return {"status": "error", "message": "Select between 1 and 25 videos."}

        # Always normalize sub-models to list for backend simplicity
        if selected_sub_models is None:
            selected_sub_models = []
        elif not isinstance(selected_sub_models, list):
            selected_sub_models = [selected_sub_models]

        # Validate context_data is valid JSON
        if isinstance(context_data, str):
            try:
                json.loads(context_data)
            except json.JSONDecodeError:
                context_data = "{}"
        else:
            context_data = json.dumps(context_data)

        logger.info(f"Queuing build: model='{model_name}' approach={approach_type} videos={len(selected_videos)} sub_models={selected_sub_models}")

        session = SessionLocal()
        try:
            repo = QueueRepository(session)
            item = repo.enqueue(
                model_name=model_name,
                approach_type=approach_type,
                selected_videos=selected_videos,
                selected_sub_models=selected_sub_models,
                notes=notes,
                context_data=context_data,
                publish_as_latest=publish_as_latest,
                user_id=user_id,
            )
            return {"status": "queued", "queue_item": item.to_dict()}
        finally:
            session.close()


class Initializer:
    def initialize(self, dto: InitDTO) -> None:
        handler = QueueAPI()
        app = dto.app
        app.add_api_route("/admin/queue", endpoint=handler.list_queue, methods=["GET"])
        app.add_api_route("/admin/queue/submit", endpoint=handler.submit_to_queue, methods=["POST"])
        app.add_api_route("/admin/queue/{id}", endpoint=handler.get_queue_item, methods=["GET"])
