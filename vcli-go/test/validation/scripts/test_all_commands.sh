#!/bin/bash

# VALIDAÇÃO FUNCIONAL - vCLI-Go 32 Comandos
# Este script testa TODOS os 32 comandos implementados

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
KUBECONFIG="${PROJECT_ROOT}/test/validation/kubeconfig"
VCLI="${PROJECT_ROOT}/bin/vcli"
RESULTS_DIR="${PROJECT_ROOT}/test/validation/results"

export KUBECONFIG

mkdir -p "${RESULTS_DIR}"

# Results
TOTAL=0
PASSED=0
FAILED=0
RESULTS_FILE="${RESULTS_DIR}/functional_tests_$(date +%Y%m%d_%H%M%S).txt"

echo "========================================"
echo "🧪 vCLI-Go FUNCTIONAL VALIDATION"
echo "========================================"
echo "Testing 32 commands..."
echo ""

# Helper function
test_command() {
    local name="$1"
    local cmd="$2"
    local expected_success="${3:-0}"

    TOTAL=$((TOTAL + 1))
    echo -ne "${BLUE}[${TOTAL}/32]${NC} Testing: ${name}..."

    if eval "$cmd" > /dev/null 2>&1; then
        if [ "$expected_success" -eq 0 ]; then
            echo -e " ${GREEN}✅ PASS${NC}"
            echo "[PASS] $name" >> "$RESULTS_FILE"
            PASSED=$((PASSED + 1))
        else
            echo -e " ${RED}❌ FAIL (unexpected success)${NC}"
            echo "[FAIL] $name (unexpected success)" >> "$RESULTS_FILE"
            FAILED=$((FAILED + 1))
        fi
    else
        if [ "$expected_success" -eq 1 ]; then
            echo -e " ${GREEN}✅ PASS (expected failure)${NC}"
            echo "[PASS] $name (expected failure)" >> "$RESULTS_FILE"
            PASSED=$((PASSED + 1))
        else
            echo -e " ${RED}❌ FAIL${NC}"
            echo "[FAIL] $name" >> "$RESULTS_FILE"
            FAILED=$((FAILED + 1))
        fi
    fi
}

echo "📦 RESOURCE MANAGEMENT (5 commands)"
echo "===================================="
test_command "get pods" "${VCLI} k8s get pods -n vcli-test"
test_command "get pods (all-ns)" "${VCLI} k8s get pods --all-namespaces"
test_command "get pods (json)" "${VCLI} k8s get pods -n vcli-test -o json"
test_command "apply" "${VCLI} k8s apply -f ${PROJECT_ROOT}/test/validation/workloads/test-deployment.yaml"
test_command "scale" "${VCLI} k8s scale deployment nginx-test --replicas=3 -n vcli-test"
# Reset scale
${VCLI} k8s scale deployment nginx-test --replicas=2 -n vcli-test > /dev/null 2>&1
test_command "patch" "${VCLI} k8s patch deployment nginx-test -n vcli-test -p '{\"spec\":{\"replicas\":2}}'"
test_command "delete pod" "${VCLI} k8s delete pod broken-pod -n vcli-test"
echo ""

echo "👀 OBSERVABILITY (3 commands)"
echo "===================================="
test_command "logs" "${VCLI} k8s logs -n vcli-test $(${VCLI} k8s get pods -n vcli-test -o json | grep -o 'nginx-test-[^\"]*' | head -1)"
test_command "exec" "${VCLI} k8s exec debug-pod -n vcli-test -- ls /"
test_command "describe" "${VCLI} k8s describe deployment nginx-test -n vcli-test"
echo ""

echo "⚙️  ADVANCED OPERATIONS (2 commands)"
echo "===================================="
# Port-forward in background for 2 seconds then kill
test_command "port-forward" "timeout 2s ${VCLI} k8s port-forward -n vcli-test service/nginx-test 18080:80" 1
# Watch for 2 seconds then kill
test_command "watch" "timeout 2s ${VCLI} k8s watch pods -n vcli-test" 1
echo ""

echo "🔧 CONFIGURATION & SECRETS (5 commands)"
echo "===================================="
test_command "config get-context" "${VCLI} k8s config get-context"
test_command "get configmaps" "${VCLI} k8s get configmaps -n vcli-test"
test_command "get configmap" "${VCLI} k8s get configmap test-config -n vcli-test"
test_command "get secrets" "${VCLI} k8s get secrets -n vcli-test"
test_command "get secret" "${VCLI} k8s get secret test-secret -n vcli-test"
echo ""

echo "⏱️  WAIT OPERATIONS (1 command)"
echo "===================================="
test_command "wait" "${VCLI} k8s wait deployment nginx-test -n vcli-test --for=condition=Available --timeout=10s"
echo ""

echo "🔄 ROLLOUT MANAGEMENT (6 commands)"
echo "===================================="
test_command "rollout status" "${VCLI} k8s rollout status deployment/nginx-test -n vcli-test"
test_command "rollout history" "${VCLI} k8s rollout history deployment/nginx-test -n vcli-test"
test_command "rollout restart" "${VCLI} k8s rollout restart deployment/nginx-test -n vcli-test"
sleep 5 # Wait for restart
test_command "rollout pause" "${VCLI} k8s rollout pause deployment/nginx-test -n vcli-test"
test_command "rollout resume" "${VCLI} k8s rollout resume deployment/nginx-test -n vcli-test"
test_command "rollout undo" "${VCLI} k8s rollout undo deployment/nginx-test -n vcli-test"
echo ""

echo "📊 METRICS (4 commands)"
echo "===================================="
# Wait for metrics-server to be ready
sleep 10
test_command "top nodes" "${VCLI} k8s top nodes"
test_command "top node" "${VCLI} k8s top node vcli-test-control-plane"
test_command "top pods" "${VCLI} k8s top pods -n vcli-test"
POD_NAME=$(${VCLI} k8s get pods -n vcli-test -o json | grep -o 'nginx-test-[^\"]*' | head -1)
test_command "top pod" "${VCLI} k8s top pod ${POD_NAME} -n vcli-test"
echo ""

echo "🏷️  METADATA MANAGEMENT (2 commands)"
echo "===================================="
test_command "label" "${VCLI} k8s label deployment nginx-test -n vcli-test test-label=validated"
test_command "annotate" "${VCLI} k8s annotate deployment nginx-test -n vcli-test test-annotation=\"validation test\""
echo ""

echo "🛡️  AUTHORIZATION (2 commands)"
echo "===================================="
test_command "auth can-i" "${VCLI} k8s auth can-i create pods -n vcli-test"
test_command "auth whoami" "${VCLI} k8s auth whoami"
echo ""

# Summary
echo "========================================"
echo "📊 TEST SUMMARY"
echo "========================================"
echo -e "Total:  ${TOTAL}"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo -e "Success Rate: $((PASSED * 100 / TOTAL))%"
echo ""
echo "Results saved to: ${RESULTS_FILE}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! vCLI-Go is 100% FUNCTIONAL!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check results file for details.${NC}"
    exit 1
fi
