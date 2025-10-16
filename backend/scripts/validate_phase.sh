#!/bin/bash
# Validate a specific phase implementation against architecture requirements
# Usage: ./validate_phase.sh <phase_number>

set -euo pipefail

PHASE=${1:-1}
BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== Validating Phase $PHASE Implementation ==="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# Check ports.yaml exists
if [ ! -f "$BACKEND_DIR/ports.yaml" ]; then
    echo -e "${RED}❌ ports.yaml not found${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ ports.yaml exists${NC}"
fi

# Validate port registry
if command -v python3 &> /dev/null; then
    if python3 "$BACKEND_DIR/scripts/validate_ports.py" &> /dev/null; then
        echo -e "${GREEN}✅ Port registry valid${NC}"
    else
        echo -e "${RED}❌ Port registry validation failed${NC}"
        ((ERRORS++))
    fi
fi

# Check libs structure (Phase 1)
if [ "$PHASE" -ge 1 ]; then
    echo ""
    echo "--- Phase 1: Libraries ---"
    
    REQUIRED_LIBS=(
        "vertice_core"
        "vertice_security"
        "vertice_data"
        "vertice_observability"
    )
    
    for lib in "${REQUIRED_LIBS[@]}"; do
        if [ -d "$BACKEND_DIR/libs/$lib" ]; then
            echo -e "${GREEN}✅ $lib exists${NC}"
            
            # Check for pyproject.toml
            if [ -f "$BACKEND_DIR/libs/$lib/pyproject.toml" ]; then
                echo -e "   ${GREEN}✅ pyproject.toml${NC}"
            else
                echo -e "   ${RED}❌ Missing pyproject.toml${NC}"
                ((ERRORS++))
            fi
            
            # Check for tests
            if [ -d "$BACKEND_DIR/libs/$lib/tests" ]; then
                TEST_COUNT=$(find "$BACKEND_DIR/libs/$lib/tests" -name "test_*.py" | wc -l)
                if [ "$TEST_COUNT" -gt 0 ]; then
                    echo -e "   ${GREEN}✅ $TEST_COUNT test files${NC}"
                else
                    echo -e "   ${YELLOW}⚠️  No test files${NC}"
                    ((WARNINGS++))
                fi
            else
                echo -e "   ${RED}❌ No tests directory${NC}"
                ((ERRORS++))
            fi
            
        else
            echo -e "${RED}❌ $lib missing${NC}"
            ((ERRORS++))
        fi
    done
fi

# Check for mocks/TODOs in production code
echo ""
echo "--- Checking for mocks/TODOs ---"
if find "$BACKEND_DIR" -type f -name "*.py" \
    -not -path "*/tests/*" \
    -not -path "*/.venv/*" \
    -not -path "*/htmlcov/*" \
    -exec grep -l "TODO\|FIXME\|mock\|Mock\|stub\|Stub" {} \; | grep -q .; then
    echo -e "${RED}❌ Found mocks/TODOs in production code${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ No mocks/TODOs in production code${NC}"
fi

# Summary
echo ""
echo "=== Validation Summary ==="
echo -e "Errors: ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"

if [ "$ERRORS" -gt 0 ]; then
    echo ""
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}"
    exit 0
fi
