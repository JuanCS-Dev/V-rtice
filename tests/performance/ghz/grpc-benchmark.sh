#!/usr/bin/env bash
set -euo pipefail

# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Colaboração: OpenAI (cGPT)

GRPC_ADDR="${BENCH_TARGET_GRPC_ADDR:-localhost:50051}"
SCENARIO="${SCENARIO:-baseline}"
SERVICE="${GRPC_SERVICE:-maximus.ConsciousnessService/StreamEvents}"
CONFIG_FILE="$(dirname "$0")/../config/scenarios.yaml"
OUTPUT_DIR="$(dirname "$0")/../reports/ghz"
mkdir -p "$OUTPUT_DIR"

if ! command -v yq >/dev/null 2>&1; then
  echo "Erro: yq não encontrado." >&2
  exit 1
fi

CONCURRENCY=$(yq eval ".${SCENARIO}.grpc.concurrency[]" "$CONFIG_FILE" 2>/dev/null || echo 10)
DURATION=$(yq eval ".${SCENARIO}.grpc.duration" "$CONFIG_FILE" 2>/dev/null || echo "1m")

for c in $CONCURRENCY; do
  out="$OUTPUT_DIR/${c}c.json"
  echo "→ Benchmark gRPC $SERVICE @ $GRPC_ADDR (concurrency=$c)"
  ghz --insecure \
      --call "$SERVICE" \
      --concurrency "$c" \
      --total "-1" \
      --duration "$DURATION" \
      --output=json \
      --format=json \
      "$GRPC_ADDR" > "$out"
done
