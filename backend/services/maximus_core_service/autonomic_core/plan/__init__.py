"""
Autonomic Plan Module - Resource Arbitration

Dynamic resource allocation using:
- Fuzzy Logic Controller (3 operational modes)
- Soft Actor-Critic RL Agent (continuous optimization)
"""

from .fuzzy_controller import FuzzyLogicController
from .mode_definitions import OPERATIONAL_MODES
from .rl_agent import SACAgent

__all__ = ["FuzzyLogicController", "SACAgent", "OPERATIONAL_MODES"]
