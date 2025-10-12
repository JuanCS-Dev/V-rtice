"""Intelligence layer initialization.

This module provides threat intelligence fusion and correlation.

Components:
- ThreatIntelFusionEngine: Multi-source IoC correlation
- AttackGraphBuilder: Attack path prediction
- ThreatIntelConnectors: Source integrations

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
"""

from .fusion_engine import (
    ThreatIntelFusionEngine,
    EnrichedThreat,
    IOC,
    IOCType,
    ThreatActor,
    ThreatIntelSource,
)

__all__ = [
    "ThreatIntelFusionEngine",
    "EnrichedThreat",
    "IOC",
    "IOCType",
    "ThreatActor",
    "ThreatIntelSource",
]
