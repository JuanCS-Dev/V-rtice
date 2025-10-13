#!/bin/bash

# HITL Console - Validation Script
# Tests all components of FASE 3 (Wargaming + HITL)

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          HITL CONSOLE - VALIDATION SCRIPT                         ║"
echo "║                    FASE 3 COMPLETE                                ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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
echo "1. PYTHON SYNTAX VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Backend files
run_test "Wargaming workflow_generator" "python3 -m py_compile wargaming/workflow_generator.py"
run_test "Wargaming exploit_templates" "python3 -m py_compile wargaming/exploit_templates.py"
run_test "Wargaming evidence_collector" "python3 -m py_compile wargaming/evidence_collector.py"
run_test "Wargaming verdict_calculator" "python3 -m py_compile wargaming/verdict_calculator.py"
run_test "Wargaming orchestrator" "python3 -m py_compile wargaming/wargame_orchestrator.py"

run_test "HITL models" "python3 -m py_compile hitl/models.py"
run_test "HITL decision_engine" "python3 -m py_compile hitl/decision_engine.py"
run_test "HITL API main" "python3 -m py_compile hitl/api/main.py"
run_test "HITL API apv_review" "python3 -m py_compile hitl/api/endpoints/apv_review.py"
run_test "HITL API decisions" "python3 -m py_compile hitl/api/endpoints/decisions.py"

# Test files
run_test "Test data generator" "python3 -m py_compile hitl/test_data_generator.py"
run_test "Test mock API" "python3 -m py_compile hitl/test_mock_api.py"
run_test "Test E2E runner" "python3 -m py_compile hitl/test_e2e_runner.py"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "2. API ENDPOINT VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Check if mock API is running
if ! curl -s http://localhost:8003/hitl/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Mock API not running on :8003${NC}"
    echo "   Skipping API tests..."
    echo "   To run API tests, start: PYTHONPATH=. python3 -m hitl.test_mock_api"
else
    run_test "Health endpoint" "curl -sf http://localhost:8003/hitl/health | grep -q healthy"
    run_test "Reviews endpoint" "curl -sf http://localhost:8003/hitl/reviews | grep -q reviews"
    run_test "Stats endpoint" "curl -sf http://localhost:8003/hitl/reviews/stats | grep -q pending_reviews"
    run_test "Filter by severity" "curl -sf 'http://localhost:8003/hitl/reviews?severity=critical' | grep -q reviews"

    echo ""
    echo "   📊 API Summary:"
    REVIEWS=$(curl -s http://localhost:8003/hitl/reviews | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])" 2>/dev/null || echo "N/A")
    PENDING=$(curl -s http://localhost:8003/hitl/reviews/stats | python3 -c "import sys, json; print(json.load(sys.stdin)['pending_reviews'])" 2>/dev/null || echo "N/A")
    DECISIONS=$(curl -s http://localhost:8003/hitl/reviews/stats | python3 -c "import sys, json; print(json.load(sys.stdin)['total_decisions'])" 2>/dev/null || echo "N/A")

    echo "   - Total Reviews: $REVIEWS"
    echo "   - Pending: $PENDING"
    echo "   - Total Decisions: $DECISIONS"
fi

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "3. FRONTEND BUILD VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Frontend build
cd /home/juan/vertice-dev/frontend
run_test "Frontend build" "npm run build"
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "4. FILE STRUCTURE VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

# Check key files exist
run_test "Wargaming files" "test -f wargaming/workflow_generator.py && test -f wargaming/wargame_orchestrator.py"
run_test "HITL Backend files" "test -f hitl/models.py && test -f hitl/decision_engine.py"
run_test "HITL API files" "test -f hitl/api/main.py && test -f hitl/api/endpoints/apv_review.py"
run_test "Test files" "test -f hitl/test_data_generator.py && test -f hitl/test_mock_api.py"
run_test "Frontend components" "test -f /home/juan/vertice-dev/frontend/src/components/admin/HITLConsole/HITLConsole.jsx"
run_test "Frontend hooks" "test -f /home/juan/vertice-dev/frontend/src/components/admin/HITLConsole/hooks/useReviewQueue.js"
run_test "Environment config" "test -f /home/juan/vertice-dev/frontend/.env"

echo ""
echo "═════════════════════════════════════════════════════════════════════"
echo "5. DOCUMENTATION VALIDATION"
echo "═════════════════════════════════════════════════════════════════════"

run_test "Docs: FASE 3 Integration" "test -f hitl/FASE_3_INTEGRATION_COMPLETE.md"
run_test "Docs: Quick Start Guide" "test -f hitl/QUICK_START_GUIDE.md"
run_test "Docs: FASE 3 Final Summary" "test -f FASE_3_FINAL_SUMMARY.md"
run_test "Docs: FASE 3.5 E2E Report" "test -f FASE_3.5_E2E_TESTING_REPORT.md"
run_test "Docs: FASE 3.6 Frontend" "test -f FASE_3.6_FRONTEND_INTEGRATION_REPORT.md"

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
    echo -e "${GREEN}║           🎉 ALL VALIDATIONS PASSED! 🎉              ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║         ❌ SOME VALIDATIONS FAILED ❌                ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════╝${NC}"
    exit 1
fi
