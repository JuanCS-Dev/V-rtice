"""
Prediction Validator
====================

Evaluates accuracy and calibration of attention predictions relative to observed
attentional focus values, providing metrics for adaptive learning.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .attention_schema import AttentionState


@dataclass
class ValidationMetrics:
    """
    Summary of validation results for attention predictions.

    Attributes:
        accuracy: Proportion of correct predictions
        calibration_error: Expected calibration error (ECE)
        mean_confidence: Average confidence across predictions
        focus_switch_rate: Rate of focus changes between predictions
    """

    accuracy: float
    calibration_error: float
    mean_confidence: float
    focus_switch_rate: float


class PredictionValidator:
    """Validates attention predictions against observed attention states."""

    def validate(
        self,
        predictions: Sequence[AttentionState],
        observations: Sequence[str],
    ) -> ValidationMetrics:
        if not predictions:
            raise ValueError("No predictions provided for validation")
        if len(predictions) != len(observations):
            raise ValueError("Predictions and observations must have matching length")

        accuracy = self._compute_accuracy(predictions, observations)
        calibration_error = self._compute_ece(predictions, observations)
        mean_confidence = float(sum(state.confidence for state in predictions) / len(predictions))
        switch_rate = self._compute_focus_switch_rate(predictions)

        return ValidationMetrics(
            accuracy=accuracy,
            calibration_error=calibration_error,
            mean_confidence=mean_confidence,
            focus_switch_rate=switch_rate,
        )

    def _compute_accuracy(
        self,
        predictions: Sequence[AttentionState],
        observations: Sequence[str],
    ) -> float:
        matches = sum(
            1 for prediction, actual in zip(predictions, observations) if prediction.focus_target == actual
        )
        return matches / len(predictions)

    def _compute_ece(
        self,
        predictions: Sequence[AttentionState],
        observations: Sequence[str],
    ) -> float:
        bucket_totals = [0] * 10
        bucket_errors = [0.0] * 10

        for prediction, actual in zip(predictions, observations):
            bucket = min(9, int(prediction.confidence * 10))
            bucket_totals[bucket] += 1
            bucket_errors[bucket] += abs(
                prediction.confidence - (1.0 if prediction.focus_target == actual else 0.0)
            )

        errors = [
            (bucket_errors[i] / bucket_totals[i]) if bucket_totals[i] else 0.0
            for i in range(10)
        ]
        return sum(errors) / len(errors)

    def _compute_focus_switch_rate(self, predictions: Sequence[AttentionState]) -> float:
        if len(predictions) < 2:
            return 0.0

        switches = sum(
            1
            for prev, curr in zip(predictions, predictions[1:])
            if prev.focus_target != curr.focus_target
        )
        return switches / (len(predictions) - 1)

