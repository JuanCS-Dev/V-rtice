"""
HCL Knowledge Base - SQLAlchemy Models
======================================
ORM models for HCL decisions, metrics, and model versions.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text,
    TIMESTAMP, Index, BigInteger, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()

# ============================================================================
# DATABASE MODELS (SQLAlchemy ORM)
# ============================================================================

class HCLDecision(Base):
    """Stores all HCL autonomous decisions with state snapshots"""
    __tablename__ = 'hcl_decisions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)

    # Trigger
    trigger_type = Column(String, nullable=False, index=True)
    trigger_details = Column(JSONB, nullable=False)

    # Operational mode
    operational_mode = Column(String, nullable=False, index=True)
    previous_mode = Column(String)

    # Actions
    actions_taken = Column(JSONB, nullable=False)

    # State snapshots
    state_before = Column(JSONB, nullable=False)
    state_after = Column(JSONB)

    # Outcome
    outcome = Column(String, index=True)  # SUCCESS, PARTIAL, FAILED, PENDING
    outcome_measured_at = Column(TIMESTAMP(timezone=True))

    # Reward for RL
    reward_signal = Column(Float)

    # Human feedback
    human_feedback = Column(Text)
    human_feedback_at = Column(TIMESTAMP(timezone=True))
    analyst_id = Column(String)

    # Metadata
    decision_latency_ms = Column(Integer)
    execution_latency_ms = Column(Integer)
    planner_used = Column(String, index=True)  # fuzzy, rl_agent, manual

    def __repr__(self):
        return f"<HCLDecision {self.id} mode={self.operational_mode} outcome={self.outcome}>"


class SystemMetric(Base):
    """Time-series system metrics"""
    __tablename__ = 'system_metrics'

    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), primary_key=True)
    service_name = Column(String, nullable=False, primary_key=True)
    metric_name = Column(String, nullable=False, primary_key=True)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSONB)

    def __repr__(self):
        return f"<Metric {self.service_name}.{self.metric_name}={self.metric_value}>"


class HCLModelVersion(Base):
    """ML model version tracking"""
    __tablename__ = 'hcl_model_versions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    trained_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    training_dataset_start = Column(TIMESTAMP(timezone=True), nullable=False)
    training_dataset_end = Column(TIMESTAMP(timezone=True), nullable=False)
    training_samples = Column(Integer, nullable=False)

    # Performance
    metrics = Column(JSONB, nullable=False)

    # Artifacts
    model_path = Column(String, nullable=False)
    model_size_bytes = Column(BigInteger)

    # Deployment
    deployed = Column(Boolean, default=False, index=True)
    deployed_at = Column(TIMESTAMP(timezone=True))
    replaced_version = Column(Integer)

    # Training metadata
    hyperparameters = Column(JSONB)
    training_duration_seconds = Column(Integer)
    training_logs = Column(Text)

    def __repr__(self):
        status = "DEPLOYED" if self.deployed else "ARCHIVED"
        return f"<Model {self.model_name} v{self.version} {status}>"


# ============================================================================
# PYDANTIC SCHEMAS (API Request/Response)
# ============================================================================

class SystemState(BaseModel):
    """System state snapshot"""
    cpu_usage: float = Field(ge=0, le=100, description="CPU usage %")
    memory_usage: float = Field(ge=0, le=100, description="Memory usage %")
    gpu_usage: float = Field(ge=0, le=100, description="GPU usage %")
    gpu_memory: float = Field(ge=0, description="GPU memory MB")
    network_latency_p99: float = Field(ge=0, description="Network latency ms")
    error_rate: float = Field(ge=0, description="Errors per minute")
    request_queue_depth: int = Field(ge=0, description="Requests queued")
    throughput: float = Field(ge=0, description="Requests per second")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_usage": 78.5,
                "memory_usage": 65.2,
                "gpu_usage": 45.0,
                "gpu_memory": 18432.0,
                "network_latency_p99": 125.5,
                "error_rate": 2.5,
                "request_queue_depth": 150,
                "throughput": 1250.0
            }
        }


class Action(BaseModel):
    """Single action taken by HCL"""
    service: str = Field(description="Service name (e.g., 'maximus_core')")
    action: str = Field(description="Action type: scale, restart, throttle, etc")
    from_value: Optional[Any] = Field(None, alias="from", description="Previous value")
    to_value: Optional[Any] = Field(None, alias="to", description="New value")
    api_call: str = Field(description="Actual API call made")
    success: bool = Field(default=True, description="Execution success")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "service": "maximus_core",
                "action": "scale",
                "from": 3,
                "to": 5,
                "api_call": "kubectl scale deployment maximus-core --replicas=5",
                "success": True
            }
        }


class DecisionCreate(BaseModel):
    """Request to record a new HCL decision"""
    trigger_type: str = Field(description="cpu_threshold, memory_threshold, prediction, manual")
    trigger_details: Dict[str, Any] = Field(description="Trigger context")
    operational_mode: str = Field(description="HIGH_PERFORMANCE, BALANCED, ENERGY_EFFICIENT")
    previous_mode: Optional[str] = None
    actions_taken: List[Action]
    state_before: SystemState
    decision_latency_ms: int = Field(description="Time to decide")
    planner_used: str = Field(description="fuzzy, rl_agent, manual")

    class Config:
        json_schema_extra = {
            "example": {
                "trigger_type": "cpu_threshold",
                "trigger_details": {"metric": "cpu_usage", "value": 85.5, "threshold": 80},
                "operational_mode": "HIGH_PERFORMANCE",
                "previous_mode": "BALANCED",
                "actions_taken": [
                    {
                        "service": "maximus_core",
                        "action": "scale",
                        "from": 3,
                        "to": 5,
                        "api_call": "kubectl scale deployment maximus-core --replicas=5",
                        "success": True
                    }
                ],
                "state_before": {
                    "cpu_usage": 85.5,
                    "memory_usage": 65.0,
                    "gpu_usage": 45.0,
                    "gpu_memory": 18432.0,
                    "network_latency_p99": 125.0,
                    "error_rate": 2.5,
                    "request_queue_depth": 150,
                    "throughput": 1250.0
                },
                "decision_latency_ms": 450,
                "planner_used": "fuzzy"
            }
        }


class DecisionUpdate(BaseModel):
    """Update decision with outcome after measuring results"""
    state_after: SystemState
    outcome: str = Field(description="SUCCESS, PARTIAL, FAILED")
    execution_latency_ms: int = Field(description="Time to execute")
    reward_signal: Optional[float] = Field(None, description="Computed reward for RL")


class DecisionResponse(BaseModel):
    """API response for decision"""
    id: uuid.UUID
    timestamp: datetime
    trigger_type: str
    operational_mode: str
    outcome: Optional[str]
    reward_signal: Optional[float]
    planner_used: str

    class Config:
        from_attributes = True


class MetricCreate(BaseModel):
    """Batch insert for metrics"""
    service_name: str
    metric_name: str
    metric_value: float
    tags: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class MetricQuery(BaseModel):
    """Query metrics"""
    service_name: Optional[str] = None
    metric_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    aggregation: str = Field(default="avg", description="avg, max, min, stddev")
    interval: str = Field(default="1m", description="1m, 5m, 1h, 1d")


class ModelVersionCreate(BaseModel):
    """Register new model version"""
    model_name: str
    version: int
    training_dataset_start: datetime
    training_dataset_end: datetime
    training_samples: int
    metrics: Dict[str, float] = Field(description="Performance metrics: auc_roc, precision, etc")
    model_path: str
    model_size_bytes: int
    hyperparameters: Optional[Dict[str, Any]] = None
    training_duration_seconds: int
    training_logs: Optional[str] = None


class ModelVersionResponse(BaseModel):
    """Model version response"""
    id: uuid.UUID
    model_name: str
    version: int
    trained_at: datetime
    metrics: Dict[str, float]
    deployed: bool
    deployed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnalyticsQuery(BaseModel):
    """Query for analytics"""
    start_time: datetime
    end_time: datetime
    operational_mode: Optional[str] = None
    outcome: Optional[str] = None
    planner_used: Optional[str] = None


class AnalyticsResponse(BaseModel):
    """Analytics aggregation response"""
    period: str
    total_decisions: int
    success_rate: float
    avg_reward: float
    avg_cpu_delta: float
    avg_memory_delta: float
    mode_distribution: Dict[str, int]
    planner_distribution: Dict[str, int]
