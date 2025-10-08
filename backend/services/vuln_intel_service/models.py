"""Maximus Vulnerability Intelligence Service - Data Models.

This module defines the Pydantic data models (schemas) used for data validation
and serialization within the Vulnerability Intelligence Service. These schemas
ensure data consistency and provide a clear structure for representing CVEs,
software vulnerabilities, and Nuclei scan results.

By using Pydantic, Maximus AI benefits from automatic data validation, clear
documentation of data structures, and seamless integration with FastAPI for
API request and response modeling. This is crucial for maintaining data integrity
and enabling efficient data exchange within the vulnerability intelligence ecosystem.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CVEDetails(BaseModel):
    """Represents detailed information about a Common Vulnerability and Exposure (CVE).

    Attributes:
        cve_id (str): The CVE ID (e.g., 'CVE-2023-1234').
        description (str): A description of the vulnerability.
        severity (str): The severity of the CVE (e.g., 'CRITICAL', 'HIGH').
        affected_products (List[str]): List of affected software products and versions.
        exploit_available (bool): True if a public exploit is known to exist.
        exploit_details (Optional[str]): Details about the exploit, if available.
        references (List[str]): List of URLs to relevant advisories or articles.
        last_updated (str): ISO formatted timestamp of when the CVE info was last updated.
    """

    cve_id: str
    description: str
    severity: str
    affected_products: List[str]
    exploit_available: bool
    exploit_details: Optional[str] = None
    references: List[str] = []
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())


class NucleiScanResult(BaseModel):
    """Represents a single finding from a Nuclei scan.

    Attributes:
        template (str): The Nuclei template that triggered the finding.
        severity (str): The severity of the finding (e.g., 'info', 'low', 'high', 'critical').
        name (str): The name of the vulnerability or issue.
        host (str): The target host where the finding was identified.
        matched_at (str): The specific path or endpoint where the match occurred.
        extracted_results (Optional[List[str]]): Any extracted data from the finding.
        timestamp (str): ISO formatted timestamp of the finding.
    """

    template: str
    severity: str
    name: str
    host: str
    matched_at: str
    extracted_results: Optional[List[str]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class VulnerabilityReport(BaseModel):
    """Represents a comprehensive report of vulnerabilities for a target.

    Attributes:
        target (str): The target that was scanned.
        scan_id (str): Unique identifier for the scan.
        scan_time (str): ISO formatted timestamp of when the scan was performed.
        cves (List[CVEDetails]): List of relevant CVEs found.
        nuclei_findings (List[NucleiScanResult]): List of findings from Nuclei scans.
        overall_risk_score (float): An aggregated risk score for the target.
        recommendations (List[str]): Actionable recommendations for remediation.
    """

    target: str
    scan_id: str
    scan_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    cves: List[CVEDetails] = []
    nuclei_findings: List[NucleiScanResult] = []
    overall_risk_score: float = 0.0
    recommendations: List[str] = []
