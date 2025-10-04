"""
Event Formatters for SIEM Integration
======================================

Formats Vértice events into SIEM-compatible formats:
- CEF (Common Event Format) - ArcSight, Splunk
- LEEF (Log Event Extended Format) - QRadar
- JSON - Elasticsearch, Splunk HEC

CEF Format:
    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension

Example:
    CEF:0|Vértice|Security Platform|1.0|SQL-001|SQL Injection Found|8|src=10.10.1.5 spt=3306 dst=192.168.1.10

LEEF Format:
    LEEF:Version|Vendor|Product|Version|EventID|
    Key1=Value1<TAB>Key2=Value2

Example:
    LEEF:2.0|Vértice|Security Platform|1.0|SQL-001|
    src=10.10.1.5    spt=3306    dst=192.168.1.10    msg=SQL Injection Found
"""

import json
from typing import Dict, Any
from datetime import datetime


class EventFormatter:
    """Base class for event formatters."""

    def format(self, event: Dict[str, Any]) -> str:
        """Format event to string."""
        raise NotImplementedError


class CEFFormatter(EventFormatter):
    """
    Common Event Format (CEF) formatter.

    Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """

    # CEF severity mapping (0-10)
    SEVERITY_MAP = {
        "critical": 10,
        "high": 8,
        "medium": 5,
        "low": 3,
        "info": 1
    }

    def format(self, event: Dict[str, Any]) -> str:
        """
        Format event as CEF.

        Args:
            event: Event data dict with keys:
                - event_type: Type of event (vulnerability, threat, etc.)
                - severity: Severity level (critical, high, medium, low, info)
                - description: Event description
                - source_ip: Source IP address
                - destination_ip: Destination IP (optional)
                - source_port: Source port (optional)
                - destination_port: Destination port (optional)
                - protocol: Network protocol (optional)
                - additional fields...

        Returns:
            CEF-formatted string
        """
        # CEF Header
        version = "0"
        device_vendor = "Vértice"
        device_product = "Security Platform"
        device_version = "1.0"

        # Signature ID (event type + hash)
        signature_id = event.get("event_type", "GENERIC")

        # Name (description)
        name = event.get("description", "Security Event")[:100]

        # Severity (0-10)
        severity_str = event.get("severity", "info").lower()
        severity = self.SEVERITY_MAP.get(severity_str, 1)

        # Extension fields
        extensions = []

        # Source/destination
        if event.get("source_ip"):
            extensions.append(f"src={event['source_ip']}")
        if event.get("destination_ip"):
            extensions.append(f"dst={event['destination_ip']}")
        if event.get("source_port"):
            extensions.append(f"spt={event['source_port']}")
        if event.get("destination_port"):
            extensions.append(f"dpt={event['destination_port']}")

        # Protocol
        if event.get("protocol"):
            extensions.append(f"proto={event['protocol']}")

        # Message
        if event.get("message"):
            # CEF escaping: | → \|, \ → \\, = → \=
            msg = event["message"].replace("\\", "\\\\").replace("|", "\\|").replace("=", "\\=")
            extensions.append(f"msg={msg}")

        # CVE ID
        if event.get("cve_id"):
            extensions.append(f"cve={event['cve_id']}")

        # Host
        if event.get("host"):
            extensions.append(f"dhost={event['host']}")

        # Timestamp
        if event.get("timestamp"):
            extensions.append(f"rt={event['timestamp']}")
        else:
            extensions.append(f"rt={int(datetime.utcnow().timestamp() * 1000)}")

        # Build CEF string
        header = f"CEF:{version}|{device_vendor}|{device_product}|{device_version}|{signature_id}|{name}|{severity}"
        extension = " ".join(extensions)

        return f"{header}|{extension}"


class LEEFFormatter(EventFormatter):
    """
    Log Event Extended Format (LEEF) formatter.

    Format: LEEF:Version|Vendor|Product|Version|EventID|\tKey1=Value1\tKey2=Value2
    """

    def format(self, event: Dict[str, Any]) -> str:
        """
        Format event as LEEF.

        Args:
            event: Event data dict

        Returns:
            LEEF-formatted string
        """
        # LEEF Header
        version = "2.0"
        vendor = "Vértice"
        product = "Security Platform"
        prod_version = "1.0"
        event_id = event.get("event_type", "GENERIC")

        # Build header
        header = f"LEEF:{version}|{vendor}|{product}|{prod_version}|{event_id}|"

        # Extension fields (tab-separated)
        extensions = []

        # Map common fields
        field_mapping = {
            "source_ip": "src",
            "destination_ip": "dst",
            "source_port": "srcPort",
            "destination_port": "dstPort",
            "protocol": "proto",
            "severity": "sev",
            "description": "devTime",
            "host": "identHostName",
            "cve_id": "cve"
        }

        for event_key, leef_key in field_mapping.items():
            if event.get(event_key):
                # LEEF escaping: \t → \\t, \n → \\n, \ → \\
                value = str(event[event_key]).replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
                extensions.append(f"{leef_key}={value}")

        # Message
        if event.get("message"):
            msg = event["message"].replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")
            extensions.append(f"msg={msg}")

        # Build LEEF string
        return header + "\t".join(extensions)


class JSONFormatter(EventFormatter):
    """
    JSON formatter for Splunk HEC, Elasticsearch, etc.
    """

    def format(self, event: Dict[str, Any]) -> str:
        """
        Format event as JSON.

        Args:
            event: Event data dict

        Returns:
            JSON string
        """
        # Add metadata
        formatted = {
            "source": "vertice",
            "sourcetype": "vertice:security",
            "time": event.get("timestamp") or datetime.utcnow().isoformat(),
            "event": event
        }

        return json.dumps(formatted)
