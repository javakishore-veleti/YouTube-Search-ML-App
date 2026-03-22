"""
Approach 01 – Workflow
======================
Orchestrates the 7 Tasks in sequence, passing a shared context bag between them.
Implements IModelWorkflow and is a stateless singleton.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.app_common.model_approaches.dtos import ModelBuildRequest
from app.app_common.model_approaches.interfaces import IModelWorkflow
from app.app_model_approaches.approach_01.tasks import (
    Task01ExtractVideoIds,
    Task02FetchVideoData,
    Task03BuildDataFrame,
    Task04SaveRawParquet,
    Task05TransformData,
    Task06BuildEmbeddings,
    Task07SaveModel,
)

logger = logging.getLogger(__name__)


class BuildEmbeddingModelWorkflow(IModelWorkflow):
    """
    Runs all 7 pipeline tasks in order:
      Task01 → Task02 → Task03 → Task04 → Task05 → Task06 → Task07
    Stateless singleton – all state lives in the ctx dict.
    """

    _instance: "BuildEmbeddingModelWorkflow | None" = None

    def __new__(cls) -> "BuildEmbeddingModelWorkflow":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tasks = [
                Task01ExtractVideoIds(),
                Task02FetchVideoData(),
                Task03BuildDataFrame(),
                Task04SaveRawParquet(),
                Task05TransformData(),
                Task06BuildEmbeddings(),
                Task07SaveModel(),
            ]
        return cls._instance

    def run(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[Workflow] Starting BuildEmbeddingModelWorkflow  model='%s'", req.model_name)
        for task in self._tasks:
            task_name = task.__class__.__name__
            logger.info("[Workflow] Running %s …", task_name)
            ctx = task.execute(req, ctx)
            logger.info("[Workflow] %s done.", task_name)
        logger.info("[Workflow] Completed  model_location=%s", ctx.get("model_location"))
        return ctx
