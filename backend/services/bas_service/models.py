"""Maximus BAS Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Breach and Attack Simulation (BAS) service.
These schemas ensure data consistency and provide a clear structure for
representing various entities like attack techniques, simulation configurations,
and attack results.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AttackTechnique(BaseModel):
    """Represents a single attack technique, often mapped to MITRE ATT&CK.

    Attributes:
        id (str): Unique identifier for the technique (e.g., 'T1059').
        name (str): The name of the technique.
        description (str): A description of the technique.
        parameters (List[str]): List of parameters required for the technique.
    """

    id: str
    name: str
    description: str
    parameters: List[str] = []


class SimulationStatus(str, Enum):
    """Enumeration for the status of an attack simulation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AttackResult(BaseModel):
    """Represents the result of a single attack technique execution within a simulation.

    Attributes:
        id (str): Unique identifier for the attack result.
        technique_id (str): The ID of the executed technique.
        timestamp (str): ISO formatted timestamp of when the technique was executed.
        attack_status (str): Status of the attack execution (e.g., 'success', 'failed').
        detection_status (str): Status of detection by defensive controls (e.g., 'detected', 'not_detected').
        response_status (str): Status of response by defensive controls (e.g., 'responded', 'no_response').
        attack_output (Dict[str, Any]): Raw output from the attack execution.
        detection_details (Dict[str, Any]): Details about the detection, if any.
        response_details (Dict[str, Any]): Details about the response, if any.
    """

    id: str
    technique_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    attack_status: str
    detection_status: str
    response_status: str
    attack_output: Dict[str, Any]
    detection_details: Dict[str, Any]
    response_details: Dict[str, Any]


class AttackSimulation(BaseModel):
    """Represents a full attack simulation campaign.

    Attributes:
        id (str): Unique identifier for the simulation.
        attack_scenario (str): The name of the attack scenario.
        target_service (str): The Maximus service or component targeted.
        start_time (str): ISO formatted timestamp of when the simulation started.
        end_time (Optional[str]): ISO formatted timestamp of when the simulation ended.
        status (SimulationStatus): The current status of the simulation.
        techniques_used (List[str]): List of technique IDs used in the simulation.
        results (List[AttackResult]): List of results for each executed technique.
    """

    id: str
    attack_scenario: str
    target_service: str
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    status: SimulationStatus = SimulationStatus.PENDING
    techniques_used: List[str] = []
    results: List[AttackResult] = []
