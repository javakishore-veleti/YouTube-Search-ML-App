# Model Approaches - Approach 01 - Building Custom Embedding Model 
 
## Introduction
- Model Unique ID: e1cffc4f-d00d-4b04-b705-18eef34e10d2
- Model Identification: Approach-01
- Model Category: Embedding Models
- Model Name: Approach 01 - Building Custom Embedding Model
- Model Implementation Location In This Codebase: app/app_model_approaches/approach_01 
  - Ensure the implemnentation follows Facade and interfaces already definedin in the codebase for model approaches
  - Also insert a row in approaches.json
- Description: 
  - This approach focuses on building a custom embedding model to generate vector representations of text data. 
  - The model will be trained on input videos selected by the user and their descriptoins
- Model Approach Backed: 
  - Input:
    - User-selected videos from the YouTube channel
      - User can select one or more videos from the channel to be used as training data for the embedding model.
    - Descriptions of the selected videos

      - Model Approach Pipeline Logic:
        - Implemenet as a Python class in Workflow and tasks approach defined in the codebase for model approaches
        - Facade -> Workflow -> Tasks
        - Facade, Workflow and Task(s) should be python classes with right interfaces as defined in the codebase for model approaches
        - interfaces are defined in app_common python module
        - Dont maintain state at the class levels, pass all the required data as parameters to the methods and functions
        - Make Facade, Workflow and Tasks as stateless always and also singleton classes
        - Step 01: Get list of Video Ids from the user selcted videos request
        - Step 02: For each video Id, fetch the video description and VideoTranscripts using YouTube Data API 
          - as a dict with keys as description and trnascript
        - Step 3: Create a dataframe from the above dict with columns as video id, description and transcript
        - Step 4: Create a parquest file in 
          - user_home/runtime_data/DataSets/YouTube-Search-ML-App/Approach-01/<Model Request UUID string>/video-transcripts.parquet
          - Note that this parquet is nothing but the dataframe with multiple rows (each row represented one video user selcted) created in step 3 stored in parquet format for faster read/write and better performance.
            - Overwrite if already exists
          - Store this location in the model request table which is already created for status traicking
        - Step 5: Use the above parquet file to transform the data by handling the special characters, removing stop words and then generate embeddings using a pre-trained language model like BERT or Word2Vec.
          - Store the resulted transformation as video-transcripts-transformed.parquet in the same location as above
        - Step 6: Use the transformed data to create a custom embedding model using Hugging Face's SentenceTransformer library 
          - User can select one of the pre-trained models available in the library as the base model for fine-tuning.
            - paraphrase-multilingual-MiniLM-L12-v2
              - id in approaches.json is -> 5f96a19d-6066-468f-bb30-112159cb49a6
              - This is a sentence-transformers model: It maps sentences & paragraphs to a 384 dimensional dense vector space and can be used for tasks like clustering or semantic search.
            - all-MiniLM-L12-v2
              - id in approaches.json is -> 7ae50b73-33a7-4586-a98d-8b49e469dafa
              - his is a sentence-transformers model: It maps sentences & paragraphs to a 384 dimensional dense vector space and can be used for tasks like clustering or semantic search.
            - all-mpnet-base-v1
              - id in approaches.json is -> 39b9a4c4-f61a-402a-a9fa-590b98e3794b
              - This is a sentence-transformers model: It maps sentences & paragraphs to a 768 dimensional dense vector space and can be used for tasks like clustering or semantic search.
              ```text
              from sentence_transformers import SentenceTransformer
              sentences = ["This is an example sentence", "Each sentence is converted"]
        
              model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
              embeddings = model.encode(sentences)
              print(embeddings)
        
                ``` 
        - Step 7: Store the fine-tuned custom embedding model in a location like 
          - user_home/runtime_data/Models/YouTube-Search-ML-App/Approach-01/<Model Request UUID string>/final-embedding-model
          - Store this location in the model request table for future reference and use.
          - Generate an UUID string for this model request and store it in the model request table for future reference and tracking.
          - Also store it in the model_approaches table which Python api will use to show in the UI

---

## Build Artefacts Summary

After a successful build, the following artefacts exist under
`~/runtime_data/DataSets/YouTube-Search-ML-App/Approach-01/<request_uuid>/`:

| File | Created By | Contents |
|------|-----------|----------|
| `video-transcripts.parquet` | Task 04 | Raw DataFrame — columns: `video_id`, `description`, `transcript` |
| `video-transcripts-transformed.parquet` | Task 05 | Cleaned DataFrame — adds: `description_clean`, `transcript_clean`, `text` |
| `embeddings.npy` | Task 06 | Numpy array shape `(sentence_count, embedding_dim)` — one embedding per row in the DataFrame |
| `latest/final-embedding-model/` | Task 07 | Full SentenceTransformer model directory (config, tokenizer, weights) |

The `ModelRecord.output_results` JSON stores all artefact paths:
```json
{
  "request_uuid": "<uuid>",
  "base_model_key": "<sub-model uuid>",
  "base_model_id": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "video_count": 5,
  "sentence_count": 5,
  "embedding_dim": 384,
  "raw_parquet": "/path/to/video-transcripts.parquet",
  "transformed_parquet": "/path/to/video-transcripts-transformed.parquet",
  "embeddings_path": "/path/to/embeddings.npy",
  "model_location": "/path/to/latest/final-embedding-model"
}
```

---

## Workflow DB Tracking

Every build run creates:
- One `model_build_wf` row (parent) — links to `model_id`, `queue_item_id`, tracks status + timing
- One `model_build_wf_task` row per task (child) — tracks task_id (Python class name), task_file, task_order, status, timing, and `output_data` JSON capturing new/changed context keys after each task

Status values: `started` → `running` → `completed` | `failed`
Task status values: `pending` → `started` → `completed` | `failed` | `skipped`

Implementation: `app/app_model_approaches/approach_01/workflow.py` — `BuildEmbeddingModelWorkflow` class
The `_extract_output()` helper captures serialisable ctx diffs (skips DataFrames, model objects, private `_` keys).

---

## Conversation Search (Inference)

### Architecture

Each approach has a `conversations/` sub-module implementing `IConversationFacade`:
- Interface: `app/app_common/model_approaches/interfaces.py` → `IConversationFacade`
- DTOs: `app/app_common/model_approaches/dtos.py` → `ConversationSearchRequest`, `ConversationSearchResponse`
- Approach 01 impl: `app/app_model_approaches/approach_01/conversations/facade.py` → `ConversationFacade`
- Loader: `app/app_model_approaches/__init__.py` → `get_conversation_facade(approach_id)`

### How It Works

1. User sends a query from the conversation detail page (`POST /conversations/{id}/search`)
2. Backend resolves: `conversation.model_id` → `ModelRecord` → `output_results` (artefact paths) + `model_approach_type`
3. `get_conversation_facade(approach_type)` dynamically imports `approach_01.conversations.facade.ConversationFacade`
4. A `ConversationSearchRequest` is built with query, artefact paths, and conversation settings (dist_name, threshold, top_k)
5. The facade executes the search and returns ranked results

### Search Algorithm

```text
1. Load artefacts (lazily cached in memory per model_location):
   - SentenceTransformer model from model_location
   - Embeddings numpy array from embeddings_path
   - Transformed DataFrame from transformed_parquet

2. Encode query:
   query_embedding = model.encode(query).reshape(1, -1)

3. Compute distances:
   dist = DistanceMetric.get_metric(dist_name)   # default: "manhattan"
   dist_arr = dist.pairwise(embeddings, query_embedding).flatten()

4. Filter and rank:
   idx_below = argwhere(dist_arr < threshold)     # default threshold: 40.0
   idx_sorted = idx_below[argsort(dist_arr[idx_below])][:top_k]  # default top_k: 5

5. Return matching rows from DataFrame (video_id, description, thumbnail URL, score)
```

### Distance Metrics

The `dist_name` setting on each conversation controls which sklearn `DistanceMetric` is used. Supported metrics for real-valued vectors:

| Identifier | Class | Formula |
|-----------|-------|---------|
| `"manhattan"` (default) | ManhattanDistance | `sum(\|x - y\|)` |
| `"euclidean"` | EuclideanDistance | `sqrt(sum((x - y)^2))` |
| `"chebyshev"` | ChebyshevDistance | `max(\|x - y\|)` |
| `"minkowski"` | MinkowskiDistance | `sum(w * \|x - y\|^p)^(1/p)` |
| `"cosine"` | Not in DistanceMetric — use `scipy` or `1 - cosine_similarity` instead |

Manhattan distance is the default because it works well with high-dimensional sentence embeddings and is computationally efficient.

### Conversation Settings

Stored in `user_conversation.settings_json` (default `{}`):
```json
{
  "dist_name": "manhattan",
  "threshold": 40.0,
  "top_k": 5
}
```

These are per-conversation overrides. If not set, the facade uses the defaults above.

### Caching

The `ConversationFacade` caches loaded models, embeddings, and DataFrames in a class-level dict keyed by `model_location`. This means:
- First query for a model is slow (loads ~130MB SentenceTransformer + embeddings + parquet)
- Subsequent queries against the same model are fast (in-memory lookup + encode + distance compute)
- Cache persists for the lifetime of the FastAPI process

### API Endpoint

```
POST /conversations/{id}/search
Body: { "query": "how to train a neural network" }
Response: {
  "results": [
    {
      "title": "...",
      "video_id": "abc123",
      "description": "...",
      "channel": "",
      "thumbnail": "https://img.youtube.com/vi/abc123/mqdefault.jpg",
      "score": 12.45
    }
  ],
  "query": "how to train a neural network",
  "status": "ok"
}
```

### Adding Conversation Search to a New Approach

To add conversation search for approach_02 (or any new approach):

1. Create `app/app_model_approaches/approach_02/conversations/__init__.py` (empty)
2. Create `app/app_model_approaches/approach_02/conversations/facade.py`:
   - Class `ConversationFacade` implementing `IConversationFacade`
   - Stateless singleton pattern (same as approach_01)
   - Implement `search(req: ConversationSearchRequest) -> ConversationSearchResponse`
3. The loader `get_conversation_facade()` will automatically discover it via the `package` field in `approaches.json`
                    