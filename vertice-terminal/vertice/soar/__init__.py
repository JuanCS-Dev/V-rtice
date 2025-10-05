"""
🔗 SOAR Integration Layer
Conecta Vértice com plataformas SOAR/XDR usando Adapter Pattern

Plataformas suportadas:
- Splunk SOAR (Phantom)
- Microsoft Sentinel
- Palo Alto Cortex XSOAR
- IBM Resilient
"""

from .base import SOARConnector, Incident, IncidentSeverity, IncidentStatus
from .splunk_soar import SplunkSOARConnector
from .sentinel import SentinelConnector

__all__ = [
    "SOARConnector",
    "Incident",
    "IncidentSeverity",
    "IncidentStatus",
    "SplunkSOARConnector",
    "SentinelConnector",
]
