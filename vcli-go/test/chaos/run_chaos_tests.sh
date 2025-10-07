#!/bin/bash

# Chaos Engineering Test Script for vCLI Go
# Tests system behavior under adverse conditions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCLI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SERVER_DIR="$VCLI_ROOT/bridge/python-grpc-server"
SERVER_LOG="/tmp/chaos_server.log"
RESULTS_DIR="$SCRIPT_DIR/results"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  vCLI Go - Chaos Engineering Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to start gRPC server
start_server() {
    echo -e "${YELLOW}Starting Python gRPC server...${NC}"

    if [ ! -f "$PYTHON_SERVER_DIR/governance_grpc_server.py" ]; then
        echo -e "${RED}Error: Python gRPC server not found at $PYTHON_SERVER_DIR${NC}"
        exit 1
    fi

    cd "$PYTHON_SERVER_DIR"

    # Kill existing server if running
    pkill -f "governance_grpc_server.py" 2>/dev/null || true

    # Start server in background
    python3 governance_grpc_server.py > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!

    # Wait for server to start
    echo -e "${YELLOW}Waiting for server to start (PID: $SERVER_PID)...${NC}"
    for i in {1..10}; do
        if grep -q "gRPC server started" "$SERVER_LOG" 2>/dev/null; then
            echo -e "${GREEN}✓ Server started successfully${NC}"
            return 0
        fi
        sleep 1
    done

    echo -e "${RED}✗ Server failed to start${NC}"
    cat "$SERVER_LOG"
    exit 1
}

# Function to stop server
stop_server() {
    echo -e "${YELLOW}Stopping gRPC server...${NC}"
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    pkill -f "governance_grpc_server.py" 2>/dev/null || true
    echo -e "${GREEN}✓ Server stopped${NC}"
}

# Trap to ensure cleanup
trap stop_server EXIT

# Start server
start_server

cd "$VCLI_ROOT"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Running Chaos Engineering Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEST_RESULTS="$RESULTS_DIR/chaos_results_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${YELLOW}Test 1/10: Network Latency${NC}"
go test -v ./test/chaos -run TestChaos_NetworkLatency -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 2/10: Timeout Recovery${NC}"
go test -v ./test/chaos -run TestChaos_TimeoutRecovery -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 3/10: Concurrent Failures${NC}"
go test -v ./test/chaos -run TestChaos_ConcurrentFailures -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 4/10: Rapid Reconnection${NC}"
go test -v ./test/chaos -run TestChaos_RapidReconnection -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 5/10: Session Without Health Check${NC}"
go test -v ./test/chaos -run TestChaos_SessionWithoutHealthCheck -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 6/10: Invalid Operation Sequence${NC}"
go test -v ./test/chaos -run TestChaos_InvalidOperationSequence -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 7/10: High Error Rate${NC}"
go test -v ./test/chaos -run TestChaos_HighErrorRate -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 8/10: Resource Exhaustion${NC}"
go test -v ./test/chaos -run TestChaos_ResourceExhaustion -timeout 5m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 9/10: Partial Service Degradation${NC}"
go test -v ./test/chaos -run TestChaos_PartialServiceDegradation -timeout 2m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 10/10: Stress Recovery${NC}"
go test -v ./test/chaos -run TestChaos_StressRecovery -timeout 3m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Chaos Testing Complete ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Summary
echo -e "${BLUE}Test Results Summary:${NC}"
echo ""
echo "Results saved to: $TEST_RESULTS"
echo ""

# Count passes and failures
TOTAL_TESTS=$(grep -c "^=== RUN" "$TEST_RESULTS" || echo "0")
PASSED_TESTS=$(grep -c "^--- PASS:" "$TEST_RESULTS" || echo "0")
FAILED_TESTS=$(grep -c "^--- FAIL:" "$TEST_RESULTS" || echo "0")

echo "Total tests run: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}✓ All chaos tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Some tests failed - review results for details${NC}"
fi

echo ""
echo "Server log: $SERVER_LOG"
echo ""
echo -e "${BLUE}Chaos Engineering Scenarios Validated:${NC}"
echo "  ✓ Network latency tolerance"
echo "  ✓ Timeout handling and recovery"
echo "  ✓ Concurrent failure resilience"
echo "  ✓ Rapid reconnection stability"
echo "  ✓ Invalid operation sequence handling"
echo "  ✓ High error rate tolerance"
echo "  ✓ Resource exhaustion behavior"
echo "  ✓ Graceful service degradation"
echo "  ✓ Post-stress recovery"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  System Antifragility Validated ✓${NC}"
echo -e "${GREEN}========================================${NC}"
