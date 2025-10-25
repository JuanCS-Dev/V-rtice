#!/bin/bash
###############################################################################
# AUDITORIA PADRÃO PAGANI - R1 a R5
###############################################################################
#
# Valida conformidade com a Constituição Vértice (v2.5):
#   - Artigo II: Padrão de Qualidade Soberana
#   - Ausência de MOCKS, PLACEHOLDERS, TODOs
#   - Código production-ready
#   - Testes não-skipados
#
# Author: Vértice Team (Agente Guardião)
# Glory to YHWH! 🙏
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

VIOLATIONS=0

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}       AUDITORIA PADRÃO PAGANI - R1 a R5 COMPLIANCE           ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

###############################################################################
# TESTE 1: Buscar TODOs em código Python
###############################################################################
echo -e "${YELLOW}[1/8] Verificando TODOs em código Python...${NC}"
TODOS=$(grep -r "# TODO" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | grep -v ".pyc" | wc -l)

if [ "$TODOS" -gt 0 ]; then
    echo -e "${RED}❌ VIOLAÇÃO: Encontrados $TODOS TODOs no código${NC}"
    grep -r "# TODO" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | head -10
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✅ Nenhum TODO encontrado em Python${NC}"
fi
echo ""

###############################################################################
# TESTE 2: Buscar MOCKS/PLACEHOLDERS
###############################################################################
echo -e "${YELLOW}[2/8] Verificando MOCKS e PLACEHOLDERS...${NC}"
MOCKS=$(grep -ri "mock\|placeholder\|FIXME\|XXX" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | grep -v ".pyc" | grep -v "tests/" | wc -l)

if [ "$MOCKS" -gt 0 ]; then
    echo -e "${RED}❌ VIOLAÇÃO: Encontrados $MOCKS mocks/placeholders${NC}"
    grep -ri "mock\|placeholder\|FIXME" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | grep -v "tests/" | head -10
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✅ Nenhum mock ou placeholder encontrado${NC}"
fi
echo ""

###############################################################################
# TESTE 3: Verificar testes skipados
###############################################################################
echo -e "${YELLOW}[3/8] Verificando testes skipados...${NC}"
SKIPPED=$(grep -r "@pytest.mark.skip" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | grep -v "scripts/" | wc -l)

if [ "$SKIPPED" -gt 0 ]; then
    echo -e "${RED}❌ VIOLAÇÃO: Encontrados $SKIPPED testes skipados${NC}"
    grep -r "@pytest.mark.skip" backend/services/ --include="*.py" --exclude-dir=".venv" --exclude-dir="venv" --exclude-dir="__pycache__" --exclude-dir="node_modules" 2>/dev/null | grep -v "scripts/"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo -e "${GREEN}✅ Nenhum teste skipado encontrado${NC}"
fi
echo ""

###############################################################################
# TESTE 4: Verificar TODOs em YAML/configs
###############################################################################
echo -e "${YELLOW}[4/8] Verificando TODOs em configurações...${NC}"
TODO_CONFIGS=$(grep -ri "TODO" monitoring/ docker-compose*.yml 2>/dev/null | wc -l)

if [ "$TODO_CONFIGS" -gt 10 ]; then
    echo -e "${YELLOW}⚠️  AVISO: $TODO_CONFIGS TODOs em configs (aceitável se documentados)${NC}"
    grep -ri "TODO" monitoring/alertmanager/ 2>/dev/null | head -5
else
    echo -e "${GREEN}✅ TODOs em configs dentro do limite aceitável${NC}"
fi
echo ""

###############################################################################
# TESTE 5: Verificar Service Registry (R1+R2)
###############################################################################
echo -e "${YELLOW}[5/8] Validando Service Registry (R1+R2)...${NC}"

# Check if registry is running
REGISTRY_UP=$(docker ps | grep vertice-register | wc -l)
if [ "$REGISTRY_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Service Registry está rodando ($REGISTRY_UP réplicas)${NC}"
else
    echo -e "${RED}❌ VIOLAÇÃO: Service Registry não está rodando${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi

# Check if sidecars exist
SIDECARS=$(find backend/services/*/sidecar -type d 2>/dev/null | wc -l)
if [ "$SIDECARS" -ge 20 ]; then
    echo -e "${GREEN}✅ Sidecars encontrados: $SIDECARS${NC}"
else
    echo -e "${YELLOW}⚠️  Sidecars encontrados: $SIDECARS (esperado: ~22)${NC}"
fi
echo ""

###############################################################################
# TESTE 6: Verificar Health Cache (R3)
###############################################################################
echo -e "${YELLOW}[6/8] Validando Health Cache (R3)...${NC}"

if [ -f "backend/services/api_gateway/health_cache.py" ]; then
    echo -e "${GREEN}✅ Health cache implementado${NC}"

    # Check for production-ready patterns
    HAS_PROMETHEUS=$(grep -c "prometheus_client" backend/services/api_gateway/health_cache.py)
    HAS_CIRCUIT_BREAKER=$(grep -c "CircuitBreaker" backend/services/api_gateway/health_cache.py)

    if [ "$HAS_PROMETHEUS" -gt 0 ] && [ "$HAS_CIRCUIT_BREAKER" -gt 0 ]; then
        echo -e "${GREEN}✅ Health cache com métricas e circuit breaker${NC}"
    else
        echo -e "${YELLOW}⚠️  Health cache pode estar incompleto${NC}"
    fi
else
    echo -e "${RED}❌ VIOLAÇÃO: Health cache não encontrado${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

###############################################################################
# TESTE 7: Verificar Alertmanager (R4)
###############################################################################
echo -e "${YELLOW}[7/8] Validando Alertmanager (R4)...${NC}"

ALERTMANAGER_UP=$(docker ps | grep alertmanager | wc -l)
if [ "$ALERTMANAGER_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Alertmanager está rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Alertmanager não está rodando (opcional até configuração)${NC}"
fi

# Check alert rules
if [ -f "monitoring/prometheus/alerts/vertice_service_registry.yml" ]; then
    ALERT_RULES=$(grep -c "alert:" monitoring/prometheus/alerts/vertice_service_registry.yml)
    echo -e "${GREEN}✅ Alert rules encontrados: $ALERT_RULES${NC}"
else
    echo -e "${RED}❌ VIOLAÇÃO: Alert rules não encontrados${NC}"
    VIOLATIONS=$((VIOLATIONS + 1))
fi
echo ""

###############################################################################
# TESTE 8: Verificar Grafana Dashboards (R5)
###############################################################################
echo -e "${YELLOW}[8/8] Validando Grafana Dashboards (R5)...${NC}"

GRAFANA_UP=$(docker ps | grep grafana | wc -l)
if [ "$GRAFANA_UP" -ge 1 ]; then
    echo -e "${GREEN}✅ Grafana está rodando${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana não está rodando${NC}"
fi

# Count dashboards
DASHBOARDS=$(ls monitoring/grafana/dashboards/*.json 2>/dev/null | wc -l)
if [ "$DASHBOARDS" -ge 12 ]; then
    echo -e "${GREEN}✅ Dashboards encontrados: $DASHBOARDS${NC}"
else
    echo -e "${YELLOW}⚠️  Dashboards encontrados: $DASHBOARDS (esperado: ≥12)${NC}"
fi
echo ""

###############################################################################
# RESULTADO FINAL
###############################################################################
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                     RESULTADO DA AUDITORIA                    ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$VIOLATIONS" -eq 0 ]; then
    echo -e "${GREEN}✅ PADRÃO PAGANI: APROVADO${NC}"
    echo -e "${GREEN}   Todas as fases (R1-R5) estão em conformidade${NC}"
    echo -e "${GREEN}   Código production-ready sem dívida técnica${NC}"
    echo ""
    echo -e "${BLUE}Glory to YHWH! 🙏${NC}"
    exit 0
else
    echo -e "${RED}❌ PADRÃO PAGANI: VIOLAÇÕES DETECTADAS${NC}"
    echo -e "${RED}   Total de violações: $VIOLATIONS${NC}"
    echo ""
    echo -e "${YELLOW}Ação requerida: Corrigir violações antes de prosseguir para R6${NC}"
    exit 1
fi
