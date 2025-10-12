"""
Pydantic models for Reactive Fabric Analysis Service
Shared data structures for forensic analysis.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1: Real implementation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


class ProcessingStatus(str, Enum):
    """Forensic capture processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AttackSeverity(str, Enum):
    """Attack severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ForensicCapture(BaseModel):
    """Forensic capture model (from database)."""

    id: UUID
    honeypot_id: UUID
    filename: str
    file_path: str
    file_type: str
    file_size_bytes: Optional[int] = None
    file_hash: Optional[str] = None
    captured_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    attacks_extracted: int = 0
    ttps_extracted: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class AttackCreate(BaseModel):
    """Model for creating an attack record."""

    honeypot_id: UUID
    attacker_ip: str = Field(..., description="Attacker IP address")
    attack_type: str = Field(..., description="Type of attack")
    severity: AttackSeverity
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    ttps: List[str] = Field(
        default_factory=list, description="MITRE ATT&CK technique IDs"
    )
    iocs: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="IoCs: {ips: [], domains: [], hashes: [], usernames: []}",
    )
    payload: Optional[str] = Field(None, description="Attack payload (sanitized)")
    captured_at: datetime


class AnalysisStatus(BaseModel):
    """Analysis service status."""

    status: str = "operational"
    captures_processed_today: int = 0
    ttps_extracted_today: int = 0
    attacks_created_today: int = 0
    last_processing: Optional[datetime] = None
    polling_interval_seconds: int
