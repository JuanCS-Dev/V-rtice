#!/usr/bin/env bash
set -euo pipefail

# Script: sign-artifact.sh
# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Colaboração: OpenAI (cGPT)
# Descrição: Assina artefatos utilizando cosign, suportando blobs ou imagens.

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <artifact_path|image_reference> [--attest <sbom_file>]" >&2
  exit 1
fi

ARTIFACT="$1"
shift || true

if [[ -z "${COSIGN_PASSWORD:-}" || -z "${COSIGN_KEY:-}" ]]; then
  echo "⚠️  Variáveis COSIGN_PASSWORD e COSIGN_KEY não definidas. Abortando." >&2
  exit 1
fi

export COSIGN_PASSWORD

echo "✍️  Assinando artefato $ARTIFACT com cosign"
cosign sign --key "$COSIGN_KEY" "$ARTIFACT"

if [[ "${1:-}" == "--attest" && -n "${2:-}" ]]; then
  SBOM="$2"
  shift 2
  echo "📄 Gerando attestation com SBOM $SBOM"
  cosign attest --key "$COSIGN_KEY" --predicate "$SBOM" --type sbom "$ARTIFACT"
fi

echo "✅ Assinatura concluída"
