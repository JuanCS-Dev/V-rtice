"""FASE 9: Adaptive Immunity Service

Antibody diversification and affinity maturation for adaptive threat detection.
Bio-inspired adaptive learning through clonal selection.

NO MOCKS - Production-ready adaptive immunity.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .adaptive_core import (
    AntibodyType,
    ThreatSample,
    Antibody,
    ClonalExpansion,
    AffinityMaturationEvent,
    AntibodyGenerator,
    AffinityMaturationEngine,
    ClonalSelectionManager,
    AdaptiveImmunityController,
)

__all__ = [
    "AntibodyType",
    "ThreatSample",
    "Antibody",
    "ClonalExpansion",
    "AffinityMaturationEvent",
    "AntibodyGenerator",
    "AffinityMaturationEngine",
    "ClonalSelectionManager",
    "AdaptiveImmunityController",
]
