# MABA - Test Coverage Roadmap

## Caminho para 90% Coverage (Padrão Pagani)

**Status Atual**: 2025-10-30
**Coverage Atual**: ~15% (smoke tests apenas)
**Meta Constitucional**: ≥ 90%
**Gap**: 75%

---

## 🎯 OBJETIVO

Atingir **90% de test coverage** conforme **Padrão Pagani** estabelecido em MABA_GOVERNANCE.md, seguindo abordagem **TDD incremental** para garantir qualidade real (não testes superficiais apenas para métrica).

---

## 📊 STATUS ATUAL (FASE 1)

### Smoke Tests Implementados

**test_health.py** (4 testes):

- ✅ `test_health_check_success`
- ✅ `test_health_check_service_not_initialized`
- ✅ `test_root_endpoint`
- ✅ `test_metrics_endpoint`

**test_api_routes.py** (8 testes):

- ✅ `test_create_session_success`
- ✅ `test_close_session_success`
- ✅ `test_navigate_success`
- ✅ `test_navigate_without_session_fails`
- ✅ `test_query_cognitive_map_find_element`
- ✅ `test_analyze_page_not_implemented`
- ✅ `test_get_stats_success`

**Total**: 12 smoke tests
**Estimated Coverage**: ~15%

### Módulos SEM Cobertura

❌ **core/browser_controller.py**: 0%
❌ **core/cognitive_map.py**: 0%
❌ **models.py**: 0% (validação Pydantic não testada)
❌ **api/routes.py**: ~20% (apenas happy paths)
❌ **main.py**: 0% (lifespan, startup, shutdown)

---

## 🗺️ ROADMAP DE TESTES (FASE 2-4)

### FASE 2: Testes de Integração Core (Target: 50% coverage)

**Prioridade**: P0 (Crítico)
**Timeline**: Durante implementação de MVPs
**Entregas**:

**test_browser_controller.py** (~50 testes):

- [ ] Session lifecycle (create, reuse, close)
- [ ] Navigation (success, timeout, network errors)
- [ ] Element interaction (click, type, screenshot)
- [ ] Error handling (session not found, navigation failed)
- [ ] Timeout behavior (30s default, custom timeouts)
- [ ] Browser context isolation
- [ ] Concurrent session management (max 10 tabs)

**test_cognitive_map.py** (~40 testes):

- [ ] Map creation and storage
- [ ] Element finding (by description, importance score)
- [ ] Navigation path discovery
- [ ] Map updates (structural changes detected)
- [ ] Confidence scoring (0.0-1.0)
- [ ] Graph traversal algorithms
- [ ] Precedent storage and retrieval

**test_models.py** (~30 testes):

- [ ] Pydantic validation (all request/response models)
- [ ] Field constraints (max lengths, ranges)
- [ ] Default values
- [ ] Optional vs required fields
- [ ] Serialization/deserialization

### FASE 3: Testes End-to-End (Target: 75% coverage)

**Prioridade**: P1 (Alta)
**Timeline**: Após MVPs funcionais
**Entregas**:

**test_e2e_navigation.py** (~30 testes):

- [ ] Full flow: create session → navigate → interact → close
- [ ] Multi-step navigation sequences
- [ ] Form filling and submission
- [ ] Data extraction from pages
- [ ] Screenshot capture and storage

**test_e2e_cognitive_learning.py** (~20 testes):

- [ ] Learn website structure (first visit)
- [ ] Reuse learned structure (second visit)
- [ ] Detect structural changes
- [ ] Confidence degradation over time
- [ ] Map pruning and optimization

**test_integration_maximus.py** (~25 testes):

- [ ] Service registry heartbeat
- [ ] Redis event streaming (task.started, task.completed)
- [ ] MAXIMUS authorization workflow
- [ ] Task cancellation by MAXIMUS
- [ ] Error escalation to MAXIMUS

### FASE 4: Testes de Robustez (Target: 90%+ coverage)

**Prioridade**: P2 (Média)
**Timeline**: Antes de deploy produção
**Entregas**:

**test_edge_cases.py** (~40 testes):

- [ ] Malformed URLs
- [ ] Extremely slow pages (> 30s)
- [ ] Pages with CAPTCHA (should fail gracefully)
- [ ] SSL certificate errors
- [ ] Redirect chains (> 10 redirects)
- [ ] Large pages (> 10MB HTML)
- [ ] JavaScript-heavy SPAs

**test_security.py** (~30 testes):

- [ ] Domain whitelist enforcement
- [ ] Credentials encryption/decryption
- [ ] Session isolation (no data leakage)
- [ ] Rate limiting (100 req/min)
- [ ] PII detection in screenshots
- [ ] SQL injection in cognitive map queries

**test_performance.py** (~20 testes):

- [ ] Navigation latency (p99 < 10s)
- [ ] Memory leaks (long-running sessions)
- [ ] Concurrent request handling
- [ ] Database connection pool exhaustion
- [ ] Redis connection pool exhaustion

**test_lifespan.py** (~15 testes):

- [ ] Startup sequence (Playwright init, DB connect, Redis connect)
- [ ] Graceful shutdown (close all sessions, flush caches)
- [ ] Service registry registration/deregistration
- [ ] Health check during startup (not ready yet)
- [ ] Crash recovery (zombie process cleanup)

---

## 📐 MÉTRICAS DE QUALIDADE

### Coverage por Módulo (Meta Final)

| Módulo                       | Meta    | Atual    | Gap     |
| ---------------------------- | ------- | -------- | ------- |
| `main.py`                    | 90%     | 0%       | 90%     |
| `api/routes.py`              | 95%     | 20%      | 75%     |
| `core/browser_controller.py` | 90%     | 0%       | 90%     |
| `core/cognitive_map.py`      | 90%     | 0%       | 90%     |
| `models.py`                  | 100%    | 0%       | 100%    |
| **TOTAL**                    | **90%** | **~15%** | **75%** |

### Test Pass Rate (Padrão Pagani)

**Meta**: ≥ 99%

**Medição**:

```bash
pytest --maxfail=5 --tb=short
# Pass rate = (testes_passou / testes_total) × 100
```

**Atual**: N/A (apenas 12 testes)
**Target**: ≥ 99% quando atingir 500+ testes

---

## 🔧 FERRAMENTAS E CONFIGURAÇÃO

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
    --maxfail=5
markers =
    smoke: Smoke tests (fast, critical paths)
    integration: Integration tests (require external services)
    e2e: End-to-end tests (slow, full workflows)
    security: Security-focused tests
    performance: Performance and load tests
```

### requirements-test.txt

```
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.25.0
faker==20.0.0
```

### Cobertura Excludes

```python
# .coveragerc
[run]
omit =
    */tests/*
    */migrations/*
    */config.py
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## ⚠️ BLOQUEIOS DE DEPLOY

### Staging

**Permitido** com coverage atual (~15%)

- Smoke tests garantem endpoints críticos funcionais
- Ambiente de teste, não afeta usuários

### Produção

**❌ BLOQUEADO** até coverage ≥ 90%

**Justificativa** (MABA_GOVERNANCE.md):

> "Test Coverage: Meta ≥ 90%. Cobertura obrigatória: 100% das funções públicas, 95% dos branches, 90% das classes."

**Critérios para Desbloqueio**:

- [ ] Coverage ≥ 90% (medido via pytest-cov)
- [ ] Test pass rate ≥ 99%
- [ ] Zero testes falhando no CI/CD
- [ ] Todos os módulos core com ≥ 90%
- [ ] E2E tests incluindo integração com MAXIMUS

---

## 📝 PROTOCOLO DE DESENVOLVIMENTO (TDD Incremental)

### Para Cada Nova Feature:

1. **Escrever testes ANTES do código** (Red → Green → Refactor)
2. **Validar coverage não caiu** (`pytest --cov`)
3. **Adicionar testes de edge cases**
4. **Documentar casos não cobertos** (se < 90%)

### CI/CD Pipeline:

```yaml
test:
  stage: test
  script:
    - pip install -r requirements-test.txt
    - pytest --cov=. --cov-fail-under=90
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

**Pipeline FALHA** se:

- Coverage < 90%
- Test pass rate < 99%
- Qualquer teste E2E falha

---

## 🎯 COMMITMENT

**Arquiteto-Chefe**: Juan Carlos
**Responsável por Testes**: [A definir]

**Declaração**:

> "Este roadmap representa nosso compromisso com o **Padrão Pagani**. Coverage de 90% não é negociável para deploy em produção. Cada feature implementada nas FASE 2-4 DEVE vir acompanhada de testes correspondentes, garantindo crescimento incremental até a meta."

**Próxima Revisão**: Ao final de FASE 2 (após implementação de MVPs)

---

**Status**: 🟡 Em Progresso (FASE 1 completa, FASE 2-4 pendentes)
**Última Atualização**: 2025-10-30
**Documento aprovado por**: \***\*\*\*\*\***\_\***\*\*\*\*\*** (Arquiteto-Chefe)
