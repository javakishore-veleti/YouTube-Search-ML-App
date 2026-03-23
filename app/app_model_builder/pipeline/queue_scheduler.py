"""
queue_scheduler.py — polls build queue and processes pending items one at a time.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from app.app_common.app_status import get_status, set_status
from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import (
    ActivityRepository, ModelRepository, QueueRepository, WorkflowRepository,
)
from app.app_model_approaches import get_facade
from app.app_common.model_approaches.dtos import ModelBuildRequest

logger = logging.getLogger(__name__)


class QueueScheduler:
    """Singleton background scheduler that processes the model build queue."""

    POLL_INTERVAL = 10

    _instance: Optional["QueueScheduler"] = None
    _initialised: bool = False

    def __new__(cls) -> "QueueScheduler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        self._thread: Optional[threading.Thread] = None

    @classmethod
    def instance(cls) -> "QueueScheduler":
        return cls()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="queue-scheduler")
        self._thread.start()
        logger.info("Queue scheduler thread started")

    def _loop(self) -> None:
        logger.info("Queue scheduler started (poll every %ds)", self.POLL_INTERVAL)
        while True:
            try:
                self._tick()
            except Exception as e:
                logger.error("Queue scheduler error: %s", e)
            time.sleep(self.POLL_INTERVAL)

    def _tick(self) -> None:
        session = SessionLocal()
        try:
            q_repo = QueueRepository(session)
            item = q_repo.pick_next_pending()
            if not item:
                return

            logger.info("Processing queue item #%d: '%s'", item.id, item.model_name)
            try:
                self._process(item)
                q_repo.mark_completed(item.id)
                ActivityRepository(session).add(
                    name=f"Model '{item.model_name}' built from queue (#{item.id})",
                    status="success",
                )
                set_status("models_built", get_status().get("models_built", 0) + 1)
                set_status("last_build", datetime.now(timezone.utc).isoformat())
                logger.info("Queue item #%d completed", item.id)
            except Exception as e:
                logger.error("Queue item #%d failed: %s", item.id, e)
                q_repo.mark_failed(item.id, str(e))
                ActivityRepository(session).add(
                    name=f"Model '{item.model_name}' build failed (#{item.id}): {e}",
                    status="error",
                )
        finally:
            session.close()

    def _process(self, item) -> None:
        """
        1. Create the model + request + version records.
        2. Call the approach facade (which runs the workflow + writes WF/task rows).
        3. Update model record with real model_location and output_results.
        """
        session = SessionLocal()
        try:
            repo   = ModelRepository(session)
            videos = json.loads(item.selected_videos or "[]")
            sub_models = json.loads(item.selected_sub_models or "[]")

            # ── Create model record ───────────────────────────────────────
            record = repo.create_model(
                model_name=item.model_name,
                approach_type=item.approach_type,
                user_id=item.user_id,
                input_criteria={
                    "video_count":      len(videos),
                    "selected_sub_models": sub_models,
                },
            )

            # ── Store video resources ─────────────────────────────────────
            resources = [
                {
                    "resource_type":    "youtube",
                    "resource_type_id": v.get("video_id", ""),
                    "metadata": {
                        "url":         f"https://www.youtube.com/watch?v={v.get('video_id', '')}",
                        "title":       v.get("title", ""),
                        "channel":     v.get("channel", ""),
                        "thumbnail":   v.get("thumbnail", ""),
                        "description": v.get("description", ""),
                    },
                }
                for v in videos
            ]
            repo.create_request(model_id=record.id, resources=resources)

            # ── Initial version placeholder ───────────────────────────────
            version_row = repo.create_version(
                model_id=record.id,
                version=record.latest_version,
                input_criteria={"video_count": len(videos), "selected_sub_models": sub_models},
                model_location="",
            )

            # capture scalar IDs before closing the session
            record_id = record.id
            version_row_id = version_row.id

            session.close()
            session = None   # closed

            # ── Run the approach facade (workflow + WF rows) ──────────────
            facade = get_facade(item.approach_type)
            if facade is None:
                raise ValueError(f"No facade found for approach '{item.approach_type}'")

            req = ModelBuildRequest(
                model_name=item.model_name,
                approach_type=item.approach_type,
                publish_as_latest=item.publish_as_latest,
                input_criteria={
                    "video_ids":         [v.get("video_id", "") for v in videos],
                    "base_model_key":    sub_models[0] if sub_models else None,
                    "model_id":          record_id,
                    "queue_item_id":     item.id,
                },
            )

            response = facade.build_model(req)
            logger.info("[Scheduler] Facade response: status=%s location=%s",
                        response.status, response.model_location)

            # ── Persist final model location + output results ─────────────
            s2 = SessionLocal()
            try:
                from app.app_common.database.db_models import ModelVersion
                r2 = ModelRepository(s2)
                r2.update_model(
                    model_id=record_id,
                    output_results=response.output_results or {},
                )
                # update the version row with real path
                ver = s2.query(ModelVersion).filter_by(id=version_row_id).first()
                if ver and response.model_location:
                    ver.model_location = response.model_location
                    ver.storage_type   = "local"
                    ver.storage_path   = response.model_location
                    s2.commit()
                # link wf back to model if wf_id was returned in output
                wf_id = (response.output_results or {}).get("wf_id") or None
                if wf_id:
                    WorkflowRepository(s2).link_wf_model(wf_id, record_id)
            finally:
                s2.close()

            logger.info(
                "[Scheduler] Queue item #%d processed — model '%s' id=%d",
                item.id, item.model_name, record_id,
            )

        finally:
            if session:
                session.close()


def start_scheduler() -> None:
    QueueScheduler.instance().start()
