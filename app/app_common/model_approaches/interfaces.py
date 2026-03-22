from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.app_common.model_approaches.dtos import ModelBuildRequest, ModelBuildResponse


class IModelApproach(ABC):
    """Interface that every model approach facade must implement."""

    @abstractmethod
    def build_model(self, req: "ModelBuildRequest") -> "ModelBuildResponse":
        ...

    @abstractmethod
    def evaluate(self, req: "ModelBuildRequest") -> "ModelBuildResponse":
        ...

    @abstractmethod
    def publish(self, req: "ModelBuildRequest") -> "ModelBuildResponse":
        ...
