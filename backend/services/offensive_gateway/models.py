"""Maximus Offensive Gateway Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Offensive Gateway Service. These schemas ensure
data consistency and provide a clear structure for representing offensive
commands, their status, and detailed results.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the offensive operations ecosystem.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class CommandStatus(str, Enum):
    """Enumeration for the status of an offensive command."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OffensiveCommand(BaseModel):
    """Represents a single offensive command to be executed.

    Attributes:
        id (str): Unique identifier for the command.
        name (str): The name of the offensive command (e.g., 'exploit_vulnerability').
        parameters (Dict[str, Any]): Parameters required for the command execution.
        target (str): The target for the offensive operation.
        tool (str): The offensive tool to use (e.g., 'metasploit', 'cobalt_strike').
        status (CommandStatus): The current status of the command.
        created_at (str): ISO formatted timestamp of when the command was created.
        completed_at (Optional[str]): ISO formatted timestamp of when the command completed.
    """
    id: str
    name: str
    parameters: Dict[str, Any]
    target: str
    tool: str
    status: CommandStatus = CommandStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None


class CommandResult(BaseModel):
    """Represents the detailed results of a completed offensive command execution.

    Attributes:
        command_id (str): The ID of the offensive command this result belongs to.
        status (str): The final status of the command execution (e.g., 'success', 'failed').
        output (Dict[str, Any]): The raw output or structured data from the offensive tool.
        timestamp (str): ISO formatted timestamp of when the result was recorded.
    """
    command_id: str
    status: str
    output: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())