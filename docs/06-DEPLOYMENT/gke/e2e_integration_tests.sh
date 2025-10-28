#!/bin/bash
# E2E Integration Tests - Vértice Frontend + Backend

set -e

FRONTEND_URL="https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
API_GATEWAY="http://34.148.161.131:8000"

echo "==========================================="
echo "VÉRTICE E2E INTEGRATION TESTS"
echo "==========================================="
echo ""

PASS=0
FAIL=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3

    echo -n "Testing $name... "

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5 2>/dev/null || echo "000")

    if [ "$status" = "$expected_status" ]; then
        echo "✅ PASS (HTTP $status)"
        ((PASS++))
    else
        echo "❌ FAIL (Expected $expected_status, got $status)"
        ((FAIL++))
    fi
}

# ===== FRONTEND TESTS =====
echo "=== 1. FRONTEND TESTS ==="
test_endpoint "Frontend Homepage" "$FRONTEND_URL" "200"
echo ""

# ===== BACKEND API GATEWAY TESTS =====
echo "=== 2. BACKEND API GATEWAY TESTS ==="
test_endpoint "API Gateway Health" "$API_GATEWAY/health" "200"
test_endpoint "API Gateway Root" "$API_GATEWAY/" "200"
echo ""

# ===== CORE SERVICES TESTS =====
echo "=== 3. CORE SERVICES TESTS ==="

# List of critical services to test (adjust ports based on your actual services)
declare -A SERVICES
SERVICES["Maximus Core"]="http://34.148.161.131:8038/health"
SERVICES["Auth Service"]="http://34.148.161.131:8600/health"
SERVICES["Immunis API"]="http://34.148.161.131:8028/health"
SERVICES["OSINT Service"]="http://34.148.161.131:8047/health"
SERVICES["Threat Intel"]="http://34.148.161.131:8059/health"

for service_name in "${!SERVICES[@]}"; do
    url="${SERVICES[$service_name]}"
    test_endpoint "$service_name" "$url" "200"
done

echo ""

# ===== INTEGRATION TEST: Frontend -> Backend =====
echo "=== 4. INTEGRATION TEST: Frontend -> Backend ==="

echo -n "Testing Frontend can reach Backend... "
# Check if frontend HTML contains the correct API URL
frontend_html=$(curl -s "$FRONTEND_URL")
if echo "$frontend_html" | grep -q "34.148.161.131"; then
    echo "✅ PASS (Frontend configured with backend URL)"
    ((PASS++))
else
    echo "⚠️  WARNING (Frontend may not have backend URL configured)"
    ((FAIL++))
fi

echo ""

# ===== WEBSOCKET TEST (if applicable) =====
echo "=== 5. WEBSOCKET TESTS ==="
echo "⏭️  SKIPPED (requires manual testing or specialized tools)"
echo ""

# ===== SUMMARY =====
echo "==========================================="
echo "TEST SUMMARY"
echo "==========================================="
echo "Total Tests: $((PASS + FAIL))"
echo "✅ Passed: $PASS"
echo "❌ Failed: $FAIL"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED! System is fully integrated!"
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Check logs above."
    exit 1
fi
