# BACKEND 100% ABSOLUTO - PLANO DE EXECUÇÃO COMPLETO

**Data:** 2025-10-17 23:46 UTC
**Executor:** Tático sob Constituição Vértice v2.7
**Commit:** 92504ca9 (HEAD -> backend-transformation/track3-services)
**Meta:** 100% Coverage Absoluto Backend (exceto consciousness)

---

## I. VERDADE ABSOLUTA - ESTADO ATUAL

### Scan Completo Executado
```bash
pytest backend/ --cov=backend --ignore=backend/consciousness
```

**Resultados:**
```
Total Statements:   98,154
Covered:             4,183  
Missing:            93,971
Coverage:            3.49%
```

**Serviços Analisados:** 93
**Arquivos Python:** 90,450

---

## II. BLOQUEADORES CRÍTICOS IDENTIFICADOS

### 1. Import Structure Broken (131 erros)
**Causa:** Namespace collision em `from services import`

**Serviços Afetados (sample):**
- offensive_orchestrator_service (15 erros)
- osint_service (15 erros)
- verdict_engine_service (8 erros)
- reactive_fabric_core/hitl (3 erros)
- wargaming_crisol (2 erros)

**Fix Obrigatório:** Migrar para absolute imports
```python
# ERRADO
from services.foo import bar

# CORRETO
from backend.services.foo import bar
```

### 2. Pytest Collection Errors
**Causa:** `pytest_plugins` em conftest.py não-root

**Fix:** Remover pytest_plugins de todos conftest.py exceto raiz

---

## III. ESTRATÉGIA DE ATAQUE - 3 FASES

### FASE 1: INFRAESTRUTURA (Dia 1)
**Objetivo:** Fix imports + collection errors → 0 erros de collection

**Tasks:**
1. ✅ Scan completo executado
2. ⬜ Script batch: Fix absolute imports (sed/find)
3. ⬜ Remove pytest_plugins de conftest.py não-root
4. ⬜ Re-scan: Validar 0 collection errors
5. ⬜ Commit: "fix(backend): absolute imports + pytest collection"

**Expected Coverage Após Fase 1:** ~3-5% (mesmo %, mas 0 erros)

---

### FASE 2: SERVIÇOS CRÍTICOS (Dias 2-30)
**Objetivo:** 100% coverage nos TOP 30 serviços (por volume)

**Priorização:** Maior impacto primeiro (mais statements)

#### Track 1: Gigantes (20k+ stmts) - Dias 2-10
1. **maximus_core_service** (24,125 stmts, 0.8% atual)
   - Estimativa: ~800-1000 testes necessários
   - Tempo: 3-4 dias

2. **active_immune_core** (11,275 stmts, 20.8% atual)
   - Estimativa: ~400-500 testes necessários
   - Tempo: 2-3 dias

#### Track 2: Grandes (5k-10k stmts) - Dias 11-20
3. **adaptive_immune_system** (7,029 stmts, 0% atual)
4. **narrative_manipulation_filter** (6,186 stmts, 0% atual)
5. **reactive_fabric_core** (4,920 stmts, 0% atual)

#### Track 3: Médios (2k-5k stmts) - Dias 21-25
6-10. osint_service, maximus_eureka, wargaming_crisol, offensive_orchestrator, etc.

#### Track 4: Pequenos (<2k stmts) - Dias 26-30
11-30. Restante dos serviços

**Expected Coverage Após Fase 2:** ~70-80%

---

### FASE 3: COBERTURA TOTAL (Dias 31-40)
**Objetivo:** 100% absoluto em TODOS os arquivos

**Categorias Finais:**
- ⬜ **Libs** (__libs__): vertice_core + security_tools
- ⬜ **Root** (__root__): api_docs_portal.py + shared
- ⬜ **Serviços Restantes:** 63 serviços pequenos/médios

**Expected Coverage Final:** 100.00%

---

## IV. METODOLOGIA DE EXECUÇÃO

### Protocolo por Serviço (Repetir para cada um)

#### Step 1: Análise (15 min)
```bash
# Gerar coverage isolado
pytest backend/services/SERVICE_NAME --cov=backend/services/SERVICE_NAME \
  --cov-report=json:cov_SERVICE.json --cov-report=term

# Identificar gaps
python scripts/analyze_gaps.py cov_SERVICE.json
```

#### Step 2: Implementação (2-4h por serviço médio)
**Template de teste:**
```python
# tests/test_MODULE.py
import pytest
from backend.services.SERVICE.module import Function

class TestFunction:
    def test_happy_path(self):
        result = Function.execute(valid_input)
        assert result.success
    
    def test_edge_case_empty(self):
        result = Function.execute([])
        assert result.error == "EmptyInput"
    
    def test_error_handling(self):
        with pytest.raises(CustomError):
            Function.execute(invalid_input)
```

#### Step 3: Validação Tripla (5 min)
```bash
# 1. Ruff
ruff check backend/services/SERVICE_NAME

# 2. MyPy
mypy backend/services/SERVICE_NAME

# 3. Coverage
pytest backend/services/SERVICE_NAME --cov=backend/services/SERVICE_NAME \
  --cov-report=term | grep "TOTAL.*100%"
```

#### Step 4: Commit + Documentação (5 min)
```bash
git add backend/services/SERVICE_NAME/tests/
git commit -m "feat(SERVICE): 100% coverage (X statements, Y testes)"

# Atualizar docs/backend_100/PROGRESS.md
```

---

## V. RECURSOS NECESSÁRIOS

### Tempo Estimado Total
**Cálculo:**
```
Fase 1 (infra):              1 dia
Fase 2 (TOP 30):            30 dias
Fase 3 (restante 63):       10 dias
TOTAL:                      41 dias úteis (~8 semanas)
```

**Com paralelização (múltiplas sessões/dia):**
- Redução possível: 30-40%
- **Tempo realista:** 25-30 dias úteis (~5-6 semanas)

### Testes Estimados
```
Serviços grandes (10):     ~5,000 testes
Serviços médios (20):      ~3,000 testes
Serviços pequenos (63):    ~2,000 testes
TOTAL:                     ~10,000 testes novos
```

---

## VI. MÉTRICAS DE PROGRESSO

### Tracking Diário
**Arquivo:** `docs/backend_100/PROGRESS.md`

**Formato:**
```markdown
## Dia X - YYYY-MM-DD

### Serviços Completados
- ✅ SERVICE_NAME: 0% → 100% (+Z stmts, Y testes)

### Coverage Global
- **Atual:** X.XX%
- **Delta:** +Y.YY%
- **Faltam:** Z stmts

### Próximo Alvo
- SERVICE_NAME (Z stmts, X% atual)
```

---

## VII. CRITÉRIOS DE SUCESSO (Padrão Pagani)

### Por Serviço
- ✅ Coverage: 100.00% (0 missing lines)
- ✅ Tests: 100% passing
- ✅ Ruff: 0 warnings
- ✅ MyPy: 0 errors
- ✅ TODOs: 0 (grep confirmed)
- ✅ Mocks: 0 em produção

### Global Backend
- ✅ Coverage: 100.00% (98,154/98,154 stmts)
- ✅ Tests: ~10,000+ passing
- ✅ Collection errors: 0
- ✅ Import errors: 0

---

## VIII. RISCOS E MITIGAÇÕES

### Risco 1: Import Fixes Quebrarem Runtime
**Mitigação:** Executar smoke tests após batch import fix

### Risco 2: Serviços com Dependências Externas
**Mitigação:** Mocking estratégico (APENAS em tests, nunca em prod)

### Risco 3: Coverage Estagnação (>95% mas <100%)
**Mitigação:** Análise linha-a-linha dos missing statements

---

## IX. COMANDOS DE REFERÊNCIA

### Coverage Global
```bash
pytest backend/ --cov=backend --ignore=backend/consciousness \
  --cov-report=json:coverage_backend_FULL.json \
  --cov-report=term-missing
```

### Coverage Por Serviço
```bash
SERVICE=maximus_core_service
pytest backend/services/$SERVICE \
  --cov=backend/services/$SERVICE \
  --cov-report=json:cov_$SERVICE.json \
  --cov-report=term-missing
```

### Fix Imports (Batch)
```bash
# Dry-run
find backend/services -name "*.py" -exec grep -l "from services import" {} \;

# Execute
find backend/services -name "*.py" -exec sed -i 's/from services\./from backend.services./g' {} \;
```

---

## X. DECLARAÇÃO DE COMPROMETIMENTO

**SOB A CONSTITUIÇÃO VÉRTICE v2.7:**

- ✅ **Artigo I:** Adesão inflexível ao plano
- ✅ **Artigo II:** Padrão Pagani (100% ou nada)
- ✅ **Artigo III:** Zero Trust (validação tripla)
- ✅ **Artigo IV:** Antifragilidade (testes edge cases)
- ✅ **Artigo V:** Legislação prévia (este plano)
- ✅ **Artigo VI:** Silêncio operacional (execução sem narração)

**META:** 100% ABSOLUTO. Sem atalhos. Sem pragmatismo.

"De tanto não parar, a gente chega lá."

---

**PRÓXIMO PASSO IMEDIATO:**

Executar FASE 1 - Step 2: Batch fix absolute imports

```bash
cd /home/juan/vertice-dev
python scripts/fix_imports_batch.py
```

