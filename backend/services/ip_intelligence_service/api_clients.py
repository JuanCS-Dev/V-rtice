"""External API integrations for IP Intelligence Service."""

import os
from datetime import datetime
from typing import Optional

import httpx

from models import IPInfo


class AbuseIPDBClient:
    """Client for AbuseIPDB API."""
    
    def __init__(self):
        self.api_key = os.getenv("ABUSEIPDB_API_KEY", "")
        self.base_url = "https://api.abuseipdb.com/api/v2"
        self.enabled = bool(self.api_key)
    
    async def check_ip(self, ip_address: str) -> Optional[IPInfo]:
        """Check IP reputation via AbuseIPDB."""
        if not self.enabled:
            return None
        
        headers = {
            "Key": self.api_key,
            "Accept": "application/json"
        }
        params = {
            "ipAddress": ip_address,
            "maxAgeInDays": "90"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/check",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()["data"]
                
                abuse_score = data.get("abuseConfidenceScore", 0)
                threat_score = abuse_score / 100.0
                reputation = "Malicious" if abuse_score > 50 else "Suspicious" if abuse_score > 20 else "Clean"
                
                return IPInfo(
                    ip_address=ip_address,
                    country=data.get("countryCode", "Unknown"),
                    city="Unknown",  # AbuseIPDB doesn't provide city
                    isp=data.get("isp", "Unknown"),
                    reputation=reputation,
                    threat_score=threat_score,
                    last_checked=datetime.now().isoformat()
                )
        except Exception as e:
            print(f"[AbuseIPDB] Error checking IP {ip_address}: {e}")
            return None


class VirusTotalClient:
    """Client for VirusTotal API."""
    
    def __init__(self):
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY", "")
        self.base_url = "https://www.virustotal.com/api/v3"
        self.enabled = bool(self.api_key)
    
    async def check_ip(self, ip_address: str) -> Optional[IPInfo]:
        """Check IP reputation via VirusTotal."""
        if not self.enabled:
            return None
        
        headers = {
            "x-apikey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/ip_addresses/{ip_address}",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()["data"]["attributes"]
                
                malicious = data.get("last_analysis_stats", {}).get("malicious", 0)
                suspicious = data.get("last_analysis_stats", {}).get("suspicious", 0)
                total = sum(data.get("last_analysis_stats", {}).values()) or 1
                
                threat_score = (malicious + suspicious * 0.5) / total
                reputation = "Malicious" if malicious > 5 else "Suspicious" if malicious > 0 else "Clean"
                
                return IPInfo(
                    ip_address=ip_address,
                    country=data.get("country", "Unknown"),
                    city="Unknown",  # VT doesn't provide city
                    isp=data.get("as_owner", "Unknown"),
                    reputation=reputation,
                    threat_score=threat_score,
                    last_checked=datetime.now().isoformat()
                )
        except Exception as e:
            print(f"[VirusTotal] Error checking IP {ip_address}: {e}")
            return None


class IPGeolocationClient:
    """Fallback client for IP geolocation using ipapi.co (free, no key required)."""
    
    async def get_geolocation(self, ip_address: str) -> dict:
        """Get IP geolocation data."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"https://ipapi.co/{ip_address}/json/")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[IPGeolocation] Error getting geo for {ip_address}: {e}")
            return {}


async def lookup_ip_intelligence(ip_address: str) -> IPInfo:
    """
    Lookup IP intelligence from multiple sources with fallback.
    
    Priority:
    1. AbuseIPDB (if key configured)
    2. VirusTotal (if key configured)
    3. Basic geolocation fallback
    """
    abuseipdb = AbuseIPDBClient()
    virustotal = VirusTotalClient()
    geo_client = IPGeolocationClient()
    
    # Try AbuseIPDB first
    if abuseipdb.enabled:
        result = await abuseipdb.check_ip(ip_address)
        if result:
            # Enhance with geolocation if needed
            if result.city == "Unknown":
                geo = await geo_client.get_geolocation(ip_address)
                result.city = geo.get("city", "Unknown")
            return result
    
    # Try VirusTotal
    if virustotal.enabled:
        result = await virustotal.check_ip(ip_address)
        if result:
            # Enhance with geolocation
            if result.city == "Unknown":
                geo = await geo_client.get_geolocation(ip_address)
                result.city = geo.get("city", "Unknown")
            return result
    
    # Fallback to basic geolocation only
    geo = await geo_client.get_geolocation(ip_address)
    return IPInfo(
        ip_address=ip_address,
        country=geo.get("country_name", "Unknown"),
        city=geo.get("city", "Unknown"),
        isp=geo.get("org", "Unknown"),
        reputation="Unknown",
        threat_score=0.0,
        last_checked=datetime.now().isoformat()
    )
