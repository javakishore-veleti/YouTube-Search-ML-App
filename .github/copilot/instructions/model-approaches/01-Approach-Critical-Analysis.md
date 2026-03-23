# Approach 01 — Critical Analysis: What Went Wrong and Lessons Learned

## Purpose

This document is a post-mortem analysis of the design and implementation mistakes discovered in Approach 01 during real-world testing. Each issue is documented with what happened, why it happened, what the correct behaviour should be, and the fix applied. This serves as a learning reference for building future approaches.

---

## Table of Contents

1. [The "Custom Model" Misconception](#1-the-custom-model-misconception)
2. [Embedding-DataFrame Row Misalignment Bug](#2-embedding-dataframe-row-misalignment-bug)
3. [Fixed Threshold Fails Across Distance Metrics](#3-fixed-threshold-fails-across-distance-metrics)
4. [The 1.5x Mean Threshold Was Still Too Permissive](#4-the-15x-mean-threshold-was-still-too-permissive)
5. [No "Unknown Word" Rejection — The "STUPID" Problem](#5-no-unknown-word-rejection--the-stupid-problem)
6. [Videos Without Transcripts Were Silently Included](#6-videos-without-transcripts-were-silently-included)
7. [English-Only Text Cleaning With a Multilingual Model](#7-english-only-text-cleaning-with-a-multilingual-model)
8. [No Content Quality Metrics Were Captured](#8-no-content-quality-metrics-were-captured)
9. [Model Artefacts Stored in Separate Directory Trees](#9-model-artefacts-stored-in-separate-directory-trees)
10. [Session Detachment After Close (SQLAlchemy)](#10-session-detachment-after-close-sqlalchemy)
11. [Dashboard Stats Never Updated After Build](#11-dashboard-stats-never-updated-after-build)
12. [Summary of Root Causes](#12-summary-of-root-causes)

---

## 1. The "Custom Model" Misconception

### What Happened

The system was presented to users as "building a custom embedding model" — implying that the AI learns from the selected videos. Users expected that searching for words not present in their videos would return "not found." Instead, every query — including completely irrelevant terms like "Kishore", "Telugu", "STUPID" — returned results with finite distance scores.

### Why It Happened

Approach 01 does NOT fine-tune or retrain the neural network. The pipeline:
1. Downloads a pre-trained SentenceTransformer from HuggingFace (33 million parameters, trained on 1 billion sentence pairs from the internet)
2. Uses it to encode video transcripts into vectors
3. Saves the exact same unchanged model to disk

The model already knows virtually every word in every language. "Building a custom model" actually means "building a custom search index" — the model's understanding is frozen from pre-training.

### What Should Have Been Clear

- The model is a universal encoder. It does not learn from your videos.
- Your videos define the INDEX (what to search against), not the VOCABULARY.
- Every possible input produces a valid vector. There is no "word not found."
- The only mechanism to filter irrelevant queries is distance thresholding.

### The Correct Mental Model

Think of a library: the SentenceTransformer is a librarian who can read every book in every language. Your "custom model" is the specific collection of books you place on the shelves. The librarian's reading ability doesn't change — you only control which books are available.

### Fix Applied

Added detailed documentation in the About page, implementation guide, and conversation settings explaining this distinction. The term "custom model" is retained but with explicit caveats.

### Lesson for Future Approaches

If Approach 02/03 claims "fine-tuning," it must actually modify model weights using a training loop with loss functions. Otherwise, clearly label it as "index construction" not "model training."

---

## 2. Embedding-DataFrame Row Misalignment Bug

### What Happened

A model built from 19 videos produced an embedding index with only 17 rows, while the DataFrame (parquet) had 19 rows. Search results for indices 11 and above returned the wrong video.

### Why It Happened

Two of the 19 selected videos had no transcript AND no description (video IDs `0B0RES6UhaM` and `H3rIoiKJ6fs`). The pipeline handled this inconsistently:

- **Task 05 (Transform Data):** Saved ALL 19 rows to the parquet, including 2 rows with empty `text` column
- **Task 06 (Build Embeddings):** Filtered to non-empty text before encoding: `[s for s in df["text"] if s.strip()]` → 17 sentences → 17 embeddings

This created a mismatch: `embeddings[11]` corresponded to `df.iloc[12]` (not `df.iloc[11]`), because Task 06 skipped row 11 (empty) but the DataFrame didn't. Every result from index 11 onward pointed to the wrong video.

### What Should Have Happened

The parquet and embeddings must ALWAYS have the same number of rows in the same order. Either:
- (A) Task 05 should drop empty rows before saving, OR
- (B) Task 06 should encode ALL rows including empty ones, OR
- (C) A validation check should catch the mismatch

Option (A) is correct — empty rows are useless for search and should not exist in the index.

### Fix Applied

**Build-time (Task 05):** Now drops rows with empty `text` before saving the parquet. If 2 out of 19 videos have no content, the parquet has 17 rows, matching the 17 embeddings Task 06 will produce.

**Search-time (Facade):** As a safety net for models built before the fix, the facade filters the DataFrame on load to align with the embeddings array.

### Lesson for Future Approaches

Any pipeline that saves data in two separate files (DataFrame + embeddings) with an implicit row-order dependency must either:
- Use a shared row identifier (e.g., store video_id alongside each embedding)
- Validate alignment at save time with an assertion
- Use a single file format that keeps both together (e.g., embed vectors as DataFrame columns)

---

## 3. Fixed Threshold Fails Across Distance Metrics

### What Happened

A user configured Bray-Curtis distance with a threshold of 10. The search returned results for completely irrelevant queries ("Telugu") with scores like 0.69 — because Bray-Curtis produces scores between 0 and 1, and `0.69 < 10` is always true.

### Why It Happened

The system used a single user-configurable threshold with no awareness that different distance metrics operate on completely different numerical scales:

| Metric | Score Range | Reasonable Threshold |
|--------|-----------|---------------------|
| Manhattan | 0 – 200+ | 15 – 40 |
| Euclidean | 0 – 50+ | 4 – 10 |
| Bray-Curtis | 0 – 1 | 0.1 – 0.3 |
| Chebyshev | 0 – 2+ | 0.3 – 0.8 |

A threshold of 10 is meaningless for Bray-Curtis (maximum possible score is 1.0) but reasonable for Euclidean.

### What Should Have Happened

The system should either:
- (A) Present metric-specific threshold ranges to the user, OR
- (B) Automatically detect and correct mis-scaled thresholds, OR
- (C) Use a metric-agnostic relevance measure (like percentile-based)

### Fix Applied

Implemented adaptive thresholding using the 20th percentile of inter-video pairwise distances. This auto-calibrates to any metric's natural scale. The user's threshold is respected only if it's stricter than the adaptive baseline.

### Lesson for Future Approaches

Never expose a raw numerical threshold without context about its valid range. Either normalise all metrics to a common scale (0-1), or compute adaptive thresholds from the data itself.

---

## 4. The 1.5x Mean Threshold Was Still Too Permissive

### What Happened

After fixing the Bray-Curtis issue with adaptive thresholds, the first adaptive strategy used `1.5 × mean_inter_video_distance`. For a 17-video model with Manhattan distance, this produced a threshold of 26.43. ALL queries — including "STUPID" (20.40), "Kishore" (20.09), "cooking recipe" (20.19) — passed the threshold.

### Why It Happened

The mean inter-video distance was 17.62, and 1.5× that = 26.43. With a diverse 17-video collection, the distance range was wide (8.7 to 22.8), and the multiplier-based threshold was far too generous. The problem is that the mean is sensitive to outliers — a few very dissimilar video pairs pull the mean up, inflating the threshold.

### What the Data Actually Showed

| Query | Manhattan Distance | Relevant? |
|-------|--------------------|-----------|
| "AI engineering" | 13.61 | Yes |
| "machine learning" | 16.48 | Borderline |
| "STUPID" | 20.40 | No |
| "Kishore" | 20.09 | No |
| "cooking recipe" | 20.19 | No |

The correct threshold needed to be ~16 to separate relevant from irrelevant. The 20th percentile of inter-video distances (15.89) achieved this perfectly.

### Fix Applied

Replaced `1.5 × mean` with `percentile(inter_video_distances, 20)`. This means: a query must be closer than 80% of video-to-video distances to be considered relevant. This is robust to outliers, adapts to any metric, and scales correctly with collection size.

### Lesson for Future Approaches

Multiplier-based thresholds are fragile because they depend on a single statistic (mean) that may not represent the distribution well. Percentile-based thresholds are more robust because they directly capture the shape of the distance distribution.

---

## 5. No "Unknown Word" Rejection — The "STUPID" Problem

### What Happened

Searching "STUPID" against an AI engineering video collection returned results with score 20.40. The user expected zero results because "STUPID" has nothing to do with AI engineering.

### Why It Happened

SentenceTransformer uses WordPiece subword tokenization. Every possible input — including gibberish, profanity, random characters — gets decomposed into known subword tokens and produces a valid 384-dimensional vector. There is no "out of vocabulary" error. The vector for "STUPID" exists in the same continuous 384-dimensional space as "machine learning" — just at a different location.

In a 384-dimensional space, the distance between any two random vectors is surprisingly bounded. "STUPID" scored 20.40 while "AI engineering" scored 13.61 — a gap of only 6.8 units. Without a well-calibrated threshold, this gap is invisible.

### What Should Have Happened

The system should recognise that a query is semantically distant from ALL indexed content and return zero results. This requires:
- An adaptive threshold that understands the model's distance distribution (now implemented)
- Possibly a "confidence score" that normalises raw distance into a 0-1 relevance scale

### Fix Applied

The percentile-based adaptive threshold (p20 = 15.89) correctly rejects "STUPID" (20.40 > 15.89). However, there is still no explicit "query is unrelated" detection — it relies entirely on the distance being above threshold.

### Lesson for Future Approaches

Embedding models will ALWAYS produce a finite distance for ANY input. This is a fundamental property, not a bug. Any retrieval system built on embeddings must have robust threshold logic. Consider adding:
- A normalised relevance score (distance relative to the index's distance distribution)
- An explicit "no relevant results" message when all distances exceed the baseline
- Query-index similarity statistics returned alongside results

---

## 6. Videos Without Transcripts Were Silently Included

### What Happened

Users could select any YouTube video for model building, including videos with no captions and no meaningful description. These videos produced empty text after cleaning, created zero-value embeddings (or were skipped, causing the alignment bug in Issue #2), and degraded search quality.

### Why It Happened

The YouTube Data API `search` endpoint returns all videos regardless of caption availability. The build pipeline fetched whatever was available and only logged warnings when transcripts were missing — it didn't exclude these videos from the index.

### What Should Have Happened

Two layers of defence:
1. **At search time:** Only show videos with closed captions in the YouTube search results
2. **At build time:** Track content quality and warn/skip videos with no usable content

### Fix Applied

**YouTube search filter:** Added `videoCaption=closedCaption` to the API search params, so only videos with captions appear in search results.

**Task 05 filter:** Now drops rows with empty text before saving the parquet, with a log warning.

**Content stats:** Task 02 now computes and stores metrics: how many videos have descriptions, how many have transcripts, how many have both, how many have neither, min/max lengths, and which video IDs were skipped. This is persisted in `ModelRecord.output_results.content_stats`.

### Lesson for Future Approaches

Never assume input data is clean. Every pipeline should:
- Validate inputs before processing
- Track data quality metrics
- Exclude or flag low-quality inputs explicitly
- Surface quality issues to the user (not just log them)

---

## 7. English-Only Text Cleaning With a Multilingual Model

### What Happened

The text cleaning function uses `re.sub(r"[^a-z0-9\s]", " ", text)` which strips ALL non-ASCII characters. This destroys Chinese, Arabic, Hindi, Korean, Japanese, and every other non-Latin script. Yet one of the available sub-models is `paraphrase-multilingual-MiniLM-L12-v2`, which supports 50+ languages.

### Why It Happened

The cleaning function was written assuming English-only content. The regex was designed to remove punctuation and special characters but inadvertently removes all non-Latin characters because they fall outside `a-z`.

### What Should Happen

The cleaning function should:
- Preserve Unicode letters from all scripts
- Only remove actual punctuation and control characters
- Use `\w` (word characters) instead of `[a-z0-9]`, or better yet, use the tokenizer's built-in preprocessing

### Fix Status

Not yet fixed. Documented as a known limitation. The fix is straightforward: replace `[^a-z0-9\s]` with a Unicode-aware pattern like `[^\w\s]` or delegate text normalisation to the SentenceTransformer tokenizer which handles all languages correctly.

### Lesson for Future Approaches

If a system supports multilingual models, every stage of the pipeline must be multilingual — not just the model. Text cleaning, stopword removal, tokenization, and display must all handle Unicode correctly. Test with non-English content early.

---

## 8. No Content Quality Metrics Were Captured

### What Happened

After building a model, the user had no visibility into whether the indexed videos actually had usable content. The model metadata only stored: video count, sentence count, embedding dimensions, and file paths. There was no way to know that 2 out of 19 videos had no transcript, or that some descriptions were only 3 characters long.

### Why It Happened

The pipeline focused on the happy path — process data, build embeddings, save model. Data quality tracking was not considered part of the build output.

### What Should Have Happened

The model metadata should include a `content_stats` section showing:
- How many videos had descriptions vs. didn't
- How many videos had transcripts vs. didn't
- How many had both (ideal) vs. neither (useless)
- Min/max character lengths for descriptions and transcripts
- Which specific video IDs were skipped due to no content

### Fix Applied

Task 02 now computes all of the above and stores it in `ctx["content_stats"]`. The facade includes it in `output_results.content_stats`, persisted in the model record's JSON metadata.

### Lesson for Future Approaches

Every ML pipeline should emit data quality metrics alongside its primary output. These metrics are essential for debugging, user trust, and identifying when a model's training data is too sparse or noisy to be useful.

---

## 9. Model Artefacts Stored in Separate Directory Trees

### What Happened

Initially, intermediate files (parquets, embeddings) were stored under `~/runtime_data/DataSets/YouTube-Search-ML-App/Approach-01/<uuid>/` while the final model was stored under `~/runtime_data/Models/YouTube-Search-ML-App/Approach-01/<uuid>/final-embedding-model/`. This split made it difficult to manage, backup, or delete a complete model build.

### Why It Happened

The directory structure was designed with a conceptual separation between "datasets" and "models." In practice, the embeddings and parquet files are just as much part of the model as the SentenceTransformer weights — they're all needed for search.

### Fix Applied

Moved the model directory to `~/runtime_data/DataSets/YouTube-Search-ML-App/Approach-01/<uuid>/latest/final-embedding-model/` so all artefacts for a build live under one UUID directory.

### Lesson for Future Approaches

All artefacts from a single build should live under one directory. Use a flat structure where the UUID directory is the complete, self-contained unit that can be copied, archived, or deleted atomically.

---

## 10. Session Detachment After Close (SQLAlchemy)

### What Happened

The queue scheduler crashed with `Instance <ModelRecord> is not bound to a Session` when trying to access `record.id` and `record.latest_version` after calling `session.close()`.

### Why It Happened

SQLAlchemy ORM objects are bound to the session that loaded them. Once `session.close()` is called, accessing any attribute on the ORM object triggers a lazy-load attempt which fails because there's no session. The code was:

1. Create model record via session
2. Close session
3. Access `record.id` — fails because `record` is now detached

### Fix Applied

Captured scalar values (`record_id = record.id`, `version_row_id = version_row.id`) before closing the session, then used those plain integers throughout the rest of the method.

### Lesson for Future Approaches

Never access SQLAlchemy ORM objects after closing their session. Always capture scalar values (ints, strings) before close. Alternatively, use `session.expunge(obj)` to detach the object while keeping its loaded attributes, or use `expire_on_commit=False` on the session factory.

---

## 11. Dashboard Stats Never Updated After Build

### What Happened

The admin dashboard always showed "Models Built: 0" and "Last Build: —" even after successfully building models through the queue.

### Why It Happened

`AppStatus` initialises `models_built: 0` and `last_build: None` at startup. The queue scheduler logged activity to the database and marked queue items as completed, but never called `set_status()` to update the in-memory status counters.

### Fix Applied

Added two lines after `q_repo.mark_completed(item.id)` in the scheduler's `_tick()` method to increment the counter and set the timestamp.

### Lesson for Future Approaches

In-memory status registries must be updated by every code path that changes the state they represent. If a status is derived from database state, consider computing it from DB queries rather than maintaining a separate in-memory counter that can fall out of sync.

---

## 12. Summary of Root Causes

Looking across all 11 issues, four root causes account for most of the problems:

### A. Implicit Assumptions Not Validated

The embedding-DataFrame alignment (Issue #2), session detachment (Issue #10), and content quality (Issues #6, #8) all share a pattern: the code assumed something was true without checking. Embeddings assumed row alignment. The scheduler assumed ORM objects were accessible after session close. The pipeline assumed all videos had usable content.

**Principle:** Assert your assumptions. If `embeddings.shape[0]` must equal `len(df)`, check it. If a video must have a transcript, validate before including it.

### B. Single Number for Multi-Scale Problem

The threshold issues (Issues #3, #4) stem from using one number (threshold = 40) to gate a multi-scale system. Different metrics, different collection sizes, and different content domains all produce different distance distributions. A single fixed number cannot work across all combinations.

**Principle:** When a parameter's valid range depends on other variables, compute it from the data rather than hardcoding it. Use adaptive, data-driven defaults.

### C. Missing Feedback Loops

The "unknown word" problem (Issue #5), the "STUPID" problem, and the content quality gap (Issue #8) all share a pattern: the system produced output without telling the user whether that output was reliable. No confidence score. No content quality warning. No "your query is unrelated to the index" message.

**Principle:** Every ML system should communicate uncertainty. If results are low-confidence, say so. If input data is sparse, warn the user. Never present results without context about their reliability.

### D. Naming Misrepresents Capability

The "custom model" misconception (Issue #1) and the multilingual cleaning bug (Issue #7) both stem from the system's naming overpromising what it delivers. Calling it a "custom model" implies training. Offering a multilingual sub-model implies multilingual support.

**Principle:** Name things honestly. "Custom Video Search Index" is more accurate than "Custom Embedding Model." If a feature isn't fully implemented (multilingual cleaning), don't offer the option that implies it works.
