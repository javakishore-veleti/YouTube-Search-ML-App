"""
Approach 01 – Workflow
======================
Orchestrates the 7 Tasks in sequence, passing a shared context bag between them.
Instruments every run with model_build_wf / model_build_wf_task DB rows.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import WorkflowRepository
from app.app_common.model_approaches.dtos import ModelBuildRequest
from app.app_common.model_approaches.interfaces import IModelWorkflow
from app.app_model_approaches.approach_01.tasks import (
    Task01ExtractVideoIds, Task02FetchVideoData, Task03BuildDataFrame,
    Task04SaveRawParquet, Task05TransformData, Task06BuildEmbeddings, Task07SaveModel,
)

logger = logging.getLogger(__name__)

APPROACH_ID   = "e1cffc4f-d00d-4b04-b705-18eef34e10d2"
TASK_FILE     = "app_model_approaches/approach_01/tasks.py"

# Keys that are safe to serialise as task output_data (skip DataFrames, model objects, etc.)
_SERIALISABLE_TYPES = (str, int, float, bool, list, dict, type(None))


def _extract_output(ctx_before: Dict[str, Any], ctx_after: Dict[str, Any]) -> dict:
    """Return only new or changed ctx keys whose values are JSON-safe."""
    output: dict = {}
    for k, v in ctx_after.items():
        if k.startswith("_"):
            continue                              # skip private keys like _st_model
        if not isinstance(v, _SERIALISABLE_TYPES):
            if isinstance(v, Path):
                v = str(v)                        # Path → string
            else:
                continue                          # skip DataFrames etc.
        old = ctx_before.get(k)
        if k not in ctx_before or old != v:
            # for lists, store count instead of full payload to keep JSON small
            if isinstance(v, list) and len(v) > 10:
                output[k + "_count"] = len(v)
            else:
                output[k] = v
    return output


class BuildEmbeddingModelWorkflow(IModelWorkflow):
    """
    Runs all 7 pipeline tasks in order.
    Writes one model_build_wf row + one model_build_wf_task row per task to DB.
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

    def run(self, req: ModelBuildRequest, ctx: Dict[str, Any],
            model_id: Optional[int] = None,
            queue_item_id: Optional[int] = None) -> Dict[str, Any]:
        logger.info("[Workflow] Starting  model='%s'", req.model_name)

        # ── create WF record ──────────────────────────────────────────────
        session = SessionLocal()
        wf_repo = WorkflowRepository(session)
        wf = wf_repo.create_wf(
            approach_id=APPROACH_ID,
            model_id=model_id,
            queue_item_id=queue_item_id,
        )
        wf_id = wf.id
        session.close()

        # store wf_id in ctx so Facade / scheduler can retrieve it
        ctx["wf_id"] = wf_id

        try:
            for order, task in enumerate(self._tasks, start=1):
                task_name = task.__class__.__name__
                logger.info("[Workflow] Running %s …", task_name)

                # create pending task row
                s2 = SessionLocal()
                t_row = WorkflowRepository(s2).create_task(
                    wf_id=wf_id,
                    task_id=task_name,
                    task_file=TASK_FILE,
                    task_order=order,
                )
                t_row_id = t_row.id
                WorkflowRepository(s2).start_task(t_row_id)
                s2.close()

                # snapshot ctx keys before task runs
                ctx_before = dict(ctx)

                try:
                    ctx = task.execute(req, ctx)
                    task_output = _extract_output(ctx_before, ctx)
                    s3 = SessionLocal()
                    WorkflowRepository(s3).finish_task(
                        t_row_id, "completed", output_data=task_output,
                    )
                    s3.close()
                    logger.info("[Workflow] %s completed.", task_name)
                except Exception as exc:
                    s3 = SessionLocal()
                    WorkflowRepository(s3).finish_task(t_row_id, "failed", str(exc))
                    s3.close()
                    logger.error("[Workflow] %s FAILED: %s", task_name, exc)
                    # mark WF failed and re-raise so caller handles it
                    s4 = SessionLocal()
                    WorkflowRepository(s4).update_wf_status(wf_id, "failed", str(exc))
                    s4.close()
                    raise

            # all tasks done → mark WF completed
            s5 = SessionLocal()
            WorkflowRepository(s5).update_wf_status(wf_id, "completed")
            s5.close()
            logger.info("[Workflow] Completed  model_location=%s", ctx.get("model_location"))
            return ctx

        except Exception:
            raise   # already marked failed above

