#!/bin/bash
# Integration Test - Backend ↔ Frontend
# Tests all communication paths

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_FILE="/tmp/integration_report_$(date +%Y%m%d_%H%M%S).txt"

log() { echo -e "${BLUE}[TEST]${NC} $1" | tee -a "$REPORT_FILE"; }
success() { echo -e "${GREEN}[✓]${NC} $1" | tee -a "$REPORT_FILE"; }
fail() { echo -e "${RED}[✗]${NC} $1" | tee -a "$REPORT_FILE"; }
warn() { echo -e "${YELLOW}[!]${NC} $1" | tee -a "$REPORT_FILE"; }

echo "════════════════════════════════════════════════════════════════" | tee "$REPORT_FILE"
echo " INTEGRATION TEST REPORT" | tee -a "$REPORT_FILE"
echo " Generated: $(date)" | tee -a "$REPORT_FILE"
echo "════════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Test counters
TOTAL=0
PASSED=0
FAILED=0

run_test() {
    local name="$1"
    local command="$2"
    local expected_pattern="$3"
    
    TOTAL=$((TOTAL + 1))
    log "Testing: $name"
    
    result=$(eval "$command" 2>&1)
    exit_code=$?
    
    if [ $exit_code -eq 0 ] && echo "$result" | grep -q "$expected_pattern"; then
        success "$name - PASSED"
        PASSED=$((PASSED + 1))
        return 0
    else
        fail "$name - FAILED"
        echo "  Exit code: $exit_code" | tee -a "$REPORT_FILE"
        echo "  Output: $result" | tee -a "$REPORT_FILE"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 1. BACKEND SERVICES STATUS" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check if services are running
run_test "API Gateway Port 8000" \
    "lsof -i :8000 -sTCP:LISTEN" \
    "LISTEN"

run_test "MAXIMUS Core Port 8100" \
    "lsof -i :8100 -sTCP:LISTEN" \
    "LISTEN"

run_test "Frontend Port 5173" \
    "lsof -i :5173 -sTCP:LISTEN" \
    "LISTEN"

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 2. BACKEND API HEALTH CHECKS" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

run_test "API Gateway Health" \
    "curl -s http://localhost:8000/health" \
    "healthy"

run_test "MAXIMUS Core Health" \
    "curl -s http://localhost:8100/health" \
    "healthy"

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 3. API GATEWAY ROUTING" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

run_test "Gateway → Core Proxy (Health)" \
    "curl -s http://localhost:8000/core/health" \
    "healthy"

run_test "API Documentation Available" \
    "curl -s http://localhost:8000/docs" \
    "swagger"

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 4. FRONTEND CONFIGURATION" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

log "Checking frontend .env configuration..."
echo "" | tee -a "$REPORT_FILE"

if [ -f "/home/juan/vertice-dev/frontend/.env" ]; then
    success "Frontend .env file exists"
    
    # Check API Gateway URL
    gateway_url=$(grep "VITE_API_GATEWAY_URL" /home/juan/vertice-dev/frontend/.env | cut -d'=' -f2)
    if [ "$gateway_url" = "http://localhost:8000" ]; then
        success "API Gateway URL configured correctly: $gateway_url"
    else
        fail "API Gateway URL misconfigured: $gateway_url (expected http://localhost:8000)"
    fi
    
    # Check other URLs
    grep "VITE_.*URL" /home/juan/vertice-dev/frontend/.env | tee -a "$REPORT_FILE"
else
    fail "Frontend .env file not found"
fi

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 5. FRONTEND API CLIENTS" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

log "Checking frontend API client configurations..."
echo "" | tee -a "$REPORT_FILE"

# Check maximusService.js
if grep -q "localhost:8099" /home/juan/vertice-dev/frontend/src/api/maximusService.js; then
    warn "maximusService.js using wrong port (8099 instead of 8000)"
    echo "  File: frontend/src/api/maximusService.js" | tee -a "$REPORT_FILE"
    echo "  Current: localhost:8099" | tee -a "$REPORT_FILE"
    echo "  Expected: localhost:8000" | tee -a "$REPORT_FILE"
else
    success "maximusService.js port configuration OK"
fi

# Check maximusAI.js
if grep -q "localhost:8001" /home/juan/vertice-dev/frontend/src/api/maximusAI.js; then
    warn "maximusAI.js using port 8001 (should use 8100 or 8000/core/*)"
    echo "  File: frontend/src/api/maximusAI.js" | tee -a "$REPORT_FILE"
    echo "  Current: localhost:8001" | tee -a "$REPORT_FILE"
    echo "  Expected: localhost:8100 or localhost:8000/core/*" | tee -a "$REPORT_FILE"
else
    success "maximusAI.js port configuration OK"
fi

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 6. CROSS-ORIGIN RESOURCE SHARING (CORS)" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

log "Testing CORS headers..."
cors_test=$(curl -s -H "Origin: http://localhost:5173" -I http://localhost:8000/health 2>&1)
if echo "$cors_test" | grep -q "Access-Control-Allow-Origin"; then
    success "CORS headers present"
    echo "$cors_test" | grep "Access-Control" | tee -a "$REPORT_FILE"
else
    warn "CORS headers not found (may cause frontend issues)"
fi

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 7. FRONTEND ACCESSIBILITY" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

run_test "Frontend Page Loads" \
    "curl -s http://localhost:5173" \
    "Vértice"

run_test "Frontend Assets Serve" \
    "curl -s http://localhost:5173/vite.svg" \
    "svg"

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " 8. END-TO-END INTEGRATION" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

log "Testing frontend → gateway → core path..."

# Test consciousness endpoint via gateway
run_test "Consciousness Status (via Gateway)" \
    "curl -s http://localhost:8000/core/consciousness/status" \
    "\"running\""

# Test direct core access
run_test "Consciousness Status (Direct)" \
    "curl -s http://localhost:8100/consciousness/status" \
    "\"running\""

echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " SUMMARY" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "Total Tests: $TOTAL" | tee -a "$REPORT_FILE"
echo "Passed:      $PASSED ($(echo "scale=1; $PASSED*100/$TOTAL" | bc)%)" | tee -a "$REPORT_FILE"
echo "Failed:      $FAILED ($(echo "scale=1; $FAILED*100/$TOTAL" | bc)%)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ $FAILED -eq 0 ]; then
    success "✅ ALL TESTS PASSED - System fully integrated!"
    exit_status=0
else
    fail "❌ SOME TESTS FAILED - Review issues above"
    exit_status=1
fi

echo "" | tee -a "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE" | tee -a "$REPORT_FILE"
echo "════════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"

exit $exit_status
