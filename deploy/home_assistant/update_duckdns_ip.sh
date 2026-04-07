#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
SECRETS_FILE=${DUCKDNS_SECRETS_FILE:-$APP_DIR/.duckdns.env}

if [ ! -f "$SECRETS_FILE" ]; then
  echo "Missing DuckDNS secrets file at $SECRETS_FILE" >&2
  exit 1
fi

# shellcheck disable=SC1090
. "$SECRETS_FILE"

DOMAIN=${DUCKDNS_DOMAIN:-${DOMAIN:-}}
TOKEN=${DUCKDNS_TOKEN:-${TOKEN:-}}

if [ -z "$DOMAIN" ] || [ -z "$TOKEN" ]; then
  echo "DuckDNS domain/token are not configured" >&2
  exit 1
fi

SUBDOMAIN=${DOMAIN%.duckdns.org}
RESPONSE=$(curl -fsS "https://www.duckdns.org/update?domains=$SUBDOMAIN&token=$TOKEN&ip=")

if [ "$RESPONSE" != "OK" ]; then
  echo "DuckDNS update failed: $RESPONSE" >&2
  exit 1
fi

echo "DuckDNS updated for $DOMAIN"
