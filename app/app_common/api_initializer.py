"""
api_initializer.py
==================
Discovers and initialises all API modules listed in apis.json.
Each module must expose an Initializer class with an initialize(dto) method.
"""
from __future__ import annotations

import importlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.app_common.dtos.init_dtos import InitDTO

logger = logging.getLogger(__name__)


class APIInitializer:
    """
    Reads apis.json and calls Initializer().initialize(dto) on each module.

    Contract for every module listed in apis.json
    ----------------------------------------------
    The module must define a class named `Initializer` that has an
    `initialize(self, dto: InitDTO) -> None` method.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(__file__).resolve().parents[1] / "apis.json"

    def load_api_config(self) -> Dict[str, Any]:
        with self.config_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def initialize_apis(self, dto: InitDTO) -> None:
        config = self.load_api_config()
        api_modules: List[str] = config.get("apis", [])
        logger.info("Initializing %d API modules", len(api_modules))

        for module_name in api_modules:
            t0 = time.time()
            module = importlib.import_module(module_name)

            initializer_cls = getattr(module, "Initializer", None)
            if initializer_cls is None:
                raise AttributeError(
                    f"Module '{module_name}' does not define an Initializer class."
                )

            initializer_cls().initialize(dto)
            logger.info("  ✓ %s initialized in %.3fs", module_name, time.time() - t0)

        logger.info("All API modules initialized")
