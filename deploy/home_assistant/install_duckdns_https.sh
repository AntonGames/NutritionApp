#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP_DIR=${APP_DIR:-$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)}
EMAIL=${DUCKDNS_EMAIL:-noreply@localhost}
ACME_HOME=${ACME_HOME:-$APP_DIR/.acme.sh}
CERT_DIR=${NUTRITION_CERT_DIR:-$APP_DIR/certs}
ACME_SH=$ACME_HOME/acme.sh
SECRETS_FILE=${DUCKDNS_SECRETS_FILE:-$APP_DIR/.duckdns.env}

if [ -f "$SECRETS_FILE" ]; then
  # shellcheck disable=SC1090
  . "$SECRETS_FILE"
fi

DOMAIN=${DUCKDNS_DOMAIN:-${DOMAIN:-}}
TOKEN=${DUCKDNS_TOKEN:-${TOKEN:-}}

if [ -z "$DOMAIN" ] || [ -z "$TOKEN" ]; then
  echo "Usage: DUCKDNS_DOMAIN=your-subdomain.duckdns.org DUCKDNS_TOKEN=... sh deploy/home_assistant/install_duckdns_https.sh" >&2
  exit 1
fi

mkdir -p "$CERT_DIR"
export HOME="$APP_DIR"

sh "$SCRIPT_DIR/update_duckdns_ip.sh"

if [ ! -x "$ACME_SH" ]; then
  curl -s https://get.acme.sh | sh -s email="$EMAIL"
fi

export DuckDNS_Token="$TOKEN"

"$ACME_SH" --register-account --server letsencrypt >/dev/null 2>&1 || true
"$ACME_SH" \
  --issue \
  --server letsencrypt \
  --dns dns_duckdns \
  --keylength ec-256 \
  -d "$DOMAIN" \
  --home "$ACME_HOME"

"$ACME_SH" \
  --install-cert \
  -d "$DOMAIN" \
  --ecc \
  --home "$ACME_HOME" \
  --fullchain-file "$CERT_DIR/fullchain.pem" \
  --key-file "$CERT_DIR/privkey.pem" \
  --reloadcmd "sh $SCRIPT_DIR/start_https_tmux.sh"

sh "$SCRIPT_DIR/start_http_tmux.sh"
sh "$SCRIPT_DIR/start_https_tmux.sh"

echo
echo "DuckDNS HTTPS setup completed."
echo "Public schema URL after router port forwarding:"
echo "https://$DOMAIN/api/actions/openapi.yaml"
echo
echo "Router requirement:"
echo "Forward external TCP 443 to this Home Assistant host on TCP 443."
