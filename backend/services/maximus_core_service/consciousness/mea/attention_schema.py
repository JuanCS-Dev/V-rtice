"""
Attention Schema Model
======================

Implements a predictive model of attention inspired by Graziano's
Attention Schema Theory (AST) and predictive processing frameworks.

Responsibilities
----------------
- Integrate multimodal attention signals (visual, auditory, proprioceptive, etc.)
- Produce a normalized attention state vector (focus, intensity, confidence)
- Maintain rolling history for prediction error estimation
- Provide salience ranking for downstream consciousness modules (ESGT, LRR)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Deque, Dict, Iterable, List, Sequence

# ==================== DATA STRUCTURES ====================


@dataclass(frozen=True)
class AttentionSignal:
    """
    Represents a single sensory or cognitive signal competing for attention.

    Attributes:
        modality: Source modality (e.g. "visual", "auditory", "proprioceptive")
        target: Target entity or identifier (e.g. "threat:192.168.1.1")
        intensity: Raw signal intensity [0, 1]
        novelty: Novelty factor compared to recent history [0, 1]
        relevance: Task relevance weight [0, 1]
        urgency: Urgency weight (time-critical) [0, 1]
    """

    modality: str
    target: str
    intensity: float
    novelty: float
    relevance: float
    urgency: float

    def normalized_score(self) -> float:
        """
        Compute a normalized salience score.

        Formula chosen to maintain interpretability:
            salience = intensity * (0.4 + 0.2*novelty + 0.2*relevance + 0.2*urgency)
        """
        base = 0.4 + 0.2 * self.novelty + 0.2 * self.relevance + 0.2 * self.urgency
        return max(0.0, min(1.0, self.intensity * base))


@dataclass
class AttentionState:
    """
    Output of the attention schema model.

    Attributes:
        focus_target: Identifier of the entity receiving maximal attention
        modality_weights: Normalized distribution over modalities
        confidence: Confidence in the current focus attribution [0, 1]
        salience_order: Ranked list of (target, score)
        baseline_intensity: Rolling average of intensities (homeostatic reference)
    """

    focus_target: str
    modality_weights: Dict[str, float]
    confidence: float
    salience_order: List[tuple[str, float]]
    baseline_intensity: float


@dataclass
class PredictionTrace:
    """Stores historical prediction vs observation pairs for calibration."""

    predicted_focus: str
    actual_focus: str
    prediction_confidence: float
    match: bool


# ==================== MODEL ====================


class AttentionSchemaModel:
    """
    Attention schema responsible for generating attention states and
    prediction errors for MAXIMUS consciousness.
    """

    HISTORY_WINDOW: int = 200

    def __init__(self) -> None:
        self._intensity_history: Deque[float] = deque(maxlen=self.HISTORY_WINDOW)
        self._prediction_traces: Deque[PredictionTrace] = deque(maxlen=self.HISTORY_WINDOW)
        self._last_state: AttentionState | None = None

    # ----- Public API -----------------------------------------------------

    def update(self, signals: Sequence[AttentionSignal]) -> AttentionState:
        """
        Ingest attention signals and compute an updated attention state.

        Args:
            signals: Sequence of attention signals collected during current cycle.

        Returns:
            AttentionState describing the predicted focus and modality distribution.
        """
        if not signals:
            raise ValueError("At least one attention signal is required")

        salience_map = {signal.target: signal.normalized_score() for signal in signals}
        modality_scores = self._aggregate_by_modality(signals)
        focus_target, focus_score = self._select_focus(salience_map)

        baseline = self._update_intensity_baseline(signals)
        confidence = self._calculate_confidence(focus_score, salience_map.values())
        salience_order = sorted(salience_map.items(), key=lambda item: item[1], reverse=True)

        modality_distribution = self._normalize_modality_scores(modality_scores)

        state = AttentionState(
            focus_target=focus_target,
            modality_weights=modality_distribution,
            confidence=confidence,
            salience_order=salience_order,
            baseline_intensity=baseline,
        )

        self._last_state = state
        return state

    def record_prediction_outcome(self, actual_focus: str) -> None:
        """
        Record the outcome of the latest attention prediction for calibration.
        """
        if self._last_state is None:
            raise RuntimeError("No attention state available for calibration")

        trace = PredictionTrace(
            predicted_focus=self._last_state.focus_target,
            actual_focus=actual_focus,
            prediction_confidence=self._last_state.confidence,
            match=self._last_state.focus_target == actual_focus,
        )
        self._prediction_traces.append(trace)

    def prediction_accuracy(self, window: int = 50) -> float:
        """
        Calculate rolling prediction accuracy over the specified window.
        """
        recent = list(self._prediction_traces)[-window:]
        if not recent:
            return 0.0
        matches = sum(1 for trace in recent if trace.match)
        return matches / len(recent)

    def prediction_calibration(self, window: int = 50) -> float:
        """
        Compute Expected Calibration Error (ECE) for prediction confidence.
        """
        recent = list(self._prediction_traces)[-window:]
        if not recent:
            return 0.0

        bucket_totals = [0] * 10
        bucket_errors = [0.0] * 10

        for trace in recent:
            bucket = min(9, int(trace.prediction_confidence * 10))
            bucket_totals[bucket] += 1
            bucket_errors[bucket] += abs(
                trace.prediction_confidence - (1.0 if trace.match else 0.0)
            )

        errors = [
            (bucket_errors[i] / bucket_totals[i]) if bucket_totals[i] else 0.0
            for i in range(10)
        ]
        return float(fmean(errors))

    def prediction_variability(self, window: int = 50) -> float:
        """
        Return standard deviation of focus confidence for stability monitoring.
        """
        recent = list(self._prediction_traces)[-window:]
        if len(recent) < 2:
            return 0.0
        confidences = [trace.prediction_confidence for trace in recent]
        return float(pstdev(confidences))

    # ----- Internal helpers -----------------------------------------------

    def _aggregate_by_modality(
        self, signals: Sequence[AttentionSignal]
    ) -> Dict[str, float]:
        modality_scores: Dict[str, List[float]] = {}
        for signal in signals:
            modality_scores.setdefault(signal.modality, []).append(signal.normalized_score())

        return {modality: float(fmean(scores)) for modality, scores in modality_scores.items()}

    def _normalize_modality_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        total = sum(scores.values())
        if total == 0:
            equal_weight = 1.0 / len(scores)
            return {modality: equal_weight for modality in scores}

        return {modality: value / total for modality, value in scores.items()}

    def _select_focus(self, salience_map: Dict[str, float]) -> tuple[str, float]:
        focus_target = max(salience_map, key=salience_map.get)
        return focus_target, salience_map[focus_target]

    def _update_intensity_baseline(self, signals: Sequence[AttentionSignal]) -> float:
        avg_intensity = fmean(signal.intensity for signal in signals)
        self._intensity_history.append(avg_intensity)
        return fmean(self._intensity_history)

    def _calculate_confidence(
        self, focus_score: float, all_scores: Iterable[float]
    ) -> float:
        sorted_scores = sorted(all_scores, reverse=True)
        if len(sorted_scores) == 1:
            return 1.0

        second_best = sorted_scores[1]
        margin = focus_score - second_best
        normalized_margin = max(0.0, min(1.0, margin))
        return 0.6 * focus_score + 0.4 * normalized_margin

