#!/bin/bash
# ============================================================================
# DOCKER BUILD VALIDATION SCRIPT
# Valida sistematicamente todos os builds de serviços no docker-compose.yml
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL=0
SUCCESS=0
FAILED=0
SKIPPED=0

# Arrays para armazenar resultados
FAILED_SERVICES=()
SUCCESS_SERVICES=()

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  VALIDAÇÃO DE BUILDS DOCKER - VERTICE PLATFORM${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar se docker-compose.yml existe
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ Erro: docker-compose.yml não encontrado${NC}"
    exit 1
fi

# Extrair nomes dos serviços do docker-compose.yml
# Pega apenas serviços que têm 'build:' configurado
SERVICES=$(grep -E "^[[:space:]]{2}[a-zA-Z0-9_-]+:" docker-compose.yml | sed 's/://g' | sed 's/^[[:space:]]*//' | grep -v "^#")

echo -e "${YELLOW}📋 Serviços encontrados no docker-compose.yml${NC}"
echo ""

# Contar total de serviços
while IFS= read -r service; do
    # Verificar se o serviço tem build configurado
    if grep -A5 "^[[:space:]]*${service}:" docker-compose.yml | grep -q "build:"; then
        TOTAL=$((TOTAL + 1))
    fi
done <<< "$SERVICES"

echo -e "${BLUE}Total de serviços a validar: ${TOTAL}${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Função para construir um serviço
build_service() {
    local service=$1
    local current=$2

    echo -e "${YELLOW}[${current}/${TOTAL}] Building ${service}...${NC}"

    # Tentar construir o serviço com timeout de 10 minutos
    if timeout 600 docker-compose build --no-cache "$service" > "/tmp/build_${service}.log" 2>&1; then
        echo -e "${GREEN}✓ ${service} - BUILD SUCCESSFUL${NC}"
        SUCCESS=$((SUCCESS + 1))
        SUCCESS_SERVICES+=("$service")
        return 0
    else
        echo -e "${RED}✗ ${service} - BUILD FAILED${NC}"
        echo -e "${RED}  Log: /tmp/build_${service}.log${NC}"
        FAILED=$((FAILED + 1))
        FAILED_SERVICES+=("$service")
        return 1
    fi
}

# Processar cada serviço
CURRENT=0
while IFS= read -r service; do
    # Verificar se o serviço tem build configurado
    if grep -A5 "^[[:space:]]*${service}:" docker-compose.yml | grep -q "build:"; then
        CURRENT=$((CURRENT + 1))
        build_service "$service" "$CURRENT"
        echo ""
    fi
done <<< "$SERVICES"

# Resumo final
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Total de serviços: ${TOTAL}"
echo -e "${GREEN}✓ Sucessos: ${SUCCESS}${NC}"
echo -e "${RED}✗ Falhas: ${FAILED}${NC}"
echo ""

# Listar serviços que falharam
if [ ${FAILED} -gt 0 ]; then
    echo -e "${RED}Serviços com falha:${NC}"
    for service in "${FAILED_SERVICES[@]}"; do
        echo -e "${RED}  - ${service}${NC}"
        echo -e "${RED}    Log: /tmp/build_${service}.log${NC}"
    done
    echo ""
fi

# Listar serviços bem-sucedidos
if [ ${SUCCESS} -gt 0 ]; then
    echo -e "${GREEN}Serviços bem-sucedidos:${NC}"
    for service in "${SUCCESS_SERVICES[@]}"; do
        echo -e "${GREEN}  ✓ ${service}${NC}"
    done
    echo ""
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

# Retornar código de erro se houver falhas
if [ ${FAILED} -gt 0 ]; then
    exit 1
else
    echo -e "${GREEN}🎉 Todos os builds foram bem-sucedidos!${NC}"
    exit 0
fi
