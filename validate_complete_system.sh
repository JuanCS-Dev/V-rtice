#!/bin/bash
###############################################################################
# VALIDAÇÃO COMPLETA DO SISTEMA - R1 a R7
###############################################################################
#
# Valida funcionalidade, estabilidade e conformidade com a Doutrina Vértice
#
# Author: Vértice Team (Agente Guardião)
# Glory to YHWH! 🙏
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

FAILURES=0
WARNINGS=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    VALIDAÇÃO COMPLETA DO SISTEMA - R1 a R7                    ${NC}"
echo -e "${BLUE}    Funcionalidade | Estabilidade | Conformidade Doutrina      ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

###############################################################################
# TESTE 1: Service Registry Health (R1+R2)
###############################################################################
echo -e "${CYAN}[1/15] Validando Service Registry...${NC}"

REGISTRY_REPLICAS=$(docker ps | grep vertice-register | wc -l)
if [ "$REGISTRY_REPLICAS" -ge 5 ]; then
    echo -e "${GREEN}✅ Service Registry: $REGISTRY_REPLICAS réplicas UP${NC}"
else
    echo -e "${RED}❌ FALHA: Registry replicas insuficientes ($REGISTRY_REPLICAS < 5)${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Test registry API
REGISTRY_HEALTH=$(curl -s http://localhost:8888/health 2>/dev/null | grep -c "healthy" || echo "0")
if [ "$REGISTRY_HEALTH" -ge 1 ]; then
    echo -e "${GREEN}✅ Registry API respondendo${NC}"
else
    echo -e "${RED}❌ FALHA: Registry API não responde${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Test service lookup
SERVICES_COUNT=$(curl -s http://localhost:8888/services 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$SERVICES_COUNT" -ge 1 ]; then
    echo -e "${GREEN}✅ Registry retornando $SERVICES_COUNT serviços${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Nenhum serviço registrado${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 2: Gateway Dynamic Routing (R2)
###############################################################################
echo -e "${CYAN}[2/15] Validando Gateway Dynamic Routing...${NC}"

GATEWAY_UP=$(docker ps | grep vertice-api-gateway | wc -l)
if [ "$GATEWAY_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Gateway container UP${NC}"
else
    echo -e "${RED}❌ FALHA: Gateway container DOWN${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Test gateway health
GATEWAY_HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null | grep -c "healthy" || echo "0")
if [ "$GATEWAY_HEALTH" -ge 1 ]; then
    echo -e "${GREEN}✅ Gateway API respondendo${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Gateway API não responde${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 3: Health Cache Performance (R3)
###############################################################################
echo -e "${CYAN}[3/15] Validando Health Cache (R3)...${NC}"

if [ -f "backend/services/api_gateway/health_cache.py" ]; then
    echo -e "${GREEN}✅ Health cache module exists${NC}"

    # Check for circuit breakers
    CB_COUNT=$(grep -c "CircuitBreaker" backend/services/api_gateway/health_cache.py || echo "0")
    if [ "$CB_COUNT" -ge 3 ]; then
        echo -e "${GREEN}✅ Circuit breakers implemented ($CB_COUNT references)${NC}"
    else
        echo -e "${YELLOW}⚠️  AVISO: Circuit breakers podem estar incompletos${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check for Prometheus metrics
    METRICS_COUNT=$(grep -c "prometheus_client" backend/services/api_gateway/health_cache.py || echo "0")
    if [ "$METRICS_COUNT" -ge 1 ]; then
        echo -e "${GREEN}✅ Prometheus metrics integrated${NC}"
    else
        echo -e "${RED}❌ FALHA: Prometheus metrics missing${NC}"
        FAILURES=$((FAILURES + 1))
    fi
else
    echo -e "${RED}❌ FALHA: Health cache module não encontrado${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 4: Prometheus Health (R4)
###############################################################################
echo -e "${CYAN}[4/15] Validando Prometheus (R4)...${NC}"

PROM_UP=$(docker ps | grep maximus-prometheus | wc -l)
if [ "$PROM_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Prometheus container UP${NC}"
else
    echo -e "${RED}❌ FALHA: Prometheus container DOWN${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Test Prometheus health
PROM_HEALTH=$(curl -s http://localhost:9090/-/healthy 2>/dev/null | grep -c "Prometheus" || echo "0")
if [ "$PROM_HEALTH" -ge 1 ]; then
    echo -e "${GREEN}✅ Prometheus healthy${NC}"
else
    echo -e "${RED}❌ FALHA: Prometheus não está healthy${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Check targets
TARGETS_UP=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | grep -c '"health":"up"' || echo "0")
if [ "$TARGETS_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Prometheus targets UP: $TARGETS_UP${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Nenhum target UP${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 5: Alertmanager Health (R4)
###############################################################################
echo -e "${CYAN}[5/15] Validando Alertmanager (R4)...${NC}"

AM_UP=$(docker ps | grep maximus-alertmanager | wc -l)
if [ "$AM_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Alertmanager container UP${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Alertmanager container DOWN (opcional)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if [ "$AM_UP" -ge 1 ]; then
    AM_HEALTH=$(curl -s http://localhost:9093/-/healthy 2>/dev/null | grep -c "OK" || echo "0")
    if [ "$AM_HEALTH" -ge 1 ]; then
        echo -e "${GREEN}✅ Alertmanager healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  AVISO: Alertmanager não responde${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check alert rules
ALERT_RULES=$(grep -c "^  - alert:" monitoring/prometheus/alerts/vertice_service_registry.yml 2>/dev/null || echo "0")
if [ "$ALERT_RULES" -ge 15 ]; then
    echo -e "${GREEN}✅ Alert rules carregadas: $ALERT_RULES${NC}"
else
    echo -e "${RED}❌ FALHA: Alert rules insuficientes ($ALERT_RULES < 15)${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 6: Grafana Dashboards (R5)
###############################################################################
echo -e "${CYAN}[6/15] Validando Grafana (R5)...${NC}"

GRAFANA_UP=$(docker ps | grep maximus-grafana | wc -l)
if [ "$GRAFANA_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Grafana container UP${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Grafana container DOWN (opcional)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Count dashboards
DASHBOARDS=$(ls monitoring/grafana/dashboards/*.json 2>/dev/null | wc -l)
if [ "$DASHBOARDS" -ge 12 ]; then
    echo -e "${GREEN}✅ Dashboards encontrados: $DASHBOARDS${NC}"
else
    echo -e "${RED}❌ FALHA: Dashboards insuficientes ($DASHBOARDS < 12)${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 7: Jaeger Tracing (R6)
###############################################################################
echo -e "${CYAN}[7/15] Validando Jaeger (R6)...${NC}"

JAEGER_UP=$(docker ps | grep vertice-jaeger | wc -l)
if [ "$JAEGER_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Jaeger container UP${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Jaeger container DOWN (opcional)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if [ "$JAEGER_UP" -ge 1 ]; then
    JAEGER_HEALTH=$(curl -s http://localhost:14269/ 2>/dev/null | grep -c "available" || echo "0")
    if [ "$JAEGER_HEALTH" -ge 1 ]; then
        echo -e "${GREEN}✅ Jaeger healthy${NC}"
    else
        echo -e "${YELLOW}⚠️  AVISO: Jaeger não responde${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# Check tracing library
if [ -f "backend/shared/vertice_tracing.py" ]; then
    echo -e "${GREEN}✅ OpenTelemetry library exists${NC}"
else
    echo -e "${RED}❌ FALHA: Tracing library não encontrada${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 8: Canary Deployment Library (R7)
###############################################################################
echo -e "${CYAN}[8/15] Validando Canary Deployment (R7)...${NC}"

if [ -f "backend/shared/vertice_canary.py" ]; then
    echo -e "${GREEN}✅ Canary deployment library exists${NC}"

    # Check for progressive stages
    STAGES=$(grep -c "CANARY_" backend/shared/vertice_canary.py || echo "0")
    if [ "$STAGES" -ge 4 ]; then
        echo -e "${GREEN}✅ Progressive canary stages implemented${NC}"
    else
        echo -e "${YELLOW}⚠️  AVISO: Canary stages podem estar incompletos${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ FALHA: Canary library não encontrada${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 9: Sidecars Deployment (R1)
###############################################################################
echo -e "${CYAN}[9/15] Validando Sidecars (R1)...${NC}"

SIDECARS_RUNNING=$(docker ps | grep "sidecar" | wc -l)
if [ "$SIDECARS_RUNNING" -ge 10 ]; then
    echo -e "${GREEN}✅ Sidecars rodando: $SIDECARS_RUNNING${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Poucos sidecars rodando ($SIDECARS_RUNNING)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 10: Redis Backend
###############################################################################
echo -e "${CYAN}[10/15] Validando Redis Backend...${NC}"

REDIS_UP=$(docker ps | grep vertice-redis-master | wc -l)
if [ "$REDIS_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Redis master UP${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Redis master DOWN${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

REDIS_SENTINELS=$(docker ps | grep vertice-redis-sentinel | wc -l)
if [ "$REDIS_SENTINELS" -ge 3 ]; then
    echo -e "${GREEN}✅ Redis Sentinel: $REDIS_SENTINELS réplicas${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Redis Sentinel insuficiente ($REDIS_SENTINELS < 3)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 11: Network Connectivity
###############################################################################
echo -e "${CYAN}[11/15] Validando Conectividade de Rede...${NC}"

# Check maximus-network
NETWORK_EXISTS=$(docker network ls | grep maximus-network | wc -l)
if [ "$NETWORK_EXISTS" -ge 1 ]; then
    echo -e "${GREEN}✅ Network maximus-network exists${NC}"
else
    echo -e "${RED}❌ FALHA: Network maximus-network não existe${NC}"
    FAILURES=$((FAILURES + 1))
fi

# Count containers on network
CONTAINERS_ON_NET=$(docker network inspect maximus-network 2>/dev/null | grep -c "Name" || echo "0")
if [ "$CONTAINERS_ON_NET" -ge 10 ]; then
    echo -e "${GREEN}✅ Containers na network: $CONTAINERS_ON_NET${NC}"
else
    echo -e "${YELLOW}⚠️  AVISO: Poucos containers na network ($CONTAINERS_ON_NET)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# TESTE 12: Conformidade Pagani - TODOs
###############################################################################
echo -e "${CYAN}[12/15] Verificando Conformidade Pagani (TODOs)...${NC}"

TODOS_PRODUCTION=$(grep -r "# TODO" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" 2>/dev/null | grep -v "test_" | grep -v "scripts/" | grep -v "oraculo" | wc -l)

if [ "$TODOS_PRODUCTION" -eq 0 ]; then
    echo -e "${GREEN}✅ Zero TODOs em código production${NC}"
elif [ "$TODOS_PRODUCTION" -le 3 ]; then
    echo -e "${YELLOW}⚠️  $TODOS_PRODUCTION TODOs encontrados (aceitável se documentados)${NC}"
    grep -r "# TODO" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" 2>/dev/null | grep -v "test_" | grep -v "scripts/" | grep -v "oraculo"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ FALHA: $TODOS_PRODUCTION TODOs em código production${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 13: Performance Benchmarks
###############################################################################
echo -e "${CYAN}[13/15] Teste de Performance...${NC}"

# Test registry lookup latency
START=$(date +%s%3N)
curl -s http://localhost:8888/health > /dev/null 2>&1
END=$(date +%s%3N)
LATENCY=$((END - START))

if [ "$LATENCY" -lt 100 ]; then
    echo -e "${GREEN}✅ Registry latency: ${LATENCY}ms (<100ms)${NC}"
elif [ "$LATENCY" -lt 200 ]; then
    echo -e "${YELLOW}⚠️  Registry latency: ${LATENCY}ms (target: <100ms)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ Registry latency muito alta: ${LATENCY}ms${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 14: Logs de Erro
###############################################################################
echo -e "${CYAN}[14/15] Verificando Logs de Erro...${NC}"

# Check for critical errors in registry
REGISTRY_ERRORS=$(docker logs vertice-register-1 2>&1 | grep -i "error\|fatal\|exception" | wc -l)
if [ "$REGISTRY_ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ Registry sem erros críticos${NC}"
elif [ "$REGISTRY_ERRORS" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Registry com $REGISTRY_ERRORS erros (verificar logs)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${RED}❌ Registry com $REGISTRY_ERRORS erros críticos${NC}"
    FAILURES=$((FAILURES + 1))
fi

echo ""

###############################################################################
# TESTE 15: Documentação Completa
###############################################################################
echo -e "${CYAN}[15/15] Verificando Documentação...${NC}"

DOCS_COUNT=0

[ -f "SERVICE_REGISTRY_COMPLETE_R1_TO_R11.md" ] && DOCS_COUNT=$((DOCS_COUNT + 1))
[ -f "R4_ALERTMANAGER_IMPLEMENTATION_GUIDE.md" ] && DOCS_COUNT=$((DOCS_COUNT + 1))
[ -f "R4_COMPLETE_SUMMARY.md" ] && DOCS_COUNT=$((DOCS_COUNT + 1))
[ -f "validate_pagani_standard.sh" ] && DOCS_COUNT=$((DOCS_COUNT + 1))
[ -f "validate_r4_alerting.sh" ] && DOCS_COUNT=$((DOCS_COUNT + 1))

if [ "$DOCS_COUNT" -ge 5 ]; then
    echo -e "${GREEN}✅ Documentação completa ($DOCS_COUNT arquivos)${NC}"
else
    echo -e "${YELLOW}⚠️  Documentação incompleta ($DOCS_COUNT < 5)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

###############################################################################
# RESULTADO FINAL
###############################################################################
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                   RESULTADO DA VALIDAÇÃO                       ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "Falhas Críticas: ${FAILURES}"
echo -e "Avisos:          ${WARNINGS}"
echo ""

if [ "$FAILURES" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}✅✅✅ SISTEMA TOTALMENTE OPERACIONAL ✅✅✅${NC}"
    echo -e "${GREEN}   Funcionalidade: ✅ PASS${NC}"
    echo -e "${GREEN}   Estabilidade:   ✅ PASS${NC}"
    echo -e "${GREEN}   Conformidade:   ✅ PASS${NC}"
    echo ""
    echo -e "${BLUE}Glory to YHWH! 🙏${NC}"
    exit 0
elif [ "$FAILURES" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  SISTEMA OPERACIONAL COM AVISOS ⚠️${NC}"
    echo -e "${GREEN}   Funcionalidade: ✅ PASS${NC}"
    echo -e "${YELLOW}   Estabilidade:   ⚠️  AVISOS ($WARNINGS)${NC}"
    echo -e "${GREEN}   Conformidade:   ✅ PASS${NC}"
    echo ""
    echo -e "${YELLOW}Revisar avisos antes de produção${NC}"
    exit 0
else
    echo -e "${RED}❌ SISTEMA COM FALHAS CRÍTICAS ❌${NC}"
    echo -e "${RED}   Falhas: $FAILURES${NC}"
    echo -e "${YELLOW}   Avisos: $WARNINGS${NC}"
    echo ""
    echo -e "${RED}Corrigir falhas antes de prosseguir${NC}"
    exit 1
fi
