from typing import Any, List

from app.app_common.cache.mem_cache import MemoryCache
from app.app_common.database.db_engine import SessionLocal
from app.app_common.database.db_repo import ModelRepository

_CACHE_KEY = "published_models"
_TTL_SECONDS = 60


class ModelListCache:
    """
    Singleton cache for published model list.
    Avoids hitting SQLite on every request from the youtube-search portal.
    """

    _instance = None

    def __new__(cls) -> "ModelListCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = MemoryCache()
        return cls._instance

    def get_models(self) -> List[dict]:
        cached = self._cache.get(_CACHE_KEY)
        if cached is not None:
            return cached

        session = SessionLocal()
        try:
            repo = ModelRepository(session)
            records = repo.list_models()
            models = [r.to_dict() for r in records]
            self._cache.set(_CACHE_KEY, models, ttl_seconds=_TTL_SECONDS)
            return models
        finally:
            session.close()

    def invalidate(self) -> None:
        self._cache.invalidate(_CACHE_KEY)
