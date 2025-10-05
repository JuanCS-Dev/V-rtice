"""Maximus ADR Core Service - Connectors Package.

This package contains modules for connecting the Automated Detection and
Response (ADR) service to various external systems and data sources.
These connectors enable Maximus AI to ingest threat intelligence, query IP
reputation, and interact with other security tools.

Modules within this package include:
- `base`: Provides a base class or interface for all connectors.
- `threat_intel_connector`: Integrates with external threat intelligence platforms.
- `ip_intelligence_connector`: Queries IP address reputation and contextual data.
- `malware_analysis`: Connects to malware analysis sandboxes or services.

These connectors are crucial for enriching security event data, providing
context for detections, and enabling comprehensive response actions.
"""
