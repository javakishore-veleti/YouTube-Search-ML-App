from fastapi import FastAPI

from app.app_common.api_initializer import APIInitializer
from app.app_model_serving.api.api_manager import ApiManager
from app.app_common.dtos.init_dtos import InitDTO

app: FastAPI = ApiManager.initialize_app()

initializer = APIInitializer()
initializer.initialize_apis(InitDTO(app=app, ctxt_data={}))
