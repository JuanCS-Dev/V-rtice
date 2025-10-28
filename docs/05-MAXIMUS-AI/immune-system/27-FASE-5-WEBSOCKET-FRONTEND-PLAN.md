# 🌐 FASE 5: WebSocket + Frontend Dashboard - Implementation Plan

**Data**: 2025-01-10  
**Status**: 🟡 **EM IMPLEMENTAÇÃO**  
**Pré-requisitos**: Phases 1-4 Complete (234/235 tests passing) ✅  
**Glory to YHWH** - Real-time visibility of His healing work

---

## 📋 OBJETIVO

Criar **real-time visibility** do Adaptive Immunity System através de:
1. **Backend WebSocket** streaming APVs + Patches
2. **Frontend Dashboard** com visualização live
3. **Métricas em tempo real** (MTTR, success rate)

---

## 🎯 ARQUITETURA - HIGH LEVEL

```
┌─────────────────────────────────────────────────────────────┐
│                    FASE 5 ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────┘

Backend (FastAPI + WebSocket):
┌──────────────────┐
│  Oráculo Engine  │ ──► Kafka Topic: maximus.adaptive-immunity.apv
└──────────────────┘              │
                                  │ subscribe
                                  ▼
                        ┌─────────────────────┐
                        │ APVStreamManager    │
                        │ - WebSocket Pool    │
                        │ - Broadcast Logic   │
                        └─────────────────────┘
                                  │
                                  │ ws://
                                  ▼
┌────────────────────────────────────────────────────────────┐
│                      WebSocket Endpoint                    │
│                   /ws/adaptive-immunity                    │
└────────────────────────────────────────────────────────────┘
                                  │
                                  │ JSON Stream
                                  ▼
Frontend (Next.js 14 + React):
┌─────────────────────────────────────────────────────────────┐
│  useAPVStream()  ──► WebSocket Connection                   │
│       │                                                      │
│       ├──► APVCard (CVE details)                            │
│       ├──► PatchCard (Remediation status)                   │
│       ├──► MetricsPanel (MTTR, success rate)                │
│       └──► APVTimeline (chronological view)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 COMPONENTES - BREAKDOWN

### BACKEND (40% - ~800-1,000 linhas)

#### 1. APVStreamManager (300-400 linhas)
**Arquivo**: `backend/services/maximus_oraculo/websocket/apv_stream_manager.py`

**Responsabilidades**:
- Gerenciar pool de conexões WebSocket ativas
- Subscrever Kafka topic `maximus.adaptive-immunity.apv`
- Broadcast APVs para todos clientes conectados
- Heartbeat/keep-alive
- Graceful disconnection handling

**APIs**:
```python
class APVStreamManager:
    async def connect(self, websocket: WebSocket) -> str
    async def disconnect(self, connection_id: str) -> None
    async def broadcast_apv(self, apv: APV) -> None
    async def start_kafka_consumer(self) -> None
    async def stop(self) -> None
```

#### 2. WebSocket Endpoint (100-150 linhas)
**Arquivo**: `backend/services/maximus_oraculo/api/websocket_endpoints.py`

**Endpoint**: `ws://localhost:8001/ws/adaptive-immunity`

**Funcionalidades**:
- Accept WebSocket connections
- Authentication (optional - JWT token in query params)
- Route to APVStreamManager
- Error handling + logging

#### 3. REST Endpoints (200-250 linhas)
**Arquivo**: `backend/services/maximus_oraculo/api/adaptive_immunity_api.py`

**Endpoints**:
```
GET  /api/adaptive-immunity/apvs           - List recent APVs
GET  /api/adaptive-immunity/apvs/{cve_id}  - Get specific APV
GET  /api/adaptive-immunity/metrics        - Get system metrics
GET  /api/adaptive-immunity/patches        - List patches
```

#### 4. Models (150-200 linhas)
**Arquivo**: `backend/services/maximus_oraculo/models/streaming.py`

**Models**:
```python
@dataclass
class StreamMessage:
    type: Literal["apv", "patch", "metrics", "heartbeat"]
    timestamp: datetime
    payload: Dict[str, Any]

@dataclass
class MetricsSnapshot:
    apvs_detected: int
    apvs_confirmed: int
    patches_applied: int
    mttr_avg_seconds: float
    success_rate: float
```

### FRONTEND (60% - ~1,200-1,500 linhas)

#### 1. API Client (200-250 linhas)
**Arquivo**: `frontend/src/api/adaptiveImmunityAPI.ts`

```typescript
export class AdaptiveImmunityAPI {
  // REST endpoints
  async getAPVs(params?: APVQueryParams): Promise<APV[]>
  async getAPV(cveId: string): Promise<APV>
  async getMetrics(): Promise<MetricsSnapshot>
  async getPatches(params?: PatchQueryParams): Promise<Patch[]>
}
```

#### 2. WebSocket Hook (250-300 linhas)
**Arquivo**: `frontend/src/hooks/useAPVStream.ts`

```typescript
export function useAPVStream() {
  const [apvs, setAPVs] = useState<APV[]>([])
  const [metrics, setMetrics] = useState<MetricsSnapshot | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected'>()
  
  // WebSocket connection management
  // Auto-reconnect logic
  // Message parsing
  
  return { apvs, metrics, connectionStatus }
}
```

#### 3. Components (700-900 linhas)

**a) APVCard** (150-200 linhas)  
`frontend/src/components/adaptive-immunity/APVCard.tsx`
```tsx
interface APVCardProps {
  apv: APV
  onDetailsClick?: () => void
}

// Displays CVE details, severity, affected services
```

**b) PatchCard** (150-200 linhas)  
`frontend/src/components/adaptive-immunity/PatchCard.tsx`
```tsx
interface PatchCardProps {
  patch: Patch
  onViewDiff?: () => void
}

// Shows remediation status, strategy used, PR link
```

**c) MetricsPanel** (200-250 linhas)  
`frontend/src/components/adaptive-immunity/MetricsPanel.tsx`
```tsx
interface MetricsPanelProps {
  metrics: MetricsSnapshot
}

// Real-time metrics: MTTR, success rate, APVs/hour
// Small charts using recharts
```

**d) APVTimeline** (200-250 linhas)  
`frontend/src/components/adaptive-immunity/APVTimeline.tsx`
```tsx
interface APVTimelineProps {
  apvs: APV[]
  maxItems?: number
}

// Chronological view of APVs
// Auto-scroll to latest
```

#### 4. Dashboard Page (200-250 linhas)
**Arquivo**: `frontend/src/app/adaptive-immunity/page.tsx`

```tsx
export default function AdaptiveImmunityDashboard() {
  const { apvs, metrics, connectionStatus } = useAPVStream()
  
  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-8">
        <APVTimeline apvs={apvs} />
      </div>
      <div className="col-span-4">
        <MetricsPanel metrics={metrics} />
      </div>
    </div>
  )
}
```

---

## 🎯 PLANO DE IMPLEMENTAÇÃO - 8 TASKS

### ESTRATÉGIA

**Ordem**: Backend → Frontend → Integration → Tests

**Tempo Estimado**: 3-4 horas

---

### 🔧 BACKEND TASKS (1.5-2h)

#### Task 5.1: APVStreamManager Implementation (45min)

**Arquivo**: `backend/services/maximus_oraculo/websocket/apv_stream_manager.py`

**Steps**:
1. Create `ConnectionPool` class (Dict[str, WebSocket])
2. Implement `connect()` / `disconnect()` methods
3. Kafka consumer subscription to APV topic
4. Broadcast logic (iterate pool + send JSON)
5. Error handling per connection

**Validação**:
```python
# Unit tests
tests/unit/websocket/test_apv_stream_manager.py
- test_connection_lifecycle
- test_broadcast_to_multiple_clients
- test_disconnect_handling
- test_kafka_message_processing
```

---

#### Task 5.2: WebSocket Endpoint (30min)

**Arquivo**: `backend/services/maximus_oraculo/api/websocket_endpoints.py`

**Steps**:
1. Create FastAPI WebSocket endpoint
2. Accept connection → delegate to APVStreamManager
3. Keep-alive loop (ping/pong)
4. Graceful shutdown

**Integration**:
```python
# In main FastAPI app
from api.websocket_endpoints import router as ws_router
app.include_router(ws_router)
```

**Validação**:
```bash
# Manual test with websocat
websocat ws://localhost:8001/ws/adaptive-immunity
```

---

#### Task 5.3: REST API Endpoints (30min)

**Arquivo**: `backend/services/maximus_oraculo/api/adaptive_immunity_api.py`

**Steps**:
1. Implement GET `/api/adaptive-immunity/apvs`
2. Implement GET `/api/adaptive-immunity/metrics`
3. Add Redis caching for metrics (5min TTL)
4. OpenAPI documentation

**Validação**:
```bash
curl http://localhost:8001/api/adaptive-immunity/apvs
curl http://localhost:8001/api/adaptive-immunity/metrics
```

---

#### Task 5.4: Backend Tests (15min)

**Arquivos**:
- `tests/unit/websocket/test_apv_stream_manager.py`
- `tests/unit/api/test_websocket_endpoints.py`
- `tests/unit/api/test_adaptive_immunity_api.py`

**Target**: 20-25 new tests

---

### 🎨 FRONTEND TASKS (1.5-2h)

#### Task 5.5: API Client + Types (30min)

**Arquivos**:
- `frontend/src/api/adaptiveImmunityAPI.ts`
- `frontend/src/types/adaptiveImmunity.ts`

**Steps**:
1. Define TypeScript interfaces (APV, Patch, MetricsSnapshot)
2. Implement REST client methods
3. Error handling + retry logic
4. Add to global API context

**Validação**:
```bash
npm run type-check
# No TypeScript errors
```

---

#### Task 5.6: WebSocket Hook (40min)

**Arquivo**: `frontend/src/hooks/useAPVStream.ts`

**Steps**:
1. WebSocket connection lifecycle
2. Auto-reconnect with exponential backoff
3. Message parsing + state management
4. Connection status indicator
5. Cleanup on unmount

**Features**:
```typescript
{
  apvs: APV[]           // Auto-updated live
  metrics: MetricsSnapshot | null
  connectionStatus: 'connected' | 'connecting' | 'disconnected'
  error: Error | null
}
```

---

#### Task 5.7: Core Components (50min)

**Arquivos**:
- `APVCard.tsx` (15min)
- `PatchCard.tsx` (15min)
- `MetricsPanel.tsx` (20min)

**Design System**: Use existing Tailwind utilities + shadcn/ui

**Features**:
- APVCard: Badge severity, affected services list
- PatchCard: Status indicator, PR link button
- MetricsPanel: Stat cards + mini sparkline charts

---

#### Task 5.8: Dashboard Page (20min)

**Arquivo**: `frontend/src/app/adaptive-immunity/page.tsx`

**Steps**:
1. Layout grid (8/4 split)
2. Integrate useAPVStream hook
3. Render APVTimeline + MetricsPanel
4. Connection status indicator header
5. Add navigation link to main menu

---

## ✅ VALIDAÇÃO FINAL

### Backend Validation (15min)

```bash
cd backend/services/maximus_oraculo

# 1. Unit tests
pytest tests/unit/websocket/ tests/unit/api/ -v

# 2. Start server
uvicorn main:app --reload --port 8001

# 3. Test WebSocket (in another terminal)
websocat ws://localhost:8001/ws/adaptive-immunity

# 4. Test REST API
curl http://localhost:8001/api/adaptive-immunity/metrics
```

**Expectativa**:
- 20-25 new tests passing
- WebSocket aceita conexões
- REST API retorna JSON válido

---

### Frontend Validation (15min)

```bash
cd frontend

# 1. Type check
npm run type-check

# 2. Build check
npm run build

# 3. Dev server
npm run dev

# 4. Navigate to http://localhost:3000/adaptive-immunity
```

**Expectativa**:
- Zero TypeScript errors
- Build succeeds
- Dashboard renders sem erros
- WebSocket conecta automaticamente

---

### Integration Test (10min)

**Cenário E2E**:
1. Start Kafka + Redis (docker-compose)
2. Start Oráculo service
3. Start Frontend
4. Trigger APV generation (simulate CVE detection)
5. Verify APV appears em dashboard real-time

```bash
# Terminal 1: Infrastructure
docker-compose up kafka redis

# Terminal 2: Oráculo
cd backend/services/maximus_oraculo
python -m uvicorn main:app --reload

# Terminal 3: Frontend
cd frontend
npm run dev

# Terminal 4: Trigger test APV
curl -X POST http://localhost:8001/api/test/trigger-apv \
  -H "Content-Type: application/json" \
  -d '{"cve_id": "CVE-2024-TEST"}'
```

**Validação**: APV aparece no dashboard em <2 segundos

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Target | Validação |
|---------|--------|-----------|
| **Backend Tests** | 20-25 new | pytest count |
| **WebSocket Latency** | <100ms | Browser DevTools |
| **Frontend Build** | Success | npm run build |
| **TypeScript Errors** | 0 | npm run type-check |
| **E2E Latency** | <2s | Manual test |
| **Connection Stability** | >99% uptime | 10min test |

---

## 🎯 PRÓXIMA FASE (FASE 6)

Após Fase 5 complete:
1. **E2E Validation Tests** (~500 linhas)
2. **Performance Testing** (load test WebSocket)
3. **Real CVE Scenario** (test with production CVE)
4. **Documentation** (user guide + API docs)

---

## 🏁 COMMITS PLANEJADOS

```bash
# Após Backend complete
git commit -m "feat(oraculo): Phase 5 Backend - WebSocket + REST API! 🌐

Implements:
- APVStreamManager (WebSocket pool + Kafka subscription)
- WebSocket endpoint /ws/adaptive-immunity
- REST API endpoints (/apvs, /metrics, /patches)
- StreamMessage models

Tests: 23/23 passing (websocket + api)

Real-time APV streaming operational ✅
Day 68 - MAXIMUS gains real-time self-awareness."

# Após Frontend complete
git commit -m "feat(frontend): Phase 5 Dashboard - Real-time Immunity! 🎨✨

Implements:
- useAPVStream WebSocket hook
- APVCard, PatchCard, MetricsPanel components
- Adaptive Immunity Dashboard page
- AdaptiveImmunityAPI client

Features:
- Real-time APV streaming
- Live MTTR metrics
- Patch status tracking
- Auto-reconnect logic

Dashboard live at /adaptive-immunity ✅
Day 68 - Visual emergence of self-healing."

# Após E2E validation
git commit -m "test(adaptive-immunity): Phase 5 E2E Validation Complete! ✅

Validates:
- WebSocket <100ms latency
- E2E APV flow <2s
- Connection stability >99%
- Frontend build success

PHASE 5 COMPLETE - Real-time visibility operational
Next: Phase 6 - Performance Testing + Documentation

Glory to YHWH - His healing work now visible! 🙏
Day 68 of consciousness emergence."
```

---

## 📝 NOTAS IMPORTANTES

### Segurança

**WebSocket Auth** (implementar se tempo permitir):
```typescript
// Frontend
const ws = new WebSocket(`ws://localhost:8001/ws/adaptive-immunity?token=${jwt}`)

// Backend
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    user = await verify_jwt(token)
    if not user:
        await websocket.close(code=1008)
        return
```

### Escalabilidade

**Redis Pub/Sub** (para múltiplas instâncias Oráculo):
```python
# Se deploy com múltiplos pods, usar Redis Pub/Sub
# para broadcast cross-instance
redis_pubsub.publish("apv-stream", apv.json())
```

### Graceful Degradation

**Fallback para REST API** se WebSocket falhar:
```typescript
// Frontend: Polling fallback
if (wsError) {
  // Poll REST API every 5s
  setInterval(() => fetchAPVs(), 5000)
}
```

---

**Aprovado para execução**: SIM  
**Estimativa**: 3-4 horas  
**Prioridade**: HIGH (visualização crítica para demo)

Glory to YHWH - Que a cura seja vista! 🙏
