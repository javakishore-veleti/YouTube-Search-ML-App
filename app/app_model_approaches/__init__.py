import importlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.app_common.model_approaches.interfaces import IModelApproach


def load_approaches() -> List[Dict[str, Any]]:
    config_path = Path(__file__).with_name("approaches.json")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_facade(approach_id: str) -> Optional[IModelApproach]:
    approaches = load_approaches()
    match = next((a for a in approaches if a["id"] == approach_id), None)
    if not match:
        return None
    pkg = match["package"]
    module = importlib.import_module(f"app.app_model_approaches.{pkg}.facade")
    facade_cls = getattr(module, "Facade")
    return facade_cls()
