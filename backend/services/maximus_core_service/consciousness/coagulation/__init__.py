"""
Coagulation Cascade Module - Biological Response System
========================================================

Implements AI analog of biological coagulation cascade for:
- Threat response amplification
- Memory consolidation (fibrin stabilization)
- Error clustering (platelet aggregation)
- Tolerance regulation (anticoagulant balance)

Biological Foundation:
- Intrinsic Pathway: Internal threat detection
- Extrinsic Pathway: External threat signals
- Common Pathway: Amplification cascade
- Fibrin Formation: Memory consolidation
- Anticoagulants: False positive suppression

Integration:
- MMEI: Triggers cascade on high repair_need
- ESGT: Amplifies response during ignition
- Immune Tools: Memory consolidation endpoint
- MCEA: Regulates tolerance/anticoagulation

Authors:
- Juan Carlos Souza - VERTICE Project
- Claude (Anthropic) - AI Co-Author

Date: October 21, 2025
"""

from .cascade import (
    CoagulationCascade,
    CascadeState,
    CascadePhase,
    ThreatSignal,
    CoagulationResponse,
)

__all__ = [
    "CoagulationCascade",
    "CascadeState",
    "CascadePhase",
    "ThreatSignal",
    "CoagulationResponse",
]
