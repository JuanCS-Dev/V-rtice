"""Maximus Vestibular Service - Semicircular Canals Module.

This module simulates the function of semicircular canals within the Maximus
AI's Vestibular Service. Inspired by biological semicircular canals, this
module is responsible for detecting angular accelerations (rotational movements)
and changes in the AI's head position.

Key functionalities include:
- Ingesting data from simulated gyroscopes.
- Processing angular motion data to determine changes in pitch, roll, and yaw.
- Perceiving rotational movements and their speed.
- Providing real-time information about angular motion and head rotation to other
  Maximus AI services for navigation, balance control, and spatial awareness,
  especially during dynamic movements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


class SemicircularCanals:
    """Detects angular accelerations (rotational movements) and changes in the
    AI's head position.

    Ingests data from simulated gyroscopes, processes angular motion data,
    and perceives rotational movements and their speed.
    """

    def __init__(self):
        """Initializes the SemicircularCanals."""
        self.last_processed_time: Optional[datetime] = None
        self.current_angular_velocity: List[float] = [0.0, 0.0, 0.0]
        self.current_orientation_change: Dict[str, float] = {
            "pitch_change": 0.0,
            "roll_change": 0.0,
            "yaw_change": 0.0,
        }
        self.current_status: str = "monitoring_angular_motion"

    def process_gyroscope_data(self, gyroscope_data: List[float]) -> Dict[str, Any]:
        """Processes simulated gyroscope data to determine angular motion.

        Args:
            gyroscope_data (List[float]): [x, y, z] angular velocity values.

        Returns:
            Dict[str, Any]: A dictionary containing the perceived angular motion.

        Raises:
            ValueError: If gyroscope_data is not a list of 3 floats.
        """
        if not (
            isinstance(gyroscope_data, list)
            and len(gyroscope_data) == 3
            and all(isinstance(x, (int, float)) for x in gyroscope_data)
        ):
            raise ValueError("gyroscope_data must be a list of 3 floats.")

        print(f"[SemicircularCanals] Processing gyroscope data: {gyroscope_data}")

        self.current_angular_velocity = gyroscope_data

        # Simulate angular changes (simplified: directly map angular velocity to changes)
        self.current_orientation_change["pitch_change"] = gyroscope_data[0] * 0.1  # Example scaling
        self.current_orientation_change["roll_change"] = gyroscope_data[1] * 0.1
        self.current_orientation_change["yaw_change"] = gyroscope_data[2] * 0.1

        self.last_processed_time = datetime.now()

        return {
            "timestamp": self.last_processed_time.isoformat(),
            "angular_velocity": self.current_angular_velocity,
            "pitch_change": self.current_orientation_change["pitch_change"],
            "roll_change": self.current_orientation_change["roll_change"],
            "yaw_change": self.current_orientation_change["yaw_change"],
            "rotation_detected": np.linalg.norm(np.array(gyroscope_data)) > 0.05,  # Simple rotation detection
        }

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Semicircular Canals module.

        Returns:
            Dict[str, Any]: A dictionary summarizing the module's status.
        """
        return {
            "status": self.current_status,
            "last_processed": (self.last_processed_time.isoformat() if self.last_processed_time else "N/A"),
            "current_angular_velocity": self.current_angular_velocity,
            "current_orientation_change": self.current_orientation_change,
        }
