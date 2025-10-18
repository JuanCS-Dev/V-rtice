"""
Reactive Fabric - Data Models Package.

Comprehensive data models for Active Deception and Counter-Intelligence architecture.
Phase 1 Focus: Passive intelligence collection with human-in-the-loop safety.

Model Categories:
- threat: Threat events, indicators, MITRE ATT&CK mapping
- deception: Honeypots, decoy assets, interaction tracking
- intelligence: Reports, TTP patterns, APT attribution
- hitl: Human authorization workflow, decision tracking

Design Principles:
- Type safety: 100% Pydantic validation
- Immutability: Core fields protected from modification
- Auditability: Complete timestamp and provenance tracking
- Extensibility: Metadata fields for future enrichment
- Safety: Built-in Phase 1 constraints and validators

Blueprint Compliance:
All models implement requirements from viability analysis:
- Clear risk communication
- Human authorization gates
- Intelligence quality metrics
- Credibility tracking for deception assets
"""

# Threat models
from .threat import (
    ThreatSeverity,
    ThreatCategory,
    DetectionSource,
    ThreatIndicator,
    MITREMapping,
    ThreatEvent,
    ThreatEventCreate,
    ThreatEventUpdate,
    ThreatEventQuery,
)

# Deception models
from .deception import (
    AssetType,
    AssetInteractionLevel,
    AssetStatus,
    AssetCredibility,
    AssetTelemetry,
    DeceptionAsset,
    DeceptionAssetCreate,
    DeceptionAssetUpdate,
    AssetInteractionEvent,
    AssetHealthCheck,
)

# Intelligence models
from .intelligence import (
    IntelligenceType,
    IntelligenceConfidence,
    IntelligenceSource,
    APTGroup,
    TTPPattern,
    IntelligenceReport,
    IntelligenceReportCreate,
    IntelligenceReportUpdate,
    IntelligenceMetrics,
)

# HITL models
from .hitl import (
    ActionLevel,
    ActionType,
    DecisionStatus,
    DecisionRationale,
    AuthorizationRequest,
    AuthorizationRequestCreate,
    AuthorizationDecision,
    HITLMetrics,
    ApproverProfile,
)

__all__ = [
    # Threat models
    "ThreatSeverity",
    "ThreatCategory",
    "DetectionSource",
    "ThreatIndicator",
    "MITREMapping",
    "ThreatEvent",
    "ThreatEventCreate",
    "ThreatEventUpdate",
    "ThreatEventQuery",
    # Deception models
    "AssetType",
    "AssetInteractionLevel",
    "AssetStatus",
    "AssetCredibility",
    "AssetTelemetry",
    "DeceptionAsset",
    "DeceptionAssetCreate",
    "DeceptionAssetUpdate",
    "AssetInteractionEvent",
    "AssetHealthCheck",
    # Intelligence models
    "IntelligenceType",
    "IntelligenceConfidence",
    "IntelligenceSource",
    "APTGroup",
    "TTPPattern",
    "IntelligenceReport",
    "IntelligenceReportCreate",
    "IntelligenceReportUpdate",
    "IntelligenceMetrics",
    # HITL models
    "ActionLevel",
    "ActionType",
    "DecisionStatus",
    "DecisionRationale",
    "AuthorizationRequest",
    "AuthorizationRequestCreate",
    "AuthorizationDecision",
    "HITLMetrics",
    "ApproverProfile",
]
