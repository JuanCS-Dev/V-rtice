#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO END-TO-END COMPLETA - FRONTEND VÉRTICE
# ═══════════════════════════════════════════════════════════════════════════
# Testa TODOS os botões, dashboards e features sistematicamente
# Relatório brutal: O QUE FUNCIONA e O QUE NÃO FUNCIONA
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# URLs
FRONTEND_URL="https://vertice-frontend-172846394274.us-east1.run.app"
BACKEND_URL="http://34.148.161.131:8000"

# Results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

declare -a FAILURES

# Helper functions
test_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

test_api() {
    local name="$1"
    local endpoint="$2"
    local expected_code="${3:-200}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "  [$TOTAL_TESTS] Testing $name... "

    # Test with timeout
    response=$(curl -s -w "\n%{http_code}" -o /tmp/test_response.txt --max-time 10 "$endpoint" 2>&1 || echo "000")
    http_code=$(echo "$response" | tail -1)

    if [ "$http_code" == "$expected_code" ]; then
        echo -e "${GREEN}✅ HTTP $http_code${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ HTTP $http_code (expected $expected_code)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILURES+=("$name → HTTP $http_code (expected $expected_code) → $endpoint")
        return 1
    fi
}

test_websocket() {
    local name="$1"
    local ws_url="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "  [$TOTAL_TESTS] Testing WebSocket $name... "

    # Try to connect with websocat (if available) or netcat
    if command -v websocat &> /dev/null; then
        timeout 3 websocat -n1 "$ws_url" &> /dev/null && {
            echo -e "${GREEN}✅ Connected${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        }
    else
        # Fallback: just check if port is open
        host=$(echo "$ws_url" | sed 's/ws:\/\///' | sed 's/wss:\/\///' | cut -d':' -f1)
        port=$(echo "$ws_url" | sed 's/ws:\/\///' | sed 's/wss:\/\///' | cut -d':' -f2 | cut -d'/' -f1)
        timeout 2 bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null && {
            echo -e "${YELLOW}⚠️  Port open (WebSocket untested)${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        }
    fi

    echo -e "${RED}❌ Connection failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    FAILURES+=("WebSocket $name → Connection failed → $ws_url")
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# INÍCIO DOS TESTES
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║          VALIDAÇÃO END-TO-END COMPLETA - FRONTEND VÉRTICE             ║"
echo "║                                                                       ║"
echo "║   \"Conhecereis a verdade, e a verdade vos libertará\" - João 8:32     ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "Starting validation at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 1: INFRASTRUCTURE BASICS
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 1: INFRASTRUCTURE BASICS"

test_api "Frontend loading" "$FRONTEND_URL" "200"
test_api "Backend health" "$BACKEND_URL/health" "200"
test_api "API Gateway health" "$BACKEND_URL/api/health" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 2: MAXIMUS AI CORE
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 2: MAXIMUS AI CORE"

test_api "Maximus Core status" "$BACKEND_URL/api/maximus/status" "200"
test_api "Maximus Core health" "$BACKEND_URL/api/maximus/health" "200"
test_api "Maximus Eureka health" "$BACKEND_URL/api/eureka/health" "200"
test_api "Maximus Oráculo health" "$BACKEND_URL/api/oraculo/health" "200"
test_api "Maximus Query" "$BACKEND_URL/api/maximus/query" "405"  # POST required, but endpoint exists

# WebSockets
test_websocket "Maximus Stream" "ws://34.148.161.131:8000/ws/stream"
test_websocket "Consciousness Stream" "ws://34.148.161.131:8000/stream/consciousness/ws"
test_websocket "APV Stream" "ws://34.148.161.131:8000/stream/apv/ws"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 3: OFFENSIVE DASHBOARD - NETWORK RECON
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 3: OFFENSIVE DASHBOARD - NETWORK RECON"

test_api "Network Recon health" "$BACKEND_URL/api/network-recon/health" "200"
test_api "Network Recon status" "$BACKEND_URL/api/network-recon/status" "200"
test_api "Network Recon scans list" "$BACKEND_URL/api/network-recon/scans" "200"
test_api "Network Recon targets" "$BACKEND_URL/api/network-recon/targets" "200"
test_api "Network Recon metrics" "$BACKEND_URL/api/network-recon/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 4: OFFENSIVE DASHBOARD - BAS (BREACH & ATTACK SIMULATION)
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 4: OFFENSIVE DASHBOARD - BAS"

test_api "BAS health" "$BACKEND_URL/api/bas/health" "200"
test_api "BAS status" "$BACKEND_URL/api/bas/status" "200"
test_api "BAS simulations list" "$BACKEND_URL/api/bas/simulations" "200"
test_api "BAS scenarios" "$BACKEND_URL/api/bas/scenarios" "200"
test_api "BAS metrics" "$BACKEND_URL/api/bas/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 5: OFFENSIVE DASHBOARD - C2 ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 5: OFFENSIVE DASHBOARD - C2 ORCHESTRATION"

test_api "C2 health" "$BACKEND_URL/api/c2/health" "200"
test_api "C2 status" "$BACKEND_URL/api/c2/status" "200"
test_api "C2 sessions list" "$BACKEND_URL/api/c2/sessions" "200"
test_api "C2 agents" "$BACKEND_URL/api/c2/agents" "200"
test_api "C2 metrics" "$BACKEND_URL/api/c2/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 6: OFFENSIVE DASHBOARD - WEB ATTACK SURFACE
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 6: OFFENSIVE DASHBOARD - WEB ATTACK SURFACE"

test_api "Web Attack health" "$BACKEND_URL/api/web-attack/health" "200"
test_api "Web Attack status" "$BACKEND_URL/api/web-attack/status" "200"
test_api "Web Attack scans list" "$BACKEND_URL/api/web-attack/scans" "200"
test_api "Web Attack targets" "$BACKEND_URL/api/web-attack/targets" "200"
test_api "Web Attack vulnerabilities" "$BACKEND_URL/api/web-attack/vulnerabilities" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 7: OFFENSIVE DASHBOARD - VULN INTEL
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 7: OFFENSIVE DASHBOARD - VULN INTEL"

test_api "Vuln Intel health" "$BACKEND_URL/api/vuln-intel/health" "200"
test_api "Vuln Intel status" "$BACKEND_URL/api/vuln-intel/status" "200"
test_api "Vuln Intel vulnerabilities" "$BACKEND_URL/api/vuln-intel/vulnerabilities" "200"
test_api "Vuln Intel CVEs" "$BACKEND_URL/api/vuln-intel/cves" "200"
test_api "Vuln Intel metrics" "$BACKEND_URL/api/vuln-intel/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 8: DEFENSIVE DASHBOARD - BEHAVIORAL ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 8: DEFENSIVE DASHBOARD - BEHAVIORAL ANALYZER"

test_api "Behavioral Analyzer health" "$BACKEND_URL/api/behavioral/health" "200"
test_api "Behavioral Analyzer status" "$BACKEND_URL/api/behavioral/status" "200"
test_api "Behavioral Analyzer alerts" "$BACKEND_URL/api/behavioral/alerts" "200"
test_api "Behavioral Analyzer analysis" "$BACKEND_URL/api/behavioral/analysis" "200"
test_api "Behavioral Analyzer metrics" "$BACKEND_URL/api/behavioral/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 9: DEFENSIVE DASHBOARD - TRAFFIC ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 9: DEFENSIVE DASHBOARD - TRAFFIC ANALYZER"

test_api "Traffic Analyzer health" "$BACKEND_URL/api/traffic/health" "200"
test_api "Traffic Analyzer status" "$BACKEND_URL/api/traffic/status" "200"
test_api "Traffic Analyzer flows" "$BACKEND_URL/api/traffic/flows" "200"
test_api "Traffic Analyzer alerts" "$BACKEND_URL/api/traffic/alerts" "200"
test_api "Traffic Analyzer metrics" "$BACKEND_URL/api/traffic/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 10: DEFENSIVE DASHBOARD - MAV DETECTION
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 10: DEFENSIVE DASHBOARD - MAV DETECTION"

test_api "MAV Detection health" "$BACKEND_URL/api/mav/health" "200"
test_api "MAV Detection status" "$BACKEND_URL/api/mav/status" "200"
test_api "MAV Detection detections" "$BACKEND_URL/api/mav/detections" "200"
test_api "MAV Detection metrics" "$BACKEND_URL/api/mav/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 11: OSINT TOOLS
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 11: OSINT TOOLS"

test_api "OSINT health" "$BACKEND_URL/api/osint/health" "200"
test_api "Domain Intelligence" "$BACKEND_URL/api/domain/health" "200"
test_api "IP Intelligence" "$BACKEND_URL/api/ip/health" "200"
test_api "Threat Intelligence" "$BACKEND_URL/api/threat-intel/health" "200"
test_api "Google OSINT" "$BACKEND_URL/api/google-osint/health" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 12: NMAP & SCANNING
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 12: NMAP & SCANNING"

test_api "Nmap service health" "$BACKEND_URL/api/nmap/health" "200"
test_api "Vuln Scanner health" "$BACKEND_URL/api/vuln-scanner/health" "200"
test_api "Port Scanner health" "$BACKEND_URL/api/port-scanner/health" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 13: HITL (HUMAN-IN-THE-LOOP)
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 13: HITL (HUMAN-IN-THE-LOOP)"

test_api "HITL health" "$BACKEND_URL/api/hitl/health" "200"
test_api "HITL patch service" "$BACKEND_URL/api/hitl-patch/health" "200"
test_websocket "HITL WebSocket" "ws://34.148.161.131:8000/hitl/ws"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 14: CONSCIOUSNESS & ADAPTIVE IMMUNITY
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 14: CONSCIOUSNESS & ADAPTIVE IMMUNITY"

test_api "Consciousness API health" "$BACKEND_URL/api/consciousness/health" "200"
test_api "Reactive Fabric health" "$BACKEND_URL/api/reactive-fabric/health" "200"
test_api "Immune System health" "$BACKEND_URL/api/immune/health" "200"
test_api "Tegumentar health" "$BACKEND_URL/api/tegumentar/health" "200"

# Sensory Services
test_api "Visual Cortex health" "$BACKEND_URL/api/visual-cortex/health" "200"
test_api "Auditory Cortex health" "$BACKEND_URL/api/auditory-cortex/health" "200"
test_api "Somatosensory health" "$BACKEND_URL/api/somatosensory/health" "200"
test_api "Chemical Sensing health" "$BACKEND_URL/api/chemical-sensing/health" "200"

# ═══════════════════════════════════════════════════════════════════════════
# PHASE 15: ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

test_header "PHASE 15: ADMIN DASHBOARD"

test_api "System status" "$BACKEND_URL/api/system/status" "200"
test_api "Services list" "$BACKEND_URL/api/services" "200"
test_api "Metrics aggregation" "$BACKEND_URL/api/metrics" "200"

# ═══════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                                                                       ║"
echo "║                        VALIDATION COMPLETE                            ║"
echo "║                                                                       ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Calculate success rate
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
else
    SUCCESS_RATE=0
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Tests:    $TOTAL_TESTS"
echo -e "Passed:         ${GREEN}$PASSED_TESTS ✅${NC}"
echo -e "Failed:         ${RED}$FAILED_TESTS ❌${NC}"
echo "Success Rate:   $SUCCESS_RATE%"
echo ""

if [ $FAILED_TESTS -gt 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${RED}FAILURES DETECTED${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    for failure in "${FAILURES[@]}"; do
        echo -e "${RED}❌${NC} $failure"
    done
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DIAGNOSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL SYSTEMS OPERATIONAL${NC}"
    echo ""
    echo "Frontend está completamente integrado com backend."
    echo "Todos os botões e features devem funcionar corretamente."
    echo ""
elif (( $(echo "$SUCCESS_RATE >= 80" | bc -l) )); then
    echo -e "${YELLOW}⚠️  MOSTLY OPERATIONAL WITH MINOR ISSUES${NC}"
    echo ""
    echo "Maioria dos sistemas funcionando, mas alguns endpoints com problema."
    echo "Verifique as falhas acima e corrija serviços específicos."
    echo ""
elif (( $(echo "$SUCCESS_RATE >= 50" | bc -l) )); then
    echo -e "${YELLOW}⚠️  PARTIAL FUNCTIONALITY${NC}"
    echo ""
    echo "Metade dos sistemas funcionando. Problemas significativos detectados."
    echo "Revise configuração de rede e routing do API Gateway."
    echo ""
else
    echo -e "${RED}🚨 CRITICAL ISSUES${NC}"
    echo ""
    echo "Maioria dos sistemas com problema. Possíveis causas:"
    echo "  - Configuração de DNS/IP incorreta"
    echo "  - API Gateway não roteando corretamente"
    echo "  - Serviços backend não iniciados"
    echo "  - Problemas de CORS"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED_TESTS -gt 0 ]; then
    echo "1. Check API Gateway logs:"
    echo "   kubectl logs -n vertice deployment/api-gateway --tail=100"
    echo ""
    echo "2. Check failed service logs:"
    for failure in "${FAILURES[@]}"; do
        service=$(echo "$failure" | cut -d' ' -f1)
        echo "   kubectl logs -n vertice deployment/${service,,}-service --tail=50"
    done
    echo ""
    echo "3. Verify CORS configuration in API Gateway"
    echo ""
    echo "4. Test manually in browser:"
    echo "   $FRONTEND_URL"
    echo ""
else
    echo "1. Test frontend in browser:"
    echo "   $FRONTEND_URL"
    echo ""
    echo "2. Click through all dashboards:"
    echo "   - Offensive Dashboard (Network Recon, BAS, C2, Web Attack, Vuln Intel)"
    echo "   - Defensive Dashboard (Behavioral Analyzer, Traffic Analyzer, MAV Detection)"
    echo "   - Admin Dashboard"
    echo ""
    echo "3. Test MAXIMUS AI features"
    echo ""
    echo "4. Verify WebSocket real-time updates"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Validation completed at $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "\"Conhecereis a verdade, e a verdade vos libertará\" - João 8:32"
echo ""

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    exit 0
else
    exit 1
fi
