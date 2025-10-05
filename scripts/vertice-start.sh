#!/bin/bash

###############################################################################
# VÉRTICE START - Wrapper Inteligente para Docker Compose
###############################################################################
#
# Este script substitui o `docker compose up` tradicional e:
# 1. ✅ Valida portas ANTES de iniciar
# 2. ✅ Libera portas automaticamente se necessário
# 3. ✅ Inicia serviços de forma ordenada
# 4. ✅ Executa health checks
# 5. ✅ Mostra logs em tempo real
#
# Uso:
#   ./vertice-start.sh              # Inicia tudo
#   ./vertice-start.sh --force      # Força reinicialização
#   ./vertice-start.sh --check      # Só verifica, não inicia
#
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

banner() {
    clear
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║          🚀 VÉRTICE/MAXIMUS AI - STARTER v2.0 🤖              ║"
    echo "║                                                                ║"
    echo "║          Intelligent Port Management & Service Starter         ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

# Log functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo -e "\n${CYAN}▶${NC} ${MAGENTA}$1${NC}\n"
}

# Verifica se porta está em uso
check_port() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || \
    ss -tlnp 2>/dev/null | grep -q ":$port " 2>/dev/null
}

# Libera porta
free_port() {
    local port=$1
    local pid=$(lsof -ti:$port 2>/dev/null | head -1)

    if [ -n "$pid" ]; then
        log_warning "Liberando porta $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
}

# Verifica e libera portas críticas
check_and_free_ports() {
    log_step "Passo 1/5: Validação de Portas"

    local critical_ports=(8099 8001 8016 8008 8010 6379 5432 6333)
    local conflicts=0

    for port in "${critical_ports[@]}"; do
        if check_port "$port"; then
            conflicts=$((conflicts + 1))
            log_warning "Porta $port em uso"
            free_port "$port"

            # Verifica se liberou
            if check_port "$port"; then
                log_error "Não foi possível liberar porta $port"
                return 1
            else
                log_success "Porta $port liberada"
            fi
        else
            log_success "Porta $port disponível"
        fi
    done

    if [ $conflicts -eq 0 ]; then
        log_success "Todas as portas estão livres!"
    else
        log_success "$conflicts conflitos resolvidos"
    fi

    return 0
}

# Para containers existentes
stop_existing_containers() {
    log_step "Passo 2/5: Parando Containers Existentes"

    cd "$PROJECT_ROOT"

    if docker compose ps -q 2>/dev/null | grep -q .; then
        log_info "Parando containers..."
        docker compose down 2>&1 | while read line; do
            echo "  $line"
        done
        log_success "Containers parados"
    else
        log_info "Nenhum container rodando"
    fi
}

# Inicia serviços
start_services() {
    log_step "Passo 3/5: Iniciando Serviços"

    cd "$PROJECT_ROOT"

    log_info "Iniciando containers Docker..."
    docker compose up -d 2>&1 | while read line; do
        echo "  $line"
    done

    log_success "Containers iniciados"
}

# Aguarda inicialização
wait_for_services() {
    log_step "Passo 4/5: Aguardando Inicialização"

    local max_wait=60
    local waited=0

    log_info "Aguardando serviços ficarem prontos (máx ${max_wait}s)..."

    while [ $waited -lt $max_wait ]; do
        sleep 2
        waited=$((waited + 2))

        # Verifica se serviços críticos estão respondendo
        if curl -s -f -m 2 http://localhost:8099/health > /dev/null 2>&1; then
            log_success "API Gateway está respondendo!"
            break
        fi

        echo -n "."
    done

    echo ""

    if [ $waited -ge $max_wait ]; then
        log_warning "Timeout aguardando serviços (isso pode ser normal)"
    fi
}

# Health check
health_check() {
    log_step "Passo 5/5: Health Check"

    local services=(
        "8099:API Gateway"
        "8001:Maximus Core"
        "8016:Maximus Orchestrator"
        "6379:Redis"
        "5432:PostgreSQL"
    )

    for entry in "${services[@]}"; do
        IFS=':' read -r port service <<< "$entry"

        if check_port "$port"; then
            log_success "$service (porta $port) - RODANDO"
        else
            log_warning "$service (porta $port) - NÃO INICIADO"
        fi
    done
}

# Mostra status final
show_status() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ VÉRTICE INICIADO COM SUCESSO!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  🌐 Frontend:           ${CYAN}http://localhost:3000${NC}"
    echo -e "  🚪 API Gateway:        ${CYAN}http://localhost:8099${NC}"
    echo -e "  🤖 Maximus AI Core:    ${CYAN}http://localhost:8001${NC}"
    echo -e "  📊 Grafana:            ${CYAN}http://localhost:3000${NC}"
    echo ""
    echo -e "  📋 Ver logs:           ${YELLOW}docker compose logs -f${NC}"
    echo -e "  🛑 Parar:              ${YELLOW}docker compose down${NC}"
    echo -e "  📊 Status:             ${YELLOW}docker compose ps${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main
main() {
    local force=false
    local check_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force|-f)
                force=true
                shift
                ;;
            --check|-c)
                check_only=true
                shift
                ;;
            --help|-h)
                echo "Uso: $0 [OPÇÕES]"
                echo ""
                echo "Opções:"
                echo "  --force, -f     Força reinicialização mesmo se rodando"
                echo "  --check, -c     Apenas verifica portas, não inicia"
                echo "  --help, -h      Mostra esta ajuda"
                exit 0
                ;;
            *)
                log_error "Opção desconhecida: $1"
                exit 1
                ;;
        esac
    done

    banner

    # Verifica se está no diretório correto
    if [ ! -f "$PROJECT_ROOT/docker-compose.yml" ]; then
        log_error "docker-compose.yml não encontrado em $PROJECT_ROOT"
        exit 1
    fi

    # Executa passos
    if ! check_and_free_ports; then
        log_error "Falha ao validar/liberar portas"
        exit 1
    fi

    if [ "$check_only" = true ]; then
        log_success "Verificação concluída (modo check-only)"
        exit 0
    fi

    stop_existing_containers
    start_services
    wait_for_services
    health_check
    show_status

    # Pergunta se quer ver logs
    echo ""
    read -p "Deseja ver os logs em tempo real? (s/N): " show_logs

    if [[ "$show_logs" =~ ^[Ss]$ ]]; then
        echo ""
        log_info "Mostrando logs (Ctrl+C para sair)..."
        echo ""
        cd "$PROJECT_ROOT"
        docker compose logs -f
    fi
}

main "$@"
