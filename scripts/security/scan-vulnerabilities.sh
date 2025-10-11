#!/bin/bash
#
# Dependency Vulnerability Scanner
# =================================
#
# Scans Python and NPM dependencies for known vulnerabilities
# Issue #40 - Dependency vulnerability scanning
#
# Usage:
#   ./scan-vulnerabilities.sh [--python|--npm|--all] [--fix]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/violation_reports/dependencies"

# Options
SCAN_PYTHON=false
SCAN_NPM=false
AUTO_FIX=false

# Parse arguments
if [ $# -eq 0 ]; then
    SCAN_PYTHON=true
    SCAN_NPM=true
else
    while [[ $# -gt 0 ]]; do
        case $1 in
            --python)
                SCAN_PYTHON=true
                shift
                ;;
            --npm)
                SCAN_NPM=true
                shift
                ;;
            --all)
                SCAN_PYTHON=true
                SCAN_NPM=true
                shift
                ;;
            --fix)
                AUTO_FIX=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                echo "Usage: $0 [--python|--npm|--all] [--fix]"
                exit 1
                ;;
        esac
    done
fi

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${GREEN}🔒 Dependency Vulnerability Scanner${NC}"
echo "===================================="
echo ""

# ============================================================================
# PYTHON DEPENDENCIES (Safety)
# ============================================================================

if [ "$SCAN_PYTHON" = true ]; then
    echo -e "${YELLOW}🐍 Scanning Python dependencies...${NC}"
    
    # Check if safety is installed
    if ! command -v safety &> /dev/null; then
        echo "Installing safety..."
        pip install safety
    fi
    
    cd "$PROJECT_ROOT"
    
    # Run safety check
    PYTHON_REPORT="$REPORTS_DIR/python-vulnerabilities-$TIMESTAMP.json"
    
    if safety check --json --output "$PYTHON_REPORT" 2>/dev/null; then
        echo -e "${GREEN}✅ No vulnerabilities found in Python dependencies!${NC}"
    else
        VULN_COUNT=$(jq '. | length' "$PYTHON_REPORT" 2>/dev/null || echo "0")
        
        if [ "$VULN_COUNT" -gt 0 ]; then
            echo -e "${RED}❌ Found $VULN_COUNT vulnerabilities in Python dependencies!${NC}"
            echo ""
            echo "Critical vulnerabilities:"
            jq -r '.[] | "  - \(.package) \(.installed_version): \(.vulnerability)"' "$PYTHON_REPORT"
            echo ""
            echo -e "Full report: $PYTHON_REPORT"
            
            if [ "$AUTO_FIX" = true ]; then
                echo ""
                echo "Attempting to upgrade vulnerable packages..."
                jq -r '.[] | .package' "$PYTHON_REPORT" | xargs -I {} pip install --upgrade {}
            fi
        else
            echo -e "${GREEN}✅ No vulnerabilities found!${NC}"
        fi
    fi
    
    echo ""
fi

# ============================================================================
# NPM DEPENDENCIES (npm audit)
# ============================================================================

if [ "$SCAN_NPM" = true ]; then
    echo -e "${YELLOW}📦 Scanning NPM dependencies...${NC}"
    
    FRONTEND_DIR="$PROJECT_ROOT/frontend"
    
    if [ -d "$FRONTEND_DIR" ] && [ -f "$FRONTEND_DIR/package.json" ]; then
        cd "$FRONTEND_DIR"
        
        NPM_REPORT="$REPORTS_DIR/npm-vulnerabilities-$TIMESTAMP.json"
        
        # Run npm audit
        if npm audit --json > "$NPM_REPORT" 2>/dev/null; then
            echo -e "${GREEN}✅ No vulnerabilities found in NPM dependencies!${NC}"
        else
            # Parse results
            CRITICAL=$(jq '.metadata.vulnerabilities.critical // 0' "$NPM_REPORT")
            HIGH=$(jq '.metadata.vulnerabilities.high // 0' "$NPM_REPORT")
            MODERATE=$(jq '.metadata.vulnerabilities.moderate // 0' "$NPM_REPORT")
            LOW=$(jq '.metadata.vulnerabilities.low // 0' "$NPM_REPORT")
            TOTAL=$((CRITICAL + HIGH + MODERATE + LOW))
            
            echo -e "${RED}❌ Found $TOTAL vulnerabilities in NPM dependencies!${NC}"
            echo ""
            echo "Breakdown:"
            echo "  🔴 Critical: $CRITICAL"
            echo "  🟠 High: $HIGH"
            echo "  🟡 Moderate: $MODERATE"
            echo "  🟢 Low: $LOW"
            echo ""
            echo -e "Full report: $NPM_REPORT"
            
            if [ "$AUTO_FIX" = true ]; then
                echo ""
                echo "Attempting to fix vulnerabilities..."
                npm audit fix
                echo ""
                echo "If issues remain, run: npm audit fix --force"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Frontend directory not found or no package.json${NC}"
    fi
    
    echo ""
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo "===================================="
echo -e "${GREEN}✅ Vulnerability scan complete!${NC}"
echo ""
echo "Reports saved to: $REPORTS_DIR"
echo ""
echo "Recommendations:"
echo "  1. Review all critical/high vulnerabilities"
echo "  2. Update dependencies: pip install --upgrade <package>"
echo "  3. For NPM: npm audit fix"
echo "  4. Check for breaking changes before deploying"
echo ""

if [ "$AUTO_FIX" = false ]; then
    echo "To automatically fix issues, run with --fix flag"
fi
