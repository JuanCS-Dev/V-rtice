# ═══════════════════════════════════════════════════════════════════════════
# ORGANISM LAYER MANAGEMENT - Cyber-Biological Architecture
# ═══════════════════════════════════════════════════════════════════════════
# This file contains layer activation functions for the complete organism
# To be sourced by maximus.sh

# Layer definitions
LAYER1_SERVICES=(
  visual_cortex_service
  auditory_cortex_service
  somatosensory_service
  vestibular_service
  prefrontal_cortex_service
  digital_thalamus_service
  neuromodulation_service
  memory_consolidation_service
)

LAYER2_SERVICES=(
  adaptive_immune_system
  adaptive_immunity_db
  adaptive_immunity_service
  active_immune_core
  ai_immune_system
  immunis_api_service
  immunis_bcell_service
  immunis_cytotoxic_t_service
  immunis_dendritic_service
  immunis_helper_t_service
  immunis_macrophage_service
  immunis_neutrophil_service
  immunis_nk_cell_service
  immunis_treg_service
)

LAYER3_SERVICES=(
  protein_c_service
  tfpi_service
  homeostatic_regulation
  reflex_triage_engine
  rte_service
  rte_quarantine
)

LAYER4_SERVICES=(
  hcl-analyzer
  hcl-executor
  hcl-kb-service
  hcl-monitor
  hcl-planner
)

LAYER5_SERVICES=(
  maximus_core_service
  maximus_eureka
  maximus-oraculo
  maximus_integration_service
  predictive_threat_hunting_service
  strategic_planning_service
  autonomous_investigation_service
)

LAYER6_SERVICES=(
  offensive_gateway
  offensive_orchestrator_service
  offensive_tools_service
  atomic_red_team
  purple_team
  bas_service
  wargaming_crisol
  web_attack_service
  mock_vulnerable_apps
)

LAYER7_SERVICES=(
  chemical_sensing_service
  narrative_analysis_service
  narrative_filter_service
  narrative_manipulation_filter
)

LAYER8_SERVICES=(
  agent_communication
  command_bus_service
  cloud_coordinator_service
  edge_agent_service
  threat_intel_bridge
  reactive_fabric_analysis
  reactive-fabric-bridge
  reactive_fabric_core
)

LAYER9_SERVICES=(
  cuckoo
  qdrant
  kafka-ui-immunity
  seriema_graph
  tataca_ingestion
  tegumentar_service
  vuln_intel_service
  hpc_service
  hsas_service
  hitl_patch_service
  ethical_audit_service
  verdict_engine_service
  adr_core_service
)

# Function to activate a specific layer
activate_layer() {
    local layer_num=$1
    local services_var="LAYER${layer_num}_SERVICES[@]"
    local services=("${!services_var}")

    local layer_names=(
        ""
        "🧠 SENSORY CORTEX (Nervous System)"
        "🛡️ ADAPTIVE & INNATE IMMUNITY"
        "⚖️ HOMEOSTATIC REGULATION"
        "🧩 COGNITIVE SYSTEMS (HCL)"
        "🎯 STRATEGIC INTELLIGENCE"
        "⚔️ OFFENSIVE CAPABILITIES"
        "👃 CHEMICAL/NARRATIVE SENSING"
        "🔗 INTEGRATION & ORCHESTRATION"
        "🔬 SPECIALIZED SERVICES"
    )

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}Layer ${layer_num}:${NC} ${layer_names[$layer_num]}"
    echo -e "${DIM}Services: ${#services[@]}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    cd "$PROJECT_ROOT"
    docker compose up -d "${services[@]}" 2>&1 | grep -E "Started|Created|Running|Error" || true

    echo ""
    echo -e "${GREEN}${CHECK}${NC} Layer ${layer_num} activation complete"
}

# Function to show layer status
show_layer_status() {
    local layer_num=$1
    local services_var="LAYER${layer_num}_SERVICES[@]"
    local services=("${!services_var}")

    local total=${#services[@]}
    local running=0
    local healthy=0

    for service in "${services[@]}"; do
        if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
            ((running++))
            if docker compose ps "$service" 2>/dev/null | grep -q "healthy"; then
                ((healthy++))
            fi
        fi
    done

    local status_icon="${CROSS}"
    local status_color="${RED}"

    if [ "$running" -eq "$total" ]; then
        status_icon="${CHECK}"
        status_color="${GREEN}"
    elif [ "$running" -gt 0 ]; then
        status_icon="${WARNING}"
        status_color="${YELLOW}"
    fi

    printf "   ${status_icon} Layer %d: ${status_color}%2d${NC}/${total} running, ${GREEN}%2d${NC} healthy\n" \
        "$layer_num" "$running" "$healthy"
}

# Function to activate all organism layers
activate_full_organism() {
    print_header
    print_section "ATIVAÇÃO DO ORGANISMO COMPLETO" "🧬"

    echo -e "${BOLD}${YELLOW}AVISO:${NC} Isto irá ativar TODAS as 9 camadas do organismo cibernético!"
    echo -e "${DIM}Total de ~99 serviços${NC}"
    echo ""
    read -p "Continuar? (s/N) " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        echo -e "${YELLOW}${WARNING}${NC} Operação cancelada"
        return 1
    fi

    echo ""
    echo -e "${BOLD}${CYAN}Iniciando ressurreição do organismo...${NC}"
    echo ""

    for layer in {1..9}; do
        activate_layer "$layer"
        sleep 2
    done

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${GREEN}${CHECK} ORGANISMO COMPLETO ATIVADO!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${DIM}Aguardando estabilização (30s)...${NC}"
    sleep 30

    # Show final status
    cmd_status
}

# Function to show organism layer map
show_organism_map() {
    print_header
    print_section "MAPA DO ORGANISMO CIBERNÉTICO" "🧬"

    echo ""
    for layer in {1..9}; do
        show_layer_status "$layer"
    done

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Interactive layer menu
interactive_layer_menu() {
    while true; do
        print_header
        print_section "GERENCIAMENTO DE CAMADAS ORGÂNICAS" "🧬"

        echo ""
        echo -e "${BOLD}Status atual das camadas:${NC}"
        for layer in {1..9}; do
            show_layer_status "$layer"
        done

        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${BOLD}Opções:${NC}"
        echo -e "   ${CYAN}1-9${NC} - Ativar Layer específica"
        echo -e "   ${CYAN} A ${NC} - Ativar TODAS as layers (organismo completo)"
        echo -e "   ${CYAN} M ${NC} - Mostrar mapa detalhado"
        echo -e "   ${CYAN} Q ${NC} - Voltar ao menu principal"
        echo ""
        read -p "$(echo -e ${BOLD}Escolha uma opção:${NC} )" choice

        case $choice in
            [1-9])
                activate_layer "$choice"
                read -p "Pressione Enter para continuar..."
                ;;
            [Aa])
                activate_full_organism
                read -p "Pressione Enter para continuar..."
                ;;
            [Mm])
                show_organism_map
                read -p "Pressione Enter para continuar..."
                ;;
            [Qq])
                break
                ;;
            *)
                echo -e "${RED}${CROSS}${NC} Opção inválida!"
                sleep 1
                ;;
        esac
    done
}
