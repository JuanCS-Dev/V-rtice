"""Maximus Network Reconnaissance Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Network Reconnaissance Service. These schemas ensure
data consistency and provide a clear structure for representing reconnaissance
tasks, their status, and detailed results.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the network reconnaissance ecosystem.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReconStatus(str, Enum):
    """Enumeration for the status of a reconnaissance task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReconTask(BaseModel):
    """Represents a single network reconnaissance task.

    Attributes:
        id (str): Unique identifier for the task.
        target (str): The target for reconnaissance (e.g., IP address, CIDR range, domain).
        scan_type (str): The type of scan to perform (e.g., 'nmap_full', 'masscan_ports').
        parameters (Dict[str, Any]): Parameters for the scan.
        start_time (str): ISO formatted timestamp of when the task started.
        end_time (Optional[str]): ISO formatted timestamp of when the task ended.
        status (ReconStatus): The current status of the task.
    """

    id: str
    target: str
    scan_type: str
    parameters: Dict[str, Any]
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    status: ReconStatus = ReconStatus.PENDING


class ReconResult(BaseModel):
    """Represents the detailed results of a completed reconnaissance task.

    Attributes:
        task_id (str): The ID of the reconnaissance task this result belongs to.
        status (str): The final status of the task execution (e.g., 'success', 'failed').
        output (Dict[str, Any]): The raw output or structured data from the reconnaissance tool.
        timestamp (str): ISO formatted timestamp of when the result was recorded.
    """

    task_id: str
    status: str
    output: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
