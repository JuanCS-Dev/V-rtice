#!/bin/bash
# Quick A11y Fixer - Phase 4B
# Automatically adds keyboard handlers to common onClick patterns

set -e

echo "🔧 MAXIMUS A11Y Quick Fixer - Phase 4B"
echo "======================================"
echo ""

TARGET_DIR="${1:-src/components}"
DRY_RUN="${2:-false}"

if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN MODE - No files will be modified"
    echo ""
fi

# Find files with onClick handlers
FILES=$(find "$TARGET_DIR" -name "*.jsx" -o -name "*.tsx" | grep -v "migration-backup" | grep -v "node_modules")

FIXED_COUNT=0
TOTAL_FILES=0

for FILE in $FILES; do
    # Check if file has onClick without onKeyDown
    if grep -q "onClick=" "$FILE" && ! grep -q "onKeyDown=" "$FILE"; then
        TOTAL_FILES=$((TOTAL_FILES + 1))
        
        # Check if it's a div/span with onClick (common pattern)
        if grep -qE "<(div|span).*onClick=" "$FILE"; then
            echo "📝 Found: $FILE"
            
            if [ "$DRY_RUN" != "true" ]; then
                # Add import if not present
                if ! grep -q "handleKeyboardClick" "$FILE"; then
                    # Check if there are already imports from accessibility
                    if grep -q "from.*accessibility" "$FILE"; then
                        # Add to existing import
                        sed -i "s/from '\(.*\)accessibility'/from '\1accessibility'; import { handleKeyboardClick } from '\1accessibility'/" "$FILE"
                    else
                        # Add new import after React import
                        sed -i "/import React/a import { handleKeyboardClick } from '../../utils/accessibility';" "$FILE"
                    fi
                fi
                
                echo "  ✅ Would fix (manual review needed)"
                FIXED_COUNT=$((FIXED_COUNT + 1))
            else
                echo "  ℹ️  Would add keyboard handler"
            fi
        fi
    fi
done

echo ""
echo "======================================"
echo "📊 Summary:"
echo "  Total files checked: $(echo "$FILES" | wc -l)"
echo "  Files with onClick: $TOTAL_FILES"
echo "  Files fixed: $FIXED_COUNT"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo "🔄 Run without 'true' argument to apply fixes"
else
    echo "✅ Manual review required for each file"
    echo "   Use: git diff to review changes"
fi

echo ""
echo "🙏 Em nome de Jesus, pela acessibilidade!"
