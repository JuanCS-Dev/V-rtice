"""
Service Mapping - Environment Variable to Service Registry Name

This module provides automatic mapping from legacy environment variable names
to Service Registry service names, enabling gradual migration from hardcoded
URLs to dynamic service discovery.

Author: Vértice Team
"""

# Automatic mapping from ENV VAR suffix to service_name
# Format: ENV_VAR_NAME -> service_name (in registry)
SERVICE_NAME_MAPPING = {
    # Core Services
    "MAXIMUS_CORE_SERVICE": "maximus_core_service",
    "MAXIMUS_ORCHESTRATOR": "maximus_orchestrator_service",
    "MAXIMUS_PREDICT": "maximus_predict_service",
    "MAXIMUS_EUREKA": "maximus_eureka_service",

    # Intelligence & OSINT
    "OSINT_SERVICE": "osint_service",
    "NMAP_SERVICE": "nmap_service",
    "IP_INTELLIGENCE_SERVICE": "ip_intel_service",
    "CYBER_SERVICE": "cyber_service",
    "THREAT_INTEL_SERVICE": "threat_intel_service",
    "SSL_MONITOR_SERVICE": "ssl_monitor_service",
    "DOMAIN_SERVICE": "domain_service",
    "SINESP_SERVICE": "sinesp_service",
    "ATLAS_SERVICE": "atlas_service",
    "NETWORK_MONITOR_SERVICE": "network_monitor_service",

    # Offensive Services
    "SOCIAL_ENG_SERVICE": "social_eng_service",
    "MALWARE_ANALYSIS_SERVICE": "malware_analysis_service",
    "VULN_SCANNER_SERVICE": "vuln_scanner_service",
    "OFFENSIVE_TOOLS": "offensive_tools_service",
    "WEB_ATTACK": "web_attack_service",
    "C2_ORCHESTRATION": "c2_orchestration_service",

    # Immune System
    "ACTIVE_IMMUNE_CORE": "active_immune_core_service",
    "ADAPTIVE_IMMUNITY": "adaptive_immunity_service",
    "IMMUNIS_API": "immunis_api_service",
    "IMMUNIS_BCELL": "immunis_bcell_service",
    "IMMUNIS_CYTOTOXIC_T": "immunis_cytotoxic_t_service",
    "IMMUNIS_DENDRITIC": "immunis_dendritic_service",
    "IMMUNIS_HELPER_T": "immunis_helper_t_service",
    "IMMUNIS_MACROPHAGE": "immunis_macrophage_service",
    "IMMUNIS_NEUTROPHIL": "immunis_neutrophil_service",
    "IMMUNIS_NK_CELL": "immunis_nk_cell_service",
    "IMMUNIS_TREG": "immunis_treg_service",

    # Sensory Services
    "VISUAL_CORTEX": "visual_cortex_service",
    "AUDITORY_CORTEX": "auditory_cortex_service",
    "SOMATOSENSORY": "somatosensory_service",
    "CHEMICAL_SENSING": "chemical_sensing_service",
    "VESTIBULAR": "vestibular_service",

    # Cognitive Services
    "PREFRONTAL_CORTEX": "prefrontal_cortex_service",
    "DIGITAL_THALAMUS": "digital_thalamus_service",
    "MEMORY_CONSOLIDATION": "memory_consolidation_service",
    "NEUROMODULATION": "neuromodulation_service",

    # HCL Services
    "HCL_ANALYZER": "hcl_analyzer_service",
    "HCL_PLANNER": "hcl_planner_service",
    "HCL_EXECUTOR": "hcl_executor_service",
    "HCL_MONITOR": "hcl_monitor_service",
    "HCL_KB": "hcl_kb_service",

    # Support Services
    "VAULT_SERVICE": "vault_service",
    "HITL_PATCH_SERVICE": "hitl_patch_service",
    "WARGAMING_CRISOL": "wargaming_crisol_service",
    "AUTH_SERVICE": "auth_service",
    "EDGE_AGENT": "edge_agent_service",
    "CLOUD_COORDINATOR": "cloud_coordinator_service",
    "HPC_SERVICE": "hpc_service",
    "HSAS_SERVICE": "hsas_service",

    # Specialized Services
    "NARRATIVE_FILTER": "narrative_filter_service",
    "NARRATIVE_ANALYSIS": "narrative_analysis_service",
    "AUTONOMOUS_INVESTIGATION": "autonomous_investigation_service",
    "PREDICTIVE_THREAT_HUNTING": "predictive_threat_hunting_service",
    "REFLEX_TRIAGE_ENGINE": "reflex_triage_engine",
    "HOMEOSTATIC_REGULATION": "homeostatic_regulation",
    "BAS": "bas_service",
    "RTE_SERVICE": "rte_service",

    # Integration & Communication
    "MAXIMUS_INTEGRATION": "maximus_integration_service",
    "COMMAND_BUS": "command_bus_service",
    "AGENT_COMMUNICATION": "agent_communication_service",

    # Data & Storage
    "TATACA_INGESTION": "tataca_ingestion_service",
    "SERIEMA_GRAPH": "seriema_graph_service",

    # Test Services
    "TEST_SERVICE": "test_service",
}


def env_var_to_service_name(env_var: str) -> str:
    """
    Convert environment variable name to service registry name.

    Examples:
        MAXIMUS_CORE_SERVICE_URL -> maximus_core_service
        OSINT_SERVICE_URL -> osint_service
        HCL_ANALYZER_URL -> hcl_analyzer_service

    Args:
        env_var: Environment variable name (e.g., "MAXIMUS_CORE_SERVICE_URL")

    Returns:
        Service name for registry lookup

    Raises:
        KeyError: If mapping not found
    """
    # Remove _URL/_ENDPOINT suffix
    clean_var = env_var.replace("_URL", "").replace("_ENDPOINT", "").replace("_SERVICE", "")

    # Direct lookup
    if clean_var in SERVICE_NAME_MAPPING:
        return SERVICE_NAME_MAPPING[clean_var]

    # Try with _SERVICE suffix
    service_key = f"{clean_var}_SERVICE"
    if service_key in SERVICE_NAME_MAPPING:
        return SERVICE_NAME_MAPPING[service_key]

    # Fallback: convert to snake_case and append _service
    # e.g., MAXIMUS_CORE -> maximus_core_service
    return f"{clean_var.lower()}_service"


def get_all_mapped_services():
    """Get all service names that have env var mappings."""
    return set(SERVICE_NAME_MAPPING.values())
