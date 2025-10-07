#!/bin/bash

# Load Testing Script for vCLI Go
# Runs comprehensive load tests and generates reports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCLI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SERVER_DIR="$VCLI_ROOT/bridge/python-grpc-server"
SERVER_LOG="/tmp/load_test_server.log"
RESULTS_DIR="$VCLI_ROOT/test/load/results"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  vCLI Go - Load Testing Suite${NC}"
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

# Run load tests
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Running Load Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TEST_RESULTS="$RESULTS_DIR/load_test_results_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${YELLOW}Test 1/9: Health Check - 1K requests${NC}"
go test -v ./test/load -run TestLoad_HealthCheck_1K -timeout 5m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 2/9: Health Check - 5K requests${NC}"
go test -v ./test/load -run TestLoad_HealthCheck_5K -timeout 10m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 3/9: Health Check - 10K requests${NC}"
go test -v ./test/load -run TestLoad_HealthCheck_10K -timeout 15m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 4/9: Create Session - 1K requests${NC}"
go test -v ./test/load -run TestLoad_CreateSession_1K -timeout 10m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 5/9: List Decisions - 5K requests${NC}"
go test -v ./test/load -run TestLoad_ListDecisions_5K -timeout 15m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 6/9: Get Metrics - 10K requests${NC}"
go test -v ./test/load -run TestLoad_GetMetrics_10K -timeout 15m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 7/9: Sustained Load (30 seconds)${NC}"
go test -v ./test/load -run TestLoad_SustainedLoad -timeout 5m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${YELLOW}Test 8/9: Mixed Operations${NC}"
go test -v ./test/load -run TestLoad_MixedOperations -timeout 10m | tee -a "$TEST_RESULTS"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Memory & CPU Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Test 9/9: Profiling with pprof${NC}"
MEMPROFILE="$RESULTS_DIR/mem_$(date +%Y%m%d_%H%M%S).prof"
CPUPROFILE="$RESULTS_DIR/cpu_$(date +%Y%m%d_%H%M%S).prof"

go test -v ./test/load -run TestLoad_HealthCheck_5K -memprofile="$MEMPROFILE" -cpuprofile="$CPUPROFILE" -timeout 10m

echo ""
echo -e "${GREEN}✓ All load tests completed${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Results Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Test results saved to: $TEST_RESULTS"
echo "Memory profile saved to: $MEMPROFILE"
echo "CPU profile saved to: $CPUPROFILE"
echo ""
echo "To analyze profiles:"
echo "  go tool pprof $MEMPROFILE"
echo "  go tool pprof $CPUPROFILE"
echo ""
echo "Server log: $SERVER_LOG"
echo ""

# Extract key metrics
echo -e "${BLUE}Key Metrics:${NC}"
grep -A 20 "Load Test:" "$TEST_RESULTS" | grep -E "(Throughput:|P99:|Success)" || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Load Testing Complete ✓${NC}"
echo -e "${GREEN}========================================${NC}"
