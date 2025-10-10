#!/bin/bash
echo "🔍 PHASE 1: DIAGNÓSTICO MASSIVO - 16 SERVIÇOS"
echo "=============================================="
echo ""

SERVICES=(
  "adaptive-immunity-service"
  "autonomous-investigation-service"
  "bas_service"
  "c2_orchestration_service"
  "hcl-analyzer"
  "hpc-service"
  "immunis-treg-service"
  "maximus-eureka"
  "maximus-oraculo"
  "memory-consolidation-service"
  "narrative-analysis-service"
  "offensive_gateway"
  "predictive-threat-hunting-service"
  "rte-service"
  "vertice-ip-intel"
  "vertice-narrative-filter"
)

> errors_summary.txt

for svc in "${SERVICES[@]}"; do
  echo "Analyzing: $svc"
  error=$(docker logs $svc --tail=10 2>&1 | grep -E "ModuleNotFoundError|ImportError|Error" | head -3)
  if [[ ! -z "$error" ]]; then
    echo "=== $svc ===" >> errors_summary.txt
    echo "$error" >> errors_summary.txt
    echo "" >> errors_summary.txt
  fi
done

echo ""
echo "✅ Diagnóstico completo! Ver errors_summary.txt"
cat errors_summary.txt
