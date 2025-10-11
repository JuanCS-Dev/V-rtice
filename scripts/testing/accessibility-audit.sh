#!/bin/bash
# Accessibility Audit Script for MAXIMUS Vértice Frontend
# Phase 4: Comprehensive accessibility validation

set -e

echo "🔍 MAXIMUS ACCESSIBILITY AUDIT - Phase 4"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
WARNINGS=0
ERRORS=0

echo "📋 Running Accessibility Checks..."
echo ""

# 1. ESLint Accessibility Rules
echo "1️⃣  ESLint JSX-A11Y Rules..."
if npm run lint 2>&1 | tee /tmp/eslint-output.txt | grep -q "✔"; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ ESLint a11y rules passed${NC}"
else
    # Count warnings and errors
    LINT_WARNINGS=$(grep -c "warning" /tmp/eslint-output.txt 2>/dev/null || echo "0")
    LINT_ERRORS=$(grep -c "error" /tmp/eslint-output.txt 2>/dev/null || echo "0")
    WARNINGS=$((WARNINGS + LINT_WARNINGS))
    ERRORS=$((ERRORS + LINT_ERRORS))
    
    if [ "$LINT_ERRORS" -gt 0 ]; then
        echo -e "${RED}✗ ESLint found $LINT_ERRORS errors${NC}"
    elif [ "$LINT_WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}⚠ ESLint found $LINT_WARNINGS warnings${NC}"
    fi
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 2. Check for ARIA attributes
echo "2️⃣  Checking ARIA Implementation..."
ARIA_COUNT=$(find src/components -type f \( -name "*.jsx" -o -name "*.tsx" \) -exec grep -l "aria-" {} \; | wc -l)
COMPONENT_COUNT=$(find src/components -type f \( -name "*.jsx" -o -name "*.tsx" \) | wc -l)
ARIA_PERCENTAGE=$((ARIA_COUNT * 100 / COMPONENT_COUNT))

if [ "$ARIA_PERCENTAGE" -gt 30 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Good ARIA coverage: $ARIA_COUNT/$COMPONENT_COUNT components ($ARIA_PERCENTAGE%)${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ Low ARIA coverage: $ARIA_COUNT/$COMPONENT_COUNT components ($ARIA_PERCENTAGE%)${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 3. Check for semantic HTML
echo "3️⃣  Checking Semantic HTML Usage..."
SEMANTIC_TAGS=(nav header main footer article section aside)
SEMANTIC_FOUND=0
for tag in "${SEMANTIC_TAGS[@]}"; do
    if grep -rq "<$tag" src/components/ 2>/dev/null; then
        SEMANTIC_FOUND=$((SEMANTIC_FOUND + 1))
    fi
done

if [ "$SEMANTIC_FOUND" -ge 5 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Good semantic HTML usage: $SEMANTIC_FOUND/7 tags found${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ Limited semantic HTML: $SEMANTIC_FOUND/7 tags found${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 4. Check for alt text on images
echo "4️⃣  Checking Image Alt Text..."
IMG_TAGS=$(grep -r "<img" src/components/ 2>/dev/null | wc -l)
IMG_WITH_ALT=$(grep -r "<img.*alt=" src/components/ 2>/dev/null | wc -l)

if [ "$IMG_TAGS" -eq 0 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ No img tags found (using SVG/components)${NC}"
elif [ "$IMG_TAGS" -eq "$IMG_WITH_ALT" ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ All images have alt text: $IMG_WITH_ALT/$IMG_TAGS${NC}"
else
    MISSING=$((IMG_TAGS - IMG_WITH_ALT))
    ERRORS=$((ERRORS + MISSING))
    echo -e "${RED}✗ Missing alt text: $MISSING images without alt${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 5. Check for keyboard navigation support
echo "5️⃣  Checking Keyboard Navigation Support..."
KEYBOARD_PATTERNS=("onKeyDown" "onKeyPress" "onKeyUp" "tabIndex")
KEYBOARD_FOUND=0
for pattern in "${KEYBOARD_PATTERNS[@]}"; do
    if grep -rq "$pattern" src/components/ 2>/dev/null; then
        KEYBOARD_FOUND=$((KEYBOARD_FOUND + 1))
    fi
done

if [ "$KEYBOARD_FOUND" -ge 2 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Keyboard navigation implemented: $KEYBOARD_FOUND/4 patterns found${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ Limited keyboard support: $KEYBOARD_FOUND/4 patterns found${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 6. Check for focus management
echo "6️⃣  Checking Focus Management..."
FOCUS_PATTERNS=("focus()" "blur()" "autoFocus" ":focus" "focus-visible")
FOCUS_FOUND=0
for pattern in "${FOCUS_PATTERNS[@]}"; do
    if grep -rq "$pattern" src/ 2>/dev/null; then
        FOCUS_FOUND=$((FOCUS_FOUND + 1))
    fi
done

if [ "$FOCUS_FOUND" -ge 3 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Focus management present: $FOCUS_FOUND/5 patterns found${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ Limited focus management: $FOCUS_FOUND/5 patterns found${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 7. Check for prefers-reduced-motion
echo "7️⃣  Checking Reduced Motion Support..."
if grep -rq "prefers-reduced-motion" src/styles/ 2>/dev/null; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ prefers-reduced-motion media query found${NC}"
else
    ERRORS=$((ERRORS + 1))
    echo -e "${RED}✗ Missing prefers-reduced-motion support${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 8. Check for color contrast (basic)
echo "8️⃣  Checking Color Usage..."
if [ -f "src/styles/tokens/colors.css" ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Centralized color system found${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ No centralized color tokens found${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 9. Check for skip links
echo "9️⃣  Checking Skip Links..."
if grep -rq "SkipLink" src/ 2>/dev/null; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Skip link component found${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ No skip link found${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# 10. Check for form labels
echo "🔟 Checking Form Labels..."
LABEL_COUNT=$(grep -r "<label" src/components/ 2>/dev/null | wc -l)
INPUT_COUNT=$(grep -r "<input" src/components/ 2>/dev/null | wc -l)

if [ "$INPUT_COUNT" -eq 0 ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ No raw inputs (using controlled components)${NC}"
elif [ "$LABEL_COUNT" -ge "$((INPUT_COUNT * 70 / 100))" ]; then
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
    echo -e "${GREEN}✓ Good label coverage: $LABEL_COUNT labels for $INPUT_COUNT inputs${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ Some inputs may lack labels: $LABEL_COUNT labels for $INPUT_COUNT inputs${NC}"
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
echo ""

# Summary
echo "=========================================="
echo "📊 AUDIT SUMMARY"
echo "=========================================="
echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
echo -e "${RED}Errors: $ERRORS${NC}"
echo ""

# Calculate score
SCORE=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))

if [ "$SCORE" -ge 90 ]; then
    echo -e "Score: ${GREEN}$SCORE/100 ⭐⭐⭐${NC}"
    echo -e "${GREEN}✓ EXCELLENT accessibility compliance!${NC}"
elif [ "$SCORE" -ge 70 ]; then
    echo -e "Score: ${YELLOW}$SCORE/100 ⭐⭐${NC}"
    echo -e "${YELLOW}⚠ GOOD, but improvements recommended${NC}"
else
    echo -e "Score: ${RED}$SCORE/100 ⭐${NC}"
    echo -e "${RED}✗ NEEDS IMPROVEMENT${NC}"
fi
echo ""

# Recommendations
if [ "$WARNINGS" -gt 0 ] || [ "$ERRORS" -gt 0 ]; then
    echo "📝 RECOMMENDATIONS:"
    echo "  • Run 'npm run lint' for detailed issues"
    echo "  • Test with screen readers (NVDA/JAWS)"
    echo "  • Validate with browser DevTools Lighthouse"
    echo "  • Test keyboard navigation manually"
    echo "  • Check color contrast ratios"
    echo ""
fi

echo "🙏 Em nome de Jesus, pela excelência e inclusão!"

# Exit with appropriate code
if [ "$ERRORS" -gt 0 ]; then
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    exit 0
else
    exit 0
fi
