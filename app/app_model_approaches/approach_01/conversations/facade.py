"""
Approach 01 – Conversation Search Facade
==========================================
Loads a pre-built SentenceTransformer model + embeddings, encodes the user's
query, computes distance, and returns the top-k closest videos.

Stateless singleton — model artefacts are lazily loaded and cached in memory.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import DistanceMetric

from app.app_common.model_approaches.dtos import (
    ConversationSearchRequest,
    ConversationSearchResponse,
)
from app.app_common.model_approaches.interfaces import IConversationFacade

logger = logging.getLogger(__name__)


class ConversationFacade(IConversationFacade):
    """
    Approach 01 conversation search.
    Caches loaded models/embeddings/DataFrames keyed by model_location.
    """

    _instance: Optional["ConversationFacade"] = None
    _cache: Dict[str, Tuple[SentenceTransformer, np.ndarray, pd.DataFrame]] = {}

    def __new__(cls) -> "ConversationFacade":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _load(self, req: ConversationSearchRequest
              ) -> Tuple[SentenceTransformer, np.ndarray, pd.DataFrame]:
        key = req.model_location
        if key not in self._cache:
            logger.info("[ConvFacade] Loading model from %s", req.model_location)
            model = SentenceTransformer(req.model_location)
            embeddings = np.load(req.embeddings_path)
            df = pd.read_parquet(req.transformed_parquet)
            self._cache[key] = (model, embeddings, df)
            logger.info(
                "[ConvFacade] Cached — embeddings shape=%s, df shape=%s",
                embeddings.shape, df.shape,
            )
        return self._cache[key]

    def search(self, req: ConversationSearchRequest) -> ConversationSearchResponse:
        model, embeddings, df = self._load(req)

        # encode query
        query_embedding = model.encode(req.query).reshape(1, -1)

        # compute distances
        dist = DistanceMetric.get_metric(req.dist_name)
        dist_arr = dist.pairwise(embeddings, query_embedding).flatten()

        # filter by threshold and keep top_k
        idx_below = np.argwhere(dist_arr < req.threshold).flatten()
        if len(idx_below) == 0:
            logger.info("[ConvFacade] No results below threshold=%s", req.threshold)
            return ConversationSearchResponse(results=[], query=req.query)

        idx_sorted = idx_below[np.argsort(dist_arr[idx_below])][:req.top_k]

        results = []
        for i in idx_sorted:
            row = df.iloc[i]
            video_id = str(row.get("video_id", ""))
            results.append({
                "title": str(row.get("description", ""))[:120] or video_id,
                "video_id": video_id,
                "description": str(row.get("description", "")),
                "channel": "",
                "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else "",
                "score": round(float(dist_arr[i]), 2),
            })

        logger.info("[ConvFacade] Returning %d results for query='%s'", len(results), req.query[:60])
        return ConversationSearchResponse(results=results, query=req.query)
