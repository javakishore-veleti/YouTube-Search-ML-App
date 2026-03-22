#!/usr/bin/env bash
# =============================================================================
# api-web-stop.sh
# Stops all YouTube Search ML App services:
#   - Backend FastAPI server (uvicorn)
#   - Angular Portal: youtube-search
#   - Angular Portal: youtube-search-admin
# =============================================================================

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
RESET="\033[0m"

API_PORT="${API_PORT:-8000}"
PORTAL_PORT="${PORTAL_PORT:-4200}"
ADMIN_PORT="${ADMIN_PORT:-4201}"

log()  { echo -e "${GREEN}[STOP]${RESET}   $1"; }
warn() { echo -e "${YELLOW}[WARN]${RESET}   $1"; }
err()  { echo -e "${RED}[ERROR]${RESET}  $1"; }

kill_port() {
  local name=$1
  local port=$2
  local pids
  pids=$(lsof -iTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null | awk 'NR>1 {print $2}')
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill -9 2>/dev/null
    log "Stopped ${name} (port ${port}, PID(s): ${pids})"
  else
    warn "${name} was not running on port ${port}."
  fi
}

echo ""
echo -e "${RED}═══════════════════════════════════════════════════${RESET}"
echo -e "${RED}  YouTube Search ML App — Stopping Services${RESET}"
echo -e "${RED}═══════════════════════════════════════════════════${RESET}"

kill_port "Backend FastAPI (uvicorn)"    "$API_PORT"
kill_port "Portal: youtube-search"       "$PORTAL_PORT"
kill_port "Portal: youtube-search-admin" "$ADMIN_PORT"

echo -e "${RED}═══════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}All services stopped.${RESET}"
echo ""
