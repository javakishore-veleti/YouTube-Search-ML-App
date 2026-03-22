import logging
import os
import time
from datetime import datetime
from typing import Optional

from app.app_common.dtos.init_dtos import InitDTO
from app.app_model_builder.handlers.model_location_resolver import ModelLocationResolver

logger = logging.getLogger(__name__)
_CACHE_TTL = 30  # seconds


class BuilderHealth:

    def __init__(self) -> None:
        logger.info("BuilderHealth.__init__ start")
        t0 = time.time()
        self._last_run: Optional[datetime] = None
        self._is_running: bool = False
        self._cached_response: Optional[dict] = None
        self._cache_time: float = 0
        self._warm_cache()
        logger.info(f"BuilderHealth.__init__ done in {time.time()-t0:.3f}s")

    def set_last_run(self, timestamp: datetime) -> None:
        self._last_run = timestamp
        self._cached_response = None  # invalidate cache

    def set_running(self, running: bool) -> None:
        self._is_running = running
        self._cached_response = None

    def health(self) -> dict:
        now = time.time()
        if self._cached_response and (now - self._cache_time) < _CACHE_TTL:
            return self._cached_response
        return self._warm_cache()

    def _warm_cache(self) -> dict:
        resolver = ModelLocationResolver(
            model_uri=os.environ.get("MODEL_URI")
        )
        location = resolver.resolve()

        self._cached_response = {
            "status": "running" if self._is_running else "idle",
            "is_running": self._is_running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "model_location": {
                "storage_type": location.storage_type.value,
                "uri": location.uri,
                "bucket": location.bucket,
                "path": location.path,
                "exists": location.exists,
                "extra": location.extra,
            },
        }
        self._cache_time = time.time()
        return self._cached_response


class Initializer:
    def initialize(self, dto: InitDTO) -> None:
        handler = BuilderHealth()
        dto.app.add_api_route("/builder/health", endpoint=handler.health, methods=["GET"])
