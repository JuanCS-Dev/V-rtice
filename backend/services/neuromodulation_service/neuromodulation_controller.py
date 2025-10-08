"""Maximus Neuromodulation Service - Neuromodulation Controller.

This module implements the central Neuromodulation Controller for the Maximus
AI. It acts as the orchestrator for all individual neuromodulator cores
(Dopamine, Serotonin, Noradrenaline, Acetylcholine), coordinating their actions
to achieve desired internal states and optimize overall AI performance.

Key functionalities include:
- Receiving high-level modulation requests or contextual cues.
- Translating requests into specific adjustments for individual neuromodulator cores.
- Monitoring the combined effects of neuromodulation on AI behavior.
- Providing a unified interface for managing and observing the AI's internal
  cognitive and emotional states (simulated).

This controller is crucial for enabling Maximus AI to dynamically adapt its
internal processing, learning, and decision-making to various tasks and
environmental conditions, enhancing its flexibility and effectiveness.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from acetylcholine_core import AcetylcholineCore
from dopamine_core import DopamineCore
from noradrenaline_core import NoradrenalineCore
from serotonin_core import SerotoninCore


class NeuromodulationController:
    """Orchestrates all individual neuromodulator cores (Dopamine, Serotonin,
    Noradrenaline, Acetylcholine), coordinating their actions to achieve desired
    internal states and optimize overall AI performance.

    Provides a unified interface for managing and observing the AI's internal
    cognitive and emotional states.
    """

    def __init__(
        self,
        dopamine_core: DopamineCore,
        serotonin_core: SerotoninCore,
        noradrenaline_core: NoradrenalineCore,
        acetylcholine_core: AcetylcholineCore,
    ):
        """Initializes the NeuromodulationController.

        Args:
            dopamine_core (DopamineCore): Instance of the DopamineCore.
            serotonin_core (SerotoninCore): Instance of the SerotoninCore.
            noradrenaline_core (NoradrenalineCore): Instance of the NoradrenalineCore.
            acetylcholine_core (AcetylcholineCore): Instance of the AcetylcholineCore.
        """
        self.dopamine_core = dopamine_core
        self.serotonin_core = serotonin_core
        self.noradrenaline_core = noradrenaline_core
        self.acetylcholine_core = acetylcholine_core
        self.last_control_action: Optional[datetime] = None
        print("[NeuromodulationController] Initialized Neuromodulation Controller.")

    async def modulate_parameter(
        self,
        modulator_type: str,
        parameter: str,
        value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Applies neuromodulation to a specific AI parameter via the relevant core.

        Args:
            modulator_type (str): The type of neuromodulator (e.g., 'dopamine', 'serotonin').
            parameter (str): The specific parameter to modulate (e.g., 'reward_sensitivity', 'attention_level').
            value (float): The new value for the parameter.
            context (Optional[Dict[str, Any]]): Additional context for the modulation.

        Returns:
            Dict[str, Any]: A dictionary summarizing the modulation effect.

        Raises:
            ValueError: If the modulator type or parameter is unsupported.
        """
        self.last_control_action = datetime.now()
        result = {"status": "failed", "message": "Unsupported modulator or parameter."}

        if modulator_type == "dopamine":
            if parameter == "reward_sensitivity":
                result = await self.dopamine_core.adjust_reward_sensitivity(value)
            elif parameter == "motivation_level":
                result = await self.dopamine_core.set_motivation_level(value)
            elif parameter == "exploration_bias":
                result = await self.dopamine_core.adjust_exploration_bias(value)
            else:
                raise ValueError(f"Unsupported dopamine parameter: {parameter}")
        elif modulator_type == "serotonin":
            if parameter == "mood_stability":
                result = await self.serotonin_core.set_mood_stability(value)
            elif parameter == "impulse_control":
                result = await self.serotonin_core.adjust_impulse_control(value)
            else:
                raise ValueError(f"Unsupported serotonin parameter: {parameter}")
        elif modulator_type == "noradrenaline":
            if parameter == "alertness_level":
                result = await self.noradrenaline_core.set_alertness_level(value)
            elif parameter == "stress_response":
                result = await self.noradrenaline_core.adjust_stress_response(value)
            else:
                raise ValueError(f"Unsupported noradrenaline parameter: {parameter}")
        elif modulator_type == "acetylcholine":
            if parameter == "attention_level":
                result = await self.acetylcholine_core.modulate_attention(context.get("target_focus", "general"), value)
            elif parameter == "learning_rate_modifier":
                result = await self.acetylcholine_core.adjust_learning_rate(value)
            elif parameter == "memory_consolidation_boost":
                result = await self.acetylcholine_core.boost_memory_consolidation(value)
            else:
                raise ValueError(f"Unsupported acetylcholine parameter: {parameter}")
        else:
            raise ValueError(f"Unsupported modulator type: {modulator_type}")

        return result

    async def get_overall_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of all neuromodulator cores.

        Returns:
            Dict[str, Any]: A dictionary summarizing the status of all neuromodulator cores.
        """
        dopamine_status = await self.dopamine_core.get_status()
        serotonin_status = await self.serotonin_core.get_status()
        noradrenaline_status = await self.noradrenaline_core.get_status()
        acetylcholine_status = await self.acetylcholine_core.get_status()

        return {
            "controller_status": "active",
            "last_control_action": (self.last_control_action.isoformat() if self.last_control_action else "N/A"),
            "dopamine_core": dopamine_status,
            "serotonin_core": serotonin_status,
            "noradrenaline_core": noradrenaline_status,
            "acetylcholine_core": acetylcholine_status,
        }
