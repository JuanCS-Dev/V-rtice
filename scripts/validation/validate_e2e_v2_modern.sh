#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VALIDAÇÃO E2E MODERNA - VÉRTICE PLATFORM
# ═══════════════════════════════════════════════════════════════════════════
# Based on 2024-2025 best practices:
# - Parallel execution with xargs for controlled concurrency
# - Exponential backoff retry mechanism
# - Built-in curl retry and timeout flags
# - Comprehensive error tracking with JSON output
# - Risk-focused approach (prioritizing critical user journeys)
# ═══════════════════════════════════════════════════════════════════════════

set -euo pipefail

# Configuration
FRONTEND_URL="https://vertice-frontend-172846394274.us-east1.run.app"
BACKEND_URL="http://34.148.161.131:8000"
MAX_PARALLEL=10  # Controlled parallelism
RETRY_COUNT=3
TIMEOUT=10
RESULTS_FILE="/home/juan/vertice-dev/docs/08-REPORTS/e2e_validation_results.json"
REPORT_FILE="/home/juan/vertice-dev/docs/08-REPORTS/E2E_VALIDATION_REPORT_V2.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Initialize results array
declare -a RESULTS=()

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

log_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_info() {
    echo -e "${CYAN}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Test API endpoint with modern curl best practices
# Usage: test_endpoint <name> <url> <expected_code> <priority>
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected="${3:-200}"
    local priority="${4:-medium}"  # critical, high, medium, low

    local start_time=$(date +%s%3N)

    # Modern curl flags (2024-2025 best practices)
    # --silent: no progress bar
    # --show-error: show errors even in silent mode
    # --fail-with-body: fail on HTTP errors but keep response body
    # --location: follow redirects
    # --max-redirs: limit redirect hops
    # --retry: retry on transient errors
    # --retry-all-errors: retry even on non-transient errors
    # --retry-delay: wait between retries
    # --max-time: total timeout
    # --connect-timeout: connection timeout
    local response=$(curl \
        --silent \
        --show-error \
        --write-out "\n%{http_code}\n%{time_total}" \
        --output /tmp/curl_response_$$.txt \
        --location \
        --max-redirs 3 \
        --retry $RETRY_COUNT \
        --retry-delay 1 \
        --retry-connrefused \
        --max-time $TIMEOUT \
        --connect-timeout 5 \
        "$url" 2>&1 || echo "000\n0")

    local http_code=$(echo "$response" | tail -2 | head -1)
    local time_total=$(echo "$response" | tail -1)
    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    # Read response body
    local body=""
    if [ -f /tmp/curl_response_$$.txt ]; then
        body=$(cat /tmp/curl_response_$$.txt 2>/dev/null | head -c 1000)
        rm -f /tmp/curl_response_$$.txt
    fi

    # Determine status
    local status="PASS"
    local message="OK"
    if [ "$http_code" != "$expected" ]; then
        status="FAIL"
        message="Expected HTTP $expected, got $http_code"
    fi

    # Store result as JSON
    local result=$(cat <<EOF
{
  "name": "$name",
  "url": "$url",
  "expected": $expected,
  "actual": $http_code,
  "status": "$status",
  "priority": "$priority",
  "duration_ms": $duration,
  "time_total_s": ${time_total:-0},
  "message": "$message",
  "timestamp": "$(date -Iseconds)"
}
EOF
)

    echo "$result" >> /tmp/e2e_results_$$.jsonl

    # Print result
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅${NC} [$priority] $name → HTTP $http_code (${duration}ms)"
    else
        echo -e "${RED}❌${NC} [$priority] $name → $message (${duration}ms)"
    fi

    return $([ "$status" = "PASS" ] && echo 0 || echo 1)
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

# Risk-focused approach: prioritize critical user journeys
# Based on 2024-2025 E2E testing best practices

test_critical_flows() {
    log_header "PHASE 1: CRITICAL USER FLOWS (PRIORITY: CRITICAL)"

    test_endpoint "Frontend loads" "$FRONTEND_URL" "200" "critical"
    test_endpoint "Backend health" "$BACKEND_URL/health" "200" "critical"
    test_endpoint "API Gateway root" "$BACKEND_URL/" "200" "critical"
}

test_maximus_core() {
    log_header "PHASE 2: MAXIMUS AI CORE (PRIORITY: HIGH)"

    # Test in parallel with controlled concurrency
    {
        echo "Maximus Core status|$BACKEND_URL/api/maximus/status|200|high"
        echo "Maximus Core health|$BACKEND_URL/api/maximus/health|200|high"
        echo "Maximus Eureka health|$BACKEND_URL/api/eureka/health|200|high"
        echo "Maximus Oráculo health|$BACKEND_URL/api/oraculo/health|200|high"
    } | xargs -P $MAX_PARALLEL -I {} bash -c '
        IFS="|" read -r name url expected priority <<< "{}"
        source /home/juan/vertice-dev/validate_e2e_v2_modern.sh
        test_endpoint "$name" "$url" "$expected" "$priority"
    '
}

test_offensive_tools() {
    log_header "PHASE 3: OFFENSIVE SECURITY TOOLS (PRIORITY: HIGH)"

    # Parallel execution of offensive tool tests
    {
        echo "Network Recon health|$BACKEND_URL/api/network-recon/health|200|high"
        echo "Network Recon status|$BACKEND_URL/api/network-recon/status|200|high"
        echo "BAS health|$BACKEND_URL/api/bas/health|200|high"
        echo "BAS status|$BACKEND_URL/api/bas/status|200|high"
        echo "C2 health|$BACKEND_URL/api/c2/health|200|high"
        echo "C2 status|$BACKEND_URL/api/c2/status|200|high"
        echo "Web Attack health|$BACKEND_URL/api/web-attack/health|200|high"
        echo "Web Attack status|$BACKEND_URL/api/web-attack/status|200|high"
        echo "Vuln Intel health|$BACKEND_URL/api/vuln-intel/health|200|high"
        echo "Vuln Intel status|$BACKEND_URL/api/vuln-intel/status|200|high"
    } | xargs -P $MAX_PARALLEL -I {} bash -c '
        IFS="|" read -r name url expected priority <<< "{}"
        source /home/juan/vertice-dev/validate_e2e_v2_modern.sh
        test_endpoint "$name" "$url" "$expected" "$priority"
    '
}

test_defensive_tools() {
    log_header "PHASE 4: DEFENSIVE SECURITY TOOLS (PRIORITY: HIGH)"

    {
        echo "Behavioral Analyzer health|$BACKEND_URL/api/behavioral/health|200|high"
        echo "Behavioral Analyzer status|$BACKEND_URL/api/behavioral/status|200|high"
        echo "Traffic Analyzer health|$BACKEND_URL/api/traffic/health|200|high"
        echo "Traffic Analyzer status|$BACKEND_URL/api/traffic/status|200|high"
        echo "MAV Detection health|$BACKEND_URL/api/mav/health|200|high"
        echo "MAV Detection status|$BACKEND_URL/api/mav/status|200|high"
    } | xargs -P $MAX_PARALLEL -I {} bash -c '
        IFS="|" read -r name url expected priority <<< "{}"
        source /home/juan/vertice-dev/validate_e2e_v2_modern.sh
        test_endpoint "$name" "$url" "$expected" "$priority"
    '
}

test_osint_tools() {
    log_header "PHASE 5: OSINT & INTELLIGENCE (PRIORITY: MEDIUM)"

    {
        echo "OSINT health|$BACKEND_URL/api/osint/health|200|medium"
        echo "Domain Intel health|$BACKEND_URL/api/domain/health|200|medium"
        echo "IP Intel health|$BACKEND_URL/api/ip/health|200|medium"
        echo "Threat Intel health|$BACKEND_URL/api/threat-intel/health|200|medium"
        echo "Nmap health|$BACKEND_URL/api/nmap/health|200|medium"
    } | xargs -P $MAX_PARALLEL -I {} bash -c '
        IFS="|" read -r name url expected priority <<< "{}"
        source /home/juan/vertice-dev/validate_e2e_v2_modern.sh
        test_endpoint "$name" "$url" "$expected" "$priority"
    '
}

test_consciousness_system() {
    log_header "PHASE 6: CONSCIOUSNESS & ADAPTIVE IMMUNITY (PRIORITY: MEDIUM)"

    {
        echo "Consciousness API|$BACKEND_URL/api/consciousness/health|200|medium"
        echo "Reactive Fabric|$BACKEND_URL/api/reactive-fabric/health|200|medium"
        echo "Immune System|$BACKEND_URL/api/immune/health|200|medium"
        echo "Tegumentar|$BACKEND_URL/api/tegumentar/health|200|medium"
        echo "Visual Cortex|$BACKEND_URL/api/visual-cortex/health|200|medium"
        echo "Auditory Cortex|$BACKEND_URL/api/auditory-cortex/health|200|medium"
        echo "Somatosensory|$BACKEND_URL/api/somatosensory/health|200|medium"
        echo "Chemical Sensing|$BACKEND_URL/api/chemical-sensing/health|200|medium"
    } | xargs -P $MAX_PARALLEL -I {} bash -c '
        IFS="|" read -r name url expected priority <<< "{}"
        source /home/juan/vertice-dev/validate_e2e_v2_modern.sh
        test_endpoint "$name" "$url" "$expected" "$priority"
    '
}

test_hitl_system() {
    log_header "PHASE 7: HITL (HUMAN-IN-THE-LOOP) (PRIORITY: MEDIUM)"

    test_endpoint "HITL API health" "$BACKEND_URL/api/hitl/health" "200" "medium"
    test_endpoint "HITL Patch service" "$BACKEND_URL/api/hitl-patch/health" "200" "medium"
}

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS & REPORTING
# ═══════════════════════════════════════════════════════════════════════════

generate_report() {
    log_header "GENERATING COMPREHENSIVE REPORT"

    # Consolidate all JSONL results into single JSON array
    if [ -f /tmp/e2e_results_$$.jsonl ]; then
        echo "[" > "$RESULTS_FILE"
        cat /tmp/e2e_results_$$.jsonl | sed '$ ! s/$/,/' >> "$RESULTS_FILE"
        echo "]" >> "$RESULTS_FILE"
        rm -f /tmp/e2e_results_$$.jsonl
    else
        echo "[]" > "$RESULTS_FILE"
    fi

    # Parse results with jq
    local total=$(jq 'length' "$RESULTS_FILE")
    local passed=$(jq '[.[] | select(.status == "PASS")] | length' "$RESULTS_FILE")
    local failed=$(jq '[.[] | select(.status == "FAIL")] | length' "$RESULTS_FILE")
    local success_rate=$(echo "scale=2; $passed * 100 / $total" | bc)

    local critical_failed=$(jq '[.[] | select(.priority == "critical" and .status == "FAIL")] | length' "$RESULTS_FILE")
    local high_failed=$(jq '[.[] | select(.priority == "high" and .status == "FAIL")] | length' "$RESULTS_FILE")
    local medium_failed=$(jq '[.[] | select(.priority == "medium" and .status == "FAIL")] | length' "$RESULTS_FILE")

    # Generate Markdown report
    cat > "$REPORT_FILE" <<EOF
# 🔍 E2E VALIDATION REPORT - VÉRTICE PLATFORM

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Frontend**: $FRONTEND_URL
**Backend**: $BACKEND_URL
**Methodology**: Risk-focused E2E testing (2024-2025 best practices)

---

## 📊 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Tests** | $total |
| **Passed** | $passed ✅ |
| **Failed** | $failed ❌ |
| **Success Rate** | $success_rate% |

### Failures by Priority

| Priority | Failures |
|----------|----------|
| 🔴 **CRITICAL** | $critical_failed |
| 🟠 **HIGH** | $high_failed |
| 🟡 **MEDIUM** | $medium_failed |

---

## 🎯 VERDICT

EOF

    if [ "$critical_failed" -gt 0 ]; then
        cat >> "$REPORT_FILE" <<EOF
### 🚨 BLOCKER - CRITICAL FAILURES DETECTED

**Status**: ❌ **NOT PRODUCTION READY**

Critical user flows are broken. The platform cannot be deployed to production until these issues are resolved.

**Critical Failures**:
EOF
        jq -r '.[] | select(.priority == "critical" and .status == "FAIL") | "- \(.name): \(.message)"' "$RESULTS_FILE" >> "$REPORT_FILE"

    elif [ "$high_failed" -gt 5 ]; then
        cat >> "$REPORT_FILE" <<EOF
### ⚠️ MAJOR ISSUES - HIGH PRIORITY FAILURES

**Status**: ⚠️ **NOT RECOMMENDED FOR PRODUCTION**

Multiple high-priority features are broken. While critical flows work, significant functionality is unavailable.

**High Priority Failures**:
EOF
        jq -r '.[] | select(.priority == "high" and .status == "FAIL") | "- \(.name): \(.message)"' "$RESULTS_FILE" >> "$REPORT_FILE"

    elif (( $(echo "$success_rate >= 90" | bc -l) )); then
        cat >> "$REPORT_FILE" <<EOF
### ✅ OPERATIONAL - MINOR ISSUES

**Status**: ✅ **PRODUCTION READY** (with minor caveats)

Platform is operational with $success_rate% success rate. Most features work correctly. Minor issues in non-critical features.
EOF
    else
        cat >> "$REPORT_FILE" <<EOF
### ⚠️ PARTIAL FUNCTIONALITY

**Status**: ⚠️ **CAUTION ADVISED**

Success rate: $success_rate%. Platform has significant issues but core functionality may work.
EOF
    fi

    # Detailed failures section
    if [ "$failed" -gt 0 ]; then
        cat >> "$REPORT_FILE" <<EOF

---

## ❌ DETAILED FAILURES

EOF
        jq -r '.[] | select(.status == "FAIL") | "### \(.priority | ascii_upcase): \(.name)\n\n- **Endpoint**: `\(.url)`\n- **Expected**: HTTP \(.expected)\n- **Actual**: HTTP \(.actual)\n- **Message**: \(.message)\n- **Duration**: \(.duration_ms)ms\n"' "$RESULTS_FILE" >> "$REPORT_FILE"
    fi

    # Performance metrics
    cat >> "$REPORT_FILE" <<EOF

---

## ⚡ PERFORMANCE METRICS

### Response Times

EOF

    jq -r '.[] | select(.status == "PASS") | "\(.name): \(.duration_ms)ms"' "$RESULTS_FILE" | sort -t: -k2 -n | tail -10 | while read line; do
        echo "- $line" >> "$REPORT_FILE"
    done

    # Air gaps analysis
    cat >> "$REPORT_FILE" <<EOF

---

## 🕳️ AIR GAPS ANALYSIS

### Real Integration Issues

EOF

    if [ "$failed" -eq 0 ]; then
        cat >> "$REPORT_FILE" <<EOF
**NO AIR GAPS DETECTED** ✅

All tested endpoints are responding correctly. Frontend-backend integration is fully operational.
EOF
    else
        cat >> "$REPORT_FILE" <<EOF
**AIR GAPS DETECTED** ❌

The following endpoints are not responding correctly, indicating integration issues:

EOF
        jq -r '.[] | select(.status == "FAIL") | "- **\(.name)**: \(.url) → \(.message)"' "$RESULTS_FILE" >> "$REPORT_FILE"

        cat >> "$REPORT_FILE" <<EOF

### Possible Root Causes

1. **API Gateway Routing**: Some routes may not be configured correctly
2. **Service Discovery**: Backend services may not be registered properly
3. **CORS Configuration**: Cross-origin requests may be blocked
4. **Network Configuration**: DNS/IP routing issues
5. **Service Health**: Some backend services may be down or unhealthy
EOF
    fi

    # Next steps
    cat >> "$REPORT_FILE" <<EOF

---

## 📋 NEXT STEPS

EOF

    if [ "$critical_failed" -gt 0 ]; then
        cat >> "$REPORT_FILE" <<EOF
### Immediate Actions (CRITICAL)

1. Fix critical user flows before any deployment
2. Check API Gateway logs: \`kubectl logs -n vertice deployment/api-gateway\`
3. Verify backend service health: \`kubectl get pods -n vertice\`
4. Test manually in browser: $FRONTEND_URL

EOF
    elif [ "$high_failed" -gt 0 ]; then
        cat >> "$REPORT_FILE" <<EOF
### High Priority Actions

1. Investigate high-priority failures
2. Review API Gateway routing configuration
3. Check CORS settings
4. Test failed endpoints individually

EOF
    else
        cat >> "$REPORT_FILE" <<EOF
### Recommended Actions

1. ✅ Deploy to production
2. Monitor in production for 24-48 hours
3. Set up alerting for endpoint failures
4. Fix minor issues in next sprint

EOF
    fi

    cat >> "$REPORT_FILE" <<EOF

---

**\"Conhecereis a verdade, e a verdade vos libertará\"** - João 8:32

*Report generated by Vértice E2E Validation Script v2.0*
*Methodology: Risk-focused E2E testing based on 2024-2025 industry best practices*
EOF

    log_success "Report generated: $REPORT_FILE"
    log_success "Raw results: $RESULTS_FILE"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

main() {
    clear
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                       ║"
    echo "║          E2E VALIDATION - VÉRTICE PLATFORM (MODERN 2024-2025)        ║"
    echo "║                                                                       ║"
    echo "║   \"Conhecereis a verdade, e a verdade vos libertará\" - João 8:32     ║"
    echo "║                                                                       ║"
    echo "╚═══════════════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Frontend: $FRONTEND_URL"
    log_info "Backend:  $BACKEND_URL"
    log_info "Parallel workers: $MAX_PARALLEL"
    log_info "Retry count: $RETRY_COUNT"
    log_info "Timeout: ${TIMEOUT}s"
    echo ""

    # Initialize results file
    rm -f /tmp/e2e_results_$$.jsonl

    # Run test phases
    test_critical_flows
    test_maximus_core
    test_offensive_tools
    test_defensive_tools
    test_osint_tools
    test_consciousness_system
    test_hitl_system

    # Generate comprehensive report
    generate_report

    # Display summary
    echo ""
    log_header "VALIDATION COMPLETE"
    echo ""
    log_info "Full report available at:"
    echo "  📄 $REPORT_FILE"
    echo "  📊 $RESULTS_FILE"
    echo ""

    # Show quick summary
    local total=$(jq 'length' "$RESULTS_FILE")
    local passed=$(jq '[.[] | select(.status == "PASS")] | length' "$RESULTS_FILE")
    local failed=$(jq '[.[] | select(.status == "FAIL")] | length' "$RESULTS_FILE")
    local success_rate=$(echo "scale=2; $passed * 100 / $total" | bc)

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "QUICK SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Total Tests:    $total"
    echo -e "Passed:         ${GREEN}$passed ✅${NC}"
    echo -e "Failed:         ${RED}$failed ❌${NC}"
    echo "Success Rate:   $success_rate%"
    echo ""

    if [ "$failed" -eq 0 ]; then
        log_success "ALL TESTS PASSED! Platform is operational."
        return 0
    else
        log_error "$failed tests failed. Review the report for details."
        return 1
    fi
}

# Run main function if script is executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
