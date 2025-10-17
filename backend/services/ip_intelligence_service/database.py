"""Maximus IP Intelligence Service - Database Module.

This module provides a simplified, in-memory database simulation for storing
and retrieving IP intelligence data within the Maximus IP Intelligence Service.
In a production environment, this would typically be replaced by a persistent
database solution (e.g., PostgreSQL, MongoDB, Redis).

Key functionalities include:
- Storing IP intelligence records.
- Retrieving IP information by address.
- Updating existing IP records.

This module facilitates quick lookups and caching of IP intelligence data,
reducing reliance on external API calls and improving response times for
IP-related queries.
"""

from typing import Dict, Optional

from backend.services.ip_intelligence_service.models import IPInfo

# In-memory database for IP intelligence (mock)
ip_intelligence_db: Dict[str, IPInfo] = {}


async def get_ip_data(ip_address: str) -> Optional[IPInfo]:
    """Retrieves IP intelligence data from the in-memory database.

    Args:
        ip_address (str): The IP address to retrieve.

    Returns:
        Optional[IPInfo]: The IPInfo object if found, None otherwise.
    """
    return ip_intelligence_db.get(ip_address)


async def update_ip_data(ip_info: IPInfo):
    """Updates or adds IP intelligence data to the in-memory database.

    Args:
        ip_info (IPInfo): The IPInfo object to store or update.
    """
    ip_intelligence_db[ip_info.ip_address] = ip_info
