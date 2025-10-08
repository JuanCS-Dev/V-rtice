"""Maximus Prefrontal Cortex Service - Impulse Inhibition Module.

This module implements an Impulse Inhibition mechanism for the Maximus AI's
Prefrontal Cortex Service. Inspired by the biological prefrontal cortex's role
in self-control, this module is responsible for modulating the AI's tendency
to act impulsively, promoting more deliberate and rational decision-making.

Key functionalities include:
- Receiving signals from other cognitive modules indicating potential impulsive actions.
- Applying inhibitory controls to delay or suppress immediate responses.
- Balancing the need for rapid action with the benefits of careful consideration.
- Providing a mechanism for Maximus AI to override its default reactive behaviors,
  enabling it to adhere to long-term goals, ethical guidelines, and strategic plans,
  even under pressure.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class ImpulseInhibition:
    """Modulates the AI's tendency to act impulsively, promoting more deliberate
    and rational decision-making.

    Applies inhibitory controls to delay or suppress immediate responses,
    and balances the need for rapid action with careful consideration.
    """

    def __init__(self, initial_inhibition_level: float = 0.5):
        """Initializes the ImpulseInhibition module.

        Args:
            initial_inhibition_level (float): The initial level of impulse inhibition (0.0 to 1.0).
        """
        self.inhibition_level = initial_inhibition_level
        self.last_adjustment_time: Optional[datetime] = None
        self.current_status: str = "active"

    async def apply_inhibition(
        self, potential_action: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Applies inhibitory control to a potential action.

        Args:
            potential_action (Dict[str, Any]): The action being considered.
            context (Optional[Dict[str, Any]]): Additional context for inhibition decision.

        Returns:
            Dict[str, Any]: A dictionary indicating whether the action is inhibited and the reason.
        """
        print(f"[ImpulseInhibition] Applying inhibition to potential action: {potential_action.get('type', 'N/A')}")
        await asyncio.sleep(0.05)  # Simulate processing

        inhibit = False
        reason = "No inhibition applied."

        # Simulate inhibition logic based on level and context
        if self.inhibition_level > 0.7 and potential_action.get("risk_score", 0) > 0.5:
            inhibit = True
            reason = "High risk action inhibited due to high impulse control."
        elif self.inhibition_level < 0.3 and potential_action.get("urgency", 0) < 0.2:
            inhibit = True
            reason = "Low urgency action inhibited to allow for more deliberation."

        self.last_adjustment_time = datetime.now()

        return {
            "timestamp": self.last_adjustment_time.isoformat(),
            "action_inhibited": inhibit,
            "reason": reason,
            "inhibition_level": self.inhibition_level,
        }

    def adjust_inhibition_level(self, new_level: float):
        """Adjusts the overall impulse inhibition level.

        Args:
            new_level (float): The new inhibition level (0.0 to 1.0).

        Raises:
            ValueError: If new_level is outside the valid range [0.0, 1.0].
        """
        if not 0.0 <= new_level <= 1.0:
            raise ValueError("Inhibition level must be between 0.0 and 1.0.")
        self.inhibition_level = new_level
        self.last_adjustment_time = datetime.now()
        print(f"[ImpulseInhibition] Inhibition level adjusted to {new_level:.2f}")

    def get_inhibition_level(self) -> float:
        """Returns the current impulse inhibition level.

        Returns:
            float: The current inhibition level.
        """
        return self.inhibition_level

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Impulse Inhibition module.

        Returns:
            Dict[str, Any]: A dictionary summarizing the module's status.
        """
        return {
            "status": self.current_status,
            "inhibition_level": self.inhibition_level,
            "last_adjustment": (self.last_adjustment_time.isoformat() if self.last_adjustment_time else "N/A"),
        }
