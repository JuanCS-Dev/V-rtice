"""
Reactive Fabric - PostgreSQL Schema Definitions.

SQLAlchemy ORM models for threat intelligence database.
Aligns with Pydantic models but adds database-specific constraints.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Enum as SQLEnum, 
    ForeignKey, Index, CheckConstraint, Text, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from ..models.threat import ThreatSeverity, ThreatCategory, DetectionSource
from ..models.deception import AssetType, AssetInteractionLevel, AssetStatus
from ..models.intelligence import IntelligenceType, IntelligenceConfidence, IntelligenceSource


Base = declarative_base()


class ThreatEventDB(Base):
    """
    Threat event database table.
    
    Stores detected malicious activity with full forensic context.
    Optimized for high-volume ingestion and fast query performance.
    
    Indexes:
    - timestamp DESC: Time-series queries
    - source_ip: Attacker correlation
    - severity + is_analyzed: Analyst workflow
    - source + timestamp: Source system tracking
    """
    __tablename__ = "threat_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Temporal
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=datetime.utcnow)
    
    # Classification
    source = Column(SQLEnum(DetectionSource), nullable=False, index=True)
    severity = Column(SQLEnum(ThreatSeverity), nullable=False, index=True)
    category = Column(SQLEnum(ThreatCategory), nullable=False)
    
    # Description
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Network context
    source_ip = Column(String(45), nullable=False, index=True)  # IPv6 support
    source_port = Column(Integer, nullable=True)
    destination_ip = Column(String(45), nullable=False)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(20), nullable=True)
    
    # Threat intelligence (JSONB for performance)
    indicators = Column(JSONB, nullable=False, default=list)
    mitre_mapping = Column(JSONB, nullable=True)
    
    # Enrichment
    geolocation = Column(JSONB, nullable=True)
    threat_intel_match = Column(JSONB, nullable=True)
    
    # Forensics
    raw_payload = Column(Text, nullable=True)
    parsed_payload = Column(JSONB, nullable=True)
    
    # Analysis tracking
    is_analyzed = Column(Boolean, nullable=False, default=False, index=True)
    analysis_timestamp = Column(DateTime(timezone=True), nullable=True)
    related_events = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    
    # Metadata
    event_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_events_time_severity', 'timestamp', 'severity'),
        Index('idx_threat_events_source_time', 'source', 'timestamp'),
        Index('idx_threat_events_analysis', 'is_analyzed', 'severity'),
        CheckConstraint('source_port >= 1 AND source_port <= 65535', name='ck_source_port_range'),
        CheckConstraint('destination_port >= 1 AND destination_port <= 65535', name='ck_dest_port_range'),
    )
    
    # Relationships
    intelligence_reports = relationship("IntelligenceReportEventLink", back_populates="threat_event")


class DeceptionAssetDB(Base):
    """
    Deception asset database table.
    
    Stores honeypot and decoy configurations with credibility tracking.
    Critical for "Ilha de Sacrifício" operational effectiveness.
    
    Indexes:
    - status + asset_type: Operational queries
    - ip_address: Network correlation
    - credibility_score: Asset effectiveness tracking
    """
    __tablename__ = "deception_assets"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identification
    name = Column(String(100), nullable=False, unique=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    interaction_level = Column(SQLEnum(AssetInteractionLevel), nullable=False)
    status = Column(SQLEnum(AssetStatus), nullable=False, default=AssetStatus.ACTIVE, index=True)
    
    # Network deployment
    ip_address = Column(String(45), nullable=False, index=True, unique=True)
    port = Column(Integer, nullable=False)
    hostname = Column(String(255), nullable=True)
    network_segment = Column(String(100), nullable=False)
    
    # Deception configuration
    service_banner = Column(String(500), nullable=True)
    emulated_os = Column(String(100), nullable=True)
    emulated_software = Column(ARRAY(String), nullable=False, default=list)
    decoy_data_profile = Column(String(200), nullable=True)
    
    # Credibility tracking (denormalized for performance)
    credibility_score = Column(Float, nullable=False, index=True)
    credibility_data = Column(JSONB, nullable=False)  # Full AssetCredibility object
    last_credibility_update = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Telemetry configuration
    telemetry_config = Column(JSONB, nullable=False)  # AssetTelemetry object
    
    # Operational metadata
    deployed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deployed_by = Column(String(100), nullable=False)
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    total_interactions = Column(Integer, nullable=False, default=0)
    unique_attackers = Column(Integer, nullable=False, default=0)
    
    # Intelligence value
    intelligence_events_generated = Column(Integer, nullable=False, default=0)
    ttps_discovered = Column(ARRAY(String), nullable=False, default=list)
    
    # Maintenance
    last_maintenance = Column(DateTime(timezone=True), nullable=True)
    next_maintenance = Column(DateTime(timezone=True), nullable=True)
    maintenance_notes = Column(Text, nullable=True)
    
    # Metadata
    event_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        Index('idx_assets_status_type', 'status', 'asset_type'),
        Index('idx_assets_credibility', 'credibility_score', 'status'),
        CheckConstraint('port >= 1 AND port <= 65535', name='ck_port_range'),
        CheckConstraint('credibility_score >= 0.0 AND credibility_score <= 1.0', name='ck_credibility_range'),
        CheckConstraint('total_interactions >= 0', name='ck_total_interactions'),
        CheckConstraint('unique_attackers >= 0', name='ck_unique_attackers'),
    )
    
    # Relationships
    interactions = relationship("AssetInteractionEventDB", back_populates="asset", cascade="all, delete-orphan")
    intelligence_reports = relationship("IntelligenceReportAssetLink", back_populates="asset")


class AssetInteractionEventDB(Base):
    """
    Asset interaction event database table.
    
    Records every attacker interaction with deception assets.
    Primary intelligence collection stream for Phase 1.
    
    Indexes:
    - asset_id + timestamp: Asset activity timeline
    - source_ip: Attacker behavior tracking
    - timestamp DESC: Real-time monitoring
    """
    __tablename__ = "asset_interaction_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    asset_id = Column(UUID(as_uuid=True), ForeignKey('deception_assets.id', ondelete='CASCADE'), nullable=False, index=True)
    threat_event_id = Column(UUID(as_uuid=True), ForeignKey('threat_events.id'), nullable=True)
    
    # Temporal
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=datetime.utcnow)
    
    # Attacker details
    source_ip = Column(String(45), nullable=False, index=True)
    source_port = Column(Integer, nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)
    command = Column(Text, nullable=True)
    payload = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    
    # Intelligence extraction
    indicators_extracted = Column(ARRAY(String), nullable=False, default=list)
    mitre_technique = Column(String(20), nullable=True)
    
    # Forensics
    raw_log = Column(Text, nullable=True)
    event_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_interactions_asset_time', 'asset_id', 'timestamp'),
        Index('idx_interactions_source_time', 'source_ip', 'timestamp'),
    )
    
    # Relationships
    asset = relationship("DeceptionAssetDB", back_populates="interactions")


class TTPPatternDB(Base):
    """
    TTP pattern database table.
    
    Stores identified attacker behavior patterns aligned with MITRE ATT&CK.
    Core intelligence artifact for Phase 1 success validation.
    """
    __tablename__ = "ttp_patterns"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # MITRE mapping
    mitre_tactics = Column(ARRAY(String), nullable=False)
    mitre_techniques = Column(ARRAY(String), nullable=False, index=True)
    
    # Indicators
    behavioral_indicators = Column(ARRAY(String), nullable=False, default=list)
    network_indicators = Column(ARRAY(String), nullable=False, default=list)
    
    # Attribution
    observed_apt_groups = Column(ARRAY(String), nullable=False, default=list)
    
    # Validation
    confidence = Column(SQLEnum(IntelligenceConfidence), nullable=False)
    first_observed = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_observed = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    observation_count = Column(Integer, nullable=False, default=1)
    
    # Detection
    detection_rules = Column(ARRAY(String), nullable=False, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_ttp_techniques', 'mitre_techniques'),
        Index('idx_ttp_confidence', 'confidence', 'observation_count'),
    )


class IntelligenceReportDB(Base):
    """
    Intelligence report database table.
    
    Stores analyzed threat intelligence reports with full context.
    Primary output artifact of reactive fabric.
    
    Indexes:
    - report_number: Human lookups
    - intelligence_type + confidence: Report classification
    - generated_at DESC: Chronological queries
    """
    __tablename__ = "intelligence_reports"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Identification
    report_number = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False)
    
    # Classification
    intelligence_type = Column(SQLEnum(IntelligenceType), nullable=False, index=True)
    confidence = Column(SQLEnum(IntelligenceConfidence), nullable=False, index=True)
    
    # Content
    executive_summary = Column(Text, nullable=False)
    technical_analysis = Column(Text, nullable=False)
    
    # Threat context
    threat_actor = Column(JSONB, nullable=True)  # APTGroup object
    ttp_patterns = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    
    # Indicators
    indicators_of_compromise = Column(ARRAY(String), nullable=False, default=list)
    behavioral_indicators = Column(ARRAY(String), nullable=False, default=list)
    
    # Intelligence fusion
    sources = Column(ARRAY(SQLEnum(IntelligenceSource)), nullable=False)
    
    # Recommendations
    defensive_recommendations = Column(ARRAY(String), nullable=False, default=list)
    detection_rules = Column(JSONB, nullable=False, default=list)
    hunt_hypotheses = Column(ARRAY(String), nullable=False, default=list)
    
    # Timeline
    analysis_period_start = Column(DateTime(timezone=True), nullable=False)
    analysis_period_end = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    generated_by = Column(String(100), nullable=False)
    
    # Distribution
    classification = Column(String(50), nullable=False, default="internal")
    tags = Column(ARRAY(String), nullable=False, default=list)
    
    # Validation
    peer_reviewed = Column(Boolean, nullable=False, default=False)
    reviewed_by = Column(String(100), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    event_metadata = Column(JSONB, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_reports_type_confidence', 'intelligence_type', 'confidence'),
        Index('idx_reports_generated', 'generated_at'),
    )
    
    # Relationships
    threat_events = relationship("IntelligenceReportEventLink", back_populates="report")
    assets = relationship("IntelligenceReportAssetLink", back_populates="report")


class IntelligenceReportEventLink(Base):
    """
    Many-to-many relationship: Intelligence Reports <-> Threat Events.
    
    Tracks which threat events contributed to which intelligence reports.
    Critical for intelligence provenance and validation.
    """
    __tablename__ = "intelligence_report_events"
    
    report_id = Column(UUID(as_uuid=True), ForeignKey('intelligence_reports.id', ondelete='CASCADE'), primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey('threat_events.id', ondelete='CASCADE'), primary_key=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    report = relationship("IntelligenceReportDB", back_populates="threat_events")
    threat_event = relationship("ThreatEventDB", back_populates="intelligence_reports")


class IntelligenceReportAssetLink(Base):
    """
    Many-to-many relationship: Intelligence Reports <-> Deception Assets.
    
    Tracks which assets contributed to which intelligence reports.
    Enables asset effectiveness measurement.
    """
    __tablename__ = "intelligence_report_assets"
    
    report_id = Column(UUID(as_uuid=True), ForeignKey('intelligence_reports.id', ondelete='CASCADE'), primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('deception_assets.id', ondelete='CASCADE'), primary_key=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    report = relationship("IntelligenceReportDB", back_populates="assets")
    asset = relationship("DeceptionAssetDB", back_populates="intelligence_reports")


class IntelligenceMetricsDB(Base):
    """
    Intelligence metrics database table.
    
    Stores Phase 1 success metrics snapshots.
    Used for progress tracking and Phase 2 go/no-go decision.
    """
    __tablename__ = "intelligence_metrics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Collection metrics
    total_threat_events = Column(Integer, nullable=False, default=0)
    unique_source_ips = Column(Integer, nullable=False, default=0)
    unique_apt_groups_observed = Column(Integer, nullable=False, default=0)
    
    # TTP discovery (PRIMARY KPI)
    novel_ttps_discovered = Column(Integer, nullable=False, default=0)
    ttp_patterns_identified = Column(Integer, nullable=False, default=0)
    
    # Intelligence output
    reports_generated = Column(Integer, nullable=False, default=0)
    tactical_reports = Column(Integer, nullable=False, default=0)
    operational_reports = Column(Integer, nullable=False, default=0)
    strategic_reports = Column(Integer, nullable=False, default=0)
    
    # Actionability (PRIMARY KPI)
    detection_rules_created = Column(Integer, nullable=False, default=0)
    hunt_hypotheses_validated = Column(Integer, nullable=False, default=0)
    defensive_measures_implemented = Column(Integer, nullable=False, default=0)
    
    # Quality
    average_confidence_score = Column(Float, nullable=False, default=0.0)
    peer_review_rate = Column(Float, nullable=False, default=0.0)
    
    # Time metrics
    average_analysis_time_hours = Column(Float, nullable=False, default=0.0)
    time_to_detection_rule_hours = Column(Float, nullable=False, default=0.0)
    
    # Asset effectiveness
    active_deception_assets = Column(Integer, nullable=False, default=0)
    assets_with_interactions = Column(Integer, nullable=False, default=0)
    average_asset_credibility = Column(Float, nullable=False, default=0.0)
    
    # Measurement period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_period', 'period_start', 'period_end'),
    )
