#!/bin/bash
# ============================================================================
# Secret Validation Test Script
# ============================================================================
# This script validates that the auth service properly enforces secret
# requirements and fails fast when configuration is invalid.
#
# Following Boris Cherny's principle: "If it doesn't have tests, it's not production"
# ============================================================================

set -e  # Exit on error

echo "🔒 Testing JWT Secret Validation"
echo "================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local expected_result="$2"  # "fail" or "success"
    local test_command="$3"

    echo -n "TEST: $test_name ... "

    if eval "$test_command" > /dev/null 2>&1; then
        actual_result="success"
    else
        actual_result="fail"
    fi

    if [ "$actual_result" == "$expected_result" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (expected: $expected_result, got: $actual_result)"
        ((TESTS_FAILED++))
    fi
}

echo "📋 Test Suite: Secret Validation"
echo ""

# ----------------------------------------------------------------------------
# Test 1: Missing JWT_SECRET_KEY should fail
# ----------------------------------------------------------------------------
run_test \
    "Startup fails without JWT_SECRET_KEY" \
    "fail" \
    "unset JWT_SECRET_KEY; python -c 'from main import validate_secrets; validate_secrets()'"

# ----------------------------------------------------------------------------
# Test 2: Short key (< 32 chars) should fail
# ----------------------------------------------------------------------------
run_test \
    "Startup fails with key < 32 chars" \
    "fail" \
    "JWT_SECRET_KEY='short_key' python -c 'from main import validate_secrets; validate_secrets()'"

# ----------------------------------------------------------------------------
# Test 3: Weak/default key should fail
# ----------------------------------------------------------------------------
run_test \
    "Startup fails with weak key 'secret'" \
    "fail" \
    "JWT_SECRET_KEY='secret' python -c 'from main import validate_secrets; validate_secrets()'"

run_test \
    "Startup fails with default key 'your-super-secret-key'" \
    "fail" \
    "JWT_SECRET_KEY='your-super-secret-key' python -c 'from main import validate_secrets; validate_secrets()'"

# ----------------------------------------------------------------------------
# Test 4: Valid strong key should succeed
# ----------------------------------------------------------------------------
SECURE_KEY=$(openssl rand -hex 32)
run_test \
    "Startup succeeds with valid 64-char key" \
    "success" \
    "JWT_SECRET_KEY='$SECURE_KEY' python -c 'from main import validate_secrets; validate_secrets()'"

# ----------------------------------------------------------------------------
# Test 5: Minimum 32-char key should succeed
# ----------------------------------------------------------------------------
run_test \
    "Startup succeeds with minimum 32-char key" \
    "success" \
    "JWT_SECRET_KEY='12345678901234567890123456789012' python -c 'from main import validate_secrets; validate_secrets()'"

# ----------------------------------------------------------------------------
# Results Summary
# ----------------------------------------------------------------------------
echo ""
echo "================================="
echo "📊 Test Results Summary"
echo "================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🎉 Secret validation is working correctly."
    echo "   The service will:"
    echo "   - ✅ Reject missing JWT_SECRET_KEY"
    echo "   - ✅ Reject short keys (< 32 chars)"
    echo "   - ✅ Reject known weak/default keys"
    echo "   - ✅ Accept cryptographically strong keys"
    exit 0
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    echo ""
    echo "🔧 Action required: Fix the failing tests."
    exit 1
fi
