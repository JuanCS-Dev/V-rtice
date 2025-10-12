# Plano de Correção: Imports e Validação Reactive Fabric
**Data**: 2025-10-12  
**Sprint**: 1 - Backend Core Implementation  
**Status**: ACTIVE

## OBJETIVO
Corrigir todos os imports quebrados no módulo Reactive Fabric seguindo a Doutrina Vértice com qualidade production-ready.

---

## ANÁLISE DE DEPENDÊNCIAS

### Estrutura Atual
```
backend/security/reactive_fabric/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── types.py           # ThreatLevel, ResponseAction, etc
│   ├── orchestrator.py    # ReactiveFabricOrchestrator
│   └── telemetry.py       # TelemetryCollector
├── deception/
│   ├── __init__.py
│   ├── honeypot_manager.py
│   └── sacrifice_island.py
├── intelligence/
│   ├── __init__.py
│   ├── threat_correlator.py
│   └── ttp_extractor.py
└── response/
    ├── __init__.py
    └── action_executor.py
```

### Dependências Identificadas

**orchestrator.py precisa:**
- `ThreatLevel` de `core.types`
- `ResponseAction` de `core.types`
- `TelemetryCollector` de `core.telemetry`
- `HoneypotManager` de `deception.honeypot_manager`
- `TTPExtractor` de `intelligence.ttp_extractor`
- `ActionExecutor` de `response.action_executor`

**action_executor.py precisa:**
- `ResponseAction` de `core.types`
- `ThreatLevel` de `core.types`

**threat_correlator.py precisa:**
- `ThreatLevel` de `core.types`

**ttp_extractor.py precisa:**
- `ThreatLevel` de `core.types`

**honeypot_manager.py precisa:**
- Tipos base (sem dependências internas identificadas)

---

## FASE 1: CORREÇÃO DE IMPORTS (30 min)

### 1.1 Definir Exports em __init__.py (5 min)
```python
# backend/security/reactive_fabric/__init__.py
from .core.types import ThreatLevel, ResponseAction, ThreatIntelligence
from .core.orchestrator import ReactiveFabricOrchestrator
from .core.telemetry import TelemetryCollector
from .deception.honeypot_manager import HoneypotManager
from .deception.sacrifice_island import SacrificeIsland
from .intelligence.threat_correlator import ThreatCorrelator
from .intelligence.ttp_extractor import TTPExtractor
from .response.action_executor import ActionExecutor

__all__ = [
    "ThreatLevel",
    "ResponseAction",
    "ThreatIntelligence",
    "ReactiveFabricOrchestrator",
    "TelemetryCollector",
    "HoneypotManager",
    "SacrificeIsland",
    "ThreatCorrelator",
    "TTPExtractor",
    "ActionExecutor",
]
```

### 1.2 Corrigir orchestrator.py (10 min)
**Ação**: Trocar imports absolutos por relativos
```python
# De:
from backend.security.reactive_fabric.core.types import ...
# Para:
from .types import ThreatLevel, ResponseAction
from .telemetry import TelemetryCollector
from ..deception.honeypot_manager import HoneypotManager
from ..intelligence.ttp_extractor import TTPExtractor
from ..response.action_executor import ActionExecutor
```

### 1.3 Corrigir action_executor.py (5 min)
```python
from ..core.types import ResponseAction, ThreatLevel
```

### 1.4 Corrigir threat_correlator.py (5 min)
```python
from ..core.types import ThreatLevel, ThreatIntelligence
```

### 1.5 Corrigir ttp_extractor.py (5 min)
```python
from ..core.types import ThreatLevel, ThreatIntelligence
```

---

## FASE 2: VALIDAÇÃO SINTÁTICA (15 min)

### 2.1 Python Import Check
```bash
cd /home/juan/vertice-dev
python -c "from backend.security.reactive_fabric import ReactiveFabricOrchestrator"
```

### 2.2 MyPy Type Check
```bash
mypy backend/security/reactive_fabric/ --strict --no-error-summary 2>&1 | head -50
```

### 2.3 Pylint
```bash
pylint backend/security/reactive_fabric/*.py backend/security/reactive_fabric/*/*.py --max-line-length=100
```

---

## FASE 3: VALIDAÇÃO FUNCIONAL (20 min)

### 3.1 Teste de Instantiação
Criar `backend/security/reactive_fabric/tests/test_imports.py`:
```python
"""Validação de imports e instantiação - Reactive Fabric."""
import pytest
from backend.security.reactive_fabric import (
    ReactiveFabricOrchestrator,
    ThreatLevel,
    ResponseAction,
)


def test_import_orchestrator():
    """Valida que ReactiveFabricOrchestrator pode ser importado."""
    assert ReactiveFabricOrchestrator is not None


def test_import_enums():
    """Valida que enums podem ser importados."""
    assert ThreatLevel.LOW is not None
    assert ResponseAction.LOG is not None


def test_orchestrator_instantiation():
    """Valida que orquestrador pode ser instanciado."""
    orchestrator = ReactiveFabricOrchestrator()
    assert orchestrator is not None
    assert orchestrator.threat_level == ThreatLevel.LOW
```

### 3.2 Executar Testes
```bash
pytest backend/security/reactive_fabric/tests/test_imports.py -v
```

---

## FASE 4: DOCUMENTAÇÃO DE VALIDAÇÃO (15 min)

### 4.1 Criar Relatório
`docs/reports/validations/reactive-fabric-imports-validation-2025-10-12.md`

### 4.2 Atualizar Session Log
Adicionar entry em `docs/sessions/2025-10/reactive-fabric-sprint1.md`

---

## CRITÉRIOS DE SUCESSO

### ✅ Validação Sintática
- [ ] Python import sem erros
- [ ] MyPy passa em todos os arquivos (strict mode)
- [ ] Pylint score ≥ 9.0

### ✅ Validação Funcional
- [ ] Teste de import passa
- [ ] Teste de instantiação passa
- [ ] Teste de enums passa

### ✅ Conformidade Doutrina
- [ ] Sem mocks ou placeholders
- [ ] Type hints completos
- [ ] Docstrings no formato Google
- [ ] Error handling adequado

---

## EXECUÇÃO

### Comando de Execução Única (Fast Track)
```bash
# Fase 1: Correção automática de imports (manual via editor)
# Fase 2+3: Validação completa
cd /home/juan/vertice-dev && \
python -c "from backend.security.reactive_fabric import ReactiveFabricOrchestrator; print('✅ Import OK')" && \
mypy backend/security/reactive_fabric/ --strict --no-error-summary 2>&1 | head -20 && \
pytest backend/security/reactive_fabric/tests/test_imports.py -v
```

---

## RISCOS E MITIGAÇÕES

### Risco 1: Circular Imports
**Probabilidade**: Baixa  
**Mitigação**: Estrutura já usa types.py como módulo base sem dependências

### Risco 2: Missing Dependencies
**Probabilidade**: Média  
**Mitigação**: Validar requirements.txt antes de executar

### Risco 3: Type Checker Failures
**Probabilidade**: Alta (strict mode)  
**Mitigação**: Corrigir incrementalmente, priorizar erros de import

---

## TIMELINE

**Total estimado**: 80 minutos

- Fase 1: 30 min
- Fase 2: 15 min
- Fase 3: 20 min
- Fase 4: 15 min

**Meta**: Deploy-ready ao final da sessão

---

**Status**: PRONTO PARA EXECUÇÃO  
**Aprovação necessária**: ✅ (implícita pelo comando "go")
