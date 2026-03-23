# Approach 01 — Building Custom Embedding Model: Implementation Guide

## Introduction

This approach builds a custom video search index from YouTube video transcripts using a pre-trained SentenceTransformer model. It converts video content into mathematical vectors (embeddings) and uses distance metrics to find the most relevant videos for your query.

- **Model Unique ID:** `e1cffc4f-d00d-4b04-b705-18eef34e10d2`
- **Implementation:** `app/app_model_approaches/approach_01/`
- **Conversation Search:** `app/app_model_approaches/approach_01/conversations/facade.py`
- **Category:** Embedding Models (Index-Based Semantic Search)

### The Embedding Index

When you build a model with this approach, the primary artefact is an **embedding index** — a NumPy array stored as `embeddings.npy`. Its shape is **(N_videos, embedding_dim)** where:

- **Rows (N_videos):** One row per video in your collection. If you selected 5 videos, the index has 5 rows. If 100 videos, 100 rows.
- **Columns (embedding_dim):** The number of dimensions in each video's vector representation. This is determined by the sub-model you choose:
  - `all-MiniLM-L12-v2` → **384 columns** (384-dimensional vector per video)
  - `paraphrase-multilingual-MiniLM-L12-v2` → **384 columns**
  - `all-mpnet-base-v1` → **768 columns**

For example, a model built from 20 videos using `all-MiniLM-L12-v2` produces an index of shape **(20, 384)** — that's 20 rows × 384 floating-point numbers = 7,680 values. Each row is one video's "semantic fingerprint". At search time, your query is encoded into a single (1, 384) vector and compared against all 20 rows to find the closest matches.

The embedding index is separate from the DataFrame (parquet file) which stores the actual video metadata (video_id, description, transcript). Row `embeddings[i]` corresponds to `DataFrame.iloc[i]` — this 1:1 alignment is critical for returning correct search results.

---

## Table of Contents

1. [Objective](#1-objective)
2. [What "Custom Model" Actually Means](#2-what-custom-model-actually-means)
3. [What is Fine-Tuning and Why This Approach Doesn't Do It](#3-what-is-fine-tuning-and-why-this-approach-doesnt-do-it)
4. [How the Build Pipeline Works](#4-how-the-build-pipeline-works)
5. [How Conversation Search Works](#5-how-conversation-search-works)
6. [SentenceTransformer: What It Is and How It Encodes Text](#6-sentencetransformer-what-it-is-and-how-it-encodes-text)
7. [Embedding Space Geometry](#7-embedding-space-geometry)
8. [Distance Metrics Deep Dive](#8-distance-metrics-deep-dive)
9. [Adaptive Threshold Strategy](#9-adaptive-threshold-strategy)
10. [Limitations and Gaps](#10-limitations-and-gaps)
11. [Best Use Cases](#11-best-use-cases)
12. [Poor Use Cases (Anti-Patterns)](#12-poor-use-cases-anti-patterns)
13. [Possible Improvements (Future Work)](#13-possible-improvements-future-work)
14. [Build Artefacts Reference](#14-build-artefacts-reference)
15. [Conversation Settings Reference](#15-conversation-settings-reference)

---

## 1. Objective

Enable users to select YouTube videos, build a semantic search index from their transcripts and descriptions, and search that index using natural language queries with ranked results based on vector similarity.

This is **NOT model training**. It is **index construction + inference** using a pre-trained encoder.

---

## 2. What "Custom Model" Actually Means

The "custom model" in Approach 01 is a **misnomer**. The user does not train, fine-tune, or modify any neural network. What actually happens:

1. A pre-trained SentenceTransformer (e.g. `all-MiniLM-L12-v2`) is downloaded from HuggingFace **as-is**
2. It is used to encode video transcripts into vectors → saved as `embeddings.npy` (the INDEX)
3. The same unchanged model is saved to disk → called "your model"

The model's weights, vocabulary, tokenizer, and language understanding are **identical** to the original HuggingFace checkpoint. The only truly custom artefact is the embedding index — the pre-computed vectors for the user's specific videos.

**Analogy:** The model is a universal translator who can read and understand any book in any language. Your "custom model" is the specific collection of books you put on a bookshelf. The translator's reading ability doesn't change — only which books are available to search through.

**Why this distinction matters:**

- Encoding the word "Kishore" always produces a valid 384-dim vector, even if "Kishore" appears nowhere in the indexed videos — because the model already knows this word from its pre-training on billions of sentences
- There is no concept of "word not found" or "out of vocabulary"
- Every possible input — even gibberish — produces a valid vector at a finite distance from your video vectors
- The **only** mechanism to filter irrelevant queries is distance threshold calibration

---

## 3. What is Fine-Tuning and Why This Approach Doesn't Do It

### What Fine-Tuning Is

Fine-tuning is the process of taking a pre-trained neural network and continuing to train it on your specific data so that it **modifies its internal weights** to better understand your domain. In the context of sentence embeddings, fine-tuning would mean:

1. **Preparing training pairs:** Creating examples of sentences that should be "similar" and sentences that should be "different" from your video content. For example: (query: "how to deploy ML models", positive: transcript excerpt about deployment, negative: transcript excerpt about cooking).

2. **Running a training loop:** Feeding these pairs through the model, computing a loss function (like contrastive loss or triplet loss) that measures how well the model separates similar from dissimilar pairs, and using backpropagation to update the model's millions of weights.

3. **Updating the model's understanding:** After many iterations, the model's internal representations shift. Words and phrases specific to your domain get tighter, more distinct embeddings. The model literally learns new semantic relationships from your data.

4. **Producing a genuinely different model:** The saved model has different weights from the original. It will encode the same text differently — ideally better for your specific use case, potentially worse for general text.

### Why Approach 01 Skips Fine-Tuning

Approach 01 deliberately avoids fine-tuning for pragmatic reasons:

- **No training data preparation needed.** Fine-tuning requires labelled pairs (similar/dissimilar). Users would need to manually create or review hundreds of pairs — a significant effort.
- **No training infrastructure.** Fine-tuning typically requires a GPU and takes 30-60 minutes. Approach 01 builds an index in 1-2 minutes on CPU.
- **No risk of overfitting.** With only 5-50 videos, fine-tuning a 33M-parameter model would almost certainly overfit — the model would memorise your data instead of learning useful patterns.
- **Pre-trained models are already very good.** Models like `all-MiniLM-L12-v2` were trained on 1 billion sentence pairs and perform well out-of-the-box for most English text.

### What This Means for Search Quality

Without fine-tuning, the model treats your domain the same as any other. A model built from machine learning videos doesn't understand "ML" any better than a model built from cooking videos. The difference is entirely in the **index** — which videos are available to match against — not in the model's understanding.

This is perfectly adequate for topic-level semantic search ("find videos about neural networks") but insufficient for domain-specific nuance ("find videos about the vanishing gradient problem in RNNs vs LSTMs" — the model may not distinguish these well without fine-tuning).

### How Other Approaches Address This

- **Approach 02 (PyTorch) / Approach 03 (TensorFlow):** Intended to include actual fine-tuning with contrastive learning on user-provided data
- **Approach 05 (LLM):** Uses large language models that can understand domain context through in-context learning without weight updates

---

## 4. How the Build Pipeline Works

The build pipeline is implemented as 7 sequential tasks orchestrated by `BuildEmbeddingModelWorkflow`. Each task is a stateless singleton class implementing `IModelTask`. The full code is in `app/app_model_approaches/approach_01/tasks.py`.

**Task 01 — Extract Video IDs:** Reads video IDs from the build request, resolves the selected sub-model UUID to a HuggingFace model identifier, and generates a unique request UUID for this build.

**Task 02 — Fetch Video Data:** For each video, fetches the description via YouTube Data API v3 and the transcript via `youtube-transcript-api`. Produces a list of dicts with `video_id`, `description`, and `transcript`.

**Task 03 — Build DataFrame:** Creates a pandas DataFrame with columns `video_id`, `description`, `transcript`. One row per video.

**Task 04 — Save Raw Parquet:** Saves the raw DataFrame as `video-transcripts.parquet` under the request UUID directory.

**Task 05 — Transform Data:** Cleans text by lowercasing, removing non-alphanumeric characters, and stripping 61 English stopwords. Produces new columns `description_clean`, `transcript_clean`, and `text` (the concatenation). Saves as `video-transcripts-transformed.parquet`.

**Gap:** The text cleaning regex strips all non-ASCII characters, destroying non-English text even when using the multilingual sub-model.

**Task 06 — Build Embeddings:** Downloads the SentenceTransformer model from HuggingFace, encodes all cleaned text into vectors, and saves the resulting NumPy array as `embeddings.npy`. Shape: `(N_videos, embedding_dim)`.

**Important:** Row `embeddings[i]` corresponds to `DataFrame.iloc[i]`. This alignment must be preserved.

**Task 07 — Save Model:** Saves the SentenceTransformer model directory to disk. This is the same pre-trained model that was downloaded — no weights were modified.

---

## 5. How Conversation Search Works

The search flow is implemented in `app/app_model_approaches/approach_01/conversations/facade.py` as a stateless singleton `ConversationFacade` implementing `IConversationFacade`.

**Step 1 — Resolve artefacts:** The API endpoint resolves conversation → model record → `output_results` JSON which contains paths to the model directory, embeddings file, and transformed parquet.

**Step 2 — Load and cache:** On first query, the facade loads the SentenceTransformer model (~130MB), the embeddings NumPy array, and the parquet DataFrame into memory. These are cached by model path for the lifetime of the FastAPI process.

**Step 3 — Encode query:** The user's query text is encoded into a single (1, embedding_dim) vector using the same model that created the index.

**Step 4 — Compute distances:** Using `sklearn.metrics.DistanceMetric`, the facade computes the distance between the query vector and every row in the embedding index. Result: one distance score per video.

**Step 5 — Adaptive threshold:** The effective threshold is computed as `min(user_threshold, 1.5 × mean_inter_video_distance)`. Videos scoring above this threshold are discarded.

**Step 6 — Rank and return:** Remaining videos are sorted by distance (ascending) and the top-k closest are returned with their video_id, description, thumbnail URL, and distance score.

**Caching gap:** No eviction policy exists. Loading many models accumulates memory without release.

---

## 6. SentenceTransformer: What It Is and How It Encodes Text

### Architecture

`all-MiniLM-L12-v2` is a 12-layer transformer with 33 million parameters, trained with a contrastive learning objective on 1 billion sentence pairs from the internet. Its sole purpose is to map any text into a fixed-size vector where semantically similar texts produce vectors that are close together.

### Encoding Process

When you call `model.encode("machine learning basics")`, the following happens:

1. **Tokenization:** The text is split into subword tokens using WordPiece. "machine" → "machine", "learning" → "learning", "basics" → "basics". Unknown or rare words are split into known subwords: "Kishore" → "ki" + "##shore".

2. **Token embeddings:** Each token is mapped to a learned vector (one of ~30,000 vocabulary entries).

3. **Transformer layers:** All token vectors pass through 12 self-attention + feedforward layers. Each layer allows tokens to exchange information — "machine" learns it's next to "learning" and adjusts its representation accordingly.

4. **Mean pooling:** All token-level vectors are averaged into a single 384-dimensional vector representing the entire input.

### Why "Unknown Words" Don't Exist

The WordPiece tokenizer can decompose ANY input into known subword pieces. Even complete gibberish like "asdfghjkl" gets tokenized into sub-pieces like "as", "##df", "##gh", "##j", "##kl" — each with a valid embedding. The resulting sentence vector will be generic (close to the mean of all possible vectors) but it is never null, infinite, or "not found".

This is fundamentally different from keyword search where a word either exists in the index or doesn't. In embedding space, everything has a location — the question is only how far it is from your indexed content.

### Supported Sub-Models

| Model | Parameters | Embedding Dim | Training Data | Best For |
|-------|-----------|---------------|---------------|----------|
| all-MiniLM-L12-v2 | 33M | 384 | 1B English pairs | Best quality/speed ratio for English |
| paraphrase-multilingual-MiniLM-L12-v2 | 33M | 384 | Multilingual pairs (50+ languages) | Non-English content |
| all-mpnet-base-v1 | 109M | 768 | 1B English pairs | Highest quality, 2x memory/compute |

---

## 7. Embedding Space Geometry

### Distance Properties in 384 Dimensions

In a 384-dimensional vector space, distances behave differently from intuitive 2D/3D experience:

- The expected Manhattan distance between two **random** unit vectors is approximately 15-25
- Semantically similar texts cluster at lower distances
- Semantically unrelated texts cluster at higher distances — but NOT at infinity
- The gap between "relevant" and "irrelevant" may be only 30-50% of the total range

### Real Calibration Data (from a 2-video AI engineering model)

| Query | Manhattan Distance | Relevant? |
|-------|--------------------|-----------|
| "AI engineering portfolio projects" | 13.45 | Yes — direct topic match |
| "machine learning" | 18.33 | Related but broader |
| "Kishore" (a person's name) | 20.93 | No — unrelated |
| "Telugu" (a language) | 21.28 | No — unrelated |
| "cooking recipe" | 23.39 | No — completely different domain |

The gap between the most relevant query (13.45) and the first irrelevant one (20.93) is only ~7.5 units on a ~25-unit scale. This narrow band is why threshold calibration matters enormously.

### The Small Index Problem

The number of videos directly affects how well the system can discriminate:

- **2 videos → 1 pairwise distance** — extremely narrow band, threshold must be precisely calibrated
- **10 videos → 45 pairwise distances** — wider distribution, threshold more forgiving
- **100 videos → 4,950 pairwise distances** — robust distribution, threshold easy to set
- **Recommendation:** Aim for **15+ videos** per model for reasonable search quality

---

## 8. Distance Metrics Deep Dive

The system uses `sklearn.metrics.DistanceMetric` to compute the distance between the query vector and all video vectors. The facade calls `dist.pairwise(embeddings, query_embedding)` which returns one distance score per video.

### Metric Comparison for 384-dim Sentence Embeddings

| Metric | Typical Score Range | What It Measures | Best For |
|--------|-------------------|-----------------|----------|
| **Manhattan** | 10 – 40 | Sum of absolute differences across all 384 dims | General purpose — robust, no single dim dominates |
| **Euclidean** | 0.8 – 3.0 | Straight-line distance (squares differences) | Precise matching — penalises large outlier dimensions |
| **Chebyshev** | 0.1 – 0.8 | Single largest dimension difference | Broad relevance — result must match on ALL aspects |
| **Minkowski** | 10 – 40 (varies with p) | Generalised — Manhattan at p=1, Euclidean at p=2 | Advanced experimentation between Manhattan/Euclidean |
| **Standardised Euclidean** | 0.8 – 3.0 | Euclidean scaled by per-dimension variance | When some semantic dimensions vary more than others |
| **Canberra** | 30 – 200 | Fractional differences (sensitive near zero) | Niche, highly specific searches |
| **Bray-Curtis** | 0.1 – 0.9 | Proportional dissimilarity (0-1 scale) | Comparing content "flavour" or emphasis |
| **Hamming** | 0.3 – 1.0 | Fraction of differing dimensions | Binary/categorical feature comparison |

### Why Manhattan Is the Default

1. **Robust to high dimensionality.** In 384 dims, Euclidean distance suffers from "concentration" — all points become roughly equidistant. Manhattan maintains better discrimination.
2. **No single dimension dominates.** Unlike Chebyshev, which only looks at the worst dimension, Manhattan considers all equally.
3. **Computationally efficient.** Simple absolute differences — no squares or square roots.
4. **Well-studied for NLP.** Known to perform well in information retrieval with sentence embeddings.

### When to Switch Metrics

- **Euclidean:** Videos tightly clustered on a single topic; need to distinguish subtle variations
- **Bray-Curtis:** Comparing proportions of topics discussed rather than absolute content
- **Chebyshev:** Need AND-style matching — result must be relevant across every semantic dimension
- **Canberra:** Very specialised corpus where subtle differences in rare features matter

### Critical: Different Metrics, Different Scales

A threshold of 40 is reasonable for Manhattan but meaningless for Bray-Curtis (max 1.0). The system uses adaptive thresholds to handle this — see next section.

---

## 9. Adaptive Threshold Strategy

### The Problem

A fixed threshold fails because:
1. Different metrics produce different score ranges (Manhattan ~20, Bray-Curtis ~0.3)
2. Small models have narrow distance bands where relevant and irrelevant queries are close
3. Users don't understand metric-specific scales and set inappropriate thresholds

### The Solution

The conversation facade computes the **mean distance between all video pairs** in the index, then sets the effective threshold to **1.5× that mean**. The final threshold is `min(user_threshold, adaptive_baseline)`.

This adapts automatically to the metric's natural scale, the number of videos, and the content similarity of the indexed collection.

### Why 1.5× Multiplier

- **1.0×** = only queries closer than the average inter-video distance pass → too strict, misses related content
- **1.5×** = queries up to 50% further than the average inter-video distance pass → balanced
- **2.0×** = too permissive, irrelevant queries start passing

### Example with Real Data

For a 2-video AI engineering model using Manhattan distance:
- Mean inter-video distance: 11.19
- Adaptive threshold: 11.19 × 1.5 = **16.79**
- "AI engineering portfolio" (13.80) → **passes** (relevant)
- "Kishore" (20.93) → **rejected** (irrelevant, name has nothing to do with AI)
- "cooking recipe" (23.39) → **rejected** (completely different domain)

The baseline is cached per (model_location, metric) combination to avoid recomputation.

---

## 10. Limitations and Gaps

### Fundamental Limitations

1. **No fine-tuning.** The model's understanding is frozen from pre-training. It cannot learn domain-specific jargon, acronyms, or meanings unique to your video collection. See [Section 3](#3-what-is-fine-tuning-and-why-this-approach-doesnt-do-it) for a full explanation of what fine-tuning is and why it's absent.

2. **No "unknown word" concept.** Every possible input produces a valid embedding vector at a finite distance. The system cannot distinguish "query the model doesn't understand" from "marginally related query." Both produce vectors — just at slightly different distances.

3. **Single vector per video.** A 2-hour video covering 10 topics gets one averaged embedding. Searching for a specific sub-topic that occupies 2 minutes may fail because the other 118 minutes dilute the embedding.

4. **English-only text cleaning.** The cleaning function strips all non-ASCII characters, destroying Chinese, Arabic, Hindi, Korean, and all other non-Latin text. This directly contradicts the multilingual capability of the `paraphrase-multilingual-MiniLM-L12-v2` sub-model.

5. **No semantic chunking.** Transcripts are concatenated into one long string per video. No sentence-level or paragraph-level embeddings. Research shows chunk-level embeddings significantly outperform document-level for retrieval.

6. **No re-ranking.** Results are ranked by a single distance metric. Production search systems use two stages: fast approximate retrieval followed by a cross-encoder re-ranker for precision.

7. **No query expansion.** The user's exact query is encoded as-is. No synonym expansion, spell correction, or query reformulation.

### Implementation Gaps

8. **No GPU support.** Encoding runs on CPU only. Slow for 100+ videos.

9. **No cache eviction.** Loaded models stay in memory indefinitely. Many models = unbounded memory growth.

10. **No approximate nearest neighbour (ANN).** Linear scan over all embeddings. At 100K+ videos this becomes slow. Should use FAISS, Annoy, or ScaNN.

11. **Embedding-DataFrame alignment.** `embeddings[i]` must correspond to `DataFrame.iloc[i]`. No checksum or validation exists — if either file is modified independently, search returns wrong videos silently.

12. **No incremental updates.** Adding a new video requires rebuilding the entire embedding index from scratch.

---

## 11. Best Use Cases

1. **Small curated collections (5-50 videos)** on a specific topic. The search index is focused and distance-based retrieval works well.

2. **Topic-level semantic search.** "Find me the video about backpropagation" across a playlist of ML tutorials. The model captures topic-level semantics effectively.

3. **Semantic discovery.** "What videos discuss transformer architecture?" will match videos even if they never use the word "transformer" but discuss attention mechanisms.

4. **Quick prototyping.** Build a searchable index in 1-2 minutes with no training loop, no hyperparameters, no GPU.

5. **English technical content.** The pre-trained models perform best on English, especially in technology, science, and education domains.

### Ideal User Profile

- Has 10-50 YouTube videos on a specific topic
- Wants semantic search (by meaning, not keywords)
- Doesn't need real-time indexing
- Primarily English-language content
- Accepts "good enough" retrieval without production-grade precision

---

## 12. Poor Use Cases (Anti-Patterns)

1. **Large-scale search (1000+ videos).** Linear scan is too slow. Needs ANN indexing (FAISS).

2. **Multi-language content.** Text cleaning destroys non-English text, wasting the multilingual sub-model.

3. **Domain-specific jargon.** Medical, legal, or niche technical content where the pre-trained model lacks exposure.

4. **Precise factual retrieval.** "What video mentions the number 42?" — embeddings capture semantics, not exact facts or numbers.

5. **Real-time indexing.** Every new video requires a full rebuild of `embeddings.npy`.

6. **Long-form video search.** A 3-hour conference recording gets one embedding. Searching for a 5-minute segment doesn't work.

7. **Conversational or multi-turn search.** Each query is independent. "Tell me more about what you just showed" has no context.

---

## 13. Possible Improvements (Future Work)

### Within Approach 01

1. **Fix multilingual text cleaning.** Remove the ASCII-only regex. Let the tokenizer handle text natively.
2. **Chunk-level embeddings.** Split transcripts into 5-sentence chunks, embed each separately. Return the best chunk rather than the whole video.
3. **LRU cache for models.** Evict least-recently-used models when memory exceeds a limit.
4. **Configurable baseline multiplier.** Let users tune the adaptive threshold sensitivity.
5. **Video metadata in results.** Include title, channel name, publish date from the parquet.

### New Approaches

6. **Approach 02/03 — Fine-tuned models.** Actually train on user data with contrastive learning. Requires positive/negative pairs from user feedback.
7. **Cross-encoder re-ranking.** Use a cross-encoder as a second stage to re-score the top-50 results from Approach 01.
8. **FAISS/Annoy ANN index.** Replace linear scan with approximate nearest neighbour for sub-millisecond retrieval at scale.
9. **Hybrid search.** Combine embedding similarity with BM25 keyword matching for better recall.

### Long-Term (Approach 05 — LLM)

10. **RAG (Retrieval-Augmented Generation).** Use Approach 01's embedding search to retrieve relevant chunks, then feed them to an LLM for a natural language answer.
11. **Multi-turn conversation memory.** LLM maintains context across queries.
12. **Query understanding.** LLM rewrites vague queries into precise search terms.

---

## 14. Build Artefacts Reference

All artefacts stored under `~/runtime_data/DataSets/YouTube-Search-ML-App/Approach-01/<request_uuid>/`:

| File | Pipeline Task | Shape / Contents |
|------|--------------|-----------------|
| `video-transcripts.parquet` | Task 04 | DataFrame: N_videos rows × 3 columns (video_id, description, transcript) |
| `video-transcripts-transformed.parquet` | Task 05 | DataFrame: N_videos rows × 6 columns (+ description_clean, transcript_clean, text) |
| `embeddings.npy` | Task 06 | NumPy float32 array: **(N_videos, embedding_dim)** — e.g. (20, 384) for 20 videos with 384-dim model |
| `latest/final-embedding-model/` | Task 07 | SentenceTransformer directory: config.json, tokenizer.json, model.safetensors (~130MB) |

The `ModelRecord.output_results` JSON stores all paths, the request UUID, sub-model ID, video count, sentence count, and embedding dimensionality.

---

## 15. Conversation Settings Reference

Stored in `user_conversation.settings_json`. For Approach 01, the configurable fields are:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `dist_name` | dropdown | `manhattan` | Which sklearn DistanceMetric to use |
| `threshold` | number | 40 | Maximum distance to include a result (subject to adaptive override) |
| `top_k` | number | 5 | Maximum number of results per search |

The adaptive threshold (`1.5 × mean_inter_video_distance`) is always applied as an upper bound, regardless of the user-configured threshold, to prevent false positives from mis-scaled settings. Metric-specific fallback thresholds are hardcoded in the facade for cases where the adaptive baseline cannot be computed (e.g. single-video models).
