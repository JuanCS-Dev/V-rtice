"""Maximus Digital Thalamus Service - Attention Control Module.

This module implements an attention control mechanism within the Maximus AI's
Digital Thalamus. Inspired by biological attention, this module dynamically
prioritizes and routes sensory information based on its perceived importance,
saliency, or relevance to current goals.

By selectively enhancing or suppressing the flow of sensory data, Maximus can
focus its cognitive resources on the most critical information, preventing
overload and improving the efficiency of higher-level processing. This is crucial
for maintaining responsiveness and effective decision-making in complex and
dynamic environments.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, Optional


class AttentionControl:
    """Dynamically prioritizes and routes sensory information based on its perceived
    importance, saliency, or relevance to current goals.

    Selectively enhances or suppresses the flow of sensory data, preventing
    overload and improving the efficiency of higher-level processing.
    """

    def __init__(self):
        """Initializes the AttentionControl module."""
        self.last_prioritization_time: Optional[datetime] = None
        self.current_focus: Optional[str] = None
        self.current_status: str = "monitoring_attention"
        self.priority_weights: Dict[str, float] = {
            "visual": 0.8,
            "auditory": 0.7,
            "chemical": 0.6,
            "somatosensory": 0.5,
        }

    async def prioritize_and_route(
        self, sensory_data: Dict[str, Any], sensor_type: str, priority: int
    ) -> Dict[str, Any]:
        """Prioritizes and routes sensory data to appropriate cortical services.

        Args:
            sensory_data (Dict[str, Any]): The pre-processed sensory data.
            sensor_type (str): The type of sensory data (e.g., 'visual', 'auditory').
            priority (int): The initial priority assigned to the data (1-10).

        Returns:
            Dict[str, Any]: The processed and routed sensory data, potentially with added metadata.
        """
        self.current_status = "prioritizing_and_routing"
        print(
            f"[AttentionControl] Prioritizing {sensor_type} data with initial priority {priority}"
        )
        await asyncio.sleep(0.05)  # Simulate processing

        # Calculate effective priority based on initial priority and type-specific weights
        effective_priority = priority * self.priority_weights.get(sensor_type, 0.5)

        # Simulate routing decision (e.g., to Maximus Core, Prefrontal Cortex)
        routing_destination = "Maximus_Core_Service"
        if effective_priority > 6.0:
            routing_destination = "Prefrontal_Cortex_Service"  # Higher priority to higher cognitive functions

        self.current_focus = sensor_type
        self.last_prioritization_time = datetime.now()
        self.current_status = "monitoring_attention"

        processed_data = sensory_data.copy()
        processed_data["effective_priority"] = effective_priority
        processed_data["routing_destination"] = routing_destination
        processed_data["attention_notes"] = (
            f"Routed to {routing_destination} based on effective priority."
        )

        return processed_data

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the attention control module.

        Returns:
            Dict[str, Any]: A dictionary with the current status, last prioritization time, and current focus.
        """
        return {
            "status": self.current_status,
            "last_prioritization": (
                self.last_prioritization_time.isoformat()
                if self.last_prioritization_time
                else "N/A"
            ),
            "current_focus": self.current_focus,
            "priority_weights": self.priority_weights,
        }

    def set_priority_weight(self, sensor_type: str, weight: float):
        """Sets a new priority weight for a specific sensor type.

        Args:
            sensor_type (str): The type of sensor (e.g., 'visual').
            weight (float): The new weight (0.0 to 1.0).

        Raises:
            ValueError: If weight is outside the valid range [0.0, 1.0].
        """
        if not 0.0 <= weight <= 1.0:
            raise ValueError("Priority weight must be between 0.0 and 1.0.")
        self.priority_weights[sensor_type] = weight
