"""Maximus Vestibular Service - Otolith Organs Module.

This module simulates the function of otolith organs within the Maximus AI's
Vestibular Service. Inspired by biological otoliths, this module is responsible
for detecting linear accelerations (forward/backward, up/down, left/right)
and the orientation of the AI's 'head' relative to gravity.

Key functionalities include:
- Ingesting data from simulated accelerometers.
- Processing linear motion data to determine changes in velocity and position.
- Perceiving gravitational pull and inferring static orientation.
- Providing real-time information about linear motion and head tilt to other
  Maximus AI services for navigation, balance control, and spatial awareness.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


class OtolithOrgans:
    """Detects linear accelerations (forward/backward, up/down, left/right)
    and the orientation of the AI's 'head' relative to gravity.

    Ingests data from simulated accelerometers, processes linear motion data,
    and perceives gravitational pull.
    """

    def __init__(self):
        """Initializes the OtolithOrgans."""
        self.last_processed_time: Optional[datetime] = None
        self.current_linear_acceleration: List[float] = [0.0, 0.0, 0.0]
        self.current_orientation_gravity: List[float] = [
            0.0,
            0.0,
            1.0,
        ]  # Assuming Z is up
        self.current_status: str = "monitoring_linear_motion"

    def process_accelerometer_data(self, accelerometer_data: List[float]) -> Dict[str, Any]:
        """Processes simulated accelerometer data to determine linear motion and orientation.

        Args:
            accelerometer_data (List[float]): [x, y, z] acceleration values.

        Returns:
            Dict[str, Any]: A dictionary containing the perceived linear motion and orientation.

        Raises:
            ValueError: If accelerometer_data is not a list of 3 floats.
        """
        if not (
            isinstance(accelerometer_data, list)
            and len(accelerometer_data) == 3
            and all(isinstance(x, (int, float)) for x in accelerometer_data)
        ):
            raise ValueError("accelerometer_data must be a list of 3 floats.")

        print(f"[OtolithOrgans] Processing accelerometer data: {accelerometer_data}")

        # Simulate linear acceleration perception
        self.current_linear_acceleration = accelerometer_data

        # Simulate orientation relative to gravity (simplified)
        # Assuming gravity is [0, 0, -9.8] and accelerometer measures total acceleration
        # If AI is static, accelerometer measures gravity in opposite direction
        gravity_vector = np.array([0.0, 0.0, -9.8])
        accel_vector = np.array(accelerometer_data)

        # If the AI is not accelerating, the accelerometer measures -gravity
        # So, the orientation relative to gravity is roughly the inverse of the measured acceleration
        if np.linalg.norm(accel_vector) > 0.1:  # If there's significant acceleration
            # This is a very simplified model. Real orientation would use sensor fusion.
            self.current_orientation_gravity = [
                -accel_vector[0],
                -accel_vector[1],
                -accel_vector[2],
            ]
            norm = np.linalg.norm(self.current_orientation_gravity)
            if norm > 0:
                self.current_orientation_gravity = (self.current_orientation_gravity / norm).tolist()

        self.last_processed_time = datetime.now()

        return {
            "timestamp": self.last_processed_time.isoformat(),
            "linear_acceleration": self.current_linear_acceleration,
            "orientation_relative_to_gravity": self.current_orientation_gravity,
            "motion_detected": np.linalg.norm(np.array(accelerometer_data)) > 0.1,  # Simple motion detection
        }

    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Otolith Organs module.

        Returns:
            Dict[str, Any]: A dictionary summarizing the module's status.
        """
        return {
            "status": self.current_status,
            "last_processed": (self.last_processed_time.isoformat() if self.last_processed_time else "N/A"),
            "current_linear_acceleration": self.current_linear_acceleration,
            "current_orientation_gravity": self.current_orientation_gravity,
        }
