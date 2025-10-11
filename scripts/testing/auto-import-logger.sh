#!/bin/bash
# Auto-add logger import to files that use it but don't import it

FILES=(
  "src/components/cyber/MaximusCyberHub/components/MaximusCore.jsx"
  "src/components/dashboards/DefensiveDashboard/hooks/useDefensiveMetrics.js"
  "src/components/dashboards/OffensiveDashboard/hooks/useOffensiveMetrics.js"
  "src/components/LandingPage/index.jsx"
  "src/components/MapPanel/index.jsx"
  "src/components/maximus/BackgroundEffects.jsx"
  "src/components/maximus/MaximusDashboard.jsx"
  "src/components/maximus/widgets/DistributedTopologyWidget.jsx"
  "src/components/maximus/widgets/HSASWidget.jsx"
  "src/components/maximus/widgets/ImmuneEnhancementWidget.jsx"
  "src/components/maximus/widgets/ImmunisWidget.jsx"
  "src/components/maximus/widgets/MemoryConsolidationWidget.jsx"
  "src/components/maximus/widgets/NeuromodulationWidget.jsx"
  "src/components/maximus/widgets/StrategicPlanningWidget.jsx"
  "src/components/maximus/widgets/ThreatPredictionWidget.jsx"
  "src/components/shared/QueryErrorBoundary.jsx"
  "src/components/shared/WidgetErrorBoundary.jsx"
  "src/config/queryClient.js"
  "src/hooks/useAdminMetrics.js"
  "src/hooks/useMaximusHealth.js"
  "src/hooks/useTheme.js"
  "src/hooks/useWebSocket.js"
)

echo "🔧 AUTO-IMPORT LOGGER FIXER"
echo "============================"
echo ""

FIXED=0

for file in "${FILES[@]}"; do
  if [ ! -f "$file" ]; then
    echo "⚠️  File not found: $file"
    continue
  fi
  
  # Check if logger is used but not imported
  if grep -q "logger\." "$file" && ! grep -q "import.*logger" "$file"; then
    # Get the first line (usually a comment or import)
    first_import_line=$(grep -n "^import" "$file" | head -1 | cut -d: -f1)
    
    if [ -z "$first_import_line" ]; then
      # No imports, add at top after comments
      first_code_line=$(grep -n "^[^/]" "$file" | head -1 | cut -d: -f1)
      if [ -z "$first_code_line" ]; then
        first_code_line=1
      fi
      
      # Insert before first code line
      sed -i "${first_code_line}i import logger from '@/utils/logger';\n" "$file"
    else
      # Add after last import
      last_import_line=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
      sed -i "${last_import_line}a import logger from '@/utils/logger';" "$file"
    fi
    
    echo "✅ Fixed: $file"
    ((FIXED++))
  else
    echo "⏭️  Skipped: $file (already has import or no logger usage)"
  fi
done

echo ""
echo "============================"
echo "📊 SUMMARY:"
echo "  Files fixed: $FIXED"
echo ""
echo "✅ Run npm run lint to verify"
echo "🙏 Em nome de Jesus!"
