"""Maximus Digital Thalamus Service - Sensory Gating Module.

This module implements a sensory gating mechanism within the Maximus AI's
Digital Thalamus. Inspired by biological sensory gating, this module controls
the flow of sensory information, selectively allowing or suppressing inputs
based on their relevance, intensity, or current cognitive load.

By filtering out irrelevant or redundant sensory data at an early stage,
Maximus can prevent sensory overload and ensure that only critical information
reaches higher-level processing centers. This is crucial for maintaining focus,
optimizing resource allocation, and enhancing the efficiency of perception
and decision-making.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime


class SensoryGating:
    """Controls the flow of sensory information, selectively allowing or suppressing
    inputs based on their relevance, intensity, or current cognitive load.

    Filters out irrelevant or redundant sensory data at an early stage,
    preventing sensory overload.
    """

    def __init__(self, default_threshold: float = 0.3):
        """Initializes the SensoryGating module.

        Args:
            default_threshold (float): The default threshold for allowing sensory data.
        """
        self.default_threshold = default_threshold
        self.gating_rules: Dict[str, float] = {
            "visual": 0.4,
            "auditory": 0.3,
            "chemical": 0.5,
            "somatosensory": 0.2
        }
        self.last_gating_decision: Optional[datetime] = None
        self.blocked_data_count: int = 0

    def allow_data(self, sensor_type: str, data_intensity: float) -> bool:
        """Determines if sensory data should be allowed to pass through the thalamus.

        Args:
            sensor_type (str): The type of sensory data (e.g., 'visual', 'auditory').
            data_intensity (float): The perceived intensity or importance of the data (0.0 to 1.0).

        Returns:
            bool: True if the data is allowed, False if it's gated (blocked).
        """
        threshold = self.gating_rules.get(sensor_type, self.default_threshold)
        
        self.last_gating_decision = datetime.now()

        if data_intensity >= threshold:
            print(f"[SensoryGating] Allowing {sensor_type} data (intensity: {data_intensity:.2f} >= threshold: {threshold:.2f})")
            return True
        else:
            self.blocked_data_count += 1
            print(f"[SensoryGating] Blocking {sensor_type} data (intensity: {data_intensity:.2f} < threshold: {threshold:.2f})")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the sensory gating module.

        Returns:
            Dict[str, Any]: A dictionary with the current status, last decision time, and total blocked data count.
        """
        return {
            "status": "active",
            "default_threshold": self.default_threshold,
            "gating_rules": self.gating_rules,
            "last_gating_decision": self.last_gating_decision.isoformat() if self.last_gating_decision else "N/A",
            "blocked_data_count_since_startup": self.blocked_data_count
        }

    def set_gating_threshold(self, sensor_type: str, threshold: float):
        """Sets a new gating threshold for a specific sensor type.

        Args:
            sensor_type (str): The type of sensor.
            threshold (float): The new threshold (0.0 to 1.0).
        
        Raises:
            ValueError: If threshold is outside the valid range [0.0, 1.0].
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0.")
        self.gating_rules[sensor_type] = threshold
