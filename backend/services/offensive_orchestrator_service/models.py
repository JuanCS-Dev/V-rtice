"""
Data models for Offensive Orchestrator Service.

Defines Pydantic models for API requests/responses and SQLAlchemy models for database persistence.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Text, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# SQLAlchemy Base
Base = declarative_base()


# Enums
class CampaignStatus(str, Enum):
    """Status of offensive campaign."""

    PLANNED = "planned"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class ActionType(str, Enum):
    """Types of offensive actions."""

    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    ANALYSIS = "analysis"


class RiskLevel(str, Enum):
    """Risk level for HOTL decisions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalStatus(str, Enum):
    """HOTL approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# Pydantic Models (API)
class CampaignObjective(BaseModel):
    """Offensive campaign objective."""

    model_config = ConfigDict(from_attributes=True)

    target: str = Field(..., min_length=1, description="Target identifier (domain, IP, application)")
    scope: List[str] = Field(..., description="Scope of engagement (IPs, domains, etc.)")
    objectives: List[str] = Field(..., description="Campaign objectives (e.g., 'test WAF bypass', 'validate controls')")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Campaign constraints (time windows, forbidden actions)")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1=low, 10=critical)")
    created_by: Optional[str] = Field(default=None, description="Operator who created this objective")


class CampaignPlan(BaseModel):
    """Generated campaign plan by orchestrator."""

    model_config = ConfigDict(from_attributes=True)

    campaign_id: UUID
    target: str
    phases: List[Dict[str, Any]] = Field(..., description="Campaign phases (recon, exploit, post-exploit)")
    ttps: List[str] = Field(..., description="MITRE ATT&CK TTPs to use")
    estimated_duration_minutes: int
    risk_assessment: RiskLevel
    success_criteria: List[str]
    created_at: datetime


class HOTLRequest(BaseModel):
    """Request for Human-on-the-Loop approval."""

    model_config = ConfigDict(from_attributes=True)

    request_id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    action_type: ActionType
    description: str = Field(..., description="Human-readable description of action")
    risk_level: RiskLevel
    context: Dict[str, Any] = Field(..., description="Additional context for decision")
    requires_approval: bool = Field(default=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HOTLResponse(BaseModel):
    """Response from HOTL system."""

    model_config = ConfigDict(from_attributes=True)

    request_id: UUID
    status: ApprovalStatus
    approved: bool
    operator: Optional[str] = None
    reasoning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttackMemoryEntry(BaseModel):
    """Entry for attack memory system."""

    model_config = ConfigDict(from_attributes=True)

    entry_id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    action_type: ActionType
    target: str
    technique: str
    success: bool
    result: Dict[str, Any]
    lessons_learned: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# SQLAlchemy Models (Database)
class CampaignDB(Base):
    """Database model for offensive campaigns."""

    __tablename__ = "campaigns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    target = Column(String(255), nullable=False, index=True)
    scope = Column(JSON, nullable=False)
    objectives = Column(JSON, nullable=False)
    constraints = Column(JSON, default={})
    priority = Column(Integer, default=5)

    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.PLANNED, index=True)
    plan = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    created_by = Column(String(100), nullable=True)


class HOTLDecisionDB(Base):
    """Database model for HOTL decisions."""

    __tablename__ = "hotl_decisions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    action_type = Column(SQLEnum(ActionType), nullable=False)
    description = Column(Text, nullable=False)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    context = Column(JSON, nullable=False)

    status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, index=True)
    approved = Column(Boolean, nullable=True)
    operator = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=True)

    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class AttackMemoryDB(Base):
    """Database model for attack memory."""

    __tablename__ = "attack_memory"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    campaign_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    action_type = Column(SQLEnum(ActionType), nullable=False, index=True)
    target = Column(String(255), nullable=False, index=True)
    technique = Column(String(255), nullable=False, index=True)

    success = Column(Boolean, nullable=False, index=True)
    result = Column(JSON, nullable=False)
    lessons_learned = Column(Text, nullable=True)

    vector_id = Column(String(100), nullable=True)  # Qdrant vector ID
    embedding = Column(JSON, nullable=True)  # Cached embedding

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# Response models
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
