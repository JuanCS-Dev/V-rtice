"""
Unified Event Schemas - Vértice Ecosystem

Standardized event schemas for inter-service communication.
All events inherit from EventBase for consistency.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EventPriority(str, Enum):
    """Event priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class EventSource(str, Enum):
    """Event source services"""
    REACTIVE_FABRIC = "reactive_fabric_core"
    IMMUNE_SYSTEM = "active_immune_core"
    ADAPTIVE_IMMUNE = "adaptive_immune_system"
    MAXIMUS_CORE = "maximus_core_service"
    API_GATEWAY = "api_gateway"
    MONITORING = "monitoring"


class SeverityLevel(str, Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventBase(BaseModel):
    """
    Base event schema for all ecosystem events.

    All events must inherit from this base class to ensure
    consistency and traceability.
    """
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(..., description="Event type identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_service: EventSource = Field(..., description="Service that generated event")
    priority: EventPriority = Field(default=EventPriority.NORMAL)
    correlation_id: str | None = Field(None, description="For event chain tracing")
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# ============================================================================
# REACTIVE FABRIC EVENTS
# ============================================================================

class ThreatDetectionEvent(EventBase):
    """
    Threat detected by Reactive Fabric honeypot.

    Published to: maximus.threats.detected
    Consumed by: Active Immune Core, SIEM, Analytics
    """
    event_type: str = "threat.detected"
    source_service: EventSource = EventSource.REACTIVE_FABRIC

    # Threat details
    honeypot_id: str = Field(..., description="Honeypot that detected threat")
    honeypot_type: str = Field(..., description="Type of honeypot (ssh, http, etc)")
    attacker_ip: str = Field(..., description="Attacker IP address")
    attacker_port: int | None = None
    attack_type: str = Field(..., description="Type of attack")
    severity: SeverityLevel = Field(..., description="Threat severity")

    # Threat intelligence
    ttps: list[str] = Field(default_factory=list, description="MITRE ATT&CK TTPs")
    iocs: dict[str, list[str]] = Field(
        default_factory=dict,
        description="IoCs: {ips: [], domains: [], hashes: [], etc}"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    # Context
    attack_payload: str | None = None
    attack_commands: list[str] | None = None
    session_duration: float | None = None


class HoneypotStatusEvent(EventBase):
    """
    Honeypot status change event.

    Published to: maximus.honeypots.status
    Consumed by: Monitoring, Reactive Fabric orchestrator
    """
    event_type: str = "honeypot.status_change"
    source_service: EventSource = EventSource.REACTIVE_FABRIC

    honeypot_id: str
    honeypot_type: str
    status: str = Field(..., description="online, offline, degraded")
    previous_status: str | None = None
    uptime_seconds: int | None = None
    error_message: str | None = None
    health_metrics: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# IMMUNE SYSTEM EVENTS
# ============================================================================

class ImmuneResponseEvent(EventBase):
    """
    Immune system response to threat.

    Published to: maximus.immune.responses
    Consumed by: Reactive Fabric, Monitoring, Analytics
    """
    event_type: str = "immune.response"
    source_service: EventSource = EventSource.IMMUNE_SYSTEM

    threat_id: str = Field(..., description="Original threat event ID")
    responder_agent_id: str = Field(..., description="Agent that responded")
    responder_agent_type: str = Field(..., description="nk_cell, neutrophil, etc")

    response_action: str = Field(..., description="isolate, neutralize, observe")
    response_status: str = Field(..., description="success, failed, partial")
    response_time_ms: float = Field(..., description="Response latency")

    target: str = Field(..., description="What was targeted")
    details: dict[str, Any] = Field(default_factory=dict)


class ClonalExpansionEvent(EventBase):
    """
    Clonal expansion event (adaptive immune response).

    Published to: maximus.immune.cloning
    Consumed by: Monitoring, Analytics, Homeostatic controller
    """
    event_type: str = "immune.clonal_expansion"
    source_service: EventSource = EventSource.IMMUNE_SYSTEM

    parent_agent_id: str
    clone_ids: list[str] = Field(..., description="IDs of created clones")
    num_clones: int
    especializacao: str = Field(..., description="Threat signature specialization")
    trigger_threat_id: str = Field(..., description="Threat that triggered expansion")
    lymphnode_id: str


class HomeostaticStateEvent(EventBase):
    """
    Homeostatic state change event.

    Published to: maximus.immune.homeostasis
    Consumed by: All immune components, Monitoring
    """
    event_type: str = "immune.homeostatic_change"
    source_service: EventSource = EventSource.IMMUNE_SYSTEM

    lymphnode_id: str
    area: str = Field(..., description="Regional area")

    old_state: str | None = None
    new_state: str = Field(..., description="repouso, vigilancia, atencao, inflamacao")

    temperatura_regional: float = Field(..., description="Regional temperature (36.0-42.0)")
    threat_density: float = Field(..., description="Threats per time unit")
    recommended_action: str

    metrics: dict[str, Any] = Field(default_factory=dict)

    @field_validator("temperatura_regional")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not (30.0 <= v <= 45.0):
            raise ValueError("Temperature must be between 30.0 and 45.0")
        return v


class SystemHealthEvent(EventBase):
    """
    System-wide health metrics.

    Published to: maximus.system.health
    Consumed by: Monitoring, Grafana, Alert manager
    """
    event_type: str = "system.health"
    source_service: EventSource = Field(..., description="Service reporting health")

    health_status: str = Field(..., description="healthy, degraded, critical")

    # Metrics
    total_agents: int | None = None
    active_agents: int | None = None
    threats_detected_total: int | None = None
    threats_neutralized_total: int | None = None
    average_temperature: float | None = None

    # Components
    components: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-component health metrics"
    )

    alerts: list[str] = Field(default_factory=list)


# ============================================================================
# INTEGRATION EVENTS
# ============================================================================

class IntegrationEvent(EventBase):
    """
    Cross-system integration event.

    Published to: maximus.integration.*
    Consumed by: Multiple systems
    """
    event_type: str = "integration.event"

    action: str = Field(..., description="Action being performed")
    target_system: str = Field(..., description="Target system")
    payload: dict[str, Any] = Field(default_factory=dict)
    requires_ack: bool = Field(default=False)
