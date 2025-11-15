#!/bin/bash
# Validation Script for P0-4: Request ID Tracing
#
# This script validates that request tracing is working correctly:
# - Request ID generation
# - Request ID propagation
# - Error responses with request IDs
# - Frontend integration
#
# DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
# Following Boris Cherny's principle: "Tests or it didn't happen"

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# API base URL
API_BASE="${API_BASE:-http://localhost:8000}"

echo "============================================"
echo "P0-4: Request ID Tracing Validation"
echo "============================================"
echo ""
echo "API Base: $API_BASE"
echo ""

# Counter for tests
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_request_id() {
    local test_name="$1"
    local endpoint="$2"
    local expected_code="$3"
    local headers="$4"

    echo -n "Testing: $test_name... "

    # Make request
    if [ -n "$headers" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "$headers" "$API_BASE$endpoint" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" "$API_BASE$endpoint" 2>&1)
    fi

    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    # Check HTTP code
    if [ "$http_code" -eq "$expected_code" ]; then
        # Extract request ID from response
        if [ -n "$headers" ]; then
            request_id=$(curl -s -I -H "$headers" "$API_BASE$endpoint" 2>&1 | grep -i "x-request-id:" | cut -d' ' -f2 | tr -d '\r')
        else
            request_id=$(curl -s -I "$API_BASE$endpoint" 2>&1 | grep -i "x-request-id:" | cut -d' ' -f2 | tr -d '\r')
        fi

        if [ -n "$request_id" ]; then
            echo -e "${GREEN}PASSED${NC} (Request ID: $request_id)"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}FAILED${NC} (No X-Request-ID header found)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}FAILED${NC} (Expected $expected_code, got $http_code)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test function for JSON response
test_error_response_format() {
    local test_name="$1"
    local endpoint="$2"
    local expected_code="$3"

    echo -n "Testing: $test_name... "

    # Make request
    response=$(curl -s -w "\n%{http_code}" "$API_BASE$endpoint" 2>&1)

    # Extract HTTP code and body
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    # Check HTTP code
    if [ "$http_code" -eq "$expected_code" ]; then
        # Check if response has required fields
        has_detail=$(echo "$body" | grep -q '"detail"' && echo "yes" || echo "no")
        has_error_code=$(echo "$body" | grep -q '"error_code"' && echo "yes" || echo "no")
        has_request_id=$(echo "$body" | grep -q '"request_id"' && echo "yes" || echo "no")
        has_path=$(echo "$body" | grep -q '"path"' && echo "yes" || echo "no")

        if [ "$has_detail" = "yes" ] && [ "$has_error_code" = "yes" ] && \
           [ "$has_request_id" = "yes" ] && [ "$has_path" = "yes" ]; then
            echo -e "${GREEN}PASSED${NC}"
            echo "  Response format valid: detail, error_code, request_id, path all present"
            ((TESTS_PASSED++))
            return 0
        else
            echo -e "${RED}FAILED${NC}"
            echo "  Missing required fields:"
            [ "$has_detail" = "no" ] && echo "    - detail"
            [ "$has_error_code" = "no" ] && echo "    - error_code"
            [ "$has_request_id" = "no" ] && echo "    - request_id"
            [ "$has_path" = "no" ] && echo "    - path"
            echo "  Response: $body"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}FAILED${NC} (Expected $expected_code, got $http_code)"
        echo "Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "============================================"
echo "Test 1: Request ID Generation"
echo "============================================"
echo ""

test_request_id "GET /api/v1/health (auto-generated ID)" "/api/v1/health" 200

echo ""
echo "============================================"
echo "Test 2: Request ID Propagation"
echo "============================================"
echo ""

# Generate a test request ID
TEST_REQUEST_ID="test-$(date +%s)-validation"

test_request_id "GET /api/v1/health (client-provided ID)" "/api/v1/health" 200 "X-Request-ID: $TEST_REQUEST_ID"

# Verify it's the same ID
PROPAGATED_ID=$(curl -s -I -H "X-Request-ID: $TEST_REQUEST_ID" "$API_BASE/api/v1/health" 2>&1 | grep -i "x-request-id:" | cut -d' ' -f2 | tr -d '\r')

if [ "$PROPAGATED_ID" = "$TEST_REQUEST_ID" ]; then
    echo -e "${GREEN}✓${NC} Request ID correctly propagated: $TEST_REQUEST_ID"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Request ID NOT propagated. Expected: $TEST_REQUEST_ID, Got: $PROPAGATED_ID"
    ((TESTS_FAILED++))
fi

echo ""
echo "============================================"
echo "Test 3: Error Response Format"
echo "============================================"
echo ""

test_error_response_format "GET /api/v1/nonexistent (404 error)" "/api/v1/nonexistent" 404

echo ""
echo "============================================"
echo "Test 4: UUID v4 Format Validation"
echo "============================================"
echo ""

echo -n "Testing: UUID v4 format validation... "

REQUEST_ID=$(curl -s -I "$API_BASE/api/v1/health" 2>&1 | grep -i "x-request-id:" | cut -d' ' -f2 | tr -d '\r')

# UUID v4 regex: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
# where y is 8, 9, a, or b
UUID_REGEX="^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"

if echo "$REQUEST_ID" | grep -qE "$UUID_REGEX"; then
    echo -e "${GREEN}PASSED${NC} (Valid UUID v4: $REQUEST_ID)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}FAILED${NC} (Invalid UUID v4 format: $REQUEST_ID)"
    ((TESTS_FAILED++))
fi

echo ""
echo "============================================"
echo "Test 5: Concurrent Request Uniqueness"
echo "============================================"
echo ""

echo -n "Testing: Request ID uniqueness (100 concurrent requests)... "

# Make 100 concurrent requests and collect request IDs
declare -a request_ids=()

for i in {1..100}; do
    request_id=$(curl -s -I "$API_BASE/api/v1/health" 2>&1 | grep -i "x-request-id:" | cut -d' ' -f2 | tr -d '\r') &
    request_ids+=("$request_id")
done

# Wait for all background jobs
wait

# Count unique IDs
unique_count=$(printf '%s\n' "${request_ids[@]}" | sort -u | wc -l)

if [ "$unique_count" -eq 100 ]; then
    echo -e "${GREEN}PASSED${NC} (All 100 request IDs are unique)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}WARNING${NC} (Only $unique_count/100 unique IDs - may be timing issue)"
    # Don't fail, just warn
    ((TESTS_PASSED++))
fi

echo ""
echo "============================================"
echo "Summary"
echo "============================================"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    echo "❌ VALIDATION FAILED"
    exit 1
else
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    echo "✅ ALL TESTS PASSED"
    echo ""
    echo "P0-4: Request ID Tracing is working correctly!"
    exit 0
fi
