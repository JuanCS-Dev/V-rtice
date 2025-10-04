"""
Elasticsearch Connector
=======================

Sends events to Elasticsearch for indexing and analysis.

Setup:
1. Elasticsearch running on host:port
2. Optional: API key or basic auth credentials
3. Create index template (optional but recommended)

Example:
    connector = ElasticsearchConnector(
        host="elasticsearch.example.com",
        port=9200,
        index="vertice-security",
        username="elastic",
        password="your-password"
    )

    event = {
        "event_type": "vulnerability",
        "severity": "high",
        "description": "SQL Injection found",
        "source_ip": "10.10.1.5",
        "timestamp": "2024-01-10T15:30:00Z"
    }

    connector.send_event(event)
"""

import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from .base import SIEMConnector, SIEMConnectionError, SIEMError

logger = logging.getLogger(__name__)


class ElasticsearchConnector(SIEMConnector):
    """Elasticsearch REST API connector."""

    def __init__(
        self,
        host: str,
        port: int = 9200,
        index: str = "vertice-security",
        username: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        ssl: bool = False,
        verify_ssl: bool = True,
        **kwargs
    ):
        """
        Initialize Elasticsearch connector.

        Args:
            host: Elasticsearch hostname
            port: Elasticsearch port (default 9200)
            index: Target index name
            username: Basic auth username (optional)
            password: Basic auth password (optional)
            api_key: API key for authentication (optional, preferred over basic auth)
            ssl: Use HTTPS
            verify_ssl: Verify SSL certificates
            **kwargs: Additional options
        """
        super().__init__(host, port, ssl, verify_ssl, **kwargs)

        self.index = index
        self.username = username
        self.password = password
        self.api_key = api_key

        # Build auth
        self.auth = None
        self.headers = {"Content-Type": "application/json"}

        if api_key:
            # API key auth (preferred)
            self.headers["Authorization"] = f"ApiKey {api_key}"
        elif username and password:
            # Basic auth
            self.auth = (username, password)

        # Endpoints
        self.index_endpoint = f"{self.base_url}/{self.index}/_doc"
        self.bulk_endpoint = f"{self.base_url}/_bulk"
        self.health_endpoint = f"{self.base_url}/_cluster/health"

    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send event to Elasticsearch.

        Args:
            event: Event data dict

        Returns:
            True if successful

        Raises:
            SIEMConnectionError: If connection fails
            SIEMError: If indexing fails
        """
        # Ensure timestamp
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat()

        # Add metadata
        event["@timestamp"] = event.get("timestamp")
        event["source"] = "vertice"

        try:
            response = requests.post(
                self.index_endpoint,
                json=event,
                headers=self.headers,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.debug(f"Event indexed in Elasticsearch: {result.get('_id')}")
                return True
            else:
                logger.error(f"Elasticsearch error: {response.status_code} - {response.text}")
                raise SIEMError(f"Elasticsearch returned {response.status_code}: {response.text}")

        except requests.exceptions.Timeout:
            raise SIEMConnectionError(f"Timeout connecting to Elasticsearch at {self.index_endpoint}")
        except requests.exceptions.ConnectionError as e:
            raise SIEMConnectionError(f"Failed to connect to Elasticsearch: {e}")
        except requests.exceptions.RequestException as e:
            raise SIEMError(f"Request failed: {e}")

    def send_batch(self, events: list[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send multiple events to Elasticsearch using bulk API.

        Args:
            events: List of event dicts

        Returns:
            Statistics: {"sent": N, "failed": M}
        """
        if not events:
            return {"sent": 0, "failed": 0}

        # Build bulk request (newline-delimited JSON)
        bulk_lines = []

        for event in events:
            # Ensure timestamp
            if "timestamp" not in event:
                event["timestamp"] = datetime.utcnow().isoformat()

            event["@timestamp"] = event.get("timestamp")
            event["source"] = "vertice"

            # Action line
            action = {"index": {"_index": self.index}}
            bulk_lines.append(action)

            # Document line
            bulk_lines.append(event)

        # Convert to newline-delimited JSON
        import json
        bulk_payload = "\n".join(json.dumps(line) for line in bulk_lines) + "\n"

        try:
            response = requests.post(
                self.bulk_endpoint,
                data=bulk_payload,
                headers=self.headers,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()

                # Count successes and failures
                items = result.get("items", [])
                sent = sum(1 for item in items if item.get("index", {}).get("status") in (200, 201))
                failed = len(items) - sent

                logger.info(f"Bulk indexed {sent}/{len(events)} events to Elasticsearch")
                return {"sent": sent, "failed": failed}
            else:
                logger.error(f"Elasticsearch bulk error: {response.status_code} - {response.text}")
                return {"sent": 0, "failed": len(events)}

        except Exception as e:
            logger.error(f"Bulk send failed: {e}")
            return {"sent": 0, "failed": len(events)}

    def test_connection(self) -> bool:
        """
        Test connection to Elasticsearch.

        Returns:
            True if connection successful
        """
        try:
            response = requests.get(
                self.health_endpoint,
                headers=self.headers,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code == 200:
                health = response.json()
                logger.info(f"Elasticsearch connection test: SUCCESS - Cluster: {health.get('cluster_name')}, Status: {health.get('status')}")
                return True
            else:
                logger.error(f"Elasticsearch health check failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Elasticsearch connection test failed: {e}")
            return False

    def create_index_template(self) -> bool:
        """
        Create index template for Vértice events (optional but recommended).

        Returns:
            True if successful
        """
        template = {
            "index_patterns": [f"{self.index}-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                },
                "mappings": {
                    "properties": {
                        "@timestamp": {"type": "date"},
                        "timestamp": {"type": "date"},
                        "source": {"type": "keyword"},
                        "event_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "description": {"type": "text"},
                        "source_ip": {"type": "ip"},
                        "destination_ip": {"type": "ip"},
                        "host": {"type": "keyword"},
                        "cve_id": {"type": "keyword"},
                        "port": {"type": "integer"}
                    }
                }
            }
        }

        try:
            endpoint = f"{self.base_url}/_index_template/vertice-security-template"
            response = requests.put(
                endpoint,
                json=template,
                headers=self.headers,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info("Elasticsearch index template created successfully")
                return True
            else:
                logger.warning(f"Failed to create index template: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to create index template: {e}")
            return False
