from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from app.app_common.model_approaches.dtos import (
        ModelBuildRequest, ModelBuildResponse,
        ConversationSearchRequest, ConversationSearchResponse,
    )


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


class IModelWorkflow(ABC):
    """
    Interface for a model-approach workflow.
    A workflow orchestrates one or more IModelTask instances in sequence.
    Implementations must be stateless singletons.
    """

    @abstractmethod
    def run(self, req: "ModelBuildRequest", ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full workflow.

        Parameters
        ----------
        req : ModelBuildRequest  – the original build request.
        ctx : dict               – mutable context bag shared across tasks.

        Returns
        -------
        dict – the final populated context bag.
        """
        ...


class IConversationFacade(ABC):
    """
    Interface for conversation search within an approach.
    Implementations must be stateless singletons.
    """

    @abstractmethod
    def search(self, req: "ConversationSearchRequest") -> "ConversationSearchResponse":
        ...


class IModelTask(ABC):
    """
    Interface for a single, atomic pipeline step.
    Implementations must be stateless singletons.
    """

    @abstractmethod
    def execute(self, req: "ModelBuildRequest", ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute this task step.

        Parameters
        ----------
        req : ModelBuildRequest  – the original build request (read-only).
        ctx : dict               – mutable context bag; read inputs from and
                                   write outputs into this dict.

        Returns
        -------
        dict – the updated context bag.
        """
        ...
