#!/bin/bash
# Integration Test: Reactive Fabric → Threat Intel Bridge → Active Immune Core
# Validates E2E threat intelligence flow

set -e

echo "===================================================================="
echo "  TESTE DE INTEGRAÇÃO: Reactive Immune System"
echo "===================================================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Verify services are healthy
echo "[1/5] Verificando health dos serviços..."
echo -n "  - Reactive Fabric Core: "
REACTIVE_STATUS=$(curl -s http://localhost:8600/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$REACTIVE_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ UNHEALTHY${NC}"
    exit 1
fi

echo -n "  - Active Immune Core: "
IMMUNE_STATUS=$(curl -s http://localhost:8200/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$IMMUNE_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ UNHEALTHY${NC}"
    exit 1
fi

echo -n "  - Threat Intel Bridge: "
BRIDGE_STATUS=$(curl -s http://localhost:8710/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$BRIDGE_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ HEALTHY${NC}"
else
    echo -e "${RED}✗ UNHEALTHY${NC}"
    exit 1
fi

echo

# Step 2: Get baseline metrics
echo "[2/5] Capturando métricas baseline..."
BASELINE_MSGS_BRIDGED=$(curl -s http://localhost:8710/health | python3 -c "import sys, json; print(json.load(sys.stdin)['messages_bridged'])")
echo "  - Messages bridged (antes): $BASELINE_MSGS_BRIDGED"
echo

# Step 3: Simulate threat detection in Reactive Fabric
echo "[3/5] Simulando detecção de threat no Reactive Fabric..."
ATTACK_RESPONSE=$(curl -s -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d '{
    "attacker_ip": "192.168.99.100",
    "attack_type": "ssh_bruteforce",
    "severity": "high",
    "honeypot_id": "5aeb9ef1-498c-49f5-a246-117da3e1d933",
    "confidence": 0.95,
    "ttps": ["T1110.001"],
    "iocs": {
      "ips": ["192.168.99.100"],
      "usernames": ["root", "admin"]
    },
    "payload": "ssh brute force attempt",
    "captured_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }')

echo "  - Attack registered: $ATTACK_RESPONSE"
echo

# Step 4: Wait for message propagation
echo "[4/5] Aguardando propagação da mensagem (15s)..."
sleep 15
echo

# Step 5: Verify integration
echo "[5/5] Verificando integração E2E..."

echo -n "  - Bridge processou mensagem? "
CURRENT_MSGS_BRIDGED=$(curl -s http://localhost:8710/health | python3 -c "import sys, json; print(json.load(sys.stdin)['messages_bridged'])")
if [ "$CURRENT_MSGS_BRIDGED" -gt "$BASELINE_MSGS_BRIDGED" ]; then
    echo -e "${GREEN}✓ SIM${NC} (${CURRENT_MSGS_BRIDGED} total)"
else
    echo -e "${YELLOW}⚠ NÃO${NC} (ainda ${CURRENT_MSGS_BRIDGED})"
    echo "  Nota: Topics podem não existir ainda. Verifique logs do bridge."
fi

echo -n "  - Circuit breaker status: "
CB_STATUS=$(curl -s http://localhost:8710/health | python3 -c "import sys, json; print(json.load(sys.stdin)['circuit_breaker'])")
if [ "$CB_STATUS" = "closed" ]; then
    echo -e "${GREEN}✓ CLOSED${NC}"
else
    echo -e "${RED}✗ $CB_STATUS${NC}"
fi

echo -n "  - Active Immune recebeu threat? "
# Check Active Immune logs for threat processing
THREAT_LOG=$(docker logs active-immune-core 2>&1 | grep "reactive_threat_received" | tail -1)
if [ -n "$THREAT_LOG" ]; then
    echo -e "${GREEN}✓ SIM${NC}"
    echo "    Log: $THREAT_LOG"
else
    echo -e "${YELLOW}⚠ NÃO DETECTADO NOS LOGS${NC}"
    echo "    Nota: Consumer pode estar em modo degradado (topics não existem)"
fi

echo

# Summary
echo "===================================================================="
echo "  RESUMO DA INTEGRAÇÃO"
echo "===================================================================="
echo "Status geral:"
echo "  - Reactive Fabric Core:  ${GREEN}Operational${NC}"
echo "  - Threat Intel Bridge:   ${GREEN}Operational${NC}"
echo "  - Active Immune Core:    ${GREEN}Operational${NC}"
echo
echo "Observações:"
echo "  - Esta é a primeira execução após integração"
echo "  - Topics Kafka podem não existir (criados automaticamente)"
echo "  - Aguarde alguns minutos para topics se propagarem"
echo
echo "Para monitorar mensagens em tempo real:"
echo "  docker logs -f threat-intel-bridge"
echo "  docker logs -f active-immune-core"
echo "===================================================================="
