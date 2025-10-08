"""Maximus Vulnerability Scanner Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Vulnerability Scanner Service. These schemas ensure
data consistency and provide a clear structure for representing scan tasks,
vulnerability findings, and scan results.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the vulnerability scanning ecosystem.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ScanTaskBase(BaseModel):
    """Base model for a vulnerability scan task."""

    target: str
    scan_type: str
    parameters: Dict[str, Any]


class ScanTaskCreate(ScanTaskBase):
    """Model for creating a new vulnerability scan task."""

    pass


class ScanTask(ScanTaskBase):
    """Model for a vulnerability scan task, including database-generated fields.

    Attributes:
        id (int): Unique identifier for the scan task.
        status (str): Current status of the scan (e.g., 'pending', 'running').
        start_time (datetime): Timestamp of when the scan started.
        end_time (Optional[datetime]): Timestamp of when the scan ended.
        report_path (Optional[str]): Path to the generated report.
        raw_results (Optional[str]): Raw results from the scanner.

    Config:
        orm_mode = True
    """

    id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    report_path: Optional[str]

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True


class VulnerabilityBase(BaseModel):
    """Base model for a detected vulnerability finding."""

    scan_task_id: int
    cve_id: Optional[str]
    name: str
    severity: str
    description: str
    solution: Optional[str]
    host: str
    port: Optional[int]
    protocol: Optional[str]


class VulnerabilityCreate(VulnerabilityBase):
    """Model for creating a new vulnerability finding."""

    pass


class Vulnerability(VulnerabilityBase):
    """Model for a detected vulnerability finding, including database-generated fields.

    Attributes:
        id (int): Unique identifier for the vulnerability.
        discovered_at (datetime): Timestamp of when the vulnerability was discovered.
        is_false_positive (bool): True if the vulnerability is a false positive.
        remediated_at (Optional[datetime]): Timestamp of when the vulnerability was remediated.

    Config:
        orm_mode = True
    """

    id: int
    discovered_at: datetime
    is_false_positive: bool
    remediated_at: Optional[datetime]

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True
