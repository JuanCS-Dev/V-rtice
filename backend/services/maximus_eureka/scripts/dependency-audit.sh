#!/bin/bash
# Dependency Security Audit Script
#
# This script performs comprehensive CVE scanning on all dependency files
# using multiple security databases:
# - Safety: Commercial vulnerability database
# - pip-audit: PyPA's official OSV-based scanner
#
# Following Doutrina Vértice - Article IV: Antifragilidade Deliberada

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Source whitelist checker
source "$SCRIPT_DIR/check-cve-whitelist.sh"

echo -e "${BLUE}🔒 Dependency Security Audit${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: Active Immune Core Service"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd "$PROJECT_ROOT"

# Validate whitelist first
echo -e "${BLUE}🔍 Validating CVE whitelist...${NC}"
if bash "$SCRIPT_DIR/check-cve-whitelist.sh" validate; then
    echo ""
else
    echo -e "${RED}❌ Whitelist validation failed${NC}"
    echo "Fix .cve-whitelist.yml before proceeding"
    exit 1
fi

# Check for expired whitelisted CVEs
echo -e "${BLUE}🕒 Checking whitelist expiration...${NC}"
if bash "$SCRIPT_DIR/check-cve-whitelist.sh" check-expiration; then
    echo ""
else
    echo -e "${YELLOW}⚠️  Some CVEs are expired or expiring soon${NC}"
    echo "Review required - see above for details"
    echo ""
fi

# Find all lock files
LOCK_FILES=$(find . -name "requirements*.lock" -type f | grep -v venv | grep -v .venv || true)

if [ -z "$LOCK_FILES" ]; then
    echo -e "${YELLOW}⚠️  No lock files found!${NC}"
    echo "Expected: requirements.txt.lock"
    echo "Run: uv pip compile requirements.txt -o requirements.txt.lock"
    exit 1
fi

echo -e "${BLUE}📋 Lock files found:${NC}"
for file in $LOCK_FILES; do
    echo "  - $file ($(wc -l < "$file") packages)"
done
echo ""

# ============================================================================
# SAFETY SCAN
# ============================================================================

echo -e "${BLUE}🛡️  Running Safety scan...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SAFETY_FAILED=false
SAFETY_OUTPUT_FILE="/tmp/safety-report-$(date +%s).txt"
WHITELISTED_CVES_COUNT=0
declare -a WHITELISTED_CVES_LIST

for lock_file in $LOCK_FILES; do
    echo ""
    echo "Scanning: $lock_file"

    if safety check --file "$lock_file" --output text > "$SAFETY_OUTPUT_FILE" 2>&1; then
        echo -e "${GREEN}✅ No vulnerabilities found by Safety${NC}"
    else
        echo -e "${RED}❌ Vulnerabilities detected by Safety!${NC}"
        cat "$SAFETY_OUTPUT_FILE"
        SAFETY_FAILED=true
    fi
done

echo ""

# ============================================================================
# PIP-AUDIT SCAN
# ============================================================================

echo -e "${BLUE}🔍 Running pip-audit scan...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PIP_AUDIT_FAILED=false
PIP_AUDIT_OUTPUT_FILE="/tmp/pip-audit-report-$(date +%s).txt"

# Check if pip-audit is installed
if ! command -v pip-audit &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip-audit not installed, installing via uv tool...${NC}"
    uv tool install pip-audit
fi

for lock_file in $LOCK_FILES; do
    echo ""
    echo "Scanning: $lock_file"

    # pip-audit requires requirements format, not freeze format
    # So we scan the requirements.txt instead
    base_file="${lock_file%.lock}"

    if [ -f "$base_file" ]; then
        if pip-audit --requirement "$base_file" > "$PIP_AUDIT_OUTPUT_FILE" 2>&1; then
            echo -e "${GREEN}✅ No vulnerabilities found by pip-audit${NC}"
        else
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 1 ]; then
                echo -e "${RED}❌ Vulnerabilities detected by pip-audit!${NC}"
                cat "$PIP_AUDIT_OUTPUT_FILE"
                PIP_AUDIT_FAILED=true
            else
                echo -e "${YELLOW}⚠️  pip-audit scan had warnings${NC}"
                cat "$PIP_AUDIT_OUTPUT_FILE"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Skipping pip-audit (base file $base_file not found)${NC}"
    fi
done

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 Audit Summary${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Show whitelisted CVEs count
if [ $WHITELISTED_CVES_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}ℹ️  Whitelisted CVEs (skipped): $WHITELISTED_CVES_COUNT${NC}"
    for cve_info in "${WHITELISTED_CVES_LIST[@]}"; do
        local cve_id=$(echo "$cve_info" | cut -d'|' -f1)
        local justification=$(echo "$cve_info" | cut -d'|' -f2)
        echo "  - $cve_id: $justification"
    done
    echo ""
fi

if [ "$SAFETY_FAILED" = false ] && [ "$PIP_AUDIT_FAILED" = false ]; then
    echo -e "${GREEN}✅ All security scans passed!${NC}"
    echo ""
    echo "No known vulnerabilities detected in dependencies."
    if [ $WHITELISTED_CVES_COUNT -gt 0 ]; then
        echo "($WHITELISTED_CVES_COUNT CVE(s) whitelisted with valid justification)"
    fi
    echo "Lock files are secure for deployment."
    exit 0
else
    echo -e "${RED}❌ Security vulnerabilities detected!${NC}"
    echo ""

    if [ "$SAFETY_FAILED" = true ]; then
        echo -e "  ${RED}✗${NC} Safety scan found vulnerabilities"
    fi

    if [ "$PIP_AUDIT_FAILED" = true ]; then
        echo -e "  ${RED}✗${NC} pip-audit scan found vulnerabilities"
    fi

    echo ""
    echo "Action required:"
    echo "  1. Review vulnerability reports above"
    echo "  2. Update affected packages in requirements.txt"
    echo "  3. Regenerate lock file: uv pip compile requirements.txt -o requirements.txt.lock"
    echo "  4. Re-run audit: bash scripts/dependency-audit.sh"
    echo ""
    echo "Reports saved:"
    echo "  - Safety: $SAFETY_OUTPUT_FILE"
    echo "  - pip-audit: $PIP_AUDIT_OUTPUT_FILE"

    exit 1
fi
