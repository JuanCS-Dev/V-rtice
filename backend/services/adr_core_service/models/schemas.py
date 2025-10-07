"""Maximus ADR Core Service - Data Schemas.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Automated Detection and Response (ADR) service.
These schemas ensure data consistency and provide a clear structure for
representing various entities like incidents, detection results, response actions,
and threat intelligence.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from models.enums import DetectionType, IncidentSeverity, ResponseActionType
from pydantic import BaseModel, Field


class DetectionResult(BaseModel):
    """Represents a single threat detection result.

    Attributes:
        detection_id (str): Unique identifier for the detection.
        event_id (str): Identifier of the original security event.
        timestamp (str): ISO formatted timestamp of when the detection occurred.
        detection_type (DetectionType): The type of threat detected.
        severity (IncidentSeverity): The severity of the detected threat.
        description (str): A brief description of the detection.
        raw_event (Dict[str, Any]): The raw event data that triggered the detection.
        ml_score (Optional[float]): Machine learning threat score (0.0 to 1.0).
    """

    detection_id: str
    event_id: str
    timestamp: str
    detection_type: DetectionType
    severity: IncidentSeverity
    description: str
    raw_event: Dict[str, Any]
    ml_score: Optional[float] = None


class Incident(BaseModel):
    """Represents a security incident, potentially composed of multiple detections.

    Attributes:
        incident_id (str): Unique identifier for the incident.
        title (str): A concise title for the incident.
        description (str): A detailed description of the incident.
        severity (IncidentSeverity): The overall severity of the incident.
        status (str): Current status of the incident (e.g., 'open', 'investigating', 'closed').
        created_at (str): ISO formatted timestamp of when the incident was created.
        updated_at (str): ISO formatted timestamp of the last update.
        detections (List[DetectionResult]): A list of detections associated with this incident.
        affected_assets (List[str]): List of assets (e.g., hostnames, IPs) affected by the incident.
        assigned_to (Optional[str]): User or system assigned to handle the incident.
    """

    incident_id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: str = "open"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    detections: List[DetectionResult] = []
    affected_assets: List[str] = []
    assigned_to: Optional[str] = None


class ResponseAction(BaseModel):
    """Represents an automated response action taken for an incident.

    Attributes:
        action_id (str): Unique identifier for the response action.
        incident_id (str): The ID of the incident this action is associated with.
        action_type (ResponseActionType): The type of action performed.
        timestamp (str): ISO formatted timestamp of when the action was executed.
        status (str): The status of the action (e.g., 'success', 'failed', 'pending').
        details (str): Detailed outcome or message regarding the action.
        parameters (Optional[Dict[str, Any]]): Parameters used to execute the action.
    """

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str
    action_type: ResponseActionType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str
    details: str
    parameters: Optional[Dict[str, Any]] = None


class ThreatIntelData(BaseModel):
    """Represents threat intelligence information for an indicator.

    Attributes:
        indicator (str): The threat indicator (e.g., IP, domain, hash).
        threat_type (str): The type of threat associated with the indicator.
        severity (str): The severity level of the threat.
        description (str): A description of the threat.
        last_updated (str): ISO formatted timestamp of when the intelligence was last updated.
        sources (List[str]): List of threat intelligence sources.
    """

    indicator: str
    threat_type: str
    severity: str
    description: str
    last_updated: str
    sources: List[str]


class IpIntelligenceData(BaseModel):
    """Represents IP address intelligence and geolocation data.

    Attributes:
        ip_address (str): The IP address.
        country (str): Geographic country.
        city (str): Geographic city.
        isp (str): Internet Service Provider.
        reputation (str): Reputation of the IP (e.g., 'Clean', 'Malicious').
        threat_score (float): A numerical threat score for the IP (0.0 to 1.0).
        last_checked (str): ISO formatted timestamp of when the IP was last checked.
    """

    ip_address: str
    country: str
    city: str
    isp: str
    reputation: str
    threat_score: float
    last_checked: str


class PlaybookStep(BaseModel):
    """Represents a single step within a playbook.

    Attributes:
        step_id (str): Unique identifier for the step.
        description (str): Description of the step.
        action (ResponseActionType): The response action to perform.
        parameters (Optional[Dict[str, Any]]): Parameters for the action.
        next_step_on_success (Optional[str]): ID of the next step if current step succeeds.
        next_step_on_failure (Optional[str]): ID of the next step if current step fails.
    """

    step_id: str
    description: str
    action: ResponseActionType
    parameters: Optional[Dict[str, Any]] = None
    next_step_on_success: Optional[str] = None
    next_step_on_failure: Optional[str] = None


class Playbook(BaseModel):
    """Represents an automated response playbook.

    Attributes:
        id (str): Unique identifier for the playbook.
        name (str): Name of the playbook.
        description (str): Description of what the playbook addresses.
        trigger_conditions (Dict[str, Any]): Conditions that trigger this playbook.
        steps (List[PlaybookStep]): Ordered list of steps in the playbook.
    """

    id: str
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    steps: List[PlaybookStep]
