#!/bin/bash

# FASE 3.8 - Frontend Integration Testing
# Tests frontend integration with Mock API

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          FASE 3.8 - FRONTEND INTEGRATION TESTING                  ║"
echo "║                    Full E2E Validation                            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run test
run_test() {
    local test_name="$1"
    local test_command="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing $test_name... "

    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

echo "═════════════════════════════════════════════════════════════════════"
echo "1. BACKEND API VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Backend API tests
run_test "Mock API Health" "curl -sf http://localhost:8003/hitl/health | grep -q healthy"
run_test "Mock API GET /reviews" "curl -sf http://localhost:8003/hitl/reviews | grep -q reviews"
run_test "Mock API GET /stats" "curl -sf http://localhost:8003/hitl/reviews/stats | grep -q pending_reviews"
run_test "Mock API has CORS configured" "grep -q 'CORSMiddleware' /home/juan/vertice-dev/backend/services/adaptive_immune_system/hitl/test_mock_api.py"

echo ""
echo "   📊 Backend API Summary:"
TOTAL_REVIEWS=$(curl -s http://localhost:8003/hitl/reviews | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "N/A")
PENDING=$(curl -s http://localhost:8003/hitl/reviews/stats | python3 -c "import sys, json; print(json.load(sys.stdin)['pending_reviews'])" 2>/dev/null || echo "N/A")
DECISIONS=$(curl -s http://localhost:8003/hitl/reviews/stats | python3 -c "import sys, json; print(json.load(sys.stdin)['total_decisions'])" 2>/dev/null || echo "N/A")

echo "   - Total Reviews: $TOTAL_REVIEWS"
echo "   - Pending Reviews: $PENDING"
echo "   - Total Decisions: $DECISIONS"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "2. FRONTEND ENVIRONMENT VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

cd /home/juan/vertice-dev/frontend

# Frontend environment tests
run_test "Frontend .env exists" "test -f .env"
run_test "Frontend .env has VITE_HITL_API_URL" "grep -q 'VITE_HITL_API_URL' .env"
run_test "HITLConsole component exists" "test -f src/components/admin/HITLConsole/HITLConsole.jsx"
run_test "useReviewQueue hook exists" "test -f src/components/admin/HITLConsole/hooks/useReviewQueue.js"
run_test "AdminDashboard imports HITLConsole" "grep -q 'HITLConsole' /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "3. COMPONENT STRUCTURE VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Component file tests
run_test "ReviewQueue component" "test -f src/components/admin/HITLConsole/components/ReviewQueue.jsx"
run_test "ReviewDetails component" "test -f src/components/admin/HITLConsole/components/ReviewDetails.jsx"
run_test "DecisionPanel component" "test -f src/components/admin/HITLConsole/components/DecisionPanel.jsx"
run_test "HITLStats component" "test -f src/components/admin/HITLConsole/components/HITLStats.jsx"

# Hook tests
run_test "useReviewQueue hook" "test -f src/components/admin/HITLConsole/hooks/useReviewQueue.js"
run_test "useReviewDetails hook" "test -f src/components/admin/HITLConsole/hooks/useReviewDetails.js"
run_test "useHITLStats hook" "test -f src/components/admin/HITLConsole/hooks/useHITLStats.js"
run_test "useDecisionSubmit hook" "test -f src/components/admin/HITLConsole/hooks/useDecisionSubmit.js"

# Style tests
run_test "HITLConsole styles" "test -f src/components/admin/HITLConsole/HITLConsole.module.css"
run_test "ReviewQueue styles" "test -f src/components/admin/HITLConsole/components/ReviewQueue.module.css"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "4. CODE QUALITY VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Check for required imports/patterns
run_test "HITLConsole imports useState" "grep -q 'useState' src/components/admin/HITLConsole/HITLConsole.jsx"
run_test "useReviewQueue uses useQuery" "grep -q 'useQuery' src/components/admin/HITLConsole/hooks/useReviewQueue.js"
run_test "useDecisionSubmit uses useMutation" "grep -q 'useMutation' src/components/admin/HITLConsole/hooks/useDecisionSubmit.js"
run_test "ReviewQueue has PropTypes" "grep -q 'PropTypes' src/components/admin/HITLConsole/components/ReviewQueue.jsx"
run_test "DecisionPanel has PropTypes" "grep -q 'PropTypes' src/components/admin/HITLConsole/components/DecisionPanel.jsx"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "5. INTEGRATION POINTS VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# AdminDashboard integration
run_test "AdminDashboard has 'hitl' module" "grep -q \"id: 'hitl'\" /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx"
run_test "AdminDashboard renders HITLConsole" "grep -q \"case 'hitl':\" /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx"
run_test "AdminDashboard imports HITLConsole" "grep -q \"HITLConsole\" /home/juan/vertice-dev/frontend/src/components/AdminDashboard.jsx"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "6. API ENDPOINT SIMULATION (Frontend Perspective)"
echo "═════════════════════════════════════════════════════════════════════"

# Simulate what the frontend would request
echo "   Testing API calls that frontend components would make..."

# Get initial reviews (ReviewQueue)
if curl -sf "http://localhost:8003/hitl/reviews?limit=50" -H "Origin: http://localhost:5173" | grep -q "reviews"; then
    echo -e "   ${GREEN}✅${NC} ReviewQueue initial fetch"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${RED}❌${NC} ReviewQueue initial fetch"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Filter by severity (ReviewQueue filter)
if curl -sf "http://localhost:8003/hitl/reviews?severity=critical" -H "Origin: http://localhost:5173" | grep -q "reviews"; then
    echo -e "   ${GREEN}✅${NC} ReviewQueue filter by severity"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${RED}❌${NC} ReviewQueue filter by severity"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Get stats (HITLStats)
if curl -sf "http://localhost:8003/hitl/reviews/stats" -H "Origin: http://localhost:5173" | grep -q "pending_reviews"; then
    echo -e "   ${GREEN}✅${NC} HITLStats fetch"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "   ${RED}❌${NC} HITLStats fetch"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Get first APV for details (ReviewDetails)
FIRST_APV=$(curl -s "http://localhost:8003/hitl/reviews?limit=1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['reviews'][0]['apv_id'] if data['reviews'] else '')" 2>/dev/null || echo "")
if [ -n "$FIRST_APV" ]; then
    if curl -sf "http://localhost:8003/hitl/reviews/$FIRST_APV" -H "Origin: http://localhost:5173" | grep -q "apv_id"; then
        echo -e "   ${GREEN}✅${NC} ReviewDetails fetch (APV: $FIRST_APV)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌${NC} ReviewDetails fetch"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

# Submit decision (DecisionPanel)
DECISION_PAYLOAD=$(cat <<EOF
{
  "apv_id": "$FIRST_APV",
  "decision": "approve",
  "justification": "Frontend integration test - patch is effective and safe",
  "confidence": 0.95,
  "reviewer_name": "Frontend Integration Test",
  "reviewer_email": "test@frontend.local"
}
EOF
)

if [ -n "$FIRST_APV" ]; then
    if curl -sf -X POST "http://localhost:8003/hitl/decisions" \
        -H "Content-Type: application/json" \
        -H "Origin: http://localhost:5173" \
        -d "$DECISION_PAYLOAD" | grep -q "decision_id"; then
        echo -e "   ${GREEN}✅${NC} DecisionPanel submit (approve)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌${NC} DecisionPanel submit"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
fi

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "7. FRONTEND BUILD VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Check if we can build successfully
echo "   Building frontend (this may take ~10s)..."
if npm run build > /tmp/frontend_build.log 2>&1; then
    echo -e "   ${GREEN}✅${NC} Frontend build successful"
    PASSED_TESTS=$((PASSED_TESTS + 1))

    # Check build output
    if [ -d "dist" ]; then
        DIST_SIZE=$(du -sh dist 2>/dev/null | cut -f1)
        echo "   📦 Build size: $DIST_SIZE"
    fi
else
    echo -e "   ${RED}❌${NC} Frontend build failed (see /tmp/frontend_build.log)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "VALIDATION SUMMARY"
echo "═════════════════════════════════════════════════════════════════════"

PASS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)

echo ""
echo "Total Tests:    $TOTAL_TESTS"
echo -e "${GREEN}✅ Passed:      $PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}❌ Failed:      $FAILED_TESTS${NC}"
else
    echo "❌ Failed:      0"
fi
echo "📊 Pass Rate:   $PASS_RATE%"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     🎉 FRONTEND INTEGRATION VALIDATED! 🎉            ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "✅ All components validated"
    echo "✅ All hooks validated"
    echo "✅ API integration working"
    echo "✅ Frontend build successful"
    echo ""
    echo "Next: Start dev server to test UI manually"
    echo "   cd /home/juan/vertice-dev/frontend"
    echo "   npm run dev"
    echo "   # Navigate to: http://localhost:5173"
    echo "   # Admin Dashboard → Tab 'HITL'"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║       ❌ SOME VALIDATIONS FAILED ❌                  ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
