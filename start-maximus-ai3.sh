#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# MAXIMUS AI 3.0 - Startup Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Description: Automated startup script for Maximus AI 3.0 Neural Architecture
# Author: Maximus AI Team
# Version: 3.0.0
# Date: 2025-10-03
#
# Usage: ./start-maximus-ai3.sh [OPTIONS]
#
# Options:
#   --build     Build Docker images before starting
#   --detach    Run in detached mode (background)
#   --logs      Follow logs after startup
#   --stop      Stop all services
#   --restart   Restart all services
#   --status    Show service status
#   --clean     Stop and remove all containers, networks, volumes
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "   __  __   _   __  __ ___  __ _   _ ___    _   ___   ____  ___  "
    echo "  |  \/  | /_\ |  \/  |_ _||  \| | | | __|  /_\ |_ _| |__ / / _ \ "
    echo "  | |\/| |/ _ \| |\/| || | | .  | |_| \__ \ / _ \ | |   |_ \| (_) |"
    echo "  |_|  |_/_/ \_\_|  |_||___||_|\_|\___/|___//_/ \_\___|  |___/\___/ "
    echo "                                                                     "
    echo "  Digital Neural Architecture for Autonomous Cybersecurity          "
    echo "  Version: 3.0.0 | Lines of Code: 27,389 | Zero Mocks              "
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker 24.0+"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose 2.20+"
        exit 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi

    log_success "All prerequisites met"
}

# Build images
build_images() {
    log_info "Building Docker images..."
    docker-compose -f docker-compose.monitoring.yml build --no-cache
    log_success "Images built successfully"
}

# Start services
start_services() {
    local detach_flag=""
    if [ "$1" = "detach" ]; then
        detach_flag="-d"
    fi

    log_info "Starting Maximus AI 3.0 services..."
    docker-compose -f docker-compose.monitoring.yml up $detach_flag

    if [ "$1" = "detach" ]; then
        log_success "All services started in background"
        echo ""
        show_endpoints
    fi
}

# Stop services
stop_services() {
    log_info "Stopping Maximus AI 3.0 services..."
    docker-compose -f docker-compose.monitoring.yml down
    log_success "All services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting Maximus AI 3.0 services..."
    docker-compose -f docker-compose.monitoring.yml restart
    log_success "All services restarted"
}

# Show status
show_status() {
    log_info "Service status:"
    echo ""
    docker-compose -f docker-compose.monitoring.yml ps
}

# Clean everything
clean_all() {
    log_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        docker-compose -f docker-compose.monitoring.yml down -v --remove-orphans
        log_success "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

# Follow logs
follow_logs() {
    log_info "Following logs (Ctrl+C to exit)..."
    docker-compose -f docker-compose.monitoring.yml logs -f
}

# Show endpoints
show_endpoints() {
    echo -e "${PURPLE}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "  SERVICE ENDPOINTS"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo -e "${CYAN}Neural Architecture Services:${NC}"
    echo "  • Neuromodulation:         http://localhost:8001"
    echo "  • Memory Consolidation:    http://localhost:8002"
    echo "  • HSAS:                    http://localhost:8003"
    echo "  • Strategic Planning:      http://localhost:8004"
    echo "  • Immunis System:          http://localhost:8005"
    echo ""
    echo -e "${CYAN}Sensory Layer Services:${NC}"
    echo "  • Visual Cortex:           http://localhost:8006"
    echo ""
    echo -e "${CYAN}Monitoring:${NC}"
    echo "  • Prometheus:              http://localhost:9090"
    echo "  • Grafana:                 http://localhost:3000"
    echo "    └─ Username: admin"
    echo "    └─ Password: maximus_ai_3_0"
    echo "  • Node Exporter:           http://localhost:9100"
    echo ""
    echo -e "${CYAN}API Documentation:${NC}"
    echo "  • Neuromodulation Docs:    http://localhost:8001/docs"
    echo "  • Memory Consolidation:    http://localhost:8002/docs"
    echo "  • HSAS Docs:               http://localhost:8003/docs"
    echo "  • Strategic Planning:      http://localhost:8004/docs"
    echo "  • Immunis Docs:            http://localhost:8005/docs"
    echo "  • Visual Cortex Docs:      http://localhost:8006/docs"
    echo ""
    echo -e "${PURPLE}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    sleep 5  # Wait for services to start

    local services=(
        "Neuromodulation:8001"
        "Memory Consolidation:8002"
        "HSAS:8003"
        "Strategic Planning:8004"
        "Immunis:8005"
        "Visual Cortex:8006"
        "Prometheus:9090"
        "Grafana:3000"
    )

    echo ""
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        if curl -s "http://localhost:$port/health" &> /dev/null || \
           curl -s "http://localhost:$port/" &> /dev/null; then
            echo -e "  ${GREEN}✓${NC} $name (port $port)"
        else
            echo -e "  ${RED}✗${NC} $name (port $port)"
        fi
    done
    echo ""
}

# Main script
main() {
    print_banner

    case "$1" in
        --build)
            check_prerequisites
            build_images
            start_services "detach"
            health_check
            ;;
        --detach|-d)
            check_prerequisites
            start_services "detach"
            health_check
            ;;
        --logs|-l)
            follow_logs
            ;;
        --stop)
            stop_services
            ;;
        --restart)
            restart_services
            ;;
        --status)
            show_status
            ;;
        --clean)
            clean_all
            ;;
        --health)
            health_check
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build     Build Docker images before starting"
            echo "  --detach    Run in detached mode (background)"
            echo "  --logs      Follow logs after startup"
            echo "  --stop      Stop all services"
            echo "  --restart   Restart all services"
            echo "  --status    Show service status"
            echo "  --clean     Stop and remove all containers, networks, volumes"
            echo "  --health    Perform health check on all services"
            echo "  --help      Show this help message"
            echo ""
            ;;
        *)
            check_prerequisites
            start_services
            ;;
    esac
}

# Execute main
main "$@"
