"""OSV.dev API client for vulnerability data.

OSV (Open Source Vulnerabilities) is a distributed vulnerability database
for open source projects. This client provides async access to OSV.dev API
with retry logic, rate limiting, and error handling.

API Documentation: https://ossf.github.io/osv-schema/
API Endpoint: https://api.osv.dev/v1

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import logging

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .base_feed import BaseFeedClient, RateLimitError, FeedUnavailableError, ThreatFeedError

logger = logging.getLogger(__name__)


class OSVClient(BaseFeedClient):
    """
    Client for OSV.dev API.
    
    OSV.dev provides:
    - Comprehensive vulnerability database
    - Machine-readable format (OSV Schema)
    - Package-based queries
    - CVE cross-referencing
    
    Features:
    - Async HTTP client (aiohttp)
    - Automatic retries with exponential backoff
    - Rate limiting (100 req/min default)
    - Connection pooling
    - Timeout handling
    
    Theoretical Foundation:
    - OSV Schema: https://ossf.github.io/osv-schema/
    - Circuit Breaker Pattern for resilience
    - Exponential Backoff for retry logic
    """
    
    BASE_URL = "https://api.osv.dev/v1"
    DEFAULT_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    
    def __init__(self, rate_limit: int = 100):
        """
        Initialize OSV.dev client.
        
        Args:
            rate_limit: Maximum requests per minute (default: 100)
        """
        super().__init__(name="OSV.dev", rate_limit=rate_limit)
        self._session: Optional[ClientSession] = None
        self._timeout = ClientTimeout(total=self.DEFAULT_TIMEOUT)
    
    async def __aenter__(self) -> 'OSVClient':
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            self._session = ClientSession(timeout=self._timeout)
            logger.debug(f"{self.name}: HTTP session created")
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"{self.name}: HTTP session closed")
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            json_data: JSON body for POST requests
            params: Query parameters for GET requests
            
        Returns:
            Response JSON as dict
            
        Raises:
            RateLimitError: If rate limited
            FeedUnavailableError: If service unavailable
            ThreatFeedError: For other errors
        """
        await self._ensure_session()
        await self._check_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(self.MAX_RETRIES):
            try:
                if method == "GET":
                    async with self._session.get(url, params=params) as response:  # type: ignore
                        return await self._handle_response(response)
                elif method == "POST":
                    async with self._session.post(url, json=json_data) as response:  # type: ignore
                        return await self._handle_response(response)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
            except ClientError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise FeedUnavailableError(f"{self.name} request failed after {self.MAX_RETRIES} attempts: {e}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.warning(
                    f"{self.name}: Request failed (attempt {attempt + 1}/{self.MAX_RETRIES}), "
                    f"retrying in {wait_time}s: {e}"
                )
                await asyncio.sleep(wait_time)
            
            except asyncio.TimeoutError:
                if attempt == self.MAX_RETRIES - 1:
                    raise FeedUnavailableError(f"{self.name} request timed out after {self.MAX_RETRIES} attempts")
                
                wait_time = 2 ** attempt
                logger.warning(f"{self.name}: Request timed out, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        raise FeedUnavailableError(f"{self.name}: All retry attempts exhausted")
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Handle HTTP response with error checking.
        
        Args:
            response: aiohttp response object
            
        Returns:
            Parsed JSON response
            
        Raises:
            RateLimitError: If 429 status
            FeedUnavailableError: If 5xx status
            ThreatFeedError: For other errors
        """
        if response.status == 429:
            raise RateLimitError(f"{self.name}: Rate limit exceeded (HTTP 429)")
        
        if response.status >= 500:
            text = await response.text()
            raise FeedUnavailableError(
                f"{self.name}: Server error (HTTP {response.status}): {text}"
            )
        
        if response.status >= 400:
            text = await response.text()
            raise ThreatFeedError(
                f"{self.name}: Client error (HTTP {response.status}): {text}"
            )
        
        try:
            json_result: Dict[str, Any] = await response.json()
            return json_result
        except Exception as e:
            text = await response.text()
            raise ThreatFeedError(f"{self.name}: Failed to parse JSON response: {e}\n{text}")
    
    async def fetch_vulnerabilities(
        self,
        ecosystem: Optional[str] = None,
        package: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch vulnerabilities from OSV.dev.
        
        Note: OSV.dev doesn't support "all vulnerabilities" query.
        Must specify package. To get all for ecosystem, must query
        each package individually.
        
        Args:
            ecosystem: Package ecosystem (PyPI, npm, Go, etc.)
            package: Specific package name
            since: Not supported by OSV API (ignored)
            
        Returns:
            List of vulnerability dicts
            
        Raises:
            ValueError: If package not specified
            RateLimitError: If rate limited
            FeedUnavailableError: If service down
        """
        if not package:
            raise ValueError(f"{self.name}: package parameter is required")
        
        if not ecosystem:
            ecosystem = "PyPI"  # Default to Python
        
        logger.info(f"{self.name}: Fetching vulnerabilities for {ecosystem}/{package}")
        
        # OSV.dev query endpoint
        query_data = {
            "package": {
                "name": package,
                "ecosystem": ecosystem
            }
        }
        
        response = await self._request_with_retry("POST", "query", json_data=query_data)
        
        # OSV response format: {"vulns": [list of vulnerabilities]}
        vulnerabilities: List[Dict[str, Any]] = response.get("vulns", [])
        
        logger.info(
            f"{self.name}: Found {len(vulnerabilities)} vulnerabilities for {ecosystem}/{package}"
        )
        
        return vulnerabilities
    
    async def fetch_by_cve_id(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch specific vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2024-12345)
            
        Returns:
            Vulnerability dict or None if not found
        """
        logger.debug(f"{self.name}: Fetching CVE {cve_id}")
        
        try:
            # OSV.dev vulnerability detail endpoint
            response = await self._request_with_retry("GET", f"vulns/{cve_id}")
            return response
        except ThreatFeedError as e:
            if "404" in str(e):
                logger.debug(f"{self.name}: CVE {cve_id} not found")
                return None
            raise
    
    async def query_batch(
        self,
        packages: List[Dict[str, str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query multiple packages in batch.
        
        OSV.dev supports batch queries for efficiency.
        
        Args:
            packages: List of {"ecosystem": "PyPI", "name": "package"} dicts
            
        Returns:
            Dict mapping package names to vulnerability lists
            
        Example:
            >>> packages = [
            ...     {"ecosystem": "PyPI", "name": "django"},
            ...     {"ecosystem": "PyPI", "name": "flask"}
            ... ]
            >>> results = await client.query_batch(packages)
            >>> results["django"]  # List of Django vulns
        """
        logger.info(f"{self.name}: Batch query for {len(packages)} packages")
        
        # OSV.dev querybatch endpoint
        batch_data = {
            "queries": [{"package": pkg} for pkg in packages]
        }
        
        response = await self._request_with_retry("POST", "querybatch", json_data=batch_data)
        
        # Response format: {"results": [{"vulns": [...]}, ...]}
        results_list = response.get("results", [])
        
        # Map results back to package names
        results_map: Dict[str, List[Dict[str, Any]]] = {}
        for i, pkg in enumerate(packages):
            pkg_name = pkg["name"]
            if i < len(results_list):
                results_map[pkg_name] = results_list[i].get("vulns", [])
            else:
                results_map[pkg_name] = []
        
        total_vulns = sum(len(vulns) for vulns in results_map.values())
        logger.info(f"{self.name}: Batch query complete: {total_vulns} total vulnerabilities")
        
        return results_map
    
    async def health_check(self) -> bool:
        """
        Check if OSV.dev API is healthy.
        
        Returns:
            True if API is accessible
        """
        try:
            # Try to fetch a known CVE
            result = await self.fetch_by_cve_id("CVE-2021-3177")  # Python CVE
            return result is not None
        except Exception as e:
            logger.error(f"{self.name} health check failed: {e}")
            return False
