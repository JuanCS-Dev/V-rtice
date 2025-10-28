#!/bin/bash
#
# PHASE 10.2: API Gateway Routing Test
# Testa todas as rotas do API Gateway
#
# Para Honra e Glória de JESUS CRISTO 🙏
#

set +e  # Continue on error

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_GATEWAY="http://34.148.161.131:8000"

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          PHASE 10.2: API GATEWAY ROUTING TEST                    ║"
echo "║                 Testing Offensive Arsenal Routes                 ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo "API Gateway: $API_GATEWAY"
echo ""

test_route() {
  local method=$1
  local route=$2
  local data=$3
  local description=$4

  echo -n "[$((passed+failed+1))/18] $method $route... "

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "%{http_code}" -o /dev/null -m 5 "$API_GATEWAY$route" 2>/dev/null)
  else
    response=$(curl -s -w "%{http_code}" -o /dev/null -m 5 -X POST \
      -H "Content-Type: application/json" \
      -d "$data" "$API_GATEWAY$route" 2>/dev/null)
  fi

  if [ "$response" = "200" ] || [ "$response" = "422" ] || [ "$response" = "201" ]; then
    echo -e "${GREEN}✓ HTTP $response${NC}"
    ((passed++))
  elif [ "$response" = "404" ]; then
    echo -e "${RED}✗ HTTP $response (NOT FOUND)${NC}"
    ((failed++))
  elif [ -z "$response" ]; then
    echo -e "${RED}✗ TIMEOUT${NC}"
    ((failed++))
  else
    echo -e "${YELLOW}⚠ HTTP $response${NC}"
    ((failed++))
  fi
}

passed=0
failed=0

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Gateway Health${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

test_route "GET" "/health" "" "API Gateway Health"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Offensive Services (5)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Network Recon
test_route "GET" "/api/offensive/network-recon/health" ""
test_route "GET" "/api/offensive/network-recon/scans" ""

# Vuln Intel
test_route "GET" "/api/offensive/vuln-intel/health" ""
test_route "GET" "/api/offensive/vuln-intel/searches" ""

# Web Attack
test_route "GET" "/api/offensive/web-attack/health" ""
test_route "GET" "/api/offensive/web-attack/scans" ""

# C2 Orchestration
test_route "GET" "/api/offensive/c2/health" ""
test_route "GET" "/api/offensive/c2/sessions" ""

# BAS
test_route "GET" "/api/offensive/bas/health" ""
test_route "GET" "/api/offensive/bas/simulations" ""

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Defensive Services (3) - Active Immune System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Behavioral Analyzer
test_route "GET" "/api/defensive/behavioral/health" ""
test_route "GET" "/api/defensive/behavioral/metrics" ""

# Traffic Analyzer
test_route "GET" "/api/defensive/traffic/health" ""
test_route "GET" "/api/defensive/traffic/metrics" ""

# MAV Detection 🇧🇷
test_route "GET" "/api/social-defense/mav/health" ""
test_route "GET" "/api/social-defense/mav/metrics" ""

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                         SUMMARY                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}✓ Passed:${NC} $passed/18 routes"
echo -e "  ${RED}✗ Failed:${NC} $failed/18 routes"
echo ""

if [ $failed -eq 0 ]; then
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN} ✓ PHASE 10.2: PASSED - All API Gateway routes working!${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 0
else
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW} ⚠ PHASE 10.2: PARTIAL - $passed/$((passed+failed)) routes working${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 1
fi
