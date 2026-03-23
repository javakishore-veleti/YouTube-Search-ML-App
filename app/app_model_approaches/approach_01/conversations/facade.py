"""
Approach 01 – Conversation Search Facade
==========================================
Loads a pre-built SentenceTransformer model + embeddings, encodes the user's
query, computes distance, and returns the top-k closest videos.

Stateless singleton — model artefacts are lazily loaded and cached in memory.

Threshold strategy: Uses the 20th percentile of inter-video pairwise distances
as the adaptive threshold. This ensures only queries that are closer than
80% of video-to-video pairs are considered relevant.
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

# Fallback thresholds when baseline can't be computed (e.g. single-video model)
METRIC_FALLBACK_THRESHOLDS: Dict[str, float] = {
    "manhattan":   15.0,
    "euclidean":    4.0,
    "chebyshev":    0.4,
    "minkowski":   15.0,
    "seuclidean":   4.0,
    "canberra":    50.0,
    "braycurtis":   0.15,
    "hamming":      0.4,
}

# Percentile of inter-video distances to use as adaptive threshold.
# 20th percentile means: query must be closer than 80% of video-to-video distances.
BASELINE_PERCENTILE = 20


class ConversationFacade(IConversationFacade):
    """
    Approach 01 conversation search.
    Caches loaded models/embeddings/DataFrames keyed by model_location.
    """

    _instance: Optional["ConversationFacade"] = None
    _cache: Dict[str, Tuple[SentenceTransformer, np.ndarray, pd.DataFrame]] = {}
    _baseline_cache: Dict[str, float] = {}

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

            # FIX: align DataFrame to embeddings by filtering out rows with empty text
            # Task06 skips empty text when encoding, so embeddings has fewer rows than df
            # if any videos had no transcript/description
            non_empty_mask = df["text"].fillna("").str.strip().astype(bool)
            df_aligned = df[non_empty_mask].reset_index(drop=True)

            if len(df_aligned) != embeddings.shape[0]:
                logger.warning(
                    "[ConvFacade] Alignment mismatch even after filtering: "
                    "df=%d rows, embeddings=%d rows. Truncating to min.",
                    len(df_aligned), embeddings.shape[0],
                )
                n = min(len(df_aligned), embeddings.shape[0])
                df_aligned = df_aligned.iloc[:n]
                embeddings = embeddings[:n]

            self._cache[key] = (model, embeddings, df_aligned)
            logger.info(
                "[ConvFacade] Cached — embeddings shape=%s, df shape=%s (aligned)",
                embeddings.shape, df_aligned.shape,
            )
        return self._cache[key]

    def _compute_baseline_threshold(self, embeddings: np.ndarray,
                                     dist_name: str, model_location: str) -> float:
        """
        Compute the adaptive threshold from the actual distance distribution
        of the video index. Uses the BASELINE_PERCENTILE of all pairwise
        inter-video distances.

        For a 17-video Manhattan model this gives ~15.9 (p20), which correctly
        passes "AI engineering" (13.6) but rejects "STUPID" (20.4).
        """
        cache_key = f"{model_location}:{dist_name}"
        if cache_key in self._baseline_cache:
            return self._baseline_cache[cache_key]

        dist = DistanceMetric.get_metric(dist_name)
        pairwise = dist.pairwise(embeddings)
        n = pairwise.shape[0]
        upper = pairwise[np.triu_indices(n, k=1)]

        if len(upper) == 0:
            threshold = METRIC_FALLBACK_THRESHOLDS.get(dist_name, 15.0)
        else:
            threshold = float(np.percentile(upper, BASELINE_PERCENTILE))
            if threshold <= 0:
                threshold = METRIC_FALLBACK_THRESHOLDS.get(dist_name, 15.0)

        self._baseline_cache[cache_key] = threshold
        logger.info(
            "[ConvFacade] Baseline threshold for %s: %.4f (p%d of %d pairs)",
            dist_name, threshold, BASELINE_PERCENTILE, len(upper),
        )
        return threshold

    def search(self, req: ConversationSearchRequest) -> ConversationSearchResponse:
        model, embeddings, df = self._load(req)

        # encode query
        query_embedding = model.encode(req.query).reshape(1, -1)

        # compute distances
        dist = DistanceMetric.get_metric(req.dist_name)
        dist_arr = dist.pairwise(embeddings, query_embedding).flatten()

        # determine effective threshold: stricter of user setting and adaptive baseline
        baseline = self._compute_baseline_threshold(embeddings, req.dist_name, req.model_location)
        effective = min(req.threshold, baseline)

        logger.info(
            "[ConvFacade] metric=%s user_threshold=%.2f baseline=%.4f effective=%.4f",
            req.dist_name, req.threshold, baseline, effective,
        )

        # filter by threshold and keep top_k
        idx_below = np.argwhere(dist_arr < effective).flatten()
        if len(idx_below) == 0:
            logger.info("[ConvFacade] No results below threshold=%.4f for query='%s'",
                        effective, req.query[:60])
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
                "score": round(float(dist_arr[i]), 4),
            })

        logger.info(
            "[ConvFacade] Returning %d results for query='%s' (threshold=%.4f)",
            len(results), req.query[:60], effective,
        )
        return ConversationSearchResponse(results=results, query=req.query)
