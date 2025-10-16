#!/bin/bash
# MAXIMUS Backend Startup Script
# Starts API Gateway + MAXIMUS Core Service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/juan/vertice-dev"

GATEWAY_DIR="$PROJECT_ROOT/backend/services/api_gateway"
MAXIMUS_DIR="$PROJECT_ROOT/backend/services/maximus_core_service"

GATEWAY_PORT="${GATEWAY_PORT:-8000}"
MAXIMUS_PORT="${MAXIMUS_PORT:-8100}"

GATEWAY_PID_FILE="/tmp/maximus_gateway.pid"
MAXIMUS_PID_FILE="/tmp/maximus_core.pid"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

stop_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            log_info "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null || true
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid 2>/dev/null || true
            fi
            log_success "$service_name stopped"
        fi
        rm -f "$pid_file"
    fi
}

start_maximus_core() {
    log_info "Starting MAXIMUS Core Service on port $MAXIMUS_PORT..."
    
    cd "$MAXIMUS_DIR"
    
    if [ ! -d ".venv" ]; then
        log_error "Virtual environment not found in $MAXIMUS_DIR"
        return 1
    fi
    
    PYTHONPATH=. .venv/bin/uvicorn main:app \
        --host 0.0.0.0 \
        --port $MAXIMUS_PORT \
        --log-level info \
        > /tmp/maximus_core.log 2>&1 &
    
    local pid=$!
    echo $pid > "$MAXIMUS_PID_FILE"
    
    # Wait for service to start
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_port $MAXIMUS_PORT; then
            log_success "MAXIMUS Core Service started (PID: $pid)"
            log_info "  → http://localhost:$MAXIMUS_PORT"
            log_info "  → Health: http://localhost:$MAXIMUS_PORT/health"
            log_info "  → Logs: /tmp/maximus_core.log"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "MAXIMUS Core Service failed to start"
    tail -20 /tmp/maximus_core.log
    return 1
}

start_api_gateway() {
    log_info "Starting API Gateway on port $GATEWAY_PORT..."
    
    cd "$GATEWAY_DIR"
    
    if [ ! -d ".venv" ]; then
        log_error "Virtual environment not found in $GATEWAY_DIR"
        return 1
    fi
    
    export MAXIMUS_CORE_SERVICE_URL="http://localhost:$MAXIMUS_PORT"
    
    PYTHONPATH=. .venv/bin/uvicorn main:app \
        --host 0.0.0.0 \
        --port $GATEWAY_PORT \
        --log-level info \
        > /tmp/maximus_gateway.log 2>&1 &
    
    local pid=$!
    echo $pid > "$GATEWAY_PID_FILE"
    
    # Wait for service to start
    local max_attempts=15
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_port $GATEWAY_PORT; then
            log_success "API Gateway started (PID: $pid)"
            log_info "  → http://localhost:$GATEWAY_PORT"
            log_info "  → Logs: /tmp/maximus_gateway.log"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    log_error "API Gateway failed to start"
    tail -20 /tmp/maximus_gateway.log
    return 1
}

show_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo " MAXIMUS Backend Status"
    echo "═══════════════════════════════════════════════════════"
    
    if check_port $MAXIMUS_PORT; then
        log_success "MAXIMUS Core Service: RUNNING (port $MAXIMUS_PORT)"
    else
        log_error "MAXIMUS Core Service: NOT RUNNING"
    fi
    
    if check_port $GATEWAY_PORT; then
        log_success "API Gateway: RUNNING (port $GATEWAY_PORT)"
    else
        log_error "API Gateway: NOT RUNNING"
    fi
    
    echo "═══════════════════════════════════════════════════════"
    echo ""
}

stop_all() {
    log_info "Stopping MAXIMUS Backend..."
    stop_service "$MAXIMUS_PID_FILE" "MAXIMUS Core Service"
    stop_service "$GATEWAY_PID_FILE" "API Gateway"
    log_success "All services stopped"
}

case "${1:-start}" in
    start)
        log_info "🚀 Starting MAXIMUS Backend..."
        
        # Check if already running
        if check_port $MAXIMUS_PORT || check_port $GATEWAY_PORT; then
            log_warning "Services already running. Use 'maximus stop' first."
            show_status
            exit 1
        fi
        
        # Start services
        start_maximus_core || exit 1
        sleep 3
        start_api_gateway || exit 1
        
        show_status
        log_success "🎉 MAXIMUS Backend ready!"
        ;;
        
    stop)
        stop_all
        ;;
        
    restart)
        stop_all
        sleep 2
        $0 start
        ;;
        
    status)
        show_status
        ;;
        
    logs)
        case "${2:-all}" in
            core|maximus)
                tail -f /tmp/maximus_core.log
                ;;
            gateway|api)
                tail -f /tmp/maximus_gateway.log
                ;;
            all|*)
                log_info "Core logs: /tmp/maximus_core.log"
                log_info "Gateway logs: /tmp/maximus_gateway.log"
                echo ""
                tail -f /tmp/maximus_core.log /tmp/maximus_gateway.log
                ;;
        esac
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|logs [core|gateway|all]}"
        exit 1
        ;;
esac
