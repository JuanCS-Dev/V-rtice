"""
Application Layer - DTOs (Data Transfer Objects)

Input/Output schemas for use cases.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateEntityDTO(BaseModel):
    """Input DTO for creating entity."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class UpdateEntityDTO(BaseModel):
    """Input DTO for updating entity."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class EntityDTO(BaseModel):
    """Output DTO for entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str]
    status: str
    metadata: dict[str, str]
    created_at: datetime
    updated_at: datetime


class PaginatedEntitiesDTO(BaseModel):
    """Output DTO for paginated entities."""

    items: list[EntityDTO]
    total: int
    limit: int
    offset: int
