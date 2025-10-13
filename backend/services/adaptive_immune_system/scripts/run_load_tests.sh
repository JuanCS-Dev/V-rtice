#!/bin/bash
#
# Run Load Tests for HITL API
# FASE 3.11 - Milestone 3.11.1
#
# Usage:
#   ./scripts/run_load_tests.sh [scenario]
#
# Scenarios:
#   all         - Run all scenarios (default)
#   read-heavy  - Read-heavy workload
#   write-heavy - Write-heavy workload
#   health      - Health check monitoring

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
HOST="${HITL_API_URL:-http://localhost:8003}"
RESULTS_DIR="tests/load/results/$(date +%Y%m%d_%H%M%S)"
SCENARIO="${1:-all}"

echo "=================================================="
echo "HITL API Load Testing"
echo "=================================================="
echo "Host: $HOST"
echo "Scenario: $SCENARIO"
echo "Results: $RESULTS_DIR"
echo "=================================================="
echo

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to check if API is healthy
check_api_health() {
    echo -n "Checking API health... "
    if curl -sf "$HOST/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ API is not responding${NC}"
        echo
        echo "Please start the API first:"
        echo "  docker-compose up -d adaptive_immune_system"
        echo
        exit 1
    fi
}

# Function to run a single load test
run_load_test() {
    local name=$1
    local user_class=$2
    local users=$3
    local spawn_rate=$4
    local duration=$5

    echo
    echo "=================================================="
    echo "Running: $name"
    echo "=================================================="
    echo "Users: $users"
    echo "Spawn rate: $spawn_rate users/s"
    echo "Duration: $duration"
    echo "User class: $user_class"
    echo

    local output_base="$RESULTS_DIR/${name// /_}"

    # Run locust headless
    cd tests/load
    locust -f locustfile.py "$user_class" \
        --headless \
        --users "$users" \
        --spawn-rate "$spawn_rate" \
        --run-time "$duration" \
        --host "$HOST" \
        --html "$output_base.html" \
        --csv "$output_base" \
        2>&1 | tee "$output_base.log"

    local exit_code=${PIPESTATUS[0]}
    cd ../..

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ $name completed successfully${NC}"
    else
        echo -e "${RED}✗ $name failed (exit code: $exit_code)${NC}"
    fi

    return $exit_code
}

# Function to analyze results
analyze_results() {
    echo
    echo "=================================================="
    echo "Test Results Summary"
    echo "=================================================="
    echo

    for csv_file in "$RESULTS_DIR"/*_stats.csv; do
        if [ -f "$csv_file" ]; then
            local test_name=$(basename "$csv_file" _stats.csv)
            echo "--- $test_name ---"

            # Extract key metrics from CSV (skip header, get Aggregated row)
            local aggregated=$(grep "Aggregated" "$csv_file" || echo "")

            if [ -n "$aggregated" ]; then
                # CSV format: Type,Name,Request Count,Failure Count,Median,Average,Min,Max,Average size,RPS,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%
                local request_count=$(echo "$aggregated" | cut -d',' -f3)
                local failure_count=$(echo "$aggregated" | cut -d',' -f4)
                local median=$(echo "$aggregated" | cut -d',' -f5)
                local p95=$(echo "$aggregated" | cut -d',' -f16)
                local p99=$(echo "$aggregated" | cut -d',' -f18)
                local rps=$(echo "$aggregated" | cut -d',' -f10)

                # Calculate failure rate
                local failure_rate=$(awk "BEGIN {printf \"%.2f\", ($failure_count / $request_count) * 100}")

                echo "  Total requests: $request_count"
                echo "  Failures: $failure_count ($failure_rate%)"
                echo "  Median: ${median}ms"
                echo "  P95: ${p95}ms"
                echo "  P99: ${p99}ms"
                echo "  RPS: $rps"

                # Validate SLAs
                echo
                echo "  SLA Validation:"

                # P95 < 500ms
                if (( $(echo "$p95 < 500" | bc -l) )); then
                    echo -e "    ${GREEN}✓ P95 latency: ${p95}ms < 500ms${NC}"
                else
                    echo -e "    ${RED}✗ P95 latency: ${p95}ms > 500ms${NC}"
                fi

                # Error rate < 0.1%
                if (( $(echo "$failure_rate < 0.1" | bc -l) )); then
                    echo -e "    ${GREEN}✓ Error rate: ${failure_rate}% < 0.1%${NC}"
                else
                    echo -e "    ${RED}✗ Error rate: ${failure_rate}% > 0.1%${NC}"
                fi

                # Throughput > 100 req/s
                if (( $(echo "$rps > 100" | bc -l) )); then
                    echo -e "    ${GREEN}✓ Throughput: ${rps} > 100 req/s${NC}"
                else
                    echo -e "    ${YELLOW}⚠ Throughput: ${rps} < 100 req/s${NC}"
                fi
            else
                echo "  No aggregated data found"
            fi

            echo
        fi
    done

    echo "HTML reports generated:"
    ls -1 "$RESULTS_DIR"/*.html | sed 's/^/  /'
    echo
}

# Main execution
main() {
    # Check API health
    check_api_health

    # Initialize exit code
    overall_exit=0

    # Run scenarios
    case "$SCENARIO" in
        all)
            echo "Running all scenarios..."
            run_load_test "Read Heavy Workload" "ReadHeavyUser" 100 10 "5m" || overall_exit=1
            run_load_test "Write Heavy Workload" "WriteHeavyUser" 50 5 "5m" || overall_exit=1
            run_load_test "Health Check Monitoring" "HealthCheckUser" 5 1 "2m" || overall_exit=1
            ;;
        read-heavy)
            run_load_test "Read Heavy Workload" "ReadHeavyUser" 100 10 "5m" || overall_exit=1
            ;;
        write-heavy)
            run_load_test "Write Heavy Workload" "WriteHeavyUser" 50 5 "5m" || overall_exit=1
            ;;
        health)
            run_load_test "Health Check Monitoring" "HealthCheckUser" 5 1 "2m" || overall_exit=1
            ;;
        *)
            echo "Unknown scenario: $SCENARIO"
            echo "Valid scenarios: all, read-heavy, write-heavy, health"
            exit 1
            ;;
    esac

    # Analyze results
    analyze_results

    # Final status
    echo "=================================================="
    if [ $overall_exit -eq 0 ]; then
        echo -e "${GREEN}✓ All load tests PASSED${NC}"
    else
        echo -e "${RED}✗ Some load tests FAILED${NC}"
    fi
    echo "=================================================="

    exit $overall_exit
}

# Run main
main
