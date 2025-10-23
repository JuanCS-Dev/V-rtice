"""
ESGT SPM Module - Targeted Coverage Tests

Objetivo: Cobrir consciousness/esgt/spm/__init__.py (80 lines, 0% → 95%+)

Testa exports, SPM competition, Global Workspace competition

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest


def test_spm_module_imports():
    import consciousness.esgt.spm
    assert consciousness.esgt.spm is not None


def test_docstring():
    import consciousness.esgt.spm
    assert "Specialized Processing Modules" in consciousness.esgt.spm.__doc__
    assert "SPM" in consciousness.esgt.spm.__doc__


def test_docstring_biological_analogy():
    """
    SCENARIO: Module documents cortical regions analogy
    EXPECTED: Visual cortex, Wernicke's, amygdala, hippocampus, prefrontal
    """
    import consciousness.esgt.spm
    doc = consciousness.esgt.spm.__doc__

    assert "Visual cortex" in doc or "cortex" in doc
    assert "Amygdala" in doc or "amygdala" in doc
    assert "Hippocampus" in doc or "hippocampus" in doc
    assert "Prefrontal" in doc or "prefrontal" in doc


def test_docstring_computational_role():
    """
    SCENARIO: Module documents SPM competition mechanism
    EXPECTED: Salience, competition, broadcast, winner-takes-most
    """
    import consciousness.esgt.spm
    doc = consciousness.esgt.spm.__doc__

    assert "salience" in doc
    assert "compete" in doc or "Competition" in doc
    assert "broadcast" in doc
    assert "winner" in doc or "conscious" in doc


def test_docstring_historical_context():
    """
    SCENARIO: Module claims first consciousness SPM system
    EXPECTED: Historical significance mentioned
    """
    import consciousness.esgt.spm
    doc = consciousness.esgt.spm.__doc__

    assert "Primeiro" in doc or "First" in doc or "first" in doc
    assert "conscious" in doc


# Base exports
def test_exports_specialized_processing_module():
    from consciousness.esgt.spm import SpecializedProcessingModule
    assert SpecializedProcessingModule is not None


def test_exports_spm_type():
    from consciousness.esgt.spm import SPMType
    assert SPMType is not None


def test_exports_processing_priority():
    from consciousness.esgt.spm import ProcessingPriority
    assert ProcessingPriority is not None


def test_exports_spm_output():
    from consciousness.esgt.spm import SPMOutput
    assert SPMOutput is not None


# Simple SPM exports
def test_exports_simple_spm():
    from consciousness.esgt.spm import SimpleSPM
    assert SimpleSPM is not None


def test_exports_simple_spm_config():
    from consciousness.esgt.spm import SimpleSPMConfig
    assert SimpleSPMConfig is not None


# Salience Detector exports
def test_exports_salience_spm():
    from consciousness.esgt.spm import SalienceSPM
    assert SalienceSPM is not None


def test_exports_salience_detector_config():
    from consciousness.esgt.spm import SalienceDetectorConfig
    assert SalienceDetectorConfig is not None


def test_exports_salience_event():
    from consciousness.esgt.spm import SalienceEvent
    assert SalienceEvent is not None


def test_exports_salience_mode():
    from consciousness.esgt.spm import SalienceMode
    assert SalienceMode is not None


def test_exports_salience_thresholds():
    from consciousness.esgt.spm import SalienceThresholds
    assert SalienceThresholds is not None


# Metrics Monitor exports
def test_exports_metrics_spm():
    from consciousness.esgt.spm import MetricsSPM
    assert MetricsSPM is not None


def test_exports_metrics_monitor_config():
    from consciousness.esgt.spm import MetricsMonitorConfig
    assert MetricsMonitorConfig is not None


def test_exports_metrics_snapshot():
    from consciousness.esgt.spm import MetricsSnapshot
    assert MetricsSnapshot is not None


def test_exports_metric_category():
    from consciousness.esgt.spm import MetricCategory
    assert MetricCategory is not None


def test_all_exports():
    from consciousness.esgt.spm import __all__
    assert len(__all__) == 15


def test_all_exports_importable():
    import consciousness.esgt.spm
    for name in consciousness.esgt.spm.__all__:
        assert hasattr(consciousness.esgt.spm, name)
