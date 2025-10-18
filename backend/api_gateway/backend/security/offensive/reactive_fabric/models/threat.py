"""
Reactive Fabric - Threat Event Models.

Data models for threat detection, classification and tracking.
Supports intelligence-driven detection aligned with MITRE ATT&CK framework.

Foundational requirement for Phase 1: Passive Intelligence Collection.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ThreatSeverity(str, Enum):
    """
    Threat severity classification aligned with NIST 800-61.
    
    Maps to defensive urgency, NOT offensive response automation.
    Phase 1 constraint: All severities trigger passive collection only.
    """
    CRITICAL = "critical"  # Active exploitation, data exfiltration
    HIGH = "high"          # Privilege escalation, lateral movement
    MEDIUM = "medium"      # Reconnaissance, initial access attempts
    LOW = "low"            # Port scans, automated probes
    INFO = "info"          # Benign anomalies, false positives


class ThreatCategory(str, Enum):
    """
    Threat categorization based on MITRE ATT&CK tactics.
    
    Enables TTP (Tactics, Techniques, Procedures) mapping for
    intelligence correlation and APT attribution.
    """
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class DetectionSource(str, Enum):
    """
    Source system that generated the threat detection.
    
    Phase 1 sources: Honeypots, network sensors, deception assets.
    Enables source reliability weighting in intelligence fusion.
    """
    HONEYPOT = "honeypot"
    IDS = "ids"
    IPS = "ips"
    WAF = "waf"
    DECEPTION_ASSET = "deception_asset"
    NETWORK_SENSOR = "network_sensor"
    ENDPOINT_SENSOR = "endpoint_sensor"
    SIEM_CORRELATION = "siem_correlation"
    THREAT_INTELLIGENCE = "threat_intelligence"


class ThreatIndicator(BaseModel):
    """
    Individual Indicator of Compromise (IoC).
    
    Atomic threat indicator extracted from detection event.
    Forms basis for threat intelligence enrichment and correlation.
    """
    type: str = Field(..., description="IoC type: ip, domain, hash, url, email")
    value: str = Field(..., description="Indicator value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    occurrence_count: int = Field(default=1, ge=1)
    
    @validator('type')
    def validate_ioc_type(cls, v: str) -> str:
        """Validate IoC type against known categories."""
        valid_types = {'ip', 'domain', 'hash', 'url', 'email', 'file', 'mutex', 'registry'}
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid IoC type: {v}")
        return v.lower()


class MITREMapping(BaseModel):
    """
    MITRE ATT&CK framework mapping.
    
    Links threat event to specific ATT&CK technique for TTP tracking.
    Critical for APT behavior pattern recognition and attribution.
    """
    tactic_id: str = Field(..., description="ATT&CK Tactic ID (e.g., TA0001)")
    tactic_name: str = Field(..., description="Tactic name (e.g., Initial Access)")
    technique_id: str = Field(..., description="ATT&CK Technique ID (e.g., T1190)")
    technique_name: str = Field(..., description="Technique name (e.g., Exploit Public-Facing Application)")
    sub_technique_id: Optional[str] = Field(None, description="Sub-technique ID if applicable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mapping confidence 0-1")


class ThreatEvent(BaseModel):
    """
    Core threat event model representing detected malicious activity.
    
    Central data structure for Phase 1 intelligence collection.
    Every detection flows through this model before intelligence processing.
    
    Design Philosophy:
    - Immutable core fields (id, timestamp, source)
    - Rich context capture for forensic analysis
    - MITRE ATT&CK alignment for TTP tracking
    - Extensible metadata for future enrichment
    
    Consciousness Alignment:
    While reactive security lacks phenomenological experience, systematic
    threat pattern recognition parallels perceptual binding in biological
    consciousness. TTP correlation creates proto-semantic understanding.
    """
    
    # Core identification
    id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event detection time")
    
    # Source and classification
    source: DetectionSource = Field(..., description="Detection source system")
    severity: ThreatSeverity = Field(..., description="Threat severity level")
    category: ThreatCategory = Field(..., description="MITRE ATT&CK tactic category")
    
    # Threat details
    title: str = Field(..., min_length=1, max_length=200, description="Brief threat description")
    description: str = Field(..., min_length=1, description="Detailed threat narrative")
    
    # Network context
    source_ip: str = Field(..., description="Attacker source IP")
    source_port: Optional[int] = Field(None, ge=1, le=65535, description="Source port if applicable")
    destination_ip: str = Field(..., description="Target destination IP")
    destination_port: Optional[int] = Field(None, ge=1, le=65535, description="Destination port")
    protocol: Optional[str] = Field(None, description="Network protocol: tcp, udp, icmp, http")
    
    # Threat intelligence
    indicators: List[ThreatIndicator] = Field(default_factory=list, description="Extracted IoCs")
    mitre_mapping: Optional[MITREMapping] = Field(None, description="ATT&CK framework mapping")
    
    # Enrichment data
    geolocation: Optional[Dict[str, Any]] = Field(None, description="Source IP geolocation data")
    threat_intel_match: Optional[Dict[str, Any]] = Field(None, description="External threat intel correlation")
    
    # Forensic payload
    raw_payload: Optional[str] = Field(None, description="Base64 encoded raw packet/request")
    parsed_payload: Optional[Dict[str, Any]] = Field(None, description="Structured payload analysis")
    
    # Tracking metadata
    is_analyzed: bool = Field(default=False, description="Intelligence analysis complete flag")
    analysis_timestamp: Optional[datetime] = Field(None, description="Analysis completion time")
    related_events: List[UUID] = Field(default_factory=list, description="Correlated event IDs")
    
    # Extensibility
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        use_enum_values = True


class ThreatEventCreate(BaseModel):
    """
    Data transfer object for creating new threat events.
    
    Minimal required fields for event ingestion from detection sources.
    Additional fields auto-populated by collection service.
    """
    source: DetectionSource
    severity: ThreatSeverity
    category: ThreatCategory
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    source_ip: str
    source_port: Optional[int] = Field(None, ge=1, le=65535)
    destination_ip: str
    destination_port: Optional[int] = Field(None, ge=1, le=65535)
    protocol: Optional[str] = None
    indicators: List[ThreatIndicator] = Field(default_factory=list)
    mitre_mapping: Optional[MITREMapping] = None
    raw_payload: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreatEventUpdate(BaseModel):
    """
    Data transfer object for updating threat events.
    
    Supports intelligence enrichment and analysis state updates.
    All fields optional to allow partial updates.
    """
    severity: Optional[ThreatSeverity] = None
    category: Optional[ThreatCategory] = None
    indicators: Optional[List[ThreatIndicator]] = None
    mitre_mapping: Optional[MITREMapping] = None
    geolocation: Optional[Dict[str, Any]] = None
    threat_intel_match: Optional[Dict[str, Any]] = None
    parsed_payload: Optional[Dict[str, Any]] = None
    is_analyzed: Optional[bool] = None
    analysis_timestamp: Optional[datetime] = None
    related_events: Optional[List[UUID]] = None
    metadata: Optional[Dict[str, Any]] = None


class ThreatEventQuery(BaseModel):
    """
    Query parameters for threat event retrieval and filtering.
    
    Supports intelligence analyst investigations and pattern analysis.
    """
    severity: Optional[List[ThreatSeverity]] = None
    category: Optional[List[ThreatCategory]] = None
    source: Optional[List[DetectionSource]] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_analyzed: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
