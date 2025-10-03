"""
Pydantic schemas for ADR Core Service
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .enums import (
    SeverityLevel,
    ThreatType,
    ActionType,
    ActionStatus,
    DetectionSource,
    PlaybookTrigger,
    AlertStatus,
    ConnectorType,
)


# ========== Detection Schemas ==========

class MITRETechnique(BaseModel):
    """MITRE ATT&CK technique information"""
    technique_id: str = Field(..., description="MITRE technique ID (e.g., T1059)")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="Associated tactic")
    subtechnique: Optional[str] = Field(None, description="Subtechnique ID if applicable")


class ThreatIndicator(BaseModel):
    """Threat indicator from detection"""
    type: str = Field(..., description="Indicator type (hash, ip, domain, etc.)")
    value: str = Field(..., description="Indicator value")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    source: DetectionSource = Field(..., description="Detection source")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreatDetection(BaseModel):
    """Complete threat detection result"""
    detection_id: str = Field(..., description="Unique detection ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    severity: SeverityLevel = Field(..., description="Threat severity")
    threat_type: ThreatType = Field(..., description="Type of threat detected")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence 0-1")
    score: int = Field(..., ge=0, le=100, description="Threat score 0-100")

    # Source information
    source: DetectionSource = Field(..., description="Detection source")
    source_details: Dict[str, Any] = Field(default_factory=dict)

    # Threat details
    title: str = Field(..., description="Detection title")
    description: str = Field(..., description="Detailed description")
    indicators: List[ThreatIndicator] = Field(default_factory=list)
    mitre_techniques: List[MITRETechnique] = Field(default_factory=list)

    # Context
    affected_assets: List[str] = Field(default_factory=list, description="IPs, hostnames, users")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting evidence")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Analysis
    kill_chain_phase: Optional[str] = Field(None, description="Cyber kill chain phase")
    false_positive_likelihood: float = Field(default=0.0, ge=0, le=1)

    @validator('score')
    def validate_score(cls, v, values):
        """Ensure score aligns with severity"""
        severity = values.get('severity')
        if severity == SeverityLevel.CRITICAL and v < 80:
            raise ValueError("Critical severity must have score >= 80")
        if severity == SeverityLevel.HIGH and v < 60:
            raise ValueError("High severity must have score >= 60")
        return v


class DetectionRule(BaseModel):
    """Custom detection rule definition"""
    rule_id: str = Field(..., description="Unique rule ID")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")
    enabled: bool = Field(default=True)

    # Rule logic
    rule_type: str = Field(..., description="sigma, yara, custom, ml")
    rule_content: str = Field(..., description="Rule content/pattern")

    # Matching
    severity: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    threat_types: List[ThreatType] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)

    # Metadata
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0")
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalysisRequest(BaseModel):
    """Request for threat analysis"""
    request_id: str = Field(..., description="Unique request ID")
    analysis_type: str = Field(..., description="file, network, process, memory")
    target: str = Field(..., description="Target to analyze")
    options: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    context: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Analysis result with detections"""
    request_id: str = Field(..., description="Original request ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    analysis_type: str
    status: str = Field(..., description="completed, failed, partial")

    detections: List[ThreatDetection] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: int = Field(..., description="Analysis duration in ms")
    errors: List[str] = Field(default_factory=list)


# ========== Response Schemas ==========

class ResponseAction(BaseModel):
    """Individual response action"""
    action_id: str = Field(..., description="Unique action ID")
    action_type: ActionType = Field(..., description="Type of action")
    status: ActionStatus = Field(default=ActionStatus.PENDING)

    # Action parameters
    target: str = Field(..., description="Target of action (IP, file, process)")
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # Execution
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: int = Field(default=300)
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)

    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Rollback
    rollback_action: Optional[Dict[str, Any]] = Field(None, description="Action to undo this")
    can_rollback: bool = Field(default=False)


class PlaybookStep(BaseModel):
    """Single step in a playbook"""
    step_id: str = Field(..., description="Step identifier")
    name: str = Field(..., description="Step name")
    action_type: ActionType = Field(..., description="Action to execute")

    parameters: Dict[str, Any] = Field(default_factory=dict)
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Pre-conditions")

    order: int = Field(..., description="Execution order")
    parallel: bool = Field(default=False, description="Can run in parallel")
    critical: bool = Field(default=False, description="Playbook fails if this fails")

    timeout_seconds: int = Field(default=300)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3)


class Playbook(BaseModel):
    """Automated response playbook"""
    playbook_id: str = Field(..., description="Unique playbook ID")
    name: str = Field(..., description="Playbook name")
    description: str = Field(..., description="Playbook description")
    enabled: bool = Field(default=True)

    # Triggers
    trigger_type: PlaybookTrigger = Field(..., description="What triggers this playbook")
    trigger_conditions: Dict[str, Any] = Field(..., description="Trigger conditions")

    # Steps
    steps: List[PlaybookStep] = Field(..., description="Ordered list of steps")

    # Execution
    auto_execute: bool = Field(default=False, description="Execute without approval")
    require_approval: bool = Field(default=True)
    approval_timeout_minutes: int = Field(default=30)

    # Metadata
    severity_threshold: SeverityLevel = Field(default=SeverityLevel.MEDIUM)
    author: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0")
    tags: List[str] = Field(default_factory=list)


class PlaybookExecution(BaseModel):
    """Playbook execution instance"""
    execution_id: str = Field(..., description="Unique execution ID")
    playbook_id: str = Field(..., description="Playbook being executed")

    # Trigger
    triggered_by: str = Field(..., description="detection_id or manual")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)

    # Status
    status: str = Field(default="pending", description="pending, running, completed, failed, cancelled")
    current_step: Optional[int] = None

    # Actions
    actions: List[ResponseAction] = Field(default_factory=list)
    actions_completed: int = Field(default=0)
    actions_failed: int = Field(default=0)

    # Results
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ResponseRequest(BaseModel):
    """Manual response request"""
    detection_id: str = Field(..., description="Detection to respond to")
    actions: List[ActionType] = Field(..., description="Actions to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    approval_token: Optional[str] = None
    auto_approve: bool = Field(default=False)


# ========== Alert Schemas ==========

class Alert(BaseModel):
    """Security alert"""
    alert_id: str = Field(..., description="Unique alert ID")
    detection_id: str = Field(..., description="Associated detection")

    # Alert details
    severity: SeverityLevel = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Alert description")

    # Status
    status: AlertStatus = Field(default=AlertStatus.NEW)
    assigned_to: Optional[str] = Field(None, description="Analyst assigned")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Response
    playbook_executions: List[str] = Field(default_factory=list, description="Execution IDs")
    manual_actions: List[str] = Field(default_factory=list, description="Action IDs")

    # Notes and tracking
    notes: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertUpdate(BaseModel):
    """Alert status update"""
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[List[str]] = None


# ========== Configuration Schemas ==========

class EngineConfig(BaseModel):
    """Engine configuration"""
    enabled: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    workers: int = Field(default=4, ge=1, le=32)
    queue_size: int = Field(default=1000)
    timeout_seconds: int = Field(default=300)
    settings: Dict[str, Any] = Field(default_factory=dict)


class ConnectorConfig(BaseModel):
    """External connector configuration"""
    connector_id: str = Field(..., description="Unique connector ID")
    connector_type: ConnectorType = Field(..., description="Connector type")
    enabled: bool = Field(default=True)

    endpoint: str = Field(..., description="Connector endpoint URL")
    credentials: Dict[str, Any] = Field(default_factory=dict)

    timeout_seconds: int = Field(default=30)
    retry_attempts: int = Field(default=3)

    settings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ADRConfig(BaseModel):
    """Complete ADR service configuration"""
    service_name: str = Field(default="adr_core_service")
    version: str = Field(default="2.0.0")

    # Engines
    detection_engine: EngineConfig = Field(default_factory=EngineConfig)
    response_engine: EngineConfig = Field(default_factory=EngineConfig)

    # Connectors
    connectors: List[ConnectorConfig] = Field(default_factory=list)

    # Thresholds
    auto_response_threshold: SeverityLevel = Field(default=SeverityLevel.HIGH)
    alert_threshold: SeverityLevel = Field(default=SeverityLevel.MEDIUM)

    # Features
    enable_ml: bool = Field(default=True)
    enable_auto_response: bool = Field(default=False)
    enable_playbooks: bool = Field(default=True)

    # Limits
    max_concurrent_analyses: int = Field(default=10)
    max_concurrent_responses: int = Field(default=5)

    metadata: Dict[str, Any] = Field(default_factory=dict)


# ========== Metrics Schemas ==========

class ServiceMetrics(BaseModel):
    """Service performance metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_seconds: int

    # Detection metrics
    total_detections: int = Field(default=0)
    detections_by_severity: Dict[str, int] = Field(default_factory=dict)
    detections_by_type: Dict[str, int] = Field(default_factory=dict)

    # Response metrics
    total_responses: int = Field(default=0)
    responses_completed: int = Field(default=0)
    responses_failed: int = Field(default=0)

    # Alert metrics
    total_alerts: int = Field(default=0)
    alerts_by_status: Dict[str, int] = Field(default_factory=dict)

    # Performance
    avg_detection_time_ms: float = Field(default=0.0)
    avg_response_time_ms: float = Field(default=0.0)

    # Current state
    active_analyses: int = Field(default=0)
    active_responses: int = Field(default=0)
    queue_depth: int = Field(default=0)


# ========== API Response Schemas ==========

class APIResponse(BaseModel):
    """Standard API response wrapper"""
    status: str = Field(..., description="success or error")
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Service health status"""
    status: str = Field(..., description="healthy, degraded, unhealthy")
    version: str
    uptime_seconds: int

    components: Dict[str, str] = Field(default_factory=dict, description="Component health")

    timestamp: datetime = Field(default_factory=datetime.utcnow)
