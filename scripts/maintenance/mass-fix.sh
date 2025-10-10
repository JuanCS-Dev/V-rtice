#!/bin/bash
set -e

echo "🔧 MASS FIX - CATEGORIA B (Missing Dependencies)"
echo "================================================"

# Categoria B: Add missing deps
echo ""
echo "1. hcl-analyzer (numpy)"
cd /home/juan/vertice-dev/backend/services/hcl_analyzer_service
if [ -f "requirements.txt" ]; then
  grep -q "numpy" requirements.txt || echo "numpy>=1.24.0" >> requirements.txt
  echo "✅ hcl-analyzer: numpy added"
fi

echo ""
echo "2. hpc-service (numpy)"
cd /home/juan/vertice-dev/backend/services/hpc_service
if [ -f "requirements.txt" ]; then
  grep -q "numpy" requirements.txt || echo "numpy>=1.24.0" >> requirements.txt
  echo "✅ hpc-service: numpy added"
fi

echo ""
echo "3. rte-service (numpy)"
cd /home/juan/vertice-dev/backend/services/rte_service
if [ -f "requirements.txt" ]; then
  grep -q "numpy" requirements.txt || echo "numpy>=1.24.0" >> requirements.txt
  echo "✅ rte-service: numpy added"
fi

echo ""
echo "4. vertice-ip-intel (pydantic_settings)"
cd /home/juan/vertice-dev/backend/services/ip_intel_service
if [ -f "requirements.txt" ]; then
  grep -q "pydantic-settings" requirements.txt || echo "pydantic-settings>=2.0.0" >> requirements.txt
  echo "✅ ip-intel: pydantic-settings added"
fi

echo ""
echo "5. vertice-narrative-filter (sqlalchemy)"
cd /home/juan/vertice-dev/backend/services/narrative_filter_service
if [ -f "requirements.txt" ]; then
  grep -q "sqlalchemy" requirements.txt || echo "sqlalchemy>=2.0.0" >> requirements.txt
  echo "✅ narrative-filter: sqlalchemy added"
fi

echo ""
echo "✅ Categoria B fixes completos!"
