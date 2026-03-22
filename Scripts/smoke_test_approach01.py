"""Quick smoke-test: imports, singleton and interface checks for approach_01."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.app_model_approaches.approach_01.tasks import Task01ExtractVideoIds, Task07SaveModel
from app.app_model_approaches.approach_01.workflow import BuildEmbeddingModelWorkflow
from app.app_model_approaches.approach_01.facade import Facade
from app.app_common.model_approaches.interfaces import IModelApproach, IModelWorkflow, IModelTask

# Singleton checks
assert Facade() is Facade(), "Facade is not a singleton"
assert BuildEmbeddingModelWorkflow() is BuildEmbeddingModelWorkflow(), "Workflow is not a singleton"
assert Task01ExtractVideoIds() is Task01ExtractVideoIds(), "Task01 is not a singleton"
assert Task07SaveModel() is Task07SaveModel(), "Task07 is not a singleton"

# Interface hierarchy checks
assert isinstance(Facade(), IModelApproach), "Facade does not implement IModelApproach"
assert isinstance(BuildEmbeddingModelWorkflow(), IModelWorkflow), "Workflow does not implement IModelWorkflow"
assert isinstance(Task01ExtractVideoIds(), IModelTask), "Task01 does not implement IModelTask"

print("✓ All smoke-test checks passed.")
