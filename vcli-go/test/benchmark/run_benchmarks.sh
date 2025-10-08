#!/bin/bash
# Performance Benchmark Suite
# Compares HTTP vs gRPC backend performance

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   PERFORMANCE BENCHMARK: HTTP vs gRPC         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if gRPC server is running
if ! lsof -i :50051 > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Python gRPC server...${NC}"
    cd bridge/python-grpc-server
    python3 governance_grpc_server.py > /tmp/grpc_bench_server.log 2>&1 &
    GRPC_PID=$!
    cd ../..

    sleep 2

    if ! kill -0 $GRPC_PID 2>/dev/null; then
        echo -e "${RED}❌ Failed to start gRPC server${NC}"
        cat /tmp/grpc_bench_server.log
        exit 1
    fi

    echo -e "${GREEN}✅ gRPC server started (PID: $GRPC_PID)${NC}"
    CLEANUP_SERVER=true
else
    echo -e "${GREEN}✅ gRPC server already running${NC}"
    CLEANUP_SERVER=false
fi

echo ""

# Set PATH for Go
export PATH="$HOME/go-sdk/bin:$HOME/go/bin:$PATH"

# Run benchmarks
echo -e "${BLUE}[1/3] Running HTTP benchmarks...${NC}"
echo ""
go test -bench=HTTP -benchmem -benchtime=3s ./test/benchmark 2>&1 | tee /tmp/bench_http.txt
echo ""

echo -e "${BLUE}[2/3] Running gRPC benchmarks...${NC}"
echo ""
go test -bench=GRPC -benchmem -benchtime=3s ./test/benchmark 2>&1 | tee /tmp/bench_grpc.txt
echo ""

echo -e "${BLUE}[3/3] Running parallel benchmarks...${NC}"
echo ""
go test -bench=Parallel -benchmem -benchtime=3s ./test/benchmark 2>&1 | tee /tmp/bench_parallel.txt
echo ""

# Generate comparison report
echo -e "${BLUE}Generating comparison report...${NC}"
echo ""

cat > /tmp/benchmark_report.txt <<'REPORT_START'
# PERFORMANCE BENCHMARK REPORT
# HTTP vs gRPC Backend Comparison

## Test Configuration
- Duration: 3s per benchmark
- Go Version: $(go version)
- Date: $(date)

## HTTP Benchmarks
REPORT_START

echo "---" >> /tmp/benchmark_report.txt
grep "Benchmark" /tmp/bench_http.txt >> /tmp/benchmark_report.txt || echo "No HTTP results" >> /tmp/benchmark_report.txt
echo "" >> /tmp/benchmark_report.txt

cat >> /tmp/benchmark_report.txt <<'REPORT_GRPC'

## gRPC Benchmarks
---
REPORT_GRPC

grep "Benchmark" /tmp/bench_grpc.txt >> /tmp/benchmark_report.txt || echo "No gRPC results" >> /tmp/benchmark_report.txt
echo "" >> /tmp/benchmark_report.txt

cat >> /tmp/benchmark_report.txt <<'REPORT_PARALLEL'

## Parallel Load Benchmarks
---
REPORT_PARALLEL

grep "Benchmark" /tmp/bench_parallel.txt >> /tmp/benchmark_report.txt || echo "No parallel results" >> /tmp/benchmark_report.txt

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        BENCHMARK RESULTS SUMMARY               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Show quick comparison
echo -e "${BLUE}HTTP HealthCheck:${NC}"
grep "BenchmarkHTTPClient_HealthCheck" /tmp/bench_http.txt | tail -1

echo -e "${BLUE}gRPC HealthCheck:${NC}"
grep "BenchmarkGRPCClient_HealthCheck" /tmp/bench_grpc.txt | tail -1

echo ""
echo -e "${BLUE}HTTP Parallel:${NC}"
grep "BenchmarkHTTPClient_Parallel" /tmp/bench_parallel.txt | tail -1

echo -e "${BLUE}gRPC Parallel:${NC}"
grep "BenchmarkGRPCClient_Parallel" /tmp/bench_parallel.txt | tail -1

echo ""
echo -e "${GREEN}Full report saved to: /tmp/benchmark_report.txt${NC}"
echo ""

# Cleanup
if [ "$CLEANUP_SERVER" = true ]; then
    echo -e "${BLUE}Stopping gRPC server...${NC}"
    kill $GRPC_PID 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Server stopped${NC}"
fi

echo ""
echo -e "${YELLOW}Pela arte. Pela velocidade. Pela proteção. ⚡🛡️${NC}"
