# Docker-Compose Command Override Audit

## adaptive_immune_system
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "hitl.api.main:app", "--host", "0.0.0.0", "--port", "8003"]`
**Compose command:** `uvicorn hitl.api.main:app --host 0.0.0.0 --port 8003 --reload`

## adr_core_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8030 --reload`

## ai_immune_system
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8014`

## api_gateway
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## atlas_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

## auditory_cortex_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8007`

## auth_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## chemical_sensing_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8009`

## cloud_coordinator_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8011"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8051 --reload`

## cyber_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## digital_thalamus_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8013"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8012`

## domain_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8014"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## edge_agent_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8015"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8021 --reload`

## ethical_audit_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8350"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8612 --reload`

## google_osint_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8016"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8031 --reload`

## hcl_analyzer_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8017"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8020 --reload`

## hcl_executor_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8018"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8021 --reload`

## hcl_kb_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8019"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8022 --reload`

## hcl_monitor_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8020"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8023 --reload`

## hcl_planner_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8021"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8024 --reload`

## homeostatic_regulation
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8022"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8015`

## hpc_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8023"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8027 --reload`

## hsas_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8024"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8003 --reload`

## immunis_api_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8025"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8005 --reload`

## immunis_bcell_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8026"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8016 --reload`

## immunis_cytotoxic_t_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8027"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8018 --reload`

## immunis_dendritic_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8028"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8014 --reload`

## immunis_helper_t_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8029"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8017 --reload`

## immunis_macrophage_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8012 --reload`

## immunis_neutrophil_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8031"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8013 --reload`

## immunis_nk_cell_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8032"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8019 --reload`

## ip_intelligence_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8034"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80`

## malware_analysis_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8035"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8014 --reload`

## maximus_core_service
**Category:** CONFLICTING
**Reason:** Compose uses direct python, Dockerfile uses uvicorn
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8150", "--workers", "4"]`
**Compose command:** `python main.py`

## maximus_eureka
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8036"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8200 --reload`

## maximus_integration_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8037"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8099 --reload`

## maximus_orchestrator_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8016"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8016 --reload`

## maximus_predict
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8040"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 80 --reload`

## narrative_manipulation_filter
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8043"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8013`

## network_monitor_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8044"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## network_recon_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8045"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8032 --reload`

## neuromodulation_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8046"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8033 --reload`

## nmap_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8047"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## osint_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8049"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8007 --reload`

## prefrontal_cortex_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8051"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8011`

## reflex_triage_engine
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8052"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8012 --reload`

## rte_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8053"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8026 --reload`

## seriema_graph
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8300"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8029 --reload`

## sinesp_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8054"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## social_eng_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8055"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## somatosensory_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8056"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8008`

## ssl_monitor_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8057"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8015 --reload`

## strategic_planning_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8058"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8042 --reload`

## tataca_ingestion
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8400"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8028 --reload`

## threat_intel_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8059"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 8013 --reload`

## vestibular_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8060"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8010`

## visual_cortex_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8061"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8006`

## vuln_intel_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8062"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8033 --reload`

## vuln_scanner_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8063"]`
**Compose command:** `uvicorn main:app --host 0.0.0.0 --port 80 --reload`

## web_attack_service
**Category:** UNNECESSARY
**Reason:** Minor uvicorn param differences (likely safe to remove)
**Dockerfile CMD:** `["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8064"]`
**Compose command:** `uvicorn api:app --host 0.0.0.0 --port 8034 --reload`

