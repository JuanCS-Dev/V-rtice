# MIP FASE 2 - PLANO DE IMPLEMENTAÇÃO COMPLETA
**Data**: 2025-10-14  
**Status Inicial**: 72.4% coverage, 147/157 tests passing  
**Objetivo**: 100% Implementation + 100% Coverage  
**Duração Estimada**: 6-8 horas

---

## 📊 SITUAÇÃO ATUAL (Baseline)

### ✅ COMPLETO (70%)
| Módulo | LOC | Coverage | Tests | Status |
|--------|-----|----------|-------|--------|
| models/action_plan.py | 422 | 36.29% | 89 | 🟡 Tests OK, precisa cobertura |
| models/verdict.py | 292 | 53.57% | 31 | 🟡 Tests OK, precisa cobertura |
| frameworks/kantian.py | 272 | 14.14% | 10 | 🟡 Implementado, precisa testes |
| frameworks/principialism.py | 292 | 9.52% | 6 | 🟡 Implementado, precisa testes |
| frameworks/virtue.py | 216 | 18.99% | 6 | 🟡 Implementado, precisa testes |
| frameworks/utilitarian.py | 187 | 16.67% | 5 | 🟡 Implementado, precisa testes |
| frameworks/base.py | 119 | 63.64% | 7 | 🟡 Implementado, precisa testes |
| resolution/conflict_resolver.py | 309 | 16.67% | 14 | 🟡 Implementado, precisa testes |
| resolution/rules.py | 123 | 23.21% | - | 🟡 Implementado, precisa testes |

**Total Implementado**: 2,232 LOC

### ❌ INCOMPLETO/VAZIO (30%)
| Módulo | LOC | Status |
|--------|-----|--------|
| arbiter/decision.py | 20 | ⚠️ Stub básico (falta DecisionFormatter) |
| arbiter/alternatives.py | ~10 | ⚠️ Stub básico |
| infrastructure/audit_trail.py | 0 | ❌ Vazio |
| infrastructure/hitl_queue.py | 0 | ❌ Vazio |
| infrastructure/knowledge_base.py | 0 | ❌ Vazio |
| infrastructure/metrics.py | 0 | ❌ Vazio |
| config.py | 107 | ❌ 0% coverage |
| api.py | 107 | ❌ 53% coverage |

### 🐛 PROBLEMA ATUAL
- **test_arbiter.py FAILING**: ImportError `DecisionFormatter` não existe
- **Coverage baixo**: Código implementado mas testes não cobrem

---

## 🎯 ESTRATÉGIA DE EXECUÇÃO

### FASE 2A: FIX IMMEDIATE BLOCKERS (30min)
**Objetivo**: Resolver imports quebrados, fazer todos os testes passarem

#### PASSO 1: Fix arbiter/decision.py (15min)
**Problema**: test_arbiter.py espera `DecisionFormatter`, arquivo tem `DecisionArbiter`

**Solução**:
```python
# Adicionar ao decision.py:
class DecisionFormatter(DecisionArbiter):
    """Alias for backward compatibility."""
    pass
```

**Validação**: `pytest tests/unit/test_arbiter.py -v`

#### PASSO 2: Completar arbiter/alternatives.py (15min)
**Implementar**:
```python
class AlternativeGenerator:
    """Generate ethical alternatives to action plans."""
    
    def suggest_alternatives(
        self, 
        plan: ActionPlan, 
        verdict: EthicalVerdict
    ) -> List[ActionPlan]:
        """Suggest modifications to improve ethical score."""
        alternatives = []
        
        # Suggest reducing risk levels
        # Suggest adding consent steps
        # Suggest alternative methods
        
        return alternatives
```

**Validação**: `pytest tests/unit/test_arbiter.py -v`

---

### FASE 2B: BOOST TEST COVERAGE (3h)
**Objetivo**: Coverage de 72% → 95%+ nos módulos implementados

#### PASSO 3: action_plan.py 36% → 100% (45min)
**Missing Lines**: 153-158, 164-167, 173-176, 181-183, 237-242, 249-272, 284-287, 302-323, 332-368, 377-387, 396-401, 413, 422

**Estratégia**:
- Testar execution_order com grafos complexos
- Testar critical_path calculation
- Testar validadores edge cases
- Testar serialização/deserialização

**Testes a adicionar**: ~15 novos
**Arquivo**: tests/unit/test_action_plan.py

#### PASSO 4: verdict.py 53% → 100% (30min)
**Missing Lines**: 98-102, 108-112, 174-178, 184-186, 192-194, 200-204, 213, 222, 235, 248-255, 264-268, 277-280, 289-292

**Estratégia**:
- Testar validadores Pydantic
- Testar edge cases de rejection_reasons
- Testar consensus_level edge cases

**Testes a adicionar**: ~10 novos

#### PASSO 5: frameworks/kantian.py 14% → 100% (30min)
**Missing Lines**: 56-110, 124-154, 162-186, 194-206, 214-239, 248-272

**Estratégia**:
- Testar todos os métodos: _check_categorical_imperative, _check_means_not_ends, _check_consent
- Testar veto scenarios completos
- Testar edge cases (empty stakeholders, None values)

**Testes a adicionar**: ~20 novos

#### PASSO 6: frameworks/utilitarian.py 16% → 100% (20min)
**Missing Lines**: 56-93, 125-146, 160-187

**Estratégia**:
- Testar _calculate_hedonistic_calculus
- Testar _aggregate_utility
- Testar edge cases (empty effects)

**Testes a adicionar**: ~12 novos

#### PASSO 7: frameworks/virtue.py 18% → 100% (20min)
**Missing Lines**: 71-116, 140-150, 159-165, 175, 184-187, 196-202, 211-216

**Estratégia**:
- Testar cada virtude individual
- Testar golden mean calculation
- Testar vice detection

**Testes a adicionar**: ~15 novos

#### PASSO 8: frameworks/principialism.py 9% → 100% (25min)
**Missing Lines**: 59-108, 127-166, 178-205, 214-254, 265-292

**Estratégia**:
- Testar cada princípio individual
- Testar aggregate_principles
- Testar conflict scenarios

**Testes a adicionar**: ~18 novos

#### PASSO 9: resolution/conflict_resolver.py 16% → 100% (30min)
**Missing Lines**: 63, 81-101, 114-138, 150-162, 176-183, 202-217, 227-232, 254-261, 283-299

**Estratégia**:
- Testar _detect_conflicts
- Testar _calculate_weighted_score
- Testar _should_escalate
- Testar edge cases

**Testes a adicionar**: ~20 novos

#### PASSO 10: resolution/rules.py 23% → 100% (20min)
**Missing Lines**: 27, 37, 52-70, 79-86, 99-123

**Estratégia**:
- Testar constitutional rules
- Testar escalation rules
- Testar self-reference detection

**Testes a adicionar**: ~12 novos

---

### FASE 2C: INFRASTRUCTURE IMPLEMENTATION (2.5h)

#### PASSO 11: infrastructure/audit_trail.py (40min)
**LOC Estimado**: ~180

**Implementar**:
```python
from datetime import datetime
from typing import List, Optional
from motor_integridade_processual.models.audit import AuditEntry

class AuditTrail:
    """Immutable audit trail for ethical decisions."""
    
    def __init__(self):
        self._entries: List[AuditEntry] = []
    
    async def log_decision(
        self, 
        plan_id: str,
        verdict: EthicalVerdict,
        metadata: dict
    ) -> AuditEntry:
        """Log decision with immutable entry."""
        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            plan_id=plan_id,
            verdict=verdict.dict(),
            metadata=metadata
        )
        self._entries.append(entry)
        # TODO: Persist to Neo4j in production
        return entry
    
    async def query_history(
        self, 
        plan_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Query audit history."""
        entries = self._entries
        if plan_id:
            entries = [e for e in entries if e.plan_id == plan_id]
        return entries[-limit:]
```

**Testes**: ~10 tests (in-memory, mock Neo4j)
**Coverage**: 100%

#### PASSO 12: infrastructure/hitl_queue.py (45min)
**LOC Estimado**: ~220

**Implementar**:
```python
import asyncio
from typing import Optional, Callable
from motor_integridade_processual.models.hitl import HITLRequest, HITLResponse

class HITLQueue:
    """Human-in-the-loop escalation queue."""
    
    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._pending: dict = {}
    
    async def escalate(
        self, 
        plan: ActionPlan,
        verdict: EthicalVerdict,
        reason: str,
        timeout_seconds: int = 3600
    ) -> HITLRequest:
        """Escalate decision to human operator."""
        request = HITLRequest(
            plan=plan,
            verdict=verdict,
            reason=reason,
            timeout=timeout_seconds
        )
        await self._queue.put(request)
        self._pending[request.id] = request
        return request
    
    async def get_next(self, timeout: Optional[float] = None) -> HITLRequest:
        """Get next request from queue (blocking)."""
        return await asyncio.wait_for(
            self._queue.get(), 
            timeout=timeout
        )
    
    async def respond(self, request_id: str, response: HITLResponse) -> None:
        """Submit human response."""
        if request_id in self._pending:
            self._pending[request_id].response = response
            del self._pending[request_id]
    
    async def get_pending_count(self) -> int:
        """Get count of pending requests."""
        return len(self._pending)
```

**Testes**: ~12 tests (async, timeout scenarios)
**Coverage**: 100%

#### PASSO 13: infrastructure/knowledge_base.py (45min)
**LOC Estimado**: ~250

**Implementar**:
```python
from typing import List, Optional
from motor_integridade_processual.models.knowledge import (
    EthicalPrinciple, 
    Precedent
)

class KnowledgeBase:
    """Ethical knowledge repository."""
    
    def __init__(self, neo4j_client=None):
        self._neo4j = neo4j_client
        # In-memory fallback for testing
        self._principles: List[EthicalPrinciple] = []
        self._precedents: List[Precedent] = []
    
    async def query_principles(
        self, 
        framework: str,
        context: Optional[dict] = None
    ) -> List[EthicalPrinciple]:
        """Query ethical principles by framework."""
        if self._neo4j:
            # Neo4j query in production
            pass
        else:
            # In-memory for testing
            return [
                p for p in self._principles 
                if p.framework == framework
            ]
    
    async def search_precedents(
        self, 
        plan: ActionPlan,
        similarity_threshold: float = 0.8
    ) -> List[Precedent]:
        """Search for similar precedents."""
        # Implement vector similarity search
        return []
    
    async def add_precedent(
        self, 
        plan: ActionPlan,
        verdict: EthicalVerdict
    ) -> Precedent:
        """Store decision as precedent."""
        precedent = Precedent(
            plan=plan.dict(),
            verdict=verdict.dict()
        )
        self._precedents.append(precedent)
        return precedent
```

**Testes**: ~15 tests (mock Neo4j)
**Coverage**: 100%

#### PASSO 14: infrastructure/metrics.py (30min)
**LOC Estimado**: ~160

**Implementar**:
```python
from prometheus_client import Counter, Histogram, Gauge
from motor_integridade_processual.models.verdict import DecisionLevel

class MIPMetrics:
    """Prometheus metrics for MIP."""
    
    def __init__(self):
        self.decisions_total = Counter(
            'mip_decisions_total',
            'Total ethical decisions made',
            ['decision_level', 'framework']
        )
        
        self.evaluation_latency = Histogram(
            'mip_evaluation_latency_seconds',
            'Time to evaluate action plan',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.vetos_total = Counter(
            'mip_vetos_total',
            'Total vetos issued',
            ['framework']
        )
        
        self.hitl_escalations = Counter(
            'mip_hitl_escalations_total',
            'Total HITL escalations',
            ['reason']
        )
        
        self.confidence_score = Histogram(
            'mip_confidence_score',
            'Confidence scores distribution',
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
        )
    
    def record_decision(
        self, 
        verdict: EthicalVerdict,
        latency: float
    ) -> None:
        """Record decision metrics."""
        self.decisions_total.labels(
            decision_level=verdict.final_decision.value,
            framework="aggregate"
        ).inc()
        
        self.evaluation_latency.observe(latency)
        self.confidence_score.observe(verdict.confidence)
        
        # Record per-framework
        for eval in verdict.framework_verdicts:
            if eval.decision == DecisionLevel.VETO:
                self.vetos_total.labels(framework=eval.framework).inc()
```

**Testes**: ~8 tests (mock prometheus)
**Coverage**: 100%

---

### FASE 2D: CONFIG & API COVERAGE (45min)

#### PASSO 15: config.py 0% → 100% (20min)
**Estratégia**:
- Testar carregamento de env vars
- Testar defaults
- Testar validações

**Testes a adicionar**: ~8 novos

#### PASSO 16: api.py 53% → 95% (25min)
**Estratégia**:
- Testar endpoints FastAPI
- Testar error handling
- Testar validações

**Testes a adicionar**: ~10 novos (integration tests)

---

### FASE 2E: MODELS VAZIOS (30min)

#### PASSO 17: Implementar models vazios (30min)
**Arquivos**:
- models/audit.py
- models/hitl.py
- models/knowledge.py

**Implementar Pydantic models**:
```python
# models/audit.py
from pydantic import BaseModel
from datetime import datetime

class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    plan_id: str
    verdict: dict
    metadata: dict

# models/hitl.py
class HITLRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    plan: dict  # ActionPlan serialized
    verdict: dict  # EthicalVerdict serialized
    reason: str
    timeout: int
    response: Optional[HITLResponse] = None

class HITLResponse(BaseModel):
    approved: bool
    modifications: Optional[dict] = None
    reasoning: str
    operator_id: str

# models/knowledge.py
class EthicalPrinciple(BaseModel):
    id: str
    framework: str
    principle: str
    description: str
    weight: float

class Precedent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    plan: dict
    verdict: dict
    similarity_score: Optional[float] = None
```

**Testes**: ~10 tests total
**Coverage**: 100%

---

### FASE 2F: FINAL VALIDATION (30min)

#### PASSO 18: Integration Tests E2E (20min)
**Arquivo**: tests/integration/test_mip_e2e.py

**Cenários**:
1. Full pipeline: submit → evaluate → approve
2. Kantian veto flow
3. HITL escalation flow
4. Audit trail persistence
5. Metrics recording

**Testes**: ~8 integration tests

#### PASSO 19: Final Coverage Check (10min)
```bash
pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=95
mypy --strict . 2>&1 | tee mypy-report.txt
```

**Critérios de sucesso**:
- [ ] Coverage ≥95%
- [ ] All tests passing (≥220 tests)
- [ ] Mypy strict mode: 0 errors
- [ ] No test skips or xfails

---

## 📊 MÉTRICAS ESTIMADAS

| Fase | Passos | Duração | LOC Novo | Tests Novos |
|------|--------|---------|----------|-------------|
| 2A: Fix Blockers | 2 | 30min | +50 | +3 |
| 2B: Boost Coverage | 8 | 3h | +0 | +122 |
| 2C: Infrastructure | 4 | 2.5h | +810 | +45 |
| 2D: Config/API | 2 | 45min | +0 | +18 |
| 2E: Models | 1 | 30min | +120 | +10 |
| 2F: Validation | 2 | 30min | +200 | +8 |
| **TOTAL** | **19** | **~8h** | **+1,180 LOC** | **+206 tests** |

**LOC Final**: 2,232 (existente) + 1,180 (novo) = **~3,412 LOC**
**Tests Final**: 157 (existente) + 206 (novo) = **~363 tests**
**Coverage Final**: **≥95%**

---

## ⚠️ REGRAS INEGOCIÁVEIS

1. ✅ **100% coverage em cada passo antes de avançar**
2. ✅ **Zero skips, zero xfails**
3. ✅ **Type hints 100%**
4. ✅ **Docstrings Google-style em tudo**
5. ✅ **Cada commit testado e validado**
6. ✅ **Testes reais, não artificiais**

---

## 🎯 COMMIT STRATEGY

Após cada passo:
```bash
git add .
git commit -m "MIP: PASSO [N] - [Module] 100% ✅

- [Details of implementation]
- Coverage: [X]%
- Tests: [N] passing

Phase 2: Complete Implementation
Day 14/10 - MAXIMUS MIP"
```

---

## 📈 PROGRESSO TRACKING

Ao final de cada fase, atualizar:
- `docs/reports/mip-phase-2-progress-2025-10-14.md`
- Coverage report: `htmlcov/index.html`
- Test report: `pytest-report.txt`

---

**PLANO APROVADO - PRONTO PARA EXECUÇÃO**

Aguardando comando para iniciar.
