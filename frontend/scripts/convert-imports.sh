#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Convert Relative Imports to Absolute Imports (@/)
# ═══════════════════════════════════════════════════════════════════════════
# Governed by: Constituição Vértice v2.5 - ADR-001 (Step 4)
#
# This script converts relative imports (../../) to absolute imports (@/)
# to improve maintainability and refactoring safety.
#
# Usage: ./scripts/convert-imports.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🔄 Converting relative imports to absolute imports..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
TOTAL_FILES=0
CONVERTED_FILES=0

# Find all JS/JSX files in src/
while IFS= read -r file; do
  TOTAL_FILES=$((TOTAL_FILES + 1))
  CHANGED=0

  # Get directory depth of current file relative to src/
  FILE_DIR=$(dirname "$file")
  REL_PATH="${FILE_DIR#src/}"

  # Calculate how many levels deep we are
  if [ "$REL_PATH" = "src/" ] || [ "$REL_PATH" = "" ]; then
    DEPTH=0
  else
    DEPTH=$(echo "$REL_PATH" | tr -cd '/' | wc -c)
  fi

  # Patterns to replace (from most specific to least)
  # Example: ../../../api/client → @/api/client

  # Process the file
  TEMP_FILE=$(mktemp)
  cp "$file" "$TEMP_FILE"

  # Replace patterns
  # Note: This is a simplified version. A full implementation would need
  # to parse the import depth correctly for each file.

  sed -i "s|from '\.\./\.\./\.\./api/|from '@/api/|g" "$file"
  sed -i "s|from '\.\./\.\./api/|from '@/api/|g" "$file"
  sed -i "s|from '\.\./api/|from '@/api/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./components/|from '@/components/|g" "$file"
  sed -i "s|from '\.\./\.\./components/|from '@/components/|g" "$file"
  sed -i "s|from '\.\./components/|from '@/components/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./config/|from '@/config/|g" "$file"
  sed -i "s|from '\.\./\.\./config/|from '@/config/|g" "$file"
  sed -i "s|from '\.\./config/|from '@/config/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./utils/|from '@/utils/|g" "$file"
  sed -i "s|from '\.\./\.\./utils/|from '@/utils/|g" "$file"
  sed -i "s|from '\.\./utils/|from '@/utils/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./hooks/|from '@/hooks/|g" "$file"
  sed -i "s|from '\.\./\.\./hooks/|from '@/hooks/|g" "$file"
  sed -i "s|from '\.\./hooks/|from '@/hooks/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./contexts/|from '@/contexts/|g" "$file"
  sed -i "s|from '\.\./\.\./contexts/|from '@/contexts/|g" "$file"
  sed -i "s|from '\.\./contexts/|from '@/contexts/|g" "$file"

  sed -i "s|from '\.\./\.\./\.\./stores/|from '@/stores/|g" "$file"
  sed -i "s|from '\.\./\.\./stores/|from '@/stores/|g" "$file"
  sed -i "s|from '\.\./stores/|from '@/stores/|g" "$file"

  # Check if file changed
  if ! cmp -s "$file" "$TEMP_FILE"; then
    CHANGED=1
    CONVERTED_FILES=$((CONVERTED_FILES + 1))
    echo -e "${GREEN}✓${NC} $file"
  fi

  rm "$TEMP_FILE"

done < <(find src -name "*.js" -o -name "*.jsx" | grep -v node_modules | grep -v __tests__)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Conversion complete!${NC}"
echo ""
echo "  Total files scanned: $TOTAL_FILES"
echo "  Files converted: $CONVERTED_FILES"
echo ""
echo "Run 'npm run build' to verify everything still works."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
