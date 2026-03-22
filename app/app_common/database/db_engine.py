"""
db_engine.py
============
DatabaseEngine is a singleton that builds and owns the SQLAlchemy engine.
DATABASE_URL is resolved via SecretsResolver — SQLite by default, any
dialect (Postgres, MySQL, Aurora RDS) via the DATABASE_URL env var.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.app_common.config.secrets_resolver import resolve_secrets


class DatabaseEngine:
    """
    Singleton that holds the SQLAlchemy engine and session factory.

    Usage
    -----
      engine  = DatabaseEngine.instance().engine
      Session = DatabaseEngine.instance().SessionLocal
      # or via context-manager helper used by FastAPI:
      with DatabaseEngine.instance().get_session() as session:
          ...
    """

    _instance: Optional["DatabaseEngine"] = None
    _initialised: bool = False

    def __new__(cls) -> "DatabaseEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        self._initialise()

    @classmethod
    def instance(cls) -> "DatabaseEngine":
        return cls()

    # ── Initialisation ───────────────────────────────────────────────────────

    def _initialise(self) -> None:
        resolve_secrets()   # ensure DATABASE_URL is in os.environ if a provider is active

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            db_dir = Path(__file__).resolve().parents[2] / "data"
            db_dir.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_dir / 'models.db'}"

        connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

        self._engine: Engine = create_engine(db_url, connect_args=connect_args, echo=False)
        self._session_factory = sessionmaker(bind=self._engine, autoflush=False, autocommit=False)

    # ── Public properties ────────────────────────────────────────────────────

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def SessionLocal(self):   # noqa: N802 — kept to match existing call sites
        return self._session_factory

    def get_session(self) -> Generator[Session, None, None]:
        """FastAPI dependency: yields a session and closes it after the request."""
        session: Session = self._session_factory()
        try:
            yield session
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Module-level shims — existing call sites (SessionLocal, engine, get_session)
# continue to work without any changes elsewhere in the codebase.
# ---------------------------------------------------------------------------
engine       = DatabaseEngine.instance().engine
SessionLocal = DatabaseEngine.instance().SessionLocal


def get_session() -> Generator[Session, None, None]:
    yield from DatabaseEngine.instance().get_session()
