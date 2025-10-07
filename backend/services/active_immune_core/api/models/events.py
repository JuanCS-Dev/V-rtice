"""Event Models for WebSocket Streaming - PRODUCTION-READY

Pydantic models for real-time event streaming.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CytokineEvent(BaseModel):
    """Cytokine event (Kafka → WebSocket)"""

    event_type: str = Field("cytokine", description="Event type")
    cytokine_type: str = Field(..., description="Cytokine type (IL1, IL6, TNF, etc.)")
    source_agent: str = Field(..., description="Agent that emitted cytokine")
    target_area: Optional[str] = Field(None, description="Target area")
    concentration: float = Field(..., ge=0.0, le=1.0, description="Concentration (0.0-1.0)")
    message: Dict[str, Any] = Field(..., description="Cytokine payload")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "cytokine",
                "cytokine_type": "IL1",
                "source_agent": "macrofago_001",
                "target_area": "subnet_10_0_1_0",
                "concentration": 0.85,
                "message": {
                    "threat_id": "threat_192_168_1_50",
                    "severity": "high",
                },
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class HormoneEvent(BaseModel):
    """Hormone event (Redis → WebSocket)"""

    event_type: str = Field("hormone", description="Event type")
    hormone_type: str = Field(..., description="Hormone type (cortisol, adrenalina, etc.)")
    level: float = Field(..., ge=0.0, le=1.0, description="Hormone level (0.0-1.0)")
    source: str = Field(..., description="Hormone source (lymphnode, controller)")
    message: Dict[str, Any] = Field(..., description="Hormone payload")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "hormone",
                "hormone_type": "cortisol",
                "level": 0.75,
                "source": "homeostatic_controller",
                "message": {
                    "reason": "high_system_load",
                    "action": "suppress_inflammation",
                },
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class AgentStateEvent(BaseModel):
    """Agent state change event"""

    event_type: str = Field("agent_state", description="Event type")
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    old_status: Optional[str] = Field(None, description="Previous status")
    new_status: str = Field(..., description="New status")
    area_patrulha: str = Field(..., description="Patrol area")
    message: Dict[str, Any] = Field(..., description="State change details")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "agent_state",
                "agent_id": "macrofago_001",
                "agent_type": "MACROFAGO",
                "old_status": "patrulhando",
                "new_status": "fagocitando",
                "area_patrulha": "subnet_10_0_1_0",
                "message": {
                    "threat_id": "threat_001",
                    "reason": "detected_malware",
                },
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class ThreatDetectionEvent(BaseModel):
    """Threat detection event"""

    event_type: str = Field("threat_detection", description="Event type")
    threat_id: str = Field(..., description="Threat identifier")
    threat_type: str = Field(..., description="Threat type")
    severity: str = Field(..., description="Severity (low/medium/high/critical)")
    detector_agent: str = Field(..., description="Agent that detected threat")
    target: str = Field(..., description="Threat target")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    details: Dict[str, Any] = Field(..., description="Threat details")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "threat_detection",
                "threat_id": "threat_192_168_1_50",
                "threat_type": "malware",
                "severity": "high",
                "detector_agent": "macrofago_001",
                "target": "192.168.1.50",
                "confidence": 0.92,
                "details": {
                    "hash": "a1b2c3d4...",
                    "behavior": "process_injection",
                },
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class CloneCreationEvent(BaseModel):
    """Clone creation event"""

    event_type: str = Field("clone_creation", description="Event type")
    parent_id: str = Field(..., description="Parent agent ID")
    clone_ids: list[str] = Field(..., description="Created clone IDs")
    num_clones: int = Field(..., description="Number of clones")
    especializacao: str = Field(..., description="Specialization")
    lymphnode_id: str = Field(..., description="Lymphnode that created clones")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "clone_creation",
                "parent_id": "macrofago_001",
                "clone_ids": ["macrofago_clone_001", "macrofago_clone_002"],
                "num_clones": 2,
                "especializacao": "threat_192_168_1_50",
                "lymphnode_id": "lymphnode_regional_001",
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class HomeostaticStateEvent(BaseModel):
    """Homeostatic state change event"""

    event_type: str = Field("homeostatic_state", description="Event type")
    lymphnode_id: str = Field(..., description="Lymphnode identifier")
    old_state: Optional[str] = Field(None, description="Previous state")
    new_state: str = Field(..., description="New homeostatic state")
    temperatura_regional: float = Field(..., description="Regional temperature")
    recommended_action: str = Field(..., description="Recommended action")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "homeostatic_state",
                "lymphnode_id": "lymphnode_regional_001",
                "old_state": "VIGILÂNCIA",
                "new_state": "ATIVAÇÃO",
                "temperatura_regional": 38.2,
                "recommended_action": "Increase agent count and activate clonal expansion",
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class SystemHealthEvent(BaseModel):
    """System health event"""

    event_type: str = Field("system_health", description="Event type")
    health_status: str = Field(..., description="Health status (healthy/degraded/critical)")
    total_agents: int = Field(..., description="Total agents")
    active_agents: int = Field(..., description="Active agents")
    threats_detected: int = Field(..., description="Threats detected")
    threats_neutralized: int = Field(..., description="Threats neutralized")
    average_temperature: float = Field(..., description="Average system temperature")
    timestamp: str = Field(..., description="Event timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "system_health",
                "health_status": "healthy",
                "total_agents": 50,
                "active_agents": 45,
                "threats_detected": 120,
                "threats_neutralized": 98,
                "average_temperature": 37.5,
                "timestamp": "2025-10-06T10:30:00",
            }
        }


class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper"""

    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Message timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "event": "cytokine",
                "data": {
                    "cytokine_type": "IL1",
                    "source_agent": "macrofago_001",
                },
                "timestamp": "2025-10-06T10:30:00",
            }
        }
