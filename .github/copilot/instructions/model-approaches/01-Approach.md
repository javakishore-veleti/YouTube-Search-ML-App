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
                    