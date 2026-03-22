from app.app_common.cache.model_cache import ModelListCache
from app.app_common.dtos.init_dtos import InitDTO


class ModelsAPI:
    """Serves published model list from cache for the youtube-search portal."""

    def __init__(self) -> None:
        self.cache = ModelListCache()

    def list_models(self) -> list:
        return self.cache.get_models()


def initialize(dto: InitDTO) -> None:
    handler = ModelsAPI()
    dto.app.add_api_route("/models", endpoint=handler.list_models, methods=["GET"])
