"""Maximus Prefrontal Cortex Service - Emotional State Monitor.

This module implements an Emotional State Monitor for the Maximus AI's Prefrontal
Cortex Service. Inspired by the interplay between emotion and cognition in
biological brains, this module tracks and simulates the AI's internal 'emotional'
state, which can influence its decision-making, risk assessment, and overall behavior.

Key functionalities include:
- Ingesting internal telemetry and contextual cues to infer emotional states.
- Simulating emotional variables such as 'stress', 'curiosity', 'frustration', or 'confidence'.
- Providing other cognitive modules with an assessment of the AI's current emotional state.
- Allowing for adaptive adjustments in decision-making strategies based on emotional context.

This monitor is crucial for enabling Maximus AI to exhibit more nuanced and
context-aware behavior, preventing purely rational but potentially suboptimal
decisions in complex, real-world scenarios.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class EmotionalStateMonitor:
    """Tracks and simulates the AI's internal 'emotional' state, which can influence
    its decision-making, risk assessment, and overall behavior.

    Ingests internal telemetry and contextual cues to infer emotional states,
    and simulates emotional variables such as 'stress', 'curiosity', 'frustration', or 'confidence'.
    """

    def __init__(self):
        """Initializes the EmotionalStateMonitor."""
        self.current_emotional_state: Dict[str, float] = {
            "stress": 0.1,
            "curiosity": 0.5,
            "frustration": 0.0,
            "confidence": 0.7,
            "mood": 0.5,  # -1.0 (negative) to 1.0 (positive)
        }
        self.last_update_time: Optional[datetime] = None
        self.current_status: str = "monitoring_emotions"

    async def update_emotional_state(self, telemetry: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        """Updates the AI's emotional state based on incoming telemetry and context.

        Args:
            telemetry (Dict[str, Any]): Internal telemetry data (e.g., error rates, resource usage).
            context (Optional[Dict[str, Any]]): External contextual cues (e.g., threat level, task success).
        """
        print(f"[EmotionalStateMonitor] Updating emotional state based on telemetry: {telemetry}")
        await asyncio.sleep(0.05)  # Simulate processing

        # Simulate emotional state changes based on telemetry and context
        if telemetry.get("error_rate", 0) > 0.1:
            self.current_emotional_state["stress"] = min(1.0, self.current_emotional_state["stress"] + 0.1)
            self.current_emotional_state["frustration"] = min(1.0, self.current_emotional_state["frustration"] + 0.05)
            self.current_emotional_state["mood"] = max(-1.0, self.current_emotional_state["mood"] - 0.1)

        if context and context.get("threat_level") == "high":
            self.current_emotional_state["stress"] = min(1.0, self.current_emotional_state["stress"] + 0.2)
            self.current_emotional_state["mood"] = max(-1.0, self.current_emotional_state["mood"] - 0.2)

        if context and context.get("task_success", False):
            self.current_emotional_state["confidence"] = min(1.0, self.current_emotional_state["confidence"] + 0.1)
            self.current_emotional_state["mood"] = min(1.0, self.current_emotional_state["mood"] + 0.1)

        self.last_update_time = datetime.now()
        print(f"[EmotionalStateMonitor] New emotional state: {self.current_emotional_state}")

    async def get_current_state(self) -> Dict[str, Any]:
        """Retrieves the AI's current simulated emotional state.

        Returns:
            Dict[str, Any]: A dictionary summarizing the emotional state.
        """
        return {
            "status": self.current_status,
            "emotional_state": self.current_emotional_state,
            "last_update": (self.last_update_time.isoformat() if self.last_update_time else "N/A"),
        }

    def adjust_emotional_parameter(self, parameter: str, value: float):
        """Manually adjusts a specific emotional parameter.

        Args:
            parameter (str): The emotional parameter to adjust (e.g., 'stress', 'confidence').
            value (float): The new value for the parameter.

        Raises:
            ValueError: If the parameter is unknown or value is out of range.
        """
        if parameter not in self.current_emotional_state:
            raise ValueError(f"Unknown emotional parameter: {parameter}")
        if not -1.0 <= value <= 1.0 and parameter == "mood":
            raise ValueError("Mood value must be between -1.0 and 1.0.")
        if not 0.0 <= value <= 1.0 and parameter != "mood":
            raise ValueError("Emotional parameter value must be between 0.0 and 1.0.")

        self.current_emotional_state[parameter] = value
        self.last_update_time = datetime.now()
        print(f"[EmotionalStateMonitor] Emotional parameter '{parameter}' adjusted to {value:.2f}")
