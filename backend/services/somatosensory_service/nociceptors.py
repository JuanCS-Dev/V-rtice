"""Maximus Somatosensory Service - Nociceptors Module.

This module simulates the function of nociceptors, which are sensory receptors
that detect and transmit information about noxious (potentially damaging) stimuli.
In Maximus AI, this translates to processing data related to extreme pressure,
temperature, or other inputs that could indicate harm or require immediate attention.

The Nociceptors module is crucial for Maximus's self-preservation mechanisms,
allowing it to identify and react to potentially harmful physical interactions.
It provides raw 'pain' or discomfort signals that can trigger defensive behaviors
or resource re-allocation within the AI system.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class Nociceptors:
    """Simulates the function of nociceptors, detecting noxious stimuli.

    This module processes data related to extreme pressure, temperature, or other
    inputs that could indicate harm or require immediate attention.
    """

    def __init__(self):
        """Initializes the Nociceptors module."""
        self.last_stimulus_time: Optional[datetime] = None
        self.current_pain_level: float = 0.0
        self.threshold_pressure: float = 0.8  # Pressure above this is noxious
        self.threshold_temp_high: float = 40.0  # Temp above this is noxious
        self.threshold_temp_low: float = 5.0  # Temp below this is noxious

    async def process_stimulus(
        self,
        pressure: float,
        temperature: Optional[float] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processes a simulated noxious stimulus.

        Args:
            pressure (float): The simulated pressure applied (0.0 to 1.0).
            temperature (Optional[float]): The simulated temperature in Celsius.
            location (Optional[str]): The simulated location of the stimulus.

        Returns:
            Dict[str, Any]: A dictionary containing the nociceptor response, including pain level.
        """
        print(
            f"[Nociceptors] Processing stimulus: Pressure={pressure}, Temp={temperature}, Location={location}"
        )
        await asyncio.sleep(0.1)  # Simulate processing time

        pain_level = 0.0
        stimulus_type = []

        if pressure > self.threshold_pressure:
            pain_level += (
                pressure - self.threshold_pressure
            ) * 5  # Scale pain with intensity
            stimulus_type.append("high_pressure")

        if temperature is not None:
            if temperature > self.threshold_temp_high:
                pain_level += (temperature - self.threshold_temp_high) * 0.5
                stimulus_type.append("high_temperature")
            elif temperature < self.threshold_temp_low:
                pain_level += (self.threshold_temp_low - temperature) * 0.5
                stimulus_type.append("low_temperature")

        self.current_pain_level = min(1.0, pain_level)  # Cap pain level at 1.0
        self.last_stimulus_time = datetime.now()

        return {
            "timestamp": self.last_stimulus_time.isoformat(),
            "location": location,
            "stimulus_detected": bool(stimulus_type),
            "stimulus_type": stimulus_type,
            "raw_pain_level": self.current_pain_level,
            "requires_attention": self.current_pain_level
            > 0.3,  # Threshold for requiring attention
        }

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current status of the nociceptor system.

        Returns:
            Dict[str, Any]: A dictionary with the current pain level and last stimulus time.
        """
        return {
            "status": "active",
            "current_pain_level": self.current_pain_level,
            "last_stimulus": (
                self.last_stimulus_time.isoformat()
                if self.last_stimulus_time
                else "N/A"
            ),
        }
