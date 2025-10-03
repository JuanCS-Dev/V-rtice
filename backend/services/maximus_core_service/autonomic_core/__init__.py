"""
Autonomic Core - System 1 (Unconscious Processing)
====================================================

O substrato inconsciente que sustenta toda a operação do Maximus AI.
Inspirado no cérebro humano, onde 95% do processamento é inconsciente.

Components:
-----------
1. Homeostatic Control Loop (HCL) - Auto-regulation
2. Predictive Coding Network - Anticipation
3. Attention System - Filtering & Focusing
4. Skill Learning - Automated behaviors
5. Neuromodulation - Meta-learning

Key Principles:
---------------
- FAST: <100ms response time
- PARALLEL: Multiple processes simultaneously
- AUTOMATIC: No conscious intervention needed
- PREDICTIVE: Always anticipating next state
- ADAPTIVE: Continuously learning and optimizing

This layer runs continuously in background, freeing System 2
(Reasoning Engine) to focus on novel, complex problems only.
"""

from .homeostatic_control import HomeostaticControlLoop
from .system_monitor import SystemMonitor
from .resource_analyzer import ResourceAnalyzer
from .resource_planner import ResourcePlanner
from .resource_executor import ResourceExecutor

__all__ = [
    'HomeostaticControlLoop',
    'SystemMonitor',
    'ResourceAnalyzer',
    'ResourcePlanner',
    'ResourceExecutor'
]
