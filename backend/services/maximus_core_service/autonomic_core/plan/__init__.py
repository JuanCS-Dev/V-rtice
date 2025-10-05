"""
Autonomic Plan Module - Resource Arbitration

Dynamic resource allocation using:
- Fuzzy Logic Controller (3 operational modes)
- Soft Actor-Critic RL Agent (continuous optimization)
"""

from .fuzzy_controller import FuzzyLogicController
from .rl_agent import SACAgent
from .mode_definitions import OPERATIONAL_MODES

__all__ = ['FuzzyLogicController', 'SACAgent', 'OPERATIONAL_MODES']
