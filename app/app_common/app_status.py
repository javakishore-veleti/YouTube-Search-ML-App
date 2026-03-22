"""
app_status.py
=============
AppStatus is a singleton in-memory registry that any module can write to
and the dashboard reads instantly.  No filesystem I/O, no external calls.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class AppStatus:
    """
    Singleton in-memory status registry.

    Usage
    -----
      AppStatus.instance().set("db_initialized", True)
      status = AppStatus.instance().get()
    """

    _instance: Optional["AppStatus"] = None
    _initialised: bool = False

    def __new__(cls) -> "AppStatus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        self._store: Dict[str, Any] = {
            "app_name":           "VidSage",
            "started_at":         datetime.now(timezone.utc).isoformat(),
            "models_built":       0,
            "last_build":         None,
            "builder_status":     "idle",
            "active_approach":    None,
            "api_key_configured": False,
            "db_initialized":     False,
        }

    @classmethod
    def instance(cls) -> "AppStatus":
        return cls()

    def get(self) -> Dict[str, Any]:
        """Return a shallow copy of the current status dict."""
        return dict(self._store)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def update(self, updates: Dict[str, Any]) -> None:
        self._store.update(updates)


# ---------------------------------------------------------------------------
# Module-level shims — existing call sites unchanged.
# ---------------------------------------------------------------------------
def get_status() -> Dict[str, Any]:
    return AppStatus.instance().get()


def set_status(key: str, value: Any) -> None:
    AppStatus.instance().set(key, value)


def update_status(updates: Dict[str, Any]) -> None:
    AppStatus.instance().update(updates)
