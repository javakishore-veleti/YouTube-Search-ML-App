from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach


class Facade(IModelApproach):
    """PyTorch approach facade."""

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("PyTorch build_model not implemented yet.")

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("PyTorch evaluate not implemented yet.")

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("PyTorch publish not implemented yet.")
