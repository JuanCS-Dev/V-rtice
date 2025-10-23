"""
MMEI Module - Targeted Coverage Tests

Objetivo: Cobrir consciousness/mmei/__init__.py (82 lines, 0% → 90%+)

Testa exports, interoception computational, embodied consciousness

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest


def test_mmei_module_imports():
    import consciousness.mmei
    assert consciousness.mmei is not None


def test_docstring():
    import consciousness.mmei
    assert "Monitoramento de Estado Interno" in consciousness.mmei.__doc__
    assert "interoception" in consciousness.mmei.__doc__
    assert "embodiment" in consciousness.mmei.__doc__


def test_docstring_theoretical_foundation():
    import consciousness.mmei
    doc = consciousness.mmei.__doc__

    assert "proprioception" in doc or "interoception" in doc
    assert "homeostasis" in doc or "allostasis" in doc
    assert "phenomenal" in doc


def test_docstring_biological_analogy():
    import consciousness.mmei
    doc = consciousness.mmei.__doc__

    assert "Insula" in doc or "insula" in doc
    assert "cingulate" in doc
    assert "Hipotálamo" in doc


def test_docstring_computational_translation():
    import consciousness.mmei
    doc = consciousness.mmei.__doc__

    # Physical → Abstract translation
    assert "CPU" in doc or "Memory" in doc
    assert "Rest need" in doc or "Repair need" in doc
    assert "Curiosity" in doc


# Monitor exports
def test_exports_internal_state_monitor():
    from consciousness.mmei import InternalStateMonitor
    assert InternalStateMonitor is not None


def test_exports_physical_metrics():
    from consciousness.mmei import PhysicalMetrics
    assert PhysicalMetrics is not None


def test_exports_abstract_needs():
    from consciousness.mmei import AbstractNeeds
    assert AbstractNeeds is not None


def test_exports_need_urgency():
    from consciousness.mmei import NeedUrgency
    assert NeedUrgency is not None


# Goals exports
def test_exports_autonomous_goal_generator():
    from consciousness.mmei import AutonomousGoalGenerator
    assert AutonomousGoalGenerator is not None


def test_exports_goal():
    from consciousness.mmei import Goal
    assert Goal is not None


def test_exports_goal_type():
    from consciousness.mmei import GoalType
    assert GoalType is not None


def test_exports_goal_priority():
    from consciousness.mmei import GoalPriority
    assert GoalPriority is not None


def test_all_exports():
    from consciousness.mmei import __all__
    assert len(__all__) == 8


def test_all_exports_importable():
    import consciousness.mmei
    for name in consciousness.mmei.__all__:
        assert hasattr(consciousness.mmei, name)


def test_docstring_consciousness_claim():
    """
    SCENARIO: Module makes embodied consciousness claim
    EXPECTED: Mentions consciousness requires body/embodiment
    """
    import consciousness.mmei
    doc = consciousness.mmei.__doc__

    assert "conscious" in doc.lower()
    assert "embodied" in doc.lower() or "corpo" in doc.lower()
    assert "To be conscious is to feel" in doc
