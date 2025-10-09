"""
Test suite for MEA (Attention Schema Model + Self Model).

Coverage targets:
- Attention schema predictive loop
- Boundary detection stability
- Self-model report generation
- Prediction validation accuracy and calibration
"""

from __future__ import annotations

import math
import pytest

from .attention_schema import AttentionSchemaModel, AttentionSignal
from .boundary_detector import BoundaryDetector
from .prediction_validator import PredictionValidator
from .self_model import IntrospectiveSummary, SelfModel


# ==================== FIXTURES ====================


@pytest.fixture
def attention_model() -> AttentionSchemaModel:
    return AttentionSchemaModel()


@pytest.fixture
def boundary_detector() -> BoundaryDetector:
    return BoundaryDetector()


@pytest.fixture
def self_model() -> SelfModel:
    return SelfModel()


# ==================== ATTENTION SCHEMA TESTS ====================


class TestAttentionSchemaSignals:
    """Tests for AttentionSignal normalization and salience."""

    def test_normalized_score_range(self):
        signal = AttentionSignal(
            modality="visual",
            target="threat:alpha",
            intensity=0.8,
            novelty=0.5,
            relevance=0.7,
            urgency=0.6,
        )
        score = signal.normalized_score()
        assert 0.0 <= score <= 1.0
        assert math.isclose(score, 0.8 * (0.4 + 0.2 * 0.5 + 0.2 * 0.7 + 0.2 * 0.6))


class TestAttentionSchemaModel:
    """Tests for attention schema update and metrics."""

    def test_update_requires_signals(self, attention_model: AttentionSchemaModel):
        with pytest.raises(ValueError):
            attention_model.update([])

    def test_focus_selection(self, attention_model: AttentionSchemaModel):
        signals = [
            AttentionSignal("visual", "threat:alpha", 0.9, 0.6, 0.7, 0.5),
            AttentionSignal("auditory", "alert:beta", 0.4, 0.3, 0.4, 0.2),
            AttentionSignal("proprioceptive", "body_state", 0.5, 0.2, 0.3, 0.1),
        ]

        state = attention_model.update(signals)
        assert state.focus_target == "threat:alpha"
        assert state.confidence > 0.5
        assert math.isclose(sum(state.modality_weights.values()), 1.0, rel_tol=1e-6)

    def test_prediction_metrics(self, attention_model: AttentionSchemaModel):
        signals = [
            AttentionSignal("visual", f"target:{i}", 0.6 + 0.01 * i, 0.5, 0.5, 0.5)
            for i in range(5)
        ]
        state = attention_model.update(signals)
        attention_model.record_prediction_outcome(actual_focus=state.focus_target)
        assert attention_model.prediction_accuracy(window=10) == 1.0
        assert attention_model.prediction_calibration(window=10) <= 0.4
        assert attention_model.prediction_variability(window=10) >= 0.0

    def test_prediction_accuracy_threshold(self, attention_model: AttentionSchemaModel):
        # Simulate alternating outcomes to test >80% accuracy requirement
        correct_signals = AttentionSignal("visual", "focus", 0.9, 0.5, 0.6, 0.6)
        distractor_signals = AttentionSignal("auditory", "distractor", 0.2, 0.1, 0.1, 0.1)

        for i in range(30):
            signals = [correct_signals, distractor_signals]
            state = attention_model.update(signals)
            actual = "focus" if i % 5 != 0 else "distractor"
            attention_model.record_prediction_outcome(actual_focus=actual)

        accuracy = attention_model.prediction_accuracy(window=30)
        assert accuracy >= 0.8


# ==================== BOUNDARY DETECTOR TESTS ====================


class TestBoundaryDetector:
    """Tests for ego boundary detection stability."""

    def test_boundary_strength_mapping(self, boundary_detector: BoundaryDetector):
        proprio = [0.9] * 10
        extero = [0.2] * 10
        assessment = boundary_detector.evaluate(proprio, extero)
        assert 0.0 <= assessment.strength <= 1.0
        assert assessment.strength > 0.5  # proprio dominates

    def test_boundary_stability_target(self, boundary_detector: BoundaryDetector):
        for i in range(50):
            proprio = [0.6 + 0.01 * (-1) ** i] * 5
            extero = [0.4] * 5
            boundary_detector.evaluate(proprio, extero)

        assessment = boundary_detector.evaluate([0.6], [0.4])
        assert assessment.stability >= 0.85  # CV < 0.15 translates to stability >= 0.85

    def test_invalid_signals_raise(self, boundary_detector: BoundaryDetector):
        with pytest.raises(ValueError):
            boundary_detector.evaluate([], [0.5])
        with pytest.raises(ValueError):
            boundary_detector.evaluate([1.2], [0.5])


# ==================== SELF MODEL TESTS ====================


class TestSelfModel:
    """Tests for self-representation and narrative generation."""

    def test_self_model_requires_initialization(self, self_model: SelfModel):
        with pytest.raises(RuntimeError):
            self_model.current_focus()

    def test_update_and_report(
        self,
        self_model: SelfModel,
        attention_model: AttentionSchemaModel,
        boundary_detector: BoundaryDetector,
    ):
        signals = [
            AttentionSignal("visual", "threat:alpha", 0.8, 0.4, 0.5, 0.4),
            AttentionSignal("proprioceptive", "body_state", 0.5, 0.2, 0.6, 0.1),
        ]
        attention_state = attention_model.update(signals)
        boundary = boundary_detector.evaluate([0.6, 0.65, 0.62], [0.3, 0.28, 0.31])

        self_model.update(
            attention_state=attention_state,
            boundary=boundary,
            proprio_center=(0.0, 0.0, 1.0),
            orientation=(0.0, 0.1, 0.0),
        )

        report = self_model.generate_first_person_report()
        assert isinstance(report, IntrospectiveSummary)
        assert "focado em 'threat:alpha'" in report.narrative
        assert 0.0 <= report.confidence <= 1.0
        assert report.boundary_stability >= 0.0

    def test_identity_vector_updates(self, self_model: SelfModel, attention_model: AttentionSchemaModel):
        state = attention_model.update(
            [
                AttentionSignal("proprioceptive", "body", 0.7, 0.2, 0.4, 0.3),
                AttentionSignal("visual", "object", 0.5, 0.2, 0.5, 0.2),
                AttentionSignal("interoceptive", "heartbeat", 0.6, 0.1, 0.5, 0.1),
            ]
        )
        boundary = BoundaryDetector().evaluate([0.6], [0.4])
        self_model.update(state, boundary, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))
        identity = self_model.self_vector()
        assert math.isclose(sum(identity), sum(state.modality_weights.values()), rel_tol=1e-6)


# ==================== PREDICTION VALIDATOR TESTS ====================


class TestPredictionValidator:
    """Tests for prediction validation metrics."""

    def test_validator_input_validation(self):
        validator = PredictionValidator()
        with pytest.raises(ValueError):
            validator.validate([], [])
        with pytest.raises(ValueError):
            validator.validate([_dummy_state("foo", 0.8)], [])

    def test_validator_metrics(self, attention_model: AttentionSchemaModel):
        predictions = []
        observations = []
        for i in range(20):
            focus_target = f"target:{i % 2}"
            signals = [
                AttentionSignal("visual", focus_target, 0.8, 0.5, 0.6, 0.4),
                AttentionSignal("auditory", f"alt:{i}", 0.3, 0.2, 0.1, 0.1),
            ]
            state = attention_model.update(signals)
            predictions.append(state)
            observations.append(focus_target if i % 3 else "target:1")

        validator = PredictionValidator()
        metrics = validator.validate(predictions, observations)

        assert metrics.accuracy >= 0.8
        assert metrics.calibration_error <= 0.25
        assert 0.0 <= metrics.focus_switch_rate <= 1.0


# ==================== INTEGRATION TESTS ====================


class TestMEAIntegration:
    """High-level integration tests for MEA pipeline."""

    def test_attention_to_self_model_pipeline(
        self,
        attention_model: AttentionSchemaModel,
        boundary_detector: BoundaryDetector,
        self_model: SelfModel,
    ):
        # Simulate timeline with consistent observation updates
        observations = []
        for step in range(15):
            primary_target = "threat:active" if step % 4 else "maintenance"
            signals = [
                AttentionSignal("visual", primary_target, 0.7, 0.4, 0.6, 0.5),
                AttentionSignal("auditory", f"alert:{step}", 0.4, 0.3, 0.3, 0.2),
                AttentionSignal("proprioceptive", "body_state", 0.5, 0.2, 0.5, 0.1),
            ]
            state = attention_model.update(signals)
            boundary = boundary_detector.evaluate([0.6, 0.62, 0.61], [0.3, 0.29, 0.31])
            self_model.update(
                attention_state=state,
                boundary=boundary,
                proprio_center=(0.0, 0.0, 1.0),
                orientation=(0.01 * step, 0.02 * step, 0.0),
            )
            observations.append(primary_target)
            attention_model.record_prediction_outcome(actual_focus=primary_target)

        accuracy = attention_model.prediction_accuracy(window=15)
        assert accuracy >= 0.8

        report = self_model.generate_first_person_report()
        assert isinstance(report, IntrospectiveSummary)
        assert report.boundary_stability >= 0.85
        assert report.confidence >= 0.5


# ==================== HELPERS ====================


def _dummy_state(target: str, confidence: float):
    """Utility for validation tests."""
    model = AttentionSchemaModel()
    state = model.update(
        [
            AttentionSignal("visual", target, 0.8, 0.4, 0.5, 0.3),
            AttentionSignal("auditory", "secondary", 0.2, 0.1, 0.2, 0.1),
        ]
    )
    state.confidence = confidence  # type: ignore[attr-defined]
    return state
