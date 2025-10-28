# MIP FASE 1.5 - PLANO DE EXECUÇÃO METÓDICO
**Data**: 2025-10-14  
**Objetivo**: Implementação Completa + 100% Coverage  
**Padrão**: PAGANI ABSOLUTO - 100% ou nada

---

## 📊 STATUS ATUAL (Baseline Day 14/10)

### ✅ IMPLEMENTADO (20% do Sistema)
- 72 testes passando
- Coverage models: 86.37%
- **models/action_plan.py**: 422 LOC, 95.97% coverage
- **models/verdict.py**: 292 LOC, 92.86% coverage  
- **config.py**: 107 LOC, 0% coverage (sem testes)
- **Blueprint**: 3,651 linhas de especificação completa

### ❌ NÃO IMPLEMENTADO (80% do Sistema)
**TODOS os arquivos abaixo têm 0 LOC (vazios):**

1. **frameworks/** (Core do MIP):
   - base.py: 0 LOC ❌
   - kantian.py: 0 LOC ❌
   - utilitarian.py: 0 LOC ❌
   - virtue.py: 0 LOC ❌
   - principialism.py: 0 LOC ❌

2. **resolution/**:
   - conflict_resolver.py: 0 LOC ❌
   - rules.py: 0 LOC ❌

3. **arbiter/**:
   - decision.py: 0 LOC ❌
   - alternatives.py: 0 LOC ❌

4. **infrastructure/**:
   - audit_trail.py: 0 LOC ❌
   - hitl_queue.py: 0 LOC ❌
   - knowledge_base.py: 0 LOC ❌
   - metrics.py: 0 LOC ❌

**TOTAL A IMPLEMENTAR**: ~4,500 LOC (estimativa baseada no blueprint)

---

## 🎯 ROADMAP REVISADO - IMPLEMENTAÇÃO + TESTES

### FASE 1A: MODELS - 100% COVERAGE (2h)
**Status**: 95% implementado  
**Objetivo**: Completar models para 100%

#### PASSO 1: action_plan.py → 100% (1h)
**Missing**: Lines 156-157, 176, 287, 321, 366

**Ações**:
1. Abrir test_action_plan.py
2. Adicionar testes para linhas faltantes
3. Validar 100%

**Critério**:
```bash
pytest tests/unit/test_action_plan.py --cov=models/action_plan.py --cov-fail-under=100
```

#### PASSO 2: verdict.py → 100% (1h)
**Missing**: Lines 176-177, 185, 193, 249, 265

**Ações**:
1. Abrir test_verdict.py
2. Adicionar testes para linhas faltantes
3. Validar 100%

**Critério**:
```bash
pytest tests/unit/test_verdict.py --cov=models/verdict.py --cov-fail-under=100
```

---

### FASE 1B: FRAMEWORKS ÉTICOS (10h)
**Status**: 0% implementado (arquivos vazios)  
**Objetivo**: Implementar 4 frameworks + base + testes 100%

#### PASSO 3: base.py - Interface Base (1h)
**LOC Estimado**: ~150

**Implementar**:
```python
from abc import ABC, abstractmethod
from typing import Protocol
from models.action_plan import ActionPlan
from models.verdict import FrameworkEvaluation

class EthicalFramework(Protocol):
    """Protocol para frameworks éticos."""
    name: str
    weight: float
    
    def evaluate(self, plan: ActionPlan) -> FrameworkEvaluation:
        """Avalia ActionPlan segundo framework específico."""
        ...
    
    def can_veto(self) -> bool:
        """Framework tem poder de veto absoluto?"""
        ...
```

**Testes**: test_frameworks.py (base)
**Validação**: 100% coverage

#### PASSO 4: kantian.py - Deontologia (2.5h)
**LOC Estimado**: ~550 (segundo blueprint)  
**Complexidade**: ALTA (lógica de veto)

**Implementar**:
- Categorical Imperative test
- Universalization logic
- Means-ends analysis
- VETO power (Lei I)
- Autonomy respect check

**Testes**: test_frameworks.py (Kantian class)
**Cenários Mínimos**: 15 testes
- Aprovação de ação ética
- Veto de instrumentalização
- Veto de coerção
- Veto de mentira
- Universalization check
- Edge cases

**Validação**: 100% coverage

#### PASSO 5: utilitarian.py - Utilitarismo (2h)
**LOC Estimado**: ~380  
**Complexidade**: MÉDIA (cálculo multi-stakeholder)

**Implementar**:
- Bentham's hedonistic calculus
- Mill's qualitative pleasures
- 7 dimensions: intensity, duration, certainty, propinquity, fecundity, purity, extent
- Aggregate utility calculation
- Stakeholder weighting

**Testes**: test_frameworks.py (Utilitarian class)
**Cenários Mínimos**: 12 testes

**Validação**: 100% coverage

#### PASSO 6: virtue.py - Ética das Virtudes (2h)
**LOC Estimado**: ~580  
**Complexidade**: MÉDIA (7 virtudes + golden mean)

**Implementar**:
- Aristotelian 7 virtues: courage, temperance, liberality, magnificence, pride, good temper, friendliness
- Golden Mean calculation (virtue between extremes)
- Character assessment
- Eudaimonia scoring

**Testes**: test_frameworks.py (Virtue class)
**Cenários Mínimos**: 10 testes

**Validação**: 100% coverage

#### PASSO 7: principialism.py - Bioética (2h)
**LOC Estimado**: ~620  
**Complexidade**: MÉDIA (4 princípios)

**Implementar**:
- Beauchamp & Childress 4 principles:
  1. Autonomy (respeito à decisão informada)
  2. Beneficence (fazer o bem)
  3. Non-maleficence (não causar dano)
  4. Justice (distribuição equitativa)
- Principle conflict resolution
- Medical ethics context

**Testes**: test_frameworks.py (Principialism class)
**Cenários Mínimos**: 10 testes

**Validação**: 100% coverage

---

### FASE 1C: RESOLUTION ENGINE (4h)
**Status**: 0% implementado  
**Objetivo**: Resolver conflitos entre frameworks

#### PASSO 8: conflict_resolver.py (2.5h)
**LOC Estimado**: ~450

**Implementar**:
- Conflict detection entre frameworks
- Weighted voting system
- Context-aware weight adjustment
- Escalation triggers para HITL
- Confidence scoring

**Lógica**:
```python
class ConflictResolver:
    def resolve(
        self, 
        evaluations: List[FrameworkEvaluation],
        context: ActionContext
    ) -> EthicalVerdict:
        # 1. Detect conflicts
        conflicts = self._detect_conflicts(evaluations)
        
        # 2. Check for vetos (Kantian priority)
        if self._has_veto(evaluations):
            return self._build_veto_verdict(evaluations)
        
        # 3. Weighted average
        score = self._weighted_score(evaluations, context)
        
        # 4. Escalation check
        if self._should_escalate(score, conflicts):
            return self._build_escalated_verdict(evaluations)
        
        # 5. Build final verdict
        return self._build_verdict(score, evaluations)
```

**Testes**: test_resolution.py
**Cenários**: 15 testes
- No conflict
- Minor conflict resolved
- Major conflict → HITL
- Veto scenario
- Weight adjustment by context

**Validação**: 100% coverage

#### PASSO 9: rules.py (1.5h)
**LOC Estimado**: ~250

**Implementar**:
- Constitutional rules (Lei I, Lei Zero, etc)
- Meta-ethical rules
- Escalation rules
- Self-reference detection

**Testes**: test_resolution.py (Rules class)
**Cenários**: 8 testes

**Validação**: 100% coverage

---

### FASE 1D: ARBITER (3h)
**Status**: 0% implementado  
**Objetivo**: Arbitragem final e alternativas

#### PASSO 10: decision.py (1.5h)
**LOC Estimado**: ~300

**Implementar**:
- Final decision logic
- Verdict formatting
- Reasoning explanation
- Confidence thresholding

**Testes**: test_arbiter.py
**Cenários**: 8 testes

**Validação**: 100% coverage

#### PASSO 11: alternatives.py (1.5h)
**LOC Estimado**: ~250

**Implementar**:
- Generate ethical alternatives
- Suggestion engine
- Modification proposals

**Testes**: test_arbiter.py (Alternatives class)
**Cenários**: 7 testes

**Validação**: 100% coverage

---

### FASE 1E: INFRASTRUCTURE (5h)
**Status**: 0% implementado  
**Objetivo**: Audit, HITL, KB, Metrics

#### PASSO 12: audit_trail.py (1h)
**LOC Estimado**: ~200

**Implementar**:
- AuditLogger class
- Immutable log entries
- Persistence to Neo4j
- Query interface

**Testes**: test_infrastructure.py
**Cenários**: 6 testes

**Validação**: 100% coverage

#### PASSO 13: hitl_queue.py (1.5h)
**LOC Estimado**: ~300

**Implementar**:
- HITLQueue class
- Priority queue for escalations
- Timeout handling
- Human operator interface

**Testes**: test_infrastructure.py (HITL class)
**Cenários**: 8 testes

**Validação**: 100% coverage

#### PASSO 14: knowledge_base.py (1.5h)
**LOC Estimado**: ~350

**Implementar**:
- KnowledgeBase repository
- Neo4j integration
- Precedent search
- Principle queries

**Testes**: test_infrastructure.py (KB class)  
**Cenários**: 10 testes (mock Neo4j)

**Validação**: 100% coverage

#### PASSO 15: metrics.py (1h)
**LOC Estimado**: ~200

**Implementar**:
- Prometheus metrics
- Counters, histograms
- Latency tracking
- Decision statistics

**Testes**: test_infrastructure.py (Metrics class)
**Cenários**: 6 testes

**Validação**: 100% coverage

---

### FASE 1F: INTEGRATION & VALIDATION (2h)

#### PASSO 16: Integration Tests (1h)
**Arquivo**: tests/integration/test_mip_e2e.py

**Cenários**:
1. E2E: Submit plan → Evaluate → Get verdict
2. Kantian veto flow
3. HITL escalation flow
4. Conflict resolution flow
5. Audit trail persistence

**Validação**: All tests pass

#### PASSO 17: Final Coverage Check (1h)
**Objetivo**: Validar ≥95% global

```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=95
mypy --strict .
pylint **/*.py --fail-under=9.5
```

**Critério**:
- [ ] Coverage ≥95%
- [ ] Mypy: 0 errors
- [ ] Pylint: ≥9.5
- [ ] Total tests: ≥150

---

## 📊 ESTIMATIVA TOTAL REVISADA

| Fase | Passos | Duração | LOC Novo | Tests |
|------|--------|---------|----------|-------|
| **1A: Models** | 2 | 2h | 0 (já exist) | +10 |
| **1B: Frameworks** | 5 | 10h | ~1,430 | +47 |
| **1C: Resolution** | 2 | 4h | ~700 | +23 |
| **1D: Arbiter** | 2 | 3h | ~550 | +15 |
| **1E: Infrastructure** | 4 | 5h | ~1,050 | +30 |
| **1F: Integration** | 2 | 2h | ~300 | +15 |
| **TOTAL** | **17** | **26h** | **~4,030 LOC** | **~140 testes** |

**LOC Total Final**: 821 (existente) + 4,030 (novo) = **~4,851 linhas**

---

## ⚠️ REGRAS INEGOCIÁVEIS

1. ❌ **NÃO passar para próximo passo sem 100% do atual**
2. ❌ **NÃO usar mocks excessivos** (apenas para I/O externo como Neo4j)
3. ❌ **NÃO deixar TODOs** nos testes
4. ❌ **NÃO skip tests**
5. ✅ **SEMPRE validar com pytest após cada mudança**
6. ✅ **SEMPRE documentar testes com docstrings**
7. ✅ **SEMPRE usar type hints 100%**

---

## 📝 TEMPLATE DE TESTE

```python
"""
Unit tests for [MODULE_NAME].

Tests cover:
- Happy path scenarios
- Edge cases
- Error handling
- Boundary conditions
- Integration points

Coverage Target: 100%
"""
from typing import List
import pytest

from motor_integridade_processual.[module] import [Class]


class Test[ClassName]:
    """Test suite for [ClassName]."""
    
    def test_[scenario]_[expected_outcome](self) -> None:
        """
        Test [specific scenario].
        
        Given: [preconditions]
        When: [action]
        Then: [expected result]
        """
        # Arrange
        ...
        
        # Act
        result = ...
        
        # Assert
        assert result == expected
```

---

## 🎯 COMMIT STRATEGY

Após cada passo completo com 100%:
```bash
git add .
git commit -m "MIP: [PASSO X] - [Module] 100% Coverage ✅

- [Module]: 100% coverage ([N] tests)
- All tests passing
- [Specific features tested]

Phase 1.5: Test Coverage Boost
Day 14/10 - MAXIMUS MIP"
```

---

**PRONTO PARA EXECUÇÃO**

Aguardando comando: "vamos lá então"
