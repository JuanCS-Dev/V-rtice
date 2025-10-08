"""
Serotonin Modulator - Production-Hardened with Bounded Behavior

Biological Inspiration:
- Raphe Nuclei: Mood regulation, emotional stability
- Prefrontal Cortex: Impulse control, decision making
- Bounded neurotransmitter levels [0, 1] with physiological constraints
- Receptor desensitization prevents overstimulation
- Reuptake mechanisms ensure temporal decay
- Homeostatic regulation maintains baseline

Functional Role in MAXIMUS:
- Mood/affect regulation
- Impulse control (antagonist to dopamine)
- Emotional stability
- Long-term planning bias

Safety Features: Inherited from NeuromodulatorBase
- HARD CLAMP to [0, 1]
- Desensitization above threshold
- Homeostatic exponential decay (SLOWER than dopamine: 0.008/s)
- Temporal smoothing
- Max change per step limit
- Circuit breaker
- Kill switch integration
- Full observability

NO MOCK, NO PLACEHOLDER, NO TODO.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

from typing import Callable, Optional

from consciousness.neuromodulation.modulator_base import (
    ModulatorConfig,
    NeuromodulatorBase,
)


class SerotoninModulator(NeuromodulatorBase):
    """
    Serotonin modulator with bounded, smooth, homeostatic behavior.

    Biological Characteristics:
    - HIGHER baseline (0.6) - serotonin is generally more stable/elevated
    - SLOWER decay (0.008/s) - serotonin has longer-lasting effects
    - Standard desensitization threshold (0.8)

    Usage identical to DopamineModulator:
        modulator = SerotoninModulator(kill_switch_callback=safety.kill_switch.trigger)
        actual_change = modulator.modulate(delta=0.1, source="mood_regulation")
        level = modulator.level
        metrics = modulator.get_health_metrics()
    """

    def __init__(
        self, config: Optional[ModulatorConfig] = None, kill_switch_callback: Optional[Callable[[str], None]] = None
    ):
        """Initialize serotonin modulator with biological defaults.

        Args:
            config: Optional custom configuration. If None, uses serotonin defaults:
                - baseline=0.6 (higher than dopamine)
                - decay_rate=0.008 (slower than dopamine 0.01)
            kill_switch_callback: Optional callback for emergency shutdown
        """
        if config is None:
            config = ModulatorConfig(
                baseline=0.6,  # Serotonin: higher baseline (more stable)
                decay_rate=0.008,  # Serotonin: slower decay (longer-lasting)
                desensitization_threshold=0.8,
                desensitization_factor=0.5,
                smoothing_factor=0.2,
                max_change_per_step=0.1,
            )

        super().__init__(config, kill_switch_callback)

    def get_modulator_name(self) -> str:
        """Return modulator name for logging/metrics."""
        return "serotonin"
