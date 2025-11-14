#!/bin/bash
# MAXIMUS Full Stack Startup Script
# Starts all 5 core services for max-code-cli integration
#
# Services:
# - MAXIMUS Core (8150): Consciousness, ESGT
# - Penelope (8154): 7 Biblical Articles, Sabbath Mode
# - Orchestrator (8027): MAPE-K Control Loop
# - Oraculo (8026): Prediction & Forecasting
# - Atlas (8007): Context Management

set -e

echo "🚀 MAXIMUS FULL STACK - STARTUP"
echo "================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Base directory (works from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$SCRIPT_DIR"

# Log directory
LOG_DIR="/tmp/maximus_logs"
mkdir -p "$LOG_DIR"

# PID file
PID_FILE="$LOG_DIR/maximus_full_stack.pid"

# Clean up old PIDs
rm -f "$PID_FILE"

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
    echo "🛑 Shutting down MAXIMUS Full Stack..."

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
check_port 8150 || exit 1  # MAXIMUS Core
check_port 8154 || exit 1  # Penelope
check_port 8027 || exit 1  # Orchestrator
check_port 8026 || exit 1  # Oraculo
check_port 8007 || exit 1  # Atlas
echo ""

# Start MAXIMUS Core Service
echo -e "${CYAN}🧠 Starting MAXIMUS Core Service (port 8150)...${NC}"
cd "$BASE_DIR/maximus_core_service"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in maximus_core_service${NC}"
    exit 1
fi

PYTHONPATH="$BASE_DIR" python3 main.py > "$LOG_DIR/maximus_core.log" 2>&1 &
CORE_PID=$!
echo $CORE_PID >> "$PID_FILE"
echo -e "${GREEN}✓ MAXIMUS Core started (PID: $CORE_PID)${NC}"
echo "  Logs: $LOG_DIR/maximus_core.log"
echo "  Health: http://localhost:8150/health"
echo ""
sleep 3

# Start Penelope Service
echo -e "${CYAN}📖 Starting Penelope Service (port 8154)...${NC}"
cd "$BASE_DIR/penelope_service"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in penelope_service${NC}"
    cleanup
    exit 1
fi

PYTHONPATH="$BASE_DIR" python3 main.py > "$LOG_DIR/penelope.log" 2>&1 &
PENELOPE_PID=$!
echo $PENELOPE_PID >> "$PID_FILE"
echo -e "${GREEN}✓ Penelope started (PID: $PENELOPE_PID)${NC}"
echo "  Logs: $LOG_DIR/penelope.log"
echo "  Health: http://localhost:8154/health"
echo ""
sleep 3

# Start Orchestrator Service
echo -e "${CYAN}🎭 Starting Orchestrator Service (port 8027)...${NC}"
cd "$BASE_DIR/maximus_orchestrator_service"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in maximus_orchestrator_service${NC}"
    cleanup
    exit 1
fi

PYTHONPATH="$BASE_DIR" python3 main.py > "$LOG_DIR/orchestrator.log" 2>&1 &
ORCHESTRATOR_PID=$!
echo $ORCHESTRATOR_PID >> "$PID_FILE"
echo -e "${GREEN}✓ Orchestrator started (PID: $ORCHESTRATOR_PID)${NC}"
echo "  Logs: $LOG_DIR/orchestrator.log"
echo "  Health: http://localhost:8027/health"
echo ""
sleep 3

# Start Oraculo Service
echo -e "${CYAN}🔮 Starting Oraculo Service (port 8026)...${NC}"
cd "$BASE_DIR/maximus_oraculo"

if [ ! -f "main.py" ]; then
    echo -e "${YELLOW}⚠  main.py not found, trying maximus_oraculo_v2...${NC}"
    cd "$BASE_DIR/maximus_oraculo_v2"
    if [ ! -f "main.py" ]; then
        echo -e "${RED}✗ Oraculo main.py not found in either location${NC}"
        cleanup
        exit 1
    fi
fi

PYTHONPATH="$BASE_DIR" python3 main.py > "$LOG_DIR/oraculo.log" 2>&1 &
ORACULO_PID=$!
echo $ORACULO_PID >> "$PID_FILE"
echo -e "${GREEN}✓ Oraculo started (PID: $ORACULO_PID)${NC}"
echo "  Logs: $LOG_DIR/oraculo.log"
echo "  Health: http://localhost:8026/health"
echo ""
sleep 3

# Start Atlas Service
echo -e "${CYAN}🗺️  Starting Atlas Service (port 8007)...${NC}"
cd "$BASE_DIR/atlas_service"

if [ ! -f "main.py" ]; then
    echo -e "${RED}✗ main.py not found in atlas_service${NC}"
    cleanup
    exit 1
fi

PYTHONPATH="$BASE_DIR" python3 main.py > "$LOG_DIR/atlas.log" 2>&1 &
ATLAS_PID=$!
echo $ATLAS_PID >> "$PID_FILE"
echo -e "${GREEN}✓ Atlas started (PID: $ATLAS_PID)${NC}"
echo "  Logs: $LOG_DIR/atlas.log"
echo "  Health: http://localhost:8007/health"
echo ""
sleep 3

echo "===================================="
echo -e "${GREEN}✅ MAXIMUS FULL STACK IS UP!${NC}"
echo "===================================="
echo ""
echo "📍 Service Endpoints:"
echo "  • MAXIMUS Core:   http://localhost:8150"
echo "  • Penelope:       http://localhost:8154"
echo "  • Orchestrator:   http://localhost:8027"
echo "  • Oraculo:        http://localhost:8026"
echo "  • Atlas:          http://localhost:8007"
echo ""
echo "🔍 Health Checks:"
for port in 8150 8154 8027 8026 8007; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Port $port responding"
    else
        echo -e "  ${YELLOW}⚠${NC} Port $port not responding yet"
    fi
done
echo ""
echo "📝 Logs Directory: $LOG_DIR"
echo "  • tail -f $LOG_DIR/maximus_core.log"
echo "  • tail -f $LOG_DIR/penelope.log"
echo "  • tail -f $LOG_DIR/orchestrator.log"
echo "  • tail -f $LOG_DIR/oraculo.log"
echo "  • tail -f $LOG_DIR/atlas.log"
echo ""
echo "🧪 Test Integration:"
echo "  cd /media/juan/DATA1/projects/MAXIMUS\ AI/max-code-cli"
echo "  ./max-code health"
echo ""
echo "🛑 To stop: Ctrl+C or kill -TERM $$"
echo ""
echo "Soli Deo Gloria 🙏"
echo ""

# Keep script running and show combined logs
echo "📋 Showing live logs (Ctrl+C to stop)..."
echo "----------------------------------------"
tail -f "$LOG_DIR"/*.log
