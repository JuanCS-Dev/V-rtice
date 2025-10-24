#!/bin/bash
# ============================================================================
# Auto-Discovery de Portas - Vértice Ecosystem
# Escaneia todos os containers Docker e gera config atualizado
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$HOME/.vcli/config.yaml"
PORTS_JSON="$HOME/vertice-dev/PORTAS_MASTER.json"

echo "🔍 Auto-Discovery de Portas - Vértice Ecosystem"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para extrair porta do host
extract_port() {
    echo "$1" | grep -o '0.0.0.0:[0-9]*' | head -1 | cut -d':' -f2
}

# Função para pegar porta de container
get_port() {
    local container="$1"
    local internal_port="$2"
    docker ps --format "{{.Names}}\t{{.Ports}}" | grep "^$container" | awk '{print $2}' | grep "${internal_port}/tcp" | grep -o '0.0.0.0:[0-9]*' | cut -d':' -f2
}

echo "📊 Mapeando serviços rodando..."
echo ""

# Mapear serviços usando get_port
# MAXIMUS
MAXIMUS_CORE_PORT=$(get_port "maximus-core" "8150")
MAXIMUS_ORCH_PORT=$(get_port "maximus-orchestrator" "8016")
MAXIMUS_EUREKA_PORT=$(get_port "vertice-maximus_eureka" "8200")
MAXIMUS_PREDICT_PORT=$(get_port "maximus-predict" "8040")

# Investigation
IP_INTEL_PORT=$(get_port "vertice-ip-intel" "8034")
NMAP_PORT=$(get_port "vertice-nmap" "8047")
OSINT_PORT=$(get_port "vertice-osint" "8049")

# Immune & Others
IMMUNE_PORT=$(get_port "active-immune-core" "8200")
HITL_PORT=$(get_port "vertice-hitl-patch" "8000")
CRISOL_PORT=$(get_port "vertice-wargaming-crisol" "8000")

# Infrastructure
POSTGRES_PORT=$(get_port "maximus-postgres-immunity" "5432")
REDIS_PORT=$(get_port "vertice-redis-master" "6379")
VAULT_PORT=$(get_port "vertice-vault" "8200")

# Display results
echo -e "${BLUE}=== MAXIMUS Services ===${NC}"
[ -n "$MAXIMUS_CORE_PORT" ] && echo -e "${GREEN}✅${NC} MAXIMUS Core:        http://localhost:$MAXIMUS_CORE_PORT" || echo "❌ MAXIMUS Core: NOT RUNNING"
[ -n "$MAXIMUS_ORCH_PORT" ] && echo -e "${GREEN}✅${NC} Orchestrator:        http://localhost:$MAXIMUS_ORCH_PORT" || echo "❌ Orchestrator: NOT RUNNING"
[ -n "$MAXIMUS_EUREKA_PORT" ] && echo -e "${GREEN}✅${NC} Eureka:              http://localhost:$MAXIMUS_EUREKA_PORT" || echo "❌ Eureka: NOT RUNNING"
[ -n "$MAXIMUS_PREDICT_PORT" ] && echo -e "${GREEN}✅${NC} Predict/Oraculo:     http://localhost:$MAXIMUS_PREDICT_PORT" || echo "❌ Predict: NOT RUNNING"

echo ""
echo -e "${BLUE}=== Investigation Services ===${NC}"
[ -n "$IP_INTEL_PORT" ] && echo -e "${GREEN}✅${NC} IP Intelligence:     http://localhost:$IP_INTEL_PORT" || echo "❌ IP Intelligence: NOT RUNNING"
[ -n "$NMAP_PORT" ] && echo -e "${GREEN}✅${NC} NMAP Scanner:        http://localhost:$NMAP_PORT" || echo "❌ NMAP: NOT RUNNING"
[ -n "$OSINT_PORT" ] && echo -e "${GREEN}✅${NC} OSINT:               http://localhost:$OSINT_PORT" || echo "❌ OSINT: NOT RUNNING"

echo ""
echo -e "${BLUE}=== Other Services ===${NC}"
[ -n "$IMMUNE_PORT" ] && echo -e "${GREEN}✅${NC} Active Immune:       http://localhost:$IMMUNE_PORT" || echo "❌ Immune: NOT RUNNING"
[ -n "$HITL_PORT" ] && echo -e "${GREEN}✅${NC} HITL Patch:          http://localhost:$HITL_PORT" || echo "❌ HITL: NOT RUNNING"
[ -n "$CRISOL_PORT" ] && echo -e "${GREEN}✅${NC} Wargaming Crisol:    http://localhost:$CRISOL_PORT" || echo "❌ Crisol: NOT RUNNING"

echo ""
echo -e "${BLUE}=== Infrastructure ===${NC}"
[ -n "$POSTGRES_PORT" ] && echo -e "${GREEN}✅${NC} PostgreSQL:          localhost:$POSTGRES_PORT" || echo "❌ PostgreSQL: NOT RUNNING"
[ -n "$REDIS_PORT" ] && echo -e "${GREEN}✅${NC} Redis:               localhost:$REDIS_PORT" || echo "❌ Redis: NOT RUNNING"
[ -n "$VAULT_PORT" ] && echo -e "${GREEN}✅${NC} Vault:               http://localhost:$VAULT_PORT" || echo "❌ Vault: NOT RUNNING"

echo ""
echo "================================================"
echo -e "${YELLOW}📝 Portas descobertas e mapeadas!${NC}"
echo ""
echo "Config file: $CONFIG_FILE"
echo "Master JSON: $PORTS_JSON"
echo ""
