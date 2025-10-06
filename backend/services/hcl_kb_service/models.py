"""Maximus HCL Knowledge Base Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Homeostatic Control Loop (HCL) Knowledge Base
Service. These schemas ensure data consistency and provide a clear structure
for representing various types of HCL-related data.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the HCL ecosystem.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HCLDataType(str, Enum):
    """Enumeration for different types of HCL data stored in the knowledge base."""

    METRICS = "metrics"
    ANALYSIS = "analysis"
    PLAN = "plan"
    EXECUTION = "execution"
    POLICY = "policy"
    EVENT = "event"


class HCLDataEntry(BaseModel):
    """Represents a single entry of HCL-related data in the knowledge base.

    Attributes:
        timestamp (str): ISO formatted timestamp of when the data was recorded.
        data_type (HCLDataType): The type of HCL data.
        data (Dict[str, Any]): The actual data payload.
        metadata (Optional[Dict[str, Any]]): Optional metadata associated with the entry.
    """

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_type: HCLDataType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
