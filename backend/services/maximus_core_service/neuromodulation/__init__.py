"""Neuromodulation System - Bio-inspired global state modulation.

This module implements 4 neuromodulatory systems inspired by neuroscience:
1. Dopamine - Reward signaling, motivation, learning rate
2. Serotonin - Mood, risk tolerance, exploration vs exploitation
3. Norepinephrine - Arousal, attention, stress response
4. Acetylcholine - Attention gating, memory encoding

NO MOCKS - Production-ready implementation.

Author: Maximus AI Team
Version: 1.0.0
"""

from .acetylcholine_system import AcetylcholineSystem
from .dopamine_system import DopamineSystem
from .neuromodulation_controller import NeuromodulationController
from .norepinephrine_system import NorepinephrineSystem
from .serotonin_system import SerotoninSystem

__all__ = [
    "DopamineSystem",
    "SerotoninSystem",
    "NorepinephrineSystem",
    "AcetylcholineSystem",
    "NeuromodulationController",
]

__version__ = "1.0.0"
