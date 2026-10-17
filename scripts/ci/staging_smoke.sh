#!/bin/sh
set -eu

api_url="${1:-${NFCORE_STAGING_BASE_URL:-}}"
portal_url="${2:-${NFCORE_STAGING_PORTAL_URL:-}}"

for url in "$api_url" "$portal_url"; do
  case "$url" in
    https://*) ;;
    *)
      echo "staging smoke: FAIL HTTPS URL required"
      exit 1
      ;;
  esac
done

api_url="${api_url%/}"
portal_url="${portal_url%/}"

curl --fail --silent --show-error --max-time 20 "$api_url/health/live" >/dev/null
curl --fail --silent --show-error --max-time 20 "$api_url/health/ready" >/dev/null

profile="$(curl --fail --silent --show-error --max-time 20 "$api_url/runtime/profile")"
printf '%s' "$profile" | python -c '
import json, sys
p = json.load(sys.stdin)
expected = {
    "environment": "staging",
    "persistence_backend": "postgres",
    "secret_backend_profile": "external",
    "https_required": True,
    "fiscal_production_activated": False,
}
for key, value in expected.items():
    if p.get(key) != value:
        raise SystemExit(f"staging smoke: FAIL runtime profile {key}={p.get(key)!r}")
'

curl --fail --silent --show-error --max-time 20 "$portal_url/" >/dev/null

# A public API must never expose tenant/unit bootstrap without a session.
# --disable prevents a local curlrc from injecting credentials into the probe.
bootstrap_status="$(curl --disable --silent --show-error --max-time 20 --output /dev/null --write-out '%{http_code}' "$api_url/v1/portal/bootstrap")"
if [ "$bootstrap_status" != "401" ]; then
  echo "staging smoke: FAIL unauthenticated portal bootstrap returned HTTP $bootstrap_status (expected 401)"
  exit 1
fi

echo "staging smoke: PASS"
