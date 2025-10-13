# FASE 3 - Wargaming + HITL (Human-in-the-Loop)

**Status**: 🚀 **EM PROGRESSO**
**Data Início**: 2025-10-13
**Objetivo**: Validação empírica de patches + aprovação humana para decisões críticas

---

## 📋 Visão Geral

A FASE 3 adiciona duas capacidades críticas ao Adaptive Immune System:

1. **Wargaming**: Validação empírica automatizada de patches através de simulação de ataques
2. **HITL (Human-in-the-Loop)**: Interface para aprovação humana de patches de alto risco

### Fluxo Completo (Fase 0 + 1 + 2 + 3)

```
┌─────────────────────────────────────────────────────────────┐
│                  ADAPTIVE IMMUNE SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Oráculo                                                  │
│     ├─> CVE Feeds (NVD, GHSA, OSV)                         │
│     ├─> Dependency Scanning (Python, JS, Go, Docker)       │
│     └─> APV Generation                                      │
│           │                                                  │
│           ▼                                                  │
│  2. Eureka                                                   │
│     ├─> Confirmation (Static + Dynamic)                     │
│     ├─> Remedy Generation (LLM + 4 strategies)             │
│     ├─> Validation (5-stage pipeline)                       │
│     └─> PR Creation (GitHub)                                │
│           │                                                  │
│           ▼                                                  │
│  3. Wargaming (NOVO - FASE 3)                               │
│     ├─> GitHub Actions Workflow Generation                  │
│     ├─> Attack Simulation (before/after patch)             │
│     ├─> Exploit Reproduction (CWE-specific)                │
│     └─> Evidence Collection                                 │
│           │                                                  │
│           ├─> Success? ──> Auto-merge PR                    │
│           │                                                  │
│           └─> Failure/High-Risk? ──> HITL Review           │
│                                      │                       │
│                                      ▼                       │
│  4. HITL Console (NOVO - FASE 3)                            │
│     ├─> Dashboard (FastAPI + React)                         │
│     ├─> Patch Review Interface                              │
│     ├─> Risk Assessment                                     │
│     └─> Human Decision (Approve/Reject/Modify)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Objetivos da FASE 3

### Objetivo 1: Wargaming Engine
**Problema**: Patches podem parecer corretos mas falhar em cenários reais
**Solução**: Simulação automatizada de ataques antes e depois do patch

**Capacidades**:
- Gerar GitHub Actions workflows dinamicamente
- Reproduzir exploits para cada CWE
- Coletar evidências (logs, screenshots, exit codes)
- Gerar relatório com veredito (success/failure)

### Objetivo 2: HITL Console
**Problema**: Patches de alto risco precisam revisão humana
**Solução**: Dashboard interativo para aprovação de patches

**Capacidades**:
- Visualizar APVs pendentes de revisão
- Ver contexto completo (CVE, patch, confidence scores, wargame results)
- Aprovar/rejeitar/modificar patches
- Adicionar comentários e justificativas
- Rastrear decisões históricas

### Objetivo 3: Confidence Dashboard
**Problema**: Falta visibilidade sobre eficácia do sistema
**Solução**: Métricas e visualizações em tempo real

**Capacidades**:
- Confirmation score trends
- False positive rate tracking
- Patch success rate (wargaming)
- MTTR (Mean Time To Remediation)
- Human decision patterns

---

## 🏗️ Arquitetura FASE 3

### Milestone 3.1: Wargaming Engine

```
wargaming/
├── __init__.py
├── workflow_generator.py      # Gera GitHub Actions YAML dinamicamente
├── exploit_templates.py        # Templates de exploits por CWE
├── evidence_collector.py       # Coleta logs, screenshots, métricas
├── verdict_calculator.py       # Calcula score baseado em evidências
└── wargame_orchestrator.py    # Orquestra todo o processo
```

**Workflow**:
1. Eureka cria PR → Trigger Wargaming
2. Wargaming gera `.github/workflows/security-test-{apv_code}.yml`
3. Workflow executa:
   - Setup: Clone repo, checkout branch
   - Test Before: Run exploit (should succeed = vulnerable)
   - Apply Patch: Checkout PR branch
   - Test After: Run exploit (should fail = fixed)
   - Collect Evidence: Logs, exit codes, screenshots
4. Wargaming recebe webhook do GitHub Actions
5. Calcula veredito (success/failure/inconclusive)
6. Envia relatório para Eureka/Oráculo

**Tecnologias**:
- GitHub Actions (workflow execution)
- GitHub API (workflow creation, status checks)
- Docker (exploit isolation)
- PyYAML (workflow generation)

---

### Milestone 3.2: HITL Console

```
hitl/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py                # FastAPI app
│   ├── endpoints/
│   │   ├── apv_review.py      # APV review endpoints
│   │   ├── decisions.py       # Decision logging
│   │   └── metrics.py         # Dashboard metrics
│   └── models.py              # Request/response models
│
├── frontend/                   # React dashboard (separado)
│   ├── src/
│   │   ├── components/
│   │   │   ├── APVList.tsx
│   │   │   ├── APVDetail.tsx
│   │   │   ├── PatchViewer.tsx
│   │   │   └── DecisionForm.tsx
│   │   └── App.tsx
│   └── package.json
│
└── decision_engine.py          # Lógica de decisão
```

**Workflow**:
1. Wargaming falha ou patch é alto risco → Trigger HITL
2. APV aparece no HITL Console dashboard
3. Humano revisa:
   - CVE details
   - Patch diff
   - Confirmation scores
   - Wargame results
   - Risk assessment
4. Humano toma decisão: Approve/Reject/Modify
5. Decisão é registrada no database
6. Ação executada:
   - Approve → Merge PR
   - Reject → Close PR
   - Modify → Solicita alterações

**Tecnologias**:
- FastAPI (backend)
- React + TypeScript (frontend)
- WebSockets (real-time updates)
- PostgreSQL (decision history)

---

### Milestone 3.3: Confidence Dashboard

```
dashboard/
├── __init__.py
├── metrics_collector.py        # Coleta métricas de todas as fases
├── prometheus_exporter.py      # Expõe métricas para Prometheus
└── grafana_dashboards/         # JSON dashboards
    ├── confirmation.json
    ├── remediation.json
    ├── wargaming.json
    └── hitl.json
```

**Métricas**:

1. **Confirmation Metrics**
   - Total APVs confirmed vs false positives
   - Average confidence score
   - Static vs dynamic agreement rate
   - False positive indicators frequency

2. **Remediation Metrics**
   - Patches generated per strategy
   - LLM costs (token usage)
   - Validation success rate
   - Average patch generation time

3. **Wargaming Metrics**
   - Total wargame runs
   - Success/failure/inconclusive rates
   - Average execution time
   - Exploit reproduction success rate

4. **HITL Metrics**
   - Pending reviews
   - Average review time
   - Approve/reject/modify rates
   - Human-AI agreement rate

5. **End-to-End Metrics**
   - MTTR (Mean Time To Remediation)
   - APV lifecycle duration
   - Pipeline success rate
   - Critical CVEs remediated

**Tecnologias**:
- Prometheus (metrics storage)
- Grafana (visualization)
- PostgreSQL (historical data)
- Python prometheus_client

---

### Milestone 3.4: Integração End-to-End

**Objetivo**: Conectar todos os componentes em um pipeline completo

**Tasks**:
1. RabbitMQ queue: `wargaming.trigger` (Eureka → Wargaming)
2. RabbitMQ queue: `wargaming.results` (Wargaming → Eureka) ✅ JÁ EXISTE
3. RabbitMQ queue: `hitl.review_request` (Wargaming → HITL)
4. RabbitMQ queue: `hitl.decision` (HITL → Eureka)
5. Callbacks de status completos
6. Testes end-to-end do pipeline completo

**Fluxo Integrado**:
```
Oráculo → [apv.dispatch] → Eureka
Eureka → [wargaming.trigger] → Wargaming
Wargaming → [wargaming.results] → Eureka
Wargaming (high-risk) → [hitl.review_request] → HITL Console
HITL → [hitl.decision] → Eureka
Eureka → [status] → Oráculo
```

---

## 📊 Estimativas

### Milestone 3.1: Wargaming Engine
- **Complexidade**: Alta
- **Tempo**: 2-3 dias
- **LOC Estimado**: ~2,500 linhas
- **Arquivos**: 6 arquivos principais
- **Testes**: 20 testes

### Milestone 3.2: HITL Console
- **Complexidade**: Alta (backend + frontend)
- **Tempo**: 2-3 dias
- **LOC Estimado**: ~2,000 linhas (backend) + frontend
- **Arquivos**: 8 arquivos backend + frontend app
- **Testes**: 15 testes

### Milestone 3.3: Confidence Dashboard
- **Complexidade**: Média
- **Tempo**: 1-2 dias
- **LOC Estimado**: ~800 linhas
- **Arquivos**: 3 arquivos + dashboards JSON
- **Testes**: 10 testes

### Milestone 3.4: Integração
- **Complexidade**: Alta
- **Tempo**: 1 dia
- **LOC Estimado**: ~500 linhas (queues + callbacks)
- **Arquivos**: 2 arquivos
- **Testes**: 15 testes (e2e)

**Total FASE 3**: 6-9 dias, ~5,800 LOC, 60 testes

---

## 🔧 Decisões de Design

### 1. Wargaming: GitHub Actions vs Local Execution

**Decisão**: GitHub Actions
**Rationale**:
- ✅ Isolamento nativo (cada workflow é um runner limpo)
- ✅ Logs persistentes e auditáveis
- ✅ Integração com PRs (status checks)
- ✅ Escalabilidade (GitHub gerencia infraestrutura)
- ❌ Dependência de GitHub (mas já usamos para PRs)

### 2. HITL: Web Dashboard vs CLI

**Decisão**: Web Dashboard (FastAPI + React)
**Rationale**:
- ✅ Melhor UX para revisão visual (diffs, gráficos)
- ✅ Multi-usuário simultâneo
- ✅ Real-time updates via WebSockets
- ✅ Acessível de qualquer lugar
- ❌ Mais complexo que CLI (mas vale o investimento)

### 3. Metrics: Prometheus vs CloudWatch/Datadog

**Decisão**: Prometheus + Grafana
**Rationale**:
- ✅ Open-source e self-hosted
- ✅ Integração nativa com Python (prometheus_client)
- ✅ Grafana dashboards ricos
- ✅ Sem custos de SaaS
- ❌ Requer infraestrutura própria (mas já temos)

### 4. HITL Decisions: Database vs Message Queue

**Decisão**: Database (PostgreSQL) + Message Queue
**Rationale**:
- ✅ Histórico persistente de decisões (compliance)
- ✅ Queries complexas para análise
- ✅ Message queue para notificações em tempo real
- Melhor dos dois mundos

---

## 🎯 Critérios de Sucesso

### Milestone 3.1: Wargaming
- [ ] Gera workflow GitHub Actions válido
- [ ] Executa exploit antes do patch (verifica vulnerabilidade)
- [ ] Executa exploit depois do patch (verifica fix)
- [ ] Coleta evidências (logs, exit codes)
- [ ] Calcula veredito correto (success/failure)
- [ ] Envia relatório via RabbitMQ

### Milestone 3.2: HITL Console
- [ ] Dashboard lista APVs pendentes
- [ ] Interface mostra contexto completo (CVE, patch, scores)
- [ ] Humano pode aprovar/rejeitar/modificar
- [ ] Decisões são registradas no database
- [ ] Ações são executadas (merge/close PR)
- [ ] Real-time updates via WebSockets

### Milestone 3.3: Confidence Dashboard
- [ ] Prometheus coleta métricas de todas as fases
- [ ] Grafana dashboards criados (4 dashboards)
- [ ] Métricas visíveis em tempo real
- [ ] Histórico de métricas persistido
- [ ] Alertas configurados para anomalias

### Milestone 3.4: Integração
- [ ] Pipeline completo funciona end-to-end
- [ ] APV vai de Oráculo → Eureka → Wargaming → HITL → Merge
- [ ] Callbacks de status em todas as etapas
- [ ] Testes e2e passam (APV completo simulado)
- [ ] Documentação completa

---

## 📝 Tarefas Imediatas (Próxima Sessão)

### Milestone 3.1: Wargaming Engine (Start Here)

1. **Criar estrutura de diretórios**
   ```
   mkdir -p wargaming/{templates,evidence}
   touch wargaming/__init__.py
   ```

2. **Implementar `workflow_generator.py`**
   - Classe `WorkflowGenerator`
   - Método `generate_workflow(apv, patch, exploit_template) -> str`
   - Gera YAML válido do GitHub Actions
   - Inclui steps: setup, test-before, apply-patch, test-after, collect-evidence

3. **Implementar `exploit_templates.py`**
   - Classe `ExploitTemplate` (Pydantic)
   - Templates para CWE-89, CWE-79, CWE-502, CWE-22
   - Formato: language, setup_commands, exploit_script, expected_before, expected_after

4. **Implementar `evidence_collector.py`**
   - Classe `EvidenceCollector`
   - Coleta logs do GitHub Actions via API
   - Parse de exit codes e outputs
   - Estrutura `WargameEvidence` (Pydantic)

5. **Implementar `verdict_calculator.py`**
   - Classe `VerdictCalculator`
   - Lógica: exploit_before_success + exploit_after_failure = SUCCESS
   - Calcula confidence score
   - Detecta casos inconclusivos

6. **Implementar `wargame_orchestrator.py`**
   - Classe `WargameOrchestrator`
   - Orquestra: generate → trigger → wait → collect → verdict
   - Integração com GitHub API
   - Envia relatório via RabbitMQ

---

## 🔄 Ordem de Implementação

**Sessão 1** (hoje):
- ✅ Planejamento FASE 3 completo
- 🚀 Milestone 3.1.1: Workflow Generator
- 🚀 Milestone 3.1.2: Exploit Templates

**Sessão 2**:
- Milestone 3.1.3: Evidence Collector
- Milestone 3.1.4: Verdict Calculator
- Milestone 3.1.5: Wargame Orchestrator

**Sessão 3**:
- Milestone 3.2.1: HITL Backend (FastAPI)
- Milestone 3.2.2: Decision Engine

**Sessão 4**:
- Milestone 3.2.3: HITL Frontend (React)

**Sessão 5**:
- Milestone 3.3: Confidence Dashboard (Prometheus + Grafana)

**Sessão 6**:
- Milestone 3.4: Integração End-to-End
- Testes e2e completos

---

## 📚 Referências

- GitHub Actions Workflow Syntax: https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions
- GitHub API Workflows: https://docs.github.com/en/rest/actions/workflows
- Prometheus Python Client: https://github.com/prometheus/client_python
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- React TypeScript: https://react-typescript-cheatsheet.netlify.app/

---

**Data**: 2025-10-13
**Status**: 🚀 **INICIANDO MILESTONE 3.1**
**Próximo**: Implementar `workflow_generator.py`
