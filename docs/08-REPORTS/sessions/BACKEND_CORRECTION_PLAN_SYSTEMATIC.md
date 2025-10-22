# PLANO DE CORREÇÃO SISTEMÁTICA - BACKEND VÉRTICE
**Status:** DRAFT → APROVAÇÃO → EXECUÇÃO  
**Data:** 2025-10-18T00:53:00Z  
**Executor:** IA Tática sob Constituição v2.7  
**Objetivo:** Backend 100% saudável para build produção

---

## PHASE 0: AUDITORIA ESTRUTURAL (15min)
**Objetivo:** Mapear dependências e impacto sistêmico

### 0.1 - Mapeamento de Imports
```bash
# Gerar grafo de dependências
- Identificar módulos órfãos (sem __init__.py)
- Mapear imports circulares
- Listar módulos com relative imports quebrados
```

### 0.2 - Classificação de Módulos
- **TIER 1 - Núcleo:** libs/vertice_{core,api,db} + shared/
- **TIER 2 - Serviços críticos:** active_immune_core, api_gateway
- **TIER 3 - Serviços satélite:** consciousness, wargaming_crisol, etc
- **TIER 4 - Utilitários:** scripts/, tests/

### 0.3 - Análise de Impacto TODOs/Mocks
```bash
# Priorizar por criticidade
- TODOs em código de segurança (HIGH)
- TODOs em lógica de negócio (MEDIUM)
- TODOs em logging/docs (LOW)
```

**Entregável:** `backend_structure_audit.json`

---

## PHASE 1: CORREÇÃO DE ESTRUTURA (45min)
**Meta:** 0 erros de importação nos testes

### 1.1 - Correção de __init__.py (TIER 1-3)
**Módulos afetados:**
- `consciousness/consciousness/`
- `consciousness/compassion/`
- `services/active_immune_core/`
- `services/wargaming_crisol/`
- `services/verdict_engine_service/`

**Ação:**
```bash
# Para cada módulo:
1. Verificar __init__.py existe
2. Validar exports explícitos
3. Corrigir relative imports (.module → module)
4. Adicionar ao pytest.ini se necessário
```

### 1.2 - Correção de PYTHONPATH em Testes
**Arquivos afetados:**
- `backend/pytest.ini`
- `services/*/pyproject.toml`
- `services/*/tests/conftest.py`

**Estratégia:**
- Padronizar pythonpath em pytest.ini global
- Remover sys.path.insert() nos conftests
- Usar imports absolutos consistentemente

### 1.3 - Validação Incremental
```bash
# Após cada correção:
python -m pytest <módulo> --collect-only -q
# Target: 0 collection errors
```

**Métrica de sucesso:** 8016 testes coletados / 0 erros

---

## PHASE 2: ELIMINAÇÃO PAGANI VIOLATIONS (90min)
**Meta:** 0 TODOs/FIXMEs em código produção

### 2.1 - Triage de TODOs (99 items)
**Classificação:**
- **IMPLEMENT NOW:** TODOs com lógica mock (ex: "TODO: Integrate with real firewall")
- **CONVERT TO ISSUE:** TODOs arquiteturais (ex: "TODO: Implement ML model")
- **REMOVE:** TODOs obsoletos/redundantes

### 2.2 - Resolução de TODOs Críticos
**Prioridade 1 (Security):**
```python
# active_immune_core/response/automated_response.py
- TODO: Integrate with firewall API → Implementar adapter real
- TODO: Integrate with HoneypotOrchestrator → Conectar serviço existente
- TODO: Integrate with CoagulationCascade → Remover se já integrado
```

**Prioridade 2 (Business Logic):**
```python
# active_immune_core/coagulation/cascade.py
- TODO: Integrate with real RTE → Conectar Real-Time Engine
- TODO: Implement smarter logic → Mover para issue GitHub
```

### 2.3 - Isolamento de Mocks (2,136 ocorrências)
**Estratégia:**
1. Confirmar mocks estão APENAS em `tests/` dirs
2. Identificar mocks vazados em `src/` ou raiz
3. Mover para fixtures pytest adequadas

**Busca refinada:**
```bash
# Mocks FORA de tests/ (violação crítica)
grep -r "mock\|Mock\|@patch" backend/ \
  --include="*.py" \
  --exclude-dir=tests \
  --exclude-dir=.venv
```

### 2.4 - Remoção de Placeholders
```python
# Padrões proibidos em produção:
- raise NotImplementedError("TODO: ...")
- pass  # FIXME: implement
- return {}  # mock response
```

**Métrica de sucesso:**
- TODOs/FIXMEs: 99 → 0
- Mocks fora de tests/: 2136 → 0

---

## PHASE 3: CORREÇÃO DE TESTES (120min)
**Meta:** ≥99% testes passando (Regra dos 99%)

### 3.1 - Correção de Erros de Importação em Testes
**Módulos afetados (84 errors):**
- consciousness/* (8 arquivos)
- services/verdict_engine_service/tests/* (7 arquivos)
- services/wargaming_crisol/tests/* (2 arquivos)

**Ação por módulo:**
1. Corrigir imports quebrados
2. Atualizar fixtures obsoletas
3. Validar execução: `pytest <test_file> -v`

### 3.2 - Correção de Testes Falhando
**Alvo atual:**
- `shared/tests/test_vault_client.py::test_init_no_credentials_else_branch`

**Estratégia:**
1. Executar teste isolado com -vv
2. Analisar asserção falhando
3. Corrigir lógica ou expectativa
4. Validar não quebrou outros testes

### 3.3 - Execução Completa
```bash
# Por TIER (incremental):
pytest libs/ -v --tb=short          # Target: 100%
pytest shared/ -v --tb=short        # Target: 99.79% → 100%
pytest services/ -v --tb=short      # Target: 0% → 95%+
pytest consciousness/ -v --tb=short # Target: 0% → 95%+
```

**Métrica de sucesso:**
- Total: 8016 testes
- Passed: ≥7936 (99%)
- Failed: ≤80 (1%)
- Errors: 0

---

## PHASE 4: ANÁLISE ESTÁTICA (30min)
**Meta:** Passar ruff + mypy sem erros críticos

### 4.1 - Correção Ruff
**Issues atuais:**
- E501 (line too long): 1,049 ocorrências → Ignorar ou corrigir batch
- E711/E713 (comparison style): Auto-fix com `ruff check --fix`
- S602/S608 (security): Revisar manualmente

**Ação:**
```bash
# Auto-fix tudo que é seguro
ruff check backend/ --fix --unsafe-fixes=false

# Revisar security issues
ruff check backend/ --select S --no-fix
```

### 4.2 - Correção Mypy
**Erro atual:** 1 type error

**Estratégia:**
```bash
# Identificar erro específico
mypy backend/ --exclude .venv --show-error-codes

# Corrigir com type hints adequados
# Não usar # type: ignore sem justificação
```

### 4.3 - Validação Deprecations
**Pydantic v2 warnings (30+):**
```python
# Padrão antigo:
class MyModel(BaseModel):
    class Config:
        orm_mode = True

# Padrão novo:
class MyModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

**Métrica de sucesso:**
- Ruff: 0 erros críticos (E/F)
- Mypy: 0 errors
- Warnings: Documentados em issue

---

## PHASE 5: VALIDAÇÃO FINAL (30min)
**Meta:** Certificação 100% build-ready

### 5.1 - Checklist Padrão Pagani
```bash
✓ Nenhum TODO/FIXME em código produção
✓ Nenhum mock fora de tests/
✓ Nenhum placeholder (NotImplementedError)
✓ 99%+ testes passando
✓ 0 erros de importação
✓ Ruff/Mypy limpos
```

### 5.2 - Build Dry-Run
```bash
# Simular build docker
docker build -f backend/Dockerfile -t vertice-backend:test .

# Validar serviços críticos sobem
docker-compose up -d api_gateway
curl http://localhost:8000/health
```

### 5.3 - Coverage Report
```bash
# Gerar coverage completo
pytest backend/ --cov=backend --cov-report=json

# Validar coverage mínimo por módulo
# TIER 1: ≥95%
# TIER 2: ≥90%
# TIER 3: ≥80%
```

### 5.4 - Relatório Final
**Entregável:** `BACKEND_100_CERTIFICATION.md`
```markdown
## Certificação Backend - Build Ready

### Métricas Finais:
- Tests: 7950/8016 passed (99.2%)
- Coverage: 92.5% (libs: 98%, services: 89%)
- Pagani Violations: 0
- Import Errors: 0
- Static Analysis: PASS

### Bloqueadores Resolvidos:
1. [x] Estrutura de imports corrigida (84 módulos)
2. [x] TODOs eliminados (99 → 0)
3. [x] Mocks isolados em tests/ (2136 movidos)
4. [x] Testes restaurados (484 → 7950)

### Regressões Conhecidas:
- [Issue #X] Pydantic v2 deprecations (30 warnings)
- [Issue #Y] Line length E501 (1049 ocorrências)

**Status:** ✅ APROVADO PARA BUILD PRODUÇÃO
```

---

## PHASE 6: MONITORAMENTO PÓS-CORREÇÃO (ongoing)
**Meta:** Garantir não-regressão

### 6.1 - CI/CD Guardians
```yaml
# .github/workflows/backend-health.yml
- name: Pagani Compliance Check
  run: |
    ! grep -r "# TODO\|# FIXME" backend/ --exclude-dir=tests
    
- name: Mock Isolation Check
  run: |
    ! grep -r "mock\|Mock" backend/ --exclude-dir=tests --exclude-dir=.venv
    
- name: Test Coverage Gate
  run: |
    pytest backend/ --cov --cov-fail-under=99
```

### 6.2 - Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: no-todos
      name: Block TODOs in production code
      entry: grep -r "# TODO\|# FIXME"
      language: system
      exclude: ^(tests/|docs/)
      pass_filenames: false
```

---

## ESTIMATIVA DE TEMPO TOTAL
| Phase | Duração | Dependências |
|-------|---------|--------------|
| 0 - Auditoria | 15min | - |
| 1 - Estrutura | 45min | Phase 0 |
| 2 - Pagani | 90min | Phase 1 |
| 3 - Testes | 120min | Phase 1, 2 |
| 4 - Static | 30min | Phase 1, 2 |
| 5 - Validação | 30min | Phase 1-4 |
| **TOTAL** | **5h30min** | Sequencial |

**Modo paralelizável:**
- Phase 2 + 4 podem rodar em paralelo após Phase 1
- Redução para ~4h15min

---

## CRITÉRIOS DE ROLLBACK
Se durante execução:
- **Bloqueador arquitetural:** Pausa → Escalar para Arquiteto-Chefe
- **Regressão >10 testes:** Rollback → Análise de impacto
- **Breaking change em API:** Pausa → Validação de contrato

---

## APROVAÇÃO REQUERIDA
**Arquiteto-Chefe:**
- [ ] Plano estrutural aprovado
- [ ] Priorização de fases aprovada
- [ ] Critérios de sucesso validados
- [ ] Autorização para execução

**Após aprovação:** Iniciar Phase 0 automaticamente

---

**Gerado por:** Executor Tático IA  
**Sob jurisdição:** Constituição Vértice v2.7 (Artigos I, II, VI)  
**Formato:** Doutrina de Legislação Prévia (Artigo V)
