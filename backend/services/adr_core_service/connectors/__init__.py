"""ADR Core Service - Connectors Package.

This package contains modules for connecting to external intelligence and analysis
services. Each connector is responsible for communicating with a specific
external API to enrich threat data.

This `__init__.py` file exports the primary connector classes for easy access.
"""

from .base import BaseConnector
from .ip_intelligence_connector import IPIntelligenceConnector
from .threat_intel_connector import ThreatIntelConnector
from .malware_analysis import MalwareAnalysisConnector

__all__ = [
    'BaseConnector',
    'IPIntelligenceConnector',
    'ThreatIntelConnector',
    'MalwareAnalysisConnector'
]