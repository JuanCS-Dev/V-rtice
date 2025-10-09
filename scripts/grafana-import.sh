#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GRAFANA_URL:-}" || -z "${GRAFANA_API_KEY:-}" ]]; then
  echo "Usage: export GRAFANA_URL and GRAFANA_API_KEY (Admin API key)." >&2
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <dashboard-file.json>" >&2
  exit 1
fi

FILE="$1"
if [[ ! -f "$FILE" ]]; then
  echo "Dashboard file $FILE not found" >&2
  exit 1
fi

data=$(jq -n --argjson dashboard "$(cat "$FILE")" '{dashboard: $dashboard, overwrite: true}')

echo "Importing dashboard from $FILE"
curl -sf \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST "${GRAFANA_URL%/}/api/dashboards/db" \
  -d "$data" >/dev/null

echo "✅ Dashboard imported"
