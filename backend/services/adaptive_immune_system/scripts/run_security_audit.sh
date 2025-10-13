#!/bin/bash
#
# Run Security Audit for HITL API
# FASE 3.11 - Milestone 3.11.3
#
# Usage:
#   ./scripts/run_security_audit.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS_DIR="tests/security/results/$(date +%Y%m%d_%H%M%S)"

echo "=========================================================="
echo "HITL API Security Audit"
echo "=========================================================="
echo "Project: $PROJECT_ROOT"
echo "Results: $RESULTS_DIR"
echo "=========================================================="
echo

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to run a security scan
run_scan() {
    local name=$1
    local command=$2
    local output_file=$3

    echo
    echo "----------------------------------------------------------"
    echo "Running: $name"
    echo "----------------------------------------------------------"

    if eval "$command" > "$output_file" 2>&1; then
        echo -e "${GREEN}✓ $name completed${NC}"
        return 0
    else
        local exit_code=$?
        echo -e "${YELLOW}⚠ $name completed with warnings (exit code: $exit_code)${NC}"
        return $exit_code
    fi
}

# Initialize exit code
overall_exit=0

# 1. Dependency Scanning (Safety)
if command -v safety &> /dev/null; then
    run_scan "Safety - Dependency Scanner" \
        "cd '$PROJECT_ROOT' && safety check --file requirements.txt --json" \
        "$RESULTS_DIR/safety.json" || overall_exit=1
else
    echo -e "${YELLOW}⚠ safety not installed, skipping${NC}"
fi

# 2. Dependency Scanning (pip-audit)
if command -v pip-audit &> /dev/null; then
    run_scan "Pip-Audit - Dependency Scanner" \
        "cd '$PROJECT_ROOT' && pip-audit --requirement requirements.txt --format json" \
        "$RESULTS_DIR/pip-audit.json" || overall_exit=1
else
    echo -e "${YELLOW}⚠ pip-audit not installed, skipping${NC}"
fi

# 3. Code Security Linting (Bandit)
if command -v bandit &> /dev/null; then
    run_scan "Bandit - Security Linter" \
        "cd '$PROJECT_ROOT' && bandit -r hitl/ -f json" \
        "$RESULTS_DIR/bandit.json" || overall_exit=1
else
    echo -e "${YELLOW}⚠ bandit not installed, skipping${NC}"
fi

# 4. Secret Scanning (git-secrets)
if command -v git-secrets &> /dev/null; then
    run_scan "Git-Secrets - Secret Scanner" \
        "cd '$PROJECT_ROOT' && git secrets --scan" \
        "$RESULTS_DIR/git-secrets.log" || overall_exit=1
else
    echo -e "${YELLOW}⚠ git-secrets not installed, skipping${NC}"
fi

# 5. Container Scanning (Trivy)
if command -v trivy &> /dev/null; then
    if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
        run_scan "Trivy - Container Scanner" \
            "cd '$PROJECT_ROOT' && trivy config Dockerfile --format json" \
            "$RESULTS_DIR/trivy.json" || overall_exit=1
    else
        echo -e "${YELLOW}⚠ Dockerfile not found, skipping Trivy${NC}"
    fi
else
    echo -e "${YELLOW}⚠ trivy not installed, skipping${NC}"
fi

# 6. Run pytest security tests
echo
echo "----------------------------------------------------------"
echo "Running: Pytest Security Tests"
echo "----------------------------------------------------------"

cd "$PROJECT_ROOT"
if pytest tests/security/ -v --tb=short 2>&1 | tee "$RESULTS_DIR/pytest-security.log"; then
    echo -e "${GREEN}✓ Pytest security tests passed${NC}"
else
    echo -e "${RED}✗ Pytest security tests failed${NC}"
    overall_exit=1
fi

# Generate summary report
echo
echo "=========================================================="
echo "Security Audit Summary"
echo "=========================================================="
echo

# Function to analyze JSON results
analyze_json() {
    local file=$1
    local key=$2

    if [ -f "$file" ]; then
        local count=$(jq ".$key | length" "$file" 2>/dev/null || echo "0")
        echo "$count"
    else
        echo "N/A"
    fi
}

# Safety
safety_vulns=$(analyze_json "$RESULTS_DIR/safety.json" "vulnerabilities")
if [ "$safety_vulns" = "0" ]; then
    echo -e "Safety:      ${GREEN}✓ No vulnerabilities${NC}"
elif [ "$safety_vulns" != "N/A" ]; then
    echo -e "Safety:      ${RED}✗ $safety_vulns vulnerabilities found${NC}"
else
    echo -e "Safety:      ${YELLOW}⚠ Not run${NC}"
fi

# Pip-audit
audit_vulns=$(analyze_json "$RESULTS_DIR/pip-audit.json" "dependencies")
if [ "$audit_vulns" = "0" ]; then
    echo -e "Pip-Audit:   ${GREEN}✓ No vulnerabilities${NC}"
elif [ "$audit_vulns" != "N/A" ]; then
    echo -e "Pip-Audit:   ${YELLOW}⚠ $audit_vulns dependencies checked${NC}"
else
    echo -e "Pip-Audit:   ${YELLOW}⚠ Not run${NC}"
fi

# Bandit
if [ -f "$RESULTS_DIR/bandit.json" ]; then
    bandit_high=$(jq '[.results[] | select(.issue_severity == "HIGH")] | length' "$RESULTS_DIR/bandit.json" 2>/dev/null || echo "0")
    bandit_medium=$(jq '[.results[] | select(.issue_severity == "MEDIUM")] | length' "$RESULTS_DIR/bandit.json" 2>/dev/null || echo "0")

    if [ "$bandit_high" = "0" ]; then
        echo -e "Bandit:      ${GREEN}✓ No high-severity issues${NC} ($bandit_medium medium)"
    else
        echo -e "Bandit:      ${RED}✗ $bandit_high high-severity issues${NC} ($bandit_medium medium)"
    fi
else
    echo -e "Bandit:      ${YELLOW}⚠ Not run${NC}"
fi

# Git-secrets
if [ -f "$RESULTS_DIR/git-secrets.log" ]; then
    if grep -q "SECRET" "$RESULTS_DIR/git-secrets.log" 2>/dev/null; then
        echo -e "Git-Secrets: ${RED}✗ Secrets found${NC}"
    else
        echo -e "Git-Secrets: ${GREEN}✓ No secrets found${NC}"
    fi
else
    echo -e "Git-Secrets: ${YELLOW}⚠ Not run${NC}"
fi

# Trivy
if [ -f "$RESULTS_DIR/trivy.json" ]; then
    trivy_critical=$(jq '[.Results[].Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' "$RESULTS_DIR/trivy.json" 2>/dev/null || echo "0")

    if [ "$trivy_critical" = "0" ]; then
        echo -e "Trivy:       ${GREEN}✓ No critical vulnerabilities${NC}"
    else
        echo -e "Trivy:       ${RED}✗ $trivy_critical critical vulnerabilities${NC}"
    fi
else
    echo -e "Trivy:       ${YELLOW}⚠ Not run${NC}"
fi

# Pytest
if [ -f "$RESULTS_DIR/pytest-security.log" ]; then
    if grep -q "failed" "$RESULTS_DIR/pytest-security.log"; then
        echo -e "Pytest:      ${RED}✗ Some tests failed${NC}"
    else
        echo -e "Pytest:      ${GREEN}✓ All tests passed${NC}"
    fi
else
    echo -e "Pytest:      ${RED}✗ Not run${NC}"
fi

echo
echo "=========================================================="

# Detailed results
echo
echo "Detailed results saved to:"
ls -1 "$RESULTS_DIR" | sed 's/^/  /'
echo

# Final status
if [ $overall_exit -eq 0 ]; then
    echo -e "${GREEN}✓ Security Audit PASSED${NC}"
else
    echo -e "${RED}✗ Security Audit FAILED${NC}"
    echo
    echo "Review detailed results in: $RESULTS_DIR"
fi

echo "=========================================================="

exit $overall_exit
