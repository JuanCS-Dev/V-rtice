"""Maximus Social Engineering Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Social Engineering Service. These schemas ensure
data consistency and provide a clear structure for representing social engineering
campaigns, simulated human targets, and interaction logs.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the social engineering simulation
ecosystem.
"""

from typing import Optional

from pydantic import BaseModel


class CampaignBase(BaseModel):
    """Base model for a social engineering campaign."""

    name: str
    description: str
    scenario: str
    target_group: str


class CampaignCreate(CampaignBase):
    """Model for creating a new social engineering campaign."""

    pass


class Campaign(CampaignBase):
    """Model for a social engineering campaign with ID and status.

    Attributes:
        id (int): Unique identifier for the campaign.
        start_time (str): ISO formatted timestamp of when the campaign started.
        end_time (Optional[str]): ISO formatted timestamp of when the campaign ended.
        status (str): Current status of the campaign (e.g., 'created', 'running').

    Config:
        orm_mode = True
    """

    id: int
    start_time: str
    end_time: Optional[str]
    status: str

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True


class TargetBase(BaseModel):
    """Base model for a simulated human target."""

    name: str
    email: str
    vulnerabilities: str  # JSON string of vulnerabilities
    phishing_susceptibility: int


class TargetCreate(TargetBase):
    """Model for creating a new simulated human target."""

    pass


class Target(TargetBase):
    """Model for a simulated human target with ID.

    Attributes:
        id (int): Unique identifier for the target.

    Config:
        orm_mode = True
    """

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True


class InteractionBase(BaseModel):
    """Base model for a simulated interaction with a target."""

    target_id: int
    action: str
    details: str  # JSON string of interaction details
    successful: bool


class InteractionCreate(InteractionBase):
    """Model for creating a new interaction record."""

    pass


class Interaction(InteractionBase):
    """Model for a simulated interaction with ID and timestamp.

    Attributes:
        id (int): Unique identifier for the interaction.
        campaign_id (int): The ID of the campaign this interaction belongs to.
        timestamp (str): ISO formatted timestamp of the interaction.

    Config:
        orm_mode = True
    """

    id: int
    campaign_id: int
    timestamp: str

    class Config:
        """Configuração para habilitar o modo ORM."""

        orm_mode = True
