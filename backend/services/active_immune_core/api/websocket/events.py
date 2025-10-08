"""WebSocket Events - PRODUCTION-READY

Event models for WebSocket communication.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WSEventType(str, Enum):
    """WebSocket event types"""

    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

    # Agent events
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_ACTION = "agent_action"

    # Task events
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # Coordination events
    ELECTION_TRIGGERED = "election_triggered"
    LEADER_ELECTED = "leader_elected"
    CONSENSUS_PROPOSED = "consensus_proposed"
    CONSENSUS_DECIDED = "consensus_decided"

    # System events
    HEALTH_CHANGED = "health_changed"
    METRICS_UPDATED = "metrics_updated"
    ALERT_TRIGGERED = "alert_triggered"


class WSEvent(BaseModel):
    """WebSocket event model"""

    event_type: WSEventType = Field(..., description="Type of event")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Event timestamp (ISO format)",
    )
    data: Dict[str, Any] = Field(..., description="Event data payload")
    source: Optional[str] = Field(None, description="Event source identifier")
    room: Optional[str] = Field(None, description="Room/channel identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "agent_created",
                "timestamp": "2025-10-06T14:30:00",
                "data": {
                    "agent_id": "agent_neutrophil_001",
                    "agent_type": "neutrophil",
                    "status": "active",
                },
                "source": "api_server",
                "room": "agents",
            }
        }


class WSMessage(BaseModel):
    """WebSocket message from client"""

    action: str = Field(..., description="Action to perform")
    data: Optional[Dict[str, Any]] = Field(None, description="Action data")
    room: Optional[str] = Field(None, description="Room to join/leave")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "subscribe",
                "data": {"event_types": ["agent_created", "agent_updated"]},
                "room": "agents",
            }
        }


class WSResponse(BaseModel):
    """WebSocket response to client"""

    success: bool = Field(..., description="Whether action succeeded")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Subscribed to agents room",
                "data": {"room": "agents", "event_types": ["agent_created"]},
            }
        }
