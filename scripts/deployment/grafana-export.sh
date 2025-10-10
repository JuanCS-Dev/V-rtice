#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GRAFANA_URL:-}" || -z "${GRAFANA_API_KEY:-}" ]]; then
  echo "Usage: export GRAFANA_URL and GRAFANA_API_KEY (Admin API key)." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <dashboard_uid> [output-file]" >&2
  exit 1
fi

UID="$1"
OUTPUT="${2:-monitoring/grafana/dashboards/${UID}.json}";
mkdir -p "$(dirname "$OUTPUT")"

echo "Exporting dashboard $UID to $OUTPUT"
curl -sf \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  "${GRAFANA_URL%/}/api/dashboards/uid/${UID}" \
  | jq '.dashboard' >"$OUTPUT"

echo "✅ Dashboard exported"
