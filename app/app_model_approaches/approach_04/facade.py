from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach


class Facade(IModelApproach):
    """AWS SageMaker approach facade."""

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("SageMaker build_model not implemented yet.")

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("SageMaker evaluate not implemented yet.")

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("SageMaker publish not implemented yet.")
