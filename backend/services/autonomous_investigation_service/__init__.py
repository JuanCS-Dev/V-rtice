"""FASE 8: Autonomous Investigation Service

Threat actor profiling, campaign correlation, and automated investigations.
Bio-inspired investigative intelligence for attribution and incident response.

NO MOCKS - Production-ready investigation algorithms.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .investigation_core import (
    TTP,
    InvestigationStatus,
    ThreatActorProfile,
    SecurityIncident,
    Campaign,
    Investigation,
    ThreatActorProfiler,
    CampaignCorrelator,
    AutonomousInvestigator,
)

__all__ = [
    "TTP",
    "InvestigationStatus",
    "ThreatActorProfile",
    "SecurityIncident",
    "Campaign",
    "Investigation",
    "ThreatActorProfiler",
    "CampaignCorrelator",
    "AutonomousInvestigator",
]
