#!/bin/bash
echo "🔧 BUILDING CATEGORIA A (11 services with main.py fix)..."

SERVICES=(
  "adaptive_immunity_service"
  "autonomous_investigation_service"
  "bas_service"
  "c2_orchestration_service"
  "immunis_treg_service"
  "memory_consolidation_service"
  "narrative_analysis_service"
  "offensive_gateway"
  "predictive_threat_hunting_service"
)

# Build em batches de 3 para não sobrecarregar
for i in $(seq 0 2 $((${#SERVICES[@]}-1))); do
  batch="${SERVICES[@]:$i:3}"
  echo ""
  echo "Building batch: $batch"
  docker compose build $batch 2>&1 | grep -E "Building|Successfully|ERROR|CACHED" | tail -5
done

echo ""
echo "✅ Categoria A build completo!"
