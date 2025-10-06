#!/bin/bash
# CI/CD Validation Script
#
# This script runs all dependency validation checks in CI/CD pipelines:
# 1. Dependency drift detection
# 2. CVE/security auditing
# 3. Docker build determinism validation
#
# Following Doutrina Vértice - Article III: Confiança Zero

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║         CI/CD Dependency Validation Suite        ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""
echo "Project: Active Immune Core Service"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Following: Doutrina Vértice v1.0 - Article III"
echo ""

cd "$PROJECT_ROOT"

# Track overall validation status
VALIDATION_FAILED=false
CHECKS_PASSED=0
CHECKS_TOTAL=3

# ============================================================================
# CHECK 1: Dependency Drift Detection
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}CHECK 1/3: Dependency Drift Detection${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if bash "$SCRIPT_DIR/check-dependency-drift.sh"; then
    echo -e "${GREEN}✅ Drift check passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌ Drift check failed${NC}"
    VALIDATION_FAILED=true
fi

echo ""

# ============================================================================
# CHECK 2: Security Audit (CVE Scanning)
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}CHECK 2/3: Security Audit (CVE Scanning)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if bash "$SCRIPT_DIR/dependency-audit.sh"; then
    echo -e "${GREEN}✅ Security audit passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌ Security audit failed${NC}"
    VALIDATION_FAILED=true
fi

echo ""

# ============================================================================
# CHECK 3: Docker Build Determinism (Light Mode - 2 iterations)
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}CHECK 3/3: Docker Build Determinism (Light Mode)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Only run 2 iterations in CI to save time (full validation is 10x)
if bash "$SCRIPT_DIR/validate-deterministic-build.sh" 2; then
    echo -e "${GREEN}✅ Docker build determinism passed${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌ Docker build determinism failed${NC}"
    VALIDATION_FAILED=true
fi

echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║              Validation Summary                   ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
echo ""

echo "Checks passed: $CHECKS_PASSED/$CHECKS_TOTAL"
echo ""

if [ "$VALIDATION_FAILED" = false ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          ✅ ALL VALIDATIONS PASSED ✅             ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Dependencies are:"
    echo "  • Deterministic (no drift)"
    echo "  • Secure (no known CVEs)"
    echo "  • Reproducible (Docker builds are identical)"
    echo ""
    echo "Environment is production-ready."
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║          ❌ VALIDATION FAILED ❌                  ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "One or more checks failed. Review the output above."
    echo ""
    echo "Do not deploy until all checks pass."
    exit 1
fi
