from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach


class Facade(IModelApproach):
    """TensorFlow / Keras approach facade."""

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("TensorFlow build_model not implemented yet.")

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("TensorFlow evaluate not implemented yet.")

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("TensorFlow publish not implemented yet.")
