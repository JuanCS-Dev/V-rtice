"""Maximus HCL Analyzer Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Homeostatic Control Loop (HCL) Analyzer service.
These schemas ensure data consistency and provide a clear structure for
representing various entities like system metrics, analysis results, and anomaly
details.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class AnomalyType(str, Enum):
    """Enumeration for different types of anomalies detected."""

    SPIKE = "spike"
    DROP = "drop"
    TREND = "trend"
    OUTLIER = "outlier"


class Anomaly(BaseModel):
    """Represents a detected anomaly in system metrics.

    Attributes:
        type (AnomalyType): The type of anomaly.
        metric_name (str): The name of the metric where the anomaly was detected.
        current_value (float): The current value of the metric.
        severity (float): The severity of the anomaly (0.0 to 1.0).
        description (str): A human-readable description of the anomaly.
    """

    type: AnomalyType
    metric_name: str
    current_value: float
    severity: float
    description: str


class AnalysisResult(BaseModel):
    """Represents the comprehensive analysis of system resources and health.

    Attributes:
        timestamp (str): ISO formatted timestamp of the analysis.
        overall_health_score (float): An aggregated score representing system health (0.0 to 1.0).
        anomalies (List[Anomaly]): A list of detected anomalies.
        trends (Dict[str, Any]): Identified trends in system metrics.
        recommendations (List[str]): Suggested actions based on the analysis.
        requires_intervention (bool): True if the analysis indicates a need for intervention.
    """

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    overall_health_score: float
    anomalies: List[Anomaly]
    trends: Dict[str, Any]
    recommendations: List[str]
    requires_intervention: bool


class SystemMetrics(BaseModel):
    """Represents a snapshot of system metrics collected by the HCL Monitor.

    Attributes:
        timestamp (str): ISO formatted timestamp of when the metrics were collected.
        cpu_usage (float): Current CPU utilization (0-100%).
        memory_usage (float): Current memory utilization (0-100%).
        disk_io_rate (float): Disk I/O rate (bytes/sec).
        network_io_rate (float): Network I/O rate (bytes/sec).
        avg_latency_ms (float): Average system latency in milliseconds.
        error_rate (float): Rate of errors in the system.
        service_status (Dict[str, str]): Status of various sub-services.
    """

    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_io_rate: float
    network_io_rate: float
    avg_latency_ms: float
    error_rate: float
    service_status: Dict[str, str]
