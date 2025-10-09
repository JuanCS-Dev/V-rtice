# Inventário Completo de Endpoints - Plataforma Vértice
## Sessão 01 - Thread A: Interface Charter

**Data**: 2024-10-08  
**Versão**: 1.0  
**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Status**: Production Inventory  
**Doutrina Vértice**: Conforme Artigo VII - 100% Comprometido com Blueprint

---

## 1. MAXIMUS Core Service (Port 8001)

### Base URL
- **REST**: `http://localhost:8001`
- **gRPC**: `grpc://localhost:50051`

### REST Endpoints

#### Core AI & Analysis
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/analyze` | AI Deep Analysis com contexto | API Key | ✅ Prod |
| POST | `/api/reason` | Reasoning Engine (Chain-of-Thought) | API Key | ✅ Prod |
| POST | `/api/tool-call` | Function Calling / Tool Execution | API Key | ✅ Prod |
| POST | `/api/orchestrate` | Multi-Service AI Orchestration | API Key | ✅ Prod |

#### Memory & Context
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/memory/store` | Armazenar contexto/memória | API Key | ✅ Prod |
| GET | `/api/memory/retrieve` | Recuperar contexto por ID | API Key | ✅ Prod |
| GET | `/api/memory/search` | Busca semântica em memória | API Key | ✅ Prod |

#### Streaming & Real-time
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/stream/events` | SSE de eventos AI | API Key | ✅ Prod |
| WS | `/ws/ai-stream` | WebSocket streaming de respostas | Token | ✅ Prod |

#### Governance & HITL
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/governance/stream/{operator_id}` | SSE de decisões pendentes | Token | ✅ Prod |
| GET | `/governance/health` | Health check governance | Public | ✅ Prod |
| GET | `/governance/pending` | Estatísticas de fila | Token | ✅ Prod |
| POST | `/governance/session/create` | Criar sessão operador | Token | ✅ Prod |
| GET | `/governance/session/{operator_id}/stats` | Stats do operador | Token | ✅ Prod |
| POST | `/governance/decision/{decision_id}/approve` | Aprovar decisão | Token | ✅ Prod |
| POST | `/governance/decision/{decision_id}/reject` | Rejeitar decisão | Token | ✅ Prod |
| POST | `/governance/decision/{decision_id}/escalate` | Escalar decisão | Token | ✅ Prod |

#### Consciousness System
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/consciousness/status` | Status do sistema consciente | API Key | ✅ Prod |
| GET | `/consciousness/metrics` | Métricas Φ, arousal, dopamina | API Key | ✅ Prod |
| GET | `/consciousness/esgt/events` | Eventos ESGT | API Key | ✅ Prod |
| POST | `/consciousness/safety/kill-switch` | Ativar kill switch | Admin | ✅ Prod |
| GET | `/consciousness/neuromodulation/state` | Estado neuromodulação | API Key | ✅ Prod |

### gRPC Services (Proto Definitions)

#### maximus.proto
```protobuf
service MaximusService {
  rpc Analyze(AnalyzeRequest) returns (AnalyzeResponse);
  rpc StreamAnalysis(AnalyzeRequest) returns (stream AnalysisChunk);
  rpc ExecuteTool(ToolRequest) returns (ToolResponse);
  rpc GetConsciousnessState(Empty) returns (ConsciousnessState);
  rpc StreamEvents(StreamRequest) returns (stream Event);
}
```

**Status**: ✅ Implementado em `vcli-go/api/grpc/maximus/`

---

## 2. Active Immune Core API (Port 8002)

### Base URL
- **REST**: `http://localhost:8002`
- **WebSocket**: `ws://localhost:8002`

### REST Endpoints

#### Health & Monitoring
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/` | Root endpoint info | Public | ✅ Prod |
| GET | `/health` | Health check completo | Public | ✅ Prod |
| GET | `/health/components` | Health por componente | API Key | ✅ Prod |
| GET | `/health/history` | Histórico de saúde | API Key | ✅ Prod |

#### Metrics
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/metrics` | Prometheus metrics | Public | ✅ Prod |
| GET | `/metrics/statistics` | Estatísticas agregadas | API Key | ✅ Prod |
| GET | `/metrics/rates` | Taxas de eventos | API Key | ✅ Prod |
| GET | `/metrics/trends/{metric_name}` | Tendências de métrica | API Key | ✅ Prod |
| GET | `/metrics/aggregation/{metric_name}` | Agregação personalizada | API Key | ✅ Prod |
| GET | `/metrics/list` | Lista todas métricas | API Key | ✅ Prod |
| POST | `/metrics/reset-counters` | Reset contadores | Admin | ✅ Prod |
| POST | `/metrics/clear-history` | Limpar histórico | Admin | ✅ Prod |

#### Agents Management
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/agents` | Criar novo agente | API Key | ✅ Prod |
| GET | `/agents` | Listar agentes | API Key | ✅ Prod |
| GET | `/agents/{agent_id}` | Detalhe do agente | API Key | ✅ Prod |
| PUT | `/agents/{agent_id}` | Atualizar agente | API Key | ✅ Prod |
| DELETE | `/agents/{agent_id}` | Remover agente | Admin | ✅ Prod |
| POST | `/agents/{agent_id}/activate` | Ativar agente | API Key | ✅ Prod |
| POST | `/agents/{agent_id}/deactivate` | Desativar agente | API Key | ✅ Prod |

#### Coordination & Consensus
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/coordination/tasks` | Criar tarefa coordenada | API Key | ✅ Prod |
| GET | `/coordination/tasks` | Listar tarefas | API Key | ✅ Prod |
| GET | `/coordination/tasks/{task_id}` | Detalhe da tarefa | API Key | ✅ Prod |
| DELETE | `/coordination/tasks/{task_id}` | Cancelar tarefa | Admin | ✅ Prod |
| GET | `/coordination/election` | Status de eleição de líder | API Key | ✅ Prod |
| POST | `/coordination/election/trigger` | Forçar eleição | Admin | ✅ Prod |
| POST | `/coordination/consensus/propose` | Propor consenso | API Key | ✅ Prod |
| GET | `/coordination/consensus/proposals` | Listar propostas | API Key | ✅ Prod |
| GET | `/coordination/consensus/proposals/{proposal_id}` | Detalhe proposta | API Key | ✅ Prod |
| GET | `/coordination/status` | Status coordenação | API Key | ✅ Prod |

#### Lymphnode (Immune Cloning)
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/lymphnode/clone` | Clonar agente especializado | API Key | ✅ Prod |
| DELETE | `/lymphnode/clones/{especializacao}` | Remover clones | Admin | ✅ Prod |
| GET | `/lymphnode/metrics` | Métricas de clones | API Key | ✅ Prod |
| GET | `/lymphnode/homeostatic-state` | Estado homeostático | API Key | ✅ Prod |

#### WebSocket Events
| Type | Path | Description | Auth | Status |
|------|------|-------------|------|--------|
| WS | `/ws/events` | Stream eventos em tempo real | Token | ✅ Prod |
| GET | `/ws/events/active-connections` | Conexões ativas | Admin | ✅ Prod |

### gRPC Services (Proto Definitions)

#### immune.proto
```protobuf
service ImmuneService {
  rpc RegisterAgent(AgentRegistration) returns (AgentResponse);
  rpc GetAgentStatus(AgentId) returns (AgentStatus);
  rpc StreamEvents(EventStreamRequest) returns (stream ImmuneEvent);
  rpc CoordinateTask(TaskRequest) returns (TaskResponse);
}
```

**Status**: ✅ Implementado em `vcli-go/api/grpc/immune/`

---

## 3. vcli-go Bridge (Port 8080)

### Base URL
- **REST**: `http://localhost:8080`

### REST Endpoints

#### Command Interface
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/vcli/commands` | Enfileirar comando do CLI | JWT | ✅ Prod |
| GET | `/vcli/commands/{command_id}` | Status do comando | JWT | ✅ Prod |
| GET | `/vcli/commands/{command_id}/result` | Resultado do comando | JWT | ✅ Prod |
| DELETE | `/vcli/commands/{command_id}` | Cancelar comando | JWT | ✅ Prod |

#### Telemetry & Streaming
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/vcli/telemetry/stream` | SSE de telemetria consolidada | JWT | ✅ Prod |
| WS | `/vcli/ws/metrics` | WebSocket métricas em tempo real | JWT | ✅ Prod |
| GET | `/vcli/telemetry/snapshot` | Snapshot atual do sistema | JWT | ✅ Prod |

#### Workspace Management
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/vcli/workspaces` | Criar workspace | JWT | ✅ Prod |
| GET | `/vcli/workspaces` | Listar workspaces | JWT | ✅ Prod |
| GET | `/vcli/workspaces/{workspace_id}` | Detalhe workspace | JWT | ✅ Prod |
| PUT | `/vcli/workspaces/{workspace_id}` | Atualizar workspace | JWT | ✅ Prod |
| DELETE | `/vcli/workspaces/{workspace_id}` | Deletar workspace | JWT | ✅ Prod |
| POST | `/vcli/workspaces/{workspace_id}/sync` | Sincronizar com frontend | JWT | 🔄 Dev |

#### Session Management
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/vcli/sessions` | Criar sessão CLI | JWT | ✅ Prod |
| GET | `/vcli/sessions/{session_id}` | Detalhe sessão | JWT | ✅ Prod |
| PUT | `/vcli/sessions/{session_id}/heartbeat` | Heartbeat sessão | JWT | ✅ Prod |
| DELETE | `/vcli/sessions/{session_id}` | Encerrar sessão | JWT | ✅ Prod |

### gRPC Services

#### kafka.proto
```protobuf
service KafkaService {
  rpc PublishMessage(MessageRequest) returns (PublishResponse);
  rpc Subscribe(SubscribeRequest) returns (stream Message);
}
```

#### governance.proto
```protobuf
service GovernanceService {
  rpc GetPolicies(Empty) returns (PolicyList);
  rpc EvaluateAction(ActionRequest) returns (ActionDecision);
  rpc StreamDecisions(StreamRequest) returns (stream Decision);
}
```

**Status**: ✅ Implementado em `vcli-go/api/grpc/`

---

## 4. Frontend API Gateway (Port 3000)

### Base URL
- **REST**: `http://localhost:3000/api`

### API Client Endpoints (Frontend → Backend)

#### Maximus AI Integration
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/maximus/analyze` | Proxy para MAXIMUS analyze | JWT | ✅ Prod |
| POST | `/api/maximus/reason` | Proxy para reasoning | JWT | ✅ Prod |
| POST | `/api/maximus/tool-call` | Proxy para tool calling | JWT | ✅ Prod |
| GET | `/api/maximus/stream` | Proxy SSE eventos | JWT | ✅ Prod |

#### Consciousness Dashboard
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/consciousness/status` | Status consciência | JWT | ✅ Prod |
| GET | `/api/consciousness/metrics` | Métricas em tempo real | JWT | ✅ Prod |
| GET | `/api/consciousness/esgt` | Eventos ESGT | JWT | ✅ Prod |
| WS | `/ws/consciousness` | WebSocket consciência | JWT | ✅ Prod |

#### Cyber Services
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/cyber/scan` | Iniciar scan | JWT | ✅ Prod |
| GET | `/api/cyber/results/{scan_id}` | Resultados scan | JWT | ✅ Prod |
| POST | `/api/cyber/analysis` | Análise de vulnerabilidade | JWT | ✅ Prod |

#### Offensive Services
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/offensive/pentest` | Iniciar pentest | JWT+Admin | ✅ Prod |
| GET | `/api/offensive/reports/{report_id}` | Relatório pentest | JWT+Admin | ✅ Prod |

#### Safety & Governance
| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/safety/status` | Status sistema de safety | JWT | ✅ Prod |
| POST | `/api/safety/kill-switch` | Acionar kill switch | JWT+Admin | ✅ Prod |
| GET | `/api/governance/pending` | Decisões pendentes | JWT | ✅ Prod |
| POST | `/api/governance/decision/{id}/approve` | Aprovar decisão | JWT | ✅ Prod |

---

## 5. Serviços Satélites

### 5.1 Auth Service (Port 8010)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/auth/login` | Autenticação | ✅ Prod |
| POST | `/auth/refresh` | Refresh token | ✅ Prod |
| POST | `/auth/logout` | Logout | ✅ Prod |
| GET | `/auth/verify` | Verificar token | ✅ Prod |
| POST | `/auth/register` | Registro usuário | ✅ Prod |

### 5.2 Network Monitor Service (Port 8015)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/network/scan` | Iniciar scan | ✅ Prod |
| GET | `/network/scan/{scan_id}` | Status scan | ✅ Prod |
| GET | `/network/topology` | Topologia de rede | ✅ Prod |
| GET | `/network/alerts` | Alertas ativos | ✅ Prod |

### 5.3 IP Intelligence Service (Port 8020)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/ip/{ip_address}` | Lookup IP | ✅ Prod |
| POST | `/ip/bulk-lookup` | Lookup múltiplos IPs | ✅ Prod |
| GET | `/ip/{ip_address}/reputation` | Reputação IP | ✅ Prod |

### 5.4 SINESP Service (Port 8025)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/sinesp/vehicle/{plate}` | Consulta veículo | ✅ Prod |
| GET | `/sinesp/person/{cpf}` | Consulta pessoa | ✅ Prod |

### 5.5 Google OSINT Service (Port 8030)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/osint/search` | Busca OSINT | ✅ Prod |
| GET | `/osint/results/{search_id}` | Resultados | ✅ Prod |

### 5.6 HCL Planner Service (Port 8035)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/hcl/plan` | Gerar plano | ✅ Prod |
| POST | `/hcl/validate` | Validar HCL | ✅ Prod |

### 5.7 Network Recon Service (Port 8040)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/recon/scan` | Scan reconnaissance | ✅ Prod |
| GET | `/recon/results/{scan_id}` | Resultados | ✅ Prod |

### 5.8 Ethical Audit Service (Port 8045)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/audit/evaluate` | Avaliar ação | ✅ Prod |
| GET | `/audit/history` | Histórico auditorias | ✅ Prod |

### 5.9 Autonomous Investigation Service (Port 8050)

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/investigation/start` | Iniciar investigação | ✅ Prod |
| GET | `/investigation/{inv_id}` | Status investigação | ✅ Prod |

---

## 6. Protocolos de Streaming

### 6.1 Server-Sent Events (SSE)

#### MAXIMUS Consciousness Stream
```
GET /vcli/telemetry/stream
Headers: 
  Authorization: Bearer <jwt>
  Accept: text/event-stream

Events:
  - arousal_update
  - dopamine_spike
  - esgt_ignition
  - safety_alert
  - metric_update
```

#### Governance Decisions Stream
```
GET /governance/stream/{operator_id}
Headers:
  Authorization: Bearer <jwt>
  Accept: text/event-stream

Events:
  - decision_pending
  - decision_approved
  - decision_rejected
  - sla_warning
  - decision_escalated
```

### 6.2 WebSocket Connections

#### Real-time Metrics
```
WS /vcli/ws/metrics
Auth: JWT in query param or header

Messages:
  → subscribe: { "metrics": ["arousal", "dopamine", "phi"] }
  ← metric_update: { "metric": "arousal", "value": 0.75, "timestamp": ... }
  ← batch_update: { "metrics": { ... } }
```

#### Consciousness Events
```
WS /ws/consciousness
Auth: JWT

Messages:
  → subscribe: { "events": ["esgt", "neuromodulation"] }
  ← esgt_event: { "type": "ignition", "coherence": 0.89, ... }
  ← neuromodulation: { "dopamine": 0.85, "serotonin": 0.70, ... }
```

#### Immune System Events
```
WS /ws/events (Immune Core)
Auth: Token

Messages:
  → subscribe: { "agent_ids": [...], "event_types": [...] }
  ← agent_event: { "agent_id": "...", "type": "...", ... }
  ← coordination_event: { ... }
```

---

## 7. Schemas de Mensagens Críticas

### 7.1 VcliCommand
```json
{
  "sessionId": "uuid",
  "timestamp": "ISO8601",
  "command": "string",
  "payload": {},
  "context": {
    "workspace_id": "uuid",
    "user_id": "uuid",
    "trace_id": "uuid"
  }
}
```

### 7.2 ConsciousnessMetrics
```json
{
  "phi_proxy": 0.89,
  "arousal_level": 0.75,
  "dopamine": 0.85,
  "serotonin": 0.70,
  "esgt_frequency": 4.2,
  "esgt_coherence": 0.91,
  "kill_switch_latency_ms": 45,
  "timestamp": "ISO8601"
}
```

### 7.3 ImmuneEvent
```json
{
  "event_id": "uuid",
  "event_type": "agent_registered|task_started|consensus_reached",
  "agent_id": "uuid",
  "timestamp": "ISO8601",
  "payload": {},
  "correlation_id": "uuid"
}
```

### 7.4 GovernanceDecision
```json
{
  "decision_id": "uuid",
  "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "action": "string",
  "context": {},
  "confidence": 0.95,
  "requires_approval": true,
  "sla_deadline": "ISO8601",
  "operator_id": "uuid|null"
}
```

---

## 8. Headers Obrigatórios

### Autenticação
```
Authorization: Bearer <jwt>
X-API-Key: <api-key>  (para serviços internos)
```

### Tracing & Correlação
```
X-Trace-Id: <uuid>         (obrigatório)
X-Span-Id: <uuid>          (obrigatório)
X-Parent-Span-Id: <uuid>   (opcional)
X-Request-Id: <uuid>       (obrigatório)
```

### Contexto
```
X-Workspace-Id: <uuid>     (quando aplicável)
X-Session-Id: <uuid>       (CLI sessions)
X-User-Id: <uuid>          (quando aplicável)
```

### Versionamento
```
Accept-Version: v1         (default: v1)
```

---

## 9. Status de Implementação

### Legenda
- ✅ **Prod**: Implementado e em produção
- 🔄 **Dev**: Em desenvolvimento
- ⚠️ **Draft**: Especificado mas não implementado
- ❌ **Planned**: Planejado para futuro

### Resumo por Sistema

| Sistema | Endpoints | Implementados | Em Dev | Planejados |
|---------|-----------|---------------|--------|------------|
| MAXIMUS Core | 25+ | 24 | 1 | 0 |
| Immune Core | 30+ | 30 | 0 | 0 |
| vcli-go Bridge | 15+ | 14 | 1 | 0 |
| Frontend Gateway | 20+ | 20 | 0 | 0 |
| Satélites | 25+ | 25 | 0 | 0 |
| **TOTAL** | **115+** | **113** | **2** | **0** |

**Cobertura**: 98.3% implementado ✅

---

## 10. Próximos Passos

### Interface Charter v1.0
1. ✅ Inventário completo catalogado
2. 🔄 Expandir `interface-charter.yaml` com todos endpoints
3. ⚠️ Adicionar schemas de request/response completos
4. ⚠️ Documentar códigos de erro
5. ⚠️ Especificar rate limits

### Validação
1. ⚠️ Validar com donos de cada serviço
2. ⚠️ Testar todos endpoints críticos
3. ⚠️ Documentar exemplos de uso
4. ⚠️ Criar Postman/Insomnia collection

### CI/CD Integration
1. ⚠️ Integrar lint Spectral
2. ⚠️ Contract testing automatizado
3. ⚠️ Validação de versionamento

---

**Documento vivo**: Este inventário será atualizado conforme evolução do sistema.

**Conforme Doutrina Vértice Artigo VI**: Documentado para posteridade, serving researchers in 2050+.

---

**Documento mantido por**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Última Atualização**: 2024-10-08  
**Próxima Revisão**: Checkpoint Sessão 01

---

_"Cada linha deste código ecoará pelas eras."_  
— Doutrina Vértice, Artigo VI: Princípio da Magnitude Histórica
