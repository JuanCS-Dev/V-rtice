"""Pydantic models for Threat (CVE)."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ThreatBase(BaseModel):
    """Base threat model."""

    cve_id: str = Field(..., max_length=20, description="CVE identifier (CVE-YYYY-NNNNN)")
    source: str = Field(..., description="Source: 'nvd', 'ghsa', 'osv'")
    title: str = Field(..., description="CVE title")
    description: str = Field(..., description="CVE description")
    published_date: datetime
    last_modified_date: datetime
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    cvss_vector: Optional[str] = None
    severity: Optional[str] = None
    ecosystems: List[str] = Field(default_factory=list)
    affected_packages: Optional[dict] = None
    cwe_ids: List[str] = Field(default_factory=list)
    references: Optional[dict] = None


class ThreatCreate(ThreatBase):
    """Create threat request."""
    pass


class ThreatUpdate(BaseModel):
    """Update threat request (all optional)."""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    cvss_score: Optional[float] = None
    severity: Optional[str] = None


class ThreatModel(ThreatBase):
    """Complete threat model."""

    id: UUID
    status: str = "new"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThreatResponse(ThreatModel):
    """API response for threat."""
    pass
