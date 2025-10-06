"""Maximus Social Engineering Service - Pydantic Schemas.

This module defines the Pydantic schemas for data validation and serialization
within the Social Engineering Service. These schemas are used for API request
and response models, ensuring data consistency and clear documentation of
data structures.

It mirrors the SQLAlchemy models defined in `database.py` but is specifically
designed for data validation and serialization, providing a clean separation
between database models and API models.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CampaignBase(BaseModel):
    """Base Pydantic model for a social engineering campaign."""

    name: str
    description: str
    scenario: str
    target_group: str


class CampaignCreate(CampaignBase):
    """Pydantic model for creating a new social engineering campaign."""

    pass


class Campaign(CampaignBase):
    """Pydantic model for a social engineering campaign, including database-generated fields.

    Attributes:
        id (int): Unique identifier for the campaign.
        start_time (datetime): Timestamp of when the campaign started.
        end_time (Optional[datetime]): Timestamp of when the campaign ended.
        status (str): Current status of the campaign (e.g., 'created', 'running').

    Config:
        orm_mode = True
    """

    id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: str

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True


class TargetBase(BaseModel):
    """Base Pydantic model for a simulated human target."""

    name: str
    email: str
    vulnerabilities: str  # JSON string of vulnerabilities
    phishing_susceptibility: int


class TargetCreate(TargetBase):
    """Pydantic model for creating a new simulated human target."""

    pass


class Target(TargetBase):
    """Pydantic model for a simulated human target, including database-generated fields.

    Attributes:
        id (int): Unique identifier for the target.

    Config:
        orm_mode = True
    """

    id: int

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True


class InteractionBase(BaseModel):
    """Base Pydantic model for a simulated interaction with a target."""

    target_id: int
    action: str
    details: str  # JSON string of interaction details
    successful: bool


class InteractionCreate(InteractionBase):
    """Pydantic model for creating a new interaction record."""

    pass


class Interaction(InteractionBase):
    """Pydantic model for a simulated interaction, including database-generated fields.

    Attributes:
        id (int): Unique identifier for the interaction.
        campaign_id (int): The ID of the campaign this interaction belongs to.
        timestamp (datetime): Timestamp of the interaction.

    Config:
        orm_mode = True
    """

    id: int
    campaign_id: int
    timestamp: datetime

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True
