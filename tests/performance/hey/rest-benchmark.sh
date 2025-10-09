#!/usr/bin/env bash
set -euo pipefail

# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Colaboração: OpenAI (cGPT)

BASE_URL="${BENCH_TARGET_BASE_URL:-http://localhost:8001}"
SCENARIO="${SCENARIO:-baseline}"
CONFIG_FILE="$(dirname "$0")/../config/scenarios.yaml"
OUTPUT_DIR="$(dirname "$0")/../reports/hey"
mkdir -p "$OUTPUT_DIR"

if ! command -v yq >/dev/null 2>&1; then
  echo "Erro: yq não encontrado. Instale com 'pip install yq' ou use Docker." >&2
  exit 1
fi

mapfile -t ENDPOINTS < <(yq eval ".${SCENARIO}.rest.endpoints[]" "$CONFIG_FILE" 2>/dev/null || true)
if [[ ${#ENDPOINTS[@]} -eq 0 ]]; then
  echo "Nenhum endpoint configurado para cenário ${SCENARIO}." >&2
  exit 1
fi

USERS=$(yq eval ".${SCENARIO}.rest.users[]" "$CONFIG_FILE" 2>/dev/null || echo 10)
DURATION=$(yq eval ".${SCENARIO}.rest.duration" "$CONFIG_FILE" 2>/dev/null || echo "1m")
WARMUP=$(yq eval ".${SCENARIO}.rest.warmup" "$CONFIG_FILE" 2>/dev/null || echo "0s")

SECONDS=$(python - <<PY
import isodate
print(int(isodate.parse_duration('$DURATION').total_seconds()))
PY
)

for endpoint in "${ENDPOINTS[@]}"; do
  method="$(awk '{print $1}' <<< "$endpoint")"
  path="$(awk '{print $2}' <<< "$endpoint")"
  file_safe="$(tr '/' '_' <<< "$path")"

  for u in $USERS; do
    out="$OUTPUT_DIR/${file_safe}_${method}_${u}u.json"
    echo "→ Benchmark ${method} ${BASE_URL}${path} (${u} usuários)"
    hey -m "$method" -z "$DURATION" -c "$u" "${BASE_URL}${path}" \
      | tee >(jq -R -s 'split("\n")[:-1]' | jq '{raw: ., metadata: {method: "'$method'", path: "'$path'", concurrent: '$u', duration: "'$DURATION'", warmup: "'$WARMUP'", scenario: "'$SCENARIO'"}}' > "$out") >/dev/null
  done
done
