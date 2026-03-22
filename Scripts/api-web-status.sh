#!/usr/bin/env bash
# =============================================================================
# api-web-status.sh
# Shows running status of all VidSage services:
#   - Backend FastAPI server
#   - Angular Portal: youtube-search         (Portals/youtube-search)
#   - Angular Portal: youtube-search-admin   (Portals/youtube-search-admin)
# =============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
CYAN="\033[0;36m"
RESET="\033[0m"

API_PORT="${API_PORT:-8000}"
PORTAL_PORT="${PORTAL_PORT:-4200}"
ADMIN_PORT="${ADMIN_PORT:-4201}"

check_port() {
  local port=$1
  lsof -iTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null | grep -q LISTEN
}

print_status() {
  local name=$1
  local port=$2
  local url=$3
  if check_port "$port"; then
    echo -e "  ${GREEN}● RUNNING${RESET}  ${name} → ${url}"
  else
    echo -e "  ${RED}○ STOPPED${RESET}  ${name} (port ${port})"
  fi
}

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}  VidSage — Service Status${RESET}"
echo -e "${CYAN}═══════════════════════════════════════════════════${RESET}"
print_status "Backend FastAPI        " "$API_PORT"    "http://localhost:${API_PORT}  (docs: http://localhost:${API_PORT}/docs)"
print_status "Portal: youtube-search " "$PORTAL_PORT" "http://localhost:${PORTAL_PORT}"
print_status "Portal: youtube-search-admin" "$ADMIN_PORT"  "http://localhost:${ADMIN_PORT}"
echo -e "${CYAN}═══════════════════════════════════════════════════${RESET}"
echo ""
