"""
Intelligence Layer - Threat Intel Processing & Narrative Analysis

This module contains advanced threat intelligence processing components:
- Narrative Filter: Hype detection & weaponization scoring
- Contextual Severity: Environment-aware CVSS adjustment
- APV Enrichment: Enhanced threat metadata generation
"""

from .narrative_filter import (
    NarrativeFilter,
    NarrativePattern,
    analyze_narrative,
    is_hype
)

__all__ = [
    "NarrativeFilter",
    "NarrativePattern",
    "analyze_narrative",
    "is_hype"
]
