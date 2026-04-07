#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
SESSION=${NUTRITION_HTTP_SESSION:-nutrition-app}
PORT=${NUTRITION_HTTP_PORT:-8000}

mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
  python3 -m venv "$APP_DIR/.venv"
  . "$APP_DIR/.venv/bin/activate"
  pip install -e "$APP_DIR" > "$APP_DIR/pip-install.log" 2>&1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux kill-session -t "$SESSION"
fi

tmux new-session -d -s "$SESSION" \
  "cd \"$APP_DIR\" && \"$APP_DIR/.venv/bin/python\" -m uvicorn nutrition_app.main:app --host 0.0.0.0 --port \"$PORT\" --env-file \"$APP_DIR/.env\" >> \"$APP_DIR/app.log\" 2>&1"

echo "Started HTTP NutritionApp on port $PORT in tmux session $SESSION"
