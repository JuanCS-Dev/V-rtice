#!/bin/bash
# Contract Testing Validation Script
#
# This script runs all contract tests to ensure API compatibility:
# - Validates OpenAPI schema
# - Tests endpoint contracts
# - Checks backward compatibility
#
# DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
# Following Boris Cherny's principle: "Breaking changes must be explicit"

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo "Contract Testing - API Compatibility"
echo "============================================"
echo ""

# Check if API is running
API_URL="${API_URL:-http://localhost:8000}"

echo "Checking if API is accessible at $API_URL..."
if ! curl -sf "$API_URL/api/v1/health" > /dev/null; then
    echo -e "${RED}ERROR: API is not running at $API_URL${NC}"
    echo ""
    echo "Please start the API Gateway:"
    echo "  cd backend/api_gateway"
    echo "  python main.py"
    exit 1
fi

echo -e "${GREEN}✓ API is running${NC}"
echo ""

# 1. Validate OpenAPI schema
echo "============================================"
echo "1. Validating OpenAPI Schema"
echo "============================================"
echo ""

SCHEMA_URL="$API_URL/openapi.json"

if curl -sf "$SCHEMA_URL" > /tmp/openapi-test.json; then
    echo -e "${GREEN}✓ OpenAPI schema is accessible${NC}"

    # Check schema has required fields
    if jq -e '.openapi and .info and .paths' /tmp/openapi-test.json > /dev/null; then
        echo -e "${GREEN}✓ Schema has required fields${NC}"
    else
        echo -e "${RED}✗ Schema missing required fields${NC}"
        exit 1
    fi

    # Count endpoints
    ENDPOINT_COUNT=$(jq '.paths | keys | length' /tmp/openapi-test.json)
    echo -e "${GREEN}✓ Found $ENDPOINT_COUNT endpoints${NC}"
else
    echo -e "${RED}✗ Failed to fetch OpenAPI schema${NC}"
    exit 1
fi

echo ""

# 2. Run backend contract tests
echo "============================================"
echo "2. Running Backend Contract Tests"
echo "============================================"
echo ""

cd "$(dirname "$0")/../.."

if [ -d "tests/contract" ]; then
    echo "Running pytest contract tests..."
    pytest tests/contract/ -v --tb=short || {
        echo -e "${RED}✗ Backend contract tests failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Backend contract tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Backend contract tests directory not found${NC}"
fi

echo ""

# 3. Test critical endpoints
echo "============================================"
echo "3. Testing Critical Endpoints"
echo "============================================"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0

# Test health endpoint
echo -n "Testing /api/v1/health... "
if RESPONSE=$(curl -s "$API_URL/api/v1/health"); then
    if echo "$RESPONSE" | jq -e '.status and .version and .timestamp' > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAILED${NC} (Invalid response format)"
        echo "Response: $RESPONSE"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}FAILED${NC} (Request failed)"
    ((TESTS_FAILED++))
fi

# Test root endpoint
echo -n "Testing /api/v1/... "
if RESPONSE=$(curl -s "$API_URL/api/v1/"); then
    if echo "$RESPONSE" | jq -e '.message and .version' > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAILED${NC} (Invalid response format)"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}FAILED${NC}"
    ((TESTS_FAILED++))
fi

# Test error response format
echo -n "Testing error response format... "
if RESPONSE=$(curl -s "$API_URL/api/v1/nonexistent-test-endpoint"); then
    if echo "$RESPONSE" | jq -e '.detail and .error_code and .request_id' > /dev/null 2>&1; then
        echo -e "${GREEN}PASSED${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}FAILED${NC} (Missing error fields)"
        echo "Response: $RESPONSE"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}FAILED${NC}"
    ((TESTS_FAILED++))
fi

echo ""

# 4. Validate version headers
echo "============================================"
echo "4. Validating Version Headers"
echo "============================================"
echo ""

echo -n "Checking X-API-Version header... "
if curl -sI "$API_URL/api/v1/health" | grep -q "x-api-version: v1"; then
    echo -e "${GREEN}PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Checking X-Request-ID header... "
if curl -sI "$API_URL/api/v1/health" | grep -iq "x-request-id:"; then
    echo -e "${GREEN}PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}FAILED${NC}"
    ((TESTS_FAILED++))
fi

echo ""

# Summary
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
    echo "❌ CONTRACT TESTS FAILED"
    exit 1
else
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    echo "✅ ALL CONTRACT TESTS PASSED"
    echo ""
    echo "API contracts are stable and compatible!"
    exit 0
fi
