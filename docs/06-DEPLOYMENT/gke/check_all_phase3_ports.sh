#!/bin/bash
cd /home/juan/vertice-dev/backend/services
for svc in offensive_orchestrator_service offensive_gateway offensive_tools_service web_attack_service malware_analysis_service c2_orchestration_service social_eng_service vuln_scanner_service reactive_fabric_core reactive_fabric_analysis reflex_triage_engine homeostatic_regulation bas_service rte_service hsas_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
