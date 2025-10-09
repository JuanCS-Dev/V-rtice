#!/usr/bin/env bash
set -euo pipefail

# Script: generate-sbom.sh
# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Colaboração: OpenAI (cGPT)
# Descrição: Gera SBOM utilizando Syft (via container) para um diretório ou imagem.

if [[ $# -lt 2 ]]; then
  echo "Uso: $0 <target_path|image> <sbom_output>" >&2
  exit 1
fi

TARGET="$1"
OUTPUT="$2"

echo "🔍 Gerando SBOM com Syft para: $TARGET"
if command -v syft >/dev/null 2>&1; then
  syft "$TARGET" -o json="$OUTPUT"
else
  docker run --rm \
    -v "$(pwd)":/workspace \
    anchore/syft:0.102.0 \
    "$TARGET" \
    -o json=/workspace/"$OUTPUT"
fi

echo "✅ SBOM salvo em $OUTPUT"
