"""Acetylcholine System - Attention gating and memory encoding.

Biological inspiration:
- Basal forebrain: ACh production
- Attention and focus: Highlights salient stimuli
- Memory encoding: High ACh during learning
- Circadian rhythm: Higher during wakefulness

Production-ready implementation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AcetylcholineState:
    """Current acetylcholine state."""

    level: float  # Current ACh level (0.0-1.0)
    attention_filter: float  # Salience threshold (0.0-1.0)
    memory_encoding_rate: float  # Memory consolidation rate (0.0-1.0)
    focus_narrow: bool  # Whether in narrow-focus mode
    timestamp: datetime


class AcetylcholineSystem:
    """Acetylcholine for attention and memory.

    Implements:
    - Salience-based attention filtering
    - Memory encoding rate modulation
    - Focus narrowing during high-importance tasks
    - Circadian-like rhythms
    """

    def __init__(
        self,
        baseline_level: float = 0.5,
        min_salience_threshold: float = 0.3,
        max_salience_threshold: float = 0.9,
    ):
        """Initialize acetylcholine system.

        Args:
            baseline_level: Baseline ACh level (0.0-1.0)
            min_salience_threshold: Min salience to pass attention filter
            max_salience_threshold: Max salience threshold
        """
        self.baseline_level = baseline_level
        self.min_salience_threshold = min_salience_threshold
        self.max_salience_threshold = max_salience_threshold

        # State
        self.level = baseline_level
        self.focus_mode = False

        logger.info(f"Acetylcholine system initialized (baseline={baseline_level})")

    def modulate_attention(self, importance: float):
        """Modulate ACh level based on task importance.

        Biological: Important tasks → ACh surge → heightened attention

        Args:
            importance: Task importance (0.0-1.0)
        """
        # High importance → ACh increase
        target_level = self.baseline_level + (importance * 0.4)
        target_level = max(0.0, min(1.0, target_level))

        # Gradual change (not instant)
        self.level = 0.8 * self.level + 0.2 * target_level

        # Enter focus mode if very important
        self.focus_mode = importance > 0.8

        logger.debug(f"ACh modulated: importance={importance:.2f}, level={self.level:.3f}, focus={self.focus_mode}")

    def get_salience_threshold(self) -> float:
        """Get current salience threshold for attention filtering.

        Biological: High ACh → lower threshold (more sensitive to stimuli)
                   Low ACh → higher threshold (more filtering)

        Returns:
            Salience threshold (0.0-1.0)
        """
        # Inverted: high ACh → low threshold (let more through)
        threshold = self.max_salience_threshold - (
            self.level * (self.max_salience_threshold - self.min_salience_threshold)
        )

        logger.debug(f"Salience threshold: {threshold:.3f} (ACh={self.level:.3f})")

        return threshold

    def get_memory_encoding_rate(self) -> float:
        """Get memory encoding rate.

        Biological: High ACh → enhanced memory encoding (hippocampus)

        Returns:
            Memory encoding rate (0.0-1.0)
        """
        # Direct relationship: high ACh → high encoding
        encoding_rate = self.level

        return encoding_rate

    def should_attend(self, salience: float) -> bool:
        """Determine if stimulus should receive attention.

        Args:
            salience: Stimulus salience (0.0-1.0)

        Returns:
            True if above threshold (should attend)
        """
        threshold = self.get_salience_threshold()

        should_attend = salience >= threshold

        if should_attend:
            logger.debug(f"Attention triggered: salience={salience:.2f} >= threshold={threshold:.2f}")

        return should_attend

    def update(self, workload: float = 0.0):
        """Update ACh based on workload.

        Args:
            workload: Current cognitive workload (0.0-1.0)
        """
        # High workload → ACh increase (need more attention)
        target_level = self.baseline_level + (workload * 0.3)

        # Drift towards target
        self.level = 0.9 * self.level + 0.1 * target_level

        # Clamp
        self.level = max(0.0, min(1.0, self.level))

        logger.debug(f"ACh updated: workload={workload:.2f}, level={self.level:.3f}")

    def get_state(self) -> AcetylcholineState:
        """Get current acetylcholine state.

        Returns:
            Current ACh state
        """
        return AcetylcholineState(
            level=self.level,
            attention_filter=self.get_salience_threshold(),
            memory_encoding_rate=self.get_memory_encoding_rate(),
            focus_narrow=self.focus_mode,
            timestamp=datetime.utcnow(),
        )

    def reset(self):
        """Reset to baseline."""
        self.level = self.baseline_level
        self.focus_mode = False

        logger.info("Acetylcholine system reset to baseline")
