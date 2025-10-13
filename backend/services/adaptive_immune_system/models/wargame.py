"""Pydantic models for Wargame Run."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WargameRunBase(BaseModel):
    """Base wargame run model."""

    exploit_type: Optional[str] = None
    exploit_script_path: Optional[str] = None


class WargameRunCreate(WargameRunBase):
    """Create wargame run request."""

    remedy_id: UUID
    run_code: str = Field(..., max_length=50, description="Unique run code (WAR-YYYYMMDD-NNN)")
    github_actions_run_id: Optional[int] = None
    github_actions_run_url: Optional[str] = None


class WargameRunUpdate(BaseModel):
    """Update wargame run request."""

    exploit_before_patch_status: Optional[str] = None
    exploit_before_patch_output: Optional[str] = None
    exploit_before_patch_duration_ms: Optional[int] = None
    exploit_after_patch_status: Optional[str] = None
    exploit_after_patch_output: Optional[str] = None
    exploit_after_patch_duration_ms: Optional[int] = None
    verdict: Optional[str] = None
    verdict_reason: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    full_report: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("success", "failed", "inconclusive", "error"):
            raise ValueError("verdict must be 'success', 'failed', 'inconclusive', or 'error'")
        return v


class WargameRunModel(WargameRunBase):
    """Complete wargame run model."""

    id: UUID
    remedy_id: UUID
    run_code: str
    github_actions_run_id: Optional[int] = None
    github_actions_run_url: Optional[str] = None
    exploit_before_patch_status: Optional[str] = None
    exploit_before_patch_output: Optional[str] = None
    exploit_before_patch_duration_ms: Optional[int] = None
    exploit_after_patch_status: Optional[str] = None
    exploit_after_patch_output: Optional[str] = None
    exploit_after_patch_duration_ms: Optional[int] = None
    verdict: str
    verdict_reason: Optional[str] = None
    confidence_score: Optional[float] = None
    full_report: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WargameRunResponse(WargameRunModel):
    """API response for wargame run."""
    pass


class WargameReportMessage(BaseModel):
    """RabbitMQ message: Wargaming report → Eureka."""

    remedy_id: UUID
    run_code: str
    verdict: str = Field(..., description="success, failed, inconclusive, error")
    verdict_reason: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    exploit_before_patch_status: str
    exploit_after_patch_status: str
    full_report: dict
    reported_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, v: str) -> str:
        if v not in ("success", "failed", "inconclusive", "error"):
            raise ValueError("verdict must be 'success', 'failed', 'inconclusive', or 'error'")
        return v
