#!/bin/bash
###############################################################################
# AUTO DISCOVER PORTS - Descoberta Automática de Portas Reais
###############################################################################
# Varre TODOS os containers Docker em execução e descobre:
# 1. Porta REAL que o serviço está rodando (via logs)
# 2. Porta MAPEADA externamente
# 3. Valida health endpoint
# 4. Gera manifest JSON e atualiza configs automaticamente
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  AUTO DISCOVER PORTS - Descoberta Automática            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

MANIFEST_FILE="/home/juan/vertice-dev/docs/port_manifest.json"
mkdir -p "$(dirname "$MANIFEST_FILE")"

echo "[" > "$MANIFEST_FILE"
FIRST=true

# Get all running containers
CONTAINERS=$(docker ps --format "{{.Names}}")

for CONTAINER in $CONTAINERS; do
    echo -e "${BLUE}Analisando: ${CONTAINER}${NC}"
    
    # Get port mappings
    PORT_INFO=$(docker port "$CONTAINER" 2>/dev/null | head -1)
    
    if [ -z "$PORT_INFO" ]; then
        echo -e "${YELLOW}  ⚠ Sem mapeamento de portas${NC}"
        continue
    fi
    
    # Extract ports: "8001/tcp -> 0.0.0.0:8151"
    INTERNAL_PORT=$(echo "$PORT_INFO" | awk '{print $1}' | cut -d'/' -f1)
    EXTERNAL_PORT=$(echo "$PORT_INFO" | awk '{print $3}' | cut -d':' -f2)
    
    # Try to find REAL port from logs
    REAL_PORT=$(docker logs "$CONTAINER" 2>&1 | grep -oP "(?<=Uvicorn running on http://0.0.0.0:)\d+" | head -1)
    
    if [ -z "$REAL_PORT" ]; then
        REAL_PORT="$INTERNAL_PORT"
    fi
    
    # Get container IP
    CONTAINER_IP=$(docker inspect "$CONTAINER" --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
    
    # Test health endpoint on REAL port
    HEALTH_STATUS="unknown"
    if curl -s --max-time 2 "http://${CONTAINER_IP}:${REAL_PORT}/health" > /dev/null 2>&1; then
        HEALTH_STATUS="healthy"
    elif curl -s --max-time 2 "http://localhost:${EXTERNAL_PORT}/health" > /dev/null 2>&1; then
        HEALTH_STATUS="healthy_via_external"
    fi
    
    echo -e "  External: ${GREEN}${EXTERNAL_PORT}${NC}"
    echo -e "  Internal Mapped: ${YELLOW}${INTERNAL_PORT}${NC}"
    echo -e "  REAL Port: ${CYAN}${REAL_PORT}${NC}"
    echo -e "  Health: ${HEALTH_STATUS}"
    
    # Add to manifest
    if [ "$FIRST" = false ]; then
        echo "," >> "$MANIFEST_FILE"
    fi
    FIRST=false
    
    cat >> "$MANIFEST_FILE" << EOF
  {
    "container": "$CONTAINER",
    "external_port": $EXTERNAL_PORT,
    "internal_mapped": $INTERNAL_PORT,
    "real_port": $REAL_PORT,
    "health_status": "$HEALTH_STATUS",
    "container_ip": "$CONTAINER_IP",
    "mismatch": $([ "$INTERNAL_MAPPED" != "$REAL_PORT" ] && echo "true" || echo "false")
  }
EOF
    
    echo ""
done

echo "]" >> "$MANIFEST_FILE"

echo -e "${GREEN}✅ Manifest gerado: ${MANIFEST_FILE}${NC}"
echo ""
echo -e "${CYAN}Serviços COM MISMATCH:${NC}"
jq -r '.[] | select(.mismatch == true) | "  \(.container): External \(.external_port) → Mapped \(.internal_mapped) ≠ REAL \(.real_port)"' "$MANIFEST_FILE" 2>/dev/null || echo "  Nenhum mismatch detectado!"

echo ""
echo -e "${CYAN}Total de serviços descobertos: $(jq length "$MANIFEST_FILE" 2>/dev/null || echo "0")${NC}"
