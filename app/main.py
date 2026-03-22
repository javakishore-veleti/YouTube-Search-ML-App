from dotenv import load_dotenv

load_dotenv()

import logging
import logging.handlers
import time
from pathlib import Path

# ── Logging setup: console + rolling file (logs/ at repo root) ─
REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

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

logger = logging.getLogger("app.main")
logger.info("=== App startup begin ===")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.app_common.api_initializer import APIInitializer
from app.app_common.app_status import set_status
from app.app_common.database.db_engine import engine
from app.app_common.database.db_models import Base
from app.app_model_serving.api.api_manager import ApiManager
from app.app_common.dtos.init_dtos import InitDTO

# Create all DB tables
t0 = time.time()
Base.metadata.create_all(bind=engine)
set_status("db_initialized", True)
logger.info(f"DB tables created in {time.time()-t0:.3f}s")

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
