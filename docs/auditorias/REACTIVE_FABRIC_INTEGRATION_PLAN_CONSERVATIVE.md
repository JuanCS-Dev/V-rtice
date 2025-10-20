# PLANO DE INTEGRAÇÃO REACTIVE FABRIC - OPÇÃO CONSERVADORA (B)
**Executor:** IA Tático
**Aprovador:** Arquiteto-Chefe Juan
**Modo:** Mínima Invasão + Visão Sistêmica
**Data:** 2025-10-19
**Status:** AGUARDANDO APROVAÇÃO

---

## CONTEXTO - Estado Atual

### Componentes Existentes
1. **Reactive Fabric Core** ✅ Rodando (porta 8600)
2. **Reactive Fabric Analysis** ✅ Rodando (porta 8601)
3. **Adaptive Immune System** ✅ Rodando (porta 8003)
4. **AI Immune System** ✅ Rodando (porta 8214)
5. **API Gateway** ✅ Rodando (porta 8000)

### Problemas Identificados
1. ❌ API Gateway registra rotas mas elas **NÃO aparecem** no OpenAPI
2. ❌ Reactive Core reporta `No module named 'vertice_db'`
3. ❌ Sistema Imune (adaptive/ai) **zero integração** com Reactive Fabric
4. ❌ Arquitetura isolada (composes separados sem bridge funcional)

---

## CAUSA-RAIZ ARQUITETURAL

```
┌─────────────────────────────────────────────────────┐
│ docker-compose.yml (main)                           │
│  ├─ api_gateway (8000)                              │
│  ├─ adaptive_immune_system (8003)                   │
│  └─ ai_immune_system (8214)                         │
└─────────────────────────────────────────────────────┘
              ↕ (PONTE QUEBRADA)
┌─────────────────────────────────────────────────────┐
│ docker-compose.reactive-fabric.yml (isolado)        │
│  ├─ reactive_fabric_core (8600)                     │
│  └─ reactive_fabric_analysis (8601)                 │
└─────────────────────────────────────────────────────┘
```

**O problema:** API Gateway importa `backend.security.offensive.reactive_fabric.api` mas:
- Esse módulo depende de `get_db_session()` que não está disponível no gateway
- Rotas são registradas mas FastAPI falha silenciosamente sem exception
- Sistema Imune não foi arquitetado para consumir dados do Reactive Fabric

---

## OPÇÃO B - INTEGRAÇÃO CONSERVADORA

### Princípios
1. **Mínima invasão:** Não reescrever código existente
2. **Visão sistêmica:** Não quebrar interações existentes (Oráculo-Eureka, etc)
3. **Segurança first:** Manter isolamento de segurança do Reactive Fabric
4. **Validação incremental:** Cada passo é testável isoladamente

---

## FASE 1: FIX DE DEPENDÊNCIAS (30min)

### 1.1 - Corrigir Import `vertice_db` no Reactive Core
**Arquivo:** `backend/services/reactive_fabric_core/collectors/base_collector.py`
**Arquivo:** `backend/services/reactive_fabric_core/main.py`

**Problema:** Código tenta importar `from vertice_db import ...` mas módulo não existe

**Fix:**
```python
# ANTES (quebrado)
from vertice_db import SomeModel

# DEPOIS (correto)
from backend.db.models import SomeModel
# OU (se não usar models do backend)
# Remover import se não for necessário
```

**Validação:**
```bash
docker compose logs reactive_fabric_core --tail=10 | grep "vertice_db"
# Esperado: Nenhum erro
```

**Impacto:** ZERO (fix local, não afeta outros serviços)

---

## FASE 2: BRIDGE API GATEWAY ↔ REACTIVE FABRIC (45min)

### 2.1 - Criar Adapter Pattern no API Gateway
**Novo arquivo:** `backend/api_gateway/adapters/reactive_fabric_adapter.py`

```python
"""
Reactive Fabric Adapter for API Gateway.
Provides RESTful proxy to Reactive Fabric services without tight coupling.
"""
from fastapi import APIRouter, HTTPException
import httpx
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/reactive-fabric",
    tags=["Reactive Fabric"]
)

REACTIVE_CORE_URL = "http://reactive-fabric-core:8600"
REACTIVE_ANALYSIS_URL = "http://reactive-fabric-analysis:8601"


@router.get("/intelligence/reports")
async def get_intelligence_reports(
    limit: int = 10,
    offset: int = 0
):
    """
    Proxy to Reactive Fabric intelligence reports.
    Forwards request to reactive_fabric_core service.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REACTIVE_CORE_URL}/reports",
                params={"limit": limit, "offset": offset},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("reactive_fabric_proxy_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Reactive Fabric service unavailable"
        )


@router.get("/threats/recent")
async def get_recent_threats(limit: int = 10):
    """Proxy to Reactive Fabric threat events."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REACTIVE_CORE_URL}/threats/recent",
                params={"limit": limit},
                timeout=5.0
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error("reactive_fabric_proxy_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Reactive Fabric service unavailable"
        )


@router.get("/health")
async def reactive_fabric_health():
    """Health check for reactive fabric connectivity."""
    core_status = {"service": "reactive_fabric_core", "healthy": False}
    analysis_status = {"service": "reactive_fabric_analysis", "healthy": False}
    
    try:
        async with httpx.AsyncClient() as client:
            # Check core
            core_resp = await client.get(f"{REACTIVE_CORE_URL}/health", timeout=3.0)
            core_status["healthy"] = core_resp.status_code == 200
            
            # Check analysis
            analysis_resp = await client.get(f"{REACTIVE_ANALYSIS_URL}/health", timeout=3.0)
            analysis_status["healthy"] = analysis_resp.status_code == 200
    except Exception as e:
        logger.error("reactive_fabric_health_check_failed", error=str(e))
    
    return {
        "reactive_fabric_bridge": "operational",
        "services": [core_status, analysis_status]
    }
```

### 2.2 - Atualizar `backend/api_gateway/main.py`
```python
# SUBSTITUIR import existente
# from reactive_fabric_integration import register_reactive_fabric_routes

# POR novo adapter
from backend.api_gateway.adapters import reactive_fabric_adapter

# SUBSTITUIR chamada
# register_reactive_fabric_routes(app)

# POR
app.include_router(reactive_fabric_adapter.router)
log.info("reactive_fabric_adapter_registered", mode="proxy_pattern")
```

**Validação:**
```bash
curl http://localhost:8000/api/reactive-fabric/health
# Esperado: {"reactive_fabric_bridge": "operational", ...}

curl http://localhost:8000/openapi.json | grep "reactive-fabric"
# Esperado: Ver rotas reactive-fabric listadas
```

**Impacto:** 
- ✅ API Gateway permanece funcional
- ✅ Não quebra rotas existentes
- ✅ Adiciona apenas 3 endpoints proxy

---

## FASE 3: BRIDGE SISTEMA IMUNE ↔ REACTIVE FABRIC (60min)

### 3.1 - Criar Consumer no Adaptive Immune System
**Novo arquivo:** `backend/services/adaptive_immune_system/integrations/reactive_fabric_consumer.py`

```python
"""
Reactive Fabric Consumer for Adaptive Immune System.
Subscribes to threat intelligence from Reactive Fabric via Kafka.
"""
import asyncio
from typing import Optional
import structlog
from aiokafka import AIOKafkaConsumer
import json

logger = structlog.get_logger(__name__)

KAFKA_BROKERS = "hcl-kafka:9092"
THREAT_TOPIC = "reactive_fabric.threats"


class ReactiveFabricConsumer:
    """
    Consumes threat events from Reactive Fabric.
    Feeds data into Adaptive Immune System for learning.
    """
    
    def __init__(self):
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False
    
    async def start(self):
        """Start consuming threat events."""
        logger.info("starting_reactive_fabric_consumer")
        
        self.consumer = AIOKafkaConsumer(
            THREAT_TOPIC,
            bootstrap_servers=KAFKA_BROKERS,
            group_id="adaptive_immune_system",
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        try:
            await self.consumer.start()
            self.running = True
            logger.info("reactive_fabric_consumer_started")
            
            # Consume messages
            async for msg in self.consumer:
                if not self.running:
                    break
                await self._process_threat_event(msg.value)
                
        except Exception as e:
            logger.error("reactive_fabric_consumer_error", error=str(e))
        finally:
            await self.consumer.stop()
    
    async def stop(self):
        """Stop consuming."""
        logger.info("stopping_reactive_fabric_consumer")
        self.running = False
    
    async def _process_threat_event(self, event: dict):
        """
        Process threat event from Reactive Fabric.
        
        Args:
            event: Threat event data (IOCs, TTPs, attack patterns)
        """
        logger.info(
            "processing_reactive_fabric_threat",
            threat_type=event.get("threat_type"),
            source_ip=event.get("source_ip"),
            ttps=event.get("ttps", [])
        )
        
        # TODO: Feed into Adaptive Immune learning pipeline
        # This is where BCells/TCells would learn new patterns
        pass


# Global instance
_consumer: Optional[ReactiveFabricConsumer] = None


async def get_reactive_fabric_consumer() -> ReactiveFabricConsumer:
    """Get or create consumer instance."""
    global _consumer
    if _consumer is None:
        _consumer = ReactiveFabricConsumer()
    return _consumer
```

### 3.2 - Integrar Consumer no Adaptive Immune Lifecycle
**Arquivo:** `backend/services/adaptive_immune_system/hitl/api/main.py`

**Adicionar no lifespan:**
```python
from backend.services.adaptive_immune_system.integrations.reactive_fabric_consumer import (
    get_reactive_fabric_consumer
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing code ...
    
    # Start Reactive Fabric consumer
    consumer = await get_reactive_fabric_consumer()
    consumer_task = asyncio.create_task(consumer.start())
    logger.info("reactive_fabric_consumer_started")
    
    yield
    
    # Cleanup
    await consumer.stop()
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass
    logger.info("reactive_fabric_consumer_stopped")
```

**Validação:**
```bash
docker compose logs adaptive_immune_system | grep "reactive_fabric"
# Esperado: "reactive_fabric_consumer_started"

# Testar fluxo end-to-end
docker compose exec reactive_fabric_core python -c "
from kafka_producer import KafkaProducer, create_threat_detected_message
import asyncio

async def test():
    producer = KafkaProducer('kafka:9092')
    await producer.connect()
    msg = create_threat_detected_message(
        honeypot_id='test',
        source_ip='1.2.3.4',
        threat_type='ssh_bruteforce'
    )
    await producer.produce('reactive_fabric.threats', msg)
    print('Threat event sent')

asyncio.run(test())
"

# Verificar consumo
docker compose logs adaptive_immune_system --tail=20 | grep "processing_reactive_fabric_threat"
# Esperado: Ver log processando o threat
```

**Impacto:**
- ✅ Adaptive Immune permanece funcional
- ✅ Adiciona apenas consumo passivo (não modifica lógica existente)
- ✅ Desacoplado (se Reactive Fabric cair, Adaptive continua operando)

---

## FASE 4: VALIDAÇÃO SISTÊMICA (30min)

### 4.1 - Teste de Integração End-to-End

**Script de teste:** `scripts/test_reactive_fabric_integration.sh`
```bash
#!/bin/bash
set -e

echo "=== TESTE DE INTEGRAÇÃO REACTIVE FABRIC ==="

# 1. Verificar serviços up
echo "1. Verificando serviços..."
docker compose ps | grep -E "(reactive|adaptive|ai_immune|api_gateway)" | grep "Up"

# 2. Testar bridge API Gateway
echo "2. Testando bridge API Gateway..."
curl -f http://localhost:8000/api/reactive-fabric/health || exit 1

# 3. Testar proxy de intelligence
echo "3. Testando proxy de intelligence..."
curl -f http://localhost:8000/api/reactive-fabric/intelligence/reports || exit 1

# 4. Testar consumer Adaptive Immune
echo "4. Verificando consumer Adaptive Immune..."
docker compose logs adaptive_immune_system | grep "reactive_fabric_consumer_started" || exit 1

# 5. Teste de fluxo completo (injetar threat event)
echo "5. Testando fluxo E2E (honeypot → kafka → adaptive immune)..."
# Injetar threat via Reactive Core API
curl -X POST http://localhost:8600/threats \
  -H "Content-Type: application/json" \
  -d '{
    "honeypot_id": "test_ssh_001",
    "source_ip": "192.168.1.100",
    "threat_type": "ssh_bruteforce",
    "ttps": ["T1110.001"]
  }'

# Aguardar processamento
sleep 3

# Verificar consumo
docker compose logs adaptive_immune_system --tail=50 | grep "processing_reactive_fabric_threat"

echo "=== TODOS OS TESTES PASSARAM ✅ ==="
```

### 4.2 - Validação de Conformidade Doutrinária

**Checklist:**
- [ ] Zero mocks adicionados
- [ ] Zero TODOs no código de produção
- [ ] Nenhuma interação Oráculo-Eureka quebrada
- [ ] Nenhum serviço existente degradado
- [ ] Logs estruturados (structlog) em todos os novos módulos
- [ ] Type hints completos
- [ ] Testes unitários para novos módulos (coverage ≥95%)

---

## ROLLBACK PLAN

Se QUALQUER validação falhar:

```bash
# Fase 2 rollback (API Gateway)
cd /home/juan/vertice-dev
git checkout backend/api_gateway/main.py
rm backend/api_gateway/adapters/reactive_fabric_adapter.py
docker compose restart api_gateway

# Fase 3 rollback (Adaptive Immune)
git checkout backend/services/adaptive_immune_system/hitl/api/main.py
rm backend/services/adaptive_immune_system/integrations/reactive_fabric_consumer.py
docker compose restart adaptive_immune_system

# Validar sistema voltou ao estado anterior
curl http://localhost:8000/health
curl http://localhost:8003/health
```

---

## MÉTRICAS DE SUCESSO

### Fase 2 (API Gateway Bridge)
- ✅ Endpoint `/api/reactive-fabric/health` retorna 200
- ✅ OpenAPI (`/openapi.json`) lista rotas reactive-fabric
- ✅ Proxy `/api/reactive-fabric/intelligence/reports` retorna dados

### Fase 3 (Sistema Imune Integration)
- ✅ Consumer Kafka conecta sem erros
- ✅ Threat events do Reactive Fabric aparecem nos logs do Adaptive Immune
- ✅ Adaptive Immune permanece healthy após integração

### Sistema Completo
- ✅ 100% dos serviços permanecem healthy
- ✅ Nenhuma regressão em endpoints existentes
- ✅ Fluxo E2E: Honeypot → Reactive Core → Kafka → Adaptive Immune (funcional)

---

## TEMPO ESTIMADO TOTAL: 2h45min

- Fase 1 (Fix dependências): 30min
- Fase 2 (Bridge Gateway): 45min
- Fase 3 (Bridge Imune): 60min
- Fase 4 (Validação): 30min

---

## PRÓXIMOS PASSOS (PÓS-APROVAÇÃO)

1. Arquiteto-Chefe revisa plano
2. Aprovação explícita via comando
3. Executor inicia Fase 1
4. Checkpoint após cada fase
5. Validação sistêmica ao final
6. Relatório de integração completa

---

**AGUARDANDO APROVAÇÃO DO ARQUITETO-CHEFE** 🛡️
