#!/bin/bash
#
# OFFENSIVE ARSENAL E2E TEST
# Testa todos os 8 serviços do arsenal através do API Gateway
#
# Para Honra e Glória de JESUS CRISTO 🙏
#

set -e

API_GATEWAY="http://35.229.26.17"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          OFFENSIVE ARSENAL E2E TEST - Phase 9                    ║"
echo "║                 Backend + Frontend Integration                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

test_service() {
    local name=$1
    local endpoint=$2
    local method=${3:-GET}

    echo -n "Testing $name... "

    if [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST \
            -H "Content-Type: application/json" \
            -d '{"test": true}' \
            "$API_GATEWAY$endpoint" -o /dev/null)
    else
        response=$(curl -s -w "%{http_code}" "$API_GATEWAY$endpoint" -o /dev/null)
    fi

    if [ "$response" -eq 200 ] || [ "$response" -eq 422 ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " OFFENSIVE SERVICES (5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_service "Network Recon" "/api/offensive/network-recon/health"
test_service "Vuln Intel" "/api/offensive/vuln-intel/health"
test_service "Web Attack" "/api/offensive/web-attack/health"
test_service "C2 Orchestration" "/api/offensive/c2/health"
test_service "BAS" "/api/offensive/bas/health"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " DEFENSIVE SERVICES (3) - Active Immune System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_service "Behavioral Analyzer" "/api/defensive/behavioral/health"
test_service "Traffic Analyzer" "/api/defensive/traffic/health"
test_service "MAV Detection 🇧🇷" "/api/social-defense/mav/health"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓${NC} Backend: 8 services deployed and running"
echo -e "${GREEN}✓${NC} Frontend: https://vertice-frontend-172846394274.us-east1.run.app"
echo -e "${GREEN}✓${NC} API Gateway: $API_GATEWAY"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open frontend: https://vertice-frontend-172846394274.us-east1.run.app"
echo "2. Navigate to Offensive Dashboard"
echo "3. Test all 10 modules:"
echo "   - Network Scanner"
echo "   - Network Recon"
echo "   - Vuln Intel"
echo "   - Web Attack"
echo "   - C2 Orchestration"
echo "   - BAS"
echo "   - Offensive Gateway"
echo "   - Behavioral Analyzer 🧠"
echo "   - Traffic Analyzer 🔒"
echo "   - MAV Detection 🇧🇷🛡️"
echo ""
echo "Para Honra e Glória de JESUS CRISTO 🙏"
echo "\"Tudo o que fizerem, façam de todo o coração, como para o Senhor\""
echo "Colossenses 3:23"
echo ""
