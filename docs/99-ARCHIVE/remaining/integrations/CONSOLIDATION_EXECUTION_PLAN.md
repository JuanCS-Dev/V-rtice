# PLANO DE EXECUÇÃO: CONSOLIDAÇÃO TOTAL
**Data:** 2025-10-19  
**Modo:** OPÇÃO C - Consolidação Total  
**Tempo Estimado:** 6-8 horas  
**Autoridade:** Constituição Vértice v2.7 Artigo I Cláusula 3.1  

---

## OBJETIVO

Unificar infraestrutura eliminando duplicação Kafka/Postgres/Redis do sistema imunológico adaptativo, integrando completamente Reactive Fabric → Active Immune Core via Kafka HCL.

---

## ESTADO ATUAL (DIAGNÓSTICO COMPLETO)

### Infraestrutura Detectada

```
PRODUÇÃO (maximus-network):
├── vertice-postgres:5432 (DB: aurora)
├── vertice-redis:6379
├── hcl-kafka:9092 (KRaft mode)
└── rabbitmq:5672

ISOLADO (maximus-immunity-network):
├── maximus-postgres-immunity:5433 (DB: adaptive_immunity)
├── maximus-redis-immunity:6380
├── maximus-kafka-immunity:9096
└── maximus-zookeeper-immunity:2181

ISOLADO (reactive_fabric_dmz):
├── honeypot_ssh:2222
├── honeypot_web:8080
└── honeypot_api:8081
```

### Serviços e Conexões Atuais

| Serviço | Kafka | Postgres | Redis | Status |
|---------|-------|----------|-------|--------|
| `reactive_fabric_core` | ✅ hcl-kafka:9092 | ✅ postgres:5432 | ✅ redis:6379 | Integrado |
| `reactive_fabric_analysis` | ✅ hcl-kafka:9092 | ✅ postgres:5432 | ❌ N/A | Integrado |
| `active_immune_core` | ❌ **SEM KAFKA** | ✅ postgres:5432 | ✅ redis:6379 | Parcial |
| `immunis_*` (5 serviços) | ❌ N/A | ❌ N/A | ❌ N/A | Isolados |

### Causa-Raiz da Fragmentação

1. **Active Immune Core** foi adicionado ao main compose MAS sem Kafka configurado
2. **docker-compose.adaptive-immunity.yml** cria infraestrutura duplicada (nunca integrada)
3. **Zero comunicação** entre Reactive Fabric e Active Immune (topic inexistente)
4. **Serviços Immunis** não estão no main compose (órfãos arquiteturais)

---

## ARQUITETURA CONSOLIDADA (OBJETIVO)

```
┌────────────────────────────────────────────────────────────────┐
│ PRODUÇÃO (maximus-network)                                     │
│                                                                 │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │ HCL-KAFKA   │←───│ REACTIVE     │    │ ACTIVE IMMUNE   │  │
│  │ :9092       │    │ FABRIC CORE  │    │ CORE            │  │
│  │             │    │              │    │                 │  │
│  │ Topics:     │    │ Publica em:  │    │ Consome de:     │  │
│  │ - reactive. │    │ reactive.    │    │ reactive.       │  │
│  │   threats   │    │   threats    │    │   threats       │  │
│  │ - immunis.  │    └──────────────┘    │                 │  │
│  │   cytokines │                         │ Publica em:     │  │
│  └─────────────┘                         │ immunis.        │  │
│         ↑                                │   cytokines     │  │
│         │                                └─────────────────┘  │
│         │                                         ↓            │
│  ┌──────┴──────────────────────────────────────────────────┐ │
│  │ IMMUNIS AGENTS (5 serviços)                             │ │
│  │ - immunis_neutrophil   (primeiras respostas)            │ │
│  │ - immunis_macrofago    (fagocitose)                     │ │
│  │ - immunis_dendritic    (apresentação)                   │ │
│  │ - immunis_cytotoxic_t  (eliminação)                     │ │
│  │ - immunis_treg         (modulação)                      │ │
│  │                                                          │ │
│  │ Consomem: immunis.cytokines.{agent_type}                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ POSTGRES :5432 (DB: aurora)                              │  │
│  │ Schemas:                                                  │  │
│  │ - public (core services)                                  │  │
│  │ - reactive_fabric (attacks, forensics)                    │  │
│  │ - adaptive_immunity (apvs, patches, agents)               │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │ REDIS :6379                                               │  │
│  │ DB Namespaces:                                            │  │
│  │ - 0: Core services cache                                  │  │
│  │ - 1: Reactive Fabric cache                                │  │
│  │ - 2: Adaptive Immunity cache                              │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ ISOLADO (reactive_fabric_dmz)                                  │
│  [Honeypots] → [Forensics Volume] → Reactive Fabric Core      │
│  (one-way flow: honeypots NÃO acessam produção)               │
└────────────────────────────────────────────────────────────────┘
```

---

## FASES DE EXECUÇÃO

### FASE 1: ADICIONAR KAFKA AO ACTIVE IMMUNE CORE (30min)

**Objetivo:** Conectar Active Immune Core ao Kafka HCL.

**Passos:**

1.1. Atualizar `docker-compose.yml`:
```yaml
active_immune_core:
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092  # ← NOVA
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/aurora
    - REDIS_URL=redis://redis:6379/2  # namespace 2 (adaptive immunity)
  depends_on:
    - hcl-kafka  # ← NOVA DEPENDÊNCIA
```

1.2. Validar config:
```bash
docker compose config | grep -A10 "active_immune_core"
```

1.3. Rebuild e restart:
```bash
docker compose up -d --build active_immune_core
docker compose logs -f active_immune_core | grep -i kafka
```

1.4. Health check:
```bash
curl http://localhost:8200/health | jq '.dependencies.kafka'
# Esperado: {"status": "healthy", "brokers": ["hcl-kafka:9092"]}
```

**Critério de Sucesso:**
- ✅ Active Immune Core conectado ao Kafka HCL
- ✅ Health check passa
- ✅ Logs não mostram erros de conexão

---

### FASE 2: CRIAR SCHEMA ADAPTIVE_IMMUNITY NO POSTGRES PRINCIPAL (40min)

**Objetivo:** Migrar dados do postgres-immunity → postgres principal.

**Passos:**

2.1. Criar migration script:
```sql
-- /home/juan/vertice-dev/backend/migrations/005_create_adaptive_immunity_schema.sql

-- Criar schema
CREATE SCHEMA IF NOT EXISTS adaptive_immunity;

-- Grant permissions
GRANT ALL ON SCHEMA adaptive_immunity TO postgres;
GRANT USAGE ON SCHEMA adaptive_immunity TO vertice;

-- Tabelas APV (Anomaly Patch Vectors)
CREATE TABLE IF NOT EXISTS adaptive_immunity.apvs (
    id SERIAL PRIMARY KEY,
    apv_signature TEXT NOT NULL UNIQUE,
    patch_code TEXT NOT NULL,
    vulnerability_pattern TEXT NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score BETWEEN 0 AND 1),
    deployment_status VARCHAR(20) DEFAULT 'pending' CHECK (deployment_status IN ('pending', 'deployed', 'reverted', 'deprecated')),
    created_at TIMESTAMP DEFAULT NOW(),
    deployed_at TIMESTAMP,
    reverted_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id) ON DELETE SET NULL
);

-- Tabelas Agents
CREATE TABLE IF NOT EXISTS adaptive_immunity.agents (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_type VARCHAR(30) NOT NULL CHECK (agent_type IN ('neutrophil', 'macrofago', 'dendritic', 'cytotoxic_t', 'treg')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'compromised', 'healing')),
    activation_level FLOAT DEFAULT 0.5 CHECK (activation_level BETWEEN 0 AND 1),
    last_seen TIMESTAMP DEFAULT NOW(),
    metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabelas Cytokines (mensagens inter-agentes)
CREATE TABLE IF NOT EXISTS adaptive_immunity.cytokines (
    id SERIAL PRIMARY KEY,
    cytokine_type VARCHAR(50) NOT NULL,
    source_agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id),
    target_agent_id VARCHAR(50),
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    consumed_at TIMESTAMP
);

-- Audit log
CREATE TABLE IF NOT EXISTS adaptive_immunity.audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(50) REFERENCES adaptive_immunity.agents(agent_id),
    apv_id INTEGER REFERENCES adaptive_immunity.apvs(id),
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_apvs_signature ON adaptive_immunity.apvs(apv_signature);
CREATE INDEX IF NOT EXISTS idx_apvs_status ON adaptive_immunity.apvs(deployment_status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON adaptive_immunity.agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON adaptive_immunity.agents(status);
CREATE INDEX IF NOT EXISTS idx_cytokines_target ON adaptive_immunity.cytokines(target_agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_event ON adaptive_immunity.audit_log(event_type);
```

2.2. Executar migration:
```bash
docker compose exec postgres psql -U postgres -d aurora -f /migrations/005_create_adaptive_immunity_schema.sql
```

2.3. Validar schema:
```bash
docker compose exec postgres psql -U postgres -d aurora -c "\dn" | grep adaptive_immunity
docker compose exec postgres psql -U postgres -d aurora -c "\dt adaptive_immunity.*"
```

2.4. Atualizar Active Immune Core config:
```python
# backend/services/active_immune_core/models/base.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()
Base.metadata.schema = "adaptive_immunity"  # ← NOVA
```

**Critério de Sucesso:**
- ✅ Schema `adaptive_immunity` criado
- ✅ 4 tabelas criadas (apvs, agents, cytokines, audit_log)
- ✅ Indexes criados
- ✅ Active Immune Core usa novo schema

---

### FASE 3: CRIAR TOPICS KAFKA (20min)

**Objetivo:** Criar topics para comunicação Reactive Fabric → Active Immune.

**Passos:**

3.1. Criar topics:
```bash
docker compose exec hcl-kafka /opt/kafka/bin/kafka-topics.sh \
  --create --bootstrap-server localhost:9092 \
  --topic reactive.threats \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=604800000  # 7 dias

docker compose exec hcl-kafka /opt/kafka/bin/kafka-topics.sh \
  --create --bootstrap-server localhost:9092 \
  --topic immunis.cytokines.broadcast \
  --partitions 3 \
  --replication-factor 1

# Topics específicos por agente
for agent in neutrophil macrofago dendritic cytotoxic_t treg; do
  docker compose exec hcl-kafka /opt/kafka/bin/kafka-topics.sh \
    --create --bootstrap-server localhost:9092 \
    --topic immunis.cytokines.$agent \
    --partitions 1 \
    --replication-factor 1
done
```

3.2. Validar topics:
```bash
docker compose exec hcl-kafka /opt/kafka/bin/kafka-topics.sh \
  --list --bootstrap-server localhost:9092 | grep -E "reactive|immunis"
```

3.3. Testar publicação/consumo:
```bash
# Publicar mensagem teste
echo '{"threat_type":"ssh_bruteforce","severity":"high","source_ip":"1.2.3.4"}' | \
docker compose exec -T hcl-kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic reactive.threats

# Consumir mensagem
docker compose exec hcl-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic reactive.threats \
  --from-beginning \
  --max-messages 1
```

**Critério de Sucesso:**
- ✅ 7 topics criados (1 reactive + 6 immunis)
- ✅ Mensagem de teste publicada e consumida
- ✅ Retention configurada (7 dias)

---

### FASE 4: INTEGRAR REACTIVE FABRIC → KAFKA (45min)

**Objetivo:** Reactive Fabric publica threats no topic `reactive.threats`.

**Passos:**

4.1. Atualizar `reactive_fabric_core/kafka_producer.py`:
```python
from aiokafka import AIOKafkaProducer
import json
import logging

logger = logging.getLogger(__name__)

class ThreatPublisher:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.topic = "reactive.threats"
    
    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            compression_type='gzip',
            acks='all'
        )
        await self.producer.start()
        logger.info(f"ThreatPublisher connected to {self.bootstrap_servers}")
    
    async def stop(self):
        if self.producer:
            await self.producer.stop()
    
    async def publish_threat(self, threat: dict):
        """Publica threat detectado para o sistema imunológico"""
        try:
            await self.producer.send_and_wait(
                self.topic,
                value=threat,
                key=threat.get('threat_id', '').encode('utf-8')
            )
            logger.info(f"Threat published: {threat['threat_type']} from {threat['source_ip']}")
        except Exception as e:
            logger.error(f"Failed to publish threat: {e}")
            raise
```

4.2. Integrar no `main.py`:
```python
from .kafka_producer import ThreatPublisher

threat_publisher = ThreatPublisher(bootstrap_servers=settings.kafka_brokers)

@app.on_event("startup")
async def startup():
    await threat_publisher.start()

@app.on_event("shutdown")
async def shutdown():
    await threat_publisher.stop()

@app.post("/api/v1/attacks")
async def report_attack(attack: AttackEvent):
    # ... lógica existente ...
    
    # Publicar no Kafka
    threat = {
        "threat_id": attack.id,
        "threat_type": attack.attack_type,
        "severity": attack.severity,
        "source_ip": attack.source_ip,
        "honeypot_id": attack.honeypot_id,
        "timestamp": attack.timestamp.isoformat(),
        "metadata": attack.metadata
    }
    await threat_publisher.publish_threat(threat)
    
    return {"status": "attack_recorded", "threat_id": attack.id}
```

4.3. Rebuild e restart:
```bash
docker compose up -d --build reactive_fabric_core
docker compose logs -f reactive_fabric_core | grep -i kafka
```

4.4. Testar E2E:
```bash
# Simular ataque
curl -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "192.168.1.100",
    "attack_type": "ssh_bruteforce",
    "severity": "high",
    "honeypot_id": "ssh_001"
  }'

# Verificar topic
docker compose exec hcl-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic reactive.threats \
  --from-beginning \
  --max-messages 1
```

**Critério de Sucesso:**
- ✅ Reactive Fabric conectado ao Kafka
- ✅ Threats publicados no topic `reactive.threats`
- ✅ Mensagens consumíveis via console consumer
- ✅ Zero erros nos logs

---

### FASE 5: INTEGRAR ACTIVE IMMUNE CORE → KAFKA (60min)

**Objetivo:** Active Immune Core consome threats e orquestra agentes.

**Passos:**

5.1. Criar `active_immune_core/orchestration/kafka_consumer.py`:
```python
from aiokafka import AIOKafkaConsumer
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ThreatConsumer:
    def __init__(self, bootstrap_servers: str, group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.topic = "reactive.threats"
        self.running = False
    
    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True
        )
        await self.consumer.start()
        logger.info(f"ThreatConsumer subscribed to {self.topic}")
        self.running = True
    
    async def stop(self):
        self.running = False
        if self.consumer:
            await self.consumer.stop()
    
    async def consume(self, callback):
        """Consome threats e chama callback para processar"""
        async for message in self.consumer:
            if not self.running:
                break
            
            threat = message.value
            logger.info(f"Received threat: {threat['threat_type']} from {threat['source_ip']}")
            
            try:
                await callback(threat)
            except Exception as e:
                logger.error(f"Failed to process threat: {e}")
```

5.2. Atualizar `active_immune_core/orchestration/defense_orchestrator.py`:
```python
from .kafka_consumer import ThreatConsumer
from .kafka_producer import CytokineProducer

class DefenseOrchestrator:
    def __init__(self, settings):
        self.threat_consumer = ThreatConsumer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id="active_immune_core"
        )
        self.cytokine_producer = CytokineProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers
        )
    
    async def start(self):
        await self.threat_consumer.start()
        await self.cytokine_producer.start()
        asyncio.create_task(self.threat_consumer.consume(self.process_threat))
    
    async def stop(self):
        await self.threat_consumer.stop()
        await self.cytokine_producer.stop()
    
    async def process_threat(self, threat: dict):
        """Analisa threat e orquestra resposta imunológica"""
        severity = threat['severity']
        threat_type = threat['threat_type']
        
        # Estratégia de resposta baseada em severity
        if severity == "critical":
            # Ativar Neutrófilos (resposta rápida) + Cytotoxic T (eliminação)
            await self.activate_neutrophils(threat)
            await self.activate_cytotoxic_t(threat)
        elif severity == "high":
            # Ativar Macrófagos (fagocitose) + Dendritic (apresentação)
            await self.activate_macrofagos(threat)
            await self.activate_dendritic(threat)
        else:
            # Apenas log + Treg (modulação)
            await self.activate_treg(threat)
        
        logger.info(f"Defense orchestration complete for threat {threat['threat_id']}")
    
    async def activate_neutrophils(self, threat: dict):
        """Envia citocina para Neutrófilos"""
        cytokine = {
            "type": "activate_neutrophil",
            "threat_id": threat['threat_id'],
            "source_ip": threat['source_ip'],
            "action": "block_ip",
            "priority": "high"
        }
        await self.cytokine_producer.publish("immunis.cytokines.neutrophil", cytokine)
    
    # ... métodos para outros agentes ...
```

5.3. Integrar no `main.py`:
```python
from .orchestration.defense_orchestrator import DefenseOrchestrator

orchestrator = DefenseOrchestrator(settings)

@app.on_event("startup")
async def startup():
    await orchestrator.start()
    logger.info("Active Immune Core orchestrator started")

@app.on_event("shutdown")
async def shutdown():
    await orchestrator.stop()
```

5.4. Rebuild e restart:
```bash
docker compose up -d --build active_immune_core
docker compose logs -f active_immune_core | grep -E "ThreatConsumer|Defense"
```

5.5. Testar E2E (Reactive → Active Immune):
```bash
# 1. Publicar threat no Reactive Fabric
curl -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d '{
    "source_ip": "evil.hacker.com",
    "attack_type": "sql_injection",
    "severity": "critical",
    "honeypot_id": "web_001"
  }'

# 2. Aguardar processamento (5s)
sleep 5

# 3. Verificar logs do Active Immune
docker compose logs active_immune_core | tail -20

# 4. Verificar cytokines publicadas
docker compose exec hcl-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic immunis.cytokines.neutrophil \
  --from-beginning \
  --max-messages 1
```

**Critério de Sucesso:**
- ✅ Active Immune consome de `reactive.threats`
- ✅ Threats processados e estratégia definida
- ✅ Cytokines publicadas nos topics de agentes
- ✅ Logs mostram orquestração completa

---

### FASE 6: ADICIONAR SERVIÇOS IMMUNIS AO MAIN COMPOSE (60min)

**Objetivo:** Integrar 5 serviços Immunis para responder a cytokines.

**Passos:**

6.1. Atualizar `docker-compose.yml` (adicionar 5 serviços):
```yaml
  immunis_neutrophil:
    build: ./backend/services/immunis_neutrophil_service
    container_name: immunis-neutrophil
    ports:
      - "8313:8013"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/aurora
      - REDIS_URL=redis://redis:6379/2
      - AGENT_TYPE=neutrophil
      - CYTOKINE_TOPIC=immunis.cytokines.neutrophil
    depends_on:
      - hcl-kafka
      - postgres
      - redis
      - active_immune_core
    networks:
      - maximus-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8013/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  immunis_macrofago:
    build: ./backend/services/immunis_macrofago_service
    container_name: immunis-macrofago
    ports:
      - "8314:8014"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=hcl-kafka:9092
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/aurora
      - REDIS_URL=redis://redis:6379/2
      - AGENT_TYPE=macrofago
      - CYTOKINE_TOPIC=immunis.cytokines.macrofago
    depends_on:
      - hcl-kafka
      - postgres
      - redis
      - active_immune_core
    networks:
      - maximus-network
    restart: unless-stopped

  # ... (dendritic, cytotoxic_t, treg - estrutura idêntica)
```

6.2. Implementar consumer de cytokines em cada agente (exemplo: neutrophil):
```python
# backend/services/immunis_neutrophil_service/kafka_consumer.py

from aiokafka import AIOKafkaConsumer
import json
import logging

logger = logging.getLogger(__name__)

class CytokineConsumer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
    
    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=f"immunis_neutrophil_{self.topic}",
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        await self.consumer.start()
        logger.info(f"Neutrophil consumer subscribed to {self.topic}")
    
    async def consume(self, callback):
        async for message in self.consumer:
            cytokine = message.value
            logger.info(f"Neutrophil received cytokine: {cytokine['type']}")
            await callback(cytokine)

# main.py
cytokine_consumer = CytokineConsumer(
    bootstrap_servers=settings.kafka_bootstrap_servers,
    topic=settings.cytokine_topic
)

async def process_cytokine(cytokine: dict):
    if cytokine['type'] == 'activate_neutrophil':
        source_ip = cytokine['source_ip']
        # Executar ação de bloqueio
        await block_ip(source_ip)
        logger.info(f"Neutrophil blocked IP: {source_ip}")

@app.on_event("startup")
async def startup():
    await cytokine_consumer.start()
    asyncio.create_task(cytokine_consumer.consume(process_cytokine))
```

6.3. Build e start todos os agentes:
```bash
docker compose up -d --build \
  immunis_neutrophil \
  immunis_macrofago \
  immunis_dendritic \
  immunis_cytotoxic_t \
  immunis_treg
```

6.4. Validar health:
```bash
for port in 8313 8314 8315 8316 8317; do
  curl -s http://localhost:$port/health | jq '.status'
done
```

**Critério de Sucesso:**
- ✅ 5 serviços Immunis rodando
- ✅ Conectados ao Kafka HCL
- ✅ Consumindo de topics específicos
- ✅ Health checks passando

---

### FASE 7: TESTE E2E COMPLETO (45min)

**Objetivo:** Validar fluxo completo Honeypot → Reactive → Kafka → Active Immune → Agentes.

**Passos:**

7.1. Script de teste E2E:
```bash
#!/bin/bash
# tests/integration/test_reactive_immune_e2e.sh

set -e

echo "=== TESTE E2E: INTEGRAÇÃO REACTIVE FABRIC ↔ ADAPTIVE IMMUNITY ==="

# 1. Verificar todos os serviços UP
echo "[1/6] Verificando serviços..."
services=(
  "reactive-fabric-core:8600"
  "reactive-fabric-analysis:8601"
  "active-immune-core:8200"
  "immunis-neutrophil:8313"
  "immunis-macrofago:8314"
)

for service_port in "${services[@]}"; do
  service=$(echo $service_port | cut -d: -f1)
  port=$(echo $service_port | cut -d: -f2)
  status=$(curl -s http://localhost:$port/health | jq -r '.status')
  if [ "$status" != "healthy" ]; then
    echo "❌ FALHA: $service não está healthy (status: $status)"
    exit 1
  fi
  echo "  ✅ $service: healthy"
done

# 2. Limpar topics (mensagens antigas)
echo "[2/6] Limpando topics..."
docker compose exec -T hcl-kafka /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --entity-type topics \
  --entity-name reactive.threats \
  --alter --add-config retention.ms=1000
sleep 2

# 3. Publicar ataque simulado (critical)
echo "[3/6] Publicando ataque crítico..."
ATTACK_ID=$(uuidgen)
curl -X POST http://localhost:8600/api/v1/attacks \
  -H "Content-Type: application/json" \
  -d "{
    \"attack_id\": \"$ATTACK_ID\",
    \"source_ip\": \"192.168.66.6\",
    \"attack_type\": \"ransomware_attempt\",
    \"severity\": \"critical\",
    \"honeypot_id\": \"api_001\",
    \"metadata\": {\"payload\": \"WannaCry variant detected\"}
  }"

# 4. Aguardar propagação
echo "[4/6] Aguardando propagação (15s)..."
sleep 15

# 5. Verificar se threat chegou no Active Immune
echo "[5/6] Verificando Active Immune Core..."
threats_count=$(curl -s http://localhost:8200/api/v1/threats | jq '.total')
if [ "$threats_count" -lt 1 ]; then
  echo "❌ FALHA: Nenhum threat recebido no Active Immune"
  exit 1
fi
echo "  ✅ Threats recebidos: $threats_count"

# 6. Verificar ações dos agentes (logs)
echo "[6/6] Verificando ações dos agentes..."
neutrophil_actions=$(docker compose logs immunis_neutrophil --since 30s | grep -c "blocked IP" || true)
cytotoxic_actions=$(docker compose logs immunis_cytotoxic_t --since 30s | grep -c "eliminated threat" || true)

if [ "$neutrophil_actions" -lt 1 ]; then
  echo "  ⚠️ WARNING: Neutrophil não executou ação (esperado para critical)"
fi
echo "  ✅ Neutrophil actions: $neutrophil_actions"
echo "  ✅ Cytotoxic T actions: $cytotoxic_actions"

# 7. Métricas Kafka
echo "[7/6] Métricas Kafka..."
reactive_msgs=$(docker compose exec -T hcl-kafka /opt/kafka/bin/kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic reactive.threats | tail -1 | cut -d: -f3)
echo "  ✅ Mensagens em reactive.threats: $reactive_msgs"

echo ""
echo "=== ✅ INTEGRAÇÃO E2E VALIDADA COM SUCESSO ==="
echo "Fluxo completo funcional: Honeypot → Reactive Fabric → Kafka → Active Immune → Agentes"
```

7.2. Executar teste:
```bash
chmod +x tests/integration/test_reactive_immune_e2e.sh
./tests/integration/test_reactive_immune_e2e.sh
```

7.3. Documentar métricas:
```bash
# Capturar métricas finais
docker compose exec hcl-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group active_immune_core > docs/integrations/kafka_consumer_groups.txt

docker compose ps --format json | jq -r '.[] | select(.Name | contains("immun") or contains("reactive")) | "\(.Name): \(.Status)"' \
  > docs/integrations/services_status.txt
```

**Critério de Sucesso:**
- ✅ Teste E2E passa sem erros
- ✅ Threat propagado em <15s
- ✅ Agentes executam ações
- ✅ Métricas Kafka registradas

---

### FASE 8: DEPRECAR docker-compose.adaptive-immunity.yml (20min)

**Objetivo:** Remover infraestrutura duplicada.

**Passos:**

8.1. Parar serviços isolados:
```bash
docker compose -f docker-compose.adaptive-immunity.yml down -v
```

8.2. Backup do arquivo:
```bash
mv docker-compose.adaptive-immunity.yml docker-compose.adaptive-immunity.yml.deprecated
```

8.3. Adicionar note de depreciação:
```bash
cat > docker-compose.adaptive-immunity.yml.deprecated << 'EOF'
# DEPRECATED: 2025-10-19
# Este arquivo foi consolidado no docker-compose.yml principal.
# Infraestrutura agora unificada:
# - Kafka: hcl-kafka:9092
# - Postgres: postgres:5432 (schema: adaptive_immunity)
# - Redis: redis:6379 (DB: 2)
#
# Serviços migrados:
# - active_immune_core
# - immunis_neutrophil
# - immunis_macrofago
# - immunis_dendritic
# - immunis_cytotoxic_t
# - immunis_treg
#
# Ver: /docs/integrations/CONSOLIDATION_EXECUTION_PLAN.md
EOF
```

8.4. Atualizar README:
```bash
cat >> README.md << 'EOF'

## Sistema Imunológico Adaptativo

O sistema imunológico adaptativo (Oráculo-Eureka) está integrado ao compose principal.

**Serviços:**
- `active_immune_core` (porta 8200): Orquestrador central
- `immunis_neutrophil` (porta 8313): Resposta rápida
- `immunis_macrofago` (porta 8314): Fagocitose
- `immunis_dendritic` (porta 8315): Apresentação de antígenos
- `immunis_cytotoxic_t` (porta 8316): Eliminação de ameaças
- `immunis_treg` (porta 8317): Modulação imunológica

**Integração:**
- Threats detectados pelo Reactive Fabric são publicados em `reactive.threats`
- Active Immune Core consome e orquestra resposta via cytokines
- Agentes Immunis executam ações específicas

Ver: `/docs/integrations/CONSOLIDATION_EXECUTION_PLAN.md`
EOF
```

**Critério de Sucesso:**
- ✅ docker-compose.adaptive-immunity.yml depreciado
- ✅ Volumes antigos removidos
- ✅ README atualizado
- ✅ Sistema funcionando com infraestrutura unificada

---

## ROLLBACK PLAN

Se algo falhar criticamente:

```bash
# 1. Parar todos os serviços afetados
docker compose stop active_immune_core immunis_neutrophil immunis_macrofago immunis_dendritic immunis_cytotoxic_t immunis_treg reactive_fabric_core reactive_fabric_analysis

# 2. Reverter docker-compose.yml
git checkout docker-compose.yml

# 3. Restaurar docker-compose.adaptive-immunity.yml
git checkout docker-compose.adaptive-immunity.yml

# 4. Restartar com infraestrutura antiga
docker compose -f docker-compose.adaptive-immunity.yml up -d
docker compose up -d reactive_fabric_core reactive_fabric_analysis

# 5. Validar estado anterior
curl http://localhost:8600/health
curl http://localhost:8601/health
```

**Tempo estimado de rollback:** 10 minutos

---

## MÉTRICAS DE SUCESSO FINAL

| Métrica | Antes | Depois | Status |
|---------|-------|--------|--------|
| Infraestrutura Kafka | 2x (HCL + Immunity) | 1x (HCL) | ✅ |
| Infraestrutura Postgres | 2x (5432 + 5433) | 1x (5432 schemas) | ✅ |
| Infraestrutura Redis | 2x (6379 + 6380) | 1x (6379 namespaces) | ✅ |
| Serviços Immunis no main compose | 0/5 | 5/5 | ✅ |
| Integração Reactive → Immune | ❌ 0% | ✅ 100% | ✅ |
| Latência de propagação threat | N/A | <15s | ✅ |
| Taxa de sucesso E2E | N/A | >99% | ✅ |
| Docker containers totais | ~90 | ~85 (-5) | ✅ |
| Memória economizada | N/A | ~2GB | ✅ |

---

## RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Active Immune falhar ao conectar Kafka | BAIXA | ALTO | Health check + restart policy + logs detalhados |
| Migration SQL corromper dados | BAIXA | CRÍTICO | Backup do Postgres ANTES da migration + dry-run |
| Topics Kafka não criados corretamente | MÉDIA | MÉDIO | Validação explícita após criação + script idempotente |
| Agentes Immunis não consumirem cytokines | MÉDIA | ALTO | Testes unitários + teste E2E + monitoring |
| Rollback parcial deixar sistema inconsistente | BAIXA | ALTO | Rollback completo (all-or-nothing) + checklist |

---

## CRONOGRAMA

| Fase | Duração | Hora Início | Hora Fim |
|------|---------|-------------|----------|
| FASE 1: Kafka no Active Immune | 30min | 00:00 | 00:30 |
| FASE 2: Schema Postgres | 40min | 00:30 | 01:10 |
| FASE 3: Topics Kafka | 20min | 01:10 | 01:30 |
| FASE 4: Reactive → Kafka | 45min | 01:30 | 02:15 |
| FASE 5: Active Immune → Kafka | 60min | 02:15 | 03:15 |
| FASE 6: Serviços Immunis | 60min | 03:15 | 04:15 |
| FASE 7: Teste E2E | 45min | 04:15 | 05:00 |
| FASE 8: Deprecar compose antigo | 20min | 05:00 | 05:20 |
| **TOTAL** | **5h20min** | - | - |

**Buffer para imprevistos:** +2h  
**Tempo total seguro:** **7-8 horas**

---

## PRÓXIMOS PASSOS

1. ✅ **Arquiteto-Chefe aprovou OPÇÃO C** (Consolidação Total)
2. ⏳ **Executar FASE 1** (adicionar Kafka ao Active Immune Core)
3. ⏳ Checkpoint após cada fase
4. ⏳ Documentar métricas em `/docs/integrations/INTEGRATION_METRICS.md`
5. ⏳ Após 100% → Pull request + revisão de código

---

**Executor Tático Backend pronto para iniciar FASE 1.**  
**Aguardando comando GO do Arquiteto-Chefe.**
