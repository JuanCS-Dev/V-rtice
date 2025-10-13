"""Pydantic models for Remedy."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RemedyBase(BaseModel):
    """Base remedy model."""

    remedy_type: str = Field(..., description="Type: dependency_upgrade, code_patch, configuration_change")
    description: str
    implementation_steps: Optional[dict] = None
    current_version: Optional[str] = None
    target_version: Optional[str] = None
    code_diff: Optional[str] = None
    affected_files: List[str] = Field(default_factory=list)
    breaking_changes_detected: bool = False
    breaking_changes_description: Optional[str] = None
    breaking_changes_mitigation: Optional[str] = None

    @field_validator("remedy_type")
    @classmethod
    def validate_remedy_type(cls, v: str) -> str:
        valid_types = ("dependency_upgrade", "code_patch", "configuration_change", "no_fix_available", "manual_intervention")
        if v not in valid_types:
            raise ValueError(f"remedy_type must be one of: {', '.join(valid_types)}")
        return v


class RemedyCreate(RemedyBase):
    """Create remedy request."""

    apv_id: UUID
    remedy_code: str = Field(..., max_length=50, description="Unique remedy code (REM-YYYYMMDD-NNN)")
    llm_model: Optional[str] = None
    llm_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    llm_reasoning: Optional[str] = None


class RemedyUpdate(BaseModel):
    """Update remedy request."""

    status: Optional[str] = None
    validation_status: Optional[str] = None
    validation_error: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None
    github_branch_name: Optional[str] = None


class RemedyModel(RemedyBase):
    """Complete remedy model."""

    id: UUID
    apv_id: UUID
    remedy_code: str
    status: str = "generated"
    validation_status: Optional[str] = None
    validation_error: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None
    github_branch_name: Optional[str] = None
    llm_model: Optional[str] = None
    llm_confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RemedyResponse(RemedyModel):
    """API response for remedy."""
    pass


class RemedyGenerationRequest(BaseModel):
    """Request to generate remedy via LLM."""

    apv_id: UUID
    cve_details: dict
    dependency_details: dict
    vulnerable_code_context: Optional[str] = None
    prefer_type: Optional[str] = Field(None, description="Preferred remedy type")
