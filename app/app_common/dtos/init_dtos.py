from dataclasses import dataclass, field
from typing import Any, Dict

from fastapi import FastAPI


@dataclass
class InitDTO:
    app: FastAPI
    ctxt_data: Dict[str, Any] = field(default_factory=dict)
