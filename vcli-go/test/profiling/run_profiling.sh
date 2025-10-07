#!/bin/bash

# Profiling Script for vCLI Go
# Generates CPU, memory, goroutine, block, and mutex profiles

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCLI_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_SERVER_DIR="$VCLI_ROOT/bridge/python-grpc-server"
SERVER_LOG="/tmp/profiling_server.log"
PROFILE_DIR="$SCRIPT_DIR/profiles"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  vCLI Go - Performance Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create profile directory
mkdir -p "$PROFILE_DIR"

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

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CPU Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

CPU_PROFILE="$PROFILE_DIR/cpu_${TIMESTAMP}.prof"
echo -e "${YELLOW}Running CPU profile test...${NC}"
go test -v ./test/profiling -run TestCPUProfile_HealthCheck -cpuprofile="$CPU_PROFILE" -timeout 2m

echo -e "${GREEN}✓ CPU profile saved to: $CPU_PROFILE${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Memory Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

MEM_PROFILE="$PROFILE_DIR/mem_${TIMESTAMP}.prof"
echo -e "${YELLOW}Running memory profile test...${NC}"
go test -v ./test/profiling -run TestMemoryProfile_SessionLifecycle -memprofile="$MEM_PROFILE" -timeout 2m

echo -e "${GREEN}✓ Memory profile saved to: $MEM_PROFILE${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Goroutine Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Running goroutine profile test...${NC}"
go test -v ./test/profiling -run TestGoroutineProfile_ConcurrentOperations -timeout 2m

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Block Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

BLOCK_PROFILE="$PROFILE_DIR/block_${TIMESTAMP}.prof"
echo -e "${YELLOW}Running block profile test...${NC}"
go test -v ./test/profiling -run TestBlockProfile_ChannelContention -blockprofile="$BLOCK_PROFILE" -timeout 2m

echo -e "${GREEN}✓ Block profile saved to: $BLOCK_PROFILE${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Mutex Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

MUTEX_PROFILE="$PROFILE_DIR/mutex_${TIMESTAMP}.prof"
echo -e "${YELLOW}Running mutex profile test...${NC}"
go test -v ./test/profiling -run TestMutexProfile_Contention -mutexprofile="$MUTEX_PROFILE" -timeout 2m

echo -e "${GREEN}✓ Mutex profile saved to: $MUTEX_PROFILE${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Heap Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Running heap profile test...${NC}"
go test -v ./test/profiling -run TestHeapProfile_AllocationPatterns -timeout 2m

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Allocation Profiling${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Running allocation profile test...${NC}"
go test -v ./test/profiling -run TestAllocationProfile_PerOperation -timeout 2m

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Profiling Complete ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Generate reports
echo -e "${BLUE}Generating profile reports...${NC}"
echo ""

REPORT_DIR="$PROFILE_DIR/reports"
mkdir -p "$REPORT_DIR"

# CPU Profile Analysis
if [ -f "$CPU_PROFILE" ]; then
    echo -e "${YELLOW}Analyzing CPU profile...${NC}"

    # Top functions by CPU time
    echo "=== Top 20 CPU-intensive functions ===" > "$REPORT_DIR/cpu_top_${TIMESTAMP}.txt"
    go tool pprof -text -nodecount=20 "$CPU_PROFILE" >> "$REPORT_DIR/cpu_top_${TIMESTAMP}.txt" 2>&1

    # Generate SVG graph
    go tool pprof -svg -output="$REPORT_DIR/cpu_graph_${TIMESTAMP}.svg" "$CPU_PROFILE" 2>/dev/null || true

    echo -e "${GREEN}✓ CPU analysis saved to: $REPORT_DIR/cpu_top_${TIMESTAMP}.txt${NC}"
    [ -f "$REPORT_DIR/cpu_graph_${TIMESTAMP}.svg" ] && echo -e "${GREEN}✓ CPU graph saved to: $REPORT_DIR/cpu_graph_${TIMESTAMP}.svg${NC}"
fi

# Memory Profile Analysis
if [ -f "$MEM_PROFILE" ]; then
    echo -e "${YELLOW}Analyzing memory profile...${NC}"

    # Top allocators
    echo "=== Top 20 memory allocators ===" > "$REPORT_DIR/mem_top_${TIMESTAMP}.txt"
    go tool pprof -text -nodecount=20 "$MEM_PROFILE" >> "$REPORT_DIR/mem_top_${TIMESTAMP}.txt" 2>&1

    # In-use memory
    echo -e "\n=== Top 20 in-use memory ===" >> "$REPORT_DIR/mem_inuse_${TIMESTAMP}.txt"
    go tool pprof -text -nodecount=20 -inuse_space "$MEM_PROFILE" >> "$REPORT_DIR/mem_inuse_${TIMESTAMP}.txt" 2>&1

    # Generate SVG graph
    go tool pprof -svg -output="$REPORT_DIR/mem_graph_${TIMESTAMP}.svg" "$MEM_PROFILE" 2>/dev/null || true

    echo -e "${GREEN}✓ Memory analysis saved to: $REPORT_DIR/mem_top_${TIMESTAMP}.txt${NC}"
    [ -f "$REPORT_DIR/mem_graph_${TIMESTAMP}.svg" ] && echo -e "${GREEN}✓ Memory graph saved to: $REPORT_DIR/mem_graph_${TIMESTAMP}.svg${NC}"
fi

# Block Profile Analysis
if [ -f "$BLOCK_PROFILE" ]; then
    echo -e "${YELLOW}Analyzing block profile...${NC}"

    echo "=== Top 20 blocking operations ===" > "$REPORT_DIR/block_top_${TIMESTAMP}.txt"
    go tool pprof -text -nodecount=20 "$BLOCK_PROFILE" >> "$REPORT_DIR/block_top_${TIMESTAMP}.txt" 2>&1 || true

    echo -e "${GREEN}✓ Block analysis saved to: $REPORT_DIR/block_top_${TIMESTAMP}.txt${NC}"
fi

# Mutex Profile Analysis
if [ -f "$MUTEX_PROFILE" ]; then
    echo -e "${YELLOW}Analyzing mutex profile...${NC}"

    echo "=== Top 20 mutex contentions ===" > "$REPORT_DIR/mutex_top_${TIMESTAMP}.txt"
    go tool pprof -text -nodecount=20 "$MUTEX_PROFILE" >> "$REPORT_DIR/mutex_top_${TIMESTAMP}.txt" 2>&1 || true

    echo -e "${GREEN}✓ Mutex analysis saved to: $REPORT_DIR/mutex_top_${TIMESTAMP}.txt${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Profile Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo "Profiles generated:"
echo "  CPU:    $CPU_PROFILE"
echo "  Memory: $MEM_PROFILE"
echo "  Block:  $BLOCK_PROFILE"
echo "  Mutex:  $MUTEX_PROFILE"
echo ""
echo "Reports generated:"
ls -1 "$REPORT_DIR"/*_${TIMESTAMP}.* 2>/dev/null | sed 's/^/  /' || echo "  (No reports generated)"
echo ""
echo "To analyze interactively:"
echo "  go tool pprof $CPU_PROFILE"
echo "  go tool pprof $MEM_PROFILE"
echo ""
echo "To visualize (requires graphviz):"
echo "  go tool pprof -http=:8080 $CPU_PROFILE"
echo "  go tool pprof -http=:8081 $MEM_PROFILE"
echo ""

# Extract key metrics from test output
echo -e "${BLUE}Key Metrics:${NC}"
echo ""

# Try to extract goroutine info
if [ -f "$SERVER_LOG" ]; then
    echo "Server activity:"
    grep -i "session created\|decision" "$SERVER_LOG" | tail -5 || true
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Profiling Session Complete ✓${NC}"
echo -e "${GREEN}========================================${NC}"
