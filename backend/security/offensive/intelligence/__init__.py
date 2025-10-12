"""
Intelligence Module
==================

OSINT and threat intelligence gathering for offensive operations.

Components:
    - OSINT Collector: Open-source intelligence aggregation
    - Threat Intel: Threat intelligence integration
    - Target Profiler: Target analysis and profiling
    - Credential Harvester: Credential discovery
    - Data Exfiltrator: Sensitive data extraction
"""

from .exfiltration import (
    DataExfiltrator,
    DataClassification,
    ExfiltrationMethod,
    FileMetadata,
    ExfiltrationResult
)

__all__ = [
    "DataExfiltrator",
    "DataClassification",
    "ExfiltrationMethod",
    "FileMetadata",
    "ExfiltrationResult"
]
