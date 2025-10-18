"""
Boundary Detector
=================

Implements computational ego-boundary detection inspired by phenomenological
accounts of self-other distinction.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Deque, Iterable
from collections import deque


@dataclass
class BoundaryAssessment:
    """
    Assessment of the ego/world boundary.

    Attributes:
        strength: Relative strength of boundary (0 weak / 1 strong)
        stability: Coefficient of variation for boundary over recent samples
        proprioception_mean: Average proprioceptive intensity
        exteroception_mean: Average exteroceptive intensity
    """

    strength: float
    stability: float
    proprioception_mean: float
    exteroception_mean: float


class BoundaryDetector:
    """
    Detects self-other boundary using proprioceptive vs exteroceptive signals.
    """

    WINDOW: int = 100

    def __init__(self) -> None:
        self._strength_history: Deque[float] = deque(maxlen=self.WINDOW)
        self._proprio_history: Deque[float] = deque(maxlen=self.WINDOW)
        self._extero_history: Deque[float] = deque(maxlen=self.WINDOW)

    def evaluate(
        self,
        proprioceptive_signals: Iterable[float],
        exteroceptive_signals: Iterable[float],
    ) -> BoundaryAssessment:
        proprio_mean = self._validate_and_mean(proprioceptive_signals)
        extero_mean = self._validate_and_mean(exteroceptive_signals)

        ratio = self._compute_ratio(proprio_mean, extero_mean)
        strength = self._ratio_to_strength(ratio)

        self._strength_history.append(strength)
        self._proprio_history.append(proprio_mean)
        self._extero_history.append(extero_mean)

        stability = self._compute_stability()

        return BoundaryAssessment(
            strength=strength,
            stability=stability,
            proprioception_mean=proprio_mean,
            exteroception_mean=extero_mean,
        )

    # ----- Helper methods -------------------------------------------------

    def _validate_and_mean(self, values: Iterable[float]) -> float:
        values_list = list(values)
        if not values_list:
            raise ValueError("Signal sequence cannot be empty")

        for value in values_list:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Signal value {value} out of range [0,1]")

        return sum(values_list) / len(values_list)

    def _compute_ratio(self, proprio: float, extero: float) -> float:
        epsilon = 1e-6
        return proprio / (extero + epsilon)

    def _ratio_to_strength(self, ratio: float) -> float:
        """
        Map ratio to boundary strength.
        Strong boundary: proprio dominates (ratio > 1)
        Weak boundary: extero dominates (ratio < 1)
        """
        normalized = ratio / (1.0 + ratio)
        return max(0.0, min(1.0, normalized))

    def _compute_stability(self) -> float:
        if len(self._strength_history) < 5:
            return 1.0  # assume stable until enough samples

        mean_strength = sum(self._strength_history) / len(self._strength_history)
        if mean_strength == 0:
            return 0.0

        variability = pstdev(self._strength_history)
        cv = variability / mean_strength

        return max(0.0, min(1.0, 1.0 - cv))

