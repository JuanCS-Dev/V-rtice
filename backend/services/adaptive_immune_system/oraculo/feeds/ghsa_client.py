"""
GHSA Feed Client - GitHub Security Advisories.

Ingests security advisories from GitHub GraphQL API:
- https://docs.github.com/en/graphql/reference/objects#securityadvisory
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GHSAPackage(BaseModel):
    """Affected package in GHSA advisory."""

    ecosystem: str
    name: str


class GHSAVulnerableVersionRange(BaseModel):
    """Vulnerable version range."""

    first_patched_version: Optional[str] = None


class GHSAVulnerability(BaseModel):
    """GHSA vulnerability data model."""

    ghsa_id: str
    cve_id: Optional[str] = None
    summary: str
    description: str
    severity: str  # CRITICAL, HIGH, MODERATE, LOW
    published_at: datetime
    updated_at: datetime
    withdrawn_at: Optional[datetime] = None

    # Affected packages
    package: GHSAPackage
    vulnerable_version_range: Optional[str] = None
    first_patched_version: Optional[str] = None

    # References
    references: List[dict] = Field(default_factory=list)

    # CWEs
    cwes: List[str] = Field(default_factory=list)


class GHSAClient:
    """
    Client for GitHub Security Advisories GraphQL API.

    Features:
    - GraphQL pagination (cursor-based)
    - Ecosystem filtering (npm, pip, cargo, go, etc.)
    - CVE ID lookup
    - Rate limiting (5000 req/hour with token)
    """

    GRAPHQL_URL = "https://api.github.com/graphql"
    RATE_LIMIT_DELAY = 0.75  # 750ms between requests (~4800 req/hour buffer)

    # Supported ecosystems
    ECOSYSTEMS = [
        "COMPOSER",
        "GO",
        "MAVEN",
        "NPM",
        "NUGET",
        "PIP",
        "RUBYGEMS",
        "RUST",
    ]

    def __init__(
        self,
        github_token: str,
        timeout: int = 30,
    ):
        """
        Initialize GHSA client.

        Args:
            github_token: GitHub Personal Access Token (required for GraphQL)
            timeout: Request timeout in seconds
        """
        self.github_token = github_token
        self.timeout = timeout

        self.session: Optional[aiohttp.ClientSession] = None
        self._last_request_time: Optional[float] = None

        logger.info("GHSAClient initialized")

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
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json",
                },
            )
            logger.info("GHSA HTTP session initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("GHSA HTTP session closed")

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        if self._last_request_time is not None:
            elapsed = asyncio.get_event_loop().time() - self._last_request_time
            if elapsed < self.RATE_LIMIT_DELAY:
                await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)

        self._last_request_time = asyncio.get_event_loop().time()

    async def _query(self, query: str, variables: dict) -> dict:
        """
        Execute GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            GraphQL response data

        Raises:
            aiohttp.ClientError: If request fails
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Call initialize() first.")

        await self._rate_limit()

        payload = {"query": query, "variables": variables}

        try:
            async with self.session.post(self.GRAPHQL_URL, json=payload) as response:
                if response.status == 200:
                    result = await response.json()

                    if "errors" in result:
                        errors = result["errors"]
                        logger.error(f"GraphQL errors: {errors}")
                        raise aiohttp.ClientError(f"GraphQL errors: {errors}")

                    return result.get("data", {})

                elif response.status == 401:
                    logger.error("GitHub API: 401 Unauthorized (check token)")
                    raise aiohttp.ClientError("GitHub API authentication failed")

                elif response.status == 403:
                    logger.error("GitHub API: 403 Forbidden (rate limit exceeded)")
                    raise aiohttp.ClientError("GitHub API rate limit exceeded")

                else:
                    error_text = await response.text()
                    logger.error(f"GitHub API error: {response.status} - {error_text}")
                    raise aiohttp.ClientError(
                        f"GitHub API returned {response.status}: {error_text}"
                    )

        except asyncio.TimeoutError:
            logger.error("GitHub API request timeout")
            raise

    async def get_advisories(
        self,
        ecosystem: Optional[str] = None,
        severity: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        first: int = 100,
    ) -> AsyncGenerator[GHSAVulnerability, None]:
        """
        Get security advisories with pagination.

        Args:
            ecosystem: Filter by ecosystem (NPM, PIP, etc.)
            severity: Filter by severity (CRITICAL, HIGH, MODERATE, LOW)
            updated_since: Filter by update date
            first: Number of results per page (max 100)

        Yields:
            GHSAVulnerability instances
        """
        query = """
        query($first: Int!, $after: String, $ecosystem: SecurityAdvisoryEcosystem, $severity: [SecurityAdvisorySeverity!]) {
          securityAdvisories(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              ghsaId
              summary
              description
              severity
              publishedAt
              updatedAt
              withdrawnAt
              identifiers {
                type
                value
              }
              references {
                url
              }
              vulnerabilities(first: 10, ecosystem: $ecosystem) {
                nodes {
                  package {
                    ecosystem
                    name
                  }
                  vulnerableVersionRange
                  firstPatchedVersion {
                    identifier
                  }
                }
              }
              cwes(first: 10) {
                nodes {
                  cweId
                  name
                }
              }
            }
          }
        }
        """

        variables = {
            "first": min(first, 100),
            "after": None,
            "ecosystem": ecosystem,
            "severity": [severity] if severity else None,
        }

        logger.info(
            f"Fetching GHSA advisories: ecosystem={ecosystem or 'all'}, "
            f"severity={severity or 'all'}"
        )

        total_fetched = 0
        has_next_page = True

        while has_next_page:
            try:
                data = await self._query(query, variables)
                security_advisories = data.get("securityAdvisories", {})

                page_info = security_advisories.get("pageInfo", {})
                has_next_page = page_info.get("hasNextPage", False)
                variables["after"] = page_info.get("endCursor")

                nodes = security_advisories.get("nodes", [])

                for advisory in nodes:
                    # Filter by updated_since if provided
                    if updated_since:
                        updated_at = datetime.fromisoformat(
                            advisory["updatedAt"].replace("Z", "+00:00")
                        )
                        if updated_at < updated_since:
                            has_next_page = False  # Stop fetching older advisories
                            break

                    # Extract CVE ID
                    cve_id = None
                    for identifier in advisory.get("identifiers", []):
                        if identifier.get("type") == "CVE":
                            cve_id = identifier.get("value")
                            break

                    # Extract CWE IDs
                    cwes = []
                    for cwe_node in advisory.get("cwes", {}).get("nodes", []):
                        cwes.append(cwe_node.get("cweId"))

                    # Extract references
                    references = [
                        {"url": ref.get("url")}
                        for ref in advisory.get("references", [])
                    ]

                    # Yield vulnerability for each affected package
                    vulnerabilities = advisory.get("vulnerabilities", {}).get("nodes", [])

                    if not vulnerabilities:
                        # Advisory without specific package info - skip or log
                        logger.debug(
                            f"Advisory {advisory['ghsaId']} has no package vulnerabilities"
                        )
                        continue

                    for vuln in vulnerabilities:
                        package = vuln.get("package", {})

                        # Apply ecosystem filter if specified
                        if ecosystem and package.get("ecosystem") != ecosystem:
                            continue

                        first_patched = vuln.get("firstPatchedVersion", {})

                        try:
                            yield GHSAVulnerability(
                                ghsa_id=advisory["ghsaId"],
                                cve_id=cve_id,
                                summary=advisory["summary"],
                                description=advisory["description"],
                                severity=advisory["severity"],
                                published_at=datetime.fromisoformat(
                                    advisory["publishedAt"].replace("Z", "+00:00")
                                ),
                                updated_at=datetime.fromisoformat(
                                    advisory["updatedAt"].replace("Z", "+00:00")
                                ),
                                withdrawn_at=(
                                    datetime.fromisoformat(
                                        advisory["withdrawnAt"].replace("Z", "+00:00")
                                    )
                                    if advisory.get("withdrawnAt")
                                    else None
                                ),
                                package=GHSAPackage(
                                    ecosystem=package["ecosystem"],
                                    name=package["name"],
                                ),
                                vulnerable_version_range=vuln.get("vulnerableVersionRange"),
                                first_patched_version=(
                                    first_patched.get("identifier") if first_patched else None
                                ),
                                references=references,
                                cwes=cwes,
                            )

                            total_fetched += 1

                        except Exception as e:
                            logger.error(f"Failed to parse GHSA advisory: {e}")
                            continue

            except Exception as e:
                logger.error(f"Error fetching GHSA advisories: {e}")
                break

        logger.info(f"✅ GHSA fetch complete: {total_fetched} advisories retrieved")

    async def get_advisory_by_ghsa_id(self, ghsa_id: str) -> Optional[List[GHSAVulnerability]]:
        """
        Get specific advisory by GHSA ID.

        Args:
            ghsa_id: GHSA identifier (e.g., "GHSA-xxxx-xxxx-xxxx")

        Returns:
            List of GHSAVulnerability instances (one per affected package) or None
        """
        query = """
        query($ghsaId: String!) {
          securityAdvisory(ghsaId: $ghsaId) {
            ghsaId
            summary
            description
            severity
            publishedAt
            updatedAt
            withdrawnAt
            identifiers {
              type
              value
            }
            references {
              url
            }
            vulnerabilities(first: 50) {
              nodes {
                package {
                  ecosystem
                  name
                }
                vulnerableVersionRange
                firstPatchedVersion {
                  identifier
                }
              }
            }
            cwes(first: 10) {
              nodes {
                cweId
                name
              }
            }
          }
        }
        """

        variables = {"ghsaId": ghsa_id}

        try:
            data = await self._query(query, variables)
            advisory = data.get("securityAdvisory")

            if not advisory:
                return None

            # Parse advisory (similar to get_advisories)
            cve_id = None
            for identifier in advisory.get("identifiers", []):
                if identifier.get("type") == "CVE":
                    cve_id = identifier.get("value")
                    break

            cwes = [cwe.get("cweId") for cwe in advisory.get("cwes", {}).get("nodes", [])]
            references = [{"url": ref.get("url")} for ref in advisory.get("references", [])]

            vulnerabilities = []
            for vuln in advisory.get("vulnerabilities", {}).get("nodes", []):
                package = vuln.get("package", {})
                first_patched = vuln.get("firstPatchedVersion", {})

                vulnerabilities.append(
                    GHSAVulnerability(
                        ghsa_id=advisory["ghsaId"],
                        cve_id=cve_id,
                        summary=advisory["summary"],
                        description=advisory["description"],
                        severity=advisory["severity"],
                        published_at=datetime.fromisoformat(
                            advisory["publishedAt"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            advisory["updatedAt"].replace("Z", "+00:00")
                        ),
                        withdrawn_at=(
                            datetime.fromisoformat(advisory["withdrawnAt"].replace("Z", "+00:00"))
                            if advisory.get("withdrawnAt")
                            else None
                        ),
                        package=GHSAPackage(
                            ecosystem=package["ecosystem"],
                            name=package["name"],
                        ),
                        vulnerable_version_range=vuln.get("vulnerableVersionRange"),
                        first_patched_version=(
                            first_patched.get("identifier") if first_patched else None
                        ),
                        references=references,
                        cwes=cwes,
                    )
                )

            return vulnerabilities if vulnerabilities else None

        except Exception as e:
            logger.error(f"Error fetching GHSA {ghsa_id}: {e}")
            return None

    def map_severity_to_standard(self, ghsa_severity: str) -> str:
        """
        Map GHSA severity to standard format.

        Args:
            ghsa_severity: GHSA severity (CRITICAL, HIGH, MODERATE, LOW)

        Returns:
            Standard severity (critical, high, medium, low)
        """
        mapping = {
            "CRITICAL": "critical",
            "HIGH": "high",
            "MODERATE": "medium",
            "LOW": "low",
        }
        return mapping.get(ghsa_severity, "unknown")

    def map_ecosystem_to_standard(self, ghsa_ecosystem: str) -> str:
        """
        Map GHSA ecosystem to standard format.

        Args:
            ghsa_ecosystem: GHSA ecosystem (NPM, PIP, etc.)

        Returns:
            Standard ecosystem (npm, pypi, etc.)
        """
        mapping = {
            "NPM": "npm",
            "PIP": "pypi",
            "RUBYGEMS": "rubygems",
            "MAVEN": "maven",
            "COMPOSER": "composer",
            "NUGET": "nuget",
            "GO": "go",
            "RUST": "cargo",
        }
        return mapping.get(ghsa_ecosystem, ghsa_ecosystem.lower())
