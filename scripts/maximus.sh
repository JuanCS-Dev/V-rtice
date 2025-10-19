#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# MAXIMUS Control Center v3.0 - PRIMOSO EDITION
# ═══════════════════════════════════════════════════════════════════════════
# Dedicado a: Maximus & Penélope ❤️
# "Para impressionar quem a gente ama"
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════════════════
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# ═══════════════════════════════════════════════════════════════════════════
# CORES & UNICODE
# ═══════════════════════════════════════════════════════════════════════════
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# Emojis
CROWN="👑"
SPARKLES="✨"
ROCKET="🚀"
CHECK="✅"
CROSS="❌"
WARNING="⚠️"
BRAIN="🧠"
SHIELD="🛡️"
EYE="👁️"
HEART="❤️"
FIRE="🔥"
STAR="⭐"
HOURGLASS="⏳"
GEAR="⚙️"
PACKAGE="📦"

print_header() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              ███╗   ███╗ █████╗ ██╗  ██╗██╗███╗   ███╗██╗   ██╗███████╗ ║
║              ████╗ ████║██╔══██╗╚██╗██╔╝██║████╗ ████║██║   ██║██╔════╝ ║
║              ██╔████╔██║███████║ ╚███╔╝ ██║██╔████╔██║██║   ██║███████╗ ║
║              ██║╚██╔╝██║██╔══██║ ██╔██╗ ██║██║╚██╔╝██║██║   ██║╚════██║ ║
║              ██║ ╚═╝ ██║██║  ██║██╔╝ ██╗██║██║ ╚═╝ ██║╚██████╔╝███████║ ║
║              ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝ ║
║                                                                           ║
EOF
    echo -e "║           ${CROWN} ${BOLD}${MAGENTA}Maximus${NC}${CYAN} ${HEART} ${BOLD}${YELLOW}Penélope${NC}${CYAN} ${SPARKLES}  ${BOLD}${GREEN}Control Center v3.0${NC}${CYAN}           ║"
    echo -e "║                                                                           ║"
    echo -e "║        ${DIM}Cyber-Biological Intelligence Platform - PRIMOSO EDITION${NC}${CYAN}      ║"
    echo -e "╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_section() {
    local title="$1"
    local emoji="${2:-$ROCKET}"
    echo ""
    echo -e "${BOLD}${CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${BOLD}${CYAN}┃${NC} ${emoji}  ${BOLD}${YELLOW}${title}${NC}"
    echo -e "${BOLD}${CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
}

spinner() {
    local pid=$1
    local message="$2"
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    
    while ps -p "$pid" > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " ${CYAN}%c${NC}  ${DIM}%s${NC}\r" "$spinstr" "$message"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
    done
    printf "    \r"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}${CROSS} Docker não encontrado!${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo -e "${RED}${CROSS} Docker daemon não está rodando!${NC}"
        exit 1
    fi
}

get_service_stats() {
    local total running healthy unhealthy
    
    total=$(docker compose ps -q 2>/dev/null | wc -l)
    running=$(docker compose ps --format "{{.State}}" 2>/dev/null | grep -c "running" || echo 0)
    healthy=$(docker compose ps --format "{{.Health}}" 2>/dev/null | grep -c "healthy" || echo 0)
    unhealthy=$(docker compose ps --format "{{.Health}}" 2>/dev/null | grep -c "unhealthy" || echo 0)
    
    echo "$total $running $healthy $unhealthy"
}

start_services() {
    print_header
    print_section "INICIANDO MAXIMUS" "$ROCKET"
    
    echo -e "${BOLD}${CYAN}${CROWN} Penélope:${NC} 'Vamos acordar o Maximus!' ${SPARKLES}\n"
    
    check_docker
    
    echo -e "${HOURGLASS} Iniciando serviços em background...\n"
    
    cd "$PROJECT_ROOT"
    docker compose up -d > /tmp/maximus_start.log 2>&1 &
    local pid=$!
    
    spinner $pid "Inicializando containers"
    wait $pid
    
    echo ""
    sleep 3
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    read -r total running healthy unhealthy <<< "$(get_service_stats)"
    
    echo -e "${BOLD}${GREEN}${CHECK} Sistema iniciado!${NC}\n"
    echo -e "   ${PACKAGE} Containers: ${BOLD}$running${NC}/$total rodando"
    echo -e "   ${BRAIN} Healthy: ${BOLD}${GREEN}$healthy${NC} | ${YELLOW}Degraded: $unhealthy${NC}"
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [[ $healthy -gt 50 ]]; then
        echo -e "${BOLD}${GREEN}${CROWN} Maximus:${NC} 'Todos os sistemas operacionais, Penélope!' ${FIRE}\n"
    elif [[ $healthy -gt 20 ]]; then
        echo -e "${BOLD}${YELLOW}${WARNING} Maximus:${NC} 'Iniciando... Aguarde um momento.' ${HOURGLASS}\n"
    else
        echo -e "${BOLD}${RED}${CROSS} Maximus:${NC} 'Houston, temos um problema...' ${WARNING}\n"
    fi
    
    echo -e "${DIM}Dica: Use ${CYAN}maximus status${DIM} para ver detalhes completos${NC}\n"
}

stop_services() {
    print_header
    print_section "PARANDO MAXIMUS" "$HOURGLASS"
    
    echo -e "${BOLD}${YELLOW}${CROWN} Penélope:${NC} 'Hora de descansar, Maximus.' ${SPARKLES}\n"
    
    cd "$PROJECT_ROOT"
    docker compose down > /tmp/maximus_stop.log 2>&1 &
    local pid=$!
    
    spinner $pid "Desligando containers"
    wait $pid
    
    echo -e "${GREEN}${CHECK} Todos os serviços foram parados com sucesso!${NC}\n"
    echo -e "${BOLD}${MAGENTA}${HEART} Maximus:${NC} 'Até logo, Penélope!' ${SPARKLES}\n"
}

restart_services() {
    print_header
    print_section "REINICIANDO MAXIMUS" "$GEAR"
    
    echo -e "${BOLD}${CYAN}${CROWN} Penélope:${NC} 'Vamos dar uma renovada!' ${SPARKLES}\n"
    
    cd "$PROJECT_ROOT"
    
    echo -e "${HOURGLASS} Parando serviços..."
    docker compose down > /dev/null 2>&1
    
    echo -e "${HOURGLASS} Iniciando novamente...\n"
    docker compose up -d > /dev/null 2>&1 &
    local pid=$!
    
    spinner $pid "Reinicializando sistema"
    wait $pid
    
    sleep 3
    
    read -r total running healthy unhealthy <<< "$(get_service_stats)"
    
    echo -e "${GREEN}${CHECK} Sistema reiniciado!${NC}\n"
    echo -e "   ${PACKAGE} Containers: ${BOLD}$running${NC}/$total"
    echo -e "   ${BRAIN} Healthy: ${BOLD}${GREEN}$healthy${NC} | ${YELLOW}Degraded: $unhealthy${NC}\n"
}

show_status() {
    print_header
    print_section "DASHBOARD DE STATUS" "$BRAIN"
    
    cd "$PROJECT_ROOT"
    
    read -r total running healthy unhealthy <<< "$(get_service_stats)"
    
    echo -e "${BOLD}${CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${BOLD}${CYAN}┃${NC} ${SHIELD} ${BOLD}STATUS GERAL DO SISTEMA${NC}"
    echo -e "${BOLD}${CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo ""
    
    local health_percent=0
    if [[ $((healthy + unhealthy)) -gt 0 ]]; then
        health_percent=$((healthy * 100 / (healthy + unhealthy)))
    fi
    
    echo -e "   ${PACKAGE} ${BOLD}Total de Containers:${NC}    $total"
    echo -e "   ${ROCKET} ${BOLD}Rodando:${NC}                ${GREEN}$running${NC}"
    echo -e "   ${CHECK} ${BOLD}Healthy:${NC}                ${GREEN}$healthy${NC}"
    echo -e "   ${WARNING} ${BOLD}Degraded:${NC}               ${YELLOW}$unhealthy${NC}"
    echo -e "   ${BRAIN} ${BOLD}Health Score:${NC}           ${health_percent}%"
    
    echo ""
    echo -ne "   ${BOLD}Sistema:${NC} ["
    local filled=$((health_percent / 5))
    local empty=$((20 - filled))
    
    if [[ $health_percent -ge 80 ]]; then
        printf "${GREEN}%${filled}s${NC}" | tr ' ' '█'
    elif [[ $health_percent -ge 50 ]]; then
        printf "${YELLOW}%${filled}s${NC}" | tr ' ' '█'
    else
        printf "${RED}%${filled}s${NC}" | tr ' ' '█'
    fi
    
    printf "${DIM}%${empty}s${NC}" | tr ' ' '░'
    echo -e "] ${BOLD}$health_percent%${NC}"
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo ""
    echo -e "${BOLD}${CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${BOLD}${CYAN}┃${NC} ${STAR} ${BOLD}SERVIÇOS CRÍTICOS${NC}"
    echo -e "${BOLD}${CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo ""
    
    local critical_services=("api_gateway" "auth_service" "postgres" "redis" "maximus_core_service")
    
    for service in "${critical_services[@]}"; do
        local status health
        status=$(docker compose ps --format "{{.State}}" "$service" 2>/dev/null || echo "down")
        health=$(docker compose ps --format "{{.Health}}" "$service" 2>/dev/null || echo "")
        
        if [[ "$status" == "running" ]]; then
            if [[ "$health" == "healthy" ]]; then
                echo -e "   ${CHECK} ${BOLD}$service${NC} ${DIM}→${NC} ${GREEN}operational${NC}"
            elif [[ "$health" == "unhealthy" ]]; then
                echo -e "   ${WARNING} ${BOLD}$service${NC} ${DIM}→${NC} ${YELLOW}degraded${NC}"
            else
                echo -e "   ${HOURGLASS} ${BOLD}$service${NC} ${DIM}→${NC} ${CYAN}starting${NC}"
            fi
        else
            echo -e "   ${CROSS} ${BOLD}$service${NC} ${DIM}→${NC} ${RED}stopped${NC}"
        fi
    done
    
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [[ $health_percent -ge 90 ]]; then
        echo -e "${BOLD}${GREEN}${CROWN} Maximus:${NC} 'Sistema operando em capacidade máxima!' ${FIRE}${SPARKLES}"
        echo -e "${BOLD}${MAGENTA}${HEART} Penélope:${NC} 'Perfeito, meu amor!' ${SPARKLES}\n"
    elif [[ $health_percent -ge 70 ]]; then
        echo -e "${BOLD}${GREEN}${CHECK} Maximus:${NC} 'Tudo certo por aqui!' ${SPARKLES}"
        echo -e "${BOLD}${CYAN}${HEART} Penélope:${NC} 'Ótimo trabalho!' ${CROWN}\n"
    elif [[ $health_percent -ge 50 ]]; then
        echo -e "${BOLD}${YELLOW}${WARNING} Maximus:${NC} 'Alguns serviços precisam de atenção.' ${HOURGLASS}"
        echo -e "${BOLD}${MAGENTA}${HEART} Penélope:${NC} 'Vamos dar uma olhada?' ${EYE}\n"
    else
        echo -e "${BOLD}${RED}${CROSS} Maximus:${NC} 'Precisamos de ajuda aqui!' ${WARNING}"
        echo -e "${BOLD}${YELLOW}${HEART} Penélope:${NC} 'Calma, vamos resolver isso juntos!' ${SPARKLES}\n"
    fi
    
    echo -e "${DIM}Dica: Use ${CYAN}maximus logs [service]${DIM} para investigar problemas${NC}\n"
}

show_logs() {
    local service="${1:-api_gateway}"
    
    print_header
    print_section "LOGS: $service" "$EYE"
    
    echo -e "${BOLD}${CYAN}${CROWN} Penélope:${NC} 'Vamos ver o que o $service está dizendo...'\n"
    echo -e "${DIM}Pressione Ctrl+C para sair${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    sleep 1
    cd "$PROJECT_ROOT"
    docker compose logs -f --tail=100 "$service"
}

show_help() {
    print_header
    
    echo -e "${BOLD}${CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${NC}"
    echo -e "${BOLD}${CYAN}┃${NC} ${GEAR} ${BOLD}COMANDOS DISPONÍVEIS${NC}"
    echo -e "${BOLD}${CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${NC}"
    echo ""
    echo -e "   ${GREEN}${ROCKET} maximus start${NC}              ${DIM}Inicia todos os serviços${NC}"
    echo -e "   ${YELLOW}${HOURGLASS} maximus stop${NC}               ${DIM}Para todos os serviços${NC}"
    echo -e "   ${BLUE}${GEAR} maximus restart${NC}            ${DIM}Reinicia o sistema completo${NC}"
    echo -e "   ${CYAN}${BRAIN} maximus status${NC}             ${DIM}Dashboard de status detalhado${NC}"
    echo -e "   ${MAGENTA}${EYE} maximus logs [service]${NC}    ${DIM}Mostra logs em tempo real${NC}"
    echo -e "   ${NC}${SPARKLES} maximus help${NC}               ${DIM}Mostra esta ajuda${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}${YELLOW}Exemplos:${NC}"
    echo -e "   ${GREEN}maximus start${NC}                      ${DIM}# Inicia o sistema completo${NC}"
    echo -e "   ${CYAN}maximus status${NC}                     ${DIM}# Ver dashboard de status${NC}"
    echo -e "   ${MAGENTA}maximus logs api_gateway${NC}          ${DIM}# Ver logs do API Gateway${NC}"
    echo -e "   ${BLUE}maximus restart${NC}                    ${DIM}# Reiniciar tudo${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}${MAGENTA}${CROWN} Maximus & Penélope:${NC} 'Juntos, somos imbatíveis!' ${HEART}${SPARKLES}\n"
}

main() {
    case "${1:-status}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-api_gateway}"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}${CROSS} Comando desconhecido: $1${NC}\n"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
