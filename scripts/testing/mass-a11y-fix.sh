#!/bin/bash
# Mass A11y Fixer - Phase 4C
# Fixes common accessibility patterns in bulk

set -e

echo "🚀 MAXIMUS A11Y MASS FIXER - Phase 4C"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FIXED_COUNT=0
COMPONENT_DIR="src/components"

# Get list of files with jsx-a11y issues
echo "📋 Analyzing files with accessibility issues..."
FILES_WITH_ISSUES=$(npm run lint 2>&1 | grep "\.jsx:" | grep -v "migration-backup" | awk -F: '{print $1}' | sort | uniq)

echo -e "${BLUE}Found $(echo "$FILES_WITH_ISSUES" | wc -l) files with issues${NC}"
echo ""

for FILE in $FILES_WITH_ISSUES; do
    if [ ! -f "$FILE" ]; then
        continue
    fi
    
    echo "🔍 Checking: $FILE"
    
    # Check if file needs handleKeyboardClick import
    NEEDS_IMPORT=false
    
    # Pattern 1: div/span with onClick but no onKeyDown
    if grep -q "onClick=" "$FILE" && ! grep -q "onKeyDown=" "$FILE"; then
        if grep -qE "<(div|span).*onClick=" "$FILE"; then
            echo -e "  ${YELLOW}⚠️  Found onClick without keyboard handler${NC}"
            NEEDS_IMPORT=true
        fi
    fi
    
    # Add import if needed and not present
    if [ "$NEEDS_IMPORT" = true ] && ! grep -q "handleKeyboardClick" "$FILE"; then
        # Check if there's already an import from accessibility
        if grep -q "from.*utils/accessibility" "$FILE"; then
            echo -e "  ${GREEN}✓ Import already exists${NC}"
        else
            # Add import after React import
            if grep -q "^import React" "$FILE"; then
                # Get relative path depth
                DEPTH=$(echo "$FILE" | grep -o "/" | wc -l)
                RELATIVE_PATH=""
                for ((i=2; i<DEPTH; i++)); do
                    RELATIVE_PATH="../$RELATIVE_PATH"
                done
                RELATIVE_PATH="${RELATIVE_PATH}utils/accessibility"
                
                # Add import
                sed -i "/^import React/a import { handleKeyboardClick } from '$RELATIVE_PATH';" "$FILE"
                echo -e "  ${GREEN}✅ Added handleKeyboardClick import${NC}"
                FIXED_COUNT=$((FIXED_COUNT + 1))
            fi
        fi
    fi
    
    # Pattern 2: Labels without htmlFor
    if grep -q "<label[^>]*>[^<]*</label>" "$FILE"; then
        LABEL_COUNT=$(grep -c "<label" "$FILE" || echo "0")
        HTMLFOR_COUNT=$(grep -c "htmlFor=" "$FILE" || echo "0")
        
        if [ "$LABEL_COUNT" -gt "$HTMLFOR_COUNT" ]; then
            echo -e "  ${YELLOW}⚠️  Found $((LABEL_COUNT - HTMLFOR_COUNT)) labels without htmlFor${NC}"
            echo -e "  ${BLUE}ℹ️  Manual fix required${NC}"
        fi
    fi
    
    echo ""
done

echo "======================================="
echo "📊 Summary:"
echo -e "  ${GREEN}Auto-fixed: $FIXED_COUNT files${NC}"
echo -e "  ${YELLOW}Manual review needed: See warnings above${NC}"
echo ""
echo "🔄 Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Add keyboard handlers manually where needed"
echo "  3. Fix label associations"
echo "  4. Run: npm run lint"
echo "  5. Test: npm run build"
echo ""
echo "🙏 Em nome de Jesus, pela acessibilidade total!"
