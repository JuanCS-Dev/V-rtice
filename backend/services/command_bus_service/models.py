"""Pydantic models for Command Bus Service."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class C2LCommandType(str, Enum):
    """Command types for C2L."""

    MUTE = "MUTE"
    ISOLATE = "ISOLATE"
    TERMINATE = "TERMINATE"
    SNAPSHOT_STATE = "SNAPSHOT_STATE"
    REVOKE_ACCESS = "REVOKE_ACCESS"
    INJECT_CONSTRAINT = "INJECT_CONSTRAINT"


class CommandStatus(str, Enum):
    """Command execution status."""

    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class C2LCommand(BaseModel):
    """C2L Command model."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    operator_id: str
    command_type: C2LCommandType
    target_agents: list[str]
    parameters: dict[str, Any] = Field(default_factory=dict)
    execution_deadline: datetime | None = None
    status: CommandStatus = CommandStatus.PENDING
    confirmation_received_at: datetime | None = None
    execution_result: dict[str, Any] | None = None


class CommandReceipt(BaseModel):
    """Command receipt after submission."""

    command_id: UUID
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KillSwitchLayer(str, Enum):
    """Kill switch execution layers."""

    SOFTWARE = "SOFTWARE"  # Layer 1: Graceful shutdown
    CONTAINER = "CONTAINER"  # Layer 2: Container destruction
    NETWORK = "NETWORK"  # Layer 3: Network isolation


class KillSwitchResult(BaseModel):
    """Kill switch execution result."""

    agent_id: str
    layers_executed: list[KillSwitchLayer]
    success: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
