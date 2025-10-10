#!/bin/bash
# Create main.py for services that have api.py but Dockerfile calls main:app

SERVICES=(
  "adaptive_immunity_service"
  "autonomous_investigation_service"
  "bas_service"
  "c2_orchestration_service"
  "immunis_treg_service"
  "maximus_eureka_service"
  "maximus_oraculo_service"
  "memory_consolidation_service"
  "narrative_analysis_service"
  "offensive_gateway"
  "predictive_threat_hunting_service"
)

cd /home/juan/vertice-dev/backend/services

for svc in "${SERVICES[@]}"; do
  if [ -d "$svc" ] && [ -f "$svc/api.py" ] && [ ! -f "$svc/main.py" ]; then
    echo "Creating main.py for $svc"
    cat > "$svc/main.py" << 'PYEOF'
"""Main entry point - imports app from api module."""
from api import app

__all__ = ["app"]
PYEOF
    echo "✅ $svc/main.py created"
  fi
done

echo ""
echo "✅ All main.py files created!"
