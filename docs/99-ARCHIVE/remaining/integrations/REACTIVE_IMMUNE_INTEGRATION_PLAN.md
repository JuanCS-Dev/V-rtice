# PLANO DE INTEGRAÇÃO: Reactive Fabric ↔ Sistema Imunológico

**Data:** 2025-10-19  
**Executor:** Tático Backend  
**Autoridade:** Constituição Vértice v2.7  
**Objetivo:** Integrar completamente Reactive Fabric e Sistema Imunológico Adaptativo preservando isolamento de segurança

---

## CONTEXTO SISTÊMICO

### Arquitetura Atual (Estado Fragmentado)

```
┌─────────────────────────────────────────────────────────────┐
│ PRODUÇÃO (vertice-network)                                  │
│                                                              │
│  [API Gateway] [Auth] [OSINT] [NLP] ...                    │
│       ↑         ↑        ↑                                   │
│       └─────────┴────────┘ (comunicação interna)           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ISOLADO: Reactive Fabric (reactive_fabric_dmz)              │
│                                                              │
│  [Honeypot SSH] [Honeypot Web] [Honeypot API]              │
│         ↓ (forensics volume)                                │
│  [Reactive Core] [Analysis Service]                         │
│         ↓ (kafka)                                            │
│  [❌ SEM CONEXÃO COM PRODUÇÃO]                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ISOLADO: Adaptive Immunity (maximus-immunity)               │
│                                                              │
│  [Kafka-Immunity] [Postgres-Immunity] [Redis-Immunity]     │
│  [Zookeeper-Immunity]                                       │
│         ↓                                                    │
│  [Adaptive Immune Service] [AI Immune Service]              │
│  [❌ Active Immune Core - AUSENTE no main compose]         │
└─────────────────────────────────────────────────────────────┘
```

### Causa-Raiz da Fragmentação

1. **3 Docker Compose separados** sem bridge de networks
2. **Active Immune Core** não está no docker-compose.yml principal
3. **Infraestrutura duplicada** (2x Kafka, 2x Postgres, 2x Redis)
4. **Zero comunicação** entre Reactive Fabric e Immune System
5. **Threat intelligence** gerada pelo Reactive Fabric não chega aos agentes imunológicos

---

## VISÃO INTEGRADA (Estado Objetivo)

```
┌─────────────────────────────────────────────────────────────────────┐
│ PRODUÇÃO (vertice-network)                                          │
│                                                                      │
│  [API Gateway] [Auth] [OSINT] [NLP] ...                            │
│       ↑                                                              │
│  [ACTIVE IMMUNE CORE] ← orquestra agentes, recebe threats          │
│       ↑                                                              │
│  [AI Immune] [Adaptive Immune] ← executam defesas                   │
└───────────────────────────────────────────────────────────────────┬┘
                                                                      │
                     ┌────────────────────────────────────────────┐  │
                     │ KAFKA BRIDGE (threat-intel topic)          │ ←┘
                     │ - Reactive Fabric publica threats          │
                     │ - Immune System consome threats             │
                     │ - Circuit breaker para falhas               │
                     └────────────────────────────────────────────┘
                                                                      ↑
┌─────────────────────────────────────────────────────────────────┐  │
│ ISOLADO: Reactive Fabric (reactive_fabric_dmz)                  │  │
│                                                                  │  │
│  [Honeypots] → [Forensics] → [Analysis] → [Reactive Core]      │  │
│                                                  ↓               │  │
│                                          [Kafka Producer] ───────┴──┘
│                                          (publica para prod)        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## METODOLOGIA TÉCNICA (Pesquisa Web 2024/2025)

### Padrões Identificados

**1. Network Bridge Controlado**
- Conectar networks isoladas via service específico (bridge)
- Bridge tem acesso a ambas as networks
- Implementa circuit breaker e rate limiting
- Referência: [Docker Microservices Patterns 2024]

**2. Event-Driven Integration**
- Reactive Fabric publica eventos em Kafka
- Immune System consome via subscriber pattern
- Desacoplamento total (producer não conhece consumer)
- Referência: [Event-Driven Microservices Resilience]

**3. Shared Infrastructure Consolidation**
- Eliminar Kafka/Postgres duplicados
- Usar infra principal com namespacing (databases separados)
- Economia de recursos + simplicidade operacional
- Referência: [Docker Compose Optimization 2025]

**4. Service Mesh Health Checks**
- Healthchecks em todas as pontas
- Prometheus metrics para observabilidade
- Circuit breaker automático em falhas
- Referência: [Resilient Microservices Architecture]

---

## OPÇÕES DE IMPLEMENTAÇÃO

### OPÇÃO A: Bridge Service (Recomendada - Mais Segura)

**Descrição:** Criar serviço intermediário `threat-intel-bridge` que conecta as duas redes de forma controlada.

**Vantagens:**
- ✅ Mantém isolamento de segurança (honeypots não acessam produção diretamente)
- ✅ Permite auditoria completa de mensagens (bridge registra tudo)
- ✅ Circuit breaker nativo (bridge pode parar se immune system falhar)
- ✅ Zero mudanças nos serviços existentes

**Desvantagens:**
- ⚠️ Adiciona um hop extra (latência +5-10ms)
- ⚠️ Ponto único de falha (mitigado com restart policy)

**Implementação:**
```yaml
# docker-compose.yml
services:
  threat-intel-bridge:
    build: ./backend/services/threat_intel_bridge
    networks:
      - vertice-network          # acessa Immune System
      - reactive_fabric_bridge   # acessa Reactive Fabric
    environment:
      - KAFKA_REACTIVE_FABRIC=reactive-fabric-core:9092
      - KAFKA_IMMUNE_SYSTEM=kafka:9092
      - CIRCUIT_BREAKER_THRESHOLD=10
    depends_on:
      - kafka
      - reactive_fabric_core
```

**Fluxo:**
1. Reactive Fabric publica em Kafka local (porta 9092)
2. Bridge subscreve Kafka do Reactive Fabric
3. Bridge valida + enriquece mensagem
4. Bridge publica em Kafka principal (produção)
5. Active Immune Core consome de Kafka principal

---

### OPÇÃO B: Shared Kafka (Mais Simples)

**Descrição:** Reactive Fabric e Immune System usam o mesmo Kafka (infra principal).

**Vantagens:**
- ✅ Mais simples (sem bridge service)
- ✅ Menor latência
- ✅ Menos componentes para gerenciar

**Desvantagens:**
- ⚠️ Reactive Fabric precisa acessar network de produção diretamente
- ⚠️ Quebra isolamento de segurança (risco: honeypot comprometido → acesso a Kafka prod)
- ⚠️ Kafka único = ponto único de falha

**Implementação:**
```yaml
# docker-compose.yml
services:
  reactive_fabric_core:
    networks:
      - reactive_fabric_dmz
      - vertice-network  # ← NOVA NETWORK (risco)
    environment:
      - KAFKA_BROKERS=kafka:9092  # usa Kafka principal
```

**Fluxo:**
1. Reactive Fabric publica diretamente em Kafka principal
2. Active Immune Core consome de Kafka principal

**⚠️ RISCO:** Honeypot comprometido pode enviar mensagens maliciosas para Kafka de produção.

---

### OPÇÃO C: Consolidação Total (Mais Eficiente, Mais Complexa)

**Descrição:** Unificar toda a infraestrutura (1x Kafka, 1x Postgres com schemas separados, 1x Redis com namespaces).

**Vantagens:**
- ✅ Máxima eficiência de recursos
- ✅ Gestão simplificada (um único stack)
- ✅ Observabilidade centralizada

**Desvantagens:**
- ⚠️ Requer refatoração de TODOS os serviços
- ⚠️ Risco de quebrar funcionamento atual
- ⚠️ Migração de dados complexa
- ⚠️ Tempo estimado: 6-8 horas (vs. 2h da Opção A)

---

## RECOMENDAÇÃO: OPÇÃO A (Bridge Service)

**Justificativa:**
1. **Segurança:** Mantém isolamento de honeypots
2. **Compatibilidade:** Zero mudanças em serviços existentes
3. **Observabilidade:** Bridge pode logar tudo
4. **Conformidade:** Alinha com Artigo III (Zero Trust) da Constituição

**Estimativa:** 2-3 horas de implementação + 1 hora de validação

---

## PLANO DE EXECUÇÃO (OPÇÃO A)

### FASE 1: Adicionar Active Immune Core ao docker-compose.yml principal

**Objetivo:** Tornar Active Immune Core parte da orquestração principal.

```yaml
# docker-compose.yml (adicionar)
active_immune_core:
  build: ./backend/services/active_immune_core
  container_name: active-immune-core
  ports:
    - "8700:8000"
  environment:
    - DATABASE_URL=postgresql://vertice:vertice_pass@postgres:5432/vertice
    - KAFKA_BROKERS=kafka:9092
    - REDIS_URL=redis://redis:6379/1  # namespace 1
  networks:
    - vertice-network
  depends_on:
    - postgres
    - kafka
    - redis
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Validação:**
```bash
docker compose up -d active_immune_core
docker compose ps active_immune_core
curl http://localhost:8700/health
```

---

### FASE 2: Criar Threat Intel Bridge Service

**Estrutura:**
```
backend/services/threat_intel_bridge/
├── main.py              # FastAPI app
├── kafka_consumer.py    # Consome de Reactive Fabric
├── kafka_producer.py    # Publica para Immune System
├── circuit_breaker.py   # Lógica de circuit breaker
├── requirements.txt
├── Dockerfile
└── tests/
    └── test_bridge.py
```

**main.py (esqueleto):**
```python
"""
Threat Intelligence Bridge
Conecta Reactive Fabric → Active Immune Core de forma segura
"""

from fastapi import FastAPI
from .kafka_consumer import ReactiveFabricConsumer
from .kafka_producer import ImmuneSystemProducer
from .circuit_breaker import CircuitBreaker

app = FastAPI()

consumer = ReactiveFabricConsumer(brokers="reactive-fabric-core:9092")
producer = ImmuneSystemProducer(brokers="kafka:9092")
breaker = CircuitBreaker(threshold=10, timeout=60)

@app.on_event("startup")
async def startup():
    await consumer.start()
    asyncio.create_task(bridge_messages())

async def bridge_messages():
    """Loop principal: consome mensagens e republica"""
    async for message in consumer.consume("threat-intel"):
        if breaker.is_open():
            logger.warning("Circuit breaker open, skipping message")
            continue
        
        try:
            # Enriquecer/validar mensagem
            enriched = enrich_threat_data(message)
            
            # Publicar para Immune System
            await producer.publish("immune-threats", enriched)
            
            breaker.record_success()
        except Exception as e:
            breaker.record_failure()
            logger.error(f"Bridge failed: {e}")
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**requirements.txt:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
aiokafka==0.10.0
pydantic==2.5.0
structlog==24.1.0
prometheus-client==0.19.0
```

---

### FASE 3: Integrar Bridge no docker-compose.yml

```yaml
# docker-compose.yml (adicionar)
networks:
  reactive_fabric_bridge:
    driver: bridge
    internal: false

services:
  threat_intel_bridge:
    build: ./backend/services/threat_intel_bridge
    container_name: threat-intel-bridge
    ports:
      - "8710:8000"  # metrics/health
    environment:
      - KAFKA_REACTIVE_FABRIC=reactive-fabric-core:9092
      - KAFKA_IMMUNE_SYSTEM=kafka:9092
      - CIRCUIT_BREAKER_THRESHOLD=10
      - CIRCUIT_BREAKER_TIMEOUT=60
      - LOG_LEVEL=INFO
    networks:
      - vertice-network              # acessa Immune System
      - reactive_fabric_bridge       # acessa Reactive Fabric
    depends_on:
      - kafka
      - reactive_fabric_core
      - active_immune_core
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Atualizar reactive_fabric_core para usar nova network
  reactive_fabric_core:
    networks:
      - reactive_fabric_dmz
      - reactive_fabric_bridge  # ← NOVA
```

---

### FASE 4: Conectar Active Immune Core ao Bridge

**Modificar active_immune_core para consumir de Kafka principal:**

```python
# backend/services/active_immune_core/kafka_consumer.py

async def consume_threats():
    """Consome threats do topic 'immune-threats'"""
    consumer = AIOKafkaConsumer(
        'immune-threats',  # ← topic criado pelo bridge
        bootstrap_servers='kafka:9092',
        group_id='active-immune-core',
    )
    
    await consumer.start()
    
    async for message in consumer:
        threat = ThreatIntel.parse_raw(message.value)
        await process_threat(threat)
```

**Adicionar ao main.py:**
```python
@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_threats())
```

---

### FASE 5: Validação E2E

**Test Script:**
```bash
#!/bin/bash
# tests/integration/test_reactive_immune_integration.sh

echo "=== Teste de Integração Reactive Fabric ↔ Immune System ==="

# 1. Verificar serviços UP
echo "[1/5] Verificando serviços..."
docker compose ps reactive_fabric_core | grep "Up (healthy)"
docker compose ps active_immune_core | grep "Up (healthy)"
docker compose ps threat_intel_bridge | grep "Up (healthy)"

# 2. Publicar threat simulado no Reactive Fabric
echo "[2/5] Publicando threat simulado..."
curl -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.100",
    "attack_type": "ssh_bruteforce",
    "severity": "high",
    "honeypot_id": "ssh_001"
  }'

# 3. Aguardar propagação (bridge + kafka)
echo "[3/5] Aguardando propagação (10s)..."
sleep 10

# 4. Verificar se threat chegou no Active Immune Core
echo "[4/5] Verificando recepção no Immune System..."
THREATS=$(curl -s http://localhost:8700/api/v1/threats | jq '.total')

if [ "$THREATS" -gt 0 ]; then
  echo "✅ Threat recebido! Total: $THREATS"
else
  echo "❌ FALHA: Nenhum threat recebido"
  exit 1
fi

# 5. Verificar métricas do bridge
echo "[5/5] Verificando métricas do bridge..."
BRIDGE_MSGS=$(curl -s http://localhost:8710/metrics | grep 'bridge_messages_total' | tail -1)
echo "Bridge messages: $BRIDGE_MSGS"

echo "=== ✅ INTEGRAÇÃO VALIDADA ==="
```

---

## MÉTRICAS DE SUCESSO

### Antes da Integração
- ❌ Reactive Fabric isolado (0 comunicação)
- ❌ Active Immune Core ausente do main compose
- ❌ Threat intel não chega aos agentes
- ❌ 3x infraestrutura duplicada

### Depois da Integração
- ✅ Reactive Fabric → Bridge → Immune System (latência <100ms)
- ✅ Active Immune Core orquestrado no main compose
- ✅ 100% dos threats chegam aos agentes (circuit breaker <1% falhas)
- ✅ Observabilidade completa (Prometheus metrics)
- ✅ Isolamento de segurança preservado (honeypots não acessam prod)
- ✅ Healthchecks 100% passando

---

## RISCOS E MITIGAÇÕES

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Bridge vira ponto único de falha | ALTA | `restart: unless-stopped` + circuit breaker + health checks |
| Latência adicional (bridge hop) | MÉDIA | Otimizar serialização + batch processing |
| Kafka congestion | MÉDIA | Rate limiting no bridge (max 1000 msgs/s) |
| Honeypot comprometido envia spam | ALTA | Bridge valida schema + rate limit por honeypot_id |
| Active Immune Core cai e bridge acumula msgs | MÉDIA | Circuit breaker abre após 10 falhas + backpressure |

---

## ROLLBACK PLAN

Se integração falhar:

```bash
# 1. Parar bridge
docker compose stop threat_intel_bridge

# 2. Remover do compose
git checkout docker-compose.yml

# 3. Restartar serviços
docker compose up -d reactive_fabric_core active_immune_core

# 4. Validar estado anterior
curl http://localhost:8600/health  # Reactive Fabric
curl http://localhost:8700/health  # Active Immune Core (se estiver rodando)
```

**Estado pós-rollback:** Serviços voltam ao estado isolado (sem comunicação).

---

## CRONOGRAMA

| Fase | Duração | Dependências |
|------|---------|--------------|
| FASE 1: Adicionar Active Immune ao main compose | 30min | - |
| FASE 2: Criar Threat Intel Bridge | 1h | FASE 1 |
| FASE 3: Integrar Bridge no compose | 20min | FASE 2 |
| FASE 4: Conectar Active Immune ao Bridge | 30min | FASE 3 |
| FASE 5: Validação E2E | 30min | FASE 4 |
| **TOTAL** | **2h50min** | - |

**Buffer para imprevistos:** +1h  
**Tempo total seguro:** 4 horas

---

## PRÓXIMOS PASSOS

1. **Arquiteto-Chefe aprova OPÇÃO A?** (Bridge Service)
2. Se SIM → Executar FASE 1
3. Checkpoint após cada fase (validar health)
4. Documentar métricas em `/docs/integrations/INTEGRATION_METRICS.md`
5. Após 100% → Deprecar docker-compose.adaptive-immunity.yml (consolidar)

---

**Executor Tático Backend pronto para iniciar.**  
**Aguardando aprovação do Arquiteto-Chefe para FASE 1.**
