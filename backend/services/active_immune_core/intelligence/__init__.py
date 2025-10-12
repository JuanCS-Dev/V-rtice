"""Intelligence layer initialization.

This module provides threat intelligence fusion and correlation.

Components:
- ThreatIntelFusionEngine: Multi-source IoC correlation
- AttackGraphBuilder: Attack path prediction
- ThreatIntelConnectors: Source integrations
- SOCAIAgent: AI-powered SOC analyst with theory of mind

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

from .soc_ai_agent import (
    SOCAIAgent,
    ThreatAssessment,
    SecurityEvent,
    AttackIntent,
    NextStepPrediction,
    SOCAIAgentError,
)

__all__ = [
    # Fusion Engine
    "ThreatIntelFusionEngine",
    "EnrichedThreat",
    "IOC",
    "IOCType",
    "ThreatActor",
    "ThreatIntelSource",
    # SOC AI Agent
    "SOCAIAgent",
    "ThreatAssessment",
    "SecurityEvent",
    "AttackIntent",
    "NextStepPrediction",
    "SOCAIAgentError",
]
