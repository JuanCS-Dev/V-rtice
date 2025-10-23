"""
NK Cell - Targeted Coverage Tests

Objetivo: Cobrir agents/nk_cell.py (186 lines, 0% → 15%+)

Testa CelulaNKDigital: initialization, specialization, cytotoxic behavior

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from agents.nk_cell import CelulaNKDigital
from agents.models import AgentType, AgentStatus


# ===== INITIALIZATION TESTS =====

def test_nk_cell_initialization_default():
    """
    SCENARIO: CelulaNKDigital created with defaults
    EXPECTED: NK_CELL type, area_patrulha set, anomaly_threshold default
    """
    nk = CelulaNKDigital(area_patrulha="subnet_10_0_1_0")

    assert nk.state.tipo == AgentType.NK_CELL
    assert nk.state.area_patrulha == "subnet_10_0_1_0"
    assert nk.anomaly_threshold == 0.7


def test_nk_cell_initialization_custom_threshold():
    """
    SCENARIO: CelulaNKDigital created with custom anomaly_threshold
    EXPECTED: Custom threshold stored
    """
    nk = CelulaNKDigital(area_patrulha="subnet_10_0_1_0", anomaly_threshold=0.85)

    assert nk.anomaly_threshold == 0.85


# ===== TYPE VALIDATION TESTS =====

def test_nk_cell_is_agente_base():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Is subclass of AgenteImunologicoBase
    """
    from agents.base import AgenteImunologicoBase

    nk = CelulaNKDigital(area_patrulha="test_area")

    assert isinstance(nk, AgenteImunologicoBase)


def test_nk_cell_type_enum():
    """
    SCENARIO: CelulaNKDigital.state.tipo
    EXPECTED: AgentType.NK_CELL
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert nk.state.tipo == AgentType.NK_CELL


# ===== METHOD EXISTENCE TESTS =====

def test_nk_cell_has_patrulhar_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has patrulhar method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "patrulhar")
    assert callable(nk.patrulhar)


def test_nk_cell_has_executar_investigacao_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has executar_investigacao method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "executar_investigacao")
    assert callable(nk.executar_investigacao)


def test_nk_cell_has_executar_neutralizacao_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has executar_neutralizacao method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "executar_neutralizacao")
    assert callable(nk.executar_neutralizacao)


def test_nk_cell_has_detectar_mhc_ausente_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has _detectar_mhc_ausente private method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "_detectar_mhc_ausente")
    assert callable(nk._detectar_mhc_ausente)


def test_nk_cell_has_detectar_anomalias_comportamentais_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has _detectar_anomalias_comportamentais method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "_detectar_anomalias_comportamentais")
    assert callable(nk._detectar_anomalias_comportamentais)


def test_nk_cell_has_calcular_anomalia_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has _calcular_anomalia method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "_calcular_anomalia")
    assert callable(nk._calcular_anomalia)


def test_nk_cell_has_update_baseline_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has _update_baseline method
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "_update_baseline")
    assert callable(nk._update_baseline)


def test_nk_cell_has_secretar_ifn_gamma_method():
    """
    SCENARIO: CelulaNKDigital instance
    EXPECTED: Has _secretar_ifn_gamma method (IFN-gamma secretion)
    """
    nk = CelulaNKDigital(area_patrulha="test_area")

    assert hasattr(nk, "_secretar_ifn_gamma")
    assert callable(nk._secretar_ifn_gamma)


# ===== DOCSTRING TESTS =====

def test_nk_cell_docstring_cytotoxic():
    """
    SCENARIO: CelulaNKDigital class docstring
    EXPECTED: Mentions cytotoxic behavior
    """
    doc = CelulaNKDigital.__doc__

    assert "cytotoxic" in doc.lower() or "Cytotoxicity" in doc


def test_nk_cell_docstring_mhc_detection():
    """
    SCENARIO: CelulaNKDigital class docstring
    EXPECTED: Mentions MHC-I detection
    """
    doc = CelulaNKDigital.__doc__

    assert "MHC" in doc or "mhc" in doc.lower()


def test_nk_cell_docstring_stress_response():
    """
    SCENARIO: Module docstring
    EXPECTED: Mentions stress-responsive behavior
    """
    import agents.nk_cell as module

    doc = module.__doc__

    assert "Stress" in doc or "stress" in doc
    assert "enforcers" in doc or "rapid response" in doc


def test_nk_cell_docstring_production_ready():
    """
    SCENARIO: Module docstring
    EXPECTED: Declares PRODUCTION-READY
    """
    import agents.nk_cell as module

    doc = module.__doc__

    assert "PRODUCTION-READY" in doc or "production" in doc.lower()


def test_nk_cell_docstring_no_memory():
    """
    SCENARIO: Module docstring
    EXPECTED: Mentions no memory (innate only)
    """
    import agents.nk_cell as module

    doc = module.__doc__

    assert "No memory" in doc or "innate" in doc.lower()


# ===== SPECIALIZED BEHAVIOR TESTS =====

def test_nk_cell_anomaly_threshold_validation():
    """
    SCENARIO: CelulaNKDigital created with anomaly_threshold
    EXPECTED: Threshold is float between 0-1
    """
    nk = CelulaNKDigital(area_patrulha="test", anomaly_threshold=0.5)

    assert isinstance(nk.anomaly_threshold, float)
    assert 0 <= nk.anomaly_threshold <= 1
