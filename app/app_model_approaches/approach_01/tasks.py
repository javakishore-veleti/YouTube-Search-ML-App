"""
Approach 01 – Tasks
====================
Each class implements IModelTask for one atomic pipeline step.
All tasks are stateless singletons (no instance state, all data via ctx).

Context-bag keys (produced / consumed)
---------------------------------------
  video_ids          : List[str]   – Step 1 → all steps
  yt_api_key         : str         – Step 1 → Step 2
  base_model_key     : str         – Step 1 → Step 6
  request_uuid       : str         – Step 1 → all steps
  raw_records        : List[dict]  – Step 2 → Step 3
  df_raw             : DataFrame   – Step 3 → Step 4
  dataset_dir        : Path        – Step 4 → Step 5,7
  raw_parquet        : str         – Step 4 → output
  df_transformed     : DataFrame   – Step 5 → Step 6
  transformed_parquet: str         – Step 5 → output
  model_location     : str         – Step 7 → output
  embeddings_path    : str         – Step 7 → output
  sentence_count     : int         – Step 6 → output
  embedding_dim      : int         – Step 6 → output
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import requests
from sentence_transformers import SentenceTransformer
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from app.app_common.model_approaches.dtos import ModelBuildRequest
from app.app_common.model_approaches.interfaces import IModelTask

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_BASE_MODELS: Dict[str, str] = {
    # UUID keys (from approaches.json)
    "5f96a19d-6066-468f-bb30-112159cb49a6": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "7ae50b73-33a7-4586-a98d-8b49e469dafa": "sentence-transformers/all-MiniLM-L12-v2",
    "39b9a4c4-f61a-402a-a9fa-590b98e3794b": "sentence-transformers/all-mpnet-base-v1",
    # Slug keys (fallback / convenience)
    "paraphrase-multilingual-MiniLM-L12-v2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "all-MiniLM-L12-v2": "sentence-transformers/all-MiniLM-L12-v2",
    "all-mpnet-base-v1": "sentence-transformers/all-mpnet-base-v1",
}

DEFAULT_BASE_MODEL_KEY = "5f96a19d-6066-468f-bb30-112159cb49a6"  # paraphrase-multilingual-MiniLM-L12-v2

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "this", "that", "was", "are",
    "be", "as", "so", "we", "his", "her", "they", "you", "i", "me",
    "my", "your", "our", "have", "has", "had", "not", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "been",
    "being", "what", "which", "who", "when", "where", "how", "all", "each",
    "both", "more", "also", "into", "about", "its", "their", "there",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dataset_dir(request_uuid: str) -> Path:
    return (
        Path.home()
        / "runtime_data" / "DataSets"
        / "YouTube-Search-ML-App" / "Approach-01"
        / request_uuid
    )


def _model_dir(request_uuid: str) -> Path:
    return (
        Path.home()
        / "runtime_data" / "DataSets"
        / "YouTube-Search-ML-App" / "Approach-01"
        / request_uuid
        / "latest" / "final-embedding-model"
    )


def _clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS]
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Task 01 – Extract video IDs and initialise context
# ---------------------------------------------------------------------------

class Task01ExtractVideoIds(IModelTask):
    """Step 1 – pull video_ids, base_model_key, request_uuid from the request."""

    _instance: "Task01ExtractVideoIds | None" = None

    def __new__(cls) -> "Task01ExtractVideoIds":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        # Extract video IDs (support List[str] or List[dict])
        raw: Any = req.input_criteria.get("video_ids") or req.ctx_data.get("video_ids", [])
        video_ids: List[str] = []
        for item in raw:
            if isinstance(item, str):
                video_ids.append(item)
            elif isinstance(item, dict):
                vid = item.get("video_id") or item.get("id", "")
                if vid:
                    video_ids.append(vid)

        if not video_ids:
            raise ValueError("No video_ids found in request input_criteria or ctx_data.")

        base_model_key: str = req.input_criteria.get("base_model_key", DEFAULT_BASE_MODEL_KEY)
        if base_model_key not in SUPPORTED_BASE_MODELS:
            logger.warning("Unknown base_model_key '%s', falling back to default.", base_model_key)
            base_model_key = DEFAULT_BASE_MODEL_KEY

        request_uuid: str = req.input_criteria.get("request_uuid") or str(uuid.uuid4())
        yt_api_key: str = req.input_criteria.get("yt_api_key", "") or os.environ.get("YOUTUBE_API_KEY", "")

        ctx.update({
            "video_ids": video_ids,
            "base_model_key": base_model_key,
            "request_uuid": request_uuid,
            "yt_api_key": yt_api_key,
        })
        logger.info("[Task01] video_ids=%d  base_model=%s  uuid=%s", len(video_ids), base_model_key, request_uuid)
        return ctx


# ---------------------------------------------------------------------------
# Task 02 – Fetch descriptions + transcripts from YouTube
# ---------------------------------------------------------------------------

class Task02FetchVideoData(IModelTask):
    """Step 2 – for each video ID fetch description (Data API) + transcript."""

    _instance: "Task02FetchVideoData | None" = None

    def __new__(cls) -> "Task02FetchVideoData":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        video_ids: List[str] = ctx["video_ids"]
        yt_api_key: str = ctx.get("yt_api_key", "")
        yt_api = YouTubeTranscriptApi()
        records: List[Dict[str, Any]] = []

        for video_id in video_ids:
            description = ""
            transcript_text = ""

            # Description via YouTube Data API v3
            if yt_api_key:
                try:
                    resp = requests.get(
                        "https://www.googleapis.com/youtube/v3/videos",
                        params={"part": "snippet", "id": video_id, "key": yt_api_key},
                        timeout=10,
                    )
                    resp.raise_for_status()
                    items = resp.json().get("items", [])
                    if items:
                        description = items[0].get("snippet", {}).get("description", "")
                except Exception as exc:
                    logger.warning("[Task02] Description fetch failed for %s: %s", video_id, exc)

            # Transcript via youtube-transcript-api v1.x
            try:
                fetched = yt_api.fetch(video_id)
                transcript_text = " ".join(seg.text for seg in fetched)
            except (NoTranscriptFound, TranscriptsDisabled) as exc:
                logger.warning("[Task02] No transcript for %s: %s", video_id, exc)
            except Exception as exc:
                logger.warning("[Task02] Transcript error for %s: %s", video_id, exc)

            records.append({"video_id": video_id, "description": description, "transcript": transcript_text})
            logger.info("[Task02] video_id=%s  desc=%d chars  transcript=%d chars",
                        video_id, len(description), len(transcript_text))

        ctx["raw_records"] = records
        return ctx


# ---------------------------------------------------------------------------
# Task 03 – Build DataFrame
# ---------------------------------------------------------------------------

class Task03BuildDataFrame(IModelTask):
    """Step 3 – create a DataFrame with columns video_id, description, transcript."""

    _instance: "Task03BuildDataFrame | None" = None

    def __new__(cls) -> "Task03BuildDataFrame":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        records: List[Dict[str, Any]] = ctx["raw_records"]
        df = pd.DataFrame(records, columns=["video_id", "description", "transcript"])
        ctx["df_raw"] = df
        logger.info("[Task03] DataFrame shape: %s", df.shape)
        return ctx


# ---------------------------------------------------------------------------
# Task 04 – Persist raw parquet
# ---------------------------------------------------------------------------

class Task04SaveRawParquet(IModelTask):
    """Step 4 – save raw DataFrame as video-transcripts.parquet."""

    _instance: "Task04SaveRawParquet | None" = None

    def __new__(cls) -> "Task04SaveRawParquet":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        request_uuid: str = ctx["request_uuid"]
        ds_dir = _dataset_dir(request_uuid)
        ds_dir.mkdir(parents=True, exist_ok=True)

        raw_parquet = ds_dir / "video-transcripts.parquet"
        ctx["df_raw"].to_parquet(raw_parquet, index=False, engine="pyarrow")
        ctx["dataset_dir"] = ds_dir
        ctx["raw_parquet"] = str(raw_parquet)
        logger.info("[Task04] Raw parquet saved → %s", raw_parquet)
        return ctx


# ---------------------------------------------------------------------------
# Task 05 – Transform data (clean + stopword removal)
# ---------------------------------------------------------------------------

class Task05TransformData(IModelTask):
    """Step 5 – clean text, remove stopwords, save transformed parquet."""

    _instance: "Task05TransformData | None" = None

    def __new__(cls) -> "Task05TransformData":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        df: pd.DataFrame = ctx["df_raw"].copy()
        df["description_clean"] = df["description"].fillna("").apply(_clean_text)
        df["transcript_clean"] = df["transcript"].fillna("").apply(_clean_text)
        df["text"] = (df["description_clean"] + " " + df["transcript_clean"]).str.strip()

        transformed_parquet = ctx["dataset_dir"] / "video-transcripts-transformed.parquet"
        df.to_parquet(transformed_parquet, index=False, engine="pyarrow")

        ctx["df_transformed"] = df
        ctx["transformed_parquet"] = str(transformed_parquet)
        logger.info("[Task05] Transformed parquet saved → %s", transformed_parquet)
        return ctx


# ---------------------------------------------------------------------------
# Task 06 – Build embeddings with SentenceTransformer
# ---------------------------------------------------------------------------

class Task06BuildEmbeddings(IModelTask):
    """Step 6 – load base model, encode all sentences, store embeddings."""

    _instance: "Task06BuildEmbeddings | None" = None

    def __new__(cls) -> "Task06BuildEmbeddings":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        base_model_key: str = ctx["base_model_key"]
        base_model_id: str = SUPPORTED_BASE_MODELS[base_model_key]

        sentences: List[str] = [
            s for s in ctx["df_transformed"]["text"].dropna().tolist() if s.strip()
        ]

        logger.info("[Task06] Loading SentenceTransformer '%s' …", base_model_id)
        model = SentenceTransformer(base_model_id)

        logger.info("[Task06] Encoding %d sentences …", len(sentences))
        embeddings = model.encode(sentences, show_progress_bar=False, convert_to_numpy=True)

        # Persist embeddings alongside parquet files
        embeddings_path = ctx["dataset_dir"] / "embeddings.npy"
        np.save(str(embeddings_path), embeddings)

        ctx["_st_model"] = model          # pass model instance to Task07
        ctx["sentence_count"] = len(sentences)
        ctx["embedding_dim"] = int(embeddings.shape[1]) if embeddings.ndim == 2 else 0
        ctx["embeddings_path"] = str(embeddings_path)
        ctx["base_model_id"] = base_model_id
        logger.info("[Task06] Embeddings shape %s  saved → %s", embeddings.shape, embeddings_path)
        return ctx


# ---------------------------------------------------------------------------
# Task 07 – Save fine-tuned model
# ---------------------------------------------------------------------------

class Task07SaveModel(IModelTask):
    """Step 7 – persist the SentenceTransformer model to disk."""

    _instance: "Task07SaveModel | None" = None

    def __new__(cls) -> "Task07SaveModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def execute(self, req: ModelBuildRequest, ctx: Dict[str, Any]) -> Dict[str, Any]:
        request_uuid: str = ctx["request_uuid"]
        mdl_dir = _model_dir(request_uuid)
        mdl_dir.mkdir(parents=True, exist_ok=True)

        model: SentenceTransformer = ctx.pop("_st_model")
        model.save(str(mdl_dir))

        ctx["model_location"] = str(mdl_dir)
        logger.info("[Task07] Model saved → %s", mdl_dir)
        return ctx
