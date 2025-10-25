#!/bin/bash
cd /home/juan/vertice-dev/backend/services
echo "=== HCL SERVICES (9) ==="
for svc in hcl_analyzer_service hcl_planner_service hcl_executor_service hcl_kb_service hcl_monitor_service strategic_planning_service tactical_decision_service policy_engine_service hcl_orchestrator_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
echo ""
echo "=== SUPPORT SERVICES (10) ==="
for svc in logging_service metrics_service alerting_service backup_service config_service discovery_service load_balancer_service proxy_service queue_service storage_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
