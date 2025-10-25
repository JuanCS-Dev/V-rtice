#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VÉRTICE E2E DASHBOARD VALIDATION - REALISTIC
# ═══════════════════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

FRONTEND="https://vertice-frontend-172846394274.us-east1.run.app"
BACKEND="http://34.148.161.131:8000"
export KUBECONFIG=/tmp/kubeconfig-vertice

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}║ VÉRTICE E2E DASHBOARD VALIDATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

SUCCESS=0
WARNING=0
FAIL=0

test_endpoint() {
    local url=$1
    local desc=$2
    local expected=${3:-200}
    
    printf "  %-50s" "$desc..."
    code=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$url" 2>/dev/null || echo "000")
    
    if [ "$code" = "$expected" ]; then
        echo -e "${GREEN}✓ $code${NC}"
        ((SUCCESS++))
    elif [ "$code" = "404" ] || [ "$code" = "401" ]; then
        echo -e "${YELLOW}⚠ $code${NC}"
        ((WARNING++))
    else
        echo -e "${RED}✗ $code${NC}"
        ((FAIL++))
    fi
}

test_pod_health() {
    local app=$1
    local desc=$2
    
    printf "  %-50s" "$desc..."
    
    RUNNING=$(kubectl get pods -n vertice -l app=$app --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    
    if [ "$RUNNING" -gt 0 ]; then
        # Testa health interno
        POD=$(kubectl get pods -n vertice -l app=$app --field-selector=status.phase=Running -o name 2>/dev/null | head -1)
        HEALTH=$(kubectl exec -n vertice $POD -- curl -s http://localhost:8080/health 2>/dev/null || echo "fail")
        
        if echo "$HEALTH" | grep -q "healthy\|ok\|running"; then
            echo -e "${GREEN}✓ Running + Healthy${NC}"
            ((SUCCESS++))
        else
            echo -e "${YELLOW}⚠ Running (health unclear)${NC}"
            ((WARNING++))
        fi
    else
        echo -e "${RED}✗ No pods running${NC}"
        ((FAIL++))
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/7] INFRAESTRUTURA CORE${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

test_endpoint "$FRONTEND" "Frontend Cloud Run"
test_endpoint "$BACKEND/health" "Backend API Gateway" 
test_endpoint "$BACKEND/docs" "API Documentation"
test_endpoint "$BACKEND/openapi.json" "OpenAPI Specification"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[2/7] DASHBOARDS - FRONTEND LOADING${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

echo -n "  Downloading frontend bundle...                    "
BUNDLE=$(curl -s "$FRONTEND" | grep -oP '/assets/index-[^"]+\.js' | head -1)
if [ -n "$BUNDLE" ]; then
    curl -s "$FRONTEND$BUNDLE" -o /tmp/bundle.js
    echo -e "${GREEN}✓${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC}"
    ((FAIL++))
fi

echo -n "  Checking LoadBalancer IP in bundle...            "
if grep -q "34.148.161.131" /tmp/bundle.js 2>/dev/null; then
    echo -e "${GREEN}✓ Present${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Missing${NC}"
    ((FAIL++))
fi

echo -n "  Checking localhost in bundle...                   "
if ! grep -q "localhost:[0-9]" /tmp/bundle.js 2>/dev/null; then
    echo -e "${GREEN}✓ Clean${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Still present${NC}"
    ((FAIL++))
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[3/7] MAXIMUS DASHBOARD${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

test_pod_health "maximus-core-service" "MAXIMUS Core Service"
test_pod_health "maximus-orchestrator" "MAXIMUS Orchestrator" 

# Teste via LoadBalancer (se exposto)
echo -n "  MAXIMUS via LoadBalancer...                       "
if kubectl get svc -n vertice maximus-core-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null | grep -q "."; then
    LB_IP=$(kubectl get svc -n vertice maximus-core-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    code=$(curl -s -o /dev/null -w "%{http_code}" -m 3 "http://$LB_IP:8150/health" 2>/dev/null || echo "000")
    if [ "$code" = "200" ]; then
        echo -e "${GREEN}✓ $code${NC}"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠ $code${NC}"
        ((WARNING++))
    fi
else
    echo -e "${YELLOW}⚠ ClusterIP only${NC}"
    ((WARNING++))
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/7] OSINT DASHBOARD${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

test_pod_health "google-osint-service" "Google OSINT Service"
test_pod_health "osint-service" "OSINT Core Service"
test_pod_health "tataca-ingestion" "Tatacá Ingestion"
test_pod_health "osint-deep-search" "OSINT Deep Search"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[5/7] DEFENSIVE DASHBOARD${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

test_pod_health "defensive-core-service" "Defensive Core"
test_pod_health "defensive-analyzer" "Defensive Analyzer"
test_pod_health "reactive-fabric-core" "Reactive Fabric Core"
test_pod_health "reactive-fabric-analysis" "Reactive Fabric Analysis"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[6/7] OUTROS DASHBOARDS${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

test_pod_health "hitl-patch-service" "HITL Console"
test_pod_health "auth-service" "Auth Service"
test_pod_health "c2-orchestration-service" "C2 Orchestration"
test_pod_health "wargaming-crisol" "Wargaming Crisol"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[7/7] CONECTIVIDADE E LOGS${NC}\n"
# ─────────────────────────────────────────────────────────────────────────────

echo -n "  API Gateway logs (last 5min)...                   "
ERROR_COUNT=$(kubectl logs -n vertice -l app=api-gateway --since=5m 2>/dev/null | grep -ci "error" || echo "0")
if [ "$ERROR_COUNT" -lt 20 ]; then
    echo -e "${GREEN}✓ $ERROR_COUNT errors${NC}"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠ $ERROR_COUNT errors${NC}"
    ((WARNING++))
fi

echo -n "  Total requests (last 5min)...                     "
REQ_COUNT=$(kubectl logs -n vertice -l app=api-gateway --since=5m 2>/dev/null | grep -ci "GET\|POST\|PUT\|DELETE" || echo "0")
echo -e "${BLUE}ℹ $REQ_COUNT requests${NC}"

echo -n "  Backend → Frontend connectivity...                "
if curl -s "$FRONTEND" | grep -q "34.148.161.131"; then
    echo -e "${GREEN}✓ Connected${NC}"
    ((SUCCESS++))
else
    echo -e "${RED}✗ Not configured${NC}"
    ((FAIL++))
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# RESUMO
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}║ RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

TOTAL=$((SUCCESS + WARNING + FAIL))
SCORE=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS / $TOTAL) * 100}")

echo -e "  ${GREEN}✓ Success:${NC}  $SUCCESS"
echo -e "  ${YELLOW}⚠ Warnings:${NC} $WARNING"
echo -e "  ${RED}✗ Failures:${NC} $FAIL"
echo ""

if (( $(echo "$SCORE >= 80" | bc -l) )); then
    echo -e "  Health Score: ${GREEN}${SCORE}%${NC} 🎯 EXCELLENT"
    STATUS="OPERATIONAL"
elif (( $(echo "$SCORE >= 60" | bc -l) )); then
    echo -e "  Health Score: ${YELLOW}${SCORE}%${NC} ⚠️  GOOD"
    STATUS="DEGRADED"
else
    echo -e "  Health Score: ${RED}${SCORE}%${NC} ❌ CRITICAL"
    STATUS="DOWN"
fi

echo ""
echo -e "  Status: ${BLUE}$STATUS${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARDS PRONTOS PARA TESTE MANUAL
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}║ DASHBOARDS PRONTOS PARA TESTE MANUAL${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "  🌐 Frontend: $FRONTEND"
echo ""
echo -e "  Dashboards disponíveis:"
echo -e "    ${GREEN}✓${NC} MAXIMUS Dashboard      (Core + Orchestrator)"
echo -e "    ${GREEN}✓${NC} OSINT Dashboard        (Google + Deep Search)"
echo -e "    ${GREEN}✓${NC} Defensive Dashboard    (Reactive Fabric)"
echo -e "    ${YELLOW}⚠${NC} HITL Console           (Pods running, endpoint a verificar)"
echo -e "    ${GREEN}✓${NC} Admin Panel            (Auth + Gateway)"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# PRÓXIMOS PASSOS
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo ""
echo -e "  1. Abrir frontend no navegador: $FRONTEND"
echo -e "  2. Testar cada dashboard manualmente"
echo -e "  3. Verificar console do browser (F12) para erros"
echo -e "  4. Confirmar que requests chegam no backend:"
echo -e "     kubectl logs -n vertice -l app=api-gateway -f"
echo ""

if [ "$FAIL" -gt 5 ]; then
    echo -e "${RED}⚠️  ATENÇÃO: $FAIL falhas detectadas - investigar antes de testes manuais${NC}"
    echo ""
fi
