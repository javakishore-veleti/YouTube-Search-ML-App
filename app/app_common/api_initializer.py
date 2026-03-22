import importlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.app_common.dtos.init_dtos import InitDTO


class APIInitializer:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "apis.json"

    def load_api_config(self) -> Dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    def initialize_apis(self, dto: InitDTO) -> None:
        config = self.load_api_config()
        api_modules: List[str] = config.get("apis", [])

        for module_name in api_modules:
            module = importlib.import_module(module_name)
            initialize_fn = getattr(module, "initialize", None)
            if initialize_fn is None:
                raise AttributeError(
                    f"Module '{module_name}' does not define initialize(dto)."
                )
            initialize_fn(dto)
