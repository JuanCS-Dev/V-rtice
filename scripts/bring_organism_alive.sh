#!/bin/bash
set -e

echo "🧬 INICIANDO RESSURREIÇÃO DO ORGANISMO CIBERNÉTICO..."
echo ""

cd /home/juan/vertice-dev

# LAYER 1: SENSORY CORTEX (Nervous System)
echo "🧠 LAYER 1: Ativando Sistema Nervoso Central..."
docker compose up -d \
  visual_cortex_service \
  auditory_cortex_service \
  somatosensory_service \
  vestibular_service \
  prefrontal_cortex_service \
  digital_thalamus_service \
  neuromodulation_service \
  memory_consolidation_service \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 2: IMMUNE SYSTEM (Adaptive + Innate)
echo ""
echo "🛡️ LAYER 2: Ativando Sistema Imune Completo..."
docker compose up -d \
  adaptive_immune_system \
  adaptive_immunity_db \
  adaptive_immunity_service \
  active_immune_core \
  ai_immune_system \
  immunis_api_service \
  immunis_bcell_service \
  immunis_cytotoxic_t_service \
  immunis_dendritic_service \
  immunis_helper_t_service \
  immunis_macrophage_service \
  immunis_neutrophil_service \
  immunis_nk_cell_service \
  immunis_treg_service \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 3: REGULATION SYSTEMS
echo ""
echo "⚖️ LAYER 3: Ativando Sistemas de Regulação..."
docker compose up -d \
  protein_c_service \
  tfpi_service \
  homeostatic_regulation \
  reflex_triage_engine \
  rte_service \
  rte_quarantine \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 4: COGNITIVE SYSTEMS (HCL)
echo ""
echo "🧩 LAYER 4: Ativando Cognição Superior (HCL)..."
docker compose up -d \
  hcl-analyzer \
  hcl-executor \
  hcl-kb-service \
  hcl-monitor \
  hcl-planner \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 5: STRATEGIC INTELLIGENCE
echo ""
echo "🎯 LAYER 5: Ativando Inteligência Estratégica..."
docker compose up -d \
  maximus_core_service \
  maximus_eureka \
  maximus-oraculo \
  maximus_integration_service \
  predictive_threat_hunting_service \
  strategic_planning_service \
  autonomous_investigation_service \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 6: OFFENSIVE CAPABILITIES
echo ""
echo "⚔️ LAYER 6: Ativando Capacidades Ofensivas..."
docker compose up -d \
  offensive_gateway \
  offensive_orchestrator_service \
  offensive_tools_service \
  atomic_red_team \
  purple_team \
  bas_service \
  wargaming_crisol \
  web_attack_service \
  mock_vulnerable_apps \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 7: SENSORY INPUT (Chemical, Narrative)
echo ""
echo "👃 LAYER 7: Ativando Sistemas Sensoriais Químicos..."
docker compose up -d \
  chemical_sensing_service \
  narrative_analysis_service \
  narrative_filter_service \
  narrative_manipulation_filter \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 8: INTEGRATION & ORCHESTRATION
echo ""
echo "🔗 LAYER 8: Ativando Camada de Integração..."
docker compose up -d \
  agent_communication \
  command_bus_service \
  cloud_coordinator_service \
  edge_agent_service \
  threat_intel_bridge \
  reactive_fabric_analysis \
  reactive-fabric-bridge \
  reactive_fabric_core \
  2>&1 | grep -E "Started|Created|Running" || true

# LAYER 9: SPECIALIZED SERVICES
echo ""
echo "🔬 LAYER 9: Ativando Serviços Especializados..."
docker compose up -d \
  cuckoo \
  qdrant \
  kafka-ui-immunity \
  seriema_graph \
  tataca_ingestion \
  tegumentar_service \
  vuln_intel_service \
  hpc_service \
  hsas_service \
  hitl_patch_service \
  ethical_audit_service \
  verdict_engine_service \
  adr_core_service \
  2>&1 | grep -E "Started|Created|Running" || true

echo ""
echo "✅ TODAS AS CAMADAS INICIADAS!"
echo "⏳ Aguardando estabilização (30s)..."
sleep 30

