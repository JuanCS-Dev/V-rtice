"""
Pydantic models for Reactive Fabric Core Service
Data validation and serialization

Sprint 1: Real implementation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


# ============================================================================
# ENUMS
# ============================================================================

class HoneypotType(str, Enum):
    """Types of honeypots."""
    SSH = "ssh"
    WEB = "web"
    API = "api"


class HoneypotStatus(str, Enum):
    """Honeypot operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class AttackSeverity(str, Enum):
    """Attack severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatus(str, Enum):
    """Forensic capture processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================================================
# HONEYPOT MODELS
# ============================================================================

class HoneypotBase(BaseModel):
    """Base honeypot model."""
    honeypot_id: str = Field(..., description="Unique honeypot identifier")
    type: HoneypotType
    container_name: str
    port: int = Field(..., ge=1, le=65535)
    config: Dict[str, Any] = Field(default_factory=dict)


class HoneypotCreate(HoneypotBase):
    """Model for creating a honeypot."""
    pass


class Honeypot(HoneypotBase):
    """Full honeypot model with database fields."""
    id: UUID
    status: HoneypotStatus = HoneypotStatus.OFFLINE
    created_at: datetime
    updated_at: datetime
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class HoneypotStats(BaseModel):
    """Honeypot statistics."""
    honeypot_id: str
    type: HoneypotType
    status: HoneypotStatus
    total_attacks: int = 0
    unique_ips: int = 0
    last_attack: Optional[datetime] = None
    critical_attacks: int = 0
    high_attacks: int = 0


class HoneypotHealthCheck(BaseModel):
    """Honeypot health check result."""
    honeypot_id: str
    status: HoneypotStatus
    uptime_seconds: Optional[int] = None
    container_status: str
    last_check: datetime
    error_message: Optional[str] = None


# ============================================================================
# ATTACK MODELS
# ============================================================================

class AttackBase(BaseModel):
    """Base attack model."""
    attacker_ip: str = Field(..., description="Attacker IP address")
    attack_type: str = Field(..., description="Type of attack")
    severity: AttackSeverity
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    ttps: List[str] = Field(default_factory=list, description="MITRE ATT&CK technique IDs")
    iocs: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="IoCs: {ips: [], domains: [], hashes: [], usernames: []}"
    )
    payload: Optional[str] = Field(None, description="Attack payload (sanitized)")
    captured_at: datetime


class AttackCreate(AttackBase):
    """Model for creating an attack record."""
    honeypot_id: UUID


class Attack(AttackBase):
    """Full attack model with database fields."""
    id: UUID
    honeypot_id: UUID
    processed_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class AttackSummary(BaseModel):
    """Summarized attack for list views."""
    id: UUID
    honeypot_id: str  # honeypot_id string, not UUID
    attacker_ip: str
    attack_type: str
    severity: AttackSeverity
    ttps: List[str]
    captured_at: datetime


# ============================================================================
# TTP MODELS
# ============================================================================

class TTPBase(BaseModel):
    """Base MITRE ATT&CK technique model."""
    technique_id: str = Field(..., description="MITRE technique ID (e.g., T1110)")
    technique_name: str
    tactic: Optional[str] = Field(None, description="MITRE tactic (e.g., Initial Access)")
    description: Optional[str] = None


class TTPCreate(TTPBase):
    """Model for creating a TTP record."""
    pass


class TTP(TTPBase):
    """Full TTP model with database fields."""
    id: UUID
    observed_count: int = 0
    first_observed: datetime
    last_observed: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class TTPFrequency(BaseModel):
    """TTP frequency statistics."""
    technique_id: str
    technique_name: str
    tactic: Optional[str]
    observed_count: int
    last_observed: datetime
    affected_honeypots: int


# ============================================================================
# IOC MODELS
# ============================================================================

class IOCBase(BaseModel):
    """Base IoC model."""
    ioc_type: str = Field(..., description="Type: ip, domain, hash, email, username")
    ioc_value: str
    threat_level: str = Field(default="unknown", description="low, medium, high, critical")


class IOCCreate(IOCBase):
    """Model for creating an IoC record."""
    pass


class IOC(IOCBase):
    """Full IoC model with database fields."""
    id: UUID
    first_seen: datetime
    last_seen: datetime
    occurrences: int = 1
    associated_attacks: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================================================
# FORENSIC CAPTURE MODELS
# ============================================================================

class ForensicCaptureBase(BaseModel):
    """Base forensic capture model."""
    filename: str
    file_path: str
    file_type: str = Field(..., description="cowrie_json, pcap, apache_log")
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = Field(None, description="SHA256 hash")
    captured_at: datetime


class ForensicCaptureCreate(ForensicCaptureBase):
    """Model for creating a forensic capture record."""
    honeypot_id: UUID


class ForensicCapture(ForensicCaptureBase):
    """Full forensic capture model."""
    id: UUID
    honeypot_id: UUID
    processed_at: Optional[datetime] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    attacks_extracted: int = 0
    ttps_extracted: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class HoneypotListResponse(BaseModel):
    """Response for listing honeypots."""
    honeypots: List[HoneypotStats]
    total: int
    online: int
    offline: int


class AttackListResponse(BaseModel):
    """Response for listing attacks."""
    attacks: List[AttackSummary]
    total: int
    limit: int
    offset: int = 0


class TTPListResponse(BaseModel):
    """Response for listing TTPs."""
    ttps: List[TTPFrequency]
    total: int
    limit: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    service: str = "reactive_fabric_core"
    timestamp: datetime
    version: str = "1.0.0"
    database_connected: bool = False
    kafka_connected: bool = False
    redis_connected: bool = False


class MetricsResponse(BaseModel):
    """Prometheus metrics response."""
    metrics: Dict[str, Any]


# ============================================================================
# KAFKA MESSAGE MODELS
# ============================================================================

class ThreatDetectedMessage(BaseModel):
    """Kafka message for reactive_fabric.threat_detected topic."""
    event_id: str = Field(..., description="Unique event ID")
    timestamp: datetime
    honeypot_id: str
    attacker_ip: str
    attack_type: str
    severity: AttackSeverity
    ttps: List[str] = Field(default_factory=list)
    iocs: Dict[str, List[str]] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "rf_attack_12345",
                "timestamp": "2025-10-12T20:30:22Z",
                "honeypot_id": "ssh_001",
                "attacker_ip": "45.142.120.15",
                "attack_type": "brute_force",
                "severity": "medium",
                "ttps": ["T1110", "T1078"],
                "iocs": {
                    "ips": ["45.142.120.15"],
                    "usernames": ["admin", "root"]
                },
                "confidence": 0.95,
                "metadata": {}
            }
        }


class HoneypotStatusMessage(BaseModel):
    """Kafka message for honeypot status updates."""
    honeypot_id: str
    status: HoneypotStatus
    timestamp: datetime
    uptime_seconds: Optional[int] = None
    error_message: Optional[str] = None
