from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelBuildRequest:
    model_name: str
    approach_type: str
    input_criteria: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "default"
    publish_as_latest: bool = False
    ctx_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelBuildResponse:
    model_id: Optional[int] = None
    model_name: str = ""
    version: str = ""
    status: str = ""
    approach_type: str = ""
    output_results: Dict[str, Any] = field(default_factory=dict)
    model_location: Optional[str] = None
    ctx_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationSearchRequest:
    query: str
    model_location: str
    transformed_parquet: str
    embeddings_path: str
    base_model_id: str
    embedding_dim: int = 384
    dist_name: str = "manhattan"
    threshold: float = 40.0
    top_k: int = 5


@dataclass
class ConversationSearchResponse:
    results: List[Dict[str, Any]] = field(default_factory=list)
    query: str = ""
    status: str = "ok"
