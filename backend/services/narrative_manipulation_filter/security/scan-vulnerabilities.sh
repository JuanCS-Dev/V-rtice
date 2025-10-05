#!/bin/bash

# ============================================================================
# Security Vulnerability Scanner - Cognitive Defense System
# Automated security scanning before deployment
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$SCRIPT_DIR/results/$(date +%Y%m%d_%H%M%S)"
IMAGE_NAME="vertice/cognitive-defense:2.0.0"

# Create results directory
mkdir -p "$RESULTS_DIR"

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "\n${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_tool() {
    local tool=$1
    local install_msg=$2

    if command -v "$tool" &> /dev/null; then
        print_success "$tool is installed"
        return 0
    else
        print_warning "$tool is not installed. $install_msg"
        return 1
    fi
}

# ============================================================================
# SCAN FUNCTIONS
# ============================================================================

scan_python_dependencies() {
    print_header "1. Scanning Python Dependencies for Vulnerabilities"

    cd "$PROJECT_ROOT"

    # pip-audit
    if check_tool "pip-audit" "Install with: pip install pip-audit"; then
        print_info "Running pip-audit..."
        if pip-audit --desc --format json --output "$RESULTS_DIR/pip-audit.json" 2>&1 | tee "$RESULTS_DIR/pip-audit.log"; then
            print_success "pip-audit scan complete"
        else
            print_warning "pip-audit found vulnerabilities (see $RESULTS_DIR/pip-audit.json)"
        fi
    fi

    # safety
    if check_tool "safety" "Install with: pip install safety"; then
        print_info "Running safety check..."
        if safety check --json --output "$RESULTS_DIR/safety.json" 2>&1 | tee "$RESULTS_DIR/safety.log"; then
            print_success "safety check complete"
        else
            print_warning "safety found vulnerabilities (see $RESULTS_DIR/safety.json)"
        fi
    fi

    # Count vulnerabilities
    if [ -f "$RESULTS_DIR/pip-audit.json" ]; then
        local vuln_count=$(python3 -c "
import json
with open('$RESULTS_DIR/pip-audit.json') as f:
    data = json.load(f)
    print(len(data.get('vulnerabilities', [])))
" 2>/dev/null || echo "0")

        if [ "$vuln_count" -eq 0 ]; then
            print_success "No vulnerabilities found in dependencies"
        else
            print_warning "Found $vuln_count vulnerabilities"
        fi
    fi
}

scan_code_security() {
    print_header "2. Scanning Code for Security Issues"

    cd "$PROJECT_ROOT"

    # bandit
    if check_tool "bandit" "Install with: pip install bandit"; then
        print_info "Running bandit security scanner..."

        if bandit -r . \
            -ll \
            -f json \
            -o "$RESULTS_DIR/bandit.json" \
            --exclude './tests,./venv,./build' \
            2>&1 | tee "$RESULTS_DIR/bandit.log"; then
            print_success "bandit scan complete"
        else
            print_warning "bandit found security issues (see $RESULTS_DIR/bandit.json)"
        fi

        # Generate HTML report
        if command -v bandit &> /dev/null; then
            bandit -r . -ll -f html -o "$RESULTS_DIR/bandit.html" --exclude './tests,./venv,./build' 2>/dev/null || true
        fi
    fi

    # ruff with security rules
    if check_tool "ruff" "Install with: pip install ruff"; then
        print_info "Running ruff linter with security rules..."

        if ruff check . --select S --output-format json > "$RESULTS_DIR/ruff-security.json" 2>&1; then
            print_success "ruff security scan complete"
        else
            print_warning "ruff found potential issues"
        fi
    fi
}

scan_secrets() {
    print_header "3. Scanning for Hardcoded Secrets"

    cd "$PROJECT_ROOT"

    # detect-secrets
    if check_tool "detect-secrets" "Install with: pip install detect-secrets"; then
        print_info "Scanning for secrets..."

        if detect-secrets scan --all-files --exclude-files 'venv/.*|build/.*|\.git/.*' > "$RESULTS_DIR/secrets-baseline.json"; then
            print_success "Secrets scan complete"

            # Audit results
            local secrets_found=$(python3 -c "
import json
with open('$RESULTS_DIR/secrets-baseline.json') as f:
    data = json.load(f)
    print(sum(len(files) for files in data.get('results', {}).values()))
" 2>/dev/null || echo "0")

            if [ "$secrets_found" -eq 0 ]; then
                print_success "No secrets found in code"
            else
                print_error "Found $secrets_found potential secrets! Review $RESULTS_DIR/secrets-baseline.json"
            fi
        fi
    else
        # Fallback: grep for common patterns
        print_info "Using grep for basic secret detection..."

        grep -r -i -E "(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key).*=.*['\"][^'\"]{8,}" \
            --exclude-dir={venv,build,.git,node_modules} \
            --exclude="*.{pyc,log,json}" \
            . > "$RESULTS_DIR/grep-secrets.txt" 2>/dev/null || true

        if [ -s "$RESULTS_DIR/grep-secrets.txt" ]; then
            print_warning "Potential secrets found via grep (see $RESULTS_DIR/grep-secrets.txt)"
        else
            print_success "No obvious secrets found"
        fi
    fi
}

scan_container_image() {
    print_header "4. Scanning Container Image"

    # Check if image exists
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        print_warning "Image $IMAGE_NAME not found locally. Building..."

        cd "$PROJECT_ROOT"
        docker build -t "$IMAGE_NAME" . 2>&1 | tail -n 10
    fi

    # trivy
    if check_tool "trivy" "Install from: https://aquasecurity.github.io/trivy/"; then
        print_info "Scanning container image with trivy..."

        trivy image \
            --format json \
            --output "$RESULTS_DIR/trivy.json" \
            --severity HIGH,CRITICAL \
            "$IMAGE_NAME" 2>&1 | tee "$RESULTS_DIR/trivy.log"

        # Generate HTML report
        trivy image \
            --format template \
            --template "@contrib/html.tpl" \
            --output "$RESULTS_DIR/trivy.html" \
            "$IMAGE_NAME" 2>/dev/null || true

        # Count vulnerabilities
        local critical=$(grep -o '"Severity":"CRITICAL"' "$RESULTS_DIR/trivy.json" 2>/dev/null | wc -l || echo 0)
        local high=$(grep -o '"Severity":"HIGH"' "$RESULTS_DIR/trivy.json" 2>/dev/null | wc -l || echo 0)

        if [ "$critical" -eq 0 ] && [ "$high" -eq 0 ]; then
            print_success "No critical or high vulnerabilities found"
        else
            print_warning "Found $critical CRITICAL and $high HIGH vulnerabilities"
        fi
    fi

    # docker scan (if available)
    if command -v docker &> /dev/null && docker scan --help &> /dev/null; then
        print_info "Running docker scan..."

        docker scan --json "$IMAGE_NAME" > "$RESULTS_DIR/docker-scan.json" 2>&1 || true
    fi
}

scan_kubernetes_manifests() {
    print_header "5. Scanning Kubernetes Manifests"

    cd "$PROJECT_ROOT"

    if [ ! -d "k8s" ]; then
        print_warning "k8s directory not found, skipping K8s scans"
        return
    fi

    # kubesec
    if check_tool "kubesec" "Install from: https://kubesec.io/"; then
        print_info "Scanning K8s manifests with kubesec..."

        for manifest in k8s/*.yaml; do
            if [ -f "$manifest" ]; then
                local filename=$(basename "$manifest")
                print_info "Scanning $filename..."

                kubesec scan "$manifest" > "$RESULTS_DIR/kubesec-${filename}.json" 2>&1 || true
            fi
        done

        print_success "kubesec scan complete"
    fi

    # kube-score
    if check_tool "kube-score" "Install from: https://github.com/zegl/kube-score"; then
        print_info "Scoring K8s manifests..."

        kube-score score k8s/*.yaml > "$RESULTS_DIR/kube-score.txt" 2>&1 || true

        print_success "kube-score analysis complete"
    fi
}

scan_network_policies() {
    print_header "6. Validating Network Policies"

    cd "$PROJECT_ROOT"

    if [ ! -f "k8s/networkpolicy.yaml" ]; then
        print_warning "Network policy not found"
        return
    fi

    # Check if kubectl is available
    if ! check_tool "kubectl" "Install from: https://kubernetes.io/docs/tasks/tools/"; then
        return
    fi

    print_info "Checking network policy syntax..."

    if kubectl --dry-run=client -f k8s/networkpolicy.yaml apply 2>&1 | tee "$RESULTS_DIR/netpol-validation.log"; then
        print_success "Network policies are valid"
    else
        print_error "Network policy validation failed"
    fi
}

check_tls_configuration() {
    print_header "7. Checking TLS Configuration"

    # Check Ingress TLS settings
    if [ -f "$PROJECT_ROOT/k8s/ingress.yaml" ]; then
        print_info "Checking Ingress TLS configuration..."

        if grep -q "tls:" "$PROJECT_ROOT/k8s/ingress.yaml"; then
            print_success "TLS configured in Ingress"
        else
            print_warning "TLS not configured in Ingress"
        fi

        # Check for strong ciphers
        if grep -q "TLSv1.3" "$PROJECT_ROOT/k8s/ingress.yaml"; then
            print_success "TLS 1.3 enabled"
        else
            print_warning "TLS 1.3 not explicitly enabled"
        fi
    fi
}

generate_summary_report() {
    print_header "8. Generating Summary Report"

    local summary_file="$RESULTS_DIR/SECURITY_SUMMARY.md"

    cat > "$summary_file" << EOF
# Security Scan Summary Report

**Date**: $(date)
**System**: Cognitive Defense System v2.0.0
**Scan ID**: $(basename "$RESULTS_DIR")

---

## Scan Results

### 1. Python Dependencies
EOF

    if [ -f "$RESULTS_DIR/pip-audit.json" ]; then
        echo "- ✅ pip-audit scan completed" >> "$summary_file"
    else
        echo "- ⚠️  pip-audit scan not run" >> "$summary_file"
    fi

    if [ -f "$RESULTS_DIR/safety.json" ]; then
        echo "- ✅ safety check completed" >> "$summary_file"
    else
        echo "- ⚠️  safety check not run" >> "$summary_file"
    fi

    cat >> "$summary_file" << EOF

### 2. Code Security
EOF

    if [ -f "$RESULTS_DIR/bandit.json" ]; then
        echo "- ✅ bandit scan completed" >> "$summary_file"
    else
        echo "- ⚠️  bandit scan not run" >> "$summary_file"
    fi

    cat >> "$summary_file" << EOF

### 3. Secrets Detection
EOF

    if [ -f "$RESULTS_DIR/secrets-baseline.json" ]; then
        echo "- ✅ Secrets scan completed" >> "$summary_file"
    else
        echo "- ⚠️  Secrets scan not run" >> "$summary_file"
    fi

    cat >> "$summary_file" << EOF

### 4. Container Security
EOF

    if [ -f "$RESULTS_DIR/trivy.json" ]; then
        echo "- ✅ Container image scan completed" >> "$summary_file"
    else
        echo "- ⚠️  Container scan not run" >> "$summary_file"
    fi

    cat >> "$summary_file" << EOF

---

## Files Generated

EOF

    for file in "$RESULTS_DIR"/*; do
        echo "- $(basename "$file")" >> "$summary_file"
    done

    cat >> "$summary_file" << EOF

---

## Next Steps

1. Review all JSON/HTML reports in detail
2. Address any CRITICAL or HIGH severity findings
3. Update dependencies with vulnerabilities
4. Rerun scans until all issues resolved
5. Document any accepted risks

---

**Report Location**: \`$RESULTS_DIR\`
EOF

    print_success "Summary report generated: $summary_file"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header "COGNITIVE DEFENSE SYSTEM - SECURITY VULNERABILITY SCAN"

    print_info "Results will be saved to: $RESULTS_DIR"
    echo ""

    # Run all scans
    scan_python_dependencies
    scan_code_security
    scan_secrets
    scan_container_image
    scan_kubernetes_manifests
    scan_network_policies
    check_tls_configuration
    generate_summary_report

    # Final summary
    print_header "SCAN COMPLETE"
    print_success "All security scans completed"
    print_info "Review the summary report at: $RESULTS_DIR/SECURITY_SUMMARY.md"
    print_info "Detailed results in: $RESULTS_DIR/"

    echo -e "\n${YELLOW}IMPORTANT:${NC}"
    echo "- Review all findings before deployment"
    echo "- Address CRITICAL and HIGH vulnerabilities"
    echo "- Update the SECURITY_AUDIT.md checklist"
    echo ""
}

# Run main
main "$@"
