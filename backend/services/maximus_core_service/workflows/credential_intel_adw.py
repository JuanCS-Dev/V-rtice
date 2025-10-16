"""ADW #2: Credential Intelligence Workflow.

Combines Breach Data + Google Dorking + Dark Web + Username Hunter for credential exposure analysis.

Workflow Steps:
1. HIBP breach data search (email/username)
2. Google dorking for exposed credentials
3. Dark web monitoring (paste sites + marketplaces)
4. Username enumeration (20 platforms)
5. Social media profile discovery
6. Credential risk scoring
7. Generate credential exposure report

Services Integrated:
- OSINT Service (BreachDataAnalyzer, GoogleDorkScanner, DarkWebMonitor, UsernameHunter, SocialScraper)

Authors: MAXIMUS Team
Date: 2025-10-15
Glory to YHWH
"""

import asyncio
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CredentialRiskLevel(Enum):
    """Credential exposure risk level."""
    CRITICAL = "critical"  # Active breach with passwords
    HIGH = "high"  # Multiple breaches or dark web presence
    MEDIUM = "medium"  # Single breach or dorking findings
    LOW = "low"  # Username enumeration only
    INFO = "info"  # No exposure found


@dataclass
class CredentialTarget:
    """Target for credential intelligence gathering."""
    email: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    include_darkweb: bool = True
    include_dorking: bool = True
    include_social: bool = True


@dataclass
class CredentialFinding:
    """Individual credential exposure finding."""
    finding_id: str
    finding_type: str  # breach, dork, darkweb, username, social
    severity: CredentialRiskLevel
    source: str
    details: Dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class CredentialIntelReport:
    """Complete credential intelligence report."""
    workflow_id: str
    target_email: Optional[str]
    target_username: Optional[str]
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str]
    findings: List[CredentialFinding] = field(default_factory=list)
    exposure_score: float = 0.0
    breach_count: int = 0
    platform_presence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "target_email": self.target_email,
            "target_username": self.target_username,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": [
                {
                    **asdict(f),
                    "severity": f.severity.value
                }
                for f in self.findings
            ],
            "exposure_score": self.exposure_score,
            "breach_count": self.breach_count,
            "platform_presence": self.platform_presence,
            "recommendations": self.recommendations,
            "statistics": self.statistics,
            "error": self.error,
        }


class CredentialIntelWorkflow:
    """Credential Intelligence AI-Driven Workflow.

    Orchestrates multiple OSINT services to discover credential exposure and risk.
    """

    def __init__(
        self,
        osint_service_url: str = "http://localhost:8036",
    ):
        """Initialize credential intelligence workflow.

        Args:
            osint_service_url: OSINT Service endpoint
        """
        self.osint_url = osint_service_url

        # Workflow state
        self.active_workflows: Dict[str, CredentialIntelReport] = {}

        logger.info("CredentialIntelWorkflow initialized")

    async def execute(self, target: CredentialTarget) -> CredentialIntelReport:
        """Execute credential intelligence workflow.

        Args:
            target: Target configuration

        Returns:
            CredentialIntelReport with complete findings
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = CredentialIntelReport(
            workflow_id=workflow_id,
            target_email=target.email,
            target_username=target.username,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )

        self.active_workflows[workflow_id] = report

        try:
            logger.info(f"Starting credential intelligence for {target.email or target.username} (workflow_id={workflow_id})")

            # Phase 1: HIBP breach data search
            if target.email or target.username:
                breach_findings = await self._search_breaches(target.email, target.username)
                report.findings.extend(breach_findings)
                report.breach_count = len(breach_findings)
                logger.info(f"Phase 1: Found {len(breach_findings)} breaches")

            # Phase 2: Google dorking for exposed credentials
            if target.include_dorking and (target.email or target.username):
                dork_findings = await self._google_dork_search(target.email, target.username)
                report.findings.extend(dork_findings)
                logger.info(f"Phase 2: Found {len(dork_findings)} dorking results")

            # Phase 3: Dark web monitoring
            if target.include_darkweb and (target.email or target.username):
                darkweb_findings = await self._monitor_darkweb(target.email, target.username)
                report.findings.extend(darkweb_findings)
                logger.info(f"Phase 3: Found {len(darkweb_findings)} dark web mentions")

            # Phase 4: Username enumeration across platforms
            if target.username:
                username_findings = await self._enumerate_username(target.username)
                report.findings.extend(username_findings)
                report.platform_presence = [f.details["platform"] for f in username_findings if f.details.get("found")]
                logger.info(f"Phase 4: Found {len(report.platform_presence)} platform presences")

            # Phase 5: Social media profile discovery
            if target.include_social and target.username:
                social_findings = await self._discover_social_profiles(target.username)
                report.findings.extend(social_findings)
                logger.info(f"Phase 5: Found {len(social_findings)} social profiles")

            # Phase 6: Calculate exposure score
            report.exposure_score = self._calculate_exposure_score(report.findings, report.breach_count)

            # Phase 7: Generate statistics
            report.statistics = self._generate_statistics(report.findings, report.breach_count)

            # Phase 8: Generate recommendations
            report.recommendations = self._generate_recommendations(report.findings, report.exposure_score)

            # Mark complete
            report.status = WorkflowStatus.COMPLETED
            report.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Credential intelligence completed: {len(report.findings)} findings, exposure_score={report.exposure_score:.2f}")

        except Exception as e:
            logger.error(f"Credential intelligence workflow failed: {e}")
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    async def _search_breaches(self, email: Optional[str], username: Optional[str]) -> List[CredentialFinding]:
        """Search HIBP for breach data.

        Args:
            email: Email address
            username: Username

        Returns:
            List of breach findings
        """
        # Simulate HIBP breach search
        # In production: Call OSINT Service /api/tools/breach-data/analyze
        await asyncio.sleep(0.5)

        findings = []
        target = email or username

        if not target:
            return findings

        # Simulate breach results
        mock_breaches = [
            {
                "name": "LinkedIn",
                "breach_date": "2021-04-01",
                "pwn_count": 700000000,
                "data_classes": ["Email", "Passwords", "PhoneNumbers"],
                "is_verified": True,
            },
            {
                "name": "Adobe",
                "breach_date": "2013-10-01",
                "pwn_count": 153000000,
                "data_classes": ["Email", "PasswordHashes", "Usernames"],
                "is_verified": True,
            },
        ]

        for breach in mock_breaches:
            severity = CredentialRiskLevel.CRITICAL if "Passwords" in breach["data_classes"] else CredentialRiskLevel.HIGH

            findings.append(CredentialFinding(
                finding_id=str(uuid4()),
                finding_type="breach",
                severity=severity,
                source="HIBP",
                details={
                    "breach_name": breach["name"],
                    "breach_date": breach["breach_date"],
                    "pwn_count": breach["pwn_count"],
                    "data_classes": breach["data_classes"],
                    "is_verified": breach["is_verified"],
                    "target": target,
                },
                timestamp=datetime.utcnow().isoformat(),
            ))

        return findings

    async def _google_dork_search(self, email: Optional[str], username: Optional[str]) -> List[CredentialFinding]:
        """Search for exposed credentials using Google dorks.

        Args:
            email: Email address
            username: Username

        Returns:
            List of dorking findings
        """
        # Simulate Google dorking
        # In production: Call OSINT Service /api/tools/google-dork/scan
        await asyncio.sleep(0.8)

        findings = []
        target = email or username

        if not target:
            return findings

        # Simulate credential dork results
        mock_dorks = [
            {
                "url": f"https://pastebin.com/example123",
                "query": f"site:pastebin.com {target}",
                "engine": "google",
            },
            {
                "url": f"https://github.com/example/repo/config.json",
                "query": f"site:github.com {target} password",
                "engine": "google",
            },
        ]

        for dork in mock_dorks:
            findings.append(CredentialFinding(
                finding_id=str(uuid4()),
                finding_type="dork",
                severity=CredentialRiskLevel.MEDIUM,
                source="GoogleDork",
                details={
                    "url": dork["url"],
                    "query": dork["query"],
                    "engine": dork["engine"],
                    "target": target,
                },
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.7,  # Lower confidence - requires manual verification
            ))

        return findings

    async def _monitor_darkweb(self, email: Optional[str], username: Optional[str]) -> List[CredentialFinding]:
        """Monitor dark web for credential mentions.

        Args:
            email: Email address
            username: Username

        Returns:
            List of dark web findings
        """
        # Simulate dark web monitoring
        # In production: Call OSINT Service /api/tools/darkweb/monitor
        await asyncio.sleep(1.0)

        findings = []
        target = email or username

        if not target:
            return findings

        # Simulate dark web results
        mock_findings = [
            {
                "url": "http://darkmarket.onion/db_dumps",
                "source": "tor_marketplace",
                "domain": "darkmarket.onion",
            },
            {
                "url": "https://paste.ee/example456",
                "source": "paste.ee",
                "domain": "paste.ee",
            },
        ]

        for item in mock_findings:
            severity = CredentialRiskLevel.CRITICAL if ".onion" in item["domain"] else CredentialRiskLevel.HIGH

            findings.append(CredentialFinding(
                finding_id=str(uuid4()),
                finding_type="darkweb",
                severity=severity,
                source="DarkWebMonitor",
                details={
                    "url": item["url"],
                    "source": item["source"],
                    "domain": item["domain"],
                    "target": target,
                    "onion_service": ".onion" in item["domain"],
                },
                timestamp=datetime.utcnow().isoformat(),
            ))

        return findings

    async def _enumerate_username(self, username: str) -> List[CredentialFinding]:
        """Enumerate username across 20+ platforms.

        Args:
            username: Username to search

        Returns:
            List of username findings
        """
        # Simulate username enumeration
        # In production: Call OSINT Service UsernameHunter
        await asyncio.sleep(0.6)

        findings = []

        # Simulate platform presence
        platforms = [
            ("GitHub", "https://github.com", True),
            ("Reddit", "https://reddit.com", True),
            ("Twitter", "https://twitter.com", False),
            ("Medium", "https://medium.com", True),
            ("LinkedIn", "https://linkedin.com", False),
            ("StackOverflow", "https://stackoverflow.com", True),
            ("Pastebin", "https://pastebin.com", True),
        ]

        for platform_name, base_url, found in platforms:
            findings.append(CredentialFinding(
                finding_id=str(uuid4()),
                finding_type="username",
                severity=CredentialRiskLevel.LOW if found else CredentialRiskLevel.INFO,
                source="UsernameHunter",
                details={
                    "platform": platform_name,
                    "username": username,
                    "found": found,
                    "url": f"{base_url}/{username}" if found else None,
                },
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.9 if found else 0.0,
            ))

        return findings

    async def _discover_social_profiles(self, username: str) -> List[CredentialFinding]:
        """Discover social media profiles.

        Args:
            username: Username to search

        Returns:
            List of social profile findings
        """
        # Simulate social media discovery
        # In production: Call OSINT Service SocialScraper
        await asyncio.sleep(0.7)

        findings = []

        # Simulate Twitter profile
        findings.append(CredentialFinding(
            finding_id=str(uuid4()),
            finding_type="social",
            severity=CredentialRiskLevel.INFO,
            source="SocialScraper",
            details={
                "platform": "twitter",
                "username": username,
                "profile_url": f"https://twitter.com/{username}",
                "followers": 1234,
                "tweets": 5678,
                "verified": False,
            },
            timestamp=datetime.utcnow().isoformat(),
        ))

        return findings

    def _calculate_exposure_score(self, findings: List[CredentialFinding], breach_count: int) -> float:
        """Calculate credential exposure score.

        Args:
            findings: All findings
            breach_count: Number of breaches

        Returns:
            Exposure score (0-100)
        """
        severity_weights = {
            CredentialRiskLevel.CRITICAL: 25.0,  # Passwords exposed
            CredentialRiskLevel.HIGH: 15.0,  # Multiple breaches or dark web
            CredentialRiskLevel.MEDIUM: 8.0,  # Dorking findings
            CredentialRiskLevel.LOW: 2.0,  # Username enumeration
            CredentialRiskLevel.INFO: 0.5,  # Informational
        }

        # Base score from findings
        total_score = sum(severity_weights.get(f.severity, 0) for f in findings)

        # Breach multiplier
        breach_multiplier = min(2.0, 1.0 + (breach_count * 0.2))
        total_score *= breach_multiplier

        # Dark web presence bonus
        darkweb_findings = [f for f in findings if f.finding_type == "darkweb"]
        if darkweb_findings:
            total_score += 15.0  # Significant risk

        # Platform presence bonus (more platforms = more attack surface)
        username_findings = [f for f in findings if f.finding_type == "username" and f.details.get("found")]
        platform_bonus = min(10.0, len(username_findings) * 0.5)
        total_score += platform_bonus

        # Normalize to 0-100 scale
        exposure_score = min(100.0, total_score)

        return round(exposure_score, 2)

    def _generate_statistics(self, findings: List[CredentialFinding], breach_count: int) -> Dict[str, Any]:
        """Generate statistics from findings.

        Args:
            findings: All findings
            breach_count: Number of breaches

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_findings": len(findings),
            "breach_count": breach_count,
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "info_count": 0,
            "platforms_found": 0,
            "darkweb_mentions": 0,
            "dorking_results": 0,
        }

        for finding in findings:
            # Count by type
            ftype = finding.finding_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

            # Count by severity
            severity = finding.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            # Count specific severities
            if finding.severity == CredentialRiskLevel.CRITICAL:
                stats["critical_count"] += 1
            elif finding.severity == CredentialRiskLevel.HIGH:
                stats["high_count"] += 1
            elif finding.severity == CredentialRiskLevel.MEDIUM:
                stats["medium_count"] += 1
            elif finding.severity == CredentialRiskLevel.LOW:
                stats["low_count"] += 1
            elif finding.severity == CredentialRiskLevel.INFO:
                stats["info_count"] += 1

            # Specific counts
            if finding.finding_type == "username" and finding.details.get("found"):
                stats["platforms_found"] += 1
            if finding.finding_type == "darkweb":
                stats["darkweb_mentions"] += 1
            if finding.finding_type == "dork":
                stats["dorking_results"] += 1

        return stats

    def _generate_recommendations(self, findings: List[CredentialFinding], exposure_score: float) -> List[str]:
        """Generate security recommendations.

        Args:
            findings: All findings
            exposure_score: Overall exposure score

        Returns:
            List of recommendations
        """
        recommendations = []

        # High-level recommendations based on exposure score
        if exposure_score >= 70:
            recommendations.append("CRITICAL: Immediate action required - credentials are highly exposed")
            recommendations.append("Change ALL passwords immediately using a password manager")
            recommendations.append("Enable multi-factor authentication (MFA) on all accounts")
        elif exposure_score >= 50:
            recommendations.append("HIGH: Significant credential exposure detected")
            recommendations.append("Change passwords for breached accounts")
            recommendations.append("Enable MFA where available")
        elif exposure_score >= 30:
            recommendations.append("MEDIUM: Moderate credential exposure detected")
            recommendations.append("Review and update passwords for affected accounts")
        else:
            recommendations.append("LOW: Limited credential exposure detected")
            recommendations.append("Continue monitoring for new breaches")

        # Breach-specific recommendations
        breach_findings = [f for f in findings if f.finding_type == "breach"]
        if breach_findings:
            password_breaches = [f for f in breach_findings if f.severity == CredentialRiskLevel.CRITICAL]
            if password_breaches:
                recommendations.append(f"URGENT: Passwords exposed in {len(password_breaches)} breaches - change immediately")

            verified_breaches = [f for f in breach_findings if f.details.get("is_verified")]
            if verified_breaches:
                recommendations.append(f"{len(verified_breaches)} verified breaches - prioritize these accounts")

        # Dark web recommendations
        darkweb_findings = [f for f in findings if f.finding_type == "darkweb"]
        if darkweb_findings:
            onion_findings = [f for f in darkweb_findings if f.details.get("onion_service")]
            if onion_findings:
                recommendations.append(f"CRITICAL: Credentials found on {len(onion_findings)} Tor marketplaces")
            recommendations.append("Monitor dark web continuously for new mentions")

        # Dorking recommendations
        dork_findings = [f for f in findings if f.finding_type == "dork"]
        if dork_findings:
            github_findings = [f for f in dork_findings if "github.com" in f.details.get("url", "")]
            if github_findings:
                recommendations.append("Remove exposed credentials from GitHub repositories")
            pastebin_findings = [f for f in dork_findings if "pastebin" in f.details.get("url", "").lower()]
            if pastebin_findings:
                recommendations.append("Contact Pastebin to remove exposed credential posts")

        # Platform presence recommendations
        username_findings = [f for f in findings if f.finding_type == "username" and f.details.get("found")]
        if len(username_findings) > 10:
            recommendations.append(f"Username found on {len(username_findings)} platforms - review account security on each")

        # General best practices
        recommendations.append("Use unique passwords for each account (password manager recommended)")
        recommendations.append("Enable breach monitoring alerts (e.g., HIBP notifications)")
        recommendations.append("Review and remove unused accounts to reduce attack surface")

        return recommendations

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow status dictionary or None
        """
        report = self.active_workflows.get(workflow_id)
        if not report:
            return None

        return {
            "workflow_id": workflow_id,
            "status": report.status.value,
            "target_email": report.target_email,
            "target_username": report.target_username,
            "findings_count": len(report.findings),
            "breach_count": report.breach_count,
            "exposure_score": report.exposure_score,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
