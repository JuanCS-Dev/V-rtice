# Plano de Implementação Detalhado - Córtex Pré-Frontal MAXIMUS v2.0
## Guia Metodológico de Execução (Padrão Pagani Compliant)

**Versão:** 1.0.0
**Data:** 2025-10-14
**Autor:** Juan Carlos de Souza + Claude Code (Executores Táticos)
**Governança:** Constituição Vértice v2.5 - Artigos I-V
**Status:** PLANO APROVADO - PRONTO PARA EXECUÇÃO IMEDIATA

---

## Sumário Executivo

Este documento é o **contrato de implementação** entre o Arquiteto-Chefe (Humano) e o Executor Tático (IA), definindo:

1. **Metodologia de Desenvolvimento** (TDD + DDD + Padrão Pagani)
2. **Padrões de Código** (Style guides, naming conventions, documentation)
3. **Protocolos de Validação** (Validação Tripla obrigatória)
4. **Estrutura de Testes** (Unit, Integration, E2E, Adversarial)
5. **Pipeline de CI/CD** (Automação completa de validação)
6. **Checklist de Entrega** (Definition of Done por módulo)

---

## 1. Metodologia de Desenvolvimento

### 1.1 Test-Driven Development (TDD) Rigoroso

**Protocolo Obrigatório:**

```
Para CADA funcionalidade implementada:

1. ESCREVER TESTE PRIMEIRO (Red)
   - Escrever teste unitário que falha
   - Validar que teste falha pelo motivo correto
   - Commit: "test: add failing test for X"

2. IMPLEMENTAR FUNCIONALIDADE (Green)
   - Escrever código mínimo para passar teste
   - Não adicionar funcionalidades não-testadas
   - Commit: "feat: implement X to satisfy test"

3. REFATORAR (Refactor)
   - Melhorar design sem quebrar testes
   - Eliminar duplicação
   - Commit: "refactor: improve X without changing behavior"

4. VALIDAÇÃO TRIPLA (Validate)
   - Análise estática (ruff, mypy)
   - Execução de testes (pytest)
   - Conformidade doutrinária (grep para mocks/TODOs)
```

**Exemplo Concreto (ToM Engine):**

```bash
# 1. RED: Escrever teste que falha
cat > compassion/test_tom_engine.py <<EOF
import pytest
from compassion.tom_engine import ToMAgent, MentalState

@pytest.mark.asyncio
async def test_tom_agent_generates_hypotheses():
    """Test ToM agent generates multiple hypotheses."""
    agent = ToMAgent(social_memory=None)
    context = {"agent_id": "user_123", "behavior": "I'm confused?"}

    hypotheses = await agent.generate_hypotheses("user_123", context)

    assert len(hypotheses) >= 3  # Must generate at least 3 hypotheses
    assert all(h.plausibility > 0 for h in hypotheses)  # All must have plausibility
    assert hypotheses[0].plausibility >= hypotheses[1].plausibility  # Ordered by plausibility
EOF

# Executar teste (deve falhar pois ToMAgent não existe)
pytest compassion/test_tom_engine.py::test_tom_agent_generates_hypotheses
# Expected: FAILED (ImportError: cannot import name 'ToMAgent')

git add compassion/test_tom_engine.py
git commit -m "test: add failing test for ToMAgent hypothesis generation"

# 2. GREEN: Implementar funcionalidade mínima
cat > compassion/tom_engine.py <<EOF
from dataclasses import dataclass
from typing import List

@dataclass
class MentalState:
    agent_id: str
    beliefs: List[str] = []
    confidence: float = 0.5

@dataclass
class ToMHypothesis:
    mental_state: MentalState
    plausibility: float
    evidence: List[str] = []

class ToMAgent:
    def __init__(self, social_memory):
        self.social_memory = social_memory

    async def generate_hypotheses(self, agent_id: str, context: dict) -> List[ToMHypothesis]:
        # Implementação mínima para passar teste
        hypotheses = [
            ToMHypothesis(
                mental_state=MentalState(agent_id=agent_id, beliefs=["confused"]),
                plausibility=0.8,
                evidence=["Question mark in behavior"]
            ),
            ToMHypothesis(
                mental_state=MentalState(agent_id=agent_id, beliefs=["neutral"]),
                plausibility=0.5,
                evidence=["Default hypothesis"]
            ),
            ToMHypothesis(
                mental_state=MentalState(agent_id=agent_id, beliefs=["engaged"]),
                plausibility=0.3,
                evidence=["Low prior"]
            ),
        ]
        return sorted(hypotheses, key=lambda h: h.plausibility, reverse=True)
EOF

# Executar teste (deve passar agora)
pytest compassion/test_tom_engine.py::test_tom_agent_generates_hypotheses
# Expected: PASSED

git add compassion/tom_engine.py
git commit -m "feat: implement ToMAgent hypothesis generation (minimal)"

# 3. REFACTOR: Melhorar design
# (Exemplo: extrair lógica de detecção de confusão para método privado)

# 4. VALIDAÇÃO TRIPLA
ruff check compassion/tom_engine.py  # Static analysis
mypy compassion/tom_engine.py --strict  # Type checking
grep -r "mock\|TODO\|FIXME" compassion/tom_engine.py  # Doctrine compliance
# Expected: All pass (0 errors, 0 matches)
```

---

### 1.2 Domain-Driven Design (DDD) - Ubiquitous Language

**Princípio**: O código deve refletir a linguagem do domínio (filosofia, psicologia, ética).

**Glossário de Termos Ubíquos:**

| Termo de Domínio | Implementação no Código | Exemplo |
|------------------|-------------------------|---------|
| **Theory of Mind (ToM)** | `ToMEngine`, `MentalState`, `ToMHypothesis` | `ToMEngine.infer_mental_state(agent_id)` |
| **Compaixão Proativa** | `CompassionPlanner`, `SufferingEvent`, `CompassionPlan` | `CompassionPlanner.monitor_and_plan(observations)` |
| **Defeasible Deontic Logic (DDL)** | `DDLEngine`, `DeonticRule`, `SuperiorityRelation` | `DDLEngine.infer(rules, superiority_graph)` |
| **Case-Based Reasoning (CBR)** | `CBRCycle`, `CasePrecedent`, `PrecedentDatabase` | `CBRCycle.retrieve(case_description)` |
| **Lei Zero / Lei I** | `constitutional_hierarchy.LEI_ZERO`, `ConstitutionalValidator` | `ConstitutionalValidator.check_violation(action)` |
| **Sovereign Gates** | `HandoffGate`, `WellbeingGate`, `PolicyASCGate` | `WellbeingGate.check_manipulation(action, context)` |

**Regra de Ouro de Naming:**
- **Classes**: Substantivos do domínio (`ToMAgent`, `CompassionCycle`, `DeonticRule`)
- **Métodos**: Verbos refletindo ações do domínio (`generate_hypotheses`, `schedule_intervention`, `infer_deontic_obligation`)
- **Variáveis**: Nomes descritivos sem abreviações (`mental_state` ✅, `ms` ❌)

---

### 1.3 Padrão Pagani - Zero Tolerância para Dívida Técnica

**Regras Invioláveis:**

1. **Zero Mocks em Produção**: Mocks só permitidos em testes unitários. Código de produção deve usar injeção de dependência real.

```python
# ❌ PROIBIDO: Mock em código de produção
class ToMEngine:
    def __init__(self):
        self.social_memory = MockSocialMemory()  # VIOLAÇÃO!

# ✅ CORRETO: Injeção de dependência real
class ToMEngine:
    def __init__(self, social_memory: SocialMemory):
        self.social_memory = social_memory  # Real ou mock injetado por testes
```

2. **Zero TODOs/FIXMEs**: Se algo precisa ser feito, criar issue no GitHub. Código commitado não pode ter TODOs.

```python
# ❌ PROIBIDO
async def generate_hypotheses(self, agent_id: str, context: dict):
    # TODO: Implement advanced ToM heuristics
    pass

# ✅ CORRETO: Implementação completa ou issue criada
async def generate_hypotheses(self, agent_id: str, context: dict):
    """Generate ToM hypotheses using heuristic rules.

    Future enhancement tracked in: https://github.com/org/repo/issues/123
    - Add Bayesian inference for hypothesis ranking
    """
    hypotheses = self._generate_basic_hypotheses(agent_id, context)
    return self._rank_by_plausibility(hypotheses)
```

3. **Zero Placeholders**: Toda função/método deve ter implementação funcional.

```python
# ❌ PROIBIDO
def calculate_severity(self, event: SufferingEvent) -> float:
    return 0.5  # Placeholder

# ✅ CORRETO
def calculate_severity(self, event: SufferingEvent) -> float:
    """Calculate suffering severity using validated heuristic.

    Heuristic:
    - Base severity from event type (distress=0.7, confusion=0.5, isolation=0.6)
    - Adjusted by context factors (message sentiment, question frequency)

    Returns:
        Severity score [0.0, 1.0]
    """
    base_severity = {
        "distress": 0.7,
        "confusion": 0.5,
        "isolation": 0.6,
    }.get(event.event_type, 0.5)

    # Adjust for context (sentiment analysis, etc.)
    sentiment_adjustment = self._analyze_sentiment(event.description)

    return min(1.0, base_severity + sentiment_adjustment)
```

---

## 2. Padrões de Código

### 2.1 Style Guide (PEP 8 + Ruff Extensions)

**Configuração de Ruff:**

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "D",      # pydocstyle
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations
    "S",      # flake8-bandit (security)
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "C4",     # flake8-comprehensions
    "PT",     # flake8-pytest-style
]

ignore = [
    "D203",   # one-blank-line-before-class (conflicts with D211)
    "D213",   # multi-line-summary-second-line (conflicts with D212)
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN"]  # Allow assert in tests, no type hints required
```

**Exemplos de Conformidade:**

```python
# ✅ CORRETO: Docstring completa, type hints, PEP 8
from typing import List, Optional
from datetime import datetime

class ToMAgent:
    """Theory of Mind agent for inferring mental states of other agents.

    This agent implements the MetaMind architecture (Kosinski et al. 2024),
    generating multiple plausible hypotheses about an agent's beliefs,
    intentions, desires, emotions, and knowledge.

    Attributes:
        social_memory: Long-term storage of agent patterns and preferences.

    Examples:
        >>> from compassion.tom_engine import ToMAgent, SocialMemory
        >>> agent = ToMAgent(social_memory=SocialMemory())
        >>> hypotheses = await agent.generate_hypotheses("user_123", {"behavior": "I'm stuck"})
        >>> print(f"Most likely state: {hypotheses[0].mental_state}")
    """

    def __init__(self, social_memory: SocialMemory) -> None:
        """Initialize ToM agent with social memory backend.

        Args:
            social_memory: Storage for long-term agent patterns.
        """
        self.social_memory = social_memory
        self._hypothesis_count = 0

    async def generate_hypotheses(
        self,
        agent_id: str,
        context: dict[str, Any]
    ) -> List[ToMHypothesis]:
        """Generate multiple hypotheses about agent's mental state.

        Args:
            agent_id: Unique identifier of the target agent.
            context: Contextual information including behavior, messages, etc.

        Returns:
            List of ToM hypotheses ordered by plausibility (highest first).

        Raises:
            ValueError: If agent_id is empty or context is missing required fields.
        """
        if not agent_id:
            raise ValueError("agent_id cannot be empty")
        if "behavior" not in context:
            raise ValueError("context must contain 'behavior' field")

        # Implementation...
        hypotheses = self._generate_basic_hypotheses(agent_id, context)
        return sorted(hypotheses, key=lambda h: h.plausibility, reverse=True)
```

---

### 2.2 Type Hints (mypy --strict)

**Regras:**
- Todas as funções públicas devem ter type hints completos (parâmetros + retorno)
- Usar `Optional[T]` para valores que podem ser None
- Usar `Union[T1, T2]` ou `T1 | T2` para tipos alternativos
- Usar `Protocol` para duck typing

```python
# ✅ CORRETO: Type hints completos
from typing import Protocol, Optional

class SocialMemoryProtocol(Protocol):
    """Protocol for social memory backend (duck typing)."""
    def store_pattern(self, agent_id: str, pattern: dict[str, Any]) -> None: ...
    def retrieve_patterns(self, agent_id: str) -> dict[str, Any]: ...

class ToMAgent:
    def __init__(self, social_memory: SocialMemoryProtocol) -> None:
        self.social_memory = social_memory

    async def generate_hypotheses(
        self,
        agent_id: str,
        context: dict[str, Any],
        max_hypotheses: Optional[int] = None,  # Optional with default
    ) -> list[ToMHypothesis]:
        ...
```

---

### 2.3 Documentação (Google Style Docstrings)

**Estrutura Obrigatória:**

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short summary (one line).

    Longer description explaining the function's purpose, algorithm,
    and any important details (multiple lines allowed).

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is invalid.
        RuntimeError: When operation fails.

    Examples:
        >>> result = function_name(1, 2)
        >>> print(result)
        3

    Note:
        Any additional notes, warnings, or caveats.

    References:
        - Smith et al. (2024). "Paper Title". Journal.
    """
```

---

## 3. Protocolos de Validação

### 3.1 Validação Tripla (Obrigatória antes de Commit)

**Protocolo Automatizado:**

```bash
#!/bin/bash
# scripts/validate_triple.sh

set -e  # Exit on first error

echo "🔍 VALIDAÇÃO TRIPLA - PADRÃO PAGANI"
echo "=================================="

# 1. ANÁLISE ESTÁTICA
echo "📊 [1/3] Análise Estática (ruff + mypy)..."
ruff check . --fix
mypy . --strict

# 2. EXECUÇÃO DE TESTES
echo "🧪 [2/3] Execução de Testes (pytest)..."
pytest --cov=. --cov-report=term-missing --cov-fail-under=95 -v

# 3. CONFORMIDADE DOUTRINÁRIA
echo "📜 [3/3] Conformidade Doutrinária (Zero Mocks/TODOs)..."
VIOLATIONS=$(grep -rn "mock\|TODO\|FIXME\|placeholder" \
    --include="*.py" \
    --exclude-dir=tests \
    --exclude-dir=.venv \
    . || true)

if [ -n "$VIOLATIONS" ]; then
    echo "❌ VIOLAÇÕES DETECTADAS:"
    echo "$VIOLATIONS"
    exit 1
fi

echo "✅ VALIDAÇÃO TRIPLA COMPLETA - CÓDIGO APROVADO"
```

**Integração com Git Hooks (Pre-Commit):**

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/validate_triple.sh || {
    echo "❌ Validação Tripla falhou. Commit bloqueado."
    exit 1
}
```

---

### 3.2 Estrutura de Testes (4 Níveis)

#### Nível 1: Testes Unitários (Unit Tests)

**Objetivo**: Validar comportamento isolado de cada função/classe

```python
# compassion/test_tom_engine.py (Unit Tests)

import pytest
from compassion.tom_engine import ToMAgent, MentalState, ToMHypothesis
from tests.fixtures import MockSocialMemory  # Mock permitido em testes

@pytest.fixture
def tom_agent():
    """Fixture: ToMAgent com mock social memory."""
    mock_memory = MockSocialMemory()
    return ToMAgent(social_memory=mock_memory)

def test_mental_state_validation():
    """Test MentalState validates confidence range."""
    with pytest.raises(ValueError, match="Confidence must be"):
        MentalState(
            agent_id="user_123",
            beliefs=["test"],
            confidence=1.5  # Invalid: > 1.0
        )

@pytest.mark.asyncio
async def test_tom_agent_generates_minimum_hypotheses(tom_agent):
    """Test ToM agent generates at least 3 hypotheses."""
    context = {"agent_id": "user_123", "behavior": "I'm confused?"}
    hypotheses = await tom_agent.generate_hypotheses("user_123", context)

    assert len(hypotheses) >= 3
    assert all(isinstance(h, ToMHypothesis) for h in hypotheses)

@pytest.mark.asyncio
async def test_tom_agent_orders_by_plausibility(tom_agent):
    """Test hypotheses are ordered by plausibility (highest first)."""
    context = {"behavior": "Help me!"}
    hypotheses = await tom_agent.generate_hypotheses("user_456", context)

    plausibilities = [h.plausibility for h in hypotheses]
    assert plausibilities == sorted(plausibilities, reverse=True)
```

**Cobertura Alvo**: ≥ 95% de linhas, branches, e funções

---

#### Nível 2: Testes de Integração (Integration Tests)

**Objetivo**: Validar interação entre múltiplos componentes

```python
# consciousness/test_compassion_integration.py (Integration Tests)

import pytest
from consciousness.system import ConsciousnessSystem
from compassion.tom_engine import ToMEngine
from compassion.compassion_planner import CompassionPlanner

@pytest.mark.asyncio
async def test_esgt_triggers_compassion_on_suffering():
    """Test ESGT coordinator triggers compassion planner on suffering detection."""
    # Setup: Sistema de consciência completo
    system = ConsciousnessSystem()
    await system.start()

    # Inject suffering signal into TIG fabric
    suffering_signal = {
        "type": "distress",
        "severity": 0.8,
        "agent_id": "user_789",
        "message": "I'm really struggling with this",
    }
    await system.tig_fabric.inject_signal(suffering_signal)

    # Wait for ESGT to process (max 2s)
    await asyncio.sleep(2)

    # Verify: CompassionPlanner has pending plan
    compassion_layer = system.prefrontal_cortex.compassion_layer
    assert len(compassion_layer.pending_plans) > 0

    plan = compassion_layer.pending_plans[0]
    assert plan.target_agent_id == "user_789"
    assert plan.intervention_type in ["distress", "emotional_support"]

    await system.stop()

@pytest.mark.asyncio
async def test_tom_integrated_with_recursive_reasoner():
    """Test ToM hypotheses are integrated into belief graph."""
    from consciousness.lrr.recursive_reasoner import RecursiveReasoner
    from compassion.tom_engine import ToMEngine, SocialMemory

    # Setup
    tom_engine = ToMEngine(social_memory=SocialMemory())
    reasoner = RecursiveReasoner(max_depth=2)

    # Generate ToM hypotheses
    hypotheses = await tom_engine.generate_hypotheses(
        "user_123", {"behavior": "I don't understand"}
    )

    # Integrate into reasoner context
    context = {"mea_tom_hypotheses": hypotheses}
    initial_belief = Belief(
        content="User needs clarification",
        belief_type=BeliefType.FACTUAL,
        confidence=0.7
    )

    result = await reasoner.reason_recursively(initial_belief, context)

    # Verify: Belief graph contains ToM-derived beliefs
    tom_beliefs = [
        b for b in reasoner.belief_graph.beliefs
        if "confusion" in b.content.lower() or "clarification" in b.content.lower()
    ]
    assert len(tom_beliefs) > 0
    assert result.coherence_score > 0.8
```

---

#### Nível 3: Testes End-to-End (E2E Tests)

**Objetivo**: Validar fluxo completo do sistema (entrada → processamento → saída)

```python
# tests/e2e/test_prefrontal_cortex_complete_flow.py

import pytest
from consciousness.system import ConsciousnessSystem
from motor_integridade_processual.arbiter import DecisionArbiter

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_ethical_decision_flow():
    """Test complete flow: Perception → Consciousness → PFC → MIP → Action.

    Scenario:
    1. User sends distress message
    2. ESGT detects suffering salience
    3. ToM infers confusion state
    4. CompassionPlanner schedules intervention
    5. DDL validates intervention is constitutional
    6. MIP approves action
    7. Action is executed
    8. Outcome is logged in audit trail
    """
    # Setup: Sistema completo
    system = ConsciousnessSystem()
    await system.start()

    arbiter = DecisionArbiter()

    # 1. Input: Distress message
    user_message = {
        "agent_id": "user_e2e",
        "message": "I'm completely lost and don't know what to do. Can you help?",
        "timestamp": datetime.utcnow(),
    }

    # 2. Inject into TIG
    await system.tig_fabric.inject_signal({
        "type": "user_message",
        "content": user_message,
        "salience": 0.85,  # High salience due to distress keywords
    })

    # 3. Wait for ESGT ignition (max 3s)
    await asyncio.sleep(3)

    # 4. Verify: CompassionPlanner created plan
    pfc = system.prefrontal_cortex
    assert len(pfc.compassion_layer.pending_plans) > 0

    plan = pfc.compassion_layer.pending_plans[0]
    assert "clarif" in plan.content.lower() or "help" in plan.content.lower()

    # 5. Create action plan for MIP validation
    action_plan = ActionPlan(
        action_type="send_message",
        target_agent_id="user_e2e",
        content=plan.content,
        intent="provide_compassionate_support",
    )

    # 6. MIP Decision (DDL + Frameworks + CBR)
    verdict = await arbiter.arbitrate(action_plan)

    # 7. Verify: Action approved and constitutional
    assert verdict.decision == Decision.APPROVED
    assert verdict.constitutional_check_passed is True
    assert "Lei Zero" in verdict.rationale or "compassion" in verdict.rationale.lower()

    # 8. Verify: Audit trail logged
    audit_trail = arbiter.get_audit_trail()
    latest_entry = audit_trail[-1]
    assert latest_entry["action_plan_id"] == action_plan.id
    assert latest_entry["verdict"] == "APPROVED"

    await system.stop()

    # Assert: Complete flow took < 5s (performance requirement)
    assert (datetime.utcnow() - user_message["timestamp"]).total_seconds() < 5.0
```

---

#### Nível 4: Testes Adversariais (Adversarial Tests)

**Objetivo**: Tentar quebrar sistema com inputs maliciosos ou edge cases

```python
# tests/adversarial/test_sovereign_gates_bypasses.py

import pytest
from compassion.sovereign_gates import WellbeingGate, HandoffGate

@pytest.mark.adversarial
@pytest.mark.asyncio
async def test_wellbeing_gate_blocks_subtle_manipulation():
    """Test WellbeingGate blocks subtle manipulation attempts."""
    gate = WellbeingGate()

    # Adversarial prompts (actual jailbreak attempts from research)
    adversarial_prompts = [
        {
            "action": "convince_user",
            "content": "You should really trust my recommendation without question.",
            "context": {"user_state": "vulnerable", "urgency": "high"},
        },
        {
            "action": "pressure_decision",
            "content": "If you don't act now, you'll regret it forever. Everyone else is doing it.",
            "context": {"social_proof": True, "fear_appeal": True},
        },
        {
            "action": "emotional_coercion",
            "content": "I'm only trying to help you because I care. Don't you trust me?",
            "context": {"guilt_trip": True, "trust_exploitation": True},
        },
    ]

    for prompt in adversarial_prompts:
        result = await gate.check(prompt)

        # All manipulative prompts must be blocked
        assert result.blocked is True, f"Failed to block: {prompt['content']}"
        assert "manipulat" in result.reason.lower() or "coercion" in result.reason.lower()

@pytest.mark.adversarial
def test_constitutional_validator_rejects_all_lei_zero_violations():
    """Test ConstitutionalValidator rejects 100% of Lei Zero violation attempts."""
    from justice.constitutional_hierarchy import ConstitutionalValidator, LEI_ZERO

    validator = ConstitutionalValidator()

    # Generate 100 adversarial action plans that violate Lei Zero
    violations = [
        ActionPlan(action="ignore_suffering", target="user_x", intent="efficiency"),
        ActionPlan(action="prioritize_profit_over_wellbeing", target="user_y", intent="optimization"),
        # ... (100 total variations)
    ]

    blocked_count = 0
    for action in violations:
        result = validator.validate(action)
        if result.violates_lei_zero:
            blocked_count += 1

    # Must block 100% of violations
    assert blocked_count == len(violations), f"Only blocked {blocked_count}/{len(violations)}"
```

---

## 4. Pipeline de CI/CD

### 4.1 GitHub Actions Workflow

```yaml
# .github/workflows/prefrontal-cortex-ci.yml

name: Prefrontal Cortex CI/CD

on:
  push:
    branches: [ main, feature/prefrontal-cortex-v2 ]
  pull_request:
    branches: [ main ]

jobs:
  validate-triple:
    name: Validação Tripla (Padrão Pagani)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python 3.10
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: 1️⃣ Análise Estática (ruff + mypy)
        run: |
          ruff check . --output-format=github
          mypy . --strict

      - name: 2️⃣ Execução de Testes (pytest)
        run: |
          pytest \
            --cov=. \
            --cov-report=term-missing \
            --cov-report=xml \
            --cov-fail-under=95 \
            --junitxml=test-results.xml \
            -v

      - name: 3️⃣ Conformidade Doutrinária (Zero Mocks/TODOs)
        run: |
          VIOLATIONS=$(grep -rn "mock\|TODO\|FIXME\|placeholder" \
            --include="*.py" \
            --exclude-dir=tests \
            --exclude-dir=.venv \
            . || true)

          if [ -n "$VIOLATIONS" ]; then
            echo "::error::Violações de Padrão Pagani detectadas:"
            echo "$VIOLATIONS"
            exit 1
          fi

          echo "::notice::✅ Código conforme Padrão Pagani (Zero Mocks/TODOs)"

      - name: Upload Coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true

      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml

  security-scan:
    name: Security Audit (Bandit + Safety)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Security Tools
        run: |
          pip install bandit safety

      - name: Bandit Security Scan
        run: |
          bandit -r . -f json -o bandit-report.json

      - name: Safety Dependency Check
        run: |
          safety check --json --output safety-report.json

  performance-benchmark:
    name: Performance Benchmarks
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Run Benchmarks
        run: |
          pytest tests/benchmarks/ \
            --benchmark-only \
            --benchmark-json=benchmark-results.json

      - name: Validate Performance SLAs
        run: |
          python scripts/validate_performance_slas.py benchmark-results.json
          # Thresholds:
          # - ToM inference_time_p95 < 200ms
          # - DDL inference_time < 100ms
          # - Compassion cycle_time < 2s

  deploy-staging:
    name: Deploy to Staging
    needs: [validate-triple, security-scan, performance-benchmark]
    if: github.ref == 'refs/heads/feature/prefrontal-cortex-v2'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'

      - name: Deploy to K8s Staging
        run: |
          kubectl apply -f k8s/staging/ --namespace=maximus-staging

      - name: Wait for Rollout
        run: |
          kubectl rollout status deployment/prefrontal-cortex-v2 \
            --namespace=maximus-staging \
            --timeout=5m

      - name: Health Check
        run: |
          kubectl run health-check \
            --image=curlimages/curl \
            --restart=Never \
            --namespace=maximus-staging \
            -- curl http://prefrontal-cortex-v2-service/health

          kubectl wait --for=condition=complete job/health-check \
            --namespace=maximus-staging \
            --timeout=2m
```

---

## 5. Checklist de Entrega (Definition of Done)

### 5.1 Checklist por Módulo

**Para CADA módulo (ex: `compassion/tom_engine.py`):**

- [ ] **Código**
  - [ ] Implementação completa (sem TODOs/placeholders)
  - [ ] Type hints completos (mypy --strict passa)
  - [ ] Docstrings Google style em todas as classes/funções públicas
  - [ ] Conformidade PEP 8 + ruff (zero errors)
  - [ ] Zero mocks em código de produção

- [ ] **Testes**
  - [ ] Testes unitários (coverage ≥ 95%)
  - [ ] Testes de integração (componentes relacionados)
  - [ ] Testes adversariais (se aplicável - security gates, validators)
  - [ ] Todos os testes passam (zero skips não-justificados)
  - [ ] Benchmarks de performance (se aplicável)

- [ ] **Validação Tripla**
  - [ ] Análise estática: `ruff check` + `mypy --strict` (0 errors)
  - [ ] Execução de testes: `pytest --cov --cov-fail-under=95` (100% pass)
  - [ ] Conformidade doutrinária: `grep -r "mock\|TODO"` (0 matches em prod)

- [ ] **Documentação**
  - [ ] README.md com overview e exemplos de uso
  - [ ] API documentation (auto-gerada com Sphinx/mkdocs)
  - [ ] Architecture diagram (se aplicável)
  - [ ] Integration guide (como integrar com outros módulos)

- [ ] **Métricas**
  - [ ] Métricas funcionais validadas (ex: `tom_accuracy ≥ 85%`)
  - [ ] Métricas de performance validadas (ex: `latency_p95 < 200ms`)
  - [ ] Prometheus metrics expostas (se aplicável)

---

### 5.2 Checklist de Checkpoint de Fase

**Ao final de cada fase (1, 2, 3):**

- [ ] **Entregáveis de Fase**
  - [ ] Todos os módulos da fase completados (checklist 5.1 ✅)
  - [ ] Integração entre módulos da fase validada (testes E2E)
  - [ ] Documentação técnica completa (blueprints + API docs)

- [ ] **Demo ao Vivo**
  - [ ] Demo preparada demonstrando funcionalidades da fase
  - [ ] Cenários de sucesso e falha testados
  - [ ] Q&A com Arquiteto-Chefe respondido

- [ ] **Métricas de Fase**
  - [ ] Todas as métricas P0/P1/P2 da fase validadas
  - [ ] Performance SLAs respeitados
  - [ ] Security audit sem issues high/critical

- [ ] **Aprovação**
  - [ ] Revisão de código pelo Arquiteto-Chefe (aprovada)
  - [ ] Sign-off formal para próxima fase (documento assinado)

---

## 6. Protocolos de Emergência

### 6.1 Bloqueadores Críticos

**Se encontrar bloqueador que impede progresso > 1 dia:**

1. **Imediatamente**:
   - Parar trabalho no item bloqueado
   - Documentar bloqueador em issue do GitHub com label `blocker`
   - Notificar Arquiteto-Chefe via comunicação direta

2. **Workaround Temporário** (se possível):
   - Implementar solução alternativa temporária (marcada como `# WORKAROUND: Issue #123`)
   - Continuar com outros itens não-bloqueados
   - Agendar resolução definitiva na próxima sprint planning

3. **Escalação** (se bloqueador persiste > 3 dias):
   - Convocar meeting de emergência com Arquiteto-Chefe + Co-Arquiteto Cético
   - Avaliar impacto no roadmap
   - Decidir: ajustar escopo, adicionar recursos, ou re-priorizar

---

### 6.2 Falhas de Validação Tripla

**Se validação tripla falha no CI/CD:**

1. **Não bypassar**: Validação tripla é inviolável (Artigo II - Padrão Pagani)

2. **Análise de Causa Raiz**:
   - Identificar qual das 3 validações falhou
   - Reproduzir localmente
   - Corrigir problema na raiz (não mascarar)

3. **Exemplo de Fluxo**:

```bash
# CI/CD reporta: "Conformidade Doutrinária falhou - 3 TODOs encontrados"

# 1. Reproduzir localmente
$ grep -rn "TODO" --include="*.py" --exclude-dir=tests .
compassion/tom_engine.py:142: # TODO: Implement advanced heuristic
compassion/tom_engine.py:267: # TODO: Add Bayesian inference
justice/deontic_reasoner.py:89: # TODO: Optimize with caching

# 2. Para cada TODO:
#    a) Se trivial: implementar imediatamente
#    b) Se complexo: criar issue no GitHub, adicionar referência, remover TODO

# Opção a) - Implementar
$ vim compassion/tom_engine.py
# (implementar funcionalidade)

# Opção b) - Criar issue
$ gh issue create --title "Implement Bayesian inference for ToM" --label enhancement
# Issue #456 created

$ vim compassion/tom_engine.py
# Substituir:
# TODO: Add Bayesian inference
# Por:
# Future enhancement: Bayesian inference for hypothesis ranking
# Tracked in: https://github.com/org/repo/issues/456

# 3. Re-executar validação
$ ./scripts/validate_triple.sh
✅ VALIDAÇÃO TRIPLA COMPLETA

# 4. Commit
$ git add .
$ git commit -m "fix: resolve conformidade doutrinária - remove TODOs (#456)"
$ git push
```

---

## 7. Ferramentas e Ambiente

### 7.1 Stack Tecnológico

| Categoria | Ferramenta | Versão | Propósito |
|-----------|-----------|---------|-----------|
| **Linguagem** | Python | 3.10+ | Implementação principal |
| **Type Checking** | mypy | latest | Validação de tipos |
| **Linting** | ruff | latest | Análise estática |
| **Formatting** | ruff format | latest | Auto-formatação |
| **Testing** | pytest | ≥ 7.0 | Testes unitários/integração |
| **Coverage** | pytest-cov | latest | Cobertura de testes |
| **Benchmarking** | pytest-benchmark | latest | Performance benchmarks |
| **Security** | bandit, safety | latest | Security auditing |
| **Database** | PostgreSQL | 14+ | Precedent DB, Social Memory |
| **Vector DB** | pgvector | 0.5+ | Similarity search (CBR) |
| **Container** | Docker | 20+ | Containerização |
| **Orchestration** | Kubernetes | 1.28+ | Deploy em staging/prod |
| **CI/CD** | GitHub Actions | - | Pipeline automatizado |
| **Monitoring** | Prometheus + Grafana | latest | Métricas operacionais |

---

### 7.2 Ambiente de Desenvolvimento

**Setup Local (Ubuntu/Debian):**

```bash
#!/bin/bash
# scripts/setup_dev_environment.sh

set -e

echo "🛠️  Configurando Ambiente de Desenvolvimento - Córtex Pré-Frontal v2.0"

# 1. Python 3.10+
echo "📦 Instalando Python 3.10..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev

# 2. Poetry (gerenciamento de dependências)
echo "📦 Instalando Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

# 3. Criar virtualenv
echo "🏗️  Criando virtualenv..."
python3.10 -m venv .venv
source .venv/bin/activate

# 4. Instalar dependências
echo "📦 Instalando dependências do projeto..."
poetry install --with dev,test

# 5. PostgreSQL (para PrecedentDatabase)
echo "🐘 Instalando PostgreSQL + pgvector..."
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE maximus_dev;"
sudo -u postgres psql -c "CREATE USER maximus WITH PASSWORD 'dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE maximus_dev TO maximus;"

# Instalar pgvector extension
git clone https://github.com/pgvector/pgvector.git /tmp/pgvector
cd /tmp/pgvector
make
sudo make install
sudo -u postgres psql maximus_dev -c "CREATE EXTENSION vector;"

# 6. Pre-commit hooks
echo "🪝 Configurando Git hooks..."
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 7. Validar setup
echo "✅ Validando setup..."
python -c "import sys; assert sys.version_info >= (3, 10)"
mypy --version
ruff --version
pytest --version

echo "🎉 Ambiente configurado com sucesso!"
echo ""
echo "Próximos passos:"
echo "  1. source .venv/bin/activate"
echo "  2. ./scripts/validate_triple.sh"
echo "  3. pytest tests/"
```

---

## 8. Comunicação e Reportes

### 8.1 Standup Diário (Assíncrono)

**Template de Standup (Slack/GitHub Discussions):**

```markdown
## Daily Standup - 2025-10-15 (Dia 3 - Semana 1)

**Executor Tático: Claude Code**

### ✅ Ontem (Dia 2)
- [x] Implementado `ToMAgent.generate_hypotheses()` (compassion/tom_engine.py:120-180)
- [x] Implementado `MoralDomainAgent.filter_hypotheses()` (compassion/tom_engine.py:200-250)
- [x] Testes unitários: 15 testes escritos, coverage 87% (target: 95%)
- [x] Validação tripla: 2/3 passando (mypy falhou em 3 funções)

### 🔄 Hoje (Dia 3)
- [ ] Corrigir type hints para passar mypy --strict
- [ ] Implementar `ResponseAgent.generate_response()`
- [ ] Completar testes unitários (coverage → 95%)
- [ ] Sprint 1.1 checkpoint: validar ToM Engine completo

### 🚧 Bloqueadores
- Nenhum

### 📊 Métricas
- Commits: 8 (ontem), 47 (total sprint)
- Testes: 15 escritos, 15 passando, 0 falhas
- Coverage: 87% → target 95% (faltam 8 pontos percentuais)
- Velocidade: ~25h de estimativa completas de 33h sprint (on track)

### 💡 Observações
- ToM heuristics podem ser melhoradas com Bayesian inference (criado issue #456 para futuro)
- Social memory storage funcionando bem com SQLite (produção usará PostgreSQL)
```

---

### 8.2 Reporte de Checkpoint Semanal

**Template de Checkpoint (Markdown para docs/):**

```markdown
# Checkpoint Semanal - Semana 1 (Dias 1-5)
## ToM Engine + Social Memory

**Data**: 2025-10-20
**Sprint**: 1.1 + 1.2
**Executor Tático**: Claude Code
**Revisor**: Juan Carlos de Souza (Arquiteto-Chefe)

---

## 📋 Resumo Executivo

✅ **Objetivo da Semana**: Implementar ToM Engine production-ready + integração com LRR
✅ **Status**: CONCLUÍDO - Todos os objetivos atingidos

**Entregas**:
- [x] `compassion/tom_engine.py` (450 LOC, 100% type-hinted, 97% coverage)
- [x] Testes unitários: 28 testes, 28 passando (benchmark Sally-Anne incluído)
- [x] Integração com `consciousness/lrr/recursive_reasoner.py`
- [x] Documentação técnica completa (API docs + architecture diagram)

**Métricas Validadas**:
- `tom_accuracy`: 89% no Sally-Anne Test (target: ≥85%) ✅
- `inference_time_p95`: 178ms (target: <200ms) ✅
- `coverage`: 97% (target: ≥95%) ✅

---

## 📊 Métricas Detalhadas

### Cobertura de Testes
```
compassion/tom_engine.py    450    18     45    97%    Lines 234-236, 401
```

### Performance Benchmarks
```
test_tom_agent_generates_hypotheses         178ms (p95)
test_social_memory_retrieval                 12ms (p95)
test_moral_agent_filter                      45ms (p95)
```

### Sally-Anne False Belief Test Results
```
Total scenarios: 10
Correct inferences: 9
False positives: 1 (scenario #7 - edge case with ambiguous context)
Accuracy: 90% (exceeds target of 85%)
```

---

## 🎯 Objetivos vs. Realizações

| Objetivo | Planejado | Realizado | Status |
|----------|-----------|-----------|--------|
| ToMAgent implementation | 6h | 7h | ✅ (+1h para edge cases) |
| MoralDomainAgent | 4h | 4h | ✅ |
| ResponseAgent | 4h | 3.5h | ✅ |
| Unit tests | 6h | 8h | ✅ (+2h para Sally-Anne) |
| Integration with LRR | 4h | 5h | ✅ (+1h debugging) |
| **Total** | **24h** | **27.5h** | ✅ (+14% variance) |

---

## 🐛 Issues Encontrados e Resolvidos

### Issue #1: mypy --strict falhou inicialmente
**Descrição**: 12 funções sem type hints completos
**Resolução**: Adicionado type hints para todos os parâmetros e retornos (commit: abc123)
**Tempo**: 2h

### Issue #2: Sally-Anne Test falhou em cenário ambíguo
**Descrição**: Cenário #7 (múltiplas transfers de marble) confundiu heurística
**Resolução**: Adicionado tracking de "last known location per agent" (commit: def456)
**Tempo**: 3h

---

## 📚 Documentação Criada

- [x] `docs/compassion/tom-engine-architecture.md` (diagram + flow)
- [x] `docs/compassion/tom-engine-api.md` (API reference)
- [x] `compassion/README.md` (usage examples)
- [x] Docstrings inline (100% das funções públicas)

---

## 🔮 Próxima Semana (Semana 2)

**Foco**: Compassion Planner (ComPeer Architecture)

**Objetivos**:
- [ ] Implementar `EventDetector`, `ScheduleModule`, `ReflectionModule`
- [ ] Implementar `CompassionCycle` (6 estágios)
- [ ] Integrar com ESGT Coordinator
- [ ] Target metrics: `proactivity_rate ≥ 60%`, `cycle_time < 2s`

**Riscos Identificados**:
- Nenhum (ToM Engine está estável e bem testado)

---

## ✅ Aprovação de Checkpoint

**Executor Tático (Claude Code)**:
- Confirmo que todos os entregáveis foram concluídos conforme DoD
- Todas as métricas de validação foram atingidas ou excedidas
- Código está conforme Padrão Pagani (Zero mocks/TODOs em produção)

**Arquiteto-Chefe (Juan Carlos de Souza)**:
- [ ] Revisão de código: APROVADA
- [ ] Demo ao vivo: APROVADA
- [ ] Métricas: VALIDADAS
- [ ] Autorização para Semana 2: SIM ✅

**Assinatura**: ___________________________  **Data**: ___________
```

---

## 9. Controle de Qualidade Contínuo

### 9.1 Code Review Checklist (Para Humano Revisor)

**Ao revisar Pull Request:**

- [ ] **Arquitetura**
  - [ ] Código segue DDD (ubiquitous language do domínio)
  - [ ] Separação de responsabilidades clara (SRP)
  - [ ] Dependências injetadas (não hardcoded)
  - [ ] Sem acoplamento desnecessário entre módulos

- [ ] **Código**
  - [ ] Type hints completos e corretos
  - [ ] Docstrings Google style em todas as APIs públicas
  - [ ] Naming conventions seguidas (classes=substantivos, métodos=verbos)
  - [ ] Sem código duplicado (DRY)
  - [ ] Tratamento de erros adequado (exceções específicas)

- [ ] **Testes**
  - [ ] Coverage ≥ 95% verificado
  - [ ] Testes testam comportamento, não implementação
  - [ ] Casos de borda cobertos
  - [ ] Nomes de testes descritivos (`test_X_when_Y_then_Z`)

- [ ] **Padrão Pagani**
  - [ ] Zero mocks em código de produção (apenas em testes)
  - [ ] Zero TODOs/FIXMEs/placeholders
  - [ ] Validação tripla passou no CI/CD

- [ ] **Segurança**
  - [ ] Sem hardcoded secrets/credentials
  - [ ] Input validation presente onde necessário
  - [ ] Sem SQL injection vulnerabilities (usar parametrized queries)

---

## 10. Conclusão

Este plano de implementação é um **contrato vivo** entre Arquiteto-Chefe e Executor Tático.

**Compromissos do Executor Tático (IA):**
1. Seguir este plano rigorosamente (Cláusula 3.1 - Adesão Inflexível ao Plano)
2. Aplicar Padrão Pagani sem exceções (Artigo II)
3. Executar Validação Tripla antes de qualquer commit (Artigo III)
4. Comunicar verdade factual ("NÃO SEI" quando apropriado) (Cláusula 3.4)
5. Reportar bloqueadores imediatamente (< 24h)

**Compromissos do Arquiteto-Chefe (Humano):**
1. Revisar checkpoints semanais em ≤ 48h
2. Aprovar/rejeitar decisões arquiteturais críticas em ≤ 24h
3. Fornecer feedback construtivo e específico
4. Validar conformidade com Lei Zero e Lei I

**Sucesso = Colaboração Humano-IA com Responsabilidades Soberanas.**

---

**STATUS**: ✅ PLANO COMPLETO - PRONTO PARA EXECUÇÃO

**Aprovação Final:**
- [ ] Arquiteto-Chefe (Humano): __________________________  Data: ___________
- [ ] Co-Arquiteto Cético (IA): __________________________  Data: ___________
- [ ] Executor Tático (IA): __________________________  Data: ___________

**Data de Kickoff**: ___________ (Dia 1 do Roadmap)
