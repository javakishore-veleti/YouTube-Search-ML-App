"""
Approach 01 – Conversation Search Facade
==========================================
Loads a pre-built SentenceTransformer model + embeddings, encodes the user's
query, computes distance, and returns the top-k closest videos.

Stateless singleton — model artefacts are lazily loaded and cached in memory.

Threshold strategy
------------------
A fixed threshold doesn't work because:
- Different metrics produce different score ranges
- Models built from few videos have narrow distance bands
- A threshold of 40 is meaningless for Bray-Curtis (max 1.0)

Solution: compute the distance between all video pairs in the index to get the
"baseline" distance distribution. Then set the effective threshold as a
percentile of that baseline. Queries that are closer than most video-to-video
distances are relevant; queries further away are not.
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

# Hard-coded fallback thresholds per metric (used only when baseline can't be computed)
METRIC_FALLBACK_THRESHOLDS: Dict[str, float] = {
    "manhattan":   20.0,
    "euclidean":    5.0,
    "chebyshev":    0.5,
    "minkowski":   20.0,
    "seuclidean":   5.0,
    "canberra":    60.0,
    "braycurtis":   0.2,
    "hamming":      0.5,
}

# Adaptive threshold multiplier: effective_threshold = mean_inter_video_distance * MULTIPLIER
# 1.5x means query must be at most 50% further than the average video-to-video distance
BASELINE_MULTIPLIER = 1.5


class ConversationFacade(IConversationFacade):
    """
    Approach 01 conversation search.
    Caches loaded models/embeddings/DataFrames keyed by model_location.
    """

    _instance: Optional["ConversationFacade"] = None
    _cache: Dict[str, Tuple[SentenceTransformer, np.ndarray, pd.DataFrame]] = {}
    _baseline_cache: Dict[str, Dict[str, float]] = {}  # model_location → {metric → threshold}

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

    def _compute_baseline_threshold(self, embeddings: np.ndarray,
                                     dist_name: str, model_location: str) -> float:
        """
        Compute the adaptive threshold from the actual distance distribution
        of the video index. Uses BASELINE_MULTIPLIER * mean inter-video distance.

        This adapts automatically to:
        - The number of videos (small models have narrow distance bands)
        - The distance metric (Manhattan ~20, Bray-Curtis ~0.3, etc.)
        - The embedding dimensionality
        """
        cache_key = f"{model_location}:{dist_name}"
        if cache_key in self._baseline_cache:
            return self._baseline_cache[cache_key]

        dist = DistanceMetric.get_metric(dist_name)
        pairwise = dist.pairwise(embeddings)
        # extract upper triangle (exclude diagonal zeros)
        n = pairwise.shape[0]
        upper = pairwise[np.triu_indices(n, k=1)]

        if len(upper) == 0:
            # single video — can't compute baseline
            threshold = METRIC_FALLBACK_THRESHOLDS.get(dist_name, 20.0)
        else:
            mean_dist = float(np.mean(upper))
            threshold = mean_dist * BASELINE_MULTIPLIER
            # safety: don't let threshold be zero or negative
            if threshold <= 0:
                threshold = METRIC_FALLBACK_THRESHOLDS.get(dist_name, 20.0)

        self._baseline_cache[cache_key] = threshold
        logger.info(
            "[ConvFacade] Baseline threshold for %s/%s: %.4f (from %d pairs, %.1fx mean)",
            dist_name, model_location[-30:], threshold, len(upper), BASELINE_MULTIPLIER,
        )
        return threshold

    def search(self, req: ConversationSearchRequest) -> ConversationSearchResponse:
        model, embeddings, df = self._load(req)

        # encode query
        query_embedding = model.encode(req.query).reshape(1, -1)

        # compute distances
        dist = DistanceMetric.get_metric(req.dist_name)
        dist_arr = dist.pairwise(embeddings, query_embedding).flatten()

        # determine effective threshold
        # use adaptive baseline unless user explicitly set a small metric-appropriate value
        baseline = self._compute_baseline_threshold(embeddings, req.dist_name, req.model_location)
        user_threshold = req.threshold

        # if user threshold is clearly from the wrong scale, use baseline
        # otherwise use the stricter of (user, baseline) to prevent false positives
        effective = min(user_threshold, baseline)
        logger.info(
            "[ConvFacade] metric=%s user_threshold=%.2f baseline=%.4f effective=%.4f",
            req.dist_name, user_threshold, baseline, effective,
        )

        # filter by threshold and keep top_k
        idx_below = np.argwhere(dist_arr < effective).flatten()
        if len(idx_below) == 0:
            logger.info("[ConvFacade] No results below threshold=%.4f", effective)
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
