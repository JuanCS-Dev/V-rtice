"""HCL Knowledge Base Service - Data Models.

This module defines the data models for the HCL Knowledge Base, including:
1.  SQLAlchemy ORM models for mapping data to the PostgreSQL/TimescaleDB database.
2.  Pydantic models for API request and response validation.

These models cover HCL decisions, system metrics, and ML model versioning.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    TIMESTAMP, Index, BigInteger, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()

# ============================================================================
# SQLAlchemy ORM Models
# ============================================================================

class HCLDecision(Base):
    """SQLAlchemy model for storing HCL autonomous decisions.

    This table records every decision made by the HCL Planner, including the
    trigger, the actions taken, and the state of the system before and after.
    """
    __tablename__ = 'hcl_decisions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)
    trigger_type = Column(String, nullable=False, index=True)
    actions_taken = Column(JSONB, nullable=False)
    state_before = Column(JSONB, nullable=False)
    state_after = Column(JSONB)
    outcome = Column(String, index=True)
    reward_signal = Column(Float)

class SystemMetric(Base):
    """SQLAlchemy model for storing time-series system metrics.

    This is a TimescaleDB hypertable, optimized for time-series data. It stores
    all telemetry collected by the HCL Monitor.
    """
    __tablename__ = 'system_metrics'
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, primary_key=True)
    service_name = Column(String, nullable=False, primary_key=True)
    metric_name = Column(String, nullable=False, primary_key=True)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSONB)

class HCLModelVersion(Base):
    """SQLAlchemy model for tracking ML model versions."""
    __tablename__ = 'hcl_model_versions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    trained_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    metrics = Column(JSONB, nullable=False)
    model_path = Column(String, nullable=False)
    deployed = Column(Boolean, default=False, index=True)

# ============================================================================
# Pydantic API Schemas
# ============================================================================

class SystemState(BaseModel):
    """Pydantic model representing a snapshot of the system's state."""
    cpu_usage: float
    memory_usage: float
    network_latency_p99: float

class Action(BaseModel):
    """Pydantic model for a single action taken by the HCL Executor."""
    service: str
    action: str
    success: bool

class DecisionCreate(BaseModel):
    """Pydantic model for creating a new HCL decision record."""
    trigger_type: str
    trigger_details: Dict[str, Any]
    operational_mode: str
    actions_taken: List[Action]
    state_before: SystemState
    planner_used: str

class DecisionUpdate(BaseModel):
    """Pydantic model for updating a decision with its outcome."""
    state_after: SystemState
    outcome: str
    reward_signal: Optional[float] = None

class DecisionResponse(BaseModel):
    """Pydantic response model for an HCL decision."""
    id: uuid.UUID
    timestamp: datetime
    operational_mode: str
    outcome: Optional[str]

    class Config:
        from_attributes = True

class MetricCreate(BaseModel):
    """Pydantic model for creating a new system metric record."""
    service_name: str
    metric_name: str
    metric_value: float
    tags: Optional[Dict[str, Any]] = None

class ModelVersionCreate(BaseModel):
    """Pydantic model for registering a new ML model version."""
    model_name: str
    version: int
    metrics: Dict[str, float]
    model_path: str

class ModelVersionResponse(BaseModel):
    """Pydantic response model for a model version."""
    id: uuid.UUID
    model_name: str
    version: int
    deployed: bool

    class Config:
        from_attributes = True