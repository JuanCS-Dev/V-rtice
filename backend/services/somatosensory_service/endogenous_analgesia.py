"""Maximus Somatosensory Service - Endogenous Analgesia Module.

This module simulates the phenomenon of endogenous analgesia within the Maximus
AI's somatosensory system. Endogenous analgesia refers to the body's natural
ability to suppress pain, often through the release of endorphins and other
neurotransmitters.

In Maximus, this module models how the AI might modulate its perception of
'pain' or discomfort (e.g., from excessive pressure or temperature) based on
internal states or external context. This allows Maximus to prioritize tasks
and maintain operational stability even when experiencing adverse physical
stimuli, mimicking a crucial biological self-preservation mechanism.
"""

from typing import Any, Dict


class EndogenousAnalgesia:
    """Simulates the phenomenon of endogenous analgesia (natural pain suppression).

    This module models how Maximus AI might modulate its perception of 'pain' or
    discomfort based on internal states or external context.
    """

    def __init__(self, modulation_factor: float = 0.5):
        """Initializes the EndogenousAnalgesia module.

        Args:
            modulation_factor (float): A factor determining the effectiveness of pain modulation (0.0 to 1.0).
        """
        self.modulation_factor = modulation_factor

    def modulate_pain(self, raw_pain_level: float, internal_state: Dict[str, Any] = None) -> float:
        """Calculates the reduction in perceived pain based on the raw pain level and internal state.

        Args:
            raw_pain_level (float): The initial, unmodulated pain level (e.g., from nociceptors).
            internal_state (Dict[str, Any]): Optional. Internal state of Maximus (e.g., stress, focus).

        Returns:
            float: The amount of pain reduction due to endogenous analgesia.
        """
        print(f"[EndogenousAnalgesia] Modulating pain level: {raw_pain_level}")

        # Simple modulation logic: higher focus or lower stress might increase analgesia
        analgesia_effect = raw_pain_level * self.modulation_factor

        if internal_state and internal_state.get("focus_level", 0) > 0.7:
            analgesia_effect *= 1.2  # Increase analgesia if highly focused

        return analgesia_effect

    def get_modulation_factor(self) -> float:
        """Returns the current pain modulation factor.

        Returns:
            float: The modulation factor.
        """
        return self.modulation_factor

    def set_modulation_factor(self, new_factor: float):
        """Sets a new pain modulation factor.

        Args:
            new_factor (float): The new modulation factor (0.0 to 1.0).

        Raises:
            ValueError: If new_factor is outside the valid range [0.0, 1.0].
        """
        if not 0.0 <= new_factor <= 1.0:
            raise ValueError("Modulation factor must be between 0.0 and 1.0.")
        self.modulation_factor = new_factor
