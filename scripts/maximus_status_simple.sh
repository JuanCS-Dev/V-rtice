#!/bin/bash

# Cores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC} 📊 Status dos Serviços MAXIMUS"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

cd /home/juan/vertice-dev

# Tier 0
echo -e "${CYAN}═══ Tier 0: Infrastructure (3) ═══${NC}"
docker compose ps redis postgres qdrant --format "{{.Service}}\t{{.Status}}" 2>/dev/null | while read svc status; do
    [[ "$status" =~ "Up" ]] && echo -e "${GREEN}[✓]${NC} $svc: RUNNING" || echo -e "[ ] $svc: STOPPED"
done

echo ""
echo -e "${CYAN}═══ Tier 1: Core Services (11) ═══${NC}"
docker compose ps api_gateway sinesp_service cyber_service domain_service --format "{{.Service}}\t{{.Status}}" 2>/dev/null | head -4 | while read svc status; do
    [[ "$status" =~ "Up" ]] && echo -e "${GREEN}[✓]${NC} $svc: RUNNING" || echo -e "[ ] $svc: STOPPED"
done
echo "  ... (7 more)"

echo ""
echo -e "${CYAN}═══ Summary ═══${NC}"
TOTAL=$(docker compose ps --format "{{.Service}}" 2>/dev/null | wc -l)
echo -e "${GREEN}Total de serviços ativos:${NC} $TOTAL/60 full stack"

echo ""
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway:${NC} HEALTHY"
else
    echo -e "✗ API Gateway: DOWN"
fi

echo ""
echo -e "${CYAN}👸 Penélope: 'Plataforma cyber-biológica operacional!'${NC}"
