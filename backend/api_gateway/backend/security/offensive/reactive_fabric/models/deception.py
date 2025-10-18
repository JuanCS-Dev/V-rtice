"""
Reactive Fabric - Deception Asset Models.

Data models for managing honeypots, decoy systems and deception infrastructure.
Supports "Ilha de Sacrifício" (Sacrifice Island) pattern for attacker engagement.

Phase 1 Focus: Asset credibility and telemetry collection.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class AssetType(str, Enum):
    """
    Deception asset type classification.
    
    Each type serves specific attacker engagement objectives.
    Phase 1: Focus on low-interaction honeypots for safe telemetry.
    """
    HONEYPOT_SSH = "honeypot_ssh"
    HONEYPOT_HTTP = "honeypot_http"
    HONEYPOT_SMB = "honeypot_smb"
    HONEYPOT_DATABASE = "honeypot_database"
    HONEYPOT_ICS = "honeypot_ics"
    DECOY_FILE = "decoy_file"
    DECOY_CREDENTIAL = "decoy_credential"
    DECOY_NETWORK = "decoy_network"
    CANARY_TOKEN = "canary_token"


class AssetInteractionLevel(str, Enum):
    """
    Honeypot interaction level per research classification.
    
    LOW: Emulated services, no actual code execution
    MEDIUM: Limited real services in isolated environment
    HIGH: Full system functionality (PHASE 1 PROHIBITED)
    
    Phase 1 Constraint: Only LOW interaction permitted for safety.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssetStatus(str, Enum):
    """Asset operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    COMPROMISED = "compromised"
    RETIRED = "retired"


class AssetCredibility(BaseModel):
    """
    Deception asset credibility metrics.
    
    Addresses "Paradox of Realism" from viability analysis.
    Tracks how convincing the asset appears to attackers.
    
    Critical Success Factor:
    High credibility = High-quality intelligence
    Low credibility = Asset abandonment by attackers
    """
    realism_score: float = Field(..., ge=0.0, le=1.0, description="Overall realism 0-1")
    service_authenticity: float = Field(..., ge=0.0, le=1.0, description="Service behavior realism")
    data_authenticity: float = Field(..., ge=0.0, le=1.0, description="Hosted data credibility")
    network_integration: float = Field(..., ge=0.0, le=1.0, description="Network topology integration")
    last_assessment: datetime = Field(default_factory=datetime.utcnow)
    assessment_method: str = Field(..., description="How credibility was measured")
    notes: Optional[str] = Field(None, description="Credibility assessment notes")


class AssetTelemetry(BaseModel):
    """
    Telemetry collection configuration for deception asset.
    
    Defines what data gets captured during attacker interaction.
    Phase 1 Core: Maximum observability, zero response.
    """
    capture_network_traffic: bool = Field(default=True)
    capture_commands: bool = Field(default=True)
    capture_file_operations: bool = Field(default=True)
    capture_screenshots: bool = Field(default=False)
    capture_keystrokes: bool = Field(default=False)
    log_retention_days: int = Field(default=90, ge=1, le=365)
    storage_location: str = Field(..., description="Telemetry storage path/bucket")


class DeceptionAsset(BaseModel):
    """
    Core deception asset model.
    
    Represents a single honeypot, decoy or canary token in the
    reactive fabric. Central to "Ilha de Sacrifício" strategy.
    
    Design Philosophy:
    - Asset exists solely to attract and observe attackers
    - Never contains real production data
    - All interactions are suspicious by definition
    - Credibility maintenance is continuous operation
    
    Phase 1 Constraints:
    - interaction_level = LOW only
    - No automated responses to interactions
    - Human review required for any asset modification
    
    Validation Requirement:
    Every asset must justify its existence in threat intelligence
    collection. Non-productive assets get retired.
    """
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100, description="Asset identifier")
    asset_type: AssetType = Field(...)
    interaction_level: AssetInteractionLevel = Field(...)
    status: AssetStatus = Field(default=AssetStatus.ACTIVE)
    
    # Deployment details
    ip_address: str = Field(..., description="Asset IP address")
    port: int = Field(..., ge=1, le=65535, description="Service port")
    hostname: Optional[str] = Field(None, description="Hostname if applicable")
    network_segment: str = Field(..., description="Network segment/VLAN")
    
    # Deception configuration
    service_banner: Optional[str] = Field(None, description="Service identification banner")
    emulated_os: Optional[str] = Field(None, description="Operating system persona")
    emulated_software: Optional[List[str]] = Field(default_factory=list, description="Installed software list")
    decoy_data_profile: Optional[str] = Field(None, description="Type of decoy data hosted")
    
    # Credibility tracking
    credibility: AssetCredibility = Field(...)
    last_credibility_update: datetime = Field(default_factory=datetime.utcnow)
    
    # Telemetry configuration
    telemetry: AssetTelemetry = Field(...)
    
    # Operational metadata
    deployed_at: datetime = Field(default_factory=datetime.utcnow)
    deployed_by: str = Field(..., description="User/system that deployed asset")
    last_interaction: Optional[datetime] = Field(None, description="Last attacker interaction")
    total_interactions: int = Field(default=0, ge=0)
    unique_attackers: int = Field(default=0, ge=0)
    
    # Intelligence value tracking
    intelligence_events_generated: int = Field(default=0, ge=0)
    ttps_discovered: List[str] = Field(default_factory=list, description="MITRE technique IDs observed")
    
    # Maintenance tracking
    last_maintenance: Optional[datetime] = Field(None)
    next_maintenance: Optional[datetime] = Field(None)
    maintenance_notes: Optional[str] = Field(None)
    
    # Extensibility
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('interaction_level')
    def validate_phase1_constraint(cls, v: AssetInteractionLevel) -> AssetInteractionLevel:
        """
        Enforce Phase 1 constraint: LOW interaction only.
        
        HIGH interaction assets pose containment risks.
        This validator prevents accidental deployment of dangerous assets.
        
        Note: Can be removed when transitioning to Phase 2 with proper safeguards.
        """
        if v == AssetInteractionLevel.HIGH:
            raise ValueError(
                "HIGH interaction assets prohibited in Phase 1. "
                "Risk: Containment failure and attacker pivot to production. "
                "Recommendation: Use LOW or MEDIUM interaction only."
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
        use_enum_values = True


class DeceptionAssetCreate(BaseModel):
    """DTO for creating new deception assets."""
    name: str = Field(..., min_length=1, max_length=100)
    asset_type: AssetType
    interaction_level: AssetInteractionLevel
    ip_address: str
    port: int = Field(..., ge=1, le=65535)
    hostname: Optional[str] = None
    network_segment: str
    service_banner: Optional[str] = None
    emulated_os: Optional[str] = None
    emulated_software: Optional[List[str]] = Field(default_factory=list)
    decoy_data_profile: Optional[str] = None
    credibility: AssetCredibility
    telemetry: AssetTelemetry
    deployed_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeceptionAssetUpdate(BaseModel):
    """DTO for updating deception assets."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[AssetStatus] = None
    service_banner: Optional[str] = None
    emulated_software: Optional[List[str]] = None
    credibility: Optional[AssetCredibility] = None
    telemetry: Optional[AssetTelemetry] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    maintenance_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetInteractionEvent(BaseModel):
    """
    Record of attacker interaction with deception asset.
    
    Every connection, command, or action against asset generates event.
    Forms primary intelligence collection stream for Phase 1.
    """
    id: UUID = Field(default_factory=uuid4)
    asset_id: UUID = Field(..., description="Deception asset that was interacted with")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Attacker details
    source_ip: str = Field(...)
    source_port: Optional[int] = Field(None, ge=1, le=65535)
    session_id: Optional[str] = Field(None, description="Session identifier if applicable")
    
    # Interaction details
    interaction_type: str = Field(..., description="Type of interaction: connection, command, file_access")
    command: Optional[str] = Field(None, description="Command executed if applicable")
    payload: Optional[str] = Field(None, description="Request payload")
    response: Optional[str] = Field(None, description="Asset response")
    
    # Intelligence extraction
    indicators_extracted: List[str] = Field(default_factory=list)
    mitre_technique: Optional[str] = Field(None)
    
    # Linked threat event
    threat_event_id: Optional[UUID] = Field(None, description="Associated ThreatEvent ID")
    
    # Forensics
    raw_log: Optional[str] = Field(None)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class AssetHealthCheck(BaseModel):
    """
    Health check result for deception asset.
    
    Validates asset is operational and credible.
    Critical for maintaining "Paradox of Realism" effectiveness.
    """
    asset_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_healthy: bool
    is_reachable: bool
    service_responding: bool
    credibility_maintained: bool
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }
