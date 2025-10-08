"""Maximus ADR Core Service - Enumerations.

This module defines enumerations (Enums) used throughout the Automated Detection
and Response (ADR) service. These enums provide a standardized set of predefined
values for various attributes, ensuring data consistency and improving code
readability.

Enums defined in this module include:
- `IncidentSeverity`: Levels of severity for security incidents.
- `DetectionType`: Categories of detected threats or anomalies.
- `ResponseActionType`: Types of automated response actions that can be taken.

Using enums helps prevent errors from typos or inconsistent string values and
facilitates clearer communication within the ADR system.
"""

from enum import Enum


class IncidentSeverity(str, Enum):
    """Enumeration for the severity levels of security incidents."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionType(str, Enum):
    """Enumeration for different types of threat detections."""

    MALWARE = "malware"
    ANOMALY = "anomaly"
    NETWORK_SCAN = "network_scan"
    BRUTE_FORCE = "brute_force"
    DATA_EXFILTRATION = "data_exfiltration"
    PHISHING = "phishing"
    UNKNOWN = "unknown"


class ResponseActionType(str, Enum):
    """Enumeration for different types of automated response actions."""

    ISOLATE_HOST = "isolate_host"
    BLOCK_IP = "block_ip"
    TERMINATE_PROCESS = "terminate_process"
    COLLECT_FORENSICS = "collect_forensics"
    NOTIFY_SOC = "notify_soc"
    DISABLE_USER = "disable_user"
    QUARANTINE_FILE = "quarantine_file"
