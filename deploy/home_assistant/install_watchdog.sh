#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
WATCHDOG_SRC="$SCRIPT_DIR/watchdog.sh"
WATCHDOG_LINK=${NUTRITION_WATCHDOG_LINK:-/etc/periodic/15min/nutrition-app-watchdog}

if [ ! -f "$WATCHDOG_SRC" ]; then
  echo "Missing watchdog source at $WATCHDOG_SRC" >&2
  exit 1
fi

chmod +x "$WATCHDOG_SRC"
mkdir -p "$(dirname "$WATCHDOG_LINK")"
ln -sf "$WATCHDOG_SRC" "$WATCHDOG_LINK"
chmod +x "$WATCHDOG_LINK"

echo "Installed NutritionApp watchdog link:"
echo "$WATCHDOG_LINK -> $WATCHDOG_SRC"
echo
echo "The host's default 15-minute periodic job will now run this watchdog."
echo "Run it once manually if you want an immediate self-heal check:"
echo "sh $WATCHDOG_SRC"
