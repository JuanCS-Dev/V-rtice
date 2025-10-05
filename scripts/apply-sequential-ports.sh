#!/bin/bash

###############################################################################
# APPLY SEQUENTIAL PORTS - Aplica mapeamento sequencial de portas
###############################################################################
#
# Este script:
# 1. Faz backup do docker-compose.yml
# 2. Aplica portas sequenciais (9000-9099)
# 3. Para containers existentes
# 4. Reinicia com novas portas
#
# Uso:
#   ./apply-sequential-ports.sh        # Aplica mudanças
#   ./apply-sequential-ports.sh revert # Reverte para backup
#
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
BACKUP_FILE="$PROJECT_ROOT/docker-compose.yml.backup"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     SEQUENTIAL PORT MAPPER - VÉRTICE/MAXIMUS AI           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

log_info() {
    echo -e "${CYAN}ℹ${NC} $1"
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

# Reverte para backup
revert() {
    banner
    log_info "Revertendo para configuração original..."

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup não encontrado em $BACKUP_FILE"
        exit 1
    fi

    cp "$BACKUP_FILE" "$COMPOSE_FILE"
    log_success "docker-compose.yml restaurado"

    log_info "Reiniciando containers..."
    cd "$PROJECT_ROOT"
    docker compose down
    docker compose up -d

    log_success "Containers reiniciados com portas originais"
}

# Aplica portas sequenciais
apply() {
    banner

    # Backup
    log_info "Criando backup..."
    if [ -f "$BACKUP_FILE" ]; then
        log_warning "Backup já existe, sobrescrevendo..."
    fi
    cp "$COMPOSE_FILE" "$BACKUP_FILE"
    log_success "Backup criado: $BACKUP_FILE"

    # Para containers
    log_info "Parando containers existentes..."
    cd "$PROJECT_ROOT"
    docker compose down 2>&1 | grep -v "variable is not set" || true
    log_success "Containers parados"

    # Aplica mudanças
    log_info "Aplicando portas sequenciais (9000-9099)..."

    # Mapeamento: serviço -> nova porta
    declare -A PORT_MAP=(
        # Core & API (9000-9009)
        ["api_gateway"]="9000:8099"
        ["maximus_core_service"]="9001:8001"
        ["maximus_orchestrator_service"]="9002:8016"
        ["maximus_predict"]="9003:80"
        ["adr_core_service"]="9004:8010"
        ["auth_service"]="9005:80"

        # Cyber Security (9010-9029)
        ["ip_intelligence_service"]="9010:80"
        ["network_monitor_service"]="9011:80"
        ["nmap_service"]="9012:80"
        ["domain_service"]="9013:80"
        ["vuln_scanner_service"]="9014:80"
        ["threat_intel_service"]="9015:80"
        ["malware_analysis_service"]="9016:80"
        ["ssl_monitor_service"]="9017:80"
        ["social_eng_service"]="9018:80"
        ["cyber_service"]="9019:80"

        # OSINT (9030-9039)
        ["osint-service"]="9030:80"
        ["google_osint_service"]="9031:80"
        ["sinesp_service"]="9032:80"

        # Offensive Arsenal (9040-9049)
        ["network_recon_service"]="9040:80"
        ["vuln_intel_service"]="9041:8080"
        ["web_attack_service"]="9042:80"
        ["c2_orchestration_service"]="9043:80"
        ["bas_service"]="9044:80"
        ["offensive_gateway"]="9045:80"

        # HCL (9050-9059)
        ["hcl-analyzer"]="9050:80"
        ["hcl_executor_service"]="9051:80"
        ["hcl_kb_service"]="9052:80"
        ["hcl-monitor"]="9053:80"
        ["hcl-planner"]="9054:80"

        # Maximus Subsystems (9060-9069)
        ["maximus-eureka"]="9060:80"
        ["maximus-oraculo"]="9061:80"
        ["maximus-models"]="9062:80"
        ["maximus_integration_service"]="9063:80"

        # ASA & Cognitive (9070-9089)
        ["prefrontal_cortex_service"]="9070:80"
        ["visual_cortex_service"]="9071:80"
        ["auditory_cortex_service"]="9072:80"
        ["somatosensory_service"]="9073:80"
        ["chemical_sensing_service"]="9074:80"
        ["vestibular_service"]="9075:80"
        ["digital_thalamus_service"]="9076:80"
        ["narrative_manipulation_filter"]="9077:80"

        # Immunis (9080-9089)
        ["immunis_api_service"]="9080:80"
        ["immunis_macrophage_service"]="9081:80"
        ["immunis_neutrophil_service"]="9082:80"
        ["immunis_dendritic_service"]="9083:80"
        ["immunis_bcell_service"]="9084:80"
        ["immunis_helper_t_service"]="9085:80"
        ["immunis_cytotoxic_t_service"]="9086:80"
        ["immunis_nk_cell_service"]="9087:80"
        ["ai_immune_system"]="9088:80"
        ["homeostatic_regulation"]="9089:80"

        # Infrastructure (9090-9099)
        ["prometheus"]="9090:9090"
        ["grafana"]="9091:3000"
        ["atlas_service"]="9092:80"
        ["rte-service"]="9093:80"
        ["hpc-service"]="9094:80"
        ["tataca_ingestion"]="9095:80"
        ["seriema_graph"]="9096:80"
    )

    # Cria arquivo temporário
    local temp_file=$(mktemp)
    cp "$COMPOSE_FILE" "$temp_file"

    # Aplica cada mapeamento
    for service in "${!PORT_MAP[@]}"; do
        local new_port="${PORT_MAP[$service]}"

        # Usa sed para substituir a seção de ports do serviço
        # Procura o serviço e substitui a linha de ports
        sed -i "/^  ${service}:/,/^  [a-z_-]*:/ {
            s|ports:.*|ports:|
            s|- \".*:.*\"|- \"${new_port}\"|
        }" "$temp_file" 2>/dev/null || true
    done

    # Move arquivo temporário
    mv "$temp_file" "$COMPOSE_FILE"

    log_success "Portas sequenciais aplicadas"

    # Reinicia
    log_info "Iniciando containers com novas portas..."
    docker compose up -d 2>&1 | grep -v "variable is not set" | tail -20

    echo ""
    log_success "✨ PORTAS SEQUENCIAIS APLICADAS COM SUCESSO!"
    echo ""
    echo -e "  ${CYAN}Novo Range:${NC} 9000-9099"
    echo -e "  ${CYAN}API Gateway:${NC} http://localhost:9000"
    echo -e "  ${CYAN}Maximus Core:${NC} http://localhost:9001"
    echo -e "  ${CYAN}Backup:${NC} $BACKUP_FILE"
    echo ""
    echo -e "  ${YELLOW}Para reverter:${NC} ./scripts/apply-sequential-ports.sh revert"
    echo ""
}

# Main
case "${1:-apply}" in
    revert)
        revert
        ;;
    apply|*)
        apply
        ;;
esac
