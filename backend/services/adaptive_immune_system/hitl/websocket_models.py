"""
WebSocket Models - Pydantic models for WebSocket messages.

Defines message types for real-time updates to HITL Console.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WebSocketMessageType(str, Enum):
    """Types of WebSocket messages."""

    # Client → Server
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Server → Client
    PONG = "pong"
    NEW_APV = "new_apv"
    DECISION_MADE = "decision_made"
    STATS_UPDATE = "stats_update"
    CONNECTION_ACK = "connection_ack"
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure."""

    type: WebSocketMessageType = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Message payload")


class SubscribeMessage(BaseModel):
    """Subscribe to updates message."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.SUBSCRIBE)
    channels: list[str] = Field(..., description="Channels to subscribe to (e.g., ['apvs', 'decisions'])")


class UnsubscribeMessage(BaseModel):
    """Unsubscribe from updates message."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.UNSUBSCRIBE)
    channels: list[str] = Field(..., description="Channels to unsubscribe from")


class NewAPVNotification(BaseModel):
    """Notification of new APV added to review queue."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.NEW_APV)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    apv_id: str = Field(..., description="APV ID")
    apv_code: str = Field(..., description="APV code (e.g., APV-TEST-001)")
    severity: str = Field(..., description="Severity level")
    cve_id: str = Field(..., description="CVE ID")
    package_name: str = Field(..., description="Package name")


class DecisionNotification(BaseModel):
    """Notification of decision made on APV."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.DECISION_MADE)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decision_id: str = Field(..., description="Decision ID")
    apv_id: str = Field(..., description="APV ID")
    apv_code: str = Field(..., description="APV code")
    decision: str = Field(..., description="Decision type (approve/reject/modify/escalate)")
    reviewer_name: str = Field(..., description="Reviewer name")
    action_taken: str = Field(..., description="Action taken (pr_merged/pr_closed/etc)")


class StatsUpdateNotification(BaseModel):
    """Notification of stats update."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.STATS_UPDATE)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    pending_reviews: int = Field(..., description="Number of pending reviews")
    total_decisions: int = Field(..., description="Total decisions made")
    decisions_today: int = Field(..., description="Decisions made today")


class ConnectionAckMessage(BaseModel):
    """Connection acknowledgment message."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.CONNECTION_ACK)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    client_id: str = Field(..., description="Unique client ID assigned")
    message: str = Field(default="Connected to HITL WebSocket", description="Welcome message")


class ErrorMessage(BaseModel):
    """Error message."""

    type: WebSocketMessageType = Field(default=WebSocketMessageType.ERROR)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
