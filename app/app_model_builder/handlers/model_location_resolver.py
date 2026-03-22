import os
from pathlib import Path
from typing import List, Optional

from app.app_common.dtos.model_location_dto import ModelLocationDTO, ModelStorageType


class ModelLocationResolver:
    """
    Resolves the model file location from various storage backends:
    local filesystem, S3, FTP, Azure Blob, GCS, or MLflow.
    The storage type is detected from the URI scheme or an explicit override.
    """

    _SCHEME_MAP = {
        "s3://": ModelStorageType.S3,
        "ftp://": ModelStorageType.FTP,
        "ftps://": ModelStorageType.FTP,
        "https://": ModelStorageType.AZURE_BLOB,
        "az://": ModelStorageType.AZURE_BLOB,
        "abfs://": ModelStorageType.AZURE_BLOB,
        "gs://": ModelStorageType.GCS,
        "mlflow://": ModelStorageType.MLFLOW,
        "runs:/": ModelStorageType.MLFLOW,
        "models:/": ModelStorageType.MLFLOW,
    }

    DEFAULT_LOCAL_PATH = os.path.join(
        os.path.expanduser("~"),
        "runtime_data", "ml_models", "YouTube-Search-Model", "Releases", "latest"
    )

    def __init__(self, model_uri: Optional[str] = None) -> None:
        self.model_uri = model_uri or os.environ.get("MODEL_URI") or self.DEFAULT_LOCAL_PATH

    def resolve(self) -> ModelLocationDTO:
        if not self.model_uri:
            return ModelLocationDTO(
                storage_type=ModelStorageType.UNKNOWN,
                exists=False,
            )

        storage_type = self._detect_storage_type(self.model_uri)

        if storage_type == ModelStorageType.LOCAL:
            return self._resolve_local(self.model_uri)

        if storage_type == ModelStorageType.S3:
            bucket, path = self._parse_s3_uri(self.model_uri)
            return ModelLocationDTO(
                storage_type=storage_type,
                uri=self.model_uri,
                bucket=bucket,
                path=path,
                exists=True,  # existence check requires boto3; assume present if URI configured
            )

        if storage_type == ModelStorageType.MLFLOW:
            return ModelLocationDTO(
                storage_type=storage_type,
                uri=self.model_uri,
                path=self.model_uri,
                exists=True,
                extra={"tracking_uri": os.environ.get("MLFLOW_TRACKING_URI", "not set")},
            )

        # Azure Blob, GCS, FTP — return URI as-is; deep existence checks require SDK clients
        return ModelLocationDTO(
            storage_type=storage_type,
            uri=self.model_uri,
            path=self.model_uri,
            exists=True,
        )

    def _resolve_local(self, latest_path: str) -> ModelLocationDTO:
        latest = Path(latest_path)
        releases_dir = latest.parent  # .../Releases
        available_versions = self._list_available_versions(releases_dir)
        latest_exists = latest.exists()

        if not latest_exists:
            return ModelLocationDTO(
                storage_type=ModelStorageType.LOCAL,
                uri=latest_path,
                path=latest_path,
                exists=False,
                extra={
                    "message": "No latest model found.",
                    "available_versions": available_versions,
                    "available_version_count": len(available_versions),
                },
            )

        return ModelLocationDTO(
            storage_type=ModelStorageType.LOCAL,
            uri=latest_path,
            path=latest_path,
            exists=True,
            extra={
                "message": "Latest model found.",
                "available_versions": available_versions,
                "available_version_count": len(available_versions),
            },
        )

    @staticmethod
    def _list_available_versions(releases_dir: Path) -> List[str]:
        if not releases_dir.exists() or not releases_dir.is_dir():
            return []
        versions = sorted(
            [
                entry.name
                for entry in releases_dir.iterdir()
                if entry.is_dir() and entry.name != "latest"
            ],
            reverse=True,
        )
        return versions[:10]

    def _detect_storage_type(self, uri: str) -> ModelStorageType:
        for scheme, storage_type in self._SCHEME_MAP.items():
            if uri.startswith(scheme):
                return storage_type
        return ModelStorageType.LOCAL

    @staticmethod
    def _parse_s3_uri(uri: str):
        # s3://bucket-name/path/to/model
        without_scheme = uri[len("s3://"):]
        parts = without_scheme.split("/", 1)
        bucket = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        return bucket, path
