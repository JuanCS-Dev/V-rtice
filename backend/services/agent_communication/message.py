"""Agent Communication Protocol (ACP) Message Schemas.

Defines type-safe message structures for inter-agent communication.
All messages follow a unified schema with strict validation.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MessageType(str, Enum):
    """Enumeration of valid ACP message types."""

    TASK_ASSIGN = "task_assign"
    TASK_RESULT = "task_result"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    HOTL_REQUEST = "hotl_request"  # Human-on-the-Loop approval request
    HOTL_RESPONSE = "hotl_response"


class AgentType(str, Enum):
    """Enumeration of agent types in the system."""

    ORCHESTRATOR = "orchestrator"
    RECONNAISSANCE = "reconnaissance"
    EXPLOITATION = "exploitation"
    POST_EXPLOITATION = "post_exploitation"
    ANALYSIS = "analysis"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ACPMessage(BaseModel):
    """Agent Communication Protocol unified message structure.

    This is the canonical message format for all agent-to-agent communication.
    Every message must be serializable to JSON for queue transport.

    Attributes:
        message_id: Unique identifier for this message
        message_type: Type of message (task, result, status, etc)
        sender: Agent type that sent this message
        recipient: Agent type that should receive this message
        timestamp: ISO 8601 timestamp of message creation
        correlation_id: ID linking related messages (e.g., task and result)
        priority: Priority level for task scheduling
        payload: Message-specific data (varies by message_type)
        metadata: Optional additional context
    """

    message_id: UUID = Field(default_factory=uuid4)
    message_type: MessageType
    sender: AgentType
    recipient: AgentType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[UUID] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v: Any) -> datetime:
        """Parse timestamp from ISO string if needed."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    def to_json(self) -> str:
        """Serialize message to JSON for queue transport."""
        return self.model_dump_json()

    @classmethod
    def from_json(cls, json_str: str) -> "ACPMessage":
        """Deserialize message from JSON."""
        return cls.model_validate_json(json_str)


class TaskAssignMessage(BaseModel):
    """Payload schema for TASK_ASSIGN messages.

    Used by Orchestrator to delegate tasks to specialized agents.
    """

    task_id: UUID = Field(default_factory=uuid4)
    task_type: str  # e.g., "port_scan", "exploit_attempt", "osint_gather"
    target: str  # Target IP/domain/URL
    parameters: Dict[str, Any]
    timeout_seconds: int = 300
    requires_hotl: bool = False  # Does this task need human approval?


class TaskResultMessage(BaseModel):
    """Payload schema for TASK_RESULT messages.

    Sent by agents back to Orchestrator upon task completion.
    """

    task_id: UUID
    success: bool
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_seconds: float
    confidence_score: Optional[float] = None  # AI confidence (0.0-1.0)


class StatusUpdateMessage(BaseModel):
    """Payload schema for STATUS_UPDATE messages.

    Periodic updates during long-running tasks.
    """

    task_id: UUID
    progress_percent: float  # 0.0 to 100.0
    current_step: str
    estimated_completion_seconds: Optional[int] = None


class ErrorMessage(BaseModel):
    """Payload schema for ERROR messages.

    Critical failures that require operator attention.
    """

    error_code: str
    error_message: str
    task_id: Optional[UUID] = None
    stack_trace: Optional[str] = None
    recoverable: bool = False


class HOTLRequestMessage(BaseModel):
    """Payload schema for HOTL_REQUEST messages.

    Human-on-the-Loop approval requests for high-risk actions.
    """

    action_type: str  # e.g., "exploit_launch", "lateral_movement"
    target: str
    risk_level: str  # "low", "medium", "high", "critical"
    justification: str  # Why this action is necessary
    proposed_command: Optional[str] = None
    timeout_seconds: int = 300  # How long to wait for approval


class HOTLResponseMessage(BaseModel):
    """Payload schema for HOTL_RESPONSE messages.

    Human operator's decision on HOTL request.
    """

    request_id: UUID
    approved: bool
    operator_notes: Optional[str] = None
    modified_parameters: Optional[Dict[str, Any]] = None
