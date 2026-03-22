import importlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.app_common.dtos.init_dtos import InitDTO

logger = logging.getLogger("app.api_initializer")


class APIInitializer:
    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "apis.json"

    def load_api_config(self) -> Dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    def initialize_apis(self, dto: InitDTO) -> None:
        config = self.load_api_config()
        api_modules: List[str] = config.get("apis", [])
        logger.info(f"Initializing {len(api_modules)} API modules")

        for module_name in api_modules:
            t0 = time.time()
            module = importlib.import_module(module_name)
            initialize_fn = getattr(module, "initialize", None)
            if initialize_fn is None:
                raise AttributeError(
                    f"Module '{module_name}' does not define initialize(dto)."
                )
            initialize_fn(dto)
            logger.info(f"  ✓ {module_name} initialized in {time.time()-t0:.3f}s")

        logger.info("All API modules initialized")
