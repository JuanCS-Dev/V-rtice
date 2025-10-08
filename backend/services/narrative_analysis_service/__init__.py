"""FASE 8: Advanced Narrative Analysis Service

Social media narrative analysis, bot detection, propaganda attribution, and meme tracking.
Bio-inspired pattern recognition for information warfare.

NO MOCKS - Production-ready narrative intelligence.
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Team"

from .narrative_core import (
    AttributionResult,
    BotDetector,
    BotScore,
    MemeLineage,
    MemeTracker,
    NarrativeEntity,
    PropagandaAttributor,
    SocialGraphAnalyzer,
)

__all__ = [
    "NarrativeEntity",
    "SocialGraphAnalyzer",
    "BotDetector",
    "BotScore",
    "PropagandaAttributor",
    "AttributionResult",
    "MemeTracker",
    "MemeLineage",
]
