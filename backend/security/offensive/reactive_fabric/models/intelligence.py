"""
Reactive Fabric - Intelligence Report Models.

Data models for threat intelligence analysis, APT correlation and TTP tracking.
Core of Phase 1 value delivery: actionable threat intelligence.

Phase 1 Success Metrics: Quality and actionability of intelligence output.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class IntelligenceType(str, Enum):
    """Classification of intelligence report types."""
    TACTICAL = "tactical"            # Immediate IoCs and signatures
    OPERATIONAL = "operational"      # Campaign tracking and TTP patterns
    STRATEGIC = "strategic"          # APT attribution and long-term trends
    INDICATOR = "indicator"          # Pure IoC feeds
    TTP_ANALYSIS = "ttp_analysis"    # Technique/procedure deep dive


class IntelligenceConfidence(str, Enum):
    """
    Confidence level in intelligence assessment.
    
    Aligned with Admiralty Scale and STIX confidence scoring.
    Critical for analyst trust and decision-making.
    """
    CONFIRMED = "confirmed"          # 90-100%: Multiple corroborating sources
    HIGH = "high"                    # 70-89%: Strong supporting evidence
    MEDIUM = "medium"                # 50-69%: Some supporting evidence
    LOW = "low"                      # 30-49%: Limited evidence
    SPECULATIVE = "speculative"      # 0-29%: Hypothesis only


class IntelligenceSource(str, Enum):
    """Source of intelligence information."""
    INTERNAL_TELEMETRY = "internal_telemetry"      # Our honeypots/sensors
    THREAT_FEED = "threat_feed"                    # External threat feeds
    OSINT = "osint"                                # Open source intelligence
    ANALYST_RESEARCH = "analyst_research"          # Human analyst investigation
    ML_CORRELATION = "ml_correlation"              # Automated correlation engine


class APTGroup(BaseModel):
    """
    Advanced Persistent Threat group identification.
    
    Tracks known APT actors and their attribution indicators.
    Critical for strategic intelligence and defense prioritization.
    """
    name: str = Field(..., description="APT group name (e.g., APT28, Lazarus)")
    aliases: List[str] = Field(default_factory=list, description="Known aliases")
    attribution_confidence: IntelligenceConfidence = Field(...)
    origin_country: Optional[str] = Field(None)
    target_sectors: List[str] = Field(default_factory=list)
    known_ttps: List[str] = Field(default_factory=list, description="MITRE technique IDs")
    reference_urls: List[str] = Field(default_factory=list)


class TTPPattern(BaseModel):
    """
    Tactics, Techniques, and Procedures pattern.
    
    Represents observed attacker behavior pattern aligned with MITRE ATT&CK.
    Core intelligence artifact for Phase 1 success validation.
    
    Success Criterion:
    Discovery of novel TTP patterns demonstrates reactive fabric value.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    
    # MITRE ATT&CK mapping
    mitre_tactics: List[str] = Field(..., description="ATT&CK tactic IDs")
    mitre_techniques: List[str] = Field(..., description="ATT&CK technique IDs")
    
    # Behavioral indicators
    behavioral_indicators: List[str] = Field(default_factory=list)
    network_indicators: List[str] = Field(default_factory=list)
    
    # Attribution
    observed_apt_groups: List[str] = Field(default_factory=list)
    
    # Validation
    confidence: IntelligenceConfidence = Field(...)
    first_observed: datetime = Field(default_factory=datetime.utcnow)
    last_observed: datetime = Field(default_factory=datetime.utcnow)
    observation_count: int = Field(default=1, ge=1)
    
    # Detection
    detection_rules: List[str] = Field(default_factory=list, description="Generated detection rule IDs")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class IntelligenceReport(BaseModel):
    """
    Structured threat intelligence report.
    
    Primary output artifact of reactive fabric intelligence pipeline.
    Represents analyzed and contextualized threat information ready
    for security operations consumption.
    
    Design Philosophy:
    - Human-readable executive summary
    - Machine-parseable structured data
    - Actionable recommendations
    - Confidence-weighted conclusions
    
    Phase 1 KPI:
    Report quality and actionability determines fabric success.
    Metrics: Analyst feedback, detection rule generation, threat hunt outcomes.
    """
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    report_number: str = Field(..., description="Human-readable report ID (e.g., INT-2024-001)")
    title: str = Field(..., min_length=1, max_length=200)
    
    # Classification
    intelligence_type: IntelligenceType = Field(...)
    confidence: IntelligenceConfidence = Field(...)
    
    # Content
    executive_summary: str = Field(..., min_length=1, description="Non-technical summary")
    technical_analysis: str = Field(..., min_length=1, description="Detailed technical analysis")
    
    # Threat context
    threat_actor: Optional[APTGroup] = Field(None, description="Attributed threat actor if known")
    ttp_patterns: List[TTPPattern] = Field(default_factory=list)
    
    # Indicators
    indicators_of_compromise: List[str] = Field(default_factory=list)
    behavioral_indicators: List[str] = Field(default_factory=list)
    
    # Intelligence fusion
    related_threat_events: List[UUID] = Field(default_factory=list, description="Source ThreatEvent IDs")
    related_assets: List[UUID] = Field(default_factory=list, description="Deception assets involved")
    sources: List[IntelligenceSource] = Field(..., min_length=1)
    
    # Recommendations
    defensive_recommendations: List[str] = Field(default_factory=list)
    detection_rules: List[Dict[str, Any]] = Field(default_factory=list)
    hunt_hypotheses: List[str] = Field(default_factory=list)
    
    # Timeline
    analysis_period_start: datetime = Field(...)
    analysis_period_end: datetime = Field(...)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="Analyst or system that generated report")
    
    # Distribution
    classification: str = Field(default="internal", description="Distribution classification")
    tags: List[str] = Field(default_factory=list)
    
    # Validation
    peer_reviewed: bool = Field(default=False)
    reviewed_by: Optional[str] = Field(None)
    review_date: Optional[datetime] = Field(None)
    
    # Extensibility
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class IntelligenceReportCreate(BaseModel):
    """DTO for creating intelligence reports."""
    report_number: str
    title: str = Field(..., min_length=1, max_length=200)
    intelligence_type: IntelligenceType
    confidence: IntelligenceConfidence
    executive_summary: str = Field(..., min_length=1)
    technical_analysis: str = Field(..., min_length=1)
    threat_actor: Optional[APTGroup] = None
    ttp_patterns: List[TTPPattern] = Field(default_factory=list)
    indicators_of_compromise: List[str] = Field(default_factory=list)
    behavioral_indicators: List[str] = Field(default_factory=list)
    related_threat_events: List[UUID] = Field(default_factory=list)
    related_assets: List[UUID] = Field(default_factory=list)
    sources: List[IntelligenceSource] = Field(..., min_length=1)
    defensive_recommendations: List[str] = Field(default_factory=list)
    detection_rules: List[Dict[str, Any]] = Field(default_factory=list)
    hunt_hypotheses: List[str] = Field(default_factory=list)
    analysis_period_start: datetime
    analysis_period_end: datetime
    generated_by: str
    classification: str = Field(default="internal")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntelligenceReportUpdate(BaseModel):
    """DTO for updating intelligence reports."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    confidence: Optional[IntelligenceConfidence] = None
    executive_summary: Optional[str] = None
    technical_analysis: Optional[str] = None
    threat_actor: Optional[APTGroup] = None
    ttp_patterns: Optional[List[TTPPattern]] = None
    indicators_of_compromise: Optional[List[str]] = None
    behavioral_indicators: Optional[List[str]] = None
    defensive_recommendations: Optional[List[str]] = None
    detection_rules: Optional[List[Dict[str, Any]]] = None
    hunt_hypotheses: Optional[List[str]] = None
    peer_reviewed: Optional[bool] = None
    reviewed_by: Optional[str] = None
    review_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class IntelligenceMetrics(BaseModel):
    """
    Phase 1 success metrics for intelligence collection.
    
    Quantifies reactive fabric value delivery.
    Used to validate progression to Phase 2 or pivot strategy.
    
    Success Criteria from Viability Analysis:
    - Quality: Reports actionable and accurate
    - Quantity: Sufficient TTP discovery rate
    - Impact: Detection rules deployed, hunts successful
    """
    
    # Collection metrics
    total_threat_events: int = Field(default=0, ge=0)
    unique_source_ips: int = Field(default=0, ge=0)
    unique_apt_groups_observed: int = Field(default=0, ge=0)
    
    # TTP discovery (PRIMARY KPI)
    novel_ttps_discovered: int = Field(default=0, ge=0, description="New ATT&CK techniques observed")
    ttp_patterns_identified: int = Field(default=0, ge=0)
    
    # Intelligence output
    reports_generated: int = Field(default=0, ge=0)
    tactical_reports: int = Field(default=0, ge=0)
    operational_reports: int = Field(default=0, ge=0)
    strategic_reports: int = Field(default=0, ge=0)
    
    # Actionability (PRIMARY KPI)
    detection_rules_created: int = Field(default=0, ge=0)
    hunt_hypotheses_validated: int = Field(default=0, ge=0)
    defensive_measures_implemented: int = Field(default=0, ge=0)
    
    # Quality
    average_confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    peer_review_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Time metrics
    average_analysis_time_hours: float = Field(default=0.0, ge=0.0)
    time_to_detection_rule_hours: float = Field(default=0.0, ge=0.0)
    
    # Asset effectiveness
    active_deception_assets: int = Field(default=0, ge=0)
    assets_with_interactions: int = Field(default=0, ge=0)
    average_asset_credibility: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Measurement period
    period_start: datetime = Field(default_factory=datetime.utcnow)
    period_end: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
