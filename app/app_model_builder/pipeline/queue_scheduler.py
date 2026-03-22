import json
import logging
import threading
import time
from datetime import datetime, timezone

from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import ActivityRepository, ModelRepository, QueueRepository

logger = logging.getLogger("app.queue_scheduler")

POLL_INTERVAL = 10  # seconds


def _process_queue_item(item) -> None:
    """Process a single queue item — create model record, request, version."""
    session = SessionLocal()
    try:
        repo = ModelRepository(session)
        videos = json.loads(item.selected_videos or "[]")

        record = repo.create_model(
            model_name=item.model_name,
            approach_type=item.approach_type,
            user_id=item.user_id,
            input_criteria={"video_count": len(videos), "context_data": json.loads(item.context_data or "{}")},
        )

        resources = []
        for video in videos:
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

        repo.create_request(model_id=record.id, resources=resources)
        repo.create_version(
            model_id=record.id,
            version=record.latest_version,
            input_criteria={"video_count": len(videos)},
            model_location="",
        )

        logger.info(f"Queue item #{item.id} processed — model '{item.model_name}' created (id={record.id})")
    finally:
        session.close()


def _scheduler_loop() -> None:
    """Background loop: pick pending items one at a time and process them."""
    logger.info("Queue scheduler started (poll every %ds)", POLL_INTERVAL)
    while True:
        try:
            session = SessionLocal()
            try:
                q_repo = QueueRepository(session)
                item = q_repo.pick_next_pending()
                if item:
                    logger.info(f"Processing queue item #{item.id}: '{item.model_name}'")
                    try:
                        _process_queue_item(item)
                        q_repo.mark_completed(item.id)
                        # Log activity
                        ActivityRepository(session).add(
                            name=f"Model '{item.model_name}' built from queue (#{item.id})",
                            status="success",
                        )
                        logger.info(f"Queue item #{item.id} completed")
                    except Exception as e:
                        logger.error(f"Queue item #{item.id} failed: {e}")
                        q_repo.mark_failed(item.id, str(e))
                        ActivityRepository(session).add(
                            name=f"Model '{item.model_name}' build failed (#{item.id}): {e}",
                            status="error",
                        )
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Queue scheduler error: {e}")

        time.sleep(POLL_INTERVAL)


def start_scheduler() -> None:
    """Start the queue scheduler in a daemon thread."""
    t = threading.Thread(target=_scheduler_loop, daemon=True, name="queue-scheduler")
    t.start()
    logger.info("Queue scheduler thread started")
