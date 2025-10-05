"""Skill Learning System - Hybrid model-free and model-based reinforcement learning.

This module implements cerebellum + basal ganglia inspired skill acquisition:
1. Model-Free RL (Basal Ganglia) - Fast habitual responses
2. Model-Based RL (Cerebellum/PFC) - Deliberate planning
3. Skill Primitives Library - Reusable action sequences
4. Hierarchical Skills - Composed from primitives

NO MOCKS - Production-ready integration with HSAS service.

Author: Maximus AI Team
Version: 1.0.0
"""

from .skill_primitive import SkillPrimitive, PrimitiveLibrary
from .model_free_agent import ModelFreeAgent
from .model_based_agent import ModelBasedAgent
from .skill_composer import SkillComposer
from .skill_learning_controller import SkillLearningController

__all__ = [
    'SkillPrimitive',
    'PrimitiveLibrary',
    'ModelFreeAgent',
    'ModelBasedAgent',
    'SkillComposer',
    'SkillLearningController',
]

__version__ = '1.0.0'
