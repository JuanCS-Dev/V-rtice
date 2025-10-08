#!/bin/bash
# Integration test script for gRPC bridge
# Starts Python server, runs Go tests, cleans up

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVER_DIR="$PROJECT_ROOT/bridge/python-grpc-server"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== gRPC Bridge Integration Test ===${NC}"
echo ""

# Step 1: Start Python gRPC server
echo -e "${BLUE}[1/4] Starting Python gRPC server...${NC}"
cd "$SERVER_DIR"
python3 governance_grpc_server.py > /tmp/grpc_server.log 2>&1 &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to be ready
echo "Waiting for server to start..."
sleep 2

# Check if server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${RED}❌ Server failed to start${NC}"
    cat /tmp/grpc_server.log
    exit 1
fi

# Check if port is listening
if ! lsof -i :50051 > /dev/null 2>&1; then
    echo -e "${RED}❌ Server not listening on port 50051${NC}"
    cat /tmp/grpc_server.log
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Server running on localhost:50051${NC}"
echo ""

# Step 2: Run Go tests
echo -e "${BLUE}[2/4] Running Go gRPC client tests...${NC}"
cd "$PROJECT_ROOT"
export PATH="$HOME/go-sdk/bin:$HOME/go/bin:$PATH"
if go test -v ./test -run TestGovernanceGRPC 2>&1 | tee /tmp/grpc_test.log; then
    echo -e "${GREEN}✅ Tests passed${NC}"
    TEST_RESULT=0
else
    echo -e "${RED}❌ Tests failed${NC}"
    TEST_RESULT=1
fi
echo ""

# Step 3: Show server logs
echo -e "${BLUE}[3/4] Server logs:${NC}"
echo "---"
tail -20 /tmp/grpc_server.log
echo "---"
echo ""

# Step 4: Cleanup
echo -e "${BLUE}[4/4] Cleaning up...${NC}"
kill $SERVER_PID 2>/dev/null || true
sleep 1
echo -e "${GREEN}✅ Server stopped${NC}"
echo ""

# Final result
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ gRPC Bridge Integration Test PASSED${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ gRPC Bridge Integration Test FAILED${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit 1
fi
