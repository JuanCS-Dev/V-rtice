"""Coagulation Package - Hemostasis-Inspired Containment System

Implements complete coagulation cascade for threat containment:
1. Primary Hemostasis - Reflex Triage Engine (already exists)
2. Secondary Hemostasis - Fibrin Mesh Containment (new)
3. Fibrinolysis - Restoration Engine (new)

Biological Inspiration:
- Platelet plug (RTE) → Fibrin mesh → Controlled dissolution
- Progressive containment from rapid to robust to restoration

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
"""

from .cascade import CoagulationCascadeSystem, CascadePhase, CascadeState
from .fibrin_mesh import (
    FibrinMeshContainment,
    FibrinMeshPolicy,
    FibrinMeshResult,
    FibrinStrength,
)
from .models import (
    ContainmentResult,
    EnrichedThreat,
    NeutralizedThreat,
    ThreatSeverity,
)
from .restoration import (
    RestorationEngine,
    RestorationPhase,
    RestorationPlan,
    RestorationResult,
)

__all__ = [
    # Cascade orchestrator
    "CoagulationCascadeSystem",
    "CascadePhase",
    "CascadeState",
    # Fibrin mesh (secondary hemostasis)
    "FibrinMeshContainment",
    "FibrinMeshPolicy",
    "FibrinMeshResult",
    "FibrinStrength",
    # Restoration (fibrinolysis)
    "RestorationEngine",
    "RestorationPhase",
    "RestorationPlan",
    "RestorationResult",
    # Models
    "ContainmentResult",
    "EnrichedThreat",
    "NeutralizedThreat",
    "ThreatSeverity",
]

__version__ = "1.0.0"
__author__ = "MAXIMUS Defensive Team"
__doc__ = """
Coagulation Cascade System - Biomimetic Threat Containment

Complete hemostasis-inspired containment architecture:

PRIMARY (Reflex Triage Engine):
- Ultra-fast response (< 100ms)
- Pattern matching (Hyperscan)
- Anomaly detection (Isolation Forest)
- Decision: BLOCK / INVESTIGATE / ALLOW

SECONDARY (Fibrin Mesh):
- Robust containment (< 60s)
- Zone isolation
- Traffic shaping
- Dynamic firewall rules

FIBRINOLYSIS (Restoration):
- Progressive restoration
- Health validation
- Rollback capability
- Forensics integration

Usage:
    >>> from coagulation import CoagulationCascadeSystem
    >>> cascade = CoagulationCascadeSystem(...)
    >>> result = await cascade.initiate_cascade(threat)
"""
