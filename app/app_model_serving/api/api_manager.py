from fastapi import FastAPI

__api_manager_instance = None

class ApiManager:
    def __init__(self):
        self.api_endpoints = {}
        self.app: FastAPI = None

    def register_endpoint(self, endpoint_name, handler):
        self.api_endpoints[endpoint_name] = handler

    def get_handler(self, endpoint_name):
        return self.api_endpoints.get(endpoint_name)

    def list_endpoints(self):
        return list(self.api_endpoints.keys())

    @staticmethod
    def initialize_app() -> FastAPI:
        api_manager_instance:ApiManager = None
        if __api_manager_instance is None:
            global __api_manager_instance
            __api_manager_instance = ApiManager()
            api_manager_instance = __api_manager_instance
        else:
            api_manager_instance = __api_manager_instance

        app = FastAPI()
        api_manager_instance.app = app
        return app

    @staticmethod
    def get_flask_app() -> FastAPI:
        api_manager_instance:ApiManager = None
        if __api_manager_instance is None:
            global __api_manager_instance
            __api_manager_instance = ApiManager()
            api_manager_instance = __api_manager_instance
        else:
            api_manager_instance = __api_manager_instance

        return api_manager_instance.app
