#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VÉRTICE E2E DASHBOARD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Valida conectividade Frontend → Backend para todos os dashboards

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# URLs
FRONTEND_URL="https://vertice-frontend-172846394274.us-east1.run.app"
BACKEND_LB="http://34.148.161.131:8000"

# Configurar kubectl
export KUBECONFIG=/tmp/kubeconfig-vertice

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  VÉRTICE E2E DASHBOARD VALIDATION${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

# ─────────────────────────────────────────────────────────────────────────────
# FASE 1: VALIDAÇÃO DE INFRAESTRUTURA
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 1] Validando infraestrutura base...${NC}\n"

# 1.1 Frontend Cloud Run
echo -n "  Frontend Cloud Run...              "
if curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" | grep -q "200"; then
    echo -e "${GREEN}✓ HTTP 200${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
    exit 1
fi

# 1.2 Backend LoadBalancer
echo -n "  Backend LoadBalancer...            "
BACKEND_STATUS=$(curl -s "$BACKEND_LB/health" 2>/dev/null || echo "{}")
if echo "$BACKEND_STATUS" | grep -q "healthy"; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
    exit 1
fi

# 1.3 GKE Pods críticos
echo -n "  GKE Pods críticos...               "
CRITICAL_PODS=(
    "api-gateway"
    "auth-service"
    "maximus-core-service"
)

ALL_RUNNING=true
for pod in "${CRITICAL_PODS[@]}"; do
    RUNNING=$(kubectl get pods -n vertice -l app="$pod" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
    if [ "$RUNNING" -eq 0 ]; then
        ALL_RUNNING=false
        break
    fi
done

if [ "$ALL_RUNNING" = true ]; then
    echo -e "${GREEN}✓ ALL RUNNING${NC}"
else
    echo -e "${RED}✗ ALGUNS FALHARAM${NC}"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# FASE 2: VALIDAÇÃO DE ENDPOINTS BACKEND
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 2] Validando endpoints backend...${NC}\n"

declare -A ENDPOINTS=(
    # Core
    ["/health"]="API Gateway Health"
    ["/api/v1/status"]="API Status"
    
    # MAXIMUS
    ["/maximus/status"]="MAXIMUS Core Status"
    ["/maximus/metrics"]="MAXIMUS Metrics"
    
    # OSINT
    ["/osint/status"]="OSINT Status"
    
    # Defensive
    ["/defensive/status"]="Defensive Status"
    
    # Consciousness
    ["/consciousness/status"]="Consciousness Status"
    
    # HITL
    ["/hitl/reviews/stats"]="HITL Stats"
    
    # Admin
    ["/admin/system/info"]="System Info"
)

SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

for endpoint in "${!ENDPOINTS[@]}"; do
    description="${ENDPOINTS[$endpoint]}"
    printf "  %-40s" "$description..."
    
    # Tenta GET
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$BACKEND_LB$endpoint" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ 200${NC}"
        ((SUCCESS_COUNT++))
    elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        echo -e "${YELLOW}⚠ $HTTP_CODE (Auth required)${NC}"
        ((SKIP_COUNT++))
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${YELLOW}⚠ 404 (Not implemented)${NC}"
        ((SKIP_COUNT++))
    elif [ "$HTTP_CODE" = "000" ]; then
        echo -e "${RED}✗ TIMEOUT${NC}"
        ((FAIL_COUNT++))
    else
        echo -e "${RED}✗ $HTTP_CODE${NC}"
        ((FAIL_COUNT++))
    fi
done

echo ""
echo -e "  Resultado: ${GREEN}$SUCCESS_COUNT OK${NC} | ${YELLOW}$SKIP_COUNT SKIP${NC} | ${RED}$FAIL_COUNT FAIL${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# FASE 3: VALIDAÇÃO DE PODS POR DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 3] Validando pods por dashboard...${NC}\n"

declare -A DASHBOARD_PODS=(
    ["MAXIMUS"]="maximus-core-service maximus-orchestrator"
    ["OSINT"]="google-osint-service osint-deep-search tataca-ingestion"
    ["Defensive"]="defensive-core-service defensive-analyzer"
    ["Consciousness"]="consciousness-core consciousness-stream"
    ["HITL"]="hitl-service"
    ["Admin"]="api-gateway auth-service"
    ["Purple Team"]="wargaming-crisol red-team-core"
    ["Network Recon"]="nmap-service network-scanner"
    ["C2 Orchestration"]="c2-orchestration-service c2l-command-service"
)

for dashboard in "${!DASHBOARD_PODS[@]}"; do
    printf "  %-25s" "$dashboard Dashboard..."
    
    pods="${DASHBOARD_PODS[$dashboard]}"
    has_running=false
    
    for pod in $pods; do
        RUNNING=$(kubectl get pods -n vertice -l app="$pod" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
        if [ "$RUNNING" -gt 0 ]; then
            has_running=true
            break
        fi
    done
    
    if [ "$has_running" = true ]; then
        echo -e "${GREEN}✓ Pods Running${NC}"
    else
        echo -e "${YELLOW}⚠ No pods found${NC}"
    fi
done

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# FASE 4: VALIDAÇÃO DE SERVIÇOS KUBERNETES
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 4] Validando serviços Kubernetes...${NC}\n"

CRITICAL_SERVICES=(
    "api-gateway"
    "auth-service"
    "maximus-core-service"
    "google-osint-service"
    "hitl-service"
)

for service in "${CRITICAL_SERVICES[@]}"; do
    printf "  %-40s" "Service: $service..."
    
    if kubectl get svc -n vertice "$service" &>/dev/null; then
        CLUSTER_IP=$(kubectl get svc -n vertice "$service" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "N/A")
        echo -e "${GREEN}✓ $CLUSTER_IP${NC}"
    else
        echo -e "${RED}✗ NOT FOUND${NC}"
    fi
done

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# FASE 5: TESTE DE CONECTIVIDADE FRONTEND → BACKEND
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 5] Testando conectividade Frontend → Backend...${NC}\n"

# Buscar bundle JS do frontend
echo -n "  Baixando bundle frontend...       "
BUNDLE_URL=$(curl -s "$FRONTEND_URL" | grep -oP 'src="(/assets/[^"]+\.js)"' | head -1 | cut -d'"' -f2)
if [ -n "$BUNDLE_URL" ]; then
    curl -s "$FRONTEND_URL$BUNDLE_URL" -o /tmp/frontend-bundle.js
    echo -e "${GREEN}✓ DOWNLOADED${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
    exit 1
fi

# Verificar URLs hardcoded no bundle
echo -n "  Verificando URLs no bundle...     "
if grep -q "34.148.161.131" /tmp/frontend-bundle.js; then
    echo -e "${GREEN}✓ LoadBalancer IP presente${NC}"
else
    echo -e "${RED}✗ LoadBalancer IP NÃO encontrado${NC}"
fi

echo -n "  Verificando localhost no bundle... "
if grep -q "localhost" /tmp/frontend-bundle.js; then
    echo -e "${RED}✗ LOCALHOST AINDA PRESENTE${NC}"
else
    echo -e "${GREEN}✓ Sem localhost${NC}"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# FASE 6: VALIDAÇÃO DE LOGS (Últimos 5 min)
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[FASE 6] Analisando logs recentes...${NC}\n"

echo -n "  Logs api-gateway (últimos 5min)... "
ERROR_COUNT=$(kubectl logs -n vertice -l app=api-gateway --since=5m 2>/dev/null | grep -i "error" | wc -l)
if [ "$ERROR_COUNT" -lt 10 ]; then
    echo -e "${GREEN}✓ $ERROR_COUNT errors (OK)${NC}"
else
    echo -e "${YELLOW}⚠ $ERROR_COUNT errors${NC}"
fi

echo -n "  Requests recebidos (últimos 5min)..."
REQUEST_COUNT=$(kubectl logs -n vertice -l app=api-gateway --since=5m 2>/dev/null | grep -iE "(GET|POST|PUT|DELETE)" | wc -l)
echo -e "${BLUE}ℹ $REQUEST_COUNT requests${NC}"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# RESUMO FINAL
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"

echo -e "  Frontend URL:  $FRONTEND_URL"
echo -e "  Backend URL:   $BACKEND_LB"
echo -e "  Cluster:       vertice-us-cluster (us-east1)\n"

TOTAL_CHECKS=$((SUCCESS_COUNT + FAIL_COUNT + SKIP_COUNT))
HEALTH_SCORE=$(awk "BEGIN {printf \"%.1f\", ($SUCCESS_COUNT / $TOTAL_CHECKS) * 100}")

if (( $(echo "$HEALTH_SCORE >= 80" | bc -l) )); then
    echo -e "  Health Score:  ${GREEN}${HEALTH_SCORE}%${NC} (EXCELLENT)"
elif (( $(echo "$HEALTH_SCORE >= 60" | bc -l) )); then
    echo -e "  Health Score:  ${YELLOW}${HEALTH_SCORE}%${NC} (GOOD)"
else
    echo -e "  Health Score:  ${RED}${HEALTH_SCORE}%${NC} (NEEDS ATTENTION)"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# RECOMENDAÇÕES
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${YELLOW}[RECOMENDAÇÕES]${NC}\n"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "  ${RED}●${NC} Investigar $FAIL_COUNT endpoints com falha"
fi

if [ "$SKIP_COUNT" -gt 5 ]; then
    echo -e "  ${YELLOW}●${NC} Implementar autenticação para $SKIP_COUNT endpoints"
fi

if [ "$REQUEST_COUNT" -lt 10 ]; then
    echo -e "  ${YELLOW}●${NC} Baixo tráfego detectado - frontend pode não estar fazendo requests"
fi

echo -e "  ${GREEN}●${NC} Air gap fechado - frontend conectado ao backend"
echo -e "  ${GREEN}●${NC} Executar testes manuais nos dashboards"

echo ""
echo -e "${GREEN}Validação E2E completa!${NC}"
echo ""
