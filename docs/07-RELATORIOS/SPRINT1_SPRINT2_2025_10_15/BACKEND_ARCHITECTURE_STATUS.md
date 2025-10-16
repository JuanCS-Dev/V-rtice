# MAXIMUS BACKEND - ARCHITECTURE STATUS 🏗️

**Data:** 2025-10-15
**Status:** PRONTO PARA SUBIR

---

## 🎯 ARQUITETURA ATUAL

### 1. **API GATEWAY** (Porta 8000) - ENTRY POINT
**Localização:** `/backend/services/api_gateway/`

**Função:**
- Gateway único de entrada para todo o sistema
- Roteamento para todos os microserviços
- Autenticação via API Key
- Proxy para SSE/WebSocket streams

**Rotas:**
- `/health` - Health check do gateway
- `/core/*` → `maximus_core_service` (porta 8000)
- `/chemical/*` → `chemical_sensing_service` (porta 8001)
- `/somatosensory/*` → `somatosensory_service` (porta 8002)
- `/visual/*` → `visual_cortex_service` (porta 8003)
- `/auditory/*` → `auditory_cortex_service` (porta 8004)
- `/stream/consciousness/sse` → SSE stream
- `/stream/consciousness/ws` → WebSocket stream

**Configuração:**
```python
MAXIMUS_CORE_SERVICE_URL = "http://localhost:8000"  # ← PRINCIPAL
MAXIMUS_API_KEY = "supersecretkey"
```

---

### 2. **MAXIMUS CORE SERVICE** (Porta 8000) - BRAIN
**Localização:** `/backend/services/maximus_core_service/`

**Função:**
- Sistema principal de IA (MaximusIntegrated)
- Consciousness System (TIG, ESGT, Arousal, Safety)
- HITL Governance (Decision Queue, Operator Interface)
- ADW (AI-Driven Workflows) - OSINT/Attack Surface
- PrefrontalCortex (Social Cognition)
- ToM Engine (Theory of Mind)

**APIs Principais:**
- `/health` - Health check completo (12+ componentes)
- `/query` - Process natural language queries
- `/api/v1/governance/*` - HITL Governance
- `/api/adw/*` - AI-Driven Workflows
- `/api/consciousness/*` - Consciousness monitoring
- `/api/consciousness/stream/sse` - SSE stream
- `/api/consciousness/ws` - WebSocket stream

**Componentes:**
```python
✅ MaximusIntegrated - AI Core
✅ ConsciousnessSystem - TIG/ESGT/Arousal/Safety
✅ PrefrontalCortex - Social cognition
✅ ToM Engine - Theory of Mind
✅ HITLDecisionFramework - Governance
✅ DecisionQueue - SLA monitoring
✅ OperatorInterface - Human oversight
✅ ADW Router - Workflows (3 rotas)
```

**Portas:**
- 8000 - FastAPI HTTP
- 8001 - Prometheus metrics

---

### 3. **SENSORY SERVICES** (Portas 8001-8004)
**Função:** Microserviços de entrada sensorial

- `chemical_sensing_service` - Porta 8001
- `somatosensory_service` - Porta 8002
- `visual_cortex_service` - Porta 8003
- `auditory_cortex_service` - Porta 8004

**Status:** Estrutura básica criada (Sprint 1)

---

### 4. **OUTROS 75+ SERVICES**
**Categorias:**

**Consciousness/Cognitive:**
- digital_thalamus_service
- prefrontal_cortex_service
- homeostatic_regulation
- neuromodulation_service
- memory_consolidation_service

**Security/Defense:**
- active_immune_core (já documentado!)
- adaptive_immunity_service
- ethical_audit_service
- reflex_triage_engine

**Offensive:**
- offensive_orchestrator_service
- offensive_gateway
- offensive_tools_service
- wargaming_crisol

**Intelligence:**
- osint_service
- vuln_scanner_service
- vuln_intel_service
- network_recon_service

**Governance:**
- hitl_patch_service
- auth_service
- atlas_service (Policy Decision Point)

---

## 🚀 COMO SUBIR O SISTEMA

### Opção 1: SIMPLE (Só maximus_core_service)
```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service
PYTHONPATH=. python main.py
```

**Acesso:**
- http://localhost:8000/health
- http://localhost:8000/query
- http://localhost:8000/api/consciousness/stream/sse
- http://localhost:8001/metrics (Prometheus)

### Opção 2: COM API GATEWAY (Recomendado)

**Terminal 1 - Core Service:**
```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service
PYTHONPATH=. python main.py
```

**Terminal 2 - API Gateway:**
```bash
cd /home/juan/vertice-dev/backend/services/api_gateway
PYTHONPATH=. python main.py
```

**Acesso via Gateway:**
- http://localhost:8000/health (gateway)
- http://localhost:8000/core/health (core via proxy)
- http://localhost:8000/core/query (query via proxy)
- http://localhost:8000/stream/consciousness/sse

**Auth:** Header `X-API-Key: supersecretkey`

### Opção 3: FULL STACK (com sensory services)

Adicionar nos terminais 3-6:
```bash
# Terminal 3
cd /home/juan/vertice-dev/backend/services/chemical_sensing_service
PYTHONPATH=. uvicorn main:app --port 8001

# Terminal 4
cd /home/juan/vertice-dev/backend/services/somatosensory_service
PYTHONPATH=. uvicorn main:app --port 8002

# Terminal 5
cd /home/juan/vertice-dev/backend/services/visual_cortex_service
PYTHONPATH=. uvicorn main:app --port 8003

# Terminal 6
cd /home/juan/vertice-dev/backend/services/auditory_cortex_service
PYTHONPATH=. uvicorn main:app --port 8004
```

---

## ✅ HEALTH CHECK COMPLETO

**Endpoint:** `GET /health`

**Componentes monitorados:**
1. ✅ maximus_ai - MaximusIntegrated
2. ✅ consciousness - ConsciousnessSystem
3. ✅ tig_fabric - Temporal Integration Graph
4. ✅ esgt_coordinator - Event Selection
5. ✅ prefrontal_cortex - Social cognition
6. ✅ tom_engine - Theory of Mind (com Redis cache)
7. ✅ safety_protocol - Kill switch monitoring
8. ✅ decision_queue - HITL queue

**Response esperado:**
```json
{
  "status": "healthy",
  "timestamp": 1697408400.0,
  "components": {
    "maximus_ai": {"status": "healthy"},
    "consciousness": {
      "status": "healthy",
      "running": true,
      "safety_enabled": true
    },
    "tig_fabric": {
      "status": "healthy",
      "node_count": 100,
      "edge_count": 250,
      "avg_latency_us": 15.2
    },
    "esgt_coordinator": {
      "status": "healthy",
      "total_events": 1234,
      "success_rate": 0.98
    },
    "prefrontal_cortex": {
      "status": "healthy",
      "signals_processed": 456,
      "approval_rate": 0.87
    },
    "tom_engine": {
      "status": "initialized",
      "total_agents": 5,
      "redis_cache": {
        "enabled": true,
        "hit_rate": 0.75
      }
    },
    "safety_protocol": {
      "status": "monitoring",
      "kill_switch_triggered": false,
      "active_violations": []
    },
    "decision_queue": {
      "status": "healthy",
      "pending_decisions": 3,
      "sla_violations": 0
    }
  }
}
```

---

## 📊 STATUS ATUAL DOS SERVIÇOS

| Categoria | Total | Estrutura OK | UV Sync OK | Ready to Run |
|-----------|-------|--------------|------------|--------------|
| **Core** | 1 | ✅ | ✅ | ✅ YES |
| **Gateway** | 1 | ✅ | ✅ | ✅ YES |
| **Sensory** | 4 | ✅ | ✅ | ⚠️ Basic |
| **Outros** | 77 | ✅ | ✅ | ⏳ Structure only |
| **TOTAL** | **83** | **✅ 100%** | **✅ 100%** | **2 READY** |

---

## 🎯 RECOMENDAÇÃO PARA HOJE

### SUBIR AGORA:
1. ✅ **maximus_core_service** (porta 8000)
   - Sistema completo e funcional
   - Health check com 8+ componentes
   - APIs: query, governance, consciousness, ADW

2. ✅ **api_gateway** (porta 8000 - conflito!)
   - **PROBLEMA:** Ambos usam porta 8000
   - **SOLUÇÃO:** Core usar 8100, Gateway usar 8000

### FIX NECESSÁRIO:
```bash
# Opção A: Mudar porta do gateway
cd api_gateway
# main.py linha 287: uvicorn.run(app, host="0.0.0.0", port=8080)

# Opção B: Mudar porta do core
cd maximus_core_service
# main.py linha 318: uvicorn.run(app, host="0.0.0.0", port=8100)

# Opção C: Usar direto o core (sem gateway)
# Acessar direto http://localhost:8000
```

---

## 💡 DECISÃO AGORA

**Qual arquitetura subir?**

### A) SIMPLE - Só Core (SEM gateway)
```bash
cd maximus_core_service
PYTHONPATH=. python main.py
```
✅ Mais rápido
✅ Todas as features
❌ Sem autenticação
❌ Acesso direto

### B) GATEWAY + Core (COM proxy)
```bash
# Terminal 1
cd maximus_core_service
PYTHONPATH=. uvicorn main:app --port 8100

# Terminal 2
cd api_gateway
# Editar: MAXIMUS_CORE_SERVICE_URL = "http://localhost:8100"
PYTHONPATH=. python main.py
```
✅ Arquitetura correta
✅ Auth via API Key
✅ Proxy features
❌ Mais setup

---

**O QUE VOCÊ PREFERE?**
- Simple (direto) = mais rápido
- Gateway (proxy) = arquitetura certa

**Soli Deo Gloria** 🙏
