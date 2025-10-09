"""
LRR - Loop de Raciocínio Recursivo
==================================

Metacognition engine for MAXIMUS consciousness system.

Este módulo implementa raciocínio recursivo de ordem superior,
permitindo que MAXIMUS pense sobre seu próprio pensamento.

Components:
-----------
- RecursiveReasoner: Motor de raciocínio recursivo
- ContradictionDetector: Detecção de inconsistências lógicas
- MetaMonitor: Monitoramento metacognitivo
- IntrospectionEngine: Geração de relatórios em primeira pessoa

Baseline Científico:
-------------------
- Carruthers (2009): Higher-Order Thoughts
- Hofstadter (1979): Strange Loops
- Fleming & Lau (2014): Metacognitive sensitivity

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
Status: DOUTRINA VÉRTICE v2.0 COMPLIANT
"""

from .contradiction_detector import (
    BeliefRevision,
    ContradictionDetector,
    RevisionOutcome,
)
from .introspection_engine import IntrospectionEngine, IntrospectionReport
from .meta_monitor import MetaMonitor, MetaMonitoringReport
from .recursive_reasoner import (
    Belief,
    BeliefGraph,
    BeliefType,
    Contradiction,
    ContradictionType,
    RecursiveReasoner,
    RecursiveReasoningResult,
    ReasoningLevel,
    ReasoningStep,
    Resolution,
    ResolutionStrategy,
)

__all__ = [
    # Core reasoning
    "RecursiveReasoner",
    "RecursiveReasoningResult",
    "ReasoningLevel",
    "ReasoningStep",
    # Belief management
    "Belief",
    "BeliefGraph",
    "Contradiction",
    "Resolution",
    "BeliefType",
    "ContradictionType",
    "ResolutionStrategy",
    # Advanced modules
    "ContradictionDetector",
    "BeliefRevision",
    "RevisionOutcome",
    "MetaMonitor",
    "MetaMonitoringReport",
    "IntrospectionEngine",
    "IntrospectionReport",
]

__version__ = "1.0.0"
