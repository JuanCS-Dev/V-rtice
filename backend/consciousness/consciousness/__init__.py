"""
Consciousness Module - PFC Orchestration and Theory of Mind

Implements the Prefrontal Cortex (PFC) orchestration layer that integrates:
- Compassion Planner (detect suffering → plan interventions)
- DDL Engine (constitutional compliance via deontic logic)
- MIP (ethical evaluation of plans)
- Theory of Mind (infer user mental states)
"""

from .prefrontal_cortex import PrefrontalCortex, OrchestratedDecision
from .tom_engine import ToMEngine, UserMentalState, EmotionalState

__all__ = [
    "PrefrontalCortex",
    "OrchestratedDecision",
    "ToMEngine",
    "UserMentalState",
    "EmotionalState",
]
