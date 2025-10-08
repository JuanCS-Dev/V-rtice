"""
Norepinephrine Modulator - Production-Hardened with Bounded Behavior

Biological Inspiration:
- Locus Coeruleus: Arousal, vigilance, stress response
- Amygdala: Threat detection, emotional intensity
- Bounded neurotransmitter levels [0, 1] with physiological constraints
- Receptor desensitization prevents overstimulation
- Reuptake mechanisms ensure temporal decay
- Homeostatic regulation maintains baseline

Functional Role in MAXIMUS:
- Arousal modulation (physiological + cognitive)
- Vigilance / alertness
- Stress response (adaptive activation)
- Urgency signaling (time pressure)

Safety Features: Inherited from NeuromodulatorBase
- HARD CLAMP to [0, 1]
- Desensitization above threshold
- Homeostatic exponential decay (FASTEST: 0.015/s)
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


class NorepinephrineModulator(NeuromodulatorBase):
    """
    Norepinephrine modulator with bounded, smooth, homeostatic behavior.

    Biological Characteristics:
    - LOWEST baseline (0.3) - norepinephrine is highly phasic (arousal bursts)
    - FASTEST decay (0.015/s) - rapid return to baseline after burst
    - Standard desensitization threshold (0.8)

    Usage identical to DopamineModulator:
        modulator = NorepinephrineModulator(kill_switch_callback=safety.kill_switch.trigger)
        actual_change = modulator.modulate(delta=0.5, source="threat_detected")
        level = modulator.level
        metrics = modulator.get_health_metrics()
    """

    def __init__(
        self, config: Optional[ModulatorConfig] = None, kill_switch_callback: Optional[Callable[[str], None]] = None
    ):
        """Initialize norepinephrine modulator with biological defaults.

        Args:
            config: Optional custom configuration. If None, uses norepinephrine defaults:
                - baseline=0.3 (lowest - highly phasic arousal bursts)
                - decay_rate=0.015 (fastest decay - rapid return to baseline)
            kill_switch_callback: Optional callback for emergency shutdown
        """
        if config is None:
            config = ModulatorConfig(
                baseline=0.3,  # NE: lowest baseline (highly phasic, burst-driven)
                decay_rate=0.015,  # NE: fastest decay (rapid return after arousal)
                desensitization_threshold=0.8,
                desensitization_factor=0.5,
                smoothing_factor=0.2,
                max_change_per_step=0.1,
            )

        super().__init__(config, kill_switch_callback)

    def get_modulator_name(self) -> str:
        """Return modulator name for logging/metrics."""
        return "norepinephrine"
