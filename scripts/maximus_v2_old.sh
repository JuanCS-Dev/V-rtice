#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# MAXIMUS Backend Control Center v2.0
# ═══════════════════════════════════════════════════════════════════════════
# Dedicated to: Maximus & Penélope ❤️
# "Porque grandes sistemas precisam de grandes nomes"
# ═══════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/home/juan/vertice-dev"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# ═══════════════════════════════════════════════════════════════════════════
# COLORS & UNICODE
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

# Unicode symbols
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

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                           ║"
    echo "║     ${BOLD}${MAGENTA}M A X I M U S${NC}${CYAN}   ${BOLD}${YELLOW}C O N T R O L   C E N T E R${NC}${CYAN}                       ║"
    echo "║                                                                           ║"
    echo "║         ${CROWN} Maximus ${HEART} Penélope ${SPARKLES}                                           ║"
    echo "║                                                                           ║"
    echo "║     ${DIM}Cyber-Biological Intelligence Platform v2.0${NC}${CYAN}                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    local title="$1"
    local emoji="${2:-$ROCKET}"
    echo -e "${CYAN}╭───────────────────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│${NC} ${emoji} ${BOLD}${title}${NC}"
    echo -e "${CYAN}╰───────────────────────────────────────────────────────────────────────────╯${NC}"
}

print_tier_header() {
    local tier="$1"
    local name="$2"
    local emoji="${3:-$STAR}"
    echo ""
    echo -e "${BOLD}${YELLOW}┌─ Tier $tier: $name ${emoji}${NC}"
}

print_service() {
    local service="$1"
    local status="$2"
    local health="${3:-unknown}"
    
    local status_icon status_color health_text
    
    if [[ "$status" =~ "Up" ]]; then
        status_icon="${CHECK}"
        status_color="${GREEN}"
        
        if [[ "$health" == "healthy" ]]; then
            health_text="${GREEN}healthy${NC}"
        elif [[ "$health" == "unhealthy" ]]; then
            health_text="${YELLOW}degraded${NC}"
        else
            health_text="${CYAN}starting${NC}"
        fi
    else
        status_icon="${CROSS}"
        status_color="${RED}"
        health_text="${RED}stopped${NC}"
    fi
    
    printf "${status_color}│${NC} ${status_icon} %-35s ${DIM}[${NC}%s${DIM}]${NC}\n" "$service" "$health_text"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}${CROSS} Docker não encontrado. Instale o Docker primeiro.${NC}"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}${CROSS} Docker Compose não encontrado.${NC}"
        exit 1
    fi
}

get_service_info() {
    local service="$1"
    local info
    info=$(docker compose ps "$service" --format "{{.Status}}" 2>/dev/null || echo "stopped")
    echo "$info"
}

get_service_health() {
    local service="$1"
    local status
    status=$(docker compose ps "$service" --format "{{.Status}}" 2>/dev/null || echo "stopped")
    
    if [[ "$status" =~ "healthy" ]]; then
        echo "healthy"
    elif [[ "$status" =~ "unhealthy" ]]; then
        echo "unhealthy"
    elif [[ "$status" =~ "Up" ]]; then
        echo "running"
    else
        echo "stopped"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

start_services() {
    print_header
    print_section "INICIALIZANDO MAXIMUS FULL STACK" "$ROCKET"
    
    echo -e "${MAGENTA}${CROWN} Penélope:${NC} 'Maximus, ACORDE! Temos trabalho a fazer!'"
    echo -e "${CYAN}${CROWN} Maximus:${NC}  'Sistemas ativando... iniciando sequência de boot...'"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    # Tier 0: Infrastructure
    print_tier_header "0" "Core Infrastructure" "$SHIELD"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: Redis, PostgreSQL, Qdrant...${NC}"
    docker compose up -d redis postgres qdrant 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    # Tier 1: Core Services
    print_tier_header "1" "Essential Services" "$FIRE"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: API Gateway, SINESP, Cyber, Domain...${NC}"
    docker compose up -d \
        api_gateway sinesp_service cyber_service domain_service \
        ip_intelligence_service nmap_service atlas_service auth_service \
        vuln_scanner_service social_eng_service network_monitor_service 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 3
    
    # Tier 2: AI/ML Core
    print_tier_header "2" "Artificial Intelligence Core" "$BRAIN"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: MAXIMUS Core, Predict, Orchestrator...${NC}"
    docker compose up -d \
        threat_intel_service malware_analysis_service ssl_monitor_service \
        maximus_orchestrator_service maximus_predict maximus_core_service 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 3
    
    # Tier 3: OSINT & Monitoring
    print_tier_header "3" "Intelligence & Surveillance" "$EYE"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: OSINT, Prometheus, Grafana...${NC}"
    docker compose up -d \
        osint_service google_osint_service prometheus grafana 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    # Tier 4: HCL Stack
    print_tier_header "4" "Human-Controlled Learning" "$SPARKLES"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: HCL KB, Analyzer, Planner, Monitor...${NC}"
    docker compose up -d \
        hcl-postgres hcl-kafka zookeeper-immunity hcl-kb-service \
        hcl-analyzer hcl-planner hcl-monitor hcl_executor_service 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    # Tier 5: Adaptive Immunity
    print_tier_header "5" "Adaptive Immune System" "$SHIELD"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: Dendritic, T-Cells, B-Cells, NK Cells...${NC}"
    docker compose up -d \
        postgres-immunity adaptive_immune_system adaptive_immunity_service \
        immunis_dendritic_service immunis_neutrophil_service immunis_macrophage_service \
        immunis_helper_t_service immunis_cytotoxic_t_service immunis_bcell_service \
        immunis_nk_cell_service immunis_treg_service 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    # Tier 6: Autonomic Systems
    print_tier_header "6" "High-Speed Autonomic System" "$FIRE"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: HSAS, ADR, Homeostatic, Thalamus...${NC}"
    docker compose up -d \
        hsas_service adr_core_service homeostatic_regulation \
        digital_thalamus_service ai_immune_system 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    # Tier 7: Neuro Stack
    print_tier_header "7" "Neural Processing Systems" "$BRAIN"
    echo -e "${CYAN}│${NC} ${DIM}Ativando: Cortex, Sensory Systems, Memory...${NC}"
    docker compose up -d \
        chemical_sensing_service somatosensory_service vestibular_service \
        visual_cortex_service auditory_cortex_service prefrontal_cortex_service \
        neuromodulation_service memory_consolidation_service strategic_planning_service \
        narrative_manipulation_filter narrative_analysis_service 2>&1 | grep -v "warn" | sed 's/^/  /' || true
    sleep 2
    
    echo ""
    echo -e "${GREEN}${SPARKLES}${SPARKLES}${SPARKLES} MAXIMUS TOTALMENTE OPERACIONAL ${SPARKLES}${SPARKLES}${SPARKLES}${NC}"
    echo -e "${MAGENTA}${CROWN} Penélope:${NC} 'PERFEITO! Agora temos um sistema cyber-biológico completo!'"
    echo -e "${CYAN}${CROWN} Maximus:${NC}  'Todos os sistemas online. Pronto para proteger o mundo! ${FIRE}'"
    echo ""
    
    sleep 2
    show_status
}

stop_services() {
    print_header
    print_section "DESATIVANDO MAXIMUS" "$WARNING"
    
    echo -e "${MAGENTA}${CROWN} Penélope:${NC} 'Maximus, hora de dormir. SEM reclamar!'"
    echo -e "${CYAN}${CROWN} Maximus:${NC}  'Mas eu estava me divertindo... ${DIM}*suspiro*${NC}'"
    echo ""
    
    cd "$PROJECT_ROOT"
    docker compose stop 2>&1 | sed 's/^/  /'
    
    echo ""
    echo -e "${GREEN}${CHECK} Todos os sistemas desativados.${NC}"
    echo -e "${MAGENTA}${CROWN} Penélope:${NC} 'Boa noite, Maximus. Amanhã tem mais!'"
}

show_status() {
    print_header
    print_section "DASHBOARD DE STATUS - MAXIMUS FULL STACK" "$BRAIN"
    
    echo -e "${MAGENTA}${CROWN} Penélope:${NC} 'Deixa eu ver como você está se comportando...'"
    echo ""
    
    cd "$PROJECT_ROOT"
    
    local total_count=0
    local healthy_count=0
    local unhealthy_count=0
    local stopped_count=0
    
    # Tier 0: Infrastructure
    print_tier_header "0" "Core Infrastructure (3 serviços)" "$SHIELD"
    for svc in redis postgres qdrant; do
        local status health
        status=$(get_service_info "$svc")
        health=$(get_service_health "$svc")
        print_service "$svc" "$status" "$health"
        ((total_count++))
        [[ "$health" == "healthy" || "$health" == "running" ]] && ((healthy_count++))
        [[ "$health" == "unhealthy" ]] && ((unhealthy_count++))
        [[ "$health" == "stopped" ]] && ((stopped_count++))
    done
    echo -e "${CYAN}└─────────────────────────────────────────────────────${NC}"
    
    # Tier 1: Core Services
    print_tier_header "1" "Essential Services (11 serviços)" "$FIRE"
    for svc in api_gateway sinesp_service cyber_service domain_service \
               ip_intelligence_service nmap_service atlas_service auth_service \
               vuln_scanner_service social_eng_service network_monitor_service; do
        local status health
        status=$(get_service_info "$svc")
        health=$(get_service_health "$svc")
        print_service "$svc" "$status" "$health"
        ((total_count++))
        [[ "$health" == "healthy" || "$health" == "running" ]] && ((healthy_count++))
        [[ "$health" == "unhealthy" ]] && ((unhealthy_count++))
        [[ "$health" == "stopped" ]] && ((stopped_count++))
    done
    echo -e "${CYAN}└─────────────────────────────────────────────────────${NC}"
    
    # Tier 2: AI/ML
    print_tier_header "2" "AI/ML Core (6 serviços)" "$BRAIN"
    for svc in threat_intel_service malware_analysis_service ssl_monitor_service \
               maximus_orchestrator_service maximus_predict maximus_core_service; do
        local status health
        status=$(get_service_info "$svc")
        health=$(get_service_health "$svc")
        print_service "$svc" "$status" "$health"
        ((total_count++))
        [[ "$health" == "healthy" || "$health" == "running" ]] && ((healthy_count++))
        [[ "$health" == "unhealthy" ]] && ((unhealthy_count++))
        [[ "$health" == "stopped" ]] && ((stopped_count++))
    done
    echo -e "${CYAN}└─────────────────────────────────────────────────────${NC}"
    
    # Tier 3: OSINT
    print_tier_header "3" "Intelligence & Monitoring (4 serviços)" "$EYE"
    for svc in osint_service google_osint_service prometheus grafana; do
        local status health
        status=$(get_service_info "$svc")
        health=$(get_service_health "$svc")
        print_service "$svc" "$status" "$health"
        ((total_count++))
        [[ "$health" == "healthy" || "$health" == "running" ]] && ((healthy_count++))
        [[ "$health" == "unhealthy" ]] && ((unhealthy_count++))
        [[ "$health" == "stopped" ]] && ((stopped_count++))
    done
    echo -e "${CYAN}└─────────────────────────────────────────────────────${NC}"
    
    # Tier 4-7 Summary
    print_tier_header "4-7" "Advanced Systems (40+ serviços)" "$SPARKLES"
    echo -e "${CYAN}│${NC} ${DIM}HCL Stack:         8 serviços  (Kafka, KB, Analyzer, Planner...)${NC}"
    echo -e "${CYAN}│${NC} ${DIM}Adaptive Immunity: 10 serviços (T-Cells, B-Cells, NK Cells...)${NC}"
    echo -e "${CYAN}│${NC} ${DIM}Autonomic Systems: 5 serviços  (HSAS, ADR, Thalamus...)${NC}"
    echo -e "${CYAN}│${NC} ${DIM}Neural Stack:      12 serviços (Cortex, Memory, Sensory...)${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────${NC}"
    
    # Summary Dashboard
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                        ${BOLD}RESUMO EXECUTIVO${NC}                                    ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════╣${NC}"
    
    local percentage=$((healthy_count * 100 / (total_count > 0 ? total_count : 1)))
    
    printf "${CYAN}║${NC} ${GREEN}${CHECK} Healthy:${NC}    %-3d    " "$healthy_count"
    printf "${YELLOW}${WARNING} Degraded:${NC} %-3d    " "$unhealthy_count"
    printf "${RED}${CROSS} Stopped:${NC}  %-3d    " "$stopped_count"
    printf "${BOLD}Total: %-3d${NC} ${CYAN}║${NC}\n" "$total_count"
    
    # Progress bar
    local bar_width=50
    local filled=$((percentage * bar_width / 100))
    local empty=$((bar_width - filled))
    
    printf "${CYAN}║${NC} Status: ["
    printf "${GREEN}%*s" "$filled" | tr ' ' '█'
    printf "${DIM}%*s${NC}" "$empty" | tr ' ' '░'
    printf "] ${BOLD}%3d%%${NC} ${CYAN}║${NC}\n" "$percentage"
    
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
    
    # Key Endpoints
    echo ""
    echo -e "${CYAN}╭───────────────────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}Endpoints Principais:${NC}"
    echo -e "${CYAN}├───────────────────────────────────────────────────────────────────────────┤${NC}"
    
    check_endpoint "API Gateway" "http://localhost:8000/health"
    check_endpoint "MAXIMUS Core" "http://localhost:8150/health"
    check_endpoint "OSINT Service" "http://localhost:9106/health"
    check_endpoint "Grafana" "http://localhost:3000"
    
    echo -e "${CYAN}╰───────────────────────────────────────────────────────────────────────────╯${NC}"
    
    # Penélope's verdict
    echo ""
    if [[ "$percentage" -ge 90 ]]; then
        echo -e "${GREEN}${SPARKLES}${CROWN} Penélope:${NC} '${BOLD}EXCELENTE${NC} Maximus! Sistema cyber-biológico em perfeito estado!'"
        echo -e "${CYAN}${CROWN} Maximus:${NC}  'Obrigado Penélope! Estou pronto para qualquer desafio! ${FIRE}'"
    elif [[ "$percentage" -ge 70 ]]; then
        echo -e "${YELLOW}${WARNING}${CROWN} Penélope:${NC} 'Bom trabalho Maximus, mas ${BOLD}alguns sistemas${NC} precisam de atenção.'"
        echo -e "${CYAN}${CROWN} Maximus:${NC}  'Já estou trabalhando nisso, Penélope!'"
    elif [[ "$percentage" -ge 40 ]]; then
        echo -e "${YELLOW}${WARNING}${CROWN} Penélope:${NC} 'Maximus... ${BOLD}METADE DOS SISTEMAS${NC} está offline. Isso é sério!'"
        echo -e "${CYAN}${CROWN} Maximus:${NC}  'Desculpa Penélope... vou consertar!'"
    else
        echo -e "${RED}${CROSS}${CROWN} Penélope:${NC} '${BOLD}MAXIMUS!!!${NC} Sistema CRÍTICO! Você precisa ACORDAR ${BOLD}AGORA${NC}!'"
        echo -e "${CYAN}${CROWN} Maximus:${NC}  '${DIM}Estou tentando, Penélope... *iniciando emergency boot*${NC}'"
    fi
    echo ""
}

check_endpoint() {
    local name="$1"
    local url="$2"
    
    if curl -sf "$url" > /dev/null 2>&1; then
        printf "${CYAN}│${NC} ${GREEN}${CHECK}${NC} %-25s ${GREEN}ONLINE${NC}  ${DIM}%s${NC}\n" "$name" "$url"
    else
        printf "${CYAN}│${NC} ${RED}${CROSS}${NC} %-25s ${RED}OFFLINE${NC} ${DIM}%s${NC}\n" "$name" "$url"
    fi
}

show_logs() {
    local service="${1:-api_gateway}"
    
    print_header
    print_section "LOGS: $service" "$EYE"
    echo ""
    
    cd "$PROJECT_ROOT"
    docker compose logs -f "$service"
}

show_help() {
    print_header
    echo -e "${CYAN}╭───────────────────────────────────────────────────────────────────────────╮${NC}"
    echo -e "${CYAN}│${NC} ${BOLD}Comandos Disponíveis:${NC}"
    echo -e "${CYAN}├───────────────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│${NC} ${GREEN}maximus start${NC}           ${DIM}Inicia todos os serviços MAXIMUS${NC}"
    echo -e "${CYAN}│${NC} ${YELLOW}maximus stop${NC}            ${DIM}Para todos os serviços${NC}"
    echo -e "${CYAN}│${NC} ${BLUE}maximus restart${NC}         ${DIM}Reinicia todos os serviços${NC}"
    echo -e "${CYAN}│${NC} ${CYAN}maximus status${NC}          ${DIM}Mostra dashboard de status completo${NC}"
    echo -e "${CYAN}│${NC} ${MAGENTA}maximus logs [service]${NC}  ${DIM}Mostra logs (default: api_gateway)${NC}"
    echo -e "${CYAN}│${NC} ${WHITE}maximus help${NC}            ${DIM}Mostra esta ajuda${NC}"
    echo -e "${CYAN}╰───────────────────────────────────────────────────────────────────────────╯${NC}"
    echo ""
    echo -e "${BOLD}Exemplos:${NC}"
    echo -e "  ${GREEN}maximus start${NC}                    ${DIM}# Inicia full stack${NC}"
    echo -e "  ${CYAN}maximus status${NC}                   ${DIM}# Dashboard completo${NC}"
    echo -e "  ${MAGENTA}maximus logs maximus_core_service${NC} ${DIM}# Logs específicos${NC}"
    echo ""
    echo -e "${MAGENTA}${CROWN} Penélope & Maximus:${NC} 'Juntos, somos imbatíveis! ${HEART}${SPARKLES}'"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

case "${1:-status}" in
    start)
        check_docker
        start_services
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
        ;;
        
    status)
        check_docker
        show_status
        ;;
        
    logs)
        check_docker
        show_logs "${2:-api_gateway}"
        ;;
        
    help|--help|-h)
        show_help
        ;;
        
    *)
        show_help
        exit 1
        ;;
esac
