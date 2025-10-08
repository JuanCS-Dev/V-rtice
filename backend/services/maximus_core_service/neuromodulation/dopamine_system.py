"""Dopamine System - Reward prediction and learning rate modulation.

Biological inspiration:
- VTA (Ventral Tegmental Area): Reward prediction errors
- Substantia Nigra: Motor learning and action selection
- Tonic dopamine: Baseline motivation
- Phasic dopamine: Reward prediction errors (TD errors)

Production-ready implementation with real algorithms.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DopamineState:
    """Current state of dopamine system."""

    tonic_level: float  # Baseline (0.0-1.0)
    phasic_burst: float  # Current burst (-1.0 to +1.0, TD error)
    learning_rate: float  # Modulated learning rate
    motivation_level: float  # Overall motivation (0.0-1.0)
    timestamp: datetime


class DopamineSystem:
    """Dopamine-based reward system for learning rate modulation.

    Implements:
    - Reward prediction errors (RPE / TD errors)
    - Learning rate modulation based on surprise
    - Motivation levels based on recent rewards
    - Tonic/phasic dopamine dynamics
    """

    def __init__(
        self,
        baseline_tonic: float = 0.5,
        learning_rate_min: float = 0.001,
        learning_rate_max: float = 0.1,
        motivation_decay: float = 0.95,
    ):
        """Initialize dopamine system.

        Args:
            baseline_tonic: Baseline dopamine level (0.0-1.0)
            learning_rate_min: Minimum learning rate
            learning_rate_max: Maximum learning rate
            motivation_decay: Decay factor for motivation (0.0-1.0)
        """
        self.baseline_tonic = baseline_tonic
        self.learning_rate_min = learning_rate_min
        self.learning_rate_max = learning_rate_max
        self.motivation_decay = motivation_decay

        # State
        self.tonic_level = baseline_tonic
        self.phasic_burst = 0.0
        self.motivation_level = 0.5
        self.recent_rpes: list = []  # Recent reward prediction errors

        logger.info(f"Dopamine system initialized (baseline_tonic={baseline_tonic})")

    def compute_reward_prediction_error(self, expected_reward: float, actual_reward: float) -> float:
        """Compute reward prediction error (RPE / TD error).

        Biological: Positive RPE → dopamine burst, Negative RPE → dopamine dip

        Args:
            expected_reward: Expected reward value
            actual_reward: Actual reward received

        Returns:
            RPE value (-inf to +inf, typically -1.0 to +1.0)
        """
        rpe = actual_reward - expected_reward

        # Store recent RPEs (for motivation calculation)
        self.recent_rpes.append(rpe)
        if len(self.recent_rpes) > 100:
            self.recent_rpes.pop(0)

        # Update phasic burst
        self.phasic_burst = max(-1.0, min(1.0, rpe))

        logger.debug(f"RPE computed: expected={expected_reward:.3f}, actual={actual_reward:.3f}, rpe={rpe:.3f}")

        return rpe

    def modulate_learning_rate(self, base_learning_rate: float, rpe: float) -> float:
        """Modulate learning rate based on RPE magnitude.

        Biological: Larger prediction errors → higher learning rates (surprise)

        Args:
            base_learning_rate: Base learning rate
            rpe: Reward prediction error

        Returns:
            Modulated learning rate
        """
        # Surprise = abs(RPE)
        surprise = abs(rpe)

        # Modulation factor (0.0 to 1.0)
        # High surprise → high modulation → high learning rate
        modulation = min(1.0, surprise)

        # Calculate modulated learning rate
        modulated_lr = base_learning_rate + (self.learning_rate_max - base_learning_rate) * modulation
        modulated_lr = max(self.learning_rate_min, min(self.learning_rate_max, modulated_lr))

        logger.debug(
            f"Learning rate modulated: base={base_learning_rate:.6f}, "
            f"surprise={surprise:.3f}, modulated={modulated_lr:.6f}"
        )

        return modulated_lr

    def update_motivation(self) -> float:
        """Update motivation level based on recent rewards.

        Biological: Consistent rewards → high motivation
                   Consistent punishments → low motivation (learned helplessness)

        Returns:
            Updated motivation level (0.0-1.0)
        """
        if not self.recent_rpes:
            return self.motivation_level

        # Calculate average recent RPE
        avg_rpe = sum(self.recent_rpes[-20:]) / min(20, len(self.recent_rpes))

        # Positive RPEs increase motivation, negative decrease
        delta_motivation = avg_rpe * 0.1  # Scaling factor

        # Update with decay
        self.motivation_level = self.motivation_level * self.motivation_decay + delta_motivation
        self.motivation_level = max(0.0, min(1.0, self.motivation_level))

        logger.debug(f"Motivation updated: avg_rpe={avg_rpe:.3f}, motivation={self.motivation_level:.3f}")

        return self.motivation_level

    def update_tonic_level(self, stress_level: float = 0.0) -> float:
        """Update tonic dopamine based on stress.

        Biological: Chronic stress depletes tonic dopamine

        Args:
            stress_level: Current stress level (0.0-1.0)

        Returns:
            Updated tonic level
        """
        # Stress depletes tonic dopamine
        target_tonic = self.baseline_tonic * (1.0 - stress_level * 0.5)

        # Slow drift towards target (homeostatic regulation)
        self.tonic_level = 0.95 * self.tonic_level + 0.05 * target_tonic

        logger.debug(f"Tonic dopamine updated: stress={stress_level:.3f}, tonic={self.tonic_level:.3f}")

        return self.tonic_level

    def get_state(self) -> DopamineState:
        """Get current dopamine system state.

        Returns:
            Current dopamine state
        """
        # Calculate current learning rate
        learning_rate = self.learning_rate_min + (self.learning_rate_max - self.learning_rate_min) * abs(
            self.phasic_burst
        )

        return DopamineState(
            tonic_level=self.tonic_level,
            phasic_burst=self.phasic_burst,
            learning_rate=learning_rate,
            motivation_level=self.motivation_level,
            timestamp=datetime.utcnow(),
        )

    def reset(self):
        """Reset dopamine system to baseline."""
        self.tonic_level = self.baseline_tonic
        self.phasic_burst = 0.0
        self.motivation_level = 0.5
        self.recent_rpes.clear()

        logger.info("Dopamine system reset to baseline")
