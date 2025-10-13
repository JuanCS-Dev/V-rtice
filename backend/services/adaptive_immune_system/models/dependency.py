"""Pydantic models for Dependency."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DependencyBase(BaseModel):
    """Base dependency model."""

    project_name: str = Field(..., max_length=255)
    project_path: str
    package_name: str = Field(..., max_length=255)
    package_version: str = Field(..., max_length=100)
    ecosystem: str = Field(..., max_length=50, description="npm, pypi, cargo, go, docker")
    direct_dependency: bool = True
    parent_package: Optional[str] = None
    manifest_file: Optional[str] = None


class DependencyCreate(DependencyBase):
    """Create dependency request."""
    pass


class DependencyUpdate(BaseModel):
    """Update dependency request."""

    package_version: Optional[str] = None
    direct_dependency: Optional[bool] = None
    parent_package: Optional[str] = None


class DependencyModel(DependencyBase):
    """Complete dependency model."""

    id: UUID
    scanned_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DependencyResponse(DependencyModel):
    """API response for dependency."""
    pass
