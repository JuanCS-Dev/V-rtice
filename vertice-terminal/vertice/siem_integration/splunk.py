"""
Splunk HEC (HTTP Event Collector) Connector
============================================

Sends events to Splunk via HTTP Event Collector API.

Setup:
1. In Splunk: Settings → Data Inputs → HTTP Event Collector
2. Create new token
3. Note the token value and port (usually 8088)

Example:
    connector = SplunkConnector(
        host="splunk.example.com",
        port=8088,
        token="your-hec-token-here",
        index="security"
    )

    event = {
        "event_type": "vulnerability",
        "severity": "high",
        "description": "SQL Injection found",
        "source_ip": "10.10.1.5"
    }

    connector.send_event(event)
"""

import requests
from typing import Dict, Any, Optional
import logging
from .base import SIEMConnector, SIEMConnectionError, SIEMError

logger = logging.getLogger(__name__)


class SplunkConnector(SIEMConnector):
    """Splunk HTTP Event Collector connector."""

    def __init__(
        self,
        host: str,
        port: int = 8088,
        token: str = "",
        index: Optional[str] = None,
        source: str = "vertice",
        sourcetype: str = "vertice:security",
        ssl: bool = True,
        verify_ssl: bool = False,  # Splunk often uses self-signed certs
        **kwargs
    ):
        """
        Initialize Splunk HEC connector.

        Args:
            host: Splunk server hostname
            port: HEC port (default 8088)
            token: HEC authentication token
            index: Target index (optional, uses default if not specified)
            source: Event source identifier
            sourcetype: Event source type
            ssl: Use HTTPS
            verify_ssl: Verify SSL certificates
            **kwargs: Additional options
        """
        super().__init__(host, port, ssl, verify_ssl, **kwargs)

        self.token = token
        self.index = index
        self.source = source
        self.sourcetype = sourcetype

        # HEC endpoint
        self.endpoint = f"{self.base_url}/services/collector/event"

        # Request headers
        self.headers = {
            "Authorization": f"Splunk {self.token}",
            "Content-Type": "application/json"
        }

    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send event to Splunk HEC.

        Args:
            event: Event data dict

        Returns:
            True if successful

        Raises:
            SIEMConnectionError: If connection fails
            SIEMError: If sending fails
        """
        # Build HEC payload
        payload = {
            "source": self.source,
            "sourcetype": self.sourcetype,
            "event": event
        }

        # Add index if specified
        if self.index:
            payload["index"] = self.index

        # Add timestamp if present
        if event.get("timestamp"):
            payload["time"] = event["timestamp"]

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.debug(f"Event sent to Splunk: {response.text}")
                return True
            else:
                logger.error(f"Splunk HEC error: {response.status_code} - {response.text}")
                raise SIEMError(f"Splunk returned {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            raise SIEMConnectionError(f"Timeout connecting to Splunk at {self.endpoint}")
        except requests.exceptions.ConnectionError as e:
            raise SIEMConnectionError(f"Failed to connect to Splunk: {e}")
        except requests.exceptions.RequestException as e:
            raise SIEMError(f"Request failed: {e}")

    def send_batch(self, events: list[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send multiple events to Splunk HEC (optimized batch).

        Splunk HEC supports sending multiple events in one request.

        Args:
            events: List of event dicts

        Returns:
            Statistics: {"sent": N, "failed": M}
        """
        if not events:
            return {"sent": 0, "failed": 0}

        # Build batch payload (newline-separated JSON objects)
        batch_lines = []
        for event in events:
            payload = {
                "source": self.source,
                "sourcetype": self.sourcetype,
                "event": event
            }

            if self.index:
                payload["index"] = self.index

            if event.get("timestamp"):
                payload["time"] = event["timestamp"]

            # Splunk HEC batch format: one JSON object per line
            import json
            batch_lines.append(json.dumps(payload))

        batch_payload = "\n".join(batch_lines)

        try:
            response = requests.post(
                self.endpoint,
                data=batch_payload,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Batch of {len(events)} events sent to Splunk")
                return {"sent": len(events), "failed": 0}
            else:
                logger.error(f"Splunk batch error: {response.status_code} - {response.text}")
                return {"sent": 0, "failed": len(events)}

        except Exception as e:
            logger.error(f"Batch send failed: {e}")
            return {"sent": 0, "failed": len(events)}

    def test_connection(self) -> bool:
        """
        Test connection to Splunk HEC.

        Returns:
            True if connection successful
        """
        # Send minimal test event
        test_event = {
            "event_type": "test",
            "message": "Vértice SIEM connectivity test"
        }

        try:
            result = self.send_event(test_event)
            logger.info("Splunk HEC connection test: SUCCESS")
            return result
        except Exception as e:
            logger.error(f"Splunk HEC connection test failed: {e}")
            return False
