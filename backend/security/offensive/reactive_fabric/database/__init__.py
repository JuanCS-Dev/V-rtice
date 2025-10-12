"""
Reactive Fabric - Database Layer.

Provides PostgreSQL persistence for threat events, deception assets,
and intelligence reports with production-grade repository pattern.
"""

from .repositories.threat_repository import ThreatEventRepository
from .repositories.deception_repository import DeceptionAssetRepository
from .repositories.intelligence_repository import IntelligenceRepository

__all__ = [
    "ThreatEventRepository",
    "DeceptionAssetRepository",
    "IntelligenceRepository",
]
