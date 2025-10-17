"""
Application Layer - DTOs (Data Transfer Objects)

Input/Output schemas for use cases.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateEntityDTO(BaseModel):
    """Input DTO for creating entity."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class UpdateEntityDTO(BaseModel):
    """Input DTO for updating entity."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class EntityDTO(BaseModel):
    """Output DTO for entity."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    status: str
    extra_data: dict[str, str]
    created_at: datetime
    updated_at: datetime


class PaginatedEntitiesDTO(BaseModel):
    """Output DTO for paginated entities."""

    items: list[EntityDTO]
    total: int
    limit: int
    offset: int
