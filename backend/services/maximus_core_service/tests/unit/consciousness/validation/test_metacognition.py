"""Tests for MetacognitionValidator."""

from __future__ import annotations

from datetime import datetime

from consciousness.lrr.recursive_reasoner import (
    Belief,
    BeliefType,
    ReasoningLevel,
    ReasoningStep,
    RecursiveReasoningResult,
)
from consciousness.lrr.meta_monitor import CalibrationMetrics, MetaMonitoringReport
from consciousness.mea import AttentionState, BoundaryAssessment, FirstPersonPerspective, IntrospectiveSummary
from consciousness.validation.metacognition import MetacognitionValidator


def _build_result() -> RecursiveReasoningResult:
    belief = Belief(content="Threat detected", belief_type=BeliefType.FACTUAL, confidence=0.9)
    level = ReasoningLevel(level=0, beliefs=[belief], coherence=0.9, steps=[ReasoningStep(belief=belief, meta_level=0, justification_chain=[], confidence_assessment=0.85)])
    result = RecursiveReasoningResult(levels=[level], final_depth=1, coherence_score=0.9)

    attention_state = AttentionState(
        focus_target="threat:alpha",
        modality_weights={"visual": 0.6, "interoceptive": 0.2, "proprioceptive": 0.2},
        confidence=0.88,
        salience_order=[("threat:alpha", 0.82)],
        baseline_intensity=0.55,
    )
    boundary = BoundaryAssessment(
        strength=0.7,
        stability=0.9,
        proprioception_mean=0.6,
        exteroception_mean=0.4,
    )
    summary = IntrospectiveSummary(
        narrative="Eu mantenho atenção na ameaça alpha com equilíbrio corporal e relato conscientemente cada nuance percebida.",
        confidence=0.85,
        boundary_stability=0.9,
        focus_target="threat:alpha",
        perspective=FirstPersonPerspective(viewpoint=(0.0, 0.0, 1.0), orientation=(0.1, 0.0, 0.0), timestamp=datetime.utcnow()),
    )

    result.attention_state = attention_state
    result.boundary_assessment = boundary
    result.self_summary = summary
    result.episodic_episode = None
    result.episodic_narrative = "Linha temporal estável"
    result.episodic_coherence = 0.88
    result.meta_report = MetaMonitoringReport(
        total_levels=1,
        average_coherence=0.9,
        average_confidence=0.86,
        processing_time_ms=12.0,
        calibration=CalibrationMetrics(brier_score=0.05, expected_calibration_error=0.08, correlation=0.75),
        biases_detected=[],
        recommendations=[],
    )

    return result


def test_metacognition_validator_passes_with_aligned_data():
    validator = MetacognitionValidator()
    result = _build_result()
    metrics = validator.evaluate(result)

    assert metrics.passes
    assert metrics.self_alignment >= 0.8
    assert metrics.narrative_coherence >= 0.85
    assert metrics.meta_memory_alignment >= 0.7
    assert metrics.introspection_quality >= 0.8


def test_metacognition_validator_flags_misalignment():
    validator = MetacognitionValidator()
    result = _build_result()
    result.attention_state = AttentionState(
        focus_target="maintenance",
        modality_weights={"proprioceptive": 0.7, "visual": 0.3},
        confidence=0.4,
        salience_order=[("maintenance", 0.4)],
        baseline_intensity=0.5,
    )
    result.meta_report = MetaMonitoringReport(
        total_levels=1,
        average_coherence=0.6,
        average_confidence=0.4,
        processing_time_ms=15.0,
        calibration=CalibrationMetrics(brier_score=0.2, expected_calibration_error=0.3, correlation=0.4),
        biases_detected=[],
        recommendations=[],
    )
    metrics = validator.evaluate(result)

    assert not metrics.passes
    assert metrics.self_alignment < 0.8
    assert metrics.meta_memory_alignment < 0.7
