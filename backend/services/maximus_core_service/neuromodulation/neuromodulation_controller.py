"""Neuromodulation Controller - Orchestrates all 4 neuromodulatory systems.

Coordinates dopamine, serotonin, norepinephrine, and acetylcholine systems
to modulate AI behavior in bio-inspired ways.

Production-ready implementation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .acetylcholine_system import AcetylcholineState, AcetylcholineSystem
from .dopamine_system import DopamineState, DopamineSystem
from .norepinephrine_system import NorepinephrineState, NorepinephrineSystem
from .serotonin_system import SerotoninState, SerotoninSystem

logger = logging.getLogger(__name__)


@dataclass
class GlobalNeuromodulationState:
    """Global state of all neuromodulatory systems."""

    dopamine: DopamineState
    serotonin: SerotoninState
    norepinephrine: NorepinephrineState
    acetylcholine: AcetylcholineState
    overall_mood: float  # Composite mood (0.0-1.0)
    cognitive_load: float  # Current cognitive load (0.0-1.0)
    timestamp: datetime


class NeuromodulationController:
    """Coordinates all 4 neuromodulatory systems.

    Provides unified interface for:
    - Learning rate modulation (dopamine)
    - Exploration-exploitation (serotonin)
    - Attention and arousal (norepinephrine, acetylcholine)
    - Stress response (all systems)

    Usage:
        controller = NeuromodulationController()
        controller.process_reward(expected=0.5, actual=0.8)
        learning_rate = controller.get_modulated_learning_rate(base_lr=0.01)
    """

    def __init__(self):
        """Initialize neuromodulation controller with all 4 systems."""
        # Create 4 neuromodulatory systems
        self.dopamine = DopamineSystem()
        self.serotonin = SerotoninSystem()
        self.norepinephrine = NorepinephrineSystem()
        self.acetylcholine = AcetylcholineSystem()

        # Global state
        self.cognitive_load = 0.0
        self.stress_level = 0.0

        logger.info("Neuromodulation controller initialized (4 systems operational)")

    def process_reward(self, expected_reward: float, actual_reward: float, success: bool) -> dict[str, float]:
        """Process task outcome through neuromodulatory systems.

        Args:
            expected_reward: Expected reward value
            actual_reward: Actual reward received
            success: Whether task succeeded

        Returns:
            Dict with modulation parameters
        """
        # Dopamine: Compute RPE
        rpe = self.dopamine.compute_reward_prediction_error(expected_reward, actual_reward)

        # Update dopamine motivation
        self.dopamine.update_motivation()

        # Serotonin: Update from outcome
        self.serotonin.update_from_outcome(success=success, stress=self.stress_level)

        logger.info(
            f"Reward processed: expected={expected_reward:.2f}, actual={actual_reward:.2f}, "
            f"rpe={rpe:.2f}, success={success}"
        )

        return {
            "rpe": rpe,
            "motivation": self.dopamine.motivation_level,
            "serotonin_level": self.serotonin.level,
        }

    def respond_to_threat(self, threat_severity: float):
        """Activate stress/threat response.

        Args:
            threat_severity: Severity of threat (0.0-1.0)
        """
        # Update stress level
        self.stress_level = max(self.stress_level, threat_severity)

        # Norepinephrine surge (fight-or-flight)
        self.norepinephrine.respond_to_threat(threat_severity)

        # Serotonin depletion from stress
        self.serotonin.update_from_outcome(success=False, stress=threat_severity)

        # Dopamine stress response
        self.dopamine.update_tonic_level(stress_level=threat_severity)

        logger.warning(f"Threat response activated! Severity: {threat_severity:.2f}")

    def modulate_attention(self, importance: float, salience: float) -> bool:
        """Determine whether to attend to stimulus.

        Args:
            importance: Task importance (0.0-1.0)
            salience: Stimulus salience (0.0-1.0)

        Returns:
            True if should attend
        """
        # Acetylcholine gates attention
        self.acetylcholine.modulate_attention(importance=importance)

        # Check if salience exceeds threshold
        should_attend = self.acetylcholine.should_attend(salience=salience)

        # Norepinephrine provides attention gain
        attention_gain = self.norepinephrine.get_attention_gain()

        logger.debug(
            f"Attention check: importance={importance:.2f}, salience={salience:.2f}, "
            f"attend={should_attend}, gain={attention_gain:.2f}"
        )

        return should_attend

    def get_modulated_learning_rate(self, base_learning_rate: float) -> float:
        """Get learning rate modulated by dopamine RPE.

        Args:
            base_learning_rate: Base learning rate

        Returns:
            Modulated learning rate
        """
        # Dopamine modulates learning rate based on surprise (RPE magnitude)
        modulated_lr = self.dopamine.modulate_learning_rate(
            base_learning_rate=base_learning_rate, rpe=self.dopamine.phasic_burst
        )

        return modulated_lr

    def get_exploration_rate(self) -> float:
        """Get exploration rate (epsilon) from serotonin.

        Returns:
            Exploration rate (0.0-1.0)
        """
        return self.serotonin.get_exploration_rate()

    def get_discount_factor(self) -> float:
        """Get temporal discount factor (gamma) from serotonin.

        Returns:
            Discount factor (0.0-1.0)
        """
        return self.serotonin.get_patience()

    def update_cognitive_load(self, workload: float):
        """Update systems based on cognitive workload.

        Args:
            workload: Current workload (0.0-1.0)
        """
        self.cognitive_load = workload

        # Update arousal (norepinephrine)
        self.norepinephrine.update(workload=workload)

        # Update attention (acetylcholine)
        self.acetylcholine.update(workload=workload)

        logger.debug(f"Cognitive load updated: {workload:.2f}")

    def get_overall_mood(self) -> float:
        """Calculate composite mood from all systems.

        Returns:
            Overall mood (0.0-1.0, higher is better)
        """
        # Weighted combination of systems
        mood = (
            0.3 * self.dopamine.motivation_level  # Motivation
            + 0.3 * self.serotonin.level  # Mood stability
            + 0.2 * (1.0 - self.stress_level)  # Low stress
            + 0.2 * min(1.0, self.norepinephrine.level)  # Moderate arousal
        )

        return max(0.0, min(1.0, mood))

    def get_global_state(self) -> GlobalNeuromodulationState:
        """Get complete state of all systems.

        Returns:
            Global neuromodulation state
        """
        return GlobalNeuromodulationState(
            dopamine=self.dopamine.get_state(),
            serotonin=self.serotonin.get_state(),
            norepinephrine=self.norepinephrine.get_state(),
            acetylcholine=self.acetylcholine.get_state(),
            overall_mood=self.get_overall_mood(),
            cognitive_load=self.cognitive_load,
            timestamp=datetime.utcnow(),
        )

    def export_state(self) -> dict[str, Any]:
        """Export state as dictionary for monitoring/logging.

        Returns:
            State dictionary
        """
        global_state = self.get_global_state()

        return {
            "dopamine": {
                "tonic": global_state.dopamine.tonic_level,
                "phasic": global_state.dopamine.phasic_burst,
                "motivation": global_state.dopamine.motivation_level,
                "learning_rate": global_state.dopamine.learning_rate,
            },
            "serotonin": {
                "level": global_state.serotonin.level,
                "exploration_rate": global_state.serotonin.exploration_rate,
                "risk_tolerance": global_state.serotonin.risk_tolerance,
                "patience": global_state.serotonin.patience,
            },
            "norepinephrine": {
                "level": global_state.norepinephrine.level,
                "arousal": global_state.norepinephrine.arousal,
                "attention_gain": global_state.norepinephrine.attention_gain,
                "stressed": global_state.norepinephrine.stress_response,
            },
            "acetylcholine": {
                "level": global_state.acetylcholine.level,
                "salience_threshold": global_state.acetylcholine.attention_filter,
                "memory_encoding": global_state.acetylcholine.memory_encoding_rate,
                "focus_mode": global_state.acetylcholine.focus_narrow,
            },
            "global": {
                "mood": global_state.overall_mood,
                "cognitive_load": global_state.cognitive_load,
                "stress": self.stress_level,
            },
            "timestamp": global_state.timestamp.isoformat(),
        }

    def reset_all(self):
        """Reset all neuromodulatory systems to baseline."""
        self.dopamine.reset()
        self.serotonin.reset()
        self.norepinephrine.reset()
        self.acetylcholine.reset()

        self.cognitive_load = 0.0
        self.stress_level = 0.0

        logger.info("All neuromodulatory systems reset to baseline")
