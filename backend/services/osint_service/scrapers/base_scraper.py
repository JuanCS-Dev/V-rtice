"""Maximus OSINT Service - Base Scraper Module.

This module defines the abstract base class or interface for all scrapers
within the Maximus AI's OSINT Service. It establishes a standard contract
that all concrete scraper implementations must adhere to, ensuring consistency
and interoperability.

By providing a common interface, this module facilitates the integration of
diverse data collection methods from various open-source platforms. It promotes
modularity, making it easier to add new scrapers or swap existing ones without
affecting the core OSINT orchestration logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseScraper(ABC):
    """Abstract base class for all scrapers in the OSINT service.

    Establishes a standard contract that all concrete scraper implementations
    must adhere to, ensuring consistency and interoperability.
    """

    @abstractmethod
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initializes the scraper with optional configuration.

        Args:
            config (Optional[Dict[str, Any]]): Configuration parameters for the scraper.
        """
        pass

    @abstractmethod
    async def scrape(self, query: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Performs a scraping operation based on a query.

        Args:
            query (str): The query string for the scraping operation.
            depth (int): The depth of the scraping (e.g., number of pages, levels of links).

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a scraped data entry.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the scraper.

        Returns:
            Dict[str, Any]: A dictionary containing the status and relevant information.
        """
        pass