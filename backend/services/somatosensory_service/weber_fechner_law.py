"""Maximus Somatosensory Service - Weber-Fechner Law Module.

This module implements the Weber-Fechner Law, a psychophysical principle that
describes the relationship between the physical magnitude of a stimulus and its
perceived intensity. In the context of Maximus AI's somatosensory system, this
law is used to model how Maximus perceives changes in physical stimuli like
pressure or temperature.

By applying this law, Maximus can process raw sensor data into a more
biologically plausible representation of perceived sensation, allowing for a
numerical understanding of how stimuli are experienced rather than just their
objective measurements.
"""

import math


class WeberFechnerLaw:
    """Implements the Weber-Fechner Law to model perceived stimulus intensity.

    This law describes the relationship between the physical magnitude of a
    stimulus and its perceived intensity.
    """

    def __init__(self, k_constant: float = 0.1):
        """Initializes the WeberFechnerLaw module with a Weber constant.

        Args:
            k_constant (float): The Weber fraction (k) for the specific sensory modality.
                This value varies depending on the type of stimulus (e.g., light, sound, pressure).
        """
        self.k_constant = k_constant

    def calculate_perceived_intensity(
        self, stimulus_magnitude: float, reference_stimulus: float = 1.0
    ) -> float:
        """Calculates the perceived intensity of a stimulus based on the Weber-Fechner Law.

        The formula used is P = k * log(S / S0), where:
        - P is the perceived intensity.
        - k is the Weber fraction (k_constant).
        - S is the magnitude of the stimulus (stimulus_magnitude).
        - S0 is the reference stimulus (threshold or baseline).

        Args:
            stimulus_magnitude (float): The physical magnitude of the stimulus.
            reference_stimulus (float): The reference or threshold stimulus magnitude.

        Returns:
            float: The calculated perceived intensity.

        Raises:
            ValueError: If stimulus_magnitude or reference_stimulus is non-positive.
        """
        if stimulus_magnitude <= 0 or reference_stimulus <= 0:
            raise ValueError(
                "Stimulus magnitudes must be positive for logarithmic calculation."
            )

        # Weber-Fechner Law: P = k * log(S / S0)
        perceived_intensity = self.k_constant * math.log(
            stimulus_magnitude / reference_stimulus
        )
        return perceived_intensity

    def get_k_constant(self) -> float:
        """Returns the current Weber fraction (k_constant).

        Returns:
            float: The Weber fraction.
        """
        return self.k_constant

    def set_k_constant(self, new_k: float):
        """Sets a new Weber fraction (k_constant).

        Args:
            new_k (float): The new Weber fraction to set.

        Raises:
            ValueError: If new_k is non-positive.
        """
        if new_k <= 0:
            raise ValueError("Weber constant (k) must be positive.")
        self.k_constant = new_k
