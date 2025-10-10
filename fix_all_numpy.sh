#!/bin/bash
echo "🔧 Adding numpy to ALL services that need it..."

SERVICES=(
  "narrative_analysis_service"
  "predictive_threat_hunting_service"
  "memory_consolidation_service"
  "adaptive_immunity_service"
  "autonomous_investigation_service"
)

cd /home/juan/vertice-dev/backend/services

for svc in "${SERVICES[@]}"; do
  if [ -f "$svc/requirements.txt" ]; then
    if ! grep -q "numpy" "$svc/requirements.txt"; then
      echo "numpy>=1.24.0" >> "$svc/requirements.txt"
      echo "✅ $svc: numpy added"
    fi
  fi
done

echo ""
echo "✅ Numpy added to all services!"
