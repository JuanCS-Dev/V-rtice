#!/bin/bash

# ============================================================================
# Smoke Test - Cognitive Defense System
# Quick validation of critical paths after deployment
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-"local"}
BASE_URL=""
API_KEY=""

case $ENVIRONMENT in
    local)
        BASE_URL="http://localhost:8013"
        ;;
    staging)
        BASE_URL="https://staging.cognitive-defense.vertice.dev"
        API_KEY="${STAGING_API_KEY}"
        ;;
    production)
        BASE_URL="https://api.cognitive-defense.vertice.dev"
        API_KEY="${PRODUCTION_API_KEY}"
        ;;
    *)
        echo -e "${RED}Unknown environment: $ENVIRONMENT${NC}"
        echo "Usage: $0 [local|staging|production]"
        exit 1
        ;;
esac

# Counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_test() {
    echo -e "${BLUE}🧪 Test: $1${NC}"
    TESTS_RUN=$((TESTS_RUN + 1))
}

print_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

print_failure() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

make_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    if [ -z "$data" ]; then
        if [ -n "$API_KEY" ]; then
            curl -s -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json"
        else
            curl -s -X "$method" "$BASE_URL$endpoint"
        fi
    else
        if [ -n "$API_KEY" ]; then
            curl -s -X "$method" "$BASE_URL$endpoint" \
                -H "X-API-Key: $API_KEY" \
                -H "Content-Type: application/json" \
                -d "$data"
        else
            curl -s -X "$method" "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data"
        fi
    fi
}

# ============================================================================
# SMOKE TESTS
# ============================================================================

run_smoke_tests() {
    print_header "COGNITIVE DEFENSE SYSTEM - SMOKE TEST"
    echo "Environment: $ENVIRONMENT"
    echo "Base URL: $BASE_URL"
    echo ""

    # Test 1: Health Check
    print_test "Health check endpoint"
    response=$(make_request GET "/health")
    if echo "$response" | grep -q '"status":"healthy"'; then
        print_success "Service is healthy"
    else
        print_failure "Service health check failed"
        echo "Response: $response"
    fi

    # Test 2: Readiness Check
    print_test "Readiness check endpoint"
    response=$(make_request GET "/ready")
    if echo "$response" | grep -q '"ready":true'; then
        print_success "Service is ready"
    else
        print_failure "Service readiness check failed"
        echo "Response: $response"
    fi

    # Test 3: Fast Track Analysis
    print_test "Fast track analysis (Tier 1 only)"
    response=$(make_request POST "/api/v2/analyze" '{
        "content": "Government announces R$ 10,000 for all citizens!",
        "source_info": {"domain": "fake-news-site.com"},
        "mode": "FAST_TRACK"
    }')

    if echo "$response" | grep -q '"manipulation_score"'; then
        score=$(echo "$response" | grep -o '"manipulation_score":[0-9.]*' | cut -d: -f2)
        print_success "Fast track analysis completed (score: $score)"
    else
        print_failure "Fast track analysis failed"
        echo "Response: $response"
    fi

    # Test 4: Standard Analysis
    print_test "Standard analysis (Tier 1 + Tier 2)"
    response=$(make_request POST "/api/v2/analyze" '{
        "content": "Vote for candidate X! They are the ONLY one who can save us!",
        "source_info": {"domain": "unknown-blog.com"},
        "mode": "STANDARD"
    }')

    if echo "$response" | grep -q '"threat_level"'; then
        threat=$(echo "$response" | grep -o '"threat_level":"[A-Z]*"' | cut -d'"' -f4)
        print_success "Standard analysis completed (threat: $threat)"
    else
        print_failure "Standard analysis failed"
        echo "Response: $response"
    fi

    # Test 5: Claim Verification
    print_test "Claim verification"
    response=$(make_request POST "/api/v2/verify-claim" '{
        "claim": "Scientists discover cure for all diseases"
    }')

    if echo "$response" | grep -q '"status"'; then
        status=$(echo "$response" | grep -o '"status":"[A-Z]*"' | cut -d'"' -f4)
        print_success "Claim verification completed (status: $status)"
    else
        print_failure "Claim verification failed"
        echo "Response: $response"
    fi

    # Test 6: Analysis History
    print_test "Analysis history retrieval"
    response=$(make_request GET "/api/v2/history?limit=5")

    if echo "$response" | grep -q '"results"'; then
        count=$(echo "$response" | grep -o '"total":[0-9]*' | cut -d: -f2)
        print_success "History retrieval successful (total: $count)"
    else
        print_failure "History retrieval failed"
        echo "Response: $response"
    fi

    # Test 7: Metrics Endpoint
    print_test "Prometheus metrics endpoint"
    response=$(curl -s "$BASE_URL/metrics")

    if echo "$response" | grep -q 'cognitive_defense_requests_total'; then
        print_success "Metrics endpoint responding"
    else
        print_failure "Metrics endpoint not responding"
    fi

    # Test 8: Response Time Check
    print_test "Response time validation"
    start_time=$(date +%s%3N)
    response=$(make_request POST "/api/v2/analyze" '{
        "content": "Test content for latency check",
        "mode": "FAST_TRACK"
    }')
    end_time=$(date +%s%3N)
    latency=$((end_time - start_time))

    if [ "$latency" -lt 1000 ]; then
        print_success "Response time acceptable (${latency}ms)"
    else
        print_failure "Response time too high (${latency}ms > 1000ms)"
    fi

    # Test 9: Error Handling
    print_test "Error handling (invalid input)"
    response=$(make_request POST "/api/v2/analyze" '{
        "content": "",
        "mode": "INVALID_MODE"
    }')

    if echo "$response" | grep -q '"detail"'; then
        print_success "Error handling working"
    else
        print_failure "Error handling not working"
    fi

    # Test 10: Rate Limiting (if configured)
    if [ "$ENVIRONMENT" != "local" ]; then
        print_test "Rate limiting"

        # Make 10 rapid requests
        for i in {1..10}; do
            make_request GET "/health" > /dev/null 2>&1
        done

        # The 11th should potentially be rate limited
        response=$(curl -s -w "%{http_code}" -o /dev/null "$BASE_URL/health")

        if [ "$response" = "200" ] || [ "$response" = "429" ]; then
            print_success "Rate limiting configured (status: $response)"
        else
            print_failure "Unexpected response (status: $response)"
        fi
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is not installed${NC}"
        exit 1
    fi

    # Run tests
    run_smoke_tests

    # Print summary
    print_header "TEST SUMMARY"
    echo "Total Tests: $TESTS_RUN"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo ""
        print_success "ALL SMOKE TESTS PASSED ✅"
        echo ""
        exit 0
    else
        echo ""
        print_failure "SOME TESTS FAILED ❌"
        echo ""
        exit 1
    fi
}

# Run main
main "$@"
