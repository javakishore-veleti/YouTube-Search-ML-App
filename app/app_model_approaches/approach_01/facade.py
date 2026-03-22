from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse
from app.app_common.model_approaches.interfaces import IModelApproach


class Facade(IModelApproach):
    """Classical ML (scikit-learn) approach facade."""

    def build_model(self, req: ModelBuildRequest) -> ModelBuildResponse:
        # TODO: implement classical ML model building
        raise NotImplementedError("Classical ML build_model not implemented yet.")

    def evaluate(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("Classical ML evaluate not implemented yet.")

    def publish(self, req: ModelBuildRequest) -> ModelBuildResponse:
        raise NotImplementedError("Classical ML publish not implemented yet.")
