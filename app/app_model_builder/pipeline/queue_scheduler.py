"""
queue_scheduler.py
==================
QueueScheduler runs a background daemon thread that polls the build queue
and processes pending items one at a time.  All logic is encapsulated in
the class; call QueueScheduler.instance().start() once at app startup.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from typing import Optional

from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import ActivityRepository, ModelRepository, QueueRepository

logger = logging.getLogger(__name__)


class QueueScheduler:
    """
    Singleton background scheduler that processes the model build queue.

    Usage
    -----
      QueueScheduler.instance().start()
    """

    POLL_INTERVAL = 10   # seconds between queue polls

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

    # ── Public API ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the daemon thread.  Safe to call multiple times — starts only once."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="queue-scheduler"
        )
        self._thread.start()
        logger.info("Queue scheduler thread started")

    # ── Private loop ─────────────────────────────────────────────────────────

    def _loop(self) -> None:
        logger.info("Queue scheduler started (poll every %ds)", self.POLL_INTERVAL)
        while True:
            try:
                self._tick()
            except Exception as e:
                logger.error("Queue scheduler error: %s", e)
            time.sleep(self.POLL_INTERVAL)

    def _tick(self) -> None:
        """Pick one pending queue item and process it."""
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
        """Create the model record, request, and version for a queue item."""
        session = SessionLocal()
        try:
            repo   = ModelRepository(session)
            videos = json.loads(item.selected_videos or "[]")

            record = repo.create_model(
                model_name=item.model_name,
                approach_type=item.approach_type,
                user_id=item.user_id,
                input_criteria={
                    "video_count":  len(videos),
                    "context_data": json.loads(item.context_data or "{}"),
                },
            )

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
            repo.create_version(
                model_id=record.id,
                version=record.latest_version,
                input_criteria={"video_count": len(videos)},
                model_location="",
            )
            logger.info(
                "Queue item #%d processed — model '%s' created (id=%d)",
                item.id, item.model_name, record.id,
            )
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Module-level shim — existing call site in main.py stays unchanged.
# ---------------------------------------------------------------------------
def start_scheduler() -> None:
    QueueScheduler.instance().start()
