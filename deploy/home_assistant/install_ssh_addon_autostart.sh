#!/bin/sh
set -eu

OPTIONS_FILE=${SSH_ADDON_OPTIONS_FILE:-/data/options.json}
APP_DIR=${APP_DIR:-/homeassistant/NutritionApp}
BACKUP_FILE="${OPTIONS_FILE}.bak.nutrition-app"

if [ ! -f "$OPTIONS_FILE" ]; then
  echo "Missing SSH add-on options file at $OPTIONS_FILE" >&2
  exit 1
fi

cp "$OPTIONS_FILE" "$BACKUP_FILE"

python3 - "$OPTIONS_FILE" "$APP_DIR" <<'PY'
import json
import sys
from pathlib import Path

options_path = Path(sys.argv[1])
app_dir = sys.argv[2]
data = json.loads(options_path.read_text())

commands = [
    "sleep 15",
    f"sh {app_dir}/deploy/home_assistant/install_watchdog.sh",
    f"sh {app_dir}/deploy/home_assistant/start_http_tmux.sh",
    f"sh {app_dir}/deploy/home_assistant/start_https_tmux.sh",
]

current = data.get("init_commands")
if not isinstance(current, list):
    current = []

managed_prefix = f"sh {app_dir}/deploy/home_assistant/"
cleaned = [
    command
    for command in current
    if not (
        command == "sleep 15"
        or command.startswith(managed_prefix)
    )
]

for command in commands:
    if command not in cleaned:
        cleaned.append(command)

data["init_commands"] = cleaned
options_path.write_text(json.dumps(data, indent=2) + "\n")

print("Configured init_commands:")
for command in cleaned:
    print(f"- {command}")
PY

echo
echo "Updated $OPTIONS_FILE"
echo "Backup saved to $BACKUP_FILE"
echo
echo "Restart the Advanced SSH & Web Terminal add-on once to apply immediately."
