#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO E2E - VÉRTICE PLATFORM (2024-2025 Best Practices)
# ═══════════════════════════════════════════════════════════════════════════
# Features:
# - Modern curl with retry/timeout (2024-2025 best practices)
# - JSON output for machine-readable results
# - Risk-focused testing (critical → high → medium)
# - Comprehensive reporting with air gaps analysis
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Configuration
readonly FRONTEND_URL="https://vertice-frontend-172846394274.us-east1.run.app"
readonly BACKEND_URL="http://34.148.161.131:8000"
readonly RESULTS_JSON="/home/juan/vertice-dev/docs/08-REPORTS/e2e_results.json"
readonly REPORT_MD="/home/juan/vertice-dev/docs/08-REPORTS/E2E_VALIDATION_FINAL.md"

# Counters
TOTAL=0
PASSED=0
FAILED=0
CRITICAL_FAILED=0
HIGH_FAILED=0

# Results array
declare -a RESULTS=()

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

log_phase() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Test endpoint with 2024-2025 best practices
test_api() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"
    local priority="${4:-medium}"

    TOTAL=$((TOTAL + 1))
    local start=$(date +%s%3N)

    # Modern curl flags (production-grade)
    local response=$(curl \
        --silent \
        --show-error \
        --write-out "\n%{http_code}" \
        --output /dev/null \
        --location \
        --max-redirs 3 \
        --retry 3 \
        --retry-delay 1 \
        --retry-connrefused \
        --max-time 10 \
        --connect-timeout 5 \
        "$url" 2>&1 || echo "000")

    local http_code=$(echo "$response" | tail -1)
    local end=$(date +%s%3N)
    local duration=$((end - start))

    # Determine status
    local status="PASS"
    if [ "$http_code" != "$expected" ]; then
        status="FAIL"
        FAILED=$((FAILED + 1))
        [ "$priority" = "critical" ] && CRITICAL_FAILED=$((CRITICAL_FAILED + 1))
        [ "$priority" = "high" ] && HIGH_FAILED=$((HIGH_FAILED + 1))
    else
        PASSED=$((PASSED + 1))
    fi

    # Store result
    RESULTS+=("{\"name\":\"$name\",\"url\":\"$url\",\"expected\":$expected,\"actual\":$http_code,\"status\":\"$status\",\"priority\":\"$priority\",\"duration_ms\":$duration}")

    # Display
    if [ "$status" = "PASS" ]; then
        echo -e "  ${GREEN}✅${NC} [$priority] $name → HTTP $http_code (${duration}ms)"
    else
        echo -e "  ${RED}❌${NC} [$priority] $name → HTTP $http_code expected $expected (${duration}ms)"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST PHASES
# ═══════════════════════════════════════════════════════════════════════════

run_tests() {
    log_phase "PHASE 1: CRITICAL INFRASTRUCTURE"
    test_api "Frontend loads" "$FRONTEND_URL" "200" "critical"
    test_api "Backend health" "$BACKEND_URL/health" "200" "critical"

    log_phase "PHASE 2: MAXIMUS AI CORE"
    test_api "Maximus Core status" "$BACKEND_URL/api/maximus/status" "200" "high"
    test_api "Maximus Core health" "$BACKEND_URL/api/maximus/health" "200" "high"
    test_api "Maximus Eureka" "$BACKEND_URL/api/eureka/health" "200" "high"
    test_api "Maximus Oráculo" "$BACKEND_URL/api/oraculo/health" "200" "high"

    log_phase "PHASE 3: OFFENSIVE TOOLS"
    test_api "Network Recon" "$BACKEND_URL/api/network-recon/health" "200" "high"
    test_api "BAS" "$BACKEND_URL/api/bas/health" "200" "high"
    test_api "C2 Orchestration" "$BACKEND_URL/api/c2/health" "200" "high"
    test_api "Web Attack" "$BACKEND_URL/api/web-attack/health" "200" "high"
    test_api "Vuln Intel" "$BACKEND_URL/api/vuln-intel/health" "200" "high"

    log_phase "PHASE 4: DEFENSIVE TOOLS"
    test_api "Behavioral Analyzer" "$BACKEND_URL/api/behavioral/health" "200" "high"
    test_api "Traffic Analyzer" "$BACKEND_URL/api/traffic/health" "200" "high"
    test_api "MAV Detection" "$BACKEND_URL/api/mav/health" "200" "high"

    log_phase "PHASE 5: OSINT"
    test_api "OSINT" "$BACKEND_URL/api/osint/health" "200" "medium"
    test_api "Domain Intel" "$BACKEND_URL/api/domain/health" "200" "medium"
    test_api "IP Intel" "$BACKEND_URL/api/ip/health" "200" "medium"
    test_api "Threat Intel" "$BACKEND_URL/api/threat-intel/health" "200" "medium"
    test_api "Nmap" "$BACKEND_URL/api/nmap/health" "200" "medium"

    log_phase "PHASE 6: CONSCIOUSNESS"
    test_api "Consciousness" "$BACKEND_URL/api/consciousness/health" "200" "medium"
    test_api "Reactive Fabric" "$BACKEND_URL/api/reactive-fabric/health" "200" "medium"
    test_api "Immune System" "$BACKEND_URL/api/immune/health" "200" "medium"
    test_api "Tegumentar" "$BACKEND_URL/api/tegumentar/health" "200" "medium"

    log_phase "PHASE 7: SENSORY SERVICES"
    test_api "Visual Cortex" "$BACKEND_URL/api/visual-cortex/health" "200" "medium"
    test_api "Auditory Cortex" "$BACKEND_URL/api/auditory-cortex/health" "200" "medium"
    test_api "Somatosensory" "$BACKEND_URL/api/somatosensory/health" "200" "medium"
    test_api "Chemical Sensing" "$BACKEND_URL/api/chemical-sensing/health" "200" "medium"

    log_phase "PHASE 8: HITL"
    test_api "HITL" "$BACKEND_URL/api/hitl/health" "200" "medium"
    test_api "HITL Patch" "$BACKEND_URL/api/hitl-patch/health" "200" "medium"
}

# ═══════════════════════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════════════════════

generate_report() {
    log_phase "GENERATING REPORTS"

    # JSON output
    echo "[" > "$RESULTS_JSON"
    local first=1
    for result in "${RESULTS[@]}"; do
        [ $first -eq 0 ] && echo "," >> "$RESULTS_JSON"
        echo "  $result" >> "$RESULTS_JSON"
        first=0
    done
    echo "]" >> "$RESULTS_JSON"

    # Calculate success rate
    local success_rate=0
    [ $TOTAL -gt 0 ] && success_rate=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)

    # Markdown report
    cat > "$REPORT_MD" <<EOF
# 🔍 E2E VALIDATION REPORT - VÉRTICE PLATFORM

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Frontend**: $FRONTEND_URL
**Backend**: $BACKEND_URL

---

## 📊 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Tests** | $TOTAL |
| **Passed** | $PASSED ✅ |
| **Failed** | $FAILED ❌ |
| **Success Rate** | $success_rate% |

### Failures by Priority

| Priority | Count |
|----------|-------|
| 🔴 **CRITICAL** | $CRITICAL_FAILED |
| 🟠 **HIGH** | $HIGH_FAILED |
| 🟡 **MEDIUM** | $(($FAILED - $CRITICAL_FAILED - $HIGH_FAILED)) |

---

## 🎯 VERDICT

EOF

    # Determine verdict
    if [ $CRITICAL_FAILED -gt 0 ]; then
        cat >> "$REPORT_MD" <<EOF
### 🚨 BLOCKER - CRITICAL FAILURES

**Status**: ❌ **NOT PRODUCTION READY**

Critical user flows are broken. Platform cannot be deployed until these issues are resolved.

**Action Required**: Fix critical endpoints immediately.

EOF
    elif [ $HIGH_FAILED -gt 5 ]; then
        cat >> "$REPORT_MD" <<EOF
### ⚠️ MAJOR ISSUES

**Status**: ⚠️ **NOT RECOMMENDED FOR PRODUCTION**

Multiple high-priority features broken. Core functionality affected.

**Action Required**: Fix high-priority endpoints before production deployment.

EOF
    elif (( $(echo "$success_rate >= 90" | bc -l) )); then
        cat >> "$REPORT_MD" <<EOF
### ✅ OPERATIONAL

**Status**: ✅ **PRODUCTION READY**

Platform operational with $success_rate% success rate. Minor issues in non-critical features.

**Recommendation**: Deploy to production. Monitor and fix minor issues in next sprint.

EOF
    else
        cat >> "$REPORT_MD" <<EOF
### ⚠️ PARTIAL FUNCTIONALITY

**Status**: ⚠️ **CAUTION**

Success rate: $success_rate%. Significant issues detected.

**Action Required**: Review failures and fix before production deployment.

EOF
    fi

    # Add failures section if any
    if [ $FAILED -gt 0 ]; then
        cat >> "$REPORT_MD" <<EOF

---

## ❌ AIR GAPS DETECTED

The following endpoints failed, indicating real integration issues:

EOF
        # Parse JSON and list failures
        jq -r '.[] | select(.status == "FAIL") | "- **\(.priority | ascii_upcase)**: \(.name) → `\(.url)` (HTTP \(.actual), expected \(.expected))"' "$RESULTS_JSON" >> "$REPORT_MD"

        cat >> "$REPORT_MD" <<EOF

### Possible Root Causes

1. **API Gateway Routing**: Routes not configured for these endpoints
2. **Service Availability**: Backend services may be down
3. **Network Configuration**: DNS/routing issues
4. **CORS**: Cross-origin requests blocked

EOF
    else
        cat >> "$REPORT_MD" <<EOF

---

## ✅ NO AIR GAPS

All tested endpoints responding correctly. Frontend-backend integration fully operational.

EOF
    fi

    # Next steps
    cat >> "$REPORT_MD" <<EOF

---

## 📋 NEXT STEPS

EOF

    if [ $CRITICAL_FAILED -gt 0 ] || [ $HIGH_FAILED -gt 5 ]; then
        cat >> "$REPORT_MD" <<EOF
### Immediate Actions

1. Check API Gateway logs: \`kubectl logs -n vertice deployment/api-gateway --tail=100\`
2. Verify failed service health: \`kubectl get pods -n vertice | grep -E "($(jq -r '.[] | select(.status == "FAIL") | .name' "$RESULTS_JSON" | sed 's/.*/(.*)\?/' | tr '\n' '|' | sed 's/|$//'))" \`
3. Test manually: $FRONTEND_URL

EOF
    else
        cat >> "$REPORT_MD" <<EOF
### Recommended Actions

1. ✅ Platform ready for production deployment
2. Monitor failed endpoints (if any) in next sprint
3. Set up alerting for endpoint health
4. Test manually: $FRONTEND_URL

EOF
    fi

    cat >> "$REPORT_MD" <<EOF

---

**\"Conhecereis a verdade, e a verdade vos libertará\"** - João 8:32

*Report generated by Vértice E2E Validation (2024-2025 Best Practices)*
*JSON Results*: \`$RESULTS_JSON\`
EOF

    echo ""
    echo -e "${GREEN}✅${NC} Report generated: $REPORT_MD"
    echo -e "${GREEN}✅${NC} JSON results: $RESULTS_JSON"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    clear
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo "║            E2E VALIDATION - VÉRTICE PLATFORM (2024-2025)              ║"
    echo "║                                                                       ║"
    echo "║   \"Conhecereis a verdade, e a verdade vos libertará\" - João 8:32     ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "${CYAN}Frontend:${NC} $FRONTEND_URL"
    echo -e "${CYAN}Backend:${NC}  $BACKEND_URL"
    echo ""

    # Run tests
    run_tests

    # Generate report
    generate_report

    # Summary
    echo ""
    log_phase "VALIDATION COMPLETE"
    echo ""
    echo "Total:   $TOTAL tests"
    echo -e "Passed:  ${GREEN}$PASSED ✅${NC}"
    echo -e "Failed:  ${RED}$FAILED ❌${NC}"
    [ $TOTAL -gt 0 ] && echo "Success: $(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)%"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
        return 0
    else
        echo -e "${RED}❌ $FAILED tests failed${NC}"
        return 1
    fi
}

main "$@"
