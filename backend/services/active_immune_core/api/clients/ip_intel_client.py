"""
IP Intelligence Service client.

Integrates with Maximus IP Intelligence Service
for IP reputation and geo-location data.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from typing import Any, Dict, Optional

from .base_client import BaseExternalClient

logger = logging.getLogger(__name__)


class IPIntelClient(BaseExternalClient):
    """
    Client for IP Intelligence Service.

    Provides:
    - IP reputation lookups
    - Geo-location data
    - Threat intelligence for IPs
    - Blacklist/whitelist checks

    Graceful degradation:
    - Falls back to local IP cache
    - Returns "unknown" for unavailable data
    - Simple threat categorization
    """

    def __init__(self, base_url: str = "http://localhost:8022", **kwargs):
        """
        Initialize IP Intelligence client.

        Args:
            base_url: IP Intelligence Service base URL
            **kwargs: Additional BaseExternalClient arguments
        """
        super().__init__(base_url=base_url, **kwargs)

        # Local IP cache (for degraded mode)
        self._local_ip_cache: Dict[str, Dict[str, Any]] = {}
        self._local_known_threats = {
            # Common malicious IP ranges (simplified)
            "0.0.0.0": True,
            "127.0.0.1": False,
            "localhost": False,
        }

    async def lookup_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Lookup IP address information.

        Args:
            ip_address: IP address to lookup

        Returns:
            IP information including reputation, geo-location, etc.
        """
        return await self.request("GET", f"/ip/{ip_address}")

    async def check_reputation(self, ip_address: str) -> Dict[str, Any]:
        """
        Check IP reputation.

        Args:
            ip_address: IP address to check

        Returns:
            Reputation score and classification
        """
        return await self.request("GET", f"/reputation/{ip_address}")

    async def batch_lookup(self, ip_addresses: list[str]) -> Dict[str, Any]:
        """
        Batch lookup multiple IPs.

        Args:
            ip_addresses: List of IP addresses

        Returns:
            Lookup results for all IPs
        """
        return await self.request("POST", "/batch_lookup", json={"ip_addresses": ip_addresses})

    async def degraded_fallback(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Fallback to local IP intelligence.

        When IP Intel service is unavailable:
        - Use local IP cache
        - Simple threat categorization
        - Conservative reputation scores

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Request kwargs

        Returns:
            Synthetic degraded response
        """
        logger.warning(f"IPIntelClient: Operating in degraded mode for {method} {endpoint}")

        # Parse endpoint
        if endpoint.startswith("/ip/"):
            # IP lookup
            ip_address = endpoint.split("/")[-1]

            # Check local cache
            if ip_address in self._local_ip_cache:
                cached = self._local_ip_cache[ip_address]
                cached["degraded_mode"] = True
                return cached

            # Generate synthetic response
            is_threat = ip_address in self._local_known_threats

            response = {
                "status": "degraded",
                "ip_address": ip_address,
                "reputation": "unknown",
                "threat_level": "medium" if is_threat else "low",
                "geo_location": {
                    "country": "unknown",
                    "city": "unknown",
                    "latitude": 0.0,
                    "longitude": 0.0,
                },
                "is_malicious": is_threat,
                "confidence": 0.3,  # Low confidence
                "degraded_mode": True,
            }

            # Cache for future use
            self._local_ip_cache[ip_address] = response

            return response

        elif endpoint.startswith("/reputation/"):
            # Reputation check
            ip_address = endpoint.split("/")[-1]

            is_threat = ip_address in self._local_known_threats

            return {
                "status": "degraded",
                "ip_address": ip_address,
                "reputation_score": 0.5,  # Neutral
                "category": "unknown",
                "is_malicious": is_threat,
                "confidence": 0.3,
                "degraded_mode": True,
            }

        elif endpoint == "/batch_lookup":
            # Batch lookup
            json_data = kwargs.get("json", {})
            ip_addresses = json_data.get("ip_addresses", [])

            results = {}
            for ip in ip_addresses:
                results[ip] = {
                    "reputation": "unknown",
                    "threat_level": "medium",
                    "is_malicious": False,
                    "degraded_mode": True,
                }

            return {
                "status": "degraded",
                "results": results,
                "count": len(ip_addresses),
                "degraded_mode": True,
            }

        else:
            return {
                "status": "degraded",
                "error": f"unknown_endpoint_{endpoint}",
                "degraded_mode": True,
            }
