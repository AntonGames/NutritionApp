#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
SESSION=${NUTRITION_HTTPS_SESSION:-nutrition-app-https}
PORT=${NUTRITION_HTTPS_PORT:-443}
CERT_DIR=${NUTRITION_CERT_DIR:-$APP_DIR/certs}
CERT_FILE=${NUTRITION_CERT_FILE:-$CERT_DIR/fullchain.pem}
KEY_FILE=${NUTRITION_KEY_FILE:-$CERT_DIR/privkey.pem}

if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
  echo "Missing virtualenv at $APP_DIR/.venv" >&2
  exit 1
fi

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  echo "Missing certificate files in $CERT_DIR" >&2
  exit 1
fi

sudo tmux kill-session -t "$SESSION" 2>/dev/null || true
sudo tmux new-session -d -s "$SESSION" \
  "cd \"$APP_DIR\" && \"$APP_DIR/.venv/bin/python\" -m uvicorn nutrition_app.main:app --host 0.0.0.0 --port \"$PORT\" --env-file \"$APP_DIR/.env\" --ssl-certfile \"$CERT_FILE\" --ssl-keyfile \"$KEY_FILE\" >> \"$APP_DIR/app-https.log\" 2>&1"

echo "Started HTTPS NutritionApp on port $PORT in tmux session $SESSION"
