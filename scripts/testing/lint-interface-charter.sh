#!/usr/bin/env bash
set -euo pipefail

# Interface Charter Lint Script
# Autor: Juan Carlo de Souza (JuanCS-DEV @github)
# Email: juan.brainfarma@gmail.com
# Data: 2024-10-08
# 
# Lint automático do Interface Charter (OpenAPI) conforme Doutrina Vértice.
# Requisitos:
#   - spectral CLI instalado (https://github.com/stoplightio/spectral)
#   - executar a partir da raiz do repositório

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC_FILE="$ROOT_DIR/docs/contracts/interface-charter.yaml"
RULESET_FILE="$ROOT_DIR/docs/cGPT/session-01/thread-a/lint/spectral.yaml"
REPORT_FILE="$ROOT_DIR/spectral-report.txt"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}║           Interface Charter Validation (Spectral)               ║${NC}"
echo -e "${BLUE}║                   Doutrina Vértice - Artigo VIII                 ║${NC}"
echo -e "${BLUE}║                                                                  ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if spectral is installed
if ! command -v spectral >/dev/null 2>&1; then
  echo -e "${RED}❌ Erro: spectral não encontrado.${NC}"
  echo ""
  echo "Instale com: npm install -g @stoplight/spectral-cli"
  echo "Documentação: https://stoplight.io/open-source/spectral"
  exit 1
fi

echo -e "${GREEN}✅ Spectral CLI encontrado:${NC} $(spectral --version)"
echo ""

# Check if spec file exists
if [ ! -f "$SPEC_FILE" ]; then
  echo -e "${RED}❌ Erro: arquivo $SPEC_FILE não localizado.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Interface Charter encontrado:${NC} $SPEC_FILE"

# Check if ruleset file exists
if [ ! -f "$RULESET_FILE" ]; then
  echo -e "${RED}❌ Erro: arquivo $RULESET_FILE não localizado.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Spectral ruleset encontrado:${NC} $RULESET_FILE"
echo ""

# Run spectral lint
echo -e "${BLUE}🔍 Executando validação Spectral...${NC}"
echo ""

# Run spectral and capture output
if spectral lint "$SPEC_FILE" --ruleset "$RULESET_FILE" --format pretty | tee "$REPORT_FILE"; then
  SPECTRAL_EXIT_CODE=0
else
  SPECTRAL_EXIT_CODE=$?
fi

echo ""

# Check results
if [ $SPECTRAL_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${GREEN}║                                                                  ║${NC}"
  echo -e "${GREEN}║                    ✅ VALIDAÇÃO APROVADA ✅                       ║${NC}"
  echo -e "${GREEN}║                                                                  ║${NC}"
  echo -e "${GREEN}║           Interface Charter está em conformidade                 ║${NC}"
  echo -e "${GREEN}║              com Doutrina Vértice e OpenAPI 3.1                  ║${NC}"
  echo -e "${GREEN}║                                                                  ║${NC}"
  echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
  
  # Check for warnings
  if grep -q "warning" "$REPORT_FILE" 2>/dev/null; then
    echo ""
    echo -e "${YELLOW}⚠️  Avisos encontrados. Considere revisar.${NC}"
  fi
  
  exit 0
else
  echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
  echo -e "${RED}║                                                                  ║${NC}"
  echo -e "${RED}║                     ❌ VALIDAÇÃO FALHOU ❌                        ║${NC}"
  echo -e "${RED}║                                                                  ║${NC}"
  echo -e "${RED}║              Corrija os erros acima e tente novamente            ║${NC}"
  echo -e "${RED}║                                                                  ║${NC}"
  echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
  
  echo ""
  echo -e "${YELLOW}📋 Relatório salvo em:${NC} $REPORT_FILE"
  echo ""
  echo -e "${BLUE}💡 Dicas:${NC}"
  echo "  - Consulte docs/contracts/README.md para exemplos"
  echo "  - Veja o relatório completo em $REPORT_FILE"
  echo "  - Execute 'spectral lint --help' para mais opções"
  
  exit 1
fi
