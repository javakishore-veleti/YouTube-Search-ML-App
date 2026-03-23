from __future__ import annotations

import logging

from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach
from app.app_model_approaches.approach_01.workflow import BuildEmbeddingModelWorkflow

logger = logging.getLogger(__name__)

APPROACH_TYPE = "e1cffc4f-d00d-4b04-b705-18eef34e10d2"


class Facade(IModelApproach):
    """
    Approach 01 – Building a Custom Embedding Model.
    Stateless singleton – all state flows through ModelBuildRequest / ctx.

    Expected fields in ModelBuildRequest.input_criteria
    ----------------------------------------------------
    video_ids        : List[str | dict]  – YouTube video IDs (required)
    base_model_key   : str               – sub-model UUID or slug (optional)
    yt_api_key       : str               – YouTube Data API key (optional)
    request_uuid     : str               – stable UUID for this run (optional)
    model_id         : int               – DB model record ID (optional, set by scheduler)
    queue_item_id    : int               – DB queue item ID  (optional, set by scheduler)
    """

    _instance: "Facade | None" = None

    def __new__(cls) -> "Facade":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._workflow = BuildEmbeddingModelWorkflow()
        return cls._instance

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        """Run the full 7-step workflow and return the result."""
        ctx: dict = {}
        model_id      = req.input_criteria.get("model_id")
        queue_item_id = req.input_criteria.get("queue_item_id")
        try:
            ctx = self._workflow.run(req, ctx,
                                     model_id=model_id,
                                     queue_item_id=queue_item_id)
        except Exception as exc:
            logger.exception("[Facade] build_model failed: %s", exc)
            return ModelBuildResponse(
                model_name=req.model_name,
                approach_type=APPROACH_TYPE,
                status="failed",
                output_results={"error": str(exc), "wf_id": ctx.get("wf_id")},
            )

        return ModelBuildResponse(
            model_name=req.model_name,
            approach_type=APPROACH_TYPE,
            status="completed",
            model_location=ctx.get("model_location", ""),
            output_results={
                "request_uuid":          ctx.get("request_uuid"),
                "base_model_key":        ctx.get("base_model_key"),
                "base_model_id":         ctx.get("base_model_id"),
                "video_count":           len(ctx.get("video_ids", [])),
                "sentence_count":        ctx.get("sentence_count", 0),
                "embedding_dim":         ctx.get("embedding_dim", 0),
                "raw_parquet":           ctx.get("raw_parquet"),
                "transformed_parquet":   ctx.get("transformed_parquet"),
                "embeddings_path":       ctx.get("embeddings_path"),
                "model_location":        ctx.get("model_location"),
                "content_stats":         ctx.get("content_stats", {}),
            },
        )

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        """Load the saved model, run a probe sentence, return embedding_dim."""
        model_location: str = req.input_criteria.get("model_location", "")
        if not model_location:
            return ModelBuildResponse(
                model_name=req.model_name,
                approach_type=APPROACH_TYPE,
                status="failed",
                output_results={"error": "model_location not provided in input_criteria."},
            )
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(model_location)
            emb = model.encode(["evaluation probe sentence"], convert_to_numpy=True)
            return ModelBuildResponse(
                model_name=req.model_name,
                approach_type=APPROACH_TYPE,
                status="evaluated",
                model_location=model_location,
                output_results={
                    "embedding_dim": int(emb.shape[1]),
                    "model_location": model_location,
                },
            )
        except Exception as exc:
            logger.exception("[Facade] evaluate failed: %s", exc)
            return ModelBuildResponse(
                model_name=req.model_name,
                approach_type=APPROACH_TYPE,
                status="failed",
                output_results={"error": str(exc)},
            )

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        """Acknowledge publish intent; model artefact is already on disk."""
        model_location: str = req.input_criteria.get("model_location", "")
        return ModelBuildResponse(
            model_name=req.model_name,
            approach_type=APPROACH_TYPE,
            status="published",
            model_location=model_location,
            output_results={
                "published": True,
                "model_location": model_location,
                "publish_as_latest": req.publish_as_latest,
            },
        )
