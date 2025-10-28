# 🎯 PLANO METODOLÓGICO - Active Immune System (Restante)

**Data**: 2025-01-10  
**Status**: 🟡 **AGUARDANDO APROVAÇÃO**  
**Sessão**: Continuação após Oráculo Core Complete  
**Glory to YHWH** - Todo progresso vem d'Ele

---

## 📊 SITUAÇÃO ATUAL - CHECKPOINT

### ✅ FASE 1 COMPLETA (Oráculo Core)
**Status**: 🟢 **100% OPERACIONAL** (conforme docs/11-ACTIVE-IMMUNE-SYSTEM/15-ORACULO-CORE-COMPLETE.md)

Implementado:
- ✅ APV Pydantic Model (428 linhas, 32 tests)
- ✅ OSV.dev Client (337 linhas, 13 tests)
- ✅ Dependency Graph Builder (368 linhas, 14 tests)
- ✅ Relevance Filter (400 linhas, tests)
- ✅ Kafka Publisher (220 linhas, tests)
- ✅ Oráculo Engine (420 linhas, tests E2E)
- ✅ **Total: 90/90 testes passando** ⚡

**Pipeline Oráculo Funcional**:
```
CVE Feed → OSV Client → Dependency Graph → Relevance Filter → APV → Kafka
```

### ❌ FALTANDO IMPLEMENTAR

1. **Eureka Consumer + Strategies** (Backend)
2. **Frontend Dashboard** (React + WebSocket)
3. **WebSocket Server** (Backend → Frontend streaming)
4. **E2E Full Cycle Tests** (Oráculo → Eureka → Dashboard)
5. **Infraestrutura Adicional** (se necessário)

---

## 🎯 PLANO ESTRUTURADO - 4 FASES COESAS

### ESTRATÉGIA
Abordagem **incremental e validada** - cada fase termina com validação completa antes de prosseguir.

**Ordem de implementação**:
1. **Prioridade 1**: Backend Eureka (consumer que processa APVs)
2. **Prioridade 2**: Frontend Dashboard (visualização tempo real)
3. **Prioridade 3**: Integração E2E (validação full cycle)
4. **Prioridade 4**: Refinamentos e Otimizações

---

## FASE 2: EUREKA CONSUMER + STRATEGIES (Backend)

**Duração Estimada**: 12-16 horas (2 dias)  
**Objetivo**: Consumir APVs do Kafka, confirmar vulnerabilidades, gerar patches

### 2.1. Componentes a Implementar

```
backend/services/maximus_eureka/
├── consumers/
│   ├── __init__.py
│   └── apv_consumer.py          # Kafka consumer APVs
├── confirmation/
│   ├── __init__.py
│   ├── ast_grep_engine.py       # Wrapper ast-grep
│   └── vulnerability_confirmer.py
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py         # Abstract base
│   ├── dependency_upgrade.py    # Strategy 1: Bump version
│   └── code_patch_llm.py        # Strategy 2: LLM patch (APPATCH)
├── llm/
│   ├── __init__.py
│   ├── base_client.py           # Abstract LLM client
│   ├── claude_client.py         # Anthropic Claude
│   └── prompt_templates.py      # APPATCH prompts
└── git_integration/
    ├── __init__.py
    └── patch_applicator.py      # Apply patch + create branch
```

### 2.2. Checklist Detalhado - Fase 2

#### Dia 1 - Manhã (4h)
- [ ] **2.1.1** Criar estrutura de diretórios Eureka
- [ ] **2.1.2** `consumers/apv_consumer.py` - Kafka consumer básico
  - Conectar ao Kafka topic `maximus.adaptive-immunity.apv`
  - Deserializar APV (Pydantic)
  - Logging estruturado
  - DLQ (Dead Letter Queue) para erros
- [ ] **2.1.3** Testes: `tests/unit/test_apv_consumer.py`
  - Mock Kafka producer
  - Test deserialização APV
  - Test DLQ behavior

#### Dia 1 - Tarde (4h)
- [ ] **2.2.1** `confirmation/ast_grep_engine.py` - Wrapper subprocess
  - Execute ast-grep CLI via subprocess
  - Parse output JSON
  - Handle errors (ast-grep not installed, pattern syntax)
- [ ] **2.2.2** `confirmation/vulnerability_confirmer.py` - Lógica confirmação
  - Recebe APV
  - Aplica ast-grep patterns contra codebase
  - Retorna lista de arquivos vulneráveis + linha número
- [ ] **2.2.3** Testes: `tests/unit/test_vulnerability_confirmer.py`
  - Mock filesystem com código vulnerável
  - Test pattern matching
  - Test false negatives/positives

#### Dia 2 - Manhã (4h)
- [ ] **2.3.1** `strategies/base_strategy.py` - Abstract class
  - Interface: `apply_strategy(apv, confirmed_files) -> Patch`
  - Métodos: `validate()`, `estimate_complexity()`
- [ ] **2.3.2** `strategies/dependency_upgrade.py` - Strategy 1
  - Parse pyproject.toml/requirements.txt
  - Check fixed version disponível
  - Generate diff para dependency bump
  - Simples e determinístico (sem LLM)
- [ ] **2.3.3** Testes: `tests/unit/test_dependency_upgrade.py`
  - Test pyproject.toml parsing
  - Test version bump logic
  - Test diff generation

#### Dia 2 - Tarde (4h)
- [ ] **2.4.1** `llm/base_client.py` - Abstract LLM client
  - Interface: `generate_patch(vulnerable_code, context) -> str`
  - Rate limiting, retry logic
- [ ] **2.4.2** `llm/claude_client.py` - Anthropic Claude
  - Use Anthropic SDK
  - APPATCH-inspired prompts (few-shot learning)
  - Max tokens, temperature config
- [ ] **2.4.3** `llm/prompt_templates.py` - APPATCH prompts
  - System prompt: "You are a security remediation expert..."
  - Few-shot examples (SQL injection, XSS, etc)
  - Output format: unified diff
- [ ] **2.4.4** `strategies/code_patch_llm.py` - Strategy 2
  - Use LLM client para gerar patch
  - Validação básica do diff
  - Fallback se LLM fail
- [ ] **2.4.5** Testes: `tests/unit/test_llm_clients.py`
  - Mock Anthropic API
  - Test prompt construction
  - Test patch parsing

### 2.3. Validação Fase 2

**Critérios de Sucesso**:
- [ ] Eureka consome APVs do Kafka sem erros
- [ ] ast-grep confirma vulnerabilidades (test case real)
- [ ] Dependency upgrade strategy gera diff válido
- [ ] LLM strategy gera patch (test com mock API)
- [ ] Testes unitários ≥90% coverage
- [ ] mypy --strict passing
- [ ] Docstrings completos (Google style)

**Comando de Validação**:
```bash
cd backend/services/maximus_eureka
pytest tests/unit/ -v --cov=. --cov-report=term-missing
mypy --strict .
```

---

## FASE 3: FRONTEND DASHBOARD (React + WebSocket)

**Duração Estimada**: 12-16 horas (2 dias)  
**Objetivo**: Dashboard tempo real para visualizar APVs e patches

### 3.1. Componentes a Implementar

```
frontend/src/components/dashboards/AdaptiveImmunityDashboard/
├── index.tsx                    # Main dashboard
├── components/
│   ├── APVStream.tsx           # Real-time APV feed
│   ├── APVCard.tsx             # Individual APV card
│   ├── PatchesTable.tsx        # Patches history table
│   └── MetricsPanel.tsx        # KPIs: MTTR, Success Rate
├── hooks/
│   ├── useAPVStream.ts         # WebSocket hook
│   └── useMetrics.ts           # Fetch metrics API
└── api/
    └── adaptiveImmunityAPI.ts  # API client
```

### 3.2. Checklist Detalhado - Fase 3

#### Dia 3 - Manhã (4h)
- [ ] **3.1.1** Criar estrutura de diretórios Frontend
- [ ] **3.1.2** `api/adaptiveImmunityAPI.ts` - API client
  - Fetch APVs history: GET /api/apvs
  - Fetch patches: GET /api/patches
  - Fetch metrics: GET /api/metrics
  - TypeScript types (APV, Patch, Metrics)
- [ ] **3.1.3** `hooks/useAPVStream.ts` - WebSocket hook
  - Connect to ws://localhost:8000/ws/apv-stream
  - Deserialize incoming APVs
  - State management (keep last 50 APVs)
  - Reconnection logic
- [ ] **3.1.4** Testes: Mock WebSocket connection

#### Dia 3 - Tarde (4h)
- [ ] **3.2.1** `components/APVCard.tsx` - Card individual
  - Display CVE ID, severity, priority
  - Color-coded by severity (critical=red, high=orange)
  - Expandable details (affected packages, CVSS)
  - Tailwind CSS styling (Windows 11 theme)
- [ ] **3.2.2** `components/APVStream.tsx` - Feed tempo real
  - Grid layout de APVCards
  - Filter by priority (all, critical, high, medium, low)
  - Connection status indicator
  - Empty state handling
- [ ] **3.2.3** Testes: Render tests

#### Dia 4 - Manhã (4h)
- [ ] **3.3.1** `components/PatchesTable.tsx` - Tabela patches
  - Columns: CVE ID, Strategy, Status, Created At
  - Link to Git PR
  - Status badges (pending, validating, merged)
  - Pagination
- [ ] **3.3.2** `components/MetricsPanel.tsx` - KPIs dashboard
  - MTTR (mean time to remediation) - gauge chart
  - Success rate - percentage
  - APVs processed (last 24h) - counter
  - Patches generated - counter
  - Use Recharts library
- [ ] **3.3.3** Testes: Integration tests

#### Dia 4 - Tarde (4h)
- [ ] **3.4.1** `index.tsx` - Dashboard principal
  - Layout: Grid 2 columns
    - Left: APVStream (real-time)
    - Right: MetricsPanel (top) + PatchesTable (bottom)
  - Responsive design
  - Loading states
  - Error handling
- [ ] **3.4.2** Integração: Conectar com backend real
  - Test WebSocket connection
  - Test API endpoints
  - Test data flow end-to-end
- [ ] **3.4.3** Accessibility audit
  - ARIA labels
  - Keyboard navigation
  - Screen reader friendly

### 3.3. Validação Fase 3

**Critérios de Sucesso**:
- [ ] Dashboard renderiza sem erros
- [ ] WebSocket conecta e recebe APVs em tempo real
- [ ] APVStream exibe APVs com filtros funcionando
- [ ] PatchesTable exibe patches history
- [ ] MetricsPanel exibe KPIs corretos
- [ ] Responsive design funciona (desktop + mobile)
- [ ] Accessibility score ≥90% (Lighthouse)

**Comando de Validação**:
```bash
cd frontend
npm run build
npm run test
npx lighthouse http://localhost:3000/dashboards/adaptive-immunity --view
```

---

## FASE 4: WEBSOCKET SERVER (Backend → Frontend)

**Duração Estimada**: 6-8 horas (1 dia)  
**Objetivo**: Streaming tempo real de APVs para frontend

### 4.1. Componentes a Implementar

```
backend/services/maximus_oraculo/
├── websocket.py                 # WebSocket server
└── api.py                       # FastAPI endpoint /ws/apv-stream
```

### 4.2. Checklist Detalhado - Fase 4

#### Dia 5 - Manhã (4h)
- [ ] **4.1.1** `websocket.py` - APVStreamManager class
  - Connection pool management
  - Broadcast method: `broadcast_apv(apv_dict)`
  - Heartbeat ping/pong (detect stale connections)
  - Error handling (disconnect failed clients)
- [ ] **4.1.2** `api.py` - WebSocket endpoint
  - Route: `/ws/apv-stream`
  - Accept WebSocket connections
  - Keep-alive loop
  - Handle disconnects gracefully
- [ ] **4.1.3** Integração com Kafka Publisher
  - Modificar `apv_publisher.py`
  - Após publicar no Kafka, broadcast via WebSocket
  - Async/await properly

#### Dia 5 - Tarde (4h)
- [ ] **4.2.1** Testes: `tests/integration/test_websocket.py`
  - Connect multiple clients
  - Test broadcast to all clients
  - Test disconnect handling
  - Test heartbeat mechanism
- [ ] **4.2.2** Load testing
  - Simulate 100 concurrent WebSocket connections
  - Test broadcast latency < 500ms
  - Test connection stability under load
- [ ] **4.2.3** Documentação: WebSocket protocol spec
  - Message format (JSON schema)
  - Heartbeat interval (30s)
  - Reconnection policy

### 4.3. Validação Fase 4

**Critérios de Sucesso**:
- [ ] WebSocket server aceita conexões
- [ ] Broadcast funciona para múltiplos clientes
- [ ] Heartbeat detecta e remove conexões mortas
- [ ] Latência < 500ms (APV → broadcast → frontend)
- [ ] Suporta ≥100 conexões simultâneas
- [ ] Testes integração passando

**Comando de Validação**:
```bash
# Terminal 1: Start server
cd backend/services/maximus_oraculo
uvicorn main:app --reload

# Terminal 2: Test WebSocket
python tests/integration/test_websocket.py

# Terminal 3: Frontend connect
cd frontend && npm run dev
# Navigate to /dashboards/adaptive-immunity
```

---

## FASE 5: INTEGRAÇÃO E2E + VALIDAÇÃO FINAL

**Duração Estimada**: 8 horas (1 dia)  
**Objetivo**: Validar ciclo completo Oráculo→Kafka→Eureka→Frontend

### 5.1. Componentes a Implementar

```
tests/e2e/
├── test_full_cycle.py           # Oráculo → Eureka → Frontend
└── test_mttr.py                 # MTTR < 45min target
```

### 5.2. Checklist Detalhado - Fase 5

#### Dia 6 - Manhã (4h)
- [ ] **5.1.1** `test_full_cycle.py` - E2E test completo
  - Injetar CVE fake no OSV.dev (mock)
  - Oráculo processa → APV
  - APV publicado no Kafka
  - Eureka consome APV
  - Eureka confirma vulnerability (ast-grep)
  - Eureka gera patch (Strategy 1 ou 2)
  - Frontend recebe APV via WebSocket
  - Assert em cada etapa
- [ ] **5.1.2** `test_mttr.py` - Validar MTTR target
  - Medir tempo: CVE ingest → Patch gerado
  - Assert: tempo < 45 minutos
  - Coletar métricas de performance

#### Dia 6 - Tarde (4h)
- [ ] **5.2.1** Executar full cycle em ambiente real
  - Levantar infraestrutura (Kafka, Redis, PostgreSQL)
  - Start Oráculo service
  - Start Eureka service
  - Start Frontend
  - Injetar CVE real (ex: CVE-2024-27351 Django)
  - Observar ciclo completo
  - Validar Pull Request criado no Git
- [ ] **5.2.2** Documentação: E2E Test Results
  - Screenshots do dashboard
  - Logs do ciclo completo
  - Métricas coletadas
  - Evidence de sucesso
- [ ] **5.2.3** Atualizar documentação do sistema
  - README.md com instruções de uso
  - Diagrams de arquitetura atualizados
  - API documentation (OpenAPI spec)

### 5.3. Validação Fase 5

**Critérios de Sucesso**:
- [ ] E2E test passa sem erros
- [ ] MTTR < 45 minutos (medido)
- [ ] Frontend exibe APV em tempo real
- [ ] Eureka gera patch válido
- [ ] Git PR criado automaticamente
- [ ] Documentação completa e atualizada

---

## 📊 CRONOGRAMA CONSOLIDADO

| Fase | Duração | Componente Principal | Entrega | Validação |
|------|---------|---------------------|---------|-----------|
| **Fase 2** | 12-16h (2 dias) | Eureka Consumer + Strategies | APV→Patch pipeline | Unit tests ≥90% |
| **Fase 3** | 12-16h (2 dias) | Frontend Dashboard | Real-time visualization | Lighthouse ≥90% |
| **Fase 4** | 6-8h (1 dia) | WebSocket Server | Backend→Frontend streaming | Load test 100 clients |
| **Fase 5** | 8h (1 dia) | E2E Integration | Full cycle validation | MTTR < 45min |
| **TOTAL** | **38-48h** | **6 dias** | **Active Immune System MVP** | **Production-ready** |

---

## 🎯 CRITÉRIOS DE SUCESSO FINAL

### Técnicos
- [ ] Oráculo ingere CVEs do OSV.dev (✅ já feito)
- [ ] Eureka consome APVs do Kafka
- [ ] Eureka confirma vulnerabilities via ast-grep
- [ ] Eureka gera patches (dependency upgrade + LLM)
- [ ] Frontend dashboard exibe APVs em tempo real
- [ ] WebSocket streaming < 500ms latency
- [ ] E2E test full cycle passa
- [ ] Git PR criado automaticamente

### Performance
- [ ] **MTTR < 45 minutos** (CVE → Patch merged)
- [ ] Latência Oráculo: CVE → APV < 30s (✅ já validado)
- [ ] Latência Eureka: APV → Patch < 10min
- [ ] WebSocket: Broadcast latency < 500ms
- [ ] Throughput Kafka: ≥100 APVs/min

### Qualidade (DOUTRINA COMPLIANCE)
- [ ] **Type hints 100%** (mypy --strict)
- [ ] **Testes ≥90% coverage**
- [ ] **Docstrings 100%** (Google style)
- [ ] **NO MOCK** (apenas unit tests)
- [ ] **NO PLACEHOLDER** (zero `pass`)
- [ ] **NO TODO** (zero débito técnico)

---

## 🚀 METODOLOGIA DE EXECUÇÃO

### Princípios
1. **Incremental**: Cada fase termina com validação completa
2. **Quality-First**: Nunca pular testes ou docstrings
3. **Disciplinado**: Seguir checklist metodicamente
4. **Auditável**: Commits bem documentados
5. **Sustentável**: Progresso consistente > sprints insustentáveis

### Workflow por Fase
```bash
# Para cada fase:

# 1. Criar branch
git checkout -b feature/adaptive-immunity-phase-N

# 2. Implementar conforme checklist
# - Zero placeholder
# - Type hints 100%
# - Docstrings desde o início
# - Testes em paralelo com implementação

# 3. Validar localmente
pytest tests/ -v --cov=. --cov-report=term-missing
mypy --strict .

# 4. Commit bem documentado
git add .
git commit -m "feat(adaptive-immunity): Phase N complete

- Implementado X, Y, Z
- Testes: N/N passing
- Coverage: X%
- Compliance: Doutrina ✅

Validation: [comandos de validação]
Day N of Active Immune System."

# 5. Documentar progresso
# Atualizar docs/11-ACTIVE-IMMUNE-SYSTEM/XX-PHASE-N-COMPLETE.md

# 6. Próxima fase
```

---

## 📝 PRÓXIMOS PASSOS IMEDIATOS

### Após Aprovação

1. **Validar Oráculo Core** (0.5h)
   ```bash
   cd backend/services/maximus_oraculo
   pytest tests/ -v --cov=. --cov-report=html
   mypy --strict .
   # Verificar 90/90 testes passando
   ```

2. **Iniciar Fase 2** (Eureka Consumer)
   ```bash
   git checkout -b feature/adaptive-immunity-phase-2-eureka
   cd backend/services/maximus_eureka
   # Seguir checklist Fase 2 Dia 1 Manhã
   ```

---

## 🙏 FUNDAMENTAÇÃO ESPIRITUAL

> **"Os planos do diligente tendem à abundância."**  
> — Provérbios 21:5

> **"Tudo quanto te vier à mão para fazer, faze-o conforme as tuas forças."**  
> — Eclesiastes 9:10

Este plano reflete:
- **Sabedoria**: Priorização correta (backend antes de frontend)
- **Disciplina**: Metodologia rigorosa fase a fase
- **Excelência**: Quality-first, zero compromissos
- **Humildade**: Reconhecer dependências e ordem lógica
- **Gratidão**: Todo progresso vem d'Ele

**Glory to YHWH** - Architect of systems, Giver of wisdom, Source of strength! 🙏✨

---

**Status**: 🟡 **AGUARDANDO APROVAÇÃO**  
**Aprovação Necessária**: Confirmar plano antes de iniciar Fase 2

**Próximo Marco**: Aprovação → Validação Oráculo → Fase 2 Dia 1

*Este trabalho durará através das eras. Cada linha será estudada por pesquisadores em 2050 como exemplo de construção disciplinada de sistemas complexos com propósito eterno.*

**Amém!** 🔥✨
