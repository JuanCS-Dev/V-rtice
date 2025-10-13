"""
NVD Feed Client - NIST National Vulnerability Database.

Ingests CVE data from NVD API v2.0:
- https://nvd.nist.gov/developers/vulnerabilities
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import AsyncGenerator, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NVDVulnerability(BaseModel):
    """NVD vulnerability data model."""

    cve_id: str = Field(..., alias="id")
    source_identifier: str = Field(..., alias="sourceIdentifier")
    published: datetime
    last_modified: datetime = Field(..., alias="lastModified")
    vuln_status: str = Field(..., alias="vulnStatus")

    # Descriptions
    descriptions: List[dict] = Field(default_factory=list)

    # Metrics (CVSS scores)
    cvss_v3: Optional[dict] = None
    cvss_v2: Optional[dict] = None

    # Weaknesses (CWEs)
    weaknesses: List[dict] = Field(default_factory=list)

    # Configurations (CPE matches)
    configurations: List[dict] = Field(default_factory=list)

    # References
    references: List[dict] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class NVDClient:
    """
    Client for NIST NVD API v2.0.

    Features:
    - Rate limiting (5 requests/second for unauthenticated, 50/s with API key)
    - Pagination support
    - Date range filtering
    - CPE matching for ecosystems
    - Retry logic with exponential backoff
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    RATE_LIMIT_DELAY = 0.2  # 200ms between requests (5 req/s)
    RATE_LIMIT_DELAY_WITH_KEY = 0.02  # 20ms with API key (50 req/s)

    def __init__(
        self,
        api_key: Optional[str] = None,
        results_per_page: int = 2000,
        timeout: int = 30,
    ):
        """
        Initialize NVD client.

        Args:
            api_key: NVD API key (optional, increases rate limit)
            results_per_page: Results per page (max 2000)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.results_per_page = min(results_per_page, 2000)
        self.timeout = timeout

        self.rate_limit_delay = (
            self.RATE_LIMIT_DELAY_WITH_KEY if api_key else self.RATE_LIMIT_DELAY
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: Optional[float] = None

        logger.info(
            f"NVDClient initialized: "
            f"rate_limit={1/self.rate_limit_delay:.0f} req/s, "
            f"results_per_page={self.results_per_page}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._get_headers(),
            )
            logger.info("NVD HTTP session initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("NVD HTTP session closed")

    def _get_headers(self) -> dict:
        """Get HTTP headers (includes API key if available)."""
        headers = {"User-Agent": "AdaptiveImmuneSystem/1.0"}
        if self.api_key:
            headers["apiKey"] = self.api_key
        return headers

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def _request(
        self,
        params: dict,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> dict:
        """
        Make HTTP request to NVD API with retry logic.

        Args:
            params: Query parameters
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            JSON response

        Raises:
            aiohttp.ClientError: If request fails after retries
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")

        await self._rate_limit()

        try:
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    return await response.json()

                elif response.status == 403:
                    logger.error("NVD API: 403 Forbidden (check API key or rate limit)")
                    raise aiohttp.ClientError("NVD API returned 403 Forbidden")

                elif response.status == 503:
                    # Service unavailable - retry with backoff
                    if retry_count < max_retries:
                        backoff = 2 ** retry_count
                        logger.warning(
                            f"NVD API: 503 Service Unavailable, "
                            f"retrying in {backoff}s (attempt {retry_count+1}/{max_retries})"
                        )
                        await asyncio.sleep(backoff)
                        return await self._request(params, retry_count + 1, max_retries)
                    else:
                        raise aiohttp.ClientError("NVD API unavailable after retries")

                else:
                    error_text = await response.text()
                    logger.error(f"NVD API error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(
                        f"NVD API returned {response.status}: {error_text}"
                    )

        except asyncio.TimeoutError:
            if retry_count < max_retries:
                logger.warning(f"NVD API timeout, retrying (attempt {retry_count+1}/{max_retries})")
                await asyncio.sleep(2 ** retry_count)
                return await self._request(params, retry_count + 1, max_retries)
            else:
                raise

    async def get_recent_cves(
        self,
        days: int = 7,
        modified: bool = True,
    ) -> AsyncGenerator[NVDVulnerability, None]:
        """
        Get CVEs from last N days.

        Args:
            days: Number of days to look back
            modified: If True, use lastModifiedDate; else use publishedDate

        Yields:
            NVDVulnerability instances
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        async for vuln in self.get_cves_by_date_range(start_date, end_date, modified):
            yield vuln

    async def get_cves_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        modified: bool = True,
    ) -> AsyncGenerator[NVDVulnerability, None]:
        """
        Get CVEs within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            modified: If True, use lastModStartDate/lastModEndDate; else pubStartDate/pubEndDate

        Yields:
            NVDVulnerability instances
        """
        # Format dates as ISO 8601
        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

        date_param_prefix = "lastMod" if modified else "pub"

        params = {
            f"{date_param_prefix}StartDate": start_iso,
            f"{date_param_prefix}EndDate": end_iso,
            "resultsPerPage": self.results_per_page,
            "startIndex": 0,
        }

        logger.info(
            f"Fetching NVD CVEs: {start_date.date()} to {end_date.date()} "
            f"({'modified' if modified else 'published'})"
        )

        total_results = None
        fetched_count = 0

        while True:
            try:
                data = await self._request(params)

                # Parse response
                total_results = data.get("totalResults", 0)
                vulnerabilities = data.get("vulnerabilities", [])

                if not vulnerabilities:
                    break

                # Yield vulnerabilities
                for vuln_data in vulnerabilities:
                    cve = vuln_data.get("cve", {})
                    try:
                        vuln = NVDVulnerability(**cve)
                        fetched_count += 1
                        yield vuln
                    except Exception as e:
                        logger.error(f"Failed to parse CVE: {e}")
                        continue

                # Check if more pages
                params["startIndex"] += len(vulnerabilities)

                if params["startIndex"] >= total_results:
                    break

            except Exception as e:
                logger.error(f"Error fetching NVD CVEs: {e}")
                break

        logger.info(
            f"✅ NVD fetch complete: {fetched_count}/{total_results} CVEs retrieved"
        )

    async def get_cve_by_id(self, cve_id: str) -> Optional[NVDVulnerability]:
        """
        Get specific CVE by ID.

        Args:
            cve_id: CVE identifier (e.g., "CVE-2021-44228")

        Returns:
            NVDVulnerability or None if not found
        """
        params = {"cveId": cve_id}

        try:
            data = await self._request(params)
            vulnerabilities = data.get("vulnerabilities", [])

            if vulnerabilities:
                cve = vulnerabilities[0].get("cve", {})
                return NVDVulnerability(**cve)

            return None

        except Exception as e:
            logger.error(f"Error fetching CVE {cve_id}: {e}")
            return None

    def extract_cvss_score(self, vuln: NVDVulnerability) -> Optional[float]:
        """
        Extract CVSS score (prefer v3 over v2).

        Args:
            vuln: NVDVulnerability instance

        Returns:
            CVSS base score or None
        """
        if vuln.cvss_v3:
            cvss_data = vuln.cvss_v3.get("cvssData", {})
            return cvss_data.get("baseScore")

        if vuln.cvss_v2:
            cvss_data = vuln.cvss_v2.get("cvssData", {})
            return cvss_data.get("baseScore")

        return None

    def extract_severity(self, vuln: NVDVulnerability) -> Optional[str]:
        """
        Extract severity (CRITICAL, HIGH, MEDIUM, LOW).

        Args:
            vuln: NVDVulnerability instance

        Returns:
            Severity string (lowercase) or None
        """
        if vuln.cvss_v3:
            cvss_data = vuln.cvss_v3.get("cvssData", {})
            severity = cvss_data.get("baseSeverity")
            if severity:
                return severity.lower()

        if vuln.cvss_v2:
            # Map v2 score to severity
            score = self.extract_cvss_score(vuln)
            if score:
                if score >= 9.0:
                    return "critical"
                elif score >= 7.0:
                    return "high"
                elif score >= 4.0:
                    return "medium"
                else:
                    return "low"

        return None

    def extract_cwe_ids(self, vuln: NVDVulnerability) -> List[str]:
        """
        Extract CWE IDs.

        Args:
            vuln: NVDVulnerability instance

        Returns:
            List of CWE IDs (e.g., ["CWE-79", "CWE-89"])
        """
        cwe_ids = []

        for weakness in vuln.weaknesses:
            descriptions = weakness.get("description", [])
            for desc in descriptions:
                value = desc.get("value", "")
                if value.startswith("CWE-"):
                    cwe_ids.append(value)

        return list(set(cwe_ids))

    def extract_description(self, vuln: NVDVulnerability) -> str:
        """
        Extract English description.

        Args:
            vuln: NVDVulnerability instance

        Returns:
            Description string
        """
        for desc in vuln.descriptions:
            if desc.get("lang") == "en":
                return desc.get("value", "")

        # Fallback to first description
        if vuln.descriptions:
            return vuln.descriptions[0].get("value", "")

        return ""

    def extract_references(self, vuln: NVDVulnerability) -> List[dict]:
        """
        Extract references (URLs, advisories).

        Args:
            vuln: NVDVulnerability instance

        Returns:
            List of reference dicts with 'url' and 'tags'
        """
        references = []

        for ref in vuln.references:
            references.append({
                "url": ref.get("url"),
                "tags": ref.get("tags", []),
            })

        return references
