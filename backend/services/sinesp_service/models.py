"""Maximus Sinesp Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Sinesp Service. These schemas ensure data consistency
and provide a clear structure for representing Sinesp queries, vehicle information,
and other public security-related data.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the Sinesp integration ecosystem.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class SinespQueryType(str, Enum):
    """Enumeration for different types of Sinesp queries."""
    PLATE = "plate"
    CHASSIS = "chassis"


class SinespQuery(BaseModel):
    """Represents a query to the Sinesp Cidadão API.

    Attributes:
        identifier (str): The identifier to query (e.g., vehicle plate, chassis number).
        query_type (SinespQueryType): The type of query.
    """
    identifier: str
    query_type: SinespQueryType


class VehicleInfo(BaseModel):
    """Represents detailed vehicle information retrieved from Sinesp.

    Attributes:
        plate (str): The vehicle's license plate.
        model (str): The vehicle model.
        color (str): The vehicle color.
        year (int): The manufacturing year of the vehicle.
        city (str): The city where the vehicle is registered.
        state (str): The state where the vehicle is registered.
        stolen (bool): True if the vehicle is reported stolen, False otherwise.
        last_updated (str): ISO formatted timestamp of when the information was last updated.
        additional_info (Optional[Dict[str, Any]]): Any additional information from Sinesp.
    """
    plate: str
    model: str
    color: str
    year: int
    city: str
    state: str
    stolen: bool
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    additional_info: Optional[Dict[str, Any]] = None