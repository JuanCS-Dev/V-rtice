"""ADW #3: Deep Target Profiling Workflow.

Combines Social Scraper + Email/Phone Analyzer + Image Analysis + Pattern Detection for comprehensive target profiling.

Workflow Steps:
1. Email/phone extraction + validation
2. Social media scraping (Twitter)
3. Username platform enumeration
4. Image metadata extraction (EXIF/GPS)
5. Pattern detection (behaviors, locations)
6. Risk assessment (social engineering susceptibility)
7. Generate target profile report

Services Integrated:
- OSINT Service (EmailAnalyzer, PhoneAnalyzer, SocialScraper, UsernameHunter, ImageAnalyzer, PatternDetector)

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


class SEVulnerability(Enum):
    """Social engineering vulnerability level."""
    CRITICAL = "critical"  # Highly susceptible, immediate risk
    HIGH = "high"  # Multiple risk factors identified
    MEDIUM = "medium"  # Some exposure, manageable risk
    LOW = "low"  # Minimal exposure
    INFO = "info"  # Informational only


@dataclass
class ProfileTarget:
    """Target for deep profiling."""
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    include_social: bool = True
    include_images: bool = True


@dataclass
class ProfileFinding:
    """Individual profiling finding."""
    finding_id: str
    finding_type: str  # contact, social, platform, image, pattern, behavior
    category: str
    details: Dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class TargetProfileReport:
    """Complete target profiling report."""
    workflow_id: str
    target_username: Optional[str]
    target_email: Optional[str]
    target_name: Optional[str]
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str]
    findings: List[ProfileFinding] = field(default_factory=list)
    contact_info: Dict[str, Any] = field(default_factory=dict)
    social_profiles: List[Dict[str, Any]] = field(default_factory=list)
    platform_presence: List[str] = field(default_factory=list)
    behavioral_patterns: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    se_vulnerability: SEVulnerability = SEVulnerability.INFO
    se_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "target_username": self.target_username,
            "target_email": self.target_email,
            "target_name": self.target_name,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "findings": [asdict(f) for f in self.findings],
            "contact_info": self.contact_info,
            "social_profiles": self.social_profiles,
            "platform_presence": self.platform_presence,
            "behavioral_patterns": self.behavioral_patterns,
            "locations": self.locations,
            "se_vulnerability": self.se_vulnerability.value,
            "se_score": self.se_score,
            "recommendations": self.recommendations,
            "statistics": self.statistics,
            "error": self.error,
        }


class TargetProfilingWorkflow:
    """Deep Target Profiling AI-Driven Workflow.

    Orchestrates multiple OSINT services to build comprehensive target profile for security assessment.
    """

    def __init__(
        self,
        osint_service_url: str = "http://localhost:8036",
    ):
        """Initialize target profiling workflow.

        Args:
            osint_service_url: OSINT Service endpoint
        """
        self.osint_url = osint_service_url

        # Workflow state
        self.active_workflows: Dict[str, TargetProfileReport] = {}

        logger.info("TargetProfilingWorkflow initialized")

    async def execute(self, target: ProfileTarget) -> TargetProfileReport:
        """Execute deep target profiling workflow.

        Args:
            target: Target configuration

        Returns:
            TargetProfileReport with complete profile
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = TargetProfileReport(
            workflow_id=workflow_id,
            target_username=target.username,
            target_email=target.email,
            target_name=target.name,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )

        self.active_workflows[workflow_id] = report

        try:
            logger.info(f"Starting deep profiling for {target.username or target.email or target.name} (workflow_id={workflow_id})")

            # Phase 1: Email/phone extraction and validation
            contact_findings = await self._analyze_contact_info(target.email, target.phone)
            report.findings.extend(contact_findings)
            report.contact_info = self._extract_contact_summary(contact_findings)
            logger.info(f"Phase 1: Analyzed contact info - {len(contact_findings)} findings")

            # Phase 2: Social media scraping
            if target.include_social and target.username:
                social_findings = await self._scrape_social_media(target.username)
                report.findings.extend(social_findings)
                report.social_profiles = self._extract_social_profiles(social_findings)
                logger.info(f"Phase 2: Found {len(report.social_profiles)} social profiles")

            # Phase 3: Username platform enumeration
            if target.username:
                platform_findings = await self._enumerate_platforms(target.username)
                report.findings.extend(platform_findings)
                report.platform_presence = [f.details["platform"] for f in platform_findings if f.details.get("found")]
                logger.info(f"Phase 3: Found presence on {len(report.platform_presence)} platforms")

            # Phase 4: Image metadata extraction
            if target.include_images and target.image_url:
                image_findings = await self._analyze_images(target.image_url)
                report.findings.extend(image_findings)
                report.locations.extend(self._extract_locations(image_findings))
                logger.info(f"Phase 4: Analyzed images - {len(image_findings)} findings")

            # Phase 5: Pattern detection
            pattern_findings = await self._detect_patterns(report.findings)
            report.findings.extend(pattern_findings)
            report.behavioral_patterns = self._extract_patterns(pattern_findings)
            logger.info(f"Phase 5: Detected {len(report.behavioral_patterns)} behavioral patterns")

            # Phase 6: Calculate SE vulnerability score
            report.se_score, report.se_vulnerability = self._calculate_se_vulnerability(report.findings, report)

            # Phase 7: Generate statistics
            report.statistics = self._generate_statistics(report.findings, report)

            # Phase 8: Generate recommendations
            report.recommendations = self._generate_recommendations(report)

            # Mark complete
            report.status = WorkflowStatus.COMPLETED
            report.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Target profiling completed: {len(report.findings)} findings, SE_score={report.se_score:.2f}")

        except Exception as e:
            logger.error(f"Target profiling workflow failed: {e}")
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    async def _analyze_contact_info(self, email: Optional[str], phone: Optional[str]) -> List[ProfileFinding]:
        """Analyze email and phone information.

        Args:
            email: Email address
            phone: Phone number

        Returns:
            List of contact findings
        """
        # Simulate email/phone analysis
        # In production: Call OSINT Service EmailAnalyzer + PhoneAnalyzer
        await asyncio.sleep(0.3)

        findings = []

        if email:
            findings.append(ProfileFinding(
                finding_id=str(uuid4()),
                finding_type="contact",
                category="email",
                details={
                    "email": email,
                    "valid": True,
                    "domain": email.split("@")[1] if "@" in email else None,
                    "common_domain": email.endswith(("gmail.com", "yahoo.com", "hotmail.com", "outlook.com")),
                    "phishing_score": 0.0,
                },
                timestamp=datetime.utcnow().isoformat(),
            ))

        if phone:
            findings.append(ProfileFinding(
                finding_id=str(uuid4()),
                finding_type="contact",
                category="phone",
                details={
                    "phone": phone,
                    "valid": True,
                    "country": "USA" if phone.startswith("+1") else "Unknown",
                    "normalized": phone.replace("-", "").replace(" ", ""),
                },
                timestamp=datetime.utcnow().isoformat(),
            ))

        return findings

    async def _scrape_social_media(self, username: str) -> List[ProfileFinding]:
        """Scrape social media profiles.

        Args:
            username: Username to search

        Returns:
            List of social media findings
        """
        # Simulate social media scraping
        # In production: Call OSINT Service SocialScraper
        await asyncio.sleep(0.6)

        findings = []

        # Simulate Twitter profile
        findings.append(ProfileFinding(
            finding_id=str(uuid4()),
            finding_type="social",
            category="twitter",
            details={
                "platform": "twitter",
                "username": username,
                "display_name": "John Doe",
                "bio": "Software engineer | Open source enthusiast",
                "followers": 1234,
                "following": 567,
                "tweets": 5678,
                "verified": False,
                "location": "San Francisco, CA",
                "created_at": "2015-03-15",
                "profile_url": f"https://twitter.com/{username}",
            },
            timestamp=datetime.utcnow().isoformat(),
        ))

        # Simulate recent tweets
        findings.append(ProfileFinding(
            finding_id=str(uuid4()),
            finding_type="social",
            category="twitter_activity",
            details={
                "platform": "twitter",
                "username": username,
                "recent_tweets": [
                    {"text": "Just finished a great coding session!", "timestamp": "2025-10-14T10:30:00Z"},
                    {"text": "Coffee break time ☕", "timestamp": "2025-10-14T14:15:00Z"},
                ],
                "activity_pattern": "Active mornings and afternoons (PST)",
            },
            timestamp=datetime.utcnow().isoformat(),
        ))

        return findings

    async def _enumerate_platforms(self, username: str) -> List[ProfileFinding]:
        """Enumerate username across platforms.

        Args:
            username: Username to search

        Returns:
            List of platform findings
        """
        # Simulate platform enumeration
        # In production: Call OSINT Service UsernameHunter
        await asyncio.sleep(0.5)

        findings = []

        platforms = [
            ("GitHub", True, "https://github.com"),
            ("Reddit", True, "https://reddit.com"),
            ("Medium", False, "https://medium.com"),
            ("StackOverflow", True, "https://stackoverflow.com"),
            ("LinkedIn", True, "https://linkedin.com"),
            ("Pastebin", False, "https://pastebin.com"),
        ]

        for platform_name, found, base_url in platforms:
            findings.append(ProfileFinding(
                finding_id=str(uuid4()),
                finding_type="platform",
                category="username_enumeration",
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

    async def _analyze_images(self, image_url: str) -> List[ProfileFinding]:
        """Analyze images for metadata (EXIF, GPS).

        Args:
            image_url: Image URL

        Returns:
            List of image findings
        """
        # Simulate image analysis
        # In production: Call OSINT Service ImageAnalyzer
        await asyncio.sleep(0.4)

        findings = []

        # Simulate EXIF data
        findings.append(ProfileFinding(
            finding_id=str(uuid4()),
            finding_type="image",
            category="exif",
            details={
                "image_url": image_url,
                "exif_available": True,
                "camera_model": "iPhone 13 Pro",
                "software": "iOS 16.5",
                "datetime": "2025:10:10 14:30:22",
                "gps_latitude": 37.7749,
                "gps_longitude": -122.4194,
                "gps_location": "San Francisco, CA",
            },
            timestamp=datetime.utcnow().isoformat(),
        ))

        return findings

    async def _detect_patterns(self, existing_findings: List[ProfileFinding]) -> List[ProfileFinding]:
        """Detect behavioral and location patterns.

        Args:
            existing_findings: Existing findings to analyze

        Returns:
            List of pattern findings
        """
        # Simulate pattern detection
        # In production: Call OSINT Service PatternDetector
        await asyncio.sleep(0.3)

        findings = []

        # Detect activity patterns from social findings
        social_findings = [f for f in existing_findings if f.finding_type == "social"]
        if social_findings:
            findings.append(ProfileFinding(
                finding_id=str(uuid4()),
                finding_type="pattern",
                category="activity_pattern",
                details={
                    "pattern_type": "time_based",
                    "description": "Most active during PST business hours (9 AM - 6 PM)",
                    "confidence": 0.85,
                    "data_points": len(social_findings),
                },
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.85,
            ))

        # Detect location patterns
        location_findings = [f for f in existing_findings if "location" in f.details or "gps_location" in f.details]
        if location_findings:
            findings.append(ProfileFinding(
                finding_id=str(uuid4()),
                finding_type="pattern",
                category="location_pattern",
                details={
                    "pattern_type": "geographic",
                    "description": "Primarily located in San Francisco Bay Area",
                    "confidence": 0.9,
                    "locations": ["San Francisco, CA"],
                },
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.9,
            ))

        # Detect interest patterns from social bio/tweets
        findings.append(ProfileFinding(
            finding_id=str(uuid4()),
            finding_type="pattern",
            category="interest_pattern",
            details={
                "pattern_type": "behavioral",
                "description": "Strong interest in technology, software engineering, open source",
                "keywords": ["coding", "software", "open source", "engineer"],
                "confidence": 0.8,
            },
            timestamp=datetime.utcnow().isoformat(),
            confidence=0.8,
        ))

        return findings

    def _extract_contact_summary(self, contact_findings: List[ProfileFinding]) -> Dict[str, Any]:
        """Extract contact information summary.

        Args:
            contact_findings: Contact findings

        Returns:
            Contact summary dictionary
        """
        summary = {
            "emails": [],
            "phones": [],
            "validated": False,
        }

        for finding in contact_findings:
            if finding.category == "email":
                summary["emails"].append(finding.details)
                if finding.details.get("valid"):
                    summary["validated"] = True
            elif finding.category == "phone":
                summary["phones"].append(finding.details)

        return summary

    def _extract_social_profiles(self, social_findings: List[ProfileFinding]) -> List[Dict[str, Any]]:
        """Extract social profile summaries.

        Args:
            social_findings: Social findings

        Returns:
            List of social profile dictionaries
        """
        profiles = []

        for finding in social_findings:
            if finding.category in ["twitter", "linkedin", "facebook"]:
                profiles.append({
                    "platform": finding.details.get("platform"),
                    "username": finding.details.get("username"),
                    "display_name": finding.details.get("display_name"),
                    "url": finding.details.get("profile_url"),
                    "followers": finding.details.get("followers"),
                    "bio": finding.details.get("bio"),
                })

        return profiles

    def _extract_locations(self, image_findings: List[ProfileFinding]) -> List[Dict[str, Any]]:
        """Extract location information from images.

        Args:
            image_findings: Image findings

        Returns:
            List of location dictionaries
        """
        locations = []

        for finding in image_findings:
            if finding.category == "exif" and "gps_location" in finding.details:
                locations.append({
                    "location": finding.details["gps_location"],
                    "latitude": finding.details.get("gps_latitude"),
                    "longitude": finding.details.get("gps_longitude"),
                    "source": "image_exif",
                    "timestamp": finding.details.get("datetime"),
                })

        return locations

    def _extract_patterns(self, pattern_findings: List[ProfileFinding]) -> List[Dict[str, Any]]:
        """Extract behavioral patterns.

        Args:
            pattern_findings: Pattern findings

        Returns:
            List of pattern dictionaries
        """
        patterns = []

        for finding in pattern_findings:
            if finding.finding_type == "pattern":
                patterns.append({
                    "type": finding.category,
                    "description": finding.details.get("description"),
                    "confidence": finding.confidence,
                })

        return patterns

    def _calculate_se_vulnerability(
        self, findings: List[ProfileFinding], report: TargetProfileReport
    ) -> tuple[float, SEVulnerability]:
        """Calculate social engineering vulnerability score.

        Args:
            findings: All findings
            report: Current report state

        Returns:
            Tuple of (score, vulnerability_level)
        """
        score = 0.0

        # Contact information exposure (+15 points per contact)
        if report.contact_info.get("emails"):
            score += 15.0 * len(report.contact_info["emails"])
        if report.contact_info.get("phones"):
            score += 15.0 * len(report.contact_info["phones"])

        # Social media presence (+10 points per profile)
        score += 10.0 * len(report.social_profiles)

        # Platform presence (+5 points per platform)
        score += 5.0 * len(report.platform_presence)

        # Location exposure (+20 points)
        if report.locations:
            score += 20.0

        # Behavioral patterns (+10 points per pattern)
        score += 10.0 * len(report.behavioral_patterns)

        # Public activity bonus
        twitter_profiles = [p for p in report.social_profiles if p.get("platform") == "twitter"]
        if twitter_profiles:
            followers = twitter_profiles[0].get("followers", 0)
            if followers > 1000:
                score += 10.0  # High visibility
            elif followers > 100:
                score += 5.0  # Medium visibility

        # Normalize to 0-100
        se_score = min(100.0, score)

        # Determine vulnerability level
        if se_score >= 70:
            vulnerability = SEVulnerability.CRITICAL
        elif se_score >= 50:
            vulnerability = SEVulnerability.HIGH
        elif se_score >= 30:
            vulnerability = SEVulnerability.MEDIUM
        elif se_score >= 10:
            vulnerability = SEVulnerability.LOW
        else:
            vulnerability = SEVulnerability.INFO

        return round(se_score, 2), vulnerability

    def _generate_statistics(self, findings: List[ProfileFinding], report: TargetProfileReport) -> Dict[str, Any]:
        """Generate statistics from findings.

        Args:
            findings: All findings
            report: Current report state

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_findings": len(findings),
            "by_type": {},
            "contact_count": len(report.contact_info.get("emails", [])) + len(report.contact_info.get("phones", [])),
            "social_profiles_count": len(report.social_profiles),
            "platforms_present": len(report.platform_presence),
            "locations_found": len(report.locations),
            "patterns_detected": len(report.behavioral_patterns),
        }

        for finding in findings:
            ftype = finding.finding_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

        return stats

    def _generate_recommendations(self, report: TargetProfileReport) -> List[str]:
        """Generate security recommendations.

        Args:
            report: Complete report

        Returns:
            List of recommendations
        """
        recommendations = []

        # High-level recommendations based on SE vulnerability
        if report.se_vulnerability == SEVulnerability.CRITICAL:
            recommendations.append("CRITICAL: Target is highly susceptible to social engineering attacks")
            recommendations.append("Recommend immediate security awareness training")
        elif report.se_vulnerability == SEVulnerability.HIGH:
            recommendations.append("HIGH: Significant social engineering risk detected")
            recommendations.append("Implement enhanced verification procedures for this target")
        elif report.se_vulnerability == SEVulnerability.MEDIUM:
            recommendations.append("MEDIUM: Moderate social engineering risk")
            recommendations.append("Standard security protocols apply")
        else:
            recommendations.append("LOW: Limited social engineering risk detected")

        # Contact exposure recommendations
        if report.contact_info.get("emails"):
            recommendations.append(f"{len(report.contact_info['emails'])} email(s) publicly exposed - recommend privacy review")

        # Social media recommendations
        if len(report.social_profiles) > 2:
            recommendations.append(f"Multiple social profiles ({len(report.social_profiles)}) increase attack surface")
            recommendations.append("Review privacy settings on all social platforms")

        # Location recommendations
        if report.locations:
            recommendations.append("PRIVACY: Location data found in image metadata")
            recommendations.append("Recommend disabling GPS tagging on mobile devices")

        # Platform presence recommendations
        if len(report.platform_presence) > 5:
            recommendations.append(f"Presence on {len(report.platform_presence)} platforms increases reconnaissance exposure")
            recommendations.append("Consider using unique usernames per platform")

        # Behavioral pattern recommendations
        activity_patterns = [p for p in report.behavioral_patterns if p["type"] == "activity_pattern"]
        if activity_patterns:
            recommendations.append("Predictable activity patterns detected - vary posting times for OPSEC")

        # General recommendations
        recommendations.append("Enable two-factor authentication on all accounts")
        recommendations.append("Regularly audit public information exposure")
        recommendations.append("Use different usernames across platforms to reduce correlation")
        recommendations.append("Disable location services for social media applications")

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
            "target_username": report.target_username,
            "target_email": report.target_email,
            "findings_count": len(report.findings),
            "se_score": report.se_score,
            "se_vulnerability": report.se_vulnerability.value,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
