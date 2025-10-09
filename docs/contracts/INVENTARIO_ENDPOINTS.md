## API_TEMPLATE.py

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze` | services/API_TEMPLATE.py |
| GET | `/health` | services/API_TEMPLATE.py |
| GET | `/status` | services/API_TEMPLATE.py |


## active_immune_core

| Method | Path | Source |
|--------|------|--------|
| GET | `/` | services/active_immune_core/main.py |
| POST | `/` | services/active_immune_core/api/routes/agents.py |
| GET | `/admin` | services/active_immune_core/api/middleware/auth.py |
| GET | `/agents` | services/active_immune_core/main.py |
| POST | `/agents/clone` | services/active_immune_core/main.py |
| GET | `/agents/{agent_id}` | services/active_immune_core/main.py |
| GET | `/aggregation/{metric_name}` | services/active_immune_core/api/routes/metrics.py |
| POST | `/clear-history` | services/active_immune_core/api/routes/metrics.py |
| POST | `/clone` | services/active_immune_core/api/routes/lymphnode.py |
| DELETE | `/clones/{especializacao}` | services/active_immune_core/api/routes/lymphnode.py |
| GET | `/components` | services/active_immune_core/api/routes/health.py |
| GET | `/components/{component_name}` | services/active_immune_core/api/routes/health.py |
| GET | `/consensus/proposals` | services/active_immune_core/api/routes/coordination.py |
| GET | `/consensus/proposals/{proposal_id}` | services/active_immune_core/api/routes/coordination.py |
| POST | `/consensus/propose` | services/active_immune_core/api/routes/coordination.py |
| GET | `/election` | services/active_immune_core/api/routes/coordination.py |
| POST | `/election/trigger` | services/active_immune_core/api/routes/coordination.py |
| GET | `/expensive` | services/active_immune_core/api/middleware/rate_limit.py |
| GET | `/health` | services/active_immune_core/main.py |
| GET | `/homeostasis` | services/active_immune_core/main.py |
| GET | `/homeostatic-state` | services/active_immune_core/api/routes/lymphnode.py |
| GET | `/list` | services/active_immune_core/api/routes/metrics.py |
| GET | `/live` | services/active_immune_core/api/routes/health.py |
| GET | `/lymphnodes` | services/active_immune_core/main.py |
| GET | `/metrics` | services/active_immune_core/api/routes/lymphnode.py |
| GET | `/rates` | services/active_immune_core/api/routes/metrics.py |
| GET | `/ready` | services/active_immune_core/main.py |
| POST | `/reset-counters` | services/active_immune_core/api/routes/metrics.py |
| GET | `/statistics` | services/active_immune_core/api/routes/metrics.py |
| GET | `/status` | services/active_immune_core/api/routes/coordination.py |
| GET | `/tasks` | services/active_immune_core/api/routes/coordination.py |
| POST | `/tasks` | services/active_immune_core/api/routes/coordination.py |
| DELETE | `/tasks/{task_id}` | services/active_immune_core/api/routes/coordination.py |
| GET | `/tasks/{task_id}` | services/active_immune_core/api/routes/coordination.py |
| GET | `/trends/{metric_name}` | services/active_immune_core/api/routes/metrics.py |
| GET | `/types/available` | services/active_immune_core/api/routes/agents.py |
| POST | `/ws/broadcast` | services/active_immune_core/api/websocket/router.py |
| GET | `/ws/stats` | services/active_immune_core/api/websocket/router.py |
| DELETE | `/{agent_id}` | services/active_immune_core/api/routes/agents.py |
| GET | `/{agent_id}` | services/active_immune_core/api/routes/agents.py |
| PATCH | `/{agent_id}` | services/active_immune_core/api/routes/agents.py |
| POST | `/{agent_id}/actions` | services/active_immune_core/api/routes/agents.py |
| GET | `/{agent_id}/stats` | services/active_immune_core/api/routes/agents.py |


## adaptive_immunity_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/antibody/list` | services/adaptive_immunity_service/api.py |
| GET | `/antibody/{antibody_id}` | services/adaptive_immunity_service/api.py |
| GET | `/health` | services/adaptive_immunity_service/api.py |
| GET | `/history/expansions` | services/adaptive_immunity_service/api.py |
| GET | `/history/maturation` | services/adaptive_immunity_service/api.py |
| POST | `/learning/provide_feedback` | services/adaptive_immunity_service/api.py |
| POST | `/learning/run_maturation` | services/adaptive_immunity_service/api.py |
| POST | `/learning/run_selection` | services/adaptive_immunity_service/api.py |
| POST | `/repertoire/initialize` | services/adaptive_immunity_service/api.py |
| GET | `/repertoire/status` | services/adaptive_immunity_service/api.py |
| GET | `/stats` | services/adaptive_immunity_service/api.py |
| GET | `/status` | services/adaptive_immunity_service/api.py |


## adr_core_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/detect` | services/adr_core_service/main.py |
| GET | `/health` | services/adr_core_service/main.py |
| GET | `/ip_intel/{ip_address}` | services/adr_core_service/main.py |
| POST | `/respond` | services/adr_core_service/main.py |
| GET | `/threat_intel/{indicator}` | services/adr_core_service/main.py |


## ai_immune_system

| Method | Path | Source |
|--------|------|--------|
| GET | `/circuit_breaker/{service_id}/status` | services/ai_immune_system/api.py |
| GET | `/health` | services/ai_immune_system/api.py |
| POST | `/immune_response` | services/ai_immune_system/api.py |
| POST | `/telemetry` | services/ai_immune_system/api.py |


## api_gateway

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/api_gateway/main.py |


## atlas_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/atlas_service/main.py |
| GET | `/map_status` | services/atlas_service/main.py |
| POST | `/query_environment` | services/atlas_service/main.py |
| POST | `/update_environment` | services/atlas_service/main.py |


## auditory_cortex_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_audio` | services/auditory_cortex_service/api.py |
| GET | `/binaural_correlation/status` | services/auditory_cortex_service/api.py |
| GET | `/cocktail_party_triage/status` | services/auditory_cortex_service/api.py |
| GET | `/health` | services/auditory_cortex_service/api.py |


## auth_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/admin_resource` | services/auth_service/main.py |
| GET | `/health` | services/auth_service/main.py |
| POST | `/token` | services/auth_service/main.py |
| GET | `/users/me` | services/auth_service/main.py |


## autonomous_investigation_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/actor` | services/autonomous_investigation_service/api.py |
| POST | `/actor/register` | services/autonomous_investigation_service/api.py |
| GET | `/actor/{actor_id}` | services/autonomous_investigation_service/api.py |
| GET | `/campaign` | services/autonomous_investigation_service/api.py |
| POST | `/campaign/correlate` | services/autonomous_investigation_service/api.py |
| GET | `/campaign/{campaign_id}` | services/autonomous_investigation_service/api.py |
| GET | `/health` | services/autonomous_investigation_service/api.py |
| POST | `/incident/attribute` | services/autonomous_investigation_service/api.py |
| POST | `/incident/ingest` | services/autonomous_investigation_service/api.py |
| POST | `/investigation/initiate` | services/autonomous_investigation_service/api.py |
| GET | `/investigation/{investigation_id}` | services/autonomous_investigation_service/api.py |
| GET | `/stats` | services/autonomous_investigation_service/api.py |
| GET | `/status` | services/autonomous_investigation_service/api.py |


## bas_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/bas_service/api.py |
| GET | `/metrics` | services/bas_service/api.py |
| POST | `/simulate` | services/bas_service/api.py |
| GET | `/simulation/{simulation_id}` | services/bas_service/api.py |
| GET | `/simulation/{simulation_id}/results` | services/bas_service/api.py |


## c2_orchestration_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/command/{command_id}` | services/c2_orchestration_service/api.py |
| GET | `/command/{command_id}/results` | services/c2_orchestration_service/api.py |
| POST | `/execute_command` | services/c2_orchestration_service/api.py |
| GET | `/health` | services/c2_orchestration_service/api.py |
| GET | `/metrics` | services/c2_orchestration_service/api.py |


## chemical_sensing_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/gustatory/status` | services/chemical_sensing_service/api.py |
| GET | `/health` | services/chemical_sensing_service/api.py |
| GET | `/olfactory/status` | services/chemical_sensing_service/api.py |
| POST | `/scan` | services/chemical_sensing_service/api.py |


## cloud_coordinator_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/agents/heartbeat` | services/cloud_coordinator_service/api.py |
| POST | `/agents/register` | services/cloud_coordinator_service/api.py |
| GET | `/agents/status` | services/cloud_coordinator_service/api.py |
| GET | `/agents/{agent_id}` | services/cloud_coordinator_service/api.py |
| GET | `/coordinator/status` | services/cloud_coordinator_service/api.py |
| POST | `/events/ingest` | services/cloud_coordinator_service/api.py |
| GET | `/health` | services/cloud_coordinator_service/api.py |


## create_immunis_apis.py

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/create_immunis_apis.py |
| POST | `/process` | services/create_immunis_apis.py |
| GET | `/status` | services/create_immunis_apis.py |


## cyber_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/cyber_service/main.py |
| POST | `/incident_response` | services/cyber_service/main.py |
| GET | `/security_posture` | services/cyber_service/main.py |
| POST | `/threat_detection` | services/cyber_service/main.py |


## digital_thalamus_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/attention_status` | services/digital_thalamus_service/api.py |
| GET | `/gating_status` | services/digital_thalamus_service/api.py |
| GET | `/health` | services/digital_thalamus_service/api.py |
| POST | `/ingest_sensory_data` | services/digital_thalamus_service/api.py |


## domain_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/domain/{domain_name}` | services/domain_service/main.py |
| GET | `/domains` | services/domain_service/main.py |
| GET | `/health` | services/domain_service/main.py |
| POST | `/query_domain` | services/domain_service/main.py |


## edge_agent_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/batch/stats` | services/edge_agent_service/api.py |
| GET | `/buffer/stats` | services/edge_agent_service/api.py |
| POST | `/control/pause` | services/edge_agent_service/api.py |
| POST | `/control/resume` | services/edge_agent_service/api.py |
| POST | `/event/collect` | services/edge_agent_service/api.py |
| POST | `/event/collect_batch` | services/edge_agent_service/api.py |
| GET | `/health` | services/edge_agent_service/api.py |
| GET | `/metrics` | services/edge_agent_service/api.py |
| GET | `/status` | services/edge_agent_service/api.py |


## ethical_audit_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/api/compliance/certification` | services/ethical_audit_service/api.py |
| POST | `/api/compliance/check` | services/ethical_audit_service/api.py |
| GET | `/api/compliance/dashboard` | services/ethical_audit_service/api.py |
| GET | `/api/compliance/evidence` | services/ethical_audit_service/api.py |
| POST | `/api/compliance/evidence/collect` | services/ethical_audit_service/api.py |
| POST | `/api/compliance/gaps` | services/ethical_audit_service/api.py |
| POST | `/api/compliance/remediation` | services/ethical_audit_service/api.py |
| GET | `/api/compliance/status` | services/ethical_audit_service/api.py |
| POST | `/api/explain` | services/ethical_audit_service/api.py |
| GET | `/api/fairness/alerts` | services/ethical_audit_service/api.py |
| GET | `/api/fairness/drift` | services/ethical_audit_service/api.py |
| POST | `/api/fairness/evaluate` | services/ethical_audit_service/api.py |
| GET | `/api/fairness/health` | services/ethical_audit_service/api.py |
| POST | `/api/fairness/mitigate` | services/ethical_audit_service/api.py |
| GET | `/api/fairness/stats` | services/ethical_audit_service/api.py |
| GET | `/api/fairness/trends` | services/ethical_audit_service/api.py |
| GET | `/api/fl/coordinator/global-model` | services/ethical_audit_service/api.py |
| GET | `/api/fl/coordinator/round-status` | services/ethical_audit_service/api.py |
| POST | `/api/fl/coordinator/start-round` | services/ethical_audit_service/api.py |
| POST | `/api/fl/coordinator/submit-update` | services/ethical_audit_service/api.py |
| GET | `/api/fl/metrics` | services/ethical_audit_service/api.py |
| POST | `/api/hitl/approve` | services/ethical_audit_service/api.py |
| GET | `/api/hitl/audit` | services/ethical_audit_service/api.py |
| POST | `/api/hitl/escalate` | services/ethical_audit_service/api.py |
| POST | `/api/hitl/evaluate` | services/ethical_audit_service/api.py |
| GET | `/api/hitl/queue` | services/ethical_audit_service/api.py |
| POST | `/api/hitl/reject` | services/ethical_audit_service/api.py |
| GET | `/api/privacy/budget` | services/ethical_audit_service/api.py |
| POST | `/api/privacy/dp-query` | services/ethical_audit_service/api.py |
| GET | `/api/privacy/health` | services/ethical_audit_service/api.py |
| GET | `/api/privacy/stats` | services/ethical_audit_service/api.py |
| GET | `/api/xai/drift` | services/ethical_audit_service/api.py |
| GET | `/api/xai/health` | services/ethical_audit_service/api.py |
| GET | `/api/xai/stats` | services/ethical_audit_service/api.py |
| GET | `/api/xai/top-features` | services/ethical_audit_service/api.py |
| GET | `/audit/analytics/risk-heatmap` | services/ethical_audit_service/api.py |
| GET | `/audit/analytics/timeline` | services/ethical_audit_service/api.py |
| POST | `/audit/compliance` | services/ethical_audit_service/api.py |
| POST | `/audit/decision` | services/ethical_audit_service/api.py |
| GET | `/audit/decision/{decision_id}` | services/ethical_audit_service/api.py |
| POST | `/audit/decisions/query` | services/ethical_audit_service/api.py |
| GET | `/audit/metrics` | services/ethical_audit_service/api.py |
| GET | `/audit/metrics/frameworks` | services/ethical_audit_service/api.py |
| POST | `/audit/override` | services/ethical_audit_service/api.py |
| GET | `/audit/overrides/{decision_id}` | services/ethical_audit_service/api.py |
| GET | `/health` | services/ethical_audit_service/api.py |
| GET | `/status` | services/ethical_audit_service/api.py |


## google_osint_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/google_osint_service/main.py |
| POST | `/query_osint` | services/google_osint_service/main.py |


## hcl_analyzer_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/analysis_history` | services/hcl_analyzer_service/main.py |
| POST | `/analyze_metrics` | services/hcl_analyzer_service/main.py |
| GET | `/health` | services/hcl_analyzer_service/main.py |


## hcl_executor_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/execute_plan` | services/hcl_executor_service/main.py |
| GET | `/health` | services/hcl_executor_service/main.py |
| GET | `/k8s_status` | services/hcl_executor_service/main.py |


## hcl_kb_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/hcl_kb_service/main.py |
| GET | `/knowledge_summary` | services/hcl_kb_service/main.py |
| GET | `/retrieve_data/{data_type}` | services/hcl_kb_service/main.py |
| POST | `/store_data` | services/hcl_kb_service/main.py |


## hcl_monitor_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/hcl_monitor_service/main.py |
| GET | `/metrics` | services/hcl_monitor_service/main.py |
| GET | `/metrics/history` | services/hcl_monitor_service/main.py |


## hcl_planner_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/generate_plan` | services/hcl_planner_service/main.py |
| GET | `/health` | services/hcl_planner_service/main.py |
| GET | `/planner_status` | services/hcl_planner_service/main.py |


## homeostatic_regulation

| Method | Path | Source |
|--------|------|--------|
| GET | `/hcl_status` | services/homeostatic_regulation/api.py |
| GET | `/health` | services/homeostatic_regulation/api.py |
| POST | `/trigger_red_line` | services/homeostatic_regulation/api.py |
| POST | `/update_operational_goal` | services/homeostatic_regulation/api.py |


## hpc_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/hpc_service/main.py |
| POST | `/infer` | services/hpc_service/main.py |
| POST | `/observe` | services/hpc_service/main.py |
| POST | `/train` | services/hpc_service/main.py |


## hsas_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/alignment_status` | services/hsas_service/api.py |
| GET | `/health` | services/hsas_service/api.py |
| POST | `/request_explanation` | services/hsas_service/api.py |
| POST | `/submit_feedback` | services/hsas_service/api.py |


## immunis_api_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_api_service/api.py |
| GET | `/immunis_status` | services/immunis_api_service/api.py |
| POST | `/threat_alert` | services/immunis_api_service/api.py |
| POST | `/trigger_immune_response` | services/immunis_api_service/api.py |


## immunis_bcell_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_bcell_service/api.py |
| POST | `/process` | services/immunis_bcell_service/api.py |
| GET | `/status` | services/immunis_bcell_service/api.py |


## immunis_cytotoxic_t_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_cytotoxic_t_service/api.py |
| POST | `/process` | services/immunis_cytotoxic_t_service/api.py |
| GET | `/status` | services/immunis_cytotoxic_t_service/api.py |


## immunis_dendritic_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_dendritic_service/api.py |
| POST | `/process` | services/immunis_dendritic_service/api.py |
| GET | `/status` | services/immunis_dendritic_service/api.py |


## immunis_helper_t_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_helper_t_service/api.py |
| POST | `/process` | services/immunis_helper_t_service/api.py |
| GET | `/status` | services/immunis_helper_t_service/api.py |


## immunis_macrophage_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/artifacts` | services/immunis_macrophage_service/api.py |
| POST | `/cleanup` | services/immunis_macrophage_service/api.py |
| GET | `/health` | services/immunis_macrophage_service/api.py |
| GET | `/metrics` | services/immunis_macrophage_service/api.py |
| POST | `/phagocytose` | services/immunis_macrophage_service/api.py |
| POST | `/present_antigen` | services/immunis_macrophage_service/api.py |
| GET | `/signatures` | services/immunis_macrophage_service/api.py |
| GET | `/status` | services/immunis_macrophage_service/api.py |


## immunis_neutrophil_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_neutrophil_service/api.py |
| GET | `/metrics` | services/immunis_neutrophil_service/api.py |
| POST | `/respond` | services/immunis_neutrophil_service/api.py |
| GET | `/response/{threat_id}` | services/immunis_neutrophil_service/api.py |
| POST | `/self_destruct` | services/immunis_neutrophil_service/api.py |
| GET | `/status` | services/immunis_neutrophil_service/api.py |


## immunis_nk_cell_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/immunis_nk_cell_service/api.py |
| POST | `/process` | services/immunis_nk_cell_service/api.py |
| GET | `/status` | services/immunis_nk_cell_service/api.py |


## immunis_treg_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/alert/evaluate` | services/immunis_treg_service/api.py |
| POST | `/feedback/provide` | services/immunis_treg_service/api.py |
| GET | `/health` | services/immunis_treg_service/api.py |
| GET | `/stats` | services/immunis_treg_service/api.py |
| GET | `/status` | services/immunis_treg_service/api.py |
| POST | `/tolerance/observe` | services/immunis_treg_service/api.py |
| GET | `/tolerance/profile/{entity_id}` | services/immunis_treg_service/api.py |
| GET | `/tolerance/profiles` | services/immunis_treg_service/api.py |


## ip_intelligence_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/ip_intelligence_service/main.py |
| GET | `/ip/{ip_address}` | services/ip_intelligence_service/main.py |
| POST | `/query_ip` | services/ip_intelligence_service/main.py |


## malware_analysis_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze` | services/malware_analysis_service/main.py |
| GET | `/health` | services/malware_analysis_service/main.py |
| POST | `/upload_and_analyze` | services/malware_analysis_service/main.py |


## maximus_core_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/` | services/maximus_core_service/governance_production_server.py |
| GET | `/arousal` | services/maximus_core_service/consciousness/api.py |
| POST | `/arousal/adjust` | services/maximus_core_service/consciousness/api.py |
| POST | `/decision/{decision_id}/approve` | services/maximus_core_service/governance_sse/api_routes.py |
| POST | `/decision/{decision_id}/escalate` | services/maximus_core_service/governance_sse/api_routes.py |
| POST | `/decision/{decision_id}/reject` | services/maximus_core_service/governance_sse/api_routes.py |
| GET | `/esgt/events` | services/maximus_core_service/consciousness/api.py |
| POST | `/esgt/trigger` | services/maximus_core_service/consciousness/api.py |
| POST | `/files/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/datastructures.py |
| GET | `/health` | services/maximus_core_service/main.py |
| GET | `/items/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| PATCH | `/items/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| POST | `/items/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| DELETE | `/items/{item_id}` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| GET | `/items/{item_id}` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/exceptions.py |
| PUT | `/items/{item_id}` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| POST | `/login` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/security/oauth2.py |
| GET | `/metrics` | services/maximus_core_service/consciousness/api.py |
| GET | `/pending` | services/maximus_core_service/governance_sse/api_routes.py |
| POST | `/query` | services/maximus_core_service/main.py |
| POST | `/safety/emergency-shutdown` | services/maximus_core_service/consciousness/api.py |
| GET | `/safety/status` | services/maximus_core_service/consciousness/api.py |
| GET | `/safety/violations` | services/maximus_core_service/consciousness/api.py |
| POST | `/send-notification/{email}` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/background.py |
| POST | `/session/create` | services/maximus_core_service/governance_sse/api_routes.py |
| GET | `/session/{operator_id}/stats` | services/maximus_core_service/governance_sse/api_routes.py |
| GET | `/state` | services/maximus_core_service/consciousness/api.py |
| GET | `/stream/{operator_id}` | services/maximus_core_service/governance_sse/api_routes.py |
| POST | `/test/enqueue` | services/maximus_core_service/governance_sse/api_routes.py |
| POST | `/uploadfile/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/datastructures.py |
| GET | `/users/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/routing.py |
| GET | `/users/me` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/security/http.py |
| GET | `/users/me/items/` | services/maximus_core_service/.venv/lib/python3.11/site-packages/fastapi/param_functions.py |
| POST | `/v1/audio/transcriptions` | services/maximus_core_service/.venv/lib/python3.11/site-packages/transformers/commands/serving.py |
| POST | `/v1/chat/completions` | services/maximus_core_service/.venv/lib/python3.11/site-packages/transformers/commands/serving.py |
| GET | `/v1/models` | services/maximus_core_service/.venv/lib/python3.11/site-packages/transformers/commands/serving.py |
| POST | `/v1/responses` | services/maximus_core_service/.venv/lib/python3.11/site-packages/transformers/commands/serving.py |


## maximus_eureka

| Method | Path | Source |
|--------|------|--------|
| POST | `/detect_pattern` | services/maximus_eureka/api.py |
| POST | `/extract_iocs` | services/maximus_eureka/api.py |
| POST | `/generate_insight` | services/maximus_eureka/api.py |
| GET | `/health` | services/maximus_eureka/api.py |


## maximus_integration_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/maximus_integration_service/main.py |
| POST | `/interact_external_service` | services/maximus_integration_service/main.py |


## maximus_oraculo

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_code` | services/maximus_oraculo/api.py |
| POST | `/auto_implement` | services/maximus_oraculo/api.py |
| GET | `/health` | services/maximus_oraculo/api.py |
| POST | `/predict` | services/maximus_oraculo/api.py |


## maximus_orchestrator_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/maximus_orchestrator_service/main.py |
| POST | `/orchestrate` | services/maximus_orchestrator_service/main.py |
| GET | `/workflow/{workflow_id}/status` | services/maximus_orchestrator_service/main.py |


## maximus_predict

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/maximus_predict/api.py |
| POST | `/predict` | services/maximus_predict/api.py |


## memory_consolidation_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/consolidation/history` | services/memory_consolidation_service/api.py |
| POST | `/consolidation/trigger` | services/memory_consolidation_service/api.py |
| POST | `/event/batch_ingest` | services/memory_consolidation_service/api.py |
| POST | `/event/ingest` | services/memory_consolidation_service/api.py |
| GET | `/health` | services/memory_consolidation_service/api.py |
| GET | `/memory/long_term` | services/memory_consolidation_service/api.py |
| GET | `/memory/long_term/{memory_id}` | services/memory_consolidation_service/api.py |
| GET | `/memory/short_term` | services/memory_consolidation_service/api.py |
| GET | `/stats` | services/memory_consolidation_service/api.py |
| GET | `/status` | services/memory_consolidation_service/api.py |


## narrative_analysis_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/bot/analyze` | services/narrative_analysis_service/api.py |
| POST | `/bot/batch_analyze` | services/narrative_analysis_service/api.py |
| POST | `/graph/add_relation` | services/narrative_analysis_service/api.py |
| GET | `/graph/communities` | services/narrative_analysis_service/api.py |
| POST | `/graph/detect_coordination` | services/narrative_analysis_service/api.py |
| GET | `/graph/influence_scores` | services/narrative_analysis_service/api.py |
| GET | `/health` | services/narrative_analysis_service/api.py |
| GET | `/meme/lineage/{meme_id}` | services/narrative_analysis_service/api.py |
| POST | `/meme/track` | services/narrative_analysis_service/api.py |
| POST | `/propaganda/analyze` | services/narrative_analysis_service/api.py |
| POST | `/propaganda/register_source` | services/narrative_analysis_service/api.py |
| GET | `/stats` | services/narrative_analysis_service/api.py |
| GET | `/status` | services/narrative_analysis_service/api.py |


## narrative_manipulation_filter

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_content` | services/narrative_manipulation_filter/api.py |
| POST | `/api/analyze` | services/narrative_manipulation_filter/api.py |
| GET | `/example` | services/narrative_manipulation_filter/database.py |
| GET | `/health` | services/narrative_manipulation_filter/api.py |
| GET | `/health/simple` | services/narrative_manipulation_filter/api.py |
| GET | `/info` | services/narrative_manipulation_filter/config.py |
| GET | `/stats/cache` | services/narrative_manipulation_filter/api.py |
| GET | `/stats/database` | services/narrative_manipulation_filter/api.py |


## network_monitor_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/network_monitor_service/main.py |
| POST | `/ingest_event` | services/network_monitor_service/main.py |
| GET | `/network_status` | services/network_monitor_service/main.py |
| GET | `/recent_events` | services/network_monitor_service/main.py |


## network_recon_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/network_recon_service/api.py |
| GET | `/metrics` | services/network_recon_service/api.py |
| GET | `/recon_task/{task_id}/results` | services/network_recon_service/api.py |
| GET | `/recon_task/{task_id}/status` | services/network_recon_service/api.py |
| POST | `/start_recon` | services/network_recon_service/api.py |


## neuromodulation_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/neuromodulation_service/api.py |
| POST | `/modulate` | services/neuromodulation_service/api.py |
| GET | `/status` | services/neuromodulation_service/api.py |


## nmap_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/nmap_service/main.py |
| POST | `/scan` | services/nmap_service/main.py |
| GET | `/scan_results/{scan_id}` | services/nmap_service/main.py |


## offensive_gateway

| Method | Path | Source |
|--------|------|--------|
| POST | `/execute_offensive_command` | services/offensive_gateway/api.py |
| GET | `/health` | services/offensive_gateway/api.py |
| GET | `/metrics` | services/offensive_gateway/api.py |
| GET | `/offensive_command/{command_id}/results` | services/offensive_gateway/api.py |
| GET | `/offensive_command/{command_id}/status` | services/offensive_gateway/api.py |


## osint_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/osint_service/api.py |
| GET | `/investigation/{investigation_id}/report` | services/osint_service/api.py |
| GET | `/investigation/{investigation_id}/status` | services/osint_service/api.py |
| POST | `/start_investigation` | services/osint_service/api.py |


## predictive_threat_hunting_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/predictive_threat_hunting_service/api.py |
| POST | `/hunt/execute` | services/predictive_threat_hunting_service/api.py |
| POST | `/hunt/recommendations` | services/predictive_threat_hunting_service/api.py |
| POST | `/prediction/ingest_event` | services/predictive_threat_hunting_service/api.py |
| POST | `/prediction/predict` | services/predictive_threat_hunting_service/api.py |
| POST | `/prediction/validate` | services/predictive_threat_hunting_service/api.py |
| GET | `/stats` | services/predictive_threat_hunting_service/api.py |
| GET | `/status` | services/predictive_threat_hunting_service/api.py |
| POST | `/vulnerability/forecast` | services/predictive_threat_hunting_service/api.py |
| POST | `/vulnerability/register` | services/predictive_threat_hunting_service/api.py |
| POST | `/vulnerability/update_trending` | services/predictive_threat_hunting_service/api.py |


## prefrontal_cortex_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/emotional_state` | services/prefrontal_cortex_service/api.py |
| GET | `/health` | services/prefrontal_cortex_service/api.py |
| GET | `/impulse_inhibition_level` | services/prefrontal_cortex_service/api.py |
| POST | `/make_decision` | services/prefrontal_cortex_service/api.py |
| POST | `/strategic_plan` | services/prefrontal_cortex_service/api.py |


## reflex_triage_engine

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/reflex_triage_engine/api.py |
| POST | `/rte/reload-signatures` | services/reflex_triage_engine/api.py |
| POST | `/rte/response/enable-production` | services/reflex_triage_engine/api.py |
| POST | `/rte/scan` | services/reflex_triage_engine/api.py |
| POST | `/rte/scan-file` | services/reflex_triage_engine/api.py |
| GET | `/rte/stats` | services/reflex_triage_engine/api.py |


## rte_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/execute_realtime_command` | services/rte_service/main.py |
| GET | `/health` | services/rte_service/main.py |
| POST | `/ingest_data_stream` | services/rte_service/main.py |


## seriema_graph

| Method | Path | Source |
|--------|------|--------|
| POST | `/framework/store` | services/seriema_graph/api.py |
| DELETE | `/framework/{framework_id}` | services/seriema_graph/api.py |
| GET | `/framework/{framework_id}` | services/seriema_graph/api.py |
| GET | `/framework/{framework_id}/centrality` | services/seriema_graph/api.py |
| GET | `/framework/{framework_id}/circular-arguments` | services/seriema_graph/api.py |
| GET | `/framework/{framework_id}/neighborhood/{argument_id}` | services/seriema_graph/api.py |
| POST | `/framework/{framework_id}/paths` | services/seriema_graph/api.py |
| GET | `/framework/{framework_id}/statistics` | services/seriema_graph/api.py |
| GET | `/health` | services/seriema_graph/api.py |


## sinesp_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_vehicle` | services/sinesp_service/main.py |
| GET | `/health` | services/sinesp_service/main.py |
| POST | `/query_vehicle` | services/sinesp_service/main.py |


## social_eng_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/campaigns/` | services/social_eng_service/main.py |
| POST | `/campaigns/` | services/social_eng_service/main.py |
| GET | `/campaigns/{campaign_id}` | services/social_eng_service/main.py |
| POST | `/campaigns/{campaign_id}/interact` | services/social_eng_service/main.py |
| GET | `/health` | services/social_eng_service/main.py |
| GET | `/targets/` | services/social_eng_service/main.py |
| POST | `/targets/` | services/social_eng_service/main.py |


## somatosensory_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/somatosensory_service/api.py |
| GET | `/mechanoreceptors/status` | services/somatosensory_service/api.py |
| GET | `/nociceptors/status` | services/somatosensory_service/api.py |
| POST | `/touch` | services/somatosensory_service/api.py |


## ssl_monitor_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/ssl_monitor_service/main.py |
| POST | `/monitor` | services/ssl_monitor_service/main.py |
| GET | `/status/{domain_port}` | services/ssl_monitor_service/main.py |


## strategic_planning_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_scenario` | services/strategic_planning_service/api.py |
| GET | `/health` | services/strategic_planning_service/api.py |
| POST | `/set_objective` | services/strategic_planning_service/api.py |
| GET | `/strategic_plan` | services/strategic_planning_service/api.py |


## tataca_ingestion

| Method | Path | Source |
|--------|------|--------|
| GET | `/entities` | services/tataca_ingestion/api.py |
| GET | `/health` | services/tataca_ingestion/api.py |
| POST | `/ingest/trigger` | services/tataca_ingestion/api.py |
| GET | `/jobs` | services/tataca_ingestion/api.py |
| POST | `/jobs` | services/tataca_ingestion/api.py |
| DELETE | `/jobs/{job_id}` | services/tataca_ingestion/api.py |
| GET | `/jobs/{job_id}` | services/tataca_ingestion/api.py |
| GET | `/sources` | services/tataca_ingestion/api.py |
| GET | `/stats` | services/tataca_ingestion/api.py |


## threat_intel_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/threat_intel_service/main.py |
| POST | `/query_threat_intel` | services/threat_intel_service/main.py |
| GET | `/threat_intel_status` | services/threat_intel_service/main.py |


## vestibular_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/vestibular_service/api.py |
| POST | `/ingest_motion_data` | services/vestibular_service/api.py |
| GET | `/orientation` | services/vestibular_service/api.py |


## visual_cortex_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/analyze_image` | services/visual_cortex_service/api.py |
| GET | `/attention_system/status` | services/visual_cortex_service/api.py |
| GET | `/event_driven_vision/status` | services/visual_cortex_service/api.py |
| GET | `/health` | services/visual_cortex_service/api.py |


## vuln_intel_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/correlate_software_vulns` | services/vuln_intel_service/api.py |
| GET | `/health` | services/vuln_intel_service/api.py |
| POST | `/nuclei_scan` | services/vuln_intel_service/api.py |
| POST | `/query_cve` | services/vuln_intel_service/api.py |


## vuln_scanner_service

| Method | Path | Source |
|--------|------|--------|
| GET | `/health` | services/vuln_scanner_service/main.py |
| GET | `/scans/` | services/vuln_scanner_service/main.py |
| POST | `/scans/` | services/vuln_scanner_service/main.py |
| GET | `/scans/{scan_id}` | services/vuln_scanner_service/main.py |
| GET | `/scans/{scan_id}/vulnerabilities` | services/vuln_scanner_service/main.py |


## web_attack_service

| Method | Path | Source |
|--------|------|--------|
| POST | `/api/v1/ai/generate-payloads` | services/web_attack_service/api.py |
| POST | `/api/v1/scan/burp` | services/web_attack_service/api.py |
| POST | `/api/v1/scan/zap` | services/web_attack_service/api.py |
| GET | `/health` | services/web_attack_service/api.py |

