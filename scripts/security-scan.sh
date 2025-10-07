#!/bin/bash
# ============================================================================
# Vértice Platform - Security Scanning Script
# ============================================================================
# Runs comprehensive security scans on the codebase:
# 1. Bandit - Python code security scanner
# 2. Safety - Dependency vulnerability scanner
# 3. pip-audit - Python package vulnerability audit
#
# Usage:
#   ./scripts/security-scan.sh [--report]
#
# Options:
#   --report    Generate HTML/JSON reports (saved to reports/)
#   --strict    Exit with error if any issues found
#   --help      Show this help message
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPORT_DIR="$PROJECT_ROOT/reports/security"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Parse arguments
GENERATE_REPORT=false
STRICT_MODE=false

for arg in "$@"; do
    case $arg in
        --report)
            GENERATE_REPORT=true
            shift
            ;;
        --strict)
            STRICT_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--report] [--strict]"
            echo ""
            echo "Options:"
            echo "  --report    Generate HTML/JSON reports"
            echo "  --strict    Exit with error if any issues found"
            echo "  --help      Show this help message"
            exit 0
            ;;
    esac
done

# Create report directory if needed
if [ "$GENERATE_REPORT" = true ]; then
    mkdir -p "$REPORT_DIR"
fi

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Vértice Platform - Security Scanning${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# 1. BANDIT - Python Code Security Scanner
# ============================================================================
echo -e "${YELLOW}[1/3] Running Bandit (Python code security scanner)...${NC}"
echo ""

BANDIT_EXIT_CODE=0

if [ "$GENERATE_REPORT" = true ]; then
    echo "  Generating reports to: $REPORT_DIR/bandit_*"

    # JSON report
    bandit -r backend/ -c .bandit -f json -o "$REPORT_DIR/bandit_${TIMESTAMP}.json" --quiet || BANDIT_EXIT_CODE=$?

    # HTML report
    bandit -r backend/ -c .bandit -f html -o "$REPORT_DIR/bandit_${TIMESTAMP}.html" --quiet || BANDIT_EXIT_CODE=$?

    # TXT report
    bandit -r backend/ -c .bandit -f txt -o "$REPORT_DIR/bandit_${TIMESTAMP}.txt" || BANDIT_EXIT_CODE=$?

    echo -e "  ${GREEN}✓${NC} Bandit reports generated"
else
    # Screen output only
    bandit -r backend/ -c .bandit || BANDIT_EXIT_CODE=$?
fi

if [ $BANDIT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Bandit: No security issues found${NC}"
else
    echo -e "${YELLOW}⚠ Bandit: Found security issues (exit code: $BANDIT_EXIT_CODE)${NC}"
fi
echo ""

# ============================================================================
# 2. SAFETY - Dependency Vulnerability Scanner
# ============================================================================
echo -e "${YELLOW}[2/3] Running Safety (dependency vulnerability scanner)...${NC}"
echo ""

SAFETY_EXIT_CODE=0

# Note: Safety 3.x requires API key for full scans
# Free tier: safety scan --key="" (limited)
# Authenticated: safety scan (requires SAFETY_API_KEY env var)

if [ "$GENERATE_REPORT" = true ]; then
    echo "  Generating reports to: $REPORT_DIR/safety_*"

    # JSON report
    safety check --json --output "$REPORT_DIR/safety_${TIMESTAMP}.json" || SAFETY_EXIT_CODE=$?

    # Text report
    safety check --output text > "$REPORT_DIR/safety_${TIMESTAMP}.txt" || SAFETY_EXIT_CODE=$?

    echo -e "  ${GREEN}✓${NC} Safety reports generated"
else
    # Screen output only
    safety check || SAFETY_EXIT_CODE=$?
fi

if [ $SAFETY_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Safety: No known vulnerabilities found${NC}"
else
    echo -e "${YELLOW}⚠ Safety: Found vulnerabilities (exit code: $SAFETY_EXIT_CODE)${NC}"
fi
echo ""

# ============================================================================
# 3. PIP-AUDIT - Python Package Vulnerability Audit
# ============================================================================
echo -e "${YELLOW}[3/3] Running pip-audit (package vulnerability audit)...${NC}"
echo ""

PIP_AUDIT_EXIT_CODE=0

if [ "$GENERATE_REPORT" = true ]; then
    echo "  Generating reports to: $REPORT_DIR/pip-audit_*"

    # JSON report
    pip-audit --format json --output "$REPORT_DIR/pip-audit_${TIMESTAMP}.json" || PIP_AUDIT_EXIT_CODE=$?

    # Markdown report
    pip-audit --format markdown > "$REPORT_DIR/pip-audit_${TIMESTAMP}.md" || PIP_AUDIT_EXIT_CODE=$?

    echo -e "  ${GREEN}✓${NC} pip-audit reports generated"
else
    # Screen output only
    pip-audit || PIP_AUDIT_EXIT_CODE=$?
fi

if [ $PIP_AUDIT_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ pip-audit: No vulnerabilities found${NC}"
else
    echo -e "${YELLOW}⚠ pip-audit: Found vulnerabilities (exit code: $PIP_AUDIT_EXIT_CODE)${NC}"
fi
echo ""

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Security Scan Summary${NC}"
echo -e "${BLUE}============================================================================${NC}"

TOTAL_ISSUES=0

if [ $BANDIT_EXIT_CODE -ne 0 ]; then
    echo -e "${YELLOW}⚠ Bandit:     Issues found${NC}"
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
else
    echo -e "${GREEN}✓ Bandit:     Clean${NC}"
fi

if [ $SAFETY_EXIT_CODE -ne 0 ]; then
    echo -e "${YELLOW}⚠ Safety:     Vulnerabilities found${NC}"
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
else
    echo -e "${GREEN}✓ Safety:     Clean${NC}"
fi

if [ $PIP_AUDIT_EXIT_CODE -ne 0 ]; then
    echo -e "${YELLOW}⚠ pip-audit:  Vulnerabilities found${NC}"
    TOTAL_ISSUES=$((TOTAL_ISSUES + 1))
else
    echo -e "${GREEN}✓ pip-audit:  Clean${NC}"
fi

echo ""

if [ "$GENERATE_REPORT" = true ]; then
    echo -e "${BLUE}Reports saved to: $REPORT_DIR/${NC}"
    echo ""
fi

if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All security scans passed!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Found issues in $TOTAL_ISSUES scanner(s)${NC}"
    echo -e "${YELLOW}  Review the output above for details.${NC}"

    if [ "$STRICT_MODE" = true ]; then
        echo -e "${RED}  Exiting with error (strict mode enabled)${NC}"
        exit 1
    else
        echo -e "${YELLOW}  Exiting with warning (use --strict to fail on issues)${NC}"
        exit 0
    fi
fi
