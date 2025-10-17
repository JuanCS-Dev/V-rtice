"""Data models for Verdict Engine Service.

This module defines Pydantic models for verdicts, WebSocket messages,
and API responses. All models are 100% type-safe and validated.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# Enums as Literals for type safety
SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
StatusType = Literal["ACTIVE", "MITIGATED", "DISMISSED", "ESCALATED"]
VerdictStatus = StatusType  # Alias for backward compatibility
CategoryType = Literal[
    "ALLIANCE",
    "DECEPTION",
    "THREAT",
    "INCONSISTENCY",
    "COLLUSION",
    "ANOMALY",
]


class VerdictBase(BaseModel):
    """Base verdict model with core fields."""

    id: UUID
    timestamp: datetime
    category: CategoryType
    severity: SeverityLevel
    title: str
    agents_involved: list[str]
    target: str | None = None
    evidence_chain: list[str]
    confidence: Decimal = Field(ge=0, le=1)
    recommended_action: str
    status: VerdictStatus = "ACTIVE"
    mitigation_command_id: UUID | None = None
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("confidence", mode="before")
    @classmethod
    def validate_confidence(cls, v: Decimal | float) -> Decimal:
        """Ensure confidence is Decimal with 2 decimals."""
        if isinstance(v, float):
            return Decimal(str(round(v, 2)))
        return v

    model_config = {"from_attributes": True}


class Verdict(VerdictBase):
    """Full verdict model with metadata."""

    created_at: datetime


class VerdictSummary(BaseModel):
    """Lightweight verdict summary for lists."""

    id: UUID
    timestamp: datetime
    category: CategoryType
    severity: SeverityLevel
    title: str
    status: VerdictStatus
    color: str
    agents_count: int


class VerdictFilter(BaseModel):
    """Query filters for verdict listing."""

    status: VerdictStatus | None = None
    severity: SeverityLevel | None = None
    category: CategoryType | None = None
    agent_id: str | None = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class VerdictStats(BaseModel):
    """Aggregated verdict statistics."""

    total_count: int
    by_severity: dict[SeverityLevel, int]
    by_status: dict[VerdictStatus, int]
    by_category: dict[CategoryType, int]
    critical_active: int
    last_updated: datetime


class WebSocketMessage(BaseModel):
    """WebSocket message format for real-time streaming."""

    type: Literal["verdict", "stats", "ping", "error"]
    data: Verdict | VerdictStats | dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "degraded", "unhealthy"]
    service: str = "verdict_engine"
    version: str = "1.0.0"
    dependencies: dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
