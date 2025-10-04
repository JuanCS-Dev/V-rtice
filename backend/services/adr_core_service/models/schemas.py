"""Pydantic schemas for the ADR Core Service.

This module defines the data structures used for API requests, responses,
and internal data handling. It uses Pydantic for data validation and
serialization, ensuring data integrity throughout the service.
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
    """Represents a MITRE ATT&CK technique.

    Attributes:
        technique_id (str): The unique MITRE technique ID (e.g., T1059).
        technique_name (str): The official name of the technique.
        tactic (str): The associated MITRE ATT&CK tactic.
        subtechnique (Optional[str]): The sub-technique ID, if applicable.
    """
    technique_id: str = Field(..., description="MITRE technique ID (e.g., T1059)")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="Associated tactic")
    subtechnique: Optional[str] = Field(None, description="Subtechnique ID if applicable")


class ThreatIndicator(BaseModel):
    """Represents a single, observable indicator of a threat.

    Indicators are atomic pieces of evidence like a file hash, IP address,
    or domain name.

    Attributes:
        type (str): The type of indicator (e.g., 'hash', 'ip', 'domain').
        value (str): The value of the indicator.
        confidence (float): The confidence score (0-1) in this indicator.
        source (DetectionSource): The source that identified this indicator.
        first_seen (datetime): Timestamp of the first observation.
        last_seen (datetime): Timestamp of the most recent observation.
        metadata (Dict[str, Any]): Additional metadata about the indicator.
    """
    type: str = Field(..., description="Indicator type (hash, ip, domain, etc.)")
    value: str = Field(..., description="Indicator value")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    source: DetectionSource = Field(..., description="Detection source")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ThreatDetection(BaseModel):
    """Represents a complete, aggregated threat detection event.

    This is a core model that encapsulates all information about a detected
    threat, from its severity and type to the evidence and affected assets.

    Attributes:
        detection_id (str): A unique identifier for this detection event.
        timestamp (datetime): The time the detection was made.
        severity (SeverityLevel): The assessed severity of the threat.
        threat_type (ThreatType): The classification of the threat.
        confidence (float): The overall confidence in the detection's accuracy.
        score (int): A numerical score (0-100) representing the threat level.
        source (DetectionSource): The primary engine or method that made the detection.
        source_details (Dict[str, Any]): Specific details from the detection source.
        title (str): A concise, human-readable title for the detection.
        description (str): A detailed description of the threat.
        indicators (List[ThreatIndicator]): A list of observable indicators.
        mitre_techniques (List[MITRETechnique]): Associated MITRE ATT&CK techniques.
        affected_assets (List[str]): A list of assets (e.g., IPs, hosts) affected.
        evidence (Dict[str, Any]): A collection of supporting evidence.
        metadata (Dict[str, Any]): Additional arbitrary metadata.
        kill_chain_phase (Optional[str]): The phase in the cyber kill chain.
        false_positive_likelihood (float): Estimated likelihood of being a false positive.
    """
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
        """Validates that the score is consistent with the severity level."""
        severity = values.get('severity')
        if severity == SeverityLevel.CRITICAL and v < 80:
            raise ValueError("Critical severity must have score >= 80")
        if severity == SeverityLevel.HIGH and v < 60:
            raise ValueError("High severity must have score >= 60")
        return v


class DetectionRule(BaseModel):
    """Defines a custom rule for the detection engine.

    This model allows for the creation of user-defined detection rules, such as
    those based on Sigma or YARA.

    Attributes:
        rule_id (str): A unique identifier for the rule.
        name (str): The name of the rule.
        description (str): A description of what the rule detects.
        enabled (bool): Whether the rule is currently active.
        rule_type (str): The type of rule (e.g., 'sigma', 'yara').
        rule_content (str): The actual content of the rule.
        severity (SeverityLevel): The severity to assign to detections from this rule.
        threat_types (List[ThreatType]): Threat types associated with this rule.
        mitre_techniques (List[str]): MITRE ATT&CK technique IDs.
        author (Optional[str]): The author of the rule.
        created_at (datetime): Timestamp of rule creation.
        updated_at (datetime): Timestamp of the last update.
        version (str): The version of the rule.
        tags (List[str]): Tags for categorizing the rule.
        metadata (Dict[str, Any]): Additional metadata.
    """
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
    """Represents a request to perform a threat analysis.

    Attributes:
        request_id (str): A unique ID for tracking the request.
        analysis_type (str): The type of analysis to perform (e.g., 'file', 'network').
        target (str): The target of the analysis (e.g., a file path or IP address).
        options (Dict[str, Any]): Analysis-specific options.
        priority (int): The priority of the request (1-10).
        context (Dict[str, Any]): Additional context for the analysis.
    """
    request_id: str = Field(..., description="Unique request ID")
    analysis_type: str = Field(..., description="file, network, process, memory")
    target: str = Field(..., description="Target to analyze")
    options: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)
    context: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    """Contains the results of a threat analysis.

    Attributes:
        request_id (str): The ID of the original `AnalysisRequest`.
        timestamp (datetime): The time the analysis was completed.
        analysis_type (str): The type of analysis that was performed.
        status (str): The final status of the analysis ('completed', 'failed').
        detections (List[ThreatDetection]): A list of threats found.
        summary (Dict[str, Any]): A summary of the analysis results.
        execution_time_ms (int): The total time taken for the analysis in ms.
        errors (List[str]): A list of any errors that occurred.
    """
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
    """Represents a single, executable response action.

    Attributes:
        action_id (str): A unique ID for this specific action instance.
        action_type (ActionType): The type of action to perform.
        status (ActionStatus): The current status of the action.
        target (str): The target of the action (e.g., an IP or file path).
        parameters (Dict[str, Any]): Parameters for the action.
        priority (int): The execution priority (1-10).
        timeout_seconds (int): How long to wait before timing out.
        retry_count (int): The number of times this action has been retried.
        max_retries (int): The maximum number of retry attempts.
        result (Optional[Dict[str, Any]]): The result of the action if successful.
        error (Optional[str]): The error message if the action failed.
        started_at (Optional[datetime]): Timestamp when the action started.
        completed_at (Optional[datetime]): Timestamp when the action completed.
        rollback_action (Optional[Dict[str, Any]]): Defines the action to undo this one.
        can_rollback (bool): Whether this action can be rolled back.
    """
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
    """Defines a single step within an automated response playbook.

    Attributes:
        step_id (str): A unique identifier for the step within the playbook.
        name (str): A human-readable name for the step.
        action_type (ActionType): The type of action to execute.
        parameters (Dict[str, Any]): Parameters for the action.
        conditions (List[Dict[str, Any]]): Conditions that must be met to run.
        order (int): The execution order of the step.
        parallel (bool): Whether this step can run in parallel with others of the same order.
        critical (bool): If true, the playbook will fail if this step fails.
        timeout_seconds (int): A specific timeout for this step.
        retry_on_failure (bool): Whether to retry this step if it fails.
        max_retries (int): The maximum number of retries for this step.
    """
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
    """Defines an automated response playbook.

    Playbooks are a series of steps (actions) that are automatically executed
    in response to a specific type of threat detection.

    Attributes:
        playbook_id (str): A unique identifier for the playbook.
        name (str): The name of the playbook.
        description (str): A description of the playbook's purpose.
        enabled (bool): Whether the playbook is active.
        trigger_type (PlaybookTrigger): The primary condition that triggers the playbook.
        trigger_conditions (Dict[str, Any]): The specific conditions for the trigger.
        steps (List[PlaybookStep]): The ordered list of steps to execute.
        auto_execute (bool): Whether the playbook can execute without manual approval.
        require_approval (bool): Whether manual approval is required.
        approval_timeout_minutes (int): Time to wait for approval before cancelling.
        severity_threshold (SeverityLevel): The minimum severity to trigger this playbook.
        author (Optional[str]): The author of the playbook.
        created_at (datetime): Timestamp of playbook creation.
        updated_at (datetime): Timestamp of the last update.
        version (str): The version of the playbook.
        tags (List[str]): Tags for categorizing the playbook.
    """
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
    """Represents a single run of a playbook.

    This model tracks the state and results of a playbook execution from
    trigger to completion.

    Attributes:
        execution_id (str): A unique ID for this specific execution.
        playbook_id (str): The ID of the playbook that is being executed.
        triggered_by (str): The ID of the detection or manual trigger.
        triggered_at (datetime): The time the execution was triggered.
        status (str): The current status of the execution.
        current_step (Optional[int]): The index of the current step being executed.
        actions (List[ResponseAction]): A list of all actions for this execution.
        actions_completed (int): The number of completed actions.
        actions_failed (int): The number of failed actions.
        started_at (Optional[datetime]): The time the execution started.
        completed_at (Optional[datetime]): The time the execution finished.
        errors (List[str]): A list of any errors that occurred during execution.
        metadata (Dict[str, Any]): Additional metadata about the execution.
    """
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
    """Represents a request to manually trigger a response.

    Attributes:
        detection_id (str): The ID of the detection to respond to.
        actions (List[ActionType]): A list of actions to execute.
        parameters (Dict[str, Any]): Parameters for the actions.
        approval_token (Optional[str]): An approval token, if required.
        auto_approve (bool): If true, bypasses the approval workflow.
    """
    detection_id: str = Field(..., description="Detection to respond to")
    actions: List[ActionType] = Field(..., description="Actions to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    approval_token: Optional[str] = None
    auto_approve: bool = Field(default=False)


# ========== Alert Schemas ==========

class Alert(BaseModel):
    """Represents a security alert for analyst review.

    Alerts are generated from high-confidence detections and serve as the
    primary unit of work for security analysts.

    Attributes:
        alert_id (str): A unique ID for the alert.
        detection_id (str): The ID of the associated detection.
        severity (SeverityLevel): The severity of the alert.
        title (str): The title of the alert.
        description (str): A description of the alert.
        status (AlertStatus): The current status in the alert lifecycle.
        assigned_to (Optional[str]): The analyst assigned to this alert.
        created_at (datetime): The time the alert was created.
        acknowledged_at (Optional[datetime]): The time the alert was acknowledged.
        resolved_at (Optional[datetime]): The time the alert was resolved.
        playbook_executions (List[str]): IDs of any playbooks executed for this alert.
        manual_actions (List[str]): IDs of any manual actions taken.
        notes (List[Dict[str, Any]]): Analyst notes.
        tags (List[str]): Tags for categorizing the alert.
        metadata (Dict[str, Any]): Additional metadata.
    """
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
    """Represents a request to update an existing alert.

    Attributes:
        status (Optional[AlertStatus]): The new status of the alert.
        assigned_to (Optional[str]): The new assignee for the alert.
        note (Optional[str]): A new note to add to the alert.
        tags (Optional[List[str]]): A new list of tags to set.
    """
    status: Optional[AlertStatus] = None
    assigned_to: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[List[str]] = None


# ========== Configuration Schemas ==========

class EngineConfig(BaseModel):
    """Represents the configuration for an internal engine.

    Attributes:
        enabled (bool): Whether the engine is enabled.
        log_level (str): The logging level for the engine.
        workers (int): The number of worker processes/threads.
        queue_size (int): The size of the input queue.
        timeout_seconds (int): The default timeout for operations.
        settings (Dict[str, Any]): Engine-specific settings.
    """
    enabled: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    workers: int = Field(default=4, ge=1, le=32)
    queue_size: int = Field(default=1000)
    timeout_seconds: int = Field(default=300)
    settings: Dict[str, Any] = Field(default_factory=dict)


class ConnectorConfig(BaseModel):
    """Represents the configuration for an external connector.

    Attributes:
        connector_id (str): A unique ID for the connector instance.
        connector_type (ConnectorType): The type of the connector.
        enabled (bool): Whether the connector is enabled.
        endpoint (str): The API endpoint of the external service.
        credentials (Dict[str, Any]): Credentials for authentication.
        timeout_seconds (int): The request timeout.
        retry_attempts (int): The number of retry attempts on failure.
        settings (Dict[str, Any]): Connector-specific settings.
        metadata (Dict[str, Any]): Additional metadata.
    """
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
    """Represents the complete configuration for the ADR service.

    Attributes:
        service_name (str): The name of the service.
        version (str): The service version.
        detection_engine (EngineConfig): Configuration for the detection engine.
        response_engine (EngineConfig): Configuration for the response engine.
        connectors (List[ConnectorConfig]): A list of external connector configurations.
        auto_response_threshold (SeverityLevel): The minimum severity for auto-response.
        alert_threshold (SeverityLevel): The minimum severity to generate an alert.
        enable_ml (bool): Whether to enable ML-based features.
        enable_auto_response (bool): Whether to enable autonomous response.
        enable_playbooks (bool): Whether to enable playbooks.
        max_concurrent_analyses (int): Max concurrent analysis tasks.
        max_concurrent_responses (int): Max concurrent response tasks.
        metadata (Dict[str, Any]): Additional service-wide metadata.
    """
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
    """Represents a snapshot of service performance metrics.

    Attributes:
        timestamp (datetime): The time the metrics were generated.
        uptime_seconds (int): The service uptime in seconds.
        total_detections (int): The total number of detections.
        detections_by_severity (Dict[str, int]): Detections broken down by severity.
        detections_by_type (Dict[str, int]): Detections broken down by type.
        total_responses (int): The total number of responses.
        responses_completed (int): The number of completed responses.
        responses_failed (int): The number of failed responses.
        total_alerts (int): The total number of alerts.
        alerts_by_status (Dict[str, int]): Alerts broken down by status.
        avg_detection_time_ms (float): Average time to detect a threat.
        avg_response_time_ms (float): Average time to respond to a threat.
        active_analyses (int): The number of currently active analyses.
        active_responses (int): The number of currently active responses.
        queue_depth (int): The current depth of the processing queue.
    """
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
    """Represents a standard API response wrapper.

    Attributes:
        status (str): The status of the response ('success' or 'error').
        message (Optional[str]): An optional message.
        data (Optional[Any]): The response payload.
        timestamp (datetime): The timestamp of the response.
    """
    status: str = Field(..., description="success or error")
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Represents the health status of the service.

    Attributes:
        status (str): The overall health status ('healthy', 'degraded', 'unhealthy').
        version (str): The service version.
        uptime_seconds (int): The service uptime in seconds.
        components (Dict[str, str]): The health status of individual components.
        timestamp (datetime): The timestamp of the health check.
    """
    status: str = Field(..., description="healthy, degraded, unhealthy")
    version: str
    uptime_seconds: int

    components: Dict[str, str] = Field(default_factory=dict, description="Component health")

    timestamp: datetime = Field(default_factory=datetime.utcnow)