"""
Guardian Agents - Constitutional Enforcement System

Autonomous agents that monitor and enforce the Vértice Constitution
across the entire MAXIMUS ecosystem.

These agents implement Anexo D: A Doutrina da "Execução Constitucional"
and ensure constitutional compliance through automated monitoring and
intervention capabilities.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

from .base import (
    GuardianAgent,
    GuardianDecision,
    GuardianIntervention,
    GuardianReport,
    VetoAction,
    ConstitutionalViolation,
    GuardianPriority,
    InterventionType
)
from .article_ii_guardian import ArticleIIGuardian
from .article_iii_guardian import ArticleIIIGuardian
from .article_iv_guardian import ArticleIVGuardian
from .article_v_guardian import ArticleVGuardian
from .coordinator import GuardianCoordinator

__all__ = [
    # Base classes
    "GuardianAgent",
    "GuardianDecision",
    "GuardianIntervention",
    "GuardianReport",
    "VetoAction",
    "ConstitutionalViolation",
    "GuardianPriority",
    "InterventionType",
    # Specific Guardians
    "ArticleIIGuardian",
    "ArticleIIIGuardian",
    "ArticleIVGuardian",
    "ArticleVGuardian",
    # Coordinator
    "GuardianCoordinator",
]