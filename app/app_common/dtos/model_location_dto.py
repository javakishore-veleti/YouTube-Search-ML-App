from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ModelStorageType(str, Enum):
    LOCAL = "local"
    S3 = "s3"
    FTP = "ftp"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    MLFLOW = "mlflow"
    UNKNOWN = "unknown"


@dataclass
class ModelLocationDTO:
    storage_type: ModelStorageType = ModelStorageType.UNKNOWN
    uri: Optional[str] = None
    bucket: Optional[str] = None
    path: Optional[str] = None
    exists: bool = False
    extra: dict = field(default_factory=dict)
