#!/bin/bash
cd /home/juan/vertice-dev/backend/services
echo "=== WARGAMING SERVICES ==="
for svc in wargaming_engine_service wargaming_scenario_service wargaming_simulator_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
echo ""
echo "=== HUB-AI SERVICES ==="
for svc in hub_ai_service hub_ai_orchestrator_service hub_ai_interface_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
echo ""
echo "=== OTHER PHASE 6 CANDIDATES ==="
for svc in simulation_service orchestration_service ml_model_service; do
  if [ -f "$svc/Dockerfile" ]; then
    port=$(grep -E "EXPOSE|--port" "$svc/Dockerfile" | grep -o "[0-9]\{4,5\}" | head -1)
    echo "$svc: ${port:-NOT_FOUND}"
  else
    echo "$svc: NO_DOCKERFILE"
  fi
done
