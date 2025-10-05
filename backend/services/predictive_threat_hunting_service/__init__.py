"""FASE 8: Predictive Threat Hunting Service

Attack prediction, vulnerability forecasting, and proactive hunting recommendations.
Bio-inspired anticipatory intelligence for threat prevention.

NO MOCKS - Production-ready predictive algorithms.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .predictive_core import (
    ThreatType,
    ConfidenceLevel,
    ThreatEvent,
    AttackPrediction,
    VulnerabilityForecast,
    HuntingRecommendation,
    AttackPredictor,
    VulnerabilityForecaster,
    ProactiveHunter,
)

__all__ = [
    "ThreatType",
    "ConfidenceLevel",
    "ThreatEvent",
    "AttackPrediction",
    "VulnerabilityForecast",
    "HuntingRecommendation",
    "AttackPredictor",
    "VulnerabilityForecaster",
    "ProactiveHunter",
]
