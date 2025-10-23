"""
Prediction Validator - Targeted Coverage Tests

Objetivo: Cobrir consciousness/mea/prediction_validator.py (101 lines, 0% → 75%+)

Testa ValidationMetrics, PredictionValidator.validate(), accuracy, ECE, switch rate

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from unittest.mock import Mock

from consciousness.mea.prediction_validator import ValidationMetrics, PredictionValidator


# ===== VALIDATION METRICS TESTS =====

def test_validation_metrics_initialization():
    metrics = ValidationMetrics(
        accuracy=0.85,
        calibration_error=0.12,
        mean_confidence=0.78,
        focus_switch_rate=0.25,
    )

    assert metrics.accuracy == 0.85
    assert metrics.calibration_error == 0.12
    assert metrics.mean_confidence == 0.78
    assert metrics.focus_switch_rate == 0.25


# ===== PREDICTION VALIDATOR TESTS =====

def test_prediction_validator_initialization():
    validator = PredictionValidator()
    assert validator is not None


def test_validate_empty_predictions_raises():
    validator = PredictionValidator()

    with pytest.raises(ValueError, match="No predictions"):
        validator.validate([], [])


def test_validate_length_mismatch_raises():
    validator = PredictionValidator()

    prediction = Mock(focus_target="task1", confidence=0.8)

    with pytest.raises(ValueError, match="matching length"):
        validator.validate([prediction], ["task1", "task2"])


def test_validate_perfect_predictions():
    validator = PredictionValidator()

    predictions = [
        Mock(focus_target="task1", confidence=0.9),
        Mock(focus_target="task2", confidence=0.85),
    ]
    observations = ["task1", "task2"]

    metrics = validator.validate(predictions, observations)

    assert metrics.accuracy == 1.0
    assert metrics.mean_confidence == 0.875


def test_validate_partial_accuracy():
    validator = PredictionValidator()

    predictions = [
        Mock(focus_target="task1", confidence=0.8),
        Mock(focus_target="task2", confidence=0.7),
        Mock(focus_target="task3", confidence=0.6),
        Mock(focus_target="task4", confidence=0.5),
    ]
    observations = ["task1", "task2", "wrong", "wrong"]

    metrics = validator.validate(predictions, observations)

    assert metrics.accuracy == 0.5  # 2/4
    assert 0.0 <= metrics.calibration_error <= 1.0


def test_compute_accuracy():
    validator = PredictionValidator()

    predictions = [
        Mock(focus_target="A", confidence=0.8),
        Mock(focus_target="B", confidence=0.7),
        Mock(focus_target="C", confidence=0.6),
    ]
    observations = ["A", "X", "C"]

    accuracy = validator._compute_accuracy(predictions, observations)

    assert abs(accuracy - 0.6666) < 0.01  # 2/3


def test_focus_switch_rate_no_switches():
    validator = PredictionValidator()

    predictions = [
        Mock(focus_target="task1", confidence=0.8),
        Mock(focus_target="task1", confidence=0.8),
        Mock(focus_target="task1", confidence=0.8),
    ]

    switch_rate = validator._compute_focus_switch_rate(predictions)

    assert switch_rate == 0.0


def test_focus_switch_rate_all_switches():
    validator = PredictionValidator()

    predictions = [
        Mock(focus_target="A", confidence=0.8),
        Mock(focus_target="B", confidence=0.8),
        Mock(focus_target="C", confidence=0.8),
    ]

    switch_rate = validator._compute_focus_switch_rate(predictions)

    assert switch_rate == 1.0  # 2 switches / 2 transitions


def test_focus_switch_rate_single_prediction():
    validator = PredictionValidator()

    predictions = [Mock(focus_target="A", confidence=0.8)]

    switch_rate = validator._compute_focus_switch_rate(predictions)

    assert switch_rate == 0.0


def test_validate_returns_metrics():
    validator = PredictionValidator()

    predictions = [Mock(focus_target="task", confidence=0.8)]
    observations = ["task"]

    metrics = validator.validate(predictions, observations)

    assert isinstance(metrics, ValidationMetrics)
    assert 0.0 <= metrics.accuracy <= 1.0
    assert 0.0 <= metrics.calibration_error <= 1.0
    assert 0.0 <= metrics.mean_confidence <= 1.0
    assert 0.0 <= metrics.focus_switch_rate <= 1.0
