"""
Alembic environment – wired to the app's SQLAlchemy models.

DB flexibility
--------------
Set the DATABASE_URL environment variable to switch databases with zero
code changes.  The alembic.ini SQLite fallback is used only when the env
var is absent (local dev without .env).

  SQLite  (default / local)   : not set  →  falls back to alembic.ini
  Postgres / Aurora PG        : postgresql+psycopg2://user:pass@host:5432/db
  MySQL / Aurora MySQL        : mysql+pymysql://user:pass@host:3306/db
  AWS RDS (SSL)               : postgresql+psycopg2://...?sslmode=require

Layout
------
  app/migrations/
    env.py                              ← this file
    script.py.mako
    MIGRATIONS.md
    versions/
      v001_20260322_initial_schema.py
      v002_YYYYMMDD_<description>.py    ← future migrations
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the repo root importable so `from app...` works from the CLI.
# app/migrations/env.py  →  parents[2] = repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Resolve secrets first (AWS SM / Azure KV / GCP SM / encrypted file / .env)
# so DATABASE_URL is in os.environ before Alembic reads it.
from dotenv import load_dotenv
load_dotenv()
from app.app_common.config.secrets_resolver import resolve_secrets
resolve_secrets()

# Import Base + all models so autogenerate can detect every table.
from app.app_common.database.db_models import Base  # noqa: E402
import app.app_common.database.db_models             # noqa: F401

# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override URL from DATABASE_URL env var if set (Docker / CI / Prod).
# Falls back to the sqlite URL in alembic.ini for local development.
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    config.set_main_option("sqlalchemy.url", _db_url)

target_metadata = Base.metadata

# render_as_batch is only required for SQLite (no native ALTER TABLE support).
# Postgres and MySQL handle ALTER TABLE natively so we disable it for them.
def _use_batch_mode() -> bool:
    url = config.get_main_option("sqlalchemy.url") or ""
    return url.startswith("sqlite")


# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Generate SQL without a live DB connection — useful for review / CI diffs."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_use_batch_mode(),
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Apply migrations against a live DB connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=_use_batch_mode(),
        )
        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
