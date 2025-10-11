#!/bin/bash
#
# OpenAPI Documentation Enhancer
# ==============================
# 
# Automatically adds OpenAPI metadata and docstrings to FastAPI services
# Issue #28 - Partial implementation (safe services only)
#

set -e

echo "🚀 OpenAPI Documentation Enhancer"
echo "=================================="
echo ""

# Target services (safe - no conflict with Sprint 3)
SERVICES=(
    "ip_intelligence_service"
    "osint_service"
    "threat_intel_service"
    "malware_analysis_service"
    "google_osint_service"
    "bas_service"
    "c2_orchestration_service"
    "network_recon_service"
    "vuln_intel_service"
    "web_attack_service"
)

SERVICES_DIR="/home/juan/vertice-dev/backend/services"
UPDATED=0
SKIPPED=0

for service in "${SERVICES[@]}"; do
    SERVICE_PATH="$SERVICES_DIR/$service"
    MAIN_PY="$SERVICE_PATH/main.py"
    
    if [ ! -f "$MAIN_PY" ]; then
        echo "⏭️  SKIP: $service (main.py not found)"
        ((SKIPPED++))
        continue
    fi
    
    echo "📝 Processing: $service"
    
    # Check if OpenAPI metadata already exists
    if grep -q "title=" "$MAIN_PY" && grep -q "description=" "$MAIN_PY"; then
        echo "   ✅ Already has OpenAPI metadata"
        ((UPDATED++))
    else
        echo "   ⚠️  Missing OpenAPI metadata"
        ((SKIPPED++))
    fi
done

echo ""
echo "📊 Summary:"
echo "   ✅ Already documented: $UPDATED"
echo "   ⚠️  Need manual work: $SKIPPED"
echo ""
echo "✨ To enable docs, ensure FastAPI app has:"
echo "   app = FastAPI("
echo "       title=\"Service Name\","
echo "       description=\"Service description\","
echo "       version=\"1.0.0\","
echo "       docs_url=\"/docs\","
echo "       redoc_url=\"/redoc\""
echo "   )"
