"""
SIEM Integration Module
=======================

Connects Vértice findings to external SIEM systems for centralized monitoring.

Supported SIEM Systems:
- Splunk (HEC - HTTP Event Collector)
- Elasticsearch (REST API)
- QRadar (Syslog CEF)
- Generic Syslog (CEF/LEEF format)

Event Normalization:
- CEF (Common Event Format) - ArcSight standard
- LEEF (Log Event Extended Format) - QRadar standard
- JSON - Splunk/Elasticsearch native

Usage:
    from vertice.siem_integration import SplunkConnector, CEFFormatter

    # Send to Splunk
    splunk = SplunkConnector(
        host="splunk.example.com",
        port=8088,
        token="your-hec-token"
    )

    event = {
        "source": "vertice",
        "severity": "high",
        "description": "SQL Injection vulnerability found",
        "host": "10.10.1.5",
        "port": 3306
    }

    splunk.send_event(event)
"""

from .base import SIEMConnector, SIEMError, SIEMConnectionError
from .formatters import CEFFormatter, LEEFFormatter, JSONFormatter
from .splunk import SplunkConnector
from .elasticsearch import ElasticsearchConnector

__all__ = [
    "SIEMConnector",
    "SIEMError",
    "SIEMConnectionError",
    "CEFFormatter",
    "LEEFFormatter",
    "JSONFormatter",
    "SplunkConnector",
    "ElasticsearchConnector"
]
