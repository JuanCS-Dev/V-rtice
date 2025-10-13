"""
OSV Feed Client - Open Source Vulnerabilities.

Ingests vulnerability data from OSV.dev API:
- https://osv.dev/docs/
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class OSVAffected(BaseModel):
    """Affected package in OSV vulnerability."""

    package_name: str = Field(..., alias="package")
    ecosystem: str
    ranges: List[dict] = Field(default_factory=list)
    versions: List[str] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class OSVVulnerability(BaseModel):
    """OSV vulnerability data model."""

    id: str  # OSV ID or CVE ID
    summary: Optional[str] = None
    details: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)  # CVE IDs, GHSA IDs, etc.
    modified: datetime
    published: Optional[datetime] = None
    withdrawn: Optional[datetime] = None

    # Affected packages
    affected: List[OSVAffected] = Field(default_factory=list)

    # Severity
    severity: Optional[List[dict]] = None

    # References
    references: List[dict] = Field(default_factory=list)

    # Database specific
    database_specific: Optional[dict] = None


class OSVClient:
    """
    Client for OSV.dev API.

    Features:
    - Query by package name + ecosystem
    - Query by vulnerability ID (CVE, GHSA, etc.)
    - Batch queries
    - No rate limiting (public API)
    """

    BASE_URL = "https://api.osv.dev/v1"

    def __init__(self, timeout: int = 30):
        """
        Initialize OSV client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info("OSVClient initialized")

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
                headers={"Content-Type": "application/json"},
            )
            logger.info("OSV HTTP session initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("OSV HTTP session closed")

    async def _post(self, endpoint: str, payload: dict) -> dict:
        """
        Make POST request to OSV API.

        Args:
            endpoint: API endpoint
            payload: Request payload

        Returns:
            JSON response

        Raises:
            aiohttp.ClientError: If request fails
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    return await response.json()

                elif response.status == 404:
                    # Not found - return empty
                    return {}

                else:
                    error_text = await response.text()
                    logger.error(f"OSV API error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(
                        f"OSV API returned {response.status}: {error_text}"
                    )

        except asyncio.TimeoutError:
            logger.error("OSV API request timeout")
            raise

    async def query_by_package(
        self,
        package_name: str,
        ecosystem: str,
        version: Optional[str] = None,
    ) -> AsyncGenerator[OSVVulnerability, None]:
        """
        Query vulnerabilities by package.

        Args:
            package_name: Package name (e.g., "lodash")
            ecosystem: Ecosystem (e.g., "npm", "PyPI", "Go")
            version: Optional specific version

        Yields:
            OSVVulnerability instances
        """
        payload = {
            "package": {"name": package_name, "ecosystem": ecosystem}
        }

        if version:
            payload["version"] = version

        try:
            data = await self._post("query", payload)

            vulns = data.get("vulns", [])

            for vuln_data in vulns:
                try:
                    yield OSVVulnerability(**vuln_data)
                except Exception as e:
                    logger.error(f"Failed to parse OSV vulnerability: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error querying OSV for {package_name}@{ecosystem}: {e}")

    async def query_by_id(self, vuln_id: str) -> Optional[OSVVulnerability]:
        """
        Query vulnerability by ID (CVE, GHSA, OSV ID).

        Args:
            vuln_id: Vulnerability ID (e.g., "CVE-2021-44228", "GHSA-xxxx-xxxx-xxxx")

        Returns:
            OSVVulnerability or None if not found
        """
        url = f"{self.BASE_URL}/vulns/{vuln_id}"

        try:
            if not self.session:
                raise RuntimeError("Session not initialized")

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return OSVVulnerability(**data)
                elif response.status == 404:
                    return None
                else:
                    logger.error(f"OSV API error: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching OSV {vuln_id}: {e}")
            return None

    async def query_batch(
        self,
        queries: List[dict],
    ) -> List[Optional[List[OSVVulnerability]]]:
        """
        Batch query vulnerabilities.

        Args:
            queries: List of query dicts [{"package": {"name": "...", "ecosystem": "..."}, "version": "..."}]

        Returns:
            List of vulnerability lists (one per query)
        """
        payload = {"queries": queries}

        try:
            data = await self._post("querybatch", payload)

            results = data.get("results", [])
            batch_results = []

            for result in results:
                vulns = result.get("vulns", [])
                parsed_vulns = []

                for vuln_data in vulns:
                    try:
                        parsed_vulns.append(OSVVulnerability(**vuln_data))
                    except Exception as e:
                        logger.error(f"Failed to parse OSV vulnerability: {e}")
                        continue

                batch_results.append(parsed_vulns if parsed_vulns else None)

            return batch_results

        except Exception as e:
            logger.error(f"Error in OSV batch query: {e}")
            return [None] * len(queries)

    def extract_cve_ids(self, vuln: OSVVulnerability) -> List[str]:
        """
        Extract CVE IDs from aliases.

        Args:
            vuln: OSVVulnerability instance

        Returns:
            List of CVE IDs
        """
        cve_ids = []

        # Check if ID itself is a CVE
        if vuln.id.startswith("CVE-"):
            cve_ids.append(vuln.id)

        # Check aliases
        for alias in vuln.aliases:
            if alias.startswith("CVE-"):
                cve_ids.append(alias)

        return list(set(cve_ids))

    def extract_ghsa_ids(self, vuln: OSVVulnerability) -> List[str]:
        """
        Extract GHSA IDs from aliases.

        Args:
            vuln: OSVVulnerability instance

        Returns:
            List of GHSA IDs
        """
        ghsa_ids = []

        # Check if ID itself is a GHSA
        if vuln.id.startswith("GHSA-"):
            ghsa_ids.append(vuln.id)

        # Check aliases
        for alias in vuln.aliases:
            if alias.startswith("GHSA-"):
                ghsa_ids.append(alias)

        return list(set(ghsa_ids))

    def extract_cvss_score(self, vuln: OSVVulnerability) -> Optional[float]:
        """
        Extract CVSS score from severity.

        Args:
            vuln: OSVVulnerability instance

        Returns:
            CVSS score or None
        """
        if not vuln.severity:
            return None

        for severity_item in vuln.severity:
            if severity_item.get("type") == "CVSS_V3":
                score = severity_item.get("score")
                if score:
                    # Parse "CVSS:3.1/AV:N/AC:L/..." format
                    try:
                        # Score is in database_specific or parsed from vector
                        if "database_specific" in vuln and vuln.database_specific:
                            return vuln.database_specific.get("cvss_score")
                    except:
                        pass

        return None

    def map_ecosystem_to_standard(self, osv_ecosystem: str) -> str:
        """
        Map OSV ecosystem to standard format.

        Args:
            osv_ecosystem: OSV ecosystem (PyPI, npm, etc.)

        Returns:
            Standard ecosystem (pypi, npm, etc.)
        """
        mapping = {
            "PyPI": "pypi",
            "npm": "npm",
            "Go": "go",
            "crates.io": "cargo",
            "Maven": "maven",
            "NuGet": "nuget",
            "RubyGems": "rubygems",
            "Packagist": "composer",
        }
        return mapping.get(osv_ecosystem, osv_ecosystem.lower())
