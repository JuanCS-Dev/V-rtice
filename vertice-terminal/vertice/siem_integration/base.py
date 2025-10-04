"""
SIEM Connector Base Classes
============================

Abstract base classes for SIEM integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SIEMError(Exception):
    """Base exception for SIEM-related errors."""
    pass


class SIEMConnectionError(SIEMError):
    """Error connecting to SIEM system."""
    pass


class SIEMConnector(ABC):
    """
    Abstract base class for SIEM connectors.

    All SIEM connectors must implement:
    - send_event(): Send single event
    - send_batch(): Send multiple events
    - test_connection(): Verify connectivity
    """

    def __init__(
        self,
        host: str,
        port: int,
        ssl: bool = True,
        verify_ssl: bool = True,
        timeout: int = 30,
        **kwargs
    ):
        """
        Initialize SIEM connector.

        Args:
            host: SIEM server hostname/IP
            port: SIEM server port
            ssl: Use SSL/TLS
            verify_ssl: Verify SSL certificates
            timeout: Request timeout in seconds
            **kwargs: Additional connector-specific options
        """
        self.host = host
        self.port = port
        self.ssl = ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout

        # Build base URL
        protocol = "https" if ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}"

        logger.info(f"Initialized {self.__class__.__name__} for {self.base_url}")

    @abstractmethod
    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send single event to SIEM.

        Args:
            event: Event data dict

        Returns:
            True if successful, False otherwise

        Raises:
            SIEMConnectionError: If connection fails
            SIEMError: If sending fails
        """
        pass

    def send_batch(self, events: list[Dict[str, Any]]) -> Dict[str, int]:
        """
        Send multiple events to SIEM.

        Default implementation sends events one by one.
        Override for batch-optimized implementations.

        Args:
            events: List of event dicts

        Returns:
            Statistics dict: {"sent": N, "failed": M}
        """
        stats = {"sent": 0, "failed": 0}

        for event in events:
            try:
                if self.send_event(event):
                    stats["sent"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Failed to send event: {e}")
                stats["failed"] += 1

        return stats

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to SIEM system.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    def format_event(self, event: Dict[str, Any], format: str = "json") -> str:
        """
        Format event for SIEM ingestion.

        Args:
            event: Raw event data
            format: Output format (json, cef, leef)

        Returns:
            Formatted event string
        """
        from .formatters import CEFFormatter, LEEFFormatter, JSONFormatter

        if format == "cef":
            formatter = CEFFormatter()
        elif format == "leef":
            formatter = LEEFFormatter()
        else:
            formatter = JSONFormatter()

        return formatter.format(event)
