#!/bin/bash
# Backend Setup Script - Start all confirmed Vértice backends for testing
#
# Constitutional Compliance: P1 - NO MOCKS (start real backends for testing)
# Usage: ./internal/testutil/backend_setup.sh [start|stop|status]

set -e

BACKEND_ROOT=~/vertice-dev/backend/services
LOG_DIR=/tmp/vertice-backend-logs

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1"
}

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if service is running
is_running() {
    local port=$1
    curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null | grep -q "200"
}

# Function to start backend service
start_backend() {
    local name=$1
    local dir=$2
    local port=$3

    log_info "Starting $name (port $port)..."

    # Check if service directory exists
    if [ ! -d "$BACKEND_ROOT/$dir" ]; then
        log_error "$name directory not found: $BACKEND_ROOT/$dir"
        return 1
    fi

    # Check if already running
    if is_running "$port"; then
        log_success "$name already running on port $port"
        return 0
    fi

    # Check if main.py exists
    if [ ! -f "$BACKEND_ROOT/$dir/main.py" ]; then
        log_error "$name main.py not found in $BACKEND_ROOT/$dir"
        return 1
    fi

    # Start service in background
    cd "$BACKEND_ROOT/$dir"

    # Check if venv exists, activate if available
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Start service with nohup
    nohup python main.py > "$LOG_DIR/${name}.log" 2>&1 &
    local pid=$!

    log_info "Started $name (PID: $pid, log: $LOG_DIR/${name}.log)"

    # Wait for health check (max 30 seconds)
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if is_running "$port"; then
            log_success "$name healthy on port $port"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    log_warning "$name did not become healthy after 30s (check log: $LOG_DIR/${name}.log)"
    return 1
}

# Function to stop backend service
stop_backend() {
    local name=$1
    local port=$2

    log_info "Stopping $name (port $port)..."

    # Find and kill process listening on port
    local pid=$(lsof -ti tcp:$port 2>/dev/null)

    if [ -z "$pid" ]; then
        log_warning "$name not running on port $port"
        return 0
    fi

    kill $pid 2>/dev/null || true
    sleep 1

    # Force kill if still running
    if kill -0 $pid 2>/dev/null; then
        log_info "Force killing $name (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
    fi

    log_success "$name stopped"
}

# Function to check backend status
check_status() {
    local name=$1
    local port=$2

    if is_running "$port"; then
        log_success "$name (port $port): HEALTHY"
    else
        log_error "$name (port $port): NOT RUNNING"
    fi
}

# Main script
case "${1:-start}" in
    start)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  VÉRTICE Backend Setup - Starting Services"
        echo "  Constitutional Compliance: P1 - NO MOCKS"
        echo "  Using REAL backends for testing"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        # Start P0 backends (confirmed and documented)
        log_info "Starting P0 (confirmed) backends..."
        start_backend "MABA" "maba_service" 8152
        start_backend "NIS" "nis_service" 8153
        start_backend "Penelope" "penelope_service" 8154

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log_success "Backend setup complete!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Test backends with:"
        echo "  curl http://localhost:8152/health  # MABA"
        echo "  curl http://localhost:8153/health  # NIS"
        echo "  curl http://localhost:8154/health  # Penelope"
        echo ""
        echo "View logs:"
        echo "  tail -f $LOG_DIR/MABA.log"
        echo "  tail -f $LOG_DIR/NIS.log"
        echo "  tail -f $LOG_DIR/Penelope.log"
        echo ""
        ;;

    stop)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  VÉRTICE Backend Setup - Stopping Services"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        stop_backend "MABA" 8152
        stop_backend "NIS" 8153
        stop_backend "Penelope" 8154

        echo ""
        log_success "All backends stopped"
        ;;

    status)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  VÉRTICE Backend Status"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        check_status "MABA" 8152
        check_status "NIS" 8153
        check_status "Penelope" 8154
        ;;

    *)
        echo "Usage: $0 {start|stop|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start all confirmed backends (MABA, NIS, Penelope)"
        echo "  stop    - Stop all backends"
        echo "  status  - Check backend health status"
        echo ""
        echo "Constitutional Compliance: P1 - NO MOCKS (real backends only)"
        exit 1
        ;;
esac
