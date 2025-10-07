"""Skill Learning System - Client Interface to HSAS Service.

This module provides a lightweight client interface to the full HSAS (Hybrid Skill
Acquisition System) service. The HSAS service implements:

1. Model-Free RL (Basal Ganglia) - Fast habitual responses
2. Model-Based RL (Cerebellum/PFC) - Deliberate planning
3. Skill Primitives Library - Reusable action sequences
4. Hierarchical Skills - Composed from primitives

Architecture:
- Full implementations: ../hsas_service/ (port 8023)
- Client interface: This module (SkillLearningController)

NO MOCKS - Production-ready HTTP client to real HSAS service.

Author: Maximus AI Team + Claude Code
Version: 1.1.0 - REGRA DE OURO compliant (removed placeholders)
"""

from .skill_learning_controller import (
    SkillExecutionResult,
    SkillLearningController,
)

__all__ = [
    "SkillLearningController",
    "SkillExecutionResult",
]

__version__ = "1.1.0"
