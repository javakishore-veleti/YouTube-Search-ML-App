from dotenv import load_dotenv

load_dotenv()   # always load .env first so FEATURES_* toggles are available

# Resolve secrets from the active provider (AWS SM / Azure KV / GCP SM / encrypted file / .env)
from app.app_common.config.secrets_resolver import resolve_secrets
resolve_secrets()

import logging
import logging.handlers
import time
from pathlib import Path

# ── Logging setup: console + rolling file (logs/ at repo root) ─
REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"

# Rolling file: 10 MB per file, keep 20 backups (app.log, app.log.1 … app.log.20)
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=20,
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

logging.basicConfig(level=logging.DEBUG, handlers=[console_handler, file_handler])

# Suppress urllib3 debug logs — they leak API keys in query params
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("=== App startup begin ===")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.app_common.api_initializer import APIInitializer
from app.app_common.app_status import set_status
from app.app_model_serving.api.api_manager import ApiManager
from app.app_common.dtos.init_dtos import InitDTO

# ── DB migrations ─────────────────────────────────────────────
# api-web-start.sh runs `alembic upgrade head` before uvicorn starts.
# This call is a safety net for Docker entrypoints and direct `uvicorn` runs
# that bypass the shell script.  Alembic is idempotent — running twice is safe.
t0 = time.time()
from alembic.config import Config
from alembic import command as alembic_command
_alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
alembic_command.upgrade(_alembic_cfg, "head")
set_status("db_initialized", True)
logger.info(f"DB migrated to head in {time.time()-t0:.3f}s")

app: FastAPI = ApiManager.initialize_app()


# ── Request logging middleware ─────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    logger.debug(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    elapsed = time.time() - start
    logger.info(f"← {request.method} {request.url.path} {response.status_code} ({elapsed:.3f}s)")
    return response


# CORS — allow Angular portals to reach the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:4201",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initializer = APIInitializer()
initializer.initialize_apis(InitDTO(app=app, ctxt_data={}))

# Start background queue scheduler
from app.app_model_builder.pipeline.queue_scheduler import start_scheduler
start_scheduler()

logger.info("=== App startup complete ===")
