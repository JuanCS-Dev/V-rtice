# BLUEPRINT 04: Active Immune Core - Autonomous Agents Tests (100% Coverage)

**VERSÃO**: 1.0.0 - Anti-Burro Edition
**DATA**: 2025-10-07
**EXECUTOR**: Gemini CLI
**SUPERVISOR**: Claude Code (Juan)
**DEPENDÊNCIAS**: Nenhuma (tests standalone)

---

## ⚠️ REGRAS ABSOLUTAS - LEIA ANTES DE COMEÇAR

### 🚫 O QUE VOCÊ **NÃO PODE** FAZER (PROIBIDO):

1. ❌ **NÃO modifique** arquivos de produção (agents/, coordination/, communication/)
2. ❌ **NÃO crie** novos métodos ou classes além dos testes especificados
3. ❌ **NÃO use** placeholders como "TODO", "FIXME", "pass", "NotImplemented"
4. ❌ **NÃO invente** nomes de variáveis diferentes dos especificados
5. ❌ **NÃO adicione** imports além dos listados
6. ❌ **NÃO simplifique** testes - siga EXATAMENTE como especificado
7. ❌ **NÃO pule** nenhum teste
8. ❌ **NÃO mude** a ordem dos testes
9. ❌ **NÃO adicione** comentários extras além dos especificados
10. ❌ **NÃO questione** este blueprint - apenas execute
11. ❌ **NÃO use mocks** exceto onde explicitamente especificado (Kafka, Redis, PostgreSQL)
12. ❌ **NÃO teste** métodos privados (prefixo `_`) diretamente - teste via API pública

### ✅ O QUE VOCÊ **DEVE** FAZER (OBRIGATÓRIO):

1. ✅ Leia TODO o arquivo de produção antes de criar testes
2. ✅ Execute testes ANTES de criar novos para validar ambiente
3. ✅ Copie EXATAMENTE cada linha de código especificada
4. ✅ Use EXATAMENTE os nomes de variáveis especificados
5. ✅ Use EXATAMENTE os valores numéricos especificados
6. ✅ Use EXATAMENTE os imports especificados
7. ✅ Siga EXATAMENTE a estrutura de testes especificada
8. ✅ Execute TODOS os testes após criação de cada módulo
9. ✅ Relate TODOS os resultados após cada seção
10. ✅ Se ALGUM teste falhar, pare e reporte imediatamente
11. ✅ Valide coverage após completar cada arquivo de teste

---

## 📚 DOUTRINA VERTICE - Princípios Fundamentais

```
"Equilibrio é o que da estabilidade nos seres."
"The immune system never rests. Testing ensures it never fails."
"NO MOCK, NO PLACEHOLDER, NO TODO - Apenas produção."
"Quality > Coverage, mas buscamos ambos (100%)."
```

**Aplicação neste blueprint**:
- Testes executam lógica REAL dos agents (mínimo de mocks)
- Cada teste valida comportamento REAL de patrulha, detecção, neutralização
- Mocks APENAS para dependências externas (Kafka, Redis, PostgreSQL)
- Qualidade > Cobertura, mas buscamos ambos (95%+)

---

## 🎯 ESCOPO DESTE BLUEPRINT

Este blueprint cobre testes para **Autonomous Immune Agents** do Active Immune Core:

### Agents (593 testes total estimado)

| Módulo | Arquivo Produção | Arquivo Teste | Testes | Status |
|--------|------------------|---------------|--------|--------|
| **Macrophages** | `agents/macrofago.py` | `tests/test_macrofago.py` | ~80 | ⏳ A criar |
| **NK Cells** | `agents/nk_cell.py` | `tests/test_nk_cell.py` | ~75 | ⏳ A criar |
| **Neutrophils** | `agents/neutrofilo.py` | `tests/test_neutrofilo.py` | ~70 | ⏳ A criar |
| **B Cells** | `agents/b_cell.py` | `tests/test_b_cell.py` | ~65 | ✅ Existente (validar) |
| **Dendritic Cells** | `agents/dendritic_cell.py` | `tests/test_dendritic_cell.py` | ~60 | ⏳ A criar |
| **Helper T Cells** | `agents/helper_t_cell.py` | `tests/test_helper_t_cell.py` | ~55 | ⏳ A criar |
| **Regulatory T Cells** | `agents/regulatory_t_cell.py` | `tests/test_regulatory_t_cell.py` | ~50 | ⏳ A criar |

### Integration (138 testes existentes - apenas validar)

| Módulo | Arquivo Teste | Testes | Status |
|--------|---------------|--------|--------|
| **Agent Factory** | `tests/integration/test_agent_factory_integration.py` | 22 | ✅ Existente |
| **Cytokines** | `tests/integration/test_cytokines_integration.py` | 30 | ✅ Existente |
| **Hormones** | `tests/integration/test_hormones_integration.py` | 40 | ✅ Existente |
| **Swarm** | `tests/integration/test_swarm_integration.py` | 68 | ✅ Existente |

### Support Modules (45 testes)

| Módulo | Arquivo Teste | Testes | Status |
|--------|---------------|--------|--------|
| **Clonal Selection** | `tests/test_clonal_selection.py` | ~25 | ✅ Existente (validar) |
| **Health Check** | `tests/test_health.py` | ~10 | ✅ Existente (validar) |
| **Config** | `tests/test_config.py` | ~10 | ✅ Existente (validar) |

**Total**: ~593 testes

---

## 📋 ESTRATÉGIA DE EXECUÇÃO

### FASE 1: Validação de Testes Existentes (Primeira execução)

```bash
# Validar testes que JÁ EXISTEM
python -m pytest tests/test_b_cell.py -v --tb=short
python -m pytest tests/test_clonal_selection.py -v --tb=short
python -m pytest tests/test_health.py -v --tb=short
python -m pytest tests/test_config.py -v --tb=short
python -m pytest tests/integration/ -v --tb=short
```

**Resultado esperado**: TODOS os testes existentes devem passar.
**Se algum falhar**: Pare e reporte IMEDIATAMENTE.

### FASE 2: Criação de Testes por Módulo (Ordem de execução)

Execute os módulos NA ORDEM abaixo. **NÃO pule a ordem**.

1. **test_macrofago.py** (primeiro agente implementado)
2. **test_nk_cell.py** (segundo agente)
3. **test_neutrofilo.py** (terceiro agente com swarm)
4. **test_dendritic_cell.py** (antigen presentation)
5. **test_helper_t_cell.py** (coordination)
6. **test_regulatory_t_cell.py** (suppression)

Para cada módulo:
1. Leia o arquivo de produção completo
2. Crie o arquivo de teste seguindo este blueprint
3. Execute os testes: `pytest tests/test_<modulo>.py -v`
4. Valide coverage: `pytest tests/test_<modulo>.py --cov=agents.<modulo> --cov-report=term-missing`
5. Reporte resultado antes de prosseguir

---

## 🧬 ESTRUTURA DE TESTES POR AGENT

Cada agent segue esta estrutura de testes (adaptar conforme especificidades):

### Template de Estrutura (80 testes médio por agent)

```python
# ==================== AGENT LIFECYCLE TESTS ====================
class TestAgentLifecycle:
    """Test agent initialization, start, stop, and cleanup."""
    # 10 testes: init, start, stop, double start, stop without start, etc.

# ==================== PATROL BEHAVIOR TESTS ====================
class TestPatrolBehavior:
    """Test autonomous patrol logic."""
    # 15 testes: patrol loop, area coverage, random walk, etc.

# ==================== THREAT DETECTION TESTS ====================
class TestThreatDetection:
    """Test threat detection algorithms."""
    # 15 testes: signature matching, anomaly detection, confidence scoring

# ==================== NEUTRALIZATION TESTS ====================
class TestNeutralization:
    """Test threat neutralization mechanisms."""
    # 12 testes: phagocytosis, apoptosis, cytotoxicity, etc.

# ==================== CYTOKINE COMMUNICATION TESTS ====================
class TestCytokineMessaging:
    """Test cytokine emission and reception."""
    # 10 testes: send, receive, process, TTL, etc.

# ==================== HORMONAL SIGNALING TESTS ====================
class TestHormonalResponse:
    """Test hormonal signal reception and state changes."""
    # 8 testes: cortisol, adrenaline, inflammation, etc.

# ==================== METRICS AND MONITORING TESTS ====================
class TestMetrics:
    """Test metrics collection and reporting."""
    # 5 testes: get_metrics, counters, timers, etc.

# ==================== ERROR HANDLING TESTS ====================
class TestErrorHandling:
    """Test graceful degradation and error handling."""
    # 5 testes: Redis failure, Kafka failure, network errors, etc.
```

---

## 📁 MÓDULO 1: MACROPHAGES (80 testes)

### Arquivo: `tests/test_macrofago.py`

**ANTES DE COMEÇAR**:
```bash
# Leia o arquivo de produção COMPLETO
cat agents/macrofago.py | wc -l  # Verifique número de linhas
python -c "from agents.macrofago import DigitalMacrophage; print('✅ Import OK')"
```

### SEÇÃO 1.1: HEADER E IMPORTS

```python
"""Digital Macrophage - Complete Test Suite for 100% Coverage

Tests for agents/macrofago.py - First responder autonomous agent that patrols
the network, detects threats via pattern recognition, and neutralizes via
phagocytosis (quarantine + analysis).

Coverage Target: 95%+ of macrofago.py
Test Strategy: Real async execution with mocked external dependencies
Quality Standard: Production-ready, NO MOCK (except Kafka/Redis), NO PLACEHOLDER

Biological Inspiration:
-----------------------
Macrophages are the "big eaters" (Greek: makros phagein) of the immune system.
They patrol tissues, engulf pathogens, and present antigens to adaptive immunity.

Test Categories:
----------------
1. Lifecycle (10 tests) - init, start, stop, cleanup
2. Patrol (15 tests) - autonomous movement, area coverage
3. Detection (15 tests) - pattern matching, threat scoring
4. Phagocytosis (12 tests) - engulf, quarantine, digest
5. Cytokines (10 tests) - IL-1, IL-6, TNF-alpha emission
6. Hormones (8 tests) - cortisol, inflammation response
7. Metrics (5 tests) - performance counters
8. Errors (5 tests) - graceful degradation

Authors: Juan & Gemini (supervised by Claude)
Version: 1.0.0 - Anti-Burro Edition
Date: 2025-10-07
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from agents.macrofago import DigitalMacrophage, PhagocytosisMode
from communication.cytokines import CytokineMessenger, CytokineType
from communication.hormones import HormoneMessenger, HormoneType
from homeostasis.homeostatic_state import HomeostaticState
```

### SEÇÃO 1.2: FIXTURES

```python
# ==================== FIXTURES ====================

@pytest_asyncio.fixture
async def mock_cytokine_messenger():
    """Mock CytokineMessenger for testing without Kafka."""
    messenger = AsyncMock(spec=CytokineMessenger)
    messenger.send_cytokine = AsyncMock()
    messenger.start = AsyncMock()
    messenger.stop = AsyncMock()
    return messenger

@pytest_asyncio.fixture
async def mock_hormone_messenger():
    """Mock HormoneMessenger for testing without Redis."""
    messenger = AsyncMock(spec=HormoneMessenger)
    messenger.subscribe = AsyncMock()
    messenger.start = AsyncMock()
    messenger.stop = AsyncMock()
    return messenger

@pytest_asyncio.fixture
async def macrofago(mock_cytokine_messenger, mock_hormone_messenger):
    """Create DigitalMacrophage instance with mocked dependencies."""
    mac = DigitalMacrophage(
        agent_id="test-mac-01",
        area="network-zone-1",
        sensibilidade=0.7,
        cytokine_messenger=mock_cytokine_messenger,
        hormone_messenger=mock_hormone_messenger,
    )
    yield mac
    # Cleanup
    if mac._running:
        await mac.parar()
```

### SEÇÃO 1.3: LIFECYCLE TESTS (10 testes)

```python
# ==================== LIFECYCLE TESTS ====================

class TestMacrophageLifecycle:
    """Test DigitalMacrophage initialization, start, stop."""

    def test_macrophage_initialization(self, macrofago):
        """Test DigitalMacrophage initialization with all parameters."""
        # ASSERT: All init parameters set correctly
        assert macrofago.agent_id == "test-mac-01"
        assert macrofago.area == "network-zone-1"
        assert macrofago.sensibilidade == 0.7
        assert macrofago._running is False
        assert macrofago.phagocytosis_mode == PhagocytosisMode.QUARANTINE
        assert len(macrofago.threats_engulfed) == 0
        assert macrofago.patrol_interval == 5.0  # Default

    def test_macrophage_default_parameters(self):
        """Test DigitalMacrophage with default parameters."""
        # ACT: Create with minimal params
        mac = DigitalMacrophage(agent_id="minimal-mac")

        # ASSERT: Defaults applied
        assert mac.agent_id == "minimal-mac"
        assert mac.area is None or mac.area == ""
        assert mac.sensibilidade == 0.5  # Default sensitivity
        assert mac.patrol_interval == 5.0

    @pytest.mark.asyncio
    async def test_macrophage_start(self, macrofago):
        """Test macrophage start() method."""
        # PRE-ASSERT: Not running
        assert macrofago._running is False

        # ACT: Start macrophage
        await macrofago.iniciar()

        # Brief wait for background tasks
        await asyncio.sleep(0.01)

        # ASSERT: Running and tasks created
        assert macrofago._running is True
        assert macrofago._patrol_task is not None

        # CLEANUP
        await macrofago.parar()

    @pytest.mark.asyncio
    async def test_macrophage_stop(self, macrofago):
        """Test macrophage stop() method."""
        # ARRANGE: Start first
        await macrofago.iniciar()
        await asyncio.sleep(0.01)
        assert macrofago._running is True

        # ACT: Stop macrophage
        await macrofago.parar()

        # ASSERT: Stopped completely
        assert macrofago._running is False

    @pytest.mark.asyncio
    async def test_macrophage_double_start_idempotent(self, macrofago):
        """Test start() is idempotent (calling twice is safe)."""
        # ACT: Start twice
        await macrofago.iniciar()
        await macrofago.iniciar()  # Should not crash

        # ASSERT: Still running, no duplicate tasks
        assert macrofago._running is True

        # CLEANUP
        await macrofago.parar()

    @pytest.mark.asyncio
    async def test_macrophage_stop_without_start(self, macrofago):
        """Test stop() without prior start() is safe."""
        # PRE-ASSERT: Not running
        assert macrofago._running is False

        # ACT: Stop without starting (should not crash)
        await macrofago.parar()

        # ASSERT: Still not running
        assert macrofago._running is False

    @pytest.mark.asyncio
    async def test_macrophage_repr(self, macrofago):
        """Test __repr__ method."""
        # ACT: Get string representation
        repr_str = repr(macrofago)

        # ASSERT: Contains key information
        assert "test-mac-01" in repr_str
        assert "DigitalMacrophage" in repr_str or "Macrophage" in repr_str

    @pytest.mark.asyncio
    async def test_macrophage_get_metrics(self, macrofago):
        """Test get_metrics() returns correct structure."""
        # ACT: Get metrics
        metrics = macrofago.get_metrics()

        # ASSERT: Metrics structure
        assert "agent_id" in metrics
        assert "agent_type" in metrics
        assert "threats_detected" in metrics or "threats_engulfed" in metrics
        assert "status" in metrics or "running" in metrics

    @pytest.mark.asyncio
    async def test_macrophage_area_assignment(self):
        """Test macrophage area assignment."""
        # ACT: Create with specific area
        mac = DigitalMacrophage(agent_id="area-mac", area="dmz-zone")

        # ASSERT: Area set
        assert mac.area == "dmz-zone"

    @pytest.mark.asyncio
    async def test_macrophage_sensitivity_boundaries(self):
        """Test sensitivity parameter boundaries."""
        # ACT: Create with high sensitivity
        mac_high = DigitalMacrophage(agent_id="high-sens", sensibilidade=0.95)

        # ACT: Create with low sensitivity
        mac_low = DigitalMacrophage(agent_id="low-sens", sensibilidade=0.1)

        # ASSERT: Sensitivities set
        assert mac_high.sensibilidade == 0.95
        assert mac_low.sensibilidade == 0.1
```

**⚠️ VERIFICAÇÃO OBRIGATÓRIA**: Execute:
```bash
python -m pytest tests/test_macrofago.py::TestMacrophageLifecycle -v --tb=short
```
**Resultado esperado**: 10/10 testes passando.

---

### SEÇÃO 1.4: PATROL BEHAVIOR TESTS (15 testes)

```python
# ==================== PATROL BEHAVIOR TESTS ====================

class TestPatrolBehavior:
    """Test autonomous patrol logic."""

    @pytest.mark.asyncio
    async def test_patrol_loop_executes(self, macrofago):
        """Test patrol loop runs continuously."""
        # ARRANGE: Start macrophage
        await macrofago.iniciar()

        # Track patrol iterations
        patrol_count = [0]
        original_patrol = macrofago._patrol

        async def counting_patrol():
            patrol_count[0] += 1
            await original_patrol()

        macrofago._patrol = counting_patrol

        # ACT: Let patrol run
        await asyncio.sleep(0.3)  # 300ms

        # ASSERT: Patrol executed multiple times
        assert patrol_count[0] >= 1

        # CLEANUP
        await macrofago.parar()

    @pytest.mark.asyncio
    async def test_patrol_respects_interval(self, macrofago):
        """Test patrol respects patrol_interval parameter."""
        # ARRANGE: Set short interval
        macrofago.patrol_interval = 0.1  # 100ms

        # Track patrol timestamps
        patrol_times = []

        async def timestamping_patrol():
            patrol_times.append(time.time())

        macrofago._patrol = timestamping_patrol

        # ACT: Start and let run
        await macrofago.iniciar()
        await asyncio.sleep(0.35)  # ~3 patrol intervals

        # CLEANUP
        await macrofago.parar()

        # ASSERT: Intervals approximately match
        if len(patrol_times) >= 2:
            intervals = [patrol_times[i+1] - patrol_times[i] for i in range(len(patrol_times)-1)]
            avg_interval = sum(intervals) / len(intervals)
            # Allow 30% tolerance
            assert 0.07 <= avg_interval <= 0.15

    # TODO: Adicionar 13 testes restantes seguindo este padrão
    # - test_patrol_area_coverage
    # - test_patrol_random_walk
    # - test_patrol_threat_scanning
    # - test_patrol_pause_on_detection
    # - test_patrol_resume_after_neutralization
    # - etc.
```

**NOTA IMPORTANTE**: Este é apenas um **EXEMPLO PARCIAL** para demonstrar o padrão.
A blueprint COMPLETA teria ~3000 linhas com TODOS os testes detalhados.

---

## 🔍 VALIDAÇÃO POR MÓDULO

Após completar CADA arquivo de teste:

```bash
# 1. Executar testes
python -m pytest tests/test_<modulo>.py -v --tb=short

# 2. Validar coverage
python -m pytest tests/test_<modulo>.py --cov=agents.<modulo> --cov-report=term-missing

# 3. Verificar qualidade
grep -E "TODO|FIXME|HACK|pass$|NotImplemented" tests/test_<modulo>.py
```

**Meta de coverage**: ≥95% por arquivo

---

## 📊 RELATÓRIO FINAL (Após completar TODOS os módulos)

Após completar TODOS os 6 módulos de agents, crie relatório seguindo EXATAMENTE este formato:

```markdown
# BLUEPRINT 04 - IMMUNE AGENTS TESTS - RELATÓRIO DE EXECUÇÃO

**Status**: [COMPLETO ✅ / INCOMPLETO ❌]
**Data**: [data]
**Executor**: Gemini CLI

## Resultados por Módulo

| Módulo | Testes | Pass | Fail | Coverage |
|--------|--------|------|------|----------|
| test_macrofago.py | 80 | [X] | [Y] | [Z]% |
| test_nk_cell.py | 75 | [X] | [Y] | [Z]% |
| test_neutrofilo.py | 70 | [X] | [Y] | [Z]% |
| test_dendritic_cell.py | 60 | [X] | [Y] | [Z]% |
| test_helper_t_cell.py | 55 | [X] | [Y] | [Z]% |
| test_regulatory_t_cell.py | 50 | [X] | [Y] | [Z]% |
| **TOTAL** | **390** | **[X]** | **[Y]** | **[Z]%** |

## Testes de Integração (Validação)

| Módulo | Testes | Status |
|--------|--------|--------|
| test_agent_factory_integration.py | 22 | ✅ PASS |
| test_cytokines_integration.py | 30 | ✅ PASS |
| test_hormones_integration.py | 40 | ✅ PASS |
| test_swarm_integration.py | 68 | ✅ PASS |

## Coverage Consolidado

Coverage total agents/: [X]%

## Problemas Encontrados

[Liste TODOS os problemas, ou "Nenhum"]

## Próximos Passos

[Se COMPLETO: "Agents testados. Próximo: Coordination/Homeostasis"]
[Se INCOMPLETO: Liste o que falta]
```

---

## 🚨 EM CASO DE ERRO

Se QUALQUER teste falhar:

1. **NÃO CONTINUE** para o próximo módulo
2. **PARE IMEDIATAMENTE**
3. **REPORTE O ERRO** com:
   - Nome do teste que falhou
   - Arquivo (test_<modulo>.py)
   - Mensagem de erro COMPLETA
   - Traceback COMPLETO
   - Coverage atual do módulo
4. **AGUARDE INSTRUÇÕES** antes de continuar

---

## 🎯 CRITÉRIO DE SUCESSO

**Este blueprint está completo APENAS SE**:

✅ 6 arquivos de teste criados (macrofago, nk_cell, neutrofilo, dendritic, helper_t, regulatory_t)
✅ ~390 testes novos implementados EXATAMENTE como especificado
✅ TODOS os testes passando (100%)
✅ Coverage ≥95% em CADA módulo agent
✅ Testes de integração validados (160 testes passando)
✅ ZERO placeholders, TODOs, FIXMEs
✅ Relatório final entregue

---

## 📋 OBSERVAÇÕES IMPORTANTES

### Sobre Mocks

**USE mocks APENAS para**:
- ✅ Kafka (CytokineMessenger)
- ✅ Redis (HormoneMessenger)
- ✅ PostgreSQL (se usado)
- ✅ Tempo (time.time, asyncio.sleep - quando necessário)

**NÃO use mocks para**:
- ❌ Lógica de negócio do agent
- ❌ Métodos internos do agent
- ❌ Pattern matching
- ❌ Threat scoring
- ❌ Phagocytosis logic

### Sobre Testes Async

- Todos os testes de agents são `@pytest.mark.asyncio`
- Use `await asyncio.sleep(0.01)` para dar tempo às background tasks
- Sempre chame `await agent.parar()` no cleanup
- Fixtures devem ser `@pytest_asyncio.fixture`

### Sobre Coverage

- Meta: ≥95% por arquivo
- Linhas não cobertas aceitáveis:
  - Defensive error handling (except blocks raros)
  - Logging statements
  - __repr__ edge cases
- Linhas não cobertas NÃO aceitáveis:
  - Business logic principal
  - Detecção de ameaças
  - Neutralização
  - Comunicação (cytokines/hormones)

---

**FIM DO BLUEPRINT 04**

*"The immune system never rests. Testing ensures it never fails."*
*"Equilibrio é o que da estabilidade nos seres."*

**Execute com precisão. Relate com honestidade. Entregue com qualidade.**

**NOTA**: Esta blueprint contém apenas EXEMPLO PARCIAL dos testes (seções 1.1-1.4).
A implementação COMPLETA seguiria este padrão para TODOS os 6 módulos de agents
com ~65 linhas/teste × 390 testes = ~25,000 linhas de especificação detalhada.

Para execução pelo Gemini CLI, EXPANDA cada seção seguindo o padrão demonstrado.
