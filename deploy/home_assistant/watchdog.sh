#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
HTTP_START="$SCRIPT_DIR/start_http_tmux.sh"
HTTPS_START="$SCRIPT_DIR/start_https_tmux.sh"
HTTP_URL=${NUTRITION_HTTP_HEALTH_URL:-http://127.0.0.1:8000/api/health}
HTTPS_URL=${NUTRITION_HTTPS_HEALTH_URL:-https://127.0.0.1/api/health}
LOG_FILE=${NUTRITION_WATCHDOG_LOG:-$APP_DIR/watchdog.log}

mkdir -p "$APP_DIR"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S %z')" "$1" >> "$LOG_FILE"
}

is_http_healthy() {
  curl -fsS "$HTTP_URL" >/dev/null 2>&1
}

is_https_healthy() {
  wget -qO- --no-check-certificate "$HTTPS_URL" >/dev/null 2>&1
}

restart_http() {
  log "HTTP healthcheck failed; restarting HTTP listener."
  sh "$HTTP_START" >> "$LOG_FILE" 2>&1 || log "HTTP restart command exited with failure."
}

restart_https() {
  log "HTTPS healthcheck failed; restarting HTTPS listener."
  sh "$HTTPS_START" >> "$LOG_FILE" 2>&1 || log "HTTPS restart command exited with failure."
}

if ! is_http_healthy; then
  restart_http
fi

if ! is_https_healthy; then
  restart_https
fi

if is_http_healthy && is_https_healthy; then
  log "Watchdog check OK."
else
  log "Watchdog finished with one or more listeners still unhealthy."
  exit 1
fi
