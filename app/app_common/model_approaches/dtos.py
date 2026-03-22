from dataclasses import dataclass, field
from typing import Any, Dict, Optional


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
