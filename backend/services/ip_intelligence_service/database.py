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

from models import IPInfo

# In-memory database for IP intelligence (mock)
ip_intelligence_db: Dict[str, IPInfo] = {}


async def get_ip_data(ip_address: str) -> Optional[IPInfo]:
    """Retrieves IP intelligence data from cache or performs live lookup.

    Args:
        ip_address (str): The IP address to retrieve.

    Returns:
        Optional[IPInfo]: The IPInfo object with geolocation data.
    """
    import httpx
    from datetime import datetime
    
    # Check cache first
    cached = ip_intelligence_db.get(ip_address)
    if cached:
        return cached
    
    # Perform live lookup using ip-api.com (free, no auth)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip_address}")
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data.get("status") == "fail":
                return None
            
            # Create IPInfo from response
            ip_info = IPInfo(
                ip_address=ip_address,
                country=data.get("country", "Unknown"),
                city=data.get("city", "Unknown"),
                isp=data.get("isp", "Unknown"),
                organization=data.get("org", "Unknown"),
                latitude=data.get("lat", 0.0),
                longitude=data.get("lon", 0.0),
                reputation="low",  # Default reputation
                threat_score=0,     # Default threat score
                threat_level="low",  # Default threat level
                last_seen=datetime.utcnow().isoformat(),
                last_checked=datetime.utcnow().isoformat(),
            )
            
            # Cache for future requests
            ip_intelligence_db[ip_address] = ip_info
            
            return ip_info
            
    except Exception as e:
        print(f"[ERROR] Failed to lookup IP {ip_address}: {e}")
        return None


async def update_ip_data(ip_info: IPInfo):
    """Updates or adds IP intelligence data to the in-memory database.

    Args:
        ip_info (IPInfo): The IPInfo object to store or update.
    """
    ip_intelligence_db[ip_info.ip_address] = ip_info
