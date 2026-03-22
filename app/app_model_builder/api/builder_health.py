import os
from datetime import datetime
from typing import Optional

from app.app_common.dtos.init_dtos import InitDTO
from app.app_model_builder.handlers.model_location_resolver import ModelLocationResolver


class BuilderHealth:
    """
    Provides health status of the model builder pipeline:
    - Whether the model is currently running
    - Last run timestamp
    - Resolved model file location (local, S3, FTP, Azure Blob, GCS, MLflow)
    """

    def __init__(self) -> None:
        self._last_run: Optional[datetime] = None
        self._is_running: bool = False

    def set_last_run(self, timestamp: datetime) -> None:
        self._last_run = timestamp

    def set_running(self, running: bool) -> None:
        self._is_running = running

    def health(self) -> dict:
        resolver = ModelLocationResolver(
            model_uri=os.environ.get("MODEL_URI")
        )
        location = resolver.resolve()

        return {
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


def initialize(dto: InitDTO) -> None:
    handler = BuilderHealth()
    dto.app.add_api_route(
        "/builder/health",
        endpoint=handler.health,
        methods=["GET"],
    )
