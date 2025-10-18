"""Coagulation Models - Data Structures for Containment System

Defines core models for threat containment and response.

Authors: MAXIMUS Team
Date: 2025-10-12
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ThreatSeverity(Enum):
    """Threat severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class QuarantineLevel(Enum):
    """Quarantine isolation levels"""

    NONE = 0
    NETWORK = 1  # Network-level isolation
    HOST = 2  # Host-level lockdown
    APPLICATION = 3  # Application suspension
    DATA = 4  # Data access revocation


class TrustLevel(Enum):
    """Zone trust levels"""

    UNTRUSTED = 0  # DMZ
    LIMITED = 1  # Application layer
    RESTRICTED = 2  # Data layer
    CRITICAL = 3  # Management layer


@dataclass
class ThreatSource:
    """Source of threat"""

    ip: str
    port: Optional[int] = None
    hostname: Optional[str] = None
    subnet: Optional[str] = None
    geolocation: Optional[Dict[str, str]] = None


@dataclass
class BlastRadius:
    """Estimated blast radius of threat"""

    affected_hosts: List[str] = field(default_factory=list)
    affected_zones: List[str] = field(default_factory=list)
    estimated_spread_rate: float = 0.0  # hosts/second
    max_impact_score: float = 0.0  # 0.0-1.0


@dataclass
class EnrichedThreat:
    """Threat with enriched context from threat intel"""

    threat_id: str
    source: ThreatSource
    severity: ThreatSeverity
    threat_type: str  # malware, intrusion, ddos, exfiltration
    signature: Optional[str] = None
    ttps: List[str] = field(default_factory=list)  # MITRE ATT&CK TTPs
    iocs: Dict[str, Any] = field(default_factory=dict)  # IOCs
    blast_radius: BlastRadius = field(default_factory=BlastRadius)
    targeted_ports: List[int] = field(default_factory=list)
    compromised_credentials: List[str] = field(default_factory=list)
    affected_hosts: List[str] = field(default_factory=list)
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0  # 0.0-1.0
    attribution: Optional[str] = None  # Threat actor


@dataclass
class ContainmentResult:
    """Result of containment operation"""

    status: str  # CONTAINED, FAILED, PARTIAL
    contained_at: datetime = field(default_factory=datetime.utcnow)
    containment_type: str = "unknown"  # primary, secondary
    affected_zones: List[str] = field(default_factory=list)
    isolation_rules: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class NeutralizedThreat:
    """Threat that has been neutralized"""

    threat_id: str
    original_threat: EnrichedThreat
    neutralization_method: str
    neutralized_at: datetime = field(default_factory=datetime.utcnow)
    artifacts_collected: List[str] = field(default_factory=list)
    forensics_required: bool = True


@dataclass
class Asset:
    """System asset (host, service, data store)"""

    id: str
    asset_type: str  # host, service, database, storage
    ip: Optional[str] = None
    hostname: Optional[str] = None
    zone: str = "unknown"
    criticality: int = 1  # 1-5, 5=most critical
    business_impact: float = 0.0  # 0.0-1.0
    services: List[str] = field(default_factory=list)
    data_stores: List[str] = field(default_factory=list)
    applications: List[str] = field(default_factory=list)


@dataclass
class HealthCheck:
    """Health check result"""

    check_name: str
    passed: bool
    details: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealthStatus:
    """Overall health status of asset"""

    asset: Asset
    healthy: bool
    checks: List[HealthCheck]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unhealthy_reason: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of threat neutralization validation"""

    safe_to_restore: bool
    checks: Dict[str, bool]
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RestoreResult:
    """Result of asset restoration"""

    asset: Asset
    status: str  # RESTORED, FAILED, ROLLBACK
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None


@dataclass
class FibrinMeshHealth:
    """Health status of active fibrin mesh"""

    mesh_id: str
    effectiveness: float  # 0.0-1.0
    zone_health: Dict[str, Any]
    traffic_health: Dict[str, Any]
    status: str  # HEALTHY, DEGRADED, FAILED


# Exception classes
class CoagulationError(Exception):
    """Base exception for coagulation system"""

    pass


class FibrinMeshDeploymentError(CoagulationError):
    """Fibrin mesh deployment failed"""

    pass


class RestorationError(CoagulationError):
    """Restoration failed"""

    pass


class CascadeError(CoagulationError):
    """Cascade orchestration failed"""

    pass


class ValidationError(CoagulationError):
    """Validation failed"""

    pass
