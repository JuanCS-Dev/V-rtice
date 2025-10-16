#!/bin/bash
# MAXIMUS Backend Startup Script - Secure Architecture
#
# Architecture:
# - API Gateway: Port 8000 (public entry point with auth)
# - Core Service: Port 8100 (internal, proxied via gateway)
# - Prometheus: Port 8001 (metrics)

set -e

echo "🚀 MAXIMUS BACKEND - SECURE STARTUP"
echo "===================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/home/juan/vertice-dev/backend/services"

# Log directory
LOG_DIR="/tmp/maximus_logs"
mkdir -p "$LOG_DIR"

# PID file
PID_FILE="$LOG_DIR/maximus.pid"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${RED}✗ Port $port is already in use${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Port $port is available${NC}"
    return 0
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down MAXIMUS Backend..."

    if [ -f "$PID_FILE" ]; then
        while IFS= read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "  Stopping process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi

    echo "✅ Shutdown complete"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check required ports
echo "📡 Checking ports..."
check_port 8000 || exit 1  # API Gateway
check_port 8100 || exit 1  # Core Service
check_port 8001 || exit 1  # Prometheus
echo ""

# Start Core Service
echo "🧠 Starting MAXIMUS Core Service (port 8100)..."
cd "$BASE_DIR/maximus_core_service"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in maximus_core_service${NC}"
    exit 1
fi

PYTHONPATH=. python main.py > "$LOG_DIR/core_service.log" 2>&1 &
CORE_PID=$!
echo $CORE_PID >> "$PID_FILE"
echo -e "${GREEN}✓ Core Service started (PID: $CORE_PID)${NC}"
echo "  Logs: $LOG_DIR/core_service.log"
echo "  Health: http://localhost:8100/health"
echo "  Metrics: http://localhost:8001/metrics"
echo ""

# Wait for core service to be ready
echo "⏳ Waiting for Core Service to initialize..."
sleep 5

# Check if core service is responding
if curl -s http://localhost:8100/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Core Service is responding${NC}"
else
    echo -e "${YELLOW}⚠  Core Service health check failed (may still be initializing)${NC}"
fi
echo ""

# Start API Gateway
echo "🔐 Starting API Gateway (port 8000)..."
cd "$BASE_DIR/api_gateway"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in api_gateway${NC}"
    cleanup
    exit 1
fi

PYTHONPATH=. python main.py > "$LOG_DIR/api_gateway.log" 2>&1 &
GATEWAY_PID=$!
echo $GATEWAY_PID >> "$PID_FILE"
echo -e "${GREEN}✓ API Gateway started (PID: $GATEWAY_PID)${NC}"
echo "  Logs: $LOG_DIR/api_gateway.log"
echo "  Public: http://localhost:8000"
echo ""

# Wait for gateway to be ready
sleep 3

# Check if gateway is responding
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway is responding${NC}"
else
    echo -e "${YELLOW}⚠  API Gateway health check failed${NC}"
fi
echo ""

echo "===================================="
echo -e "${GREEN}✅ MAXIMUS Backend is UP!${NC}"
echo "===================================="
echo ""
echo "📍 Access Points:"
echo "  • API Gateway: http://localhost:8000"
echo "  • Health Check: http://localhost:8000/health"
echo "  • Core via Proxy: http://localhost:8000/core/health"
echo "  • Metrics: http://localhost:8001/metrics"
echo ""
echo "🔑 Authentication:"
echo "  Header: X-API-Key: supersecretkey"
echo ""
echo "📊 Available APIs:"
echo "  • POST /core/query - Process queries"
echo "  • GET /api/v1/governance/* - HITL Governance"
echo "  • GET /api/adw/* - AI-Driven Workflows"
echo "  • GET /api/consciousness/* - Consciousness monitoring"
echo "  • GET /stream/consciousness/sse - SSE stream"
echo "  • WS /stream/consciousness/ws - WebSocket stream"
echo ""
echo "📝 Logs:"
echo "  • Core: tail -f $LOG_DIR/core_service.log"
echo "  • Gateway: tail -f $LOG_DIR/api_gateway.log"
echo ""
echo "🛑 To stop: Ctrl+C or kill -TERM $$"
echo ""
echo "Soli Deo Gloria 🙏"
echo ""

# Keep script running and show logs
echo "📋 Showing live logs (Ctrl+C to stop)..."
echo "----------------------------------------"
tail -f "$LOG_DIR/core_service.log" "$LOG_DIR/api_gateway.log"
