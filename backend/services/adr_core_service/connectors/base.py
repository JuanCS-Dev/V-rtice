"""Maximus ADR Core Service - Base Connector Module.

This module defines the abstract base class or interface for all connectors
within the Automated Detection and Response (ADR) service. It establishes a
standard contract that all concrete connector implementations must adhere to,
ensuring consistency and interoperability.

By providing a common interface, this module facilitates the integration of
diverse external security tools and data sources into the Maximus AI system.
It promotes modularity, making it easier to add new connectors or swap existing
ones without affecting the core ADR logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseConnector(ABC):
    """Abstract base class for all connectors in the ADR service.

    Establishes a standard contract that all concrete connector implementations
    must adhere to, ensuring consistency and interoperability.
    """

    @abstractmethod
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initializes the connector with optional configuration.

        Args:
            config (Optional[Dict[str, Any]]): Configuration parameters for the connector.
        """
        pass

    @abstractmethod
    async def connect(self) -> bool:
        """Establishes a connection to the external service.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Closes the connection to the external service.

        Returns:
            bool: True if the disconnection is successful, False otherwise.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the connector.

        Returns:
            Dict[str, Any]: A dictionary containing the status and relevant information.
        """
        pass
