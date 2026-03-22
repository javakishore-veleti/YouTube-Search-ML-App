"""
Global application status registry.
A simple in-memory dict that any module can write to and the dashboard reads instantly.
No filesystem scanning, no external calls — just a dict.
"""

from datetime import datetime, timezone
from typing import Any, Dict

_status: Dict[str, Any] = {
    "app_name": "YouTube Search ML App",
    "started_at": datetime.now(timezone.utc).isoformat(),
    "models_built": 0,
    "last_build": None,
    "builder_status": "idle",
    "active_approach": None,
    "api_key_configured": False,
    "db_initialized": False,
}


def get_status() -> Dict[str, Any]:
    return dict(_status)


def set_status(key: str, value: Any) -> None:
    _status[key] = value


def update_status(updates: Dict[str, Any]) -> None:
    _status.update(updates)
