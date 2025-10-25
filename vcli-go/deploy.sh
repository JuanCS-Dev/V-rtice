#!/bin/bash
# VCLI 2.0 - Automated Deploy Script
# Padrão Pagani: "O simples funciona"

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
VERSION="${1:-2.0.0}"
BUILD_DIR="$(pwd)"
BINARY_NAME="vcli"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      VCLI 2.0 - Automated Deploy Script       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" == "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    elif [ "$status" == "INFO" ]; then
        echo -e "${CYAN}ℹ${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 1. Check prerequisites
echo -e "${BLUE}[1/6] Verificando pré-requisitos...${NC}"
if ! command -v go &> /dev/null; then
    print_status "ERROR" "Go não está instalado. Instale Go 1.21+ primeiro."
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
print_status "OK" "Go $GO_VERSION instalado"

if ! command -v git &> /dev/null; then
    print_status "WARN" "Git não encontrado (opcional para versionamento)"
else
    print_status "OK" "Git instalado"
fi
echo ""

# 2. Clean previous build
echo -e "${BLUE}[2/6] Limpando builds anteriores...${NC}"
if [ -f "$BINARY_NAME" ]; then
    rm -f "$BINARY_NAME"
    print_status "OK" "Build anterior removido"
else
    print_status "INFO" "Nenhum build anterior encontrado"
fi
echo ""

# 3. Build optimized binary
echo -e "${BLUE}[3/6] Compilando binary otimizado...${NC}"
print_status "INFO" "Build flags: CGO_ENABLED=0 -ldflags=\"-s -w\""
print_status "INFO" "Target: $BINARY_NAME v$VERSION"

START_TIME=$(date +%s)
if CGO_ENABLED=0 go build -ldflags="-s -w" -o "$BINARY_NAME" ./cmd/; then
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))

    BINARY_SIZE=$(ls -lh "$BINARY_NAME" | awk '{print $5}')
    print_status "OK" "Build concluído em ${BUILD_TIME}s - Tamanho: $BINARY_SIZE"
else
    print_status "ERROR" "Falha no build"
    exit 1
fi
echo ""

# 4. Verify binary
echo -e "${BLUE}[4/6] Verificando binary...${NC}"
if [ ! -f "$BINARY_NAME" ]; then
    print_status "ERROR" "Binary não encontrado após build"
    exit 1
fi

if ! ./"$BINARY_NAME" --version &> /dev/null; then
    print_status "ERROR" "Binary não é executável"
    exit 1
fi

VCLI_VERSION=$(./"$BINARY_NAME" --version 2>&1 || echo "unknown")
print_status "OK" "Binary executável: $VCLI_VERSION"
print_status "OK" "Binário validado com sucesso"
echo ""

# 5. Install binary
echo -e "${BLUE}[5/6] Instalando binary...${NC}"
if [ ! -d "$INSTALL_DIR" ]; then
    print_status "INFO" "Criando diretório de instalação: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
fi

cp "$BINARY_NAME" "$INSTALL_DIR/$BINARY_NAME"
chmod +x "$INSTALL_DIR/$BINARY_NAME"
print_status "OK" "Binary instalado em: $INSTALL_DIR/$BINARY_NAME"
echo ""

# 6. Configure PATH
echo -e "${BLUE}[6/6] Configurando PATH...${NC}"
if echo "$PATH" | grep -q "$INSTALL_DIR"; then
    print_status "OK" "$INSTALL_DIR já está no PATH"
else
    print_status "WARN" "$INSTALL_DIR não está no PATH"
    echo ""
    echo -e "${YELLOW}Adicione isso ao seu ~/.bashrc ou ~/.zshrc:${NC}"
    echo -e "${CYAN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
    echo ""
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            DEPLOY COMPLETO COM SUCESSO         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Binary:${NC} $INSTALL_DIR/$BINARY_NAME"
echo -e "${GREEN}Versão:${NC} $VCLI_VERSION"
echo -e "${GREEN}Tamanho:${NC} $BINARY_SIZE"
echo ""
echo -e "${CYAN}Teste o VCLI:${NC}"
echo -e "  $INSTALL_DIR/$BINARY_NAME --version"
echo -e "  $INSTALL_DIR/$BINARY_NAME shell"
echo -e "  $INSTALL_DIR/$BINARY_NAME k8s get pods"
echo ""
echo -e "${CYAN}Ou adicione ao PATH e use:${NC}"
echo -e "  vcli --version"
echo -e "  vcli shell"
echo ""

# Optional: Create alias suggestions
echo -e "${YELLOW}Sugestões de aliases para ~/.bashrc ou ~/.zshrc:${NC}"
echo -e "${CYAN}alias neuroshell='$INSTALL_DIR/vcli shell'${NC}"
echo -e "${CYAN}alias vk='$INSTALL_DIR/vcli k8s'${NC}"
echo ""

print_status "OK" "Deploy finalizado!"
