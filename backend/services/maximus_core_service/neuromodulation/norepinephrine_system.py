"""Norepinephrine System - Arousal, attention, and stress response.

Biological inspiration:
- Locus coeruleus: Norepinephrine source
- Fight-or-flight response: Acute stress activation
- Attention and vigilance enhancement
- Inverted-U performance: Optimal arousal level

Production-ready implementation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NorepinephrineState:
    """Current norepinephrine state."""
    level: float  # Current NE level (0.0-1.0)
    arousal: float  # Arousal/alertness (0.0-1.0)
    attention_gain: float  # Attention multiplier (0.5-2.0)
    stress_response: bool  # Whether in acute stress mode
    timestamp: datetime


class NorepinephrineSystem:
    """Norepinephrine for arousal and stress response.

    Implements:
    - Yerkes-Dodson inverted-U: Optimal arousal level
    - Attention gain modulation
    - Acute stress detection and response
    - Performance optimization under pressure
    """

    def __init__(
        self,
        baseline_level: float = 0.4,
        optimal_arousal: float = 0.5,
        stress_threshold: float = 0.7
    ):
        """Initialize norepinephrine system.

        Args:
            baseline_level: Baseline NE level (0.0-1.0)
            optimal_arousal: Optimal arousal for performance (0.0-1.0)
            stress_threshold: Threshold for stress response
        """
        self.baseline_level = baseline_level
        self.optimal_arousal = optimal_arousal
        self.stress_threshold = stress_threshold

        # State
        self.level = baseline_level
        self.acute_stressors = []

        logger.info(f"Norepinephrine system initialized (baseline={baseline_level})")

    def respond_to_threat(self, threat_severity: float):
        """Activate fight-or-flight response.

        Biological: Acute threat → norepinephrine surge

        Args:
            threat_severity: Severity of threat (0.0-1.0)
        """
        # NE surge proportional to threat
        ne_surge = threat_severity * 0.5
        self.level = min(1.0, self.level + ne_surge)

        # Track stressor
        self.acute_stressors.append(threat_severity)
        if len(self.acute_stressors) > 10:
            self.acute_stressors.pop(0)

        logger.warning(f"Threat detected! NE surge: {ne_surge:.2f}, level now: {self.level:.3f}")

    def get_arousal_level(self) -> float:
        """Get current arousal level.

        Returns:
            Arousal level (0.0-1.0)
        """
        return self.level

    def get_attention_gain(self) -> float:
        """Calculate attention gain based on Yerkes-Dodson law.

        Biological: Optimal arousal → max performance
                   Too low → sluggish, too high → anxious/impaired

        Returns:
            Attention gain multiplier (0.5-2.0)
        """
        # Inverted-U curve: performance peaks at optimal arousal
        deviation = abs(self.level - self.optimal_arousal)

        # Max gain at optimal, degrades with distance
        gain = 2.0 - (deviation * 2.0)  # Linear degradation
        gain = max(0.5, min(2.0, gain))

        logger.debug(f"Attention gain: {gain:.2f} (arousal={self.level:.3f}, optimal={self.optimal_arousal})")

        return gain

    def is_stressed(self) -> bool:
        """Check if system is in acute stress mode.

        Returns:
            True if in stress response
        """
        return self.level > self.stress_threshold

    def update(self, workload: float = 0.0):
        """Update NE level based on workload.

        Args:
            workload: Current workload (0.0-1.0)
        """
        # Workload drives arousal
        target_level = self.baseline_level + (workload * 0.3)

        # Drift towards target (with inertia)
        self.level = 0.9 * self.level + 0.1 * target_level

        # Clamp to valid range
        self.level = max(0.0, min(1.0, self.level))

        # Clear old stressors (habituation)
        if len(self.acute_stressors) > 5:
            self.acute_stressors = self.acute_stressors[-5:]

        logger.debug(f"NE updated: workload={workload:.2f}, level={self.level:.3f}")

    def get_state(self) -> NorepinephrineState:
        """Get current norepinephrine state.

        Returns:
            Current NE state
        """
        return NorepinephrineState(
            level=self.level,
            arousal=self.get_arousal_level(),
            attention_gain=self.get_attention_gain(),
            stress_response=self.is_stressed(),
            timestamp=datetime.utcnow()
        )

    def reset(self):
        """Reset to baseline."""
        self.level = self.baseline_level
        self.acute_stressors.clear()

        logger.info("Norepinephrine system reset to baseline")
