"""IP Intelligence Connector for enriching threat data.

This module provides a connector to the IP Intelligence Service, which is used
to gather context about IP addresses, such as geolocation, ISP, ASN, and
reputation. This information is used to enrich threat detections.
"""

import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Assuming BaseConnector is in a sibling file, but the provided context
# doesn't show it. If it were, the import would be:
# from .base import BaseConnector 
# For now, we define a placeholder to satisfy the class definition.
class BaseConnector:
    def __init__(self, config):
        pass
    async def enrich(self, data):
        return data

logger = logging.getLogger(__name__)


class IPIntelligenceConnector(BaseConnector):
    """Connects to the IP Intelligence Service to enrich threat data.

    This connector fetches details for IP addresses, including geolocation,
    ISP, ASN, reputation scores, and known open ports. It includes an
    in-memory cache to avoid redundant lookups for the same IP address.

    Attributes:
        base_url (str): The base URL of the IP Intelligence Service.
        client (httpx.AsyncClient): The client for making asynchronous HTTP requests.
        cache (Dict[str, Any]): A simple in-memory cache for IP analysis results.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initializes the IPIntelligenceConnector.

        Args:
            base_url (str, optional): The base URL of the IP Intelligence Service.
                Defaults to "http://localhost:8000".
        """
        # This would call super().__init__(config) in a real scenario
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.cache = {}  # Simple cache to avoid duplicate lookups
        logger.info(f"Initialized IPIntelligenceConnector for URL: {base_url}")

    async def analyze_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """Analyzes a single IP address using the IP Intelligence Service.

        It first checks the local cache for the IP. If not found, it queries
        the service and caches the result upon success.

        Args:
            ip (str): The IP address to analyze.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the enriched IP
                data, or None if the analysis fails.
        """
        if ip in self.cache:
            logger.debug(f"Cache hit for IP: {ip}")
            return self.cache[ip]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/ip/analyze",
                json={"ip": ip}
            )
            response.raise_for_status()
            data = response.json()

            enriched_data = self._format_response(data)
            self.cache[ip] = enriched_data

            logger.info(f"Enriched IP {ip}: {enriched_data.get('geolocation', {}).get('city')}, {enriched_data.get('geolocation', {}).get('country')}")
            return enriched_data

        except httpx.HTTPStatusError as e:
            logger.warning(
                f"IP Intelligence Service returned status {e.response.status_code} for {ip}"
            )
            return None
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to IP Intelligence Service: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while enriching IP {ip}: {e}")
            return None

    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Formats the raw response from the service into a structured dictionary."""
        geo = data.get('geolocation', {})
        asn_raw = geo.get('as', '')
        asn = asn_raw.split(' ')[0] if asn_raw else None

        return {
            'ip': data.get('ip'),
            'source': data.get('source'),
            'timestamp': data.get('timestamp'),
            'geolocation': {
                'country': geo.get('country'),
                'region': geo.get('regionName'),
                'city': geo.get('city'),
                'lat': geo.get('lat'),
                'lon': geo.get('lon'),
                'isp': geo.get('isp'),
                'asn': asn,
            },
            'reputation': data.get('reputation', {}),
            'ptr_record': data.get('ptr_record'),
            'open_ports': data.get('open_ports', []),
            'enriched_at': datetime.utcnow().isoformat(),
            'enriched_by': 'ip_intelligence_service'
        }

    async def enrich_threat_with_ip_context(self, threat: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches a threat detection object with IP intelligence.

        This method extracts all valid IP addresses from a threat object,
        analyzes them, and adds the intelligence data back into the threat's
        `enriched_context`. It also adjusts the threat score based on the
        reputation of the IPs found.

        Args:
            threat (Dict[str, Any]): The threat detection object to enrich.

        Returns:
            Dict[str, Any]: The enriched threat detection object.
        """
        ips_to_analyze = self._extract_ips_from_threat(threat)
        enriched_ips = {}

        for ip in ips_to_analyze:
            ip_data = await self.analyze_ip(ip)
            if ip_data:
                enriched_ips[ip] = ip_data

        if 'enriched_context' not in threat:
            threat['enriched_context'] = {}
        threat['enriched_context']['ip_intelligence'] = enriched_ips

        if enriched_ips:
            self._adjust_threat_score(threat, enriched_ips)

        return threat

    def _extract_ips_from_threat(self, threat: Dict[str, Any]) -> set:
        """Extracts unique IP addresses from a threat object."""
        ips = set()
        source = threat.get('source', '')
        if self._is_valid_ip(source):
            ips.add(source)

        for indicator in threat.get('indicators', []):
            potential_ip = self._extract_ip_from_indicator(str(indicator))
            if potential_ip:
                ips.add(potential_ip)
        return ips

    def _adjust_threat_score(self, threat: Dict[str, Any], enriched_ips: Dict[str, Any]):
        """Adjusts the threat score based on IP reputation."""
        reputation_scores = [
            ip_data.get('reputation', {}).get('score', 0)
            for ip_data in enriched_ips.values()
        ]
        if not reputation_scores:
            return

        worst_score = max(reputation_scores)
        original_score = threat.get('threat_score', 0)
        # Weighted average: 50% original, 50% IP reputation
        adjusted_score = int((original_score + worst_score) / 2)

        threat['threat_score_original'] = original_score
        threat['threat_score'] = adjusted_score
        threat['threat_score_adjusted_by'] = 'ip_reputation'

        logger.info(f"Threat score adjusted: {original_score} -> {adjusted_score} based on IP reputation.")

    def _is_valid_ip(self, text: str) -> bool:
        """Validates if a given string is a well-formed IPv4 address."""
        import re
        ipv4_pattern = r'^(?:\d{1,3}\.){3}\d{1,3}$'
        return bool(re.match(ipv4_pattern, text))

    def _extract_ip_from_indicator(self, indicator: str) -> Optional[str]:
        """Extracts the first valid IPv4 address found in a string."""
        import re
        ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        match = re.search(ipv4_pattern, indicator)
        return match.group(0) if match else None

    async def get_my_ip(self) -> Optional[str]:
        """Detects the public IP address of the server running the service."""
        try:
            response = await self.client.get(f"{self.base_url}/api/ip/my-ip")
            response.raise_for_status()
            data = response.json()
            return data.get('detected_ip')
        except Exception as e:
            logger.error(f"Failed to get public IP address: {e}")
            return None

    async def close(self):
        """Closes the asynchronous HTTP client session."""
        await self.client.aclose()
        logger.info("IPIntelligenceConnector client closed.")

    async def enrich(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriches threat data. This is the implementation of the abstract method."""
        return await self.enrich_threat_with_ip_context(data)