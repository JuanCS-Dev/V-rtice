"""
Metacognition Validator - Targeted Coverage Tests

Objetivo: Cobrir consciousness/validation/metacognition.py (99 lines, 0% → 80%+)

Testa MetacognitionMetrics, MetacognitionValidator.evaluate(), thresholds

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from unittest.mock import Mock

from consciousness.validation.metacognition import (
    MetacognitionMetrics,
    MetacognitionValidator,
)


# ===== METACOGNITION METRICS TESTS =====

def test_metacognition_metrics_initialization():
    """
    SCENARIO: Create MetacognitionMetrics dataclass
    EXPECTED: Initializes with 4 metrics + issues
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.85,
        narrative_coherence=0.90,
        meta_memory_alignment=0.75,
        introspection_quality=0.88,
        issues=["Test issue"],
    )

    assert metrics.self_alignment == 0.85
    assert metrics.narrative_coherence == 0.90
    assert metrics.meta_memory_alignment == 0.75
    assert metrics.introspection_quality == 0.88
    assert len(metrics.issues) == 1


def test_metacognition_metrics_passes_all_thresholds():
    """
    SCENARIO: All metrics meet minimum thresholds
    EXPECTED: passes property returns True
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.85,  # >= 0.8
        narrative_coherence=0.90,  # >= 0.85
        meta_memory_alignment=0.75,  # >= 0.7
        introspection_quality=0.85,  # >= 0.8
    )

    assert metrics.passes is True


def test_metacognition_metrics_fails_self_alignment():
    """
    SCENARIO: self_alignment below 0.8 threshold
    EXPECTED: passes returns False
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.75,  # < 0.8
        narrative_coherence=0.90,
        meta_memory_alignment=0.75,
        introspection_quality=0.85,
    )

    assert metrics.passes is False


def test_metacognition_metrics_fails_narrative_coherence():
    """
    SCENARIO: narrative_coherence below 0.85 threshold
    EXPECTED: passes returns False
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.85,
        narrative_coherence=0.80,  # < 0.85
        meta_memory_alignment=0.75,
        introspection_quality=0.85,
    )

    assert metrics.passes is False


def test_metacognition_metrics_fails_meta_memory_alignment():
    """
    SCENARIO: meta_memory_alignment below 0.7 threshold
    EXPECTED: passes returns False
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.85,
        narrative_coherence=0.90,
        meta_memory_alignment=0.65,  # < 0.7
        introspection_quality=0.85,
    )

    assert metrics.passes is False


def test_metacognition_metrics_fails_introspection_quality():
    """
    SCENARIO: introspection_quality below 0.8 threshold
    EXPECTED: passes returns False
    """
    metrics = MetacognitionMetrics(
        self_alignment=0.85,
        narrative_coherence=0.90,
        meta_memory_alignment=0.75,
        introspection_quality=0.75,  # < 0.8
    )

    assert metrics.passes is False


# ===== METACOGNITION VALIDATOR TESTS =====

def test_metacognition_validator_initialization():
    """
    SCENARIO: Create MetacognitionValidator instance
    EXPECTED: Initializes successfully
    """
    validator = MetacognitionValidator()

    assert validator is not None


def test_evaluate_with_complete_result():
    """
    SCENARIO: Evaluate result with all components present
    EXPECTED: Returns MetacognitionMetrics with valid scores
    """
    validator = MetacognitionValidator()

    # Mock complete RecursiveReasoningResult
    result = Mock()
    result.attention_state = Mock(focus_target="monitoring task")
    result.self_summary = Mock(
        focus_target="monitoring task",
        confidence=0.9,
        narrative="Eu estou monitorando o sistema com atenção total",
    )
    result.boundary_assessment = Mock(stability=0.85)
    result.episodic_coherence = 0.88
    result.meta_report = Mock(average_confidence=0.87)

    metrics = validator.evaluate(result)

    assert isinstance(metrics, MetacognitionMetrics)
    assert 0.0 <= metrics.self_alignment <= 1.0
    assert 0.0 <= metrics.narrative_coherence <= 1.0
    assert 0.0 <= metrics.meta_memory_alignment <= 1.0
    assert 0.0 <= metrics.introspection_quality <= 1.0


def test_evaluate_missing_attention_state():
    """
    SCENARIO: Evaluate result with missing attention_state
    EXPECTED: Adds issue, self_alignment = 0.0
    """
    validator = MetacognitionValidator()

    result = Mock()
    result.attention_state = None
    result.self_summary = Mock(
        focus_target="task",
        confidence=0.9,
        narrative="Test narrative",
    )
    result.boundary_assessment = None
    result.episodic_coherence = None
    result.meta_report = None

    metrics = validator.evaluate(result)

    assert "Attention state ausente" in metrics.issues
    assert metrics.self_alignment == 0.0


def test_evaluate_missing_self_summary():
    """
    SCENARIO: Evaluate result with missing self_summary
    EXPECTED: Adds multiple issues, low scores
    """
    validator = MetacognitionValidator()

    result = Mock()
    result.attention_state = Mock(focus_target="task")
    result.self_summary = None
    result.boundary_assessment = None
    result.episodic_coherence = None
    result.meta_report = None

    metrics = validator.evaluate(result)

    assert "Self-summary ausente" in metrics.issues
    assert "Sem narrativa para avaliar coerência" in metrics.issues
    assert metrics.self_alignment == 0.0
    assert metrics.narrative_coherence == 0.0


def test_token_overlap_identical_strings():
    """
    SCENARIO: Token overlap with identical strings
    EXPECTED: Returns 1.0 (100% overlap)
    """
    overlap = MetacognitionValidator._token_overlap(
        "monitoring task",
        "monitoring task",
    )

    assert overlap == 1.0


def test_token_overlap_no_overlap():
    """
    SCENARIO: Token overlap with completely different strings
    EXPECTED: Returns 0.0 (no overlap)
    """
    overlap = MetacognitionValidator._token_overlap(
        "monitoring task",
        "security analysis",
    )

    assert overlap == 0.0


def test_token_overlap_partial():
    """
    SCENARIO: Token overlap with partial match
    EXPECTED: Returns Jaccard index (intersection / union)
    """
    overlap = MetacognitionValidator._token_overlap(
        "monitoring system task",
        "system analysis task",
    )

    # Tokens A: {monitoring, system, task}
    # Tokens B: {system, analysis, task}
    # Intersection: {system, task} = 2
    # Union: {monitoring, system, task, analysis} = 4
    # Jaccard: 2 / 4 = 0.5
    assert overlap == 0.5


def test_token_overlap_empty_strings():
    """
    SCENARIO: Token overlap with empty string
    EXPECTED: Returns 0.0
    """
    overlap = MetacognitionValidator._token_overlap("", "monitoring task")

    assert overlap == 0.0


def test_narrative_coherence_formula():
    """
    SCENARIO: Evaluate narrative coherence with all components
    EXPECTED: Formula 0.5 * confidence + 0.3 * episodic + 0.2 * boundary
    """
    validator = MetacognitionValidator()

    result = Mock()
    result.attention_state = Mock(focus_target="task")
    result.self_summary = Mock(
        focus_target="task",
        confidence=0.9,
        narrative="Test narrative",
    )
    result.boundary_assessment = Mock(stability=0.8)
    result.episodic_coherence = 0.85
    result.meta_report = None

    metrics = validator.evaluate(result)

    # Expected: 0.5 * 0.9 + 0.3 * 0.85 + 0.2 * 0.8 = 0.45 + 0.255 + 0.16 = 0.865
    assert abs(metrics.narrative_coherence - 0.865) < 0.01


def test_introspection_quality_with_first_person():
    """
    SCENARIO: Narrative contains first-person cue "eu"
    EXPECTED: Higher introspection quality
    """
    validator = MetacognitionValidator()

    result = Mock()
    result.attention_state = Mock(focus_target="task")
    result.self_summary = Mock(
        focus_target="task",
        confidence=0.9,
        narrative="Eu estou processando informações com máxima atenção neste momento crucial para o sistema",
    )
    result.boundary_assessment = None
    result.episodic_coherence = None
    result.meta_report = None

    metrics = validator.evaluate(result)

    # Length quality: 89 chars / 120 ≈ 0.74
    # Perspective quality: 1.0 (has "eu")
    # Expected: 0.6 * 0.74 + 0.4 * 1.0 ≈ 0.844
    assert metrics.introspection_quality > 0.8


def test_introspection_quality_without_first_person():
    """
    SCENARIO: Narrative without first-person cue
    EXPECTED: Lower introspection quality (perspective_quality = 0.5)
    """
    validator = MetacognitionValidator()

    result = Mock()
    result.attention_state = Mock(focus_target="task")
    result.self_summary = Mock(
        focus_target="task",
        confidence=0.9,
        narrative="The system is processing information with maximum attention right now",
    )
    result.boundary_assessment = None
    result.episodic_coherence = None
    result.meta_report = None

    metrics = validator.evaluate(result)

    # Length quality: 75 chars / 120 ≈ 0.625
    # Perspective quality: 0.5 (no "eu")
    # Expected: 0.6 * 0.625 + 0.4 * 0.5 = 0.375 + 0.2 = 0.575
    assert abs(metrics.introspection_quality - 0.575) < 0.05


def test_all_exports():
    """
    SCENARIO: Check __all__ exports
    EXPECTED: Contains 2 exports
    """
    from consciousness.validation import metacognition

    assert len(metacognition.__all__) == 2
    assert "MetacognitionMetrics" in metacognition.__all__
    assert "MetacognitionValidator" in metacognition.__all__
