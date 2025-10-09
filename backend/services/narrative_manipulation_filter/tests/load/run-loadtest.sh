#!/bin/bash

# ============================================================================
# Load Testing Runner - Cognitive Defense System
# Automates load testing with Locust or k6
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_HOST="http://localhost:8013"
DEFAULT_USERS=100
DEFAULT_DURATION="5m"
DEFAULT_SPAWN_RATE=10

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_header "Checking Dependencies"

    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3: $(python3 --version)"
    else
        print_error "Python 3 not found"
        exit 1
    fi

    # Check Locust
    if command -v locust &> /dev/null; then
        print_success "Locust: $(locust --version)"
        LOCUST_AVAILABLE=true
    else
        print_warning "Locust not installed (uv tool install locust)"
        LOCUST_AVAILABLE=false
    fi

    # Check k6
    if command -v k6 &> /dev/null; then
        print_success "k6: $(k6 version --no-usage-report)"
        K6_AVAILABLE=true
    else
        print_warning "k6 not installed (https://k6.io/docs/getting-started/installation/)"
        K6_AVAILABLE=false
    fi

    # Check jq (for JSON parsing)
    if command -v jq &> /dev/null; then
        print_success "jq: $(jq --version)"
    else
        print_warning "jq not installed (optional, for JSON parsing)"
    fi

    echo ""
}

check_service_health() {
    local host=$1
    print_info "Checking service health at $host"

    if curl -sf "$host/health" > /dev/null 2>&1; then
        print_success "Service is healthy"
        return 0
    else
        print_error "Service is not responding at $host"
        return 1
    fi
}

run_locust() {
    local host=$1
    local users=$2
    local duration=$3
    local spawn_rate=$4
    local mode=$5

    print_header "Running Locust Load Test"
    print_info "Host: $host"
    print_info "Users: $users"
    print_info "Duration: $duration"
    print_info "Spawn Rate: $spawn_rate/sec"
    print_info "Mode: $mode"
    echo ""

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local results_dir="results/locust_${timestamp}"
    mkdir -p "$results_dir"

    if [ "$mode" == "headless" ]; then
        # Headless mode with reports
        locust -f locustfile.py \
            --host="$host" \
            --users="$users" \
            --spawn-rate="$spawn_rate" \
            --run-time="$duration" \
            --headless \
            --csv="$results_dir/results" \
            --html="$results_dir/report.html" \
            --loglevel INFO

        print_success "Results saved to $results_dir/"
        print_info "HTML Report: $results_dir/report.html"
        print_info "CSV Results: $results_dir/results_*.csv"

    else
        # Web UI mode
        print_info "Starting Locust Web UI at http://localhost:8089"
        locust -f locustfile.py --host="$host"
    fi
}

run_k6() {
    local host=$1
    local duration=$2
    local vus=$3

    print_header "Running k6 Load Test"
    print_info "Host: $host"
    print_info "Virtual Users: $vus"
    print_info "Duration: $duration"
    echo ""

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local results_dir="results/k6_${timestamp}"
    mkdir -p "$results_dir"

    # Run k6 with JSON output
    k6 run k6-loadtest.js \
        --env BASE_URL="$host" \
        --vus="$vus" \
        --duration="$duration" \
        --out json="$results_dir/results.json" \
        --summary-export="$results_dir/summary.json"

    print_success "Results saved to $results_dir/"
    print_info "JSON Results: $results_dir/results.json"
    print_info "Summary: $results_dir/summary.json"

    # Generate simple report if jq is available
    if command -v jq &> /dev/null && [ -f "$results_dir/summary.json" ]; then
        echo ""
        print_header "Test Summary"
        jq -r '
            "Total Requests: \(.metrics.http_reqs.values.count // 0)",
            "Failed Requests: \(.metrics.http_req_failed.values.rate * 100 // 0)%",
            "Avg Response Time: \(.metrics.http_req_duration.values.avg // 0)ms",
            "P95 Response Time: \(.metrics.http_req_duration.values["p(95)"] // 0)ms",
            "P99 Response Time: \(.metrics.http_req_duration.values["p(99)"] // 0)ms"
        ' "$results_dir/summary.json"
    fi
}

run_quick_test() {
    local host=$1

    print_header "Running Quick Smoke Test"

    if [ "$LOCUST_AVAILABLE" = true ]; then
        locust -f locustfile.py \
            --host="$host" \
            --users=10 \
            --spawn-rate=2 \
            --run-time=1m \
            --headless
    elif [ "$K6_AVAILABLE" = true ]; then
        k6 run k6-loadtest.js \
            --env BASE_URL="$host" \
            --vus=10 \
            --duration=1m
    else
        print_error "No load testing tool available"
        exit 1
    fi
}

show_usage() {
    cat << EOF
${BLUE}Cognitive Defense System - Load Testing Runner${NC}

${GREEN}Usage:${NC}
    $0 [OPTIONS] <test-type>

${GREEN}Test Types:${NC}
    locust          Run Locust load test (web UI)
    locust-headless Run Locust load test (headless with reports)
    k6              Run k6 load test
    quick           Run quick smoke test (1 min, 10 users)
    check           Check dependencies and service health

${GREEN}Options:${NC}
    -h, --host HOST       Target host (default: $DEFAULT_HOST)
    -u, --users USERS     Number of users (default: $DEFAULT_USERS)
    -d, --duration TIME   Test duration (default: $DEFAULT_DURATION)
    -r, --rate RATE       Spawn rate for Locust (default: $DEFAULT_SPAWN_RATE)
    --help                Show this help message

${GREEN}Examples:${NC}
    # Check dependencies
    $0 check

    # Quick smoke test
    $0 quick

    # Locust with custom settings
    $0 locust-headless --host https://api.vertice.dev --users 500 --duration 10m

    # k6 stress test
    $0 k6 --host http://localhost:8013 --users 200 --duration 5m

    # Locust web UI (interactive)
    $0 locust --host http://localhost:8013

EOF
}

# ============================================================================
# MAIN
# ============================================================================

# Parse arguments
HOST="$DEFAULT_HOST"
USERS="$DEFAULT_USERS"
DURATION="$DEFAULT_DURATION"
SPAWN_RATE="$DEFAULT_SPAWN_RATE"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -r|--rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            TEST_TYPE="$1"
            shift
            ;;
    esac
done

# Change to script directory
cd "$(dirname "$0")"

# Check dependencies first
check_dependencies

# Execute based on test type
case "$TEST_TYPE" in
    check)
        check_service_health "$HOST"
        ;;

    quick)
        if ! check_service_health "$HOST"; then
            exit 1
        fi
        run_quick_test "$HOST"
        ;;

    locust)
        if [ "$LOCUST_AVAILABLE" != true ]; then
            print_error "Locust is not installed"
            print_info "Install with: uv tool install locust"
            exit 1
        fi
        if ! check_service_health "$HOST"; then
            exit 1
        fi
        run_locust "$HOST" "$USERS" "$DURATION" "$SPAWN_RATE" "web"
        ;;

    locust-headless)
        if [ "$LOCUST_AVAILABLE" != true ]; then
            print_error "Locust is not installed"
            print_info "Install with: uv tool install locust"
            exit 1
        fi
        if ! check_service_health "$HOST"; then
            exit 1
        fi
        run_locust "$HOST" "$USERS" "$DURATION" "$SPAWN_RATE" "headless"
        ;;

    k6)
        if [ "$K6_AVAILABLE" != true ]; then
            print_error "k6 is not installed"
            print_info "Install from: https://k6.io/docs/getting-started/installation/"
            exit 1
        fi
        if ! check_service_health "$HOST"; then
            exit 1
        fi
        run_k6 "$HOST" "$DURATION" "$USERS"
        ;;

    "")
        print_error "No test type specified"
        echo ""
        show_usage
        exit 1
        ;;

    *)
        print_error "Unknown test type: $TEST_TYPE"
        echo ""
        show_usage
        exit 1
        ;;
esac

print_success "Load test completed!"
