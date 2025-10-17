#!/bin/bash
# MAXIMUS Backend Startup Script
# Starts Docker Compose services for new architecture (3 libs + services)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/juan/vertice-dev"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_section() {
    echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} $1"
    echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker não encontrado. Instale o Docker primeiro."
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose não encontrado. Instale o Docker Compose primeiro."
        exit 1
    fi
}

get_service_status() {
    local service=$1
    if docker compose -f "$DOCKER_COMPOSE_FILE" ps --status running | grep -q "$service"; then
        echo "running"
    else
        echo "stopped"
    fi
}

count_running_services() {
    docker compose -f "$DOCKER_COMPOSE_FILE" ps --status running --format json 2>/dev/null | wc -l
}

start_services() {
    log_section "🚀 Iniciando MAXIMUS Backend"
    echo -e "${CYAN}👸 Penélope: 'Maximus, acorde! Mas lembre-se: EU mando aqui!'${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Start core infrastructure first
    log_info "Penélope: Ativando fundações (Redis, Postgres, Qdrant)..."
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d redis postgres qdrant 2>&1 | grep -v "warn" || true
    
    sleep 3
    
    # Start main services
    log_info "Penélope: Trazendo Maximus online..."
    docker compose -f "$DOCKER_COMPOSE_FILE" up -d \
        api_gateway \
        maximus_core_service \
        maximus_integration_service \
        maximus_orchestrator_service 2>&1 | grep -v "warn" || true
    
    sleep 2
    
    log_success "✨ Maximus está VIVO... mas totalmente sob CONTROLE de Penélope! 👑"
}

stop_services() {
    log_section "🛑 Parando MAXIMUS Backend"
    echo -e "${CYAN}👸 Penélope: 'Maximus, hora de dormir. SEM reclamar!'${NC}"
    
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" stop
    
    log_success "✅ Maximus desativado. Penélope mantém vigilância! 👸"
}

show_status() {
    log_section "📊 Status dos Serviços MAXIMUS"
    echo -e "${CYAN}👸 Penélope: 'Deixa eu ver como Maximus está se comportando...'${NC}"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Core Infrastructure
    echo ""
    echo -e "${CYAN}═══ Core Infrastructure ═══${NC}"
    
    local infra=("redis" "postgres" "qdrant")
    for service in "${infra[@]}"; do
        local status=$(get_service_status "$service")
        if [ "$status" = "running" ]; then
            log_success "$service: RUNNING"
        else
            log_error "$service: STOPPED"
        fi
    done
    
    # MAXIMUS AI Core
    echo ""
    echo -e "${CYAN}═══ MAXIMUS AI Core ═══${NC}"
    
    local core_services=(
        "api_gateway:8000"
        "maximus_core_service:8150"
        "maximus_predict:8126"
        "maximus_orchestrator_service:8125"
    )
    
    for service_port in "${core_services[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        local status=$(get_service_status "$service")
        if [ "$status" = "running" ]; then
            log_success "$service: RUNNING → http://localhost:$port"
        else
            log_error "$service: STOPPED"
        fi
    done
    
    # Support Services
    echo ""
    echo -e "${CYAN}═══ Support Services ═══${NC}"
    
    local support=(
        "osint-service:8036"
        "vuln_scanner_service:8111"
        "threat_intel_service:8113"
        "malware_analysis_service:8114"
        "ssl_monitor_service:8115"
        "nmap_service:8106"
        "domain_service:8104"
        "ip_intelligence_service:8105"
    )
    
    for service_port in "${support[@]}"; do
        IFS=':' read -r service port <<< "$service_port"
        local status=$(get_service_status "$service")
        if [ "$status" = "running" ]; then
            log_success "$service: RUNNING"
        else
            log_error "$service: STOPPED"
        fi
    done
    
    # Health Check Summary
    echo ""
    echo -e "${CYAN}═══ Health Status ═══${NC}"
    
    local healthy=$(docker compose ps --format "{{.Health}}" 2>/dev/null | grep "healthy" | wc -l)
    local unhealthy=$(docker compose ps --format "{{.Health}}" 2>/dev/null | grep "unhealthy" | wc -l)
    local starting=$(docker compose ps --format "{{.Health}}" 2>/dev/null | grep "starting" | wc -l)
    
    echo -e "${GREEN}✓ Healthy:${NC} $healthy"
    if [[ "$unhealthy" -gt 0 ]]; then
        echo -e "${RED}✗ Unhealthy:${NC} $unhealthy"
    else
        echo -e "${GREEN}✓ Unhealthy:${NC} 0"
    fi
    if [[ "$starting" -gt 0 ]]; then
        echo -e "${YELLOW}⟳ Starting:${NC} $starting"
    fi
    
    # Summary
    echo ""
    local total=$(count_running_services)
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}Total de serviços ativos:${NC} $total"
    echo -e "${CYAN}═══════════════════════════════════════════${NC}"
    if [[ "$total" -gt 10 ]]; then
        echo -e "${CYAN}👸 Penélope: 'Muito bem Maximus, continue assim!'${NC}"
    elif [[ "$total" -gt 5 ]]; then
        echo -e "${YELLOW}👸 Penélope: 'Maximus, você pode fazer melhor...'${NC}"
    else
        echo -e "${RED}👸 Penélope: 'MAXIMUS! Acorde agora ou vai ficar de castigo!'${NC}"
    fi
    echo ""
}

show_logs() {
    local service="${1:-api_gateway}"
    
    log_info "Mostrando logs de: $service"
    echo ""
    
    cd "$PROJECT_ROOT"
    docker compose -f "$DOCKER_COMPOSE_FILE" logs -f "$service"
}

case "${1:-start}" in
    start)
        check_docker
        start_services
        sleep 3
        show_status
        ;;
        
    stop)
        check_docker
        stop_services
        ;;
        
    restart)
        check_docker
        stop_services
        sleep 2
        start_services
        sleep 3
        show_status
        ;;
        
    status)
        check_docker
        show_status
        ;;
        
    logs)
        check_docker
        show_logs "${2:-api_gateway}"
        ;;
        
    *)
        echo "MAXIMUS Backend Manager"
        echo ""
        echo "Uso: maximus {start|stop|restart|status|logs [service]}"
        echo ""
        echo "Comandos:"
        echo "  start    - Inicia todos os serviços"
        echo "  stop     - Para todos os serviços"
        echo "  restart  - Reinicia todos os serviços"
        echo "  status   - Mostra status dos serviços"
        echo "  logs     - Mostra logs (opcional: especificar serviço)"
        echo ""
        echo "Exemplos:"
        echo "  maximus start"
        echo "  maximus status"
        echo "  maximus logs maximus_core_service"
        exit 1
        ;;
esac
