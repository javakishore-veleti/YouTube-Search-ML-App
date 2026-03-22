from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach


class Facade(IModelApproach):
    """Large Language Model (LLM) approach facade."""

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("LLM build_model not implemented yet.")

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("LLM evaluate not implemented yet.")

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("LLM publish not implemented yet.")
