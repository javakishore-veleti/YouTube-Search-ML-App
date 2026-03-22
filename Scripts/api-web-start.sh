#!/usr/bin/env bash
# =============================================================================
# api-web-start.sh
# Starts all services for VidSage:
#   - Backend FastAPI server
#   - Angular Portal: youtube-search         (Portals/youtube-search)
#   - Angular Portal: youtube-search-admin   (Portals/youtube-search-admin)
#
# Models supported:
#   - Classical ML (scikit-learn, etc.)
#   - PyTorch
#   - TensorFlow / Keras
#   - AWS SageMaker endpoints
#   - LLM-based approaches
# =============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

log()  { echo -e "${GREEN}[START]${RESET}  $1"; }
info() { echo -e "${CYAN}[INFO]${RESET}   $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}   $1"; }

# ── Ports ────────────────────────────────────────────────────────────────────
API_PORT="${API_PORT:-8000}"
PORTAL_PORT="${PORTAL_PORT:-4200}"
ADMIN_PORT="${ADMIN_PORT:-4201}"

# ── 1. Backend FastAPI ────────────────────────────────────────────────────────
log "Starting Backend FastAPI server on port ${API_PORT}..."
cd "$REPO_ROOT"

if [ ! -f "requirements.txt" ]; then
  warn "requirements.txt not found — skipping pip install."
else
  info "Installing Python dependencies..."
  pip install -r requirements.txt --quiet
fi

# ── DB migrations ─────────────────────────────────────────────────────────────
info "Running database migrations (alembic upgrade head)..."
alembic upgrade head
log "Database migrations applied."

uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$API_PORT" \
  --reload \
  --reload-exclude "*.db" \
  --reload-exclude "*.log" \
  --reload-exclude "app/data/*" &
API_PID=$!
log "FastAPI started (PID: ${API_PID}) → http://localhost:${API_PORT}"
log "API Docs available at           → http://localhost:${API_PORT}/docs"

# ── 2. Angular Portal: youtube-search ────────────────────────────────────────
PORTAL_DIR="$REPO_ROOT/Portals/youtube-search"
if [ -d "$PORTAL_DIR" ]; then
  log "Starting Angular Portal: youtube-search on port ${PORTAL_PORT}..."
  cd "$PORTAL_DIR"
  info "Installing/updating Angular dependencies for youtube-search..."
  npm install --silent
  npx ng serve --port "$PORTAL_PORT" --open &
  PORTAL_PID=$!
  log "youtube-search portal started (PID: ${PORTAL_PID}) → http://localhost:${PORTAL_PORT}"
else
  warn "Portals/youtube-search not found — skipping. (Create it when ready)"
fi

# ── 3. Angular Portal: youtube-search-admin ──────────────────────────────────
ADMIN_DIR="$REPO_ROOT/Portals/youtube-search-admin"
if [ -d "$ADMIN_DIR" ]; then
  log "Starting Angular Portal: youtube-search-admin on port ${ADMIN_PORT}..."
  cd "$ADMIN_DIR"
  info "Installing/updating Angular dependencies for youtube-search-admin..."
  npm install --silent
  npx ng serve --port "$ADMIN_PORT" --open &
  ADMIN_PID=$!
  log "youtube-search-admin portal started (PID: ${ADMIN_PID}) → http://localhost:${ADMIN_PORT}"
else
  warn "Portals/youtube-search-admin not found — skipping. (Create it when ready)"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  VidSage — Services Running${RESET}"
echo -e "${GREEN}═══════════════════════════════════════════════════${RESET}"
echo -e "  Backend API       → http://localhost:${API_PORT}"
echo -e "  API Docs          → http://localhost:${API_PORT}/docs"
echo -e "  Search Portal     → http://localhost:${PORTAL_PORT}  (when ready)"
echo -e "  Admin Portal      → http://localhost:${ADMIN_PORT}  (when ready)"
echo -e "${GREEN}═══════════════════════════════════════════════════${RESET}"
echo ""
info "Press Ctrl+C to stop all services."

# ── Wait & Cleanup ────────────────────────────────────────────────────────────
trap 'echo ""; log "Stopping all services..."; kill $API_PID $PORTAL_PID $ADMIN_PID 2>/dev/null; exit 0' SIGINT SIGTERM

wait
