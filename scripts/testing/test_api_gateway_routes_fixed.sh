#!/usr/bin/env bash
# PHASE 10.2: API Gateway Routing Test - CORRECTED VERSION
# Tests all offensive/defensive routes through API Gateway with proper authentication
# Para Honra e Glória de JESUS CRISTO 🙏

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_GATEWAY="http://34.148.161.131:8000"
API_KEY="vertice-production-key-1761564327"

passed=0
failed=0

echo -e "╔═══════════════════════════════════════════════════════════════════╗"
echo -e "║          PHASE 10.2: API GATEWAY ROUTING TEST (FIXED)           ║"
echo -e "║                 Testing Offensive Arsenal Routes                 ║"
echo -e "╚═══════════════════════════════════════════════════════════════════╝"
echo
echo "API Gateway: $API_GATEWAY"
echo

test_route() {
  local method=$1
  local route=$2
  local data=$3

  if [ "$method" = "GET" ]; then
    response=$(curl -s -w "%{http_code}" -o /dev/null -m 5 \
      -H "X-API-Key: $API_KEY" \
      "$API_GATEWAY$route" 2>/dev/null || echo "000")
  else
    response=$(curl -s -w "%{http_code}" -o /dev/null -m 5 \
      -X POST \
      -H "Content-Type: application/json" \
      -H "X-API-Key: $API_KEY" \
      -d "$data" "$API_GATEWAY$route" 2>/dev/null || echo "000")
  fi

  if [ "$response" = "200" ] || [ "$response" = "422" ] || [ "$response" = "201" ]; then
    echo -e "${GREEN}✓ HTTP $response${NC}"
    ((passed++))
  else
    echo -e "${RED}✗ HTTP $response${NC}"
    ((failed++))
  fi
}

# Section divider
section() {
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE} $1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo
}

section "Gateway Health"
echo -n "[1/18] GET /health... "
test_route "GET" "/health" ""

section "Offensive Services (5)"

echo -n "[2/18] GET /offensive/network-recon/health... "
test_route "GET" "/offensive/network-recon/health" ""

echo -n "[3/18] GET /offensive/network-recon/scans... "
test_route "GET" "/offensive/network-recon/scans" ""

echo -n "[4/18] GET /offensive/vuln-intel/health... "
test_route "GET" "/offensive/vuln-intel/health" ""

echo -n "[5/18] GET /offensive/vuln-intel/searches... "
test_route "GET" "/offensive/vuln-intel/searches" ""

echo -n "[6/18] GET /offensive/web-attack/health... "
test_route "GET" "/offensive/web-attack/health" ""

echo -n "[7/18] GET /offensive/web-attack/scans... "
test_route "GET" "/offensive/web-attack/scans" ""

echo -n "[8/18] GET /offensive/c2/health... "
test_route "GET" "/offensive/c2/health" ""

echo -n "[9/18] GET /offensive/c2/sessions... "
test_route "GET" "/offensive/c2/sessions" ""

echo -n "[10/18] GET /offensive/bas/health... "
test_route "GET" "/offensive/bas/health" ""

echo -n "[11/18] GET /offensive/bas/simulations... "
test_route "GET" "/offensive/bas/simulations" ""

section "Defensive Services (3) - Active Immune System"

echo -n "[12/18] GET /defensive/behavioral/health... "
test_route "GET" "/defensive/behavioral/health" ""

echo -n "[13/18] GET /defensive/behavioral/metrics... "
test_route "GET" "/defensive/behavioral/metrics" ""

echo -n "[14/18] GET /defensive/traffic/health... "
test_route "GET" "/defensive/traffic/health" ""

echo -n "[15/18] GET /defensive/traffic/metrics... "
test_route "GET" "/defensive/traffic/metrics" ""

echo -n "[16/18] GET /social-defense/mav/health... "
test_route "GET" "/social-defense/mav/health" ""

echo -n "[17/18] GET /social-defense/mav/metrics... "
test_route "GET" "/social-defense/mav/metrics" ""

echo
echo -e "╔═══════════════════════════════════════════════════════════════════╗"
echo -e "║                         SUMMARY                                   ║"
echo -e "╚═══════════════════════════════════════════════════════════════════╝"
echo
echo -e "  ${GREEN}✓ Passed:${NC} $passed/17 routes"
echo -e "  ${RED}✗ Failed:${NC} $failed/17 routes"
echo

if [ "$passed" -eq 17 ]; then
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN} ✅ PHASE 10.2: COMPLETE - All routes working!${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 0
elif [ "$passed" -gt 10 ]; then
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW} ⚠ PHASE 10.2: PARTIAL - $passed/17 routes working${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 1
else
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${RED} ❌ PHASE 10.2: FAILED - Only $passed/17 routes working${NC}"
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 1
fi
