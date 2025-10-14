#!/bin/bash
#
# HITL Integration Test Script
# Tests vcli-go HITL commands against HITL backend
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HITL_ENDPOINT="${HITL_ENDPOINT:-http://localhost:8000/api}"
HITL_USERNAME="${HITL_USERNAME:-admin}"
HITL_PASSWORD="${HITL_PASSWORD:-ChangeMe123!}"
VCLI_BIN="${VCLI_BIN:-./bin/vcli}"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

vcli_hitl() {
    "$VCLI_BIN" hitl "$@" \
        --endpoint "$HITL_ENDPOINT" \
        --username "$HITL_USERNAME" \
        --password "$HITL_PASSWORD"
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

print_header "HITL Integration Test Suite"
echo ""

print_info "Configuration:"
print_info "  HITL Endpoint: $HITL_ENDPOINT"
print_info "  HITL Username: $HITL_USERNAME"
print_info "  vcli Binary:   $VCLI_BIN"
echo ""

# Check vcli binary exists
if [ ! -f "$VCLI_BIN" ]; then
    echo -e "${RED}ERROR:${NC} vcli binary not found at $VCLI_BIN"
    echo "Build it with: /home/juan/go-sdk/bin/go build -o bin/vcli ./cmd/"
    exit 1
fi

# Check HITL backend is running
print_test "Checking HITL backend connectivity..."
if curl -s -f "$HITL_ENDPOINT/../health" > /dev/null 2>&1; then
    print_pass "HITL backend is reachable"
else
    print_fail "HITL backend is not reachable at $HITL_ENDPOINT"
    echo ""
    echo "Start HITL backend with:"
    echo "  cd /home/juan/vertice-dev/backend/services/reactive_fabric_core"
    echo "  python hitl/hitl_backend.py"
    exit 1
fi

echo ""

# ============================================================================
# TEST 1: SYSTEM STATUS
# ============================================================================

print_header "Test 1: System Status"
print_test "Running: vcli hitl status"

if vcli_hitl status > /tmp/hitl_test_status.txt 2>&1; then
    if grep -q "HITL System Status" /tmp/hitl_test_status.txt; then
        print_pass "Status command successful"
        cat /tmp/hitl_test_status.txt
    else
        print_fail "Status output unexpected"
        cat /tmp/hitl_test_status.txt
    fi
else
    print_fail "Status command failed"
    cat /tmp/hitl_test_status.txt
fi

echo ""

# ============================================================================
# TEST 2: LIST DECISIONS
# ============================================================================

print_header "Test 2: List Pending Decisions"
print_test "Running: vcli hitl list"

if vcli_hitl list > /tmp/hitl_test_list.txt 2>&1; then
    if grep -q -E "(ANALYSIS_ID|No pending decisions)" /tmp/hitl_test_list.txt; then
        print_pass "List command successful"
        cat /tmp/hitl_test_list.txt
    else
        print_fail "List output unexpected"
        cat /tmp/hitl_test_list.txt
    fi
else
    print_fail "List command failed"
    cat /tmp/hitl_test_list.txt
fi

echo ""

# ============================================================================
# TEST 3: LIST WITH PRIORITY FILTER
# ============================================================================

print_header "Test 3: List with Priority Filter"
print_test "Running: vcli hitl list --priority critical"

if vcli_hitl list --priority critical > /tmp/hitl_test_list_critical.txt 2>&1; then
    if grep -q -E "(ANALYSIS_ID|No pending decisions)" /tmp/hitl_test_list_critical.txt; then
        print_pass "List with priority filter successful"
        cat /tmp/hitl_test_list_critical.txt
    else
        print_fail "List with priority output unexpected"
        cat /tmp/hitl_test_list_critical.txt
    fi
else
    print_fail "List with priority failed"
    cat /tmp/hitl_test_list_critical.txt
fi

echo ""

# ============================================================================
# TEST 4: STATISTICS
# ============================================================================

print_header "Test 4: Decision Statistics"
print_test "Running: vcli hitl stats"

if vcli_hitl stats > /tmp/hitl_test_stats.txt 2>&1; then
    if grep -q "HITL Decision Statistics" /tmp/hitl_test_stats.txt; then
        print_pass "Stats command successful"
        cat /tmp/hitl_test_stats.txt
    else
        print_fail "Stats output unexpected"
        cat /tmp/hitl_test_stats.txt
    fi
else
    print_fail "Stats command failed"
    cat /tmp/hitl_test_stats.txt
fi

echo ""

# ============================================================================
# TEST 5: JSON OUTPUT
# ============================================================================

print_header "Test 5: JSON Output Format"
print_test "Running: vcli hitl list --output json"

if vcli_hitl list --output json > /tmp/hitl_test_json.txt 2>&1; then
    if python3 -m json.tool /tmp/hitl_test_json.txt > /dev/null 2>&1; then
        print_pass "JSON output is valid"
        echo "Sample JSON:"
        head -20 /tmp/hitl_test_json.txt
    else
        print_fail "JSON output is invalid"
        cat /tmp/hitl_test_json.txt
    fi
else
    print_fail "JSON output command failed"
    cat /tmp/hitl_test_json.txt
fi

echo ""

# ============================================================================
# TEST 6: SHOW DECISION (if any exist)
# ============================================================================

print_header "Test 6: Show Decision Details"

# Get first analysis ID from list
ANALYSIS_ID=$(vcli_hitl list --output json 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['analysis_id']) if data else ''" 2>/dev/null || echo "")

if [ -z "$ANALYSIS_ID" ]; then
    print_info "No pending decisions to show - skipping test"
else
    print_test "Running: vcli hitl show $ANALYSIS_ID"

    if vcli_hitl show "$ANALYSIS_ID" > /tmp/hitl_test_show.txt 2>&1; then
        if grep -q "Decision:" /tmp/hitl_test_show.txt; then
            print_pass "Show command successful"
            cat /tmp/hitl_test_show.txt
        else
            print_fail "Show output unexpected"
            cat /tmp/hitl_test_show.txt
        fi
    else
        print_fail "Show command failed"
        cat /tmp/hitl_test_show.txt
    fi
fi

echo ""

# ============================================================================
# TEST 7: AUTHENTICATION ERROR HANDLING
# ============================================================================

print_header "Test 7: Authentication Error Handling"
print_test "Running: vcli hitl status with wrong password"

if "$VCLI_BIN" hitl status \
    --endpoint "$HITL_ENDPOINT" \
    --username "$HITL_USERNAME" \
    --password "wrong_password" > /tmp/hitl_test_auth_fail.txt 2>&1; then
    print_fail "Command should have failed with wrong password"
    cat /tmp/hitl_test_auth_fail.txt
else
    if grep -q -i "authentication failed" /tmp/hitl_test_auth_fail.txt; then
        print_pass "Authentication error handled correctly"
    else
        print_fail "Unexpected error message"
        cat /tmp/hitl_test_auth_fail.txt
    fi
fi

echo ""

# ============================================================================
# TEST 8: HELP TEXT
# ============================================================================

print_header "Test 8: Help Text"
print_test "Running: vcli hitl --help"

if "$VCLI_BIN" hitl --help > /tmp/hitl_test_help.txt 2>&1; then
    if grep -q "Human-in-the-Loop" /tmp/hitl_test_help.txt; then
        print_pass "Help text displays correctly"
    else
        print_fail "Help text incomplete"
        cat /tmp/hitl_test_help.txt
    fi
else
    print_fail "Help command failed"
    cat /tmp/hitl_test_help.txt
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

print_header "Test Summary"
echo ""
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi
