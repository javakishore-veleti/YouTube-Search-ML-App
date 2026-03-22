import time
from typing import Any, Optional


class MemoryCache:
    """Simple in-memory key-value cache with TTL support."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds if ttl_seconds > 0 else None,
        }

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
