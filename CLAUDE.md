# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VidSage — a full-stack ML platform for building and serving YouTube video search models. Two Angular frontends communicate with a FastAPI backend that supports multiple ML approach implementations and background model building via a queue system.

## Architecture

**Three services run concurrently:**
- **FastAPI backend** (port 8000) — model serving APIs, admin APIs, background queue scheduler
- **VidSage Search Portal** (Angular, port 4200) — end-user video search interface
- **VidSage Studio Portal** (Angular, port 4201) — admin model builder interface

**Backend layout (`app/`):**
- `main.py` — entry point; loads .env, runs Alembic migrations, creates FastAPI app, starts QueueScheduler daemon thread
- `apis.json` — registry of API modules loaded dynamically by `APIInitializer` (each module exports an `Initializer` class with `initialize(dto)`)
- `app_common/` — shared infra: database engine/models/repos, secrets resolver, caching, DTOs, feature toggles, abstract interfaces (`IModelApproach`, `IModelWorkflow`)
- `app_model_serving/` — public APIs: health check, models list
- `app_model_builder/` — admin APIs, queue scheduler, model location resolver
- `app_model_approaches/` — ML implementations (approach_01 through approach_05). Each has facade → workflow → tasks pipeline. Only approach_01 (classical embeddings) is fully implemented; others are skeletons.
- `app_integrators/youtube/` — YouTube Data API v3 client
- `migrations/` — Alembic migration versions

**Key design patterns:** Singleton (DatabaseEngine, SecretsResolver, QueueScheduler), Repository (db_repo.py), Strategy (IModelApproach per approach), Task-based Workflow (sequential tasks with DB status tracking).

**API module contract:** Each module in `apis.json` must have `Initializer.initialize(dto: InitDTO)` that registers routes on the FastAPI app.

**Background queue:** QueueScheduler polls `model_build_queue` every 10 seconds, picks pending items, invokes the approach facade, records workflow execution to DB.

## Common Commands

```bash
# Install dependencies
npm run env-setup:init:install          # Python deps (pip)
npm run env-setup:portals:install       # Angular deps (npm)

# Start/stop all services
npm run app-api-web:start               # FastAPI + both Angular portals
npm run app-api-web:stop
npm run app-api-web:status

# Run services individually
cd app && uvicorn main:app --reload --port 8000
cd Portals/youtube-search && npx ng serve --port 4200
cd Portals/youtube-search-admin && npx ng serve --port 4201

# Database migrations
alembic upgrade head                    # Applied automatically on startup
alembic revision --autogenerate -m "description"

# Angular tests
cd Portals/youtube-search && npm test
cd Portals/youtube-search-admin && npm test
```

## Configuration

Environment variables loaded from `.env` (see `.env-template` for reference). Key vars:
- `YOUTUBE_API_KEY` — required for video data fetching
- `DATABASE_URL` — defaults to SQLite at `app/data/models.db`; supports PostgreSQL, MySQL, Aurora
- Secrets provider toggles: exactly one of `FEATURES_DB_AWS_SECRETS_MGR_ENABLED`, `FEATURES_DB_AZURE_KEY_VAULT_ENABLED`, `FEATURES_DB_GCP_SECRET_MGR_ENABLED`, `FEATURES_DB_ENCRYPTED_FILE_ENABLED` (or none for plain .env)

## Database

SQLAlchemy 2.0+ ORM with Alembic migrations. Models defined in `app/app_common/database/db_models.py`, repositories in `db_repo.py`. Key entities: `ModelRecord` → `ModelVersion`, `ModelRequest` → `ModelRequestResource`, `ModelBuildWf` → `ModelBuildWfTask`, `ModelBuildQueue`, `ActivityLog`.

## Angular Frontends

Both portals use Angular 21 with standalone components (no NgModules), Bootstrap 5, SCSS, and Vite builds. Dev proxy configs (`proxy.conf.json`) forward API calls to localhost:8000. Routes defined in `app.routes.ts` per portal.
