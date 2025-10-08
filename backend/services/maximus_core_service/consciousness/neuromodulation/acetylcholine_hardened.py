"""
Acetylcholine Modulator - Production-Hardened with Bounded Behavior

Biological Inspiration:
- Nucleus Basalis: Attention, learning rate modulation
- Hippocampus: Memory encoding, consolidation
- Bounded neurotransmitter levels [0, 1] with physiological constraints
- Receptor desensitization prevents overstimulation
- Reuptake mechanisms ensure temporal decay
- Homeostatic regulation maintains baseline

Functional Role in MAXIMUS:
- Attention allocation (salience gating)
- Learning rate modulation (synaptic plasticity)
- Memory encoding strength
- Surprise-driven exploration

Safety Features: Inherited from NeuromodulatorBase
- HARD CLAMP to [0, 1]
- Desensitization above threshold
- Homeostatic exponential decay (MODERATE: 0.012/s)
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

from typing import Optional, Callable
from consciousness.neuromodulation.modulator_base import (
    NeuromodulatorBase,
    ModulatorConfig,
)


class AcetylcholineModulator(NeuromodulatorBase):
    """
    Acetylcholine modulator with bounded, smooth, homeostatic behavior.

    Biological Characteristics:
    - LOWER baseline (0.4) - acetylcholine is phasic (burst-driven)
    - MODERATE decay (0.012/s) - moderate persistence
    - Standard desensitization threshold (0.8)

    Usage identical to DopamineModulator:
        modulator = AcetylcholineModulator(kill_switch_callback=safety.kill_switch.trigger)
        actual_change = modulator.modulate(delta=0.3, source="surprise_signal")
        level = modulator.level
        metrics = modulator.get_health_metrics()
    """

    def __init__(
        self,
        config: Optional[ModulatorConfig] = None,
        kill_switch_callback: Optional[Callable[[str], None]] = None
    ):
        """Initialize acetylcholine modulator with biological defaults.

        Args:
            config: Optional custom configuration. If None, uses acetylcholine defaults:
                - baseline=0.4 (lower - phasic modulator)
                - decay_rate=0.012 (moderate decay)
            kill_switch_callback: Optional callback for emergency shutdown
        """
        if config is None:
            config = ModulatorConfig(
                baseline=0.4,  # ACh: lower baseline (phasic, burst-driven)
                decay_rate=0.012,  # ACh: moderate decay
                desensitization_threshold=0.8,
                desensitization_factor=0.5,
                smoothing_factor=0.2,
                max_change_per_step=0.1
            )

        super().__init__(config, kill_switch_callback)

    def get_modulator_name(self) -> str:
        """Return modulator name for logging/metrics."""
        return "acetylcholine"
