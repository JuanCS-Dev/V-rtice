"""Maximus Vulnerability Scanner Service - Pydantic Schemas.

This module defines the Pydantic schemas for data validation and serialization
within the Vulnerability Scanner Service. These schemas are used for API request
and response models, ensuring data consistency and clear documentation of
data structures.

It mirrors the SQLAlchemy models defined in `database.py` but is specifically
designed for data validation and serialization, providing a clean separation
between database models and API models.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ScanTaskBase(BaseModel):
    """Base Pydantic model for a vulnerability scan task."""
    target: str
    scan_type: str
    parameters: Dict[str, Any]


class ScanTaskCreate(ScanTaskBase):
    """Pydantic model for creating a new vulnerability scan task."""
    pass


class ScanTask(ScanTaskBase):
    """Pydantic model for a vulnerability scan task, including database-generated fields.

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
    """Base Pydantic model for a detected vulnerability finding."""
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
    """Pydantic model for creating a new vulnerability finding."""
    pass


class Vulnerability(VulnerabilityBase):
    """Pydantic model for a detected vulnerability finding, including database-generated fields.

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