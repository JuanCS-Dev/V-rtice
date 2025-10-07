"""Serotonin System - Mood, patience, and exploration-exploitation balance.

Biological inspiration:
- Raphe nuclei: Serotonin production
- Mood regulation: High serotonin → patience, low → impatience/aggression
- Risk tolerance: Modulates exploration vs exploitation tradeoff
- Time horizon: Patience for long-term rewards

Production-ready implementation.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SerotoninState:
    """Current serotonin system state."""

    level: float  # Current serotonin level (0.0-1.0)
    risk_tolerance: float  # Willingness to explore (0.0-1.0)
    patience: float  # Discount factor for future rewards (0.0-1.0)
    exploration_rate: float  # Epsilon for epsilon-greedy (0.0-1.0)
    timestamp: datetime


class SerotoninSystem:
    """Serotonin system for exploration-exploitation balance.

    Implements:
    - Mood-based risk tolerance modulation
    - Patience (temporal discount factor)
    - Exploration rate (epsilon) modulation
    - Stress response (serotonin depletion)
    """

    def __init__(
        self,
        baseline_level: float = 0.6,
        min_exploration: float = 0.05,
        max_exploration: float = 0.3,
        baseline_patience: float = 0.95,
    ):
        """Initialize serotonin system.

        Args:
            baseline_level: Baseline serotonin (0.0-1.0)
            min_exploration: Minimum exploration rate
            max_exploration: Maximum exploration rate
            baseline_patience: Baseline discount factor
        """
        self.baseline_level = baseline_level
        self.min_exploration = min_exploration
        self.max_exploration = max_exploration
        self.baseline_patience = baseline_patience

        # State
        self.level = baseline_level
        self.consecutive_failures = 0

        logger.info(f"Serotonin system initialized (baseline={baseline_level})")

    def update_from_outcome(self, success: bool, stress: float = 0.0):
        """Update serotonin based on task outcome.

        Biological: Success → serotonin increase, Failure → decrease
                   Chronic stress → serotonin depletion

        Args:
            success: Whether task succeeded
            stress: Current stress level (0.0-1.0)
        """
        if success:
            # Success boosts serotonin
            self.level = min(1.0, self.level + 0.05)
            self.consecutive_failures = 0
        else:
            # Failure depletes serotonin
            self.level = max(0.0, self.level - 0.03)
            self.consecutive_failures += 1

        # Stress depletes serotonin (chronic stress)
        stress_depletion = stress * 0.02
        self.level = max(0.0, self.level - stress_depletion)

        # Homeostatic drift back to baseline
        self.level = 0.95 * self.level + 0.05 * self.baseline_level

        logger.debug(
            f"Serotonin updated: success={success}, stress={stress:.2f}, "
            f"level={self.level:.3f}, failures={self.consecutive_failures}"
        )

    def get_exploration_rate(self) -> float:
        """Calculate exploration rate (epsilon) based on serotonin.

        Biological: Low serotonin → risk-seeking (explore more)
                   High serotonin → risk-averse (exploit more)

        Returns:
            Exploration rate (epsilon for epsilon-greedy)
        """
        # Inverted relationship: low serotonin → high exploration
        exploration = self.max_exploration - (
            self.level * (self.max_exploration - self.min_exploration)
        )

        # Increase exploration after consecutive failures (exploration bonus)
        failure_bonus = min(0.2, self.consecutive_failures * 0.02)
        exploration = min(1.0, exploration + failure_bonus)

        logger.debug(
            f"Exploration rate: {exploration:.3f} (serotonin={self.level:.3f})"
        )

        return exploration

    def get_risk_tolerance(self) -> float:
        """Get risk tolerance based on serotonin.

        Returns:
            Risk tolerance (0.0 = risk-averse, 1.0 = risk-seeking)
        """
        # Low serotonin → high risk tolerance (desperate/aggressive)
        risk_tolerance = 1.0 - self.level

        return risk_tolerance

    def get_patience(self) -> float:
        """Get temporal discount factor based on serotonin.

        Biological: High serotonin → patient (value future rewards)
                   Low serotonin → impatient (only value immediate rewards)

        Returns:
            Discount factor gamma (0.0-1.0)
        """
        # High serotonin → high discount factor (patient)
        # Low serotonin → low discount factor (impatient)
        patience = self.baseline_patience * self.level

        logger.debug(f"Patience (gamma): {patience:.3f}")

        return patience

    def get_state(self) -> SerotoninState:
        """Get current serotonin state.

        Returns:
            Current serotonin state
        """
        return SerotoninState(
            level=self.level,
            risk_tolerance=self.get_risk_tolerance(),
            patience=self.get_patience(),
            exploration_rate=self.get_exploration_rate(),
            timestamp=datetime.utcnow(),
        )

    def reset(self):
        """Reset serotonin to baseline."""
        self.level = self.baseline_level
        self.consecutive_failures = 0

        logger.info("Serotonin system reset to baseline")
