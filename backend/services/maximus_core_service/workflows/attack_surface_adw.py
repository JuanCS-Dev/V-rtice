"""ADW #1: External Attack Surface Mapping Workflow.

Combines Network Recon + Vuln Intel + Service Detection for comprehensive attack surface analysis.

Workflow Steps:
1. Passive DNS enumeration (subdomains)
2. Port scanning (Nmap/Masscan)
3. Service detection + version identification
4. CVE correlation for detected services
5. Nuclei vulnerability scanning
6. Risk scoring + prioritization
7. Generate attack surface report

Services Integrated:
- Network Recon Service (nmap/masscan)
- Vuln Intel Service (CVE correlator)
- Offensive Orchestrator Recon Agent (passive DNS)
- Vuln Scanner Service (Nuclei)

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


class RiskLevel(Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AttackSurfaceTarget:
    """Target for attack surface mapping."""
    domain: str
    include_subdomains: bool = True
    port_range: Optional[str] = None  # e.g., "1-1000" or "80,443,22"
    scan_depth: str = "standard"  # standard, deep, quick


@dataclass
class Finding:
    """Individual attack surface finding."""
    finding_id: str
    finding_type: str  # subdomain, open_port, service, vulnerability
    severity: RiskLevel
    target: str
    details: Dict[str, Any]
    timestamp: str
    confidence: float = 1.0


@dataclass
class AttackSurfaceReport:
    """Complete attack surface mapping report."""
    workflow_id: str
    target: str
    status: WorkflowStatus
    started_at: str
    completed_at: Optional[str]
    findings: List[Finding] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "target": self.target,
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
            "statistics": self.statistics,
            "risk_score": self.risk_score,
            "recommendations": self.recommendations,
            "error": self.error,
        }


class AttackSurfaceWorkflow:
    """External Attack Surface Mapping AI-Driven Workflow.

    Orchestrates multiple OSINT services to build comprehensive attack surface map.
    """

    def __init__(
        self,
        network_recon_service_url: str = "http://localhost:8032",
        vuln_intel_service_url: str = "http://localhost:8045",
        vuln_scanner_service_url: str = "http://localhost:8046",
    ):
        """Initialize attack surface workflow.

        Args:
            network_recon_service_url: Network Recon Service endpoint
            vuln_intel_service_url: Vuln Intel Service endpoint
            vuln_scanner_service_url: Vuln Scanner Service endpoint
        """
        self.network_recon_url = network_recon_service_url
        self.vuln_intel_url = vuln_intel_service_url
        self.vuln_scanner_url = vuln_scanner_service_url

        # Workflow state
        self.active_workflows: Dict[str, AttackSurfaceReport] = {}

        logger.info("AttackSurfaceWorkflow initialized")

    async def execute(self, target: AttackSurfaceTarget) -> AttackSurfaceReport:
        """Execute attack surface mapping workflow.

        Args:
            target: Target configuration

        Returns:
            AttackSurfaceReport with complete findings
        """
        workflow_id = str(uuid4())
        started_at = datetime.utcnow().isoformat()

        report = AttackSurfaceReport(
            workflow_id=workflow_id,
            target=target.domain,
            status=WorkflowStatus.RUNNING,
            started_at=started_at,
            completed_at=None,
        )

        self.active_workflows[workflow_id] = report

        try:
            logger.info(f"Starting attack surface mapping for {target.domain} (workflow_id={workflow_id})")

            # Phase 1: Subdomain enumeration (passive DNS)
            subdomains = await self._enumerate_subdomains(target.domain, target.include_subdomains)
            report.findings.extend(subdomains)
            logger.info(f"Phase 1: Found {len(subdomains)} subdomains")

            # Phase 2: Port scanning on all discovered targets
            all_targets = [target.domain] + [f.details["subdomain"] for f in subdomains]
            port_scan_findings = await self._scan_ports(all_targets, target.port_range)
            report.findings.extend(port_scan_findings)
            logger.info(f"Phase 2: Found {len(port_scan_findings)} open ports")

            # Phase 3: Service detection on open ports
            service_findings = await self._detect_services(port_scan_findings)
            report.findings.extend(service_findings)
            logger.info(f"Phase 3: Detected {len(service_findings)} services")

            # Phase 4: CVE correlation for detected services
            cve_findings = await self._correlate_cves(service_findings)
            report.findings.extend(cve_findings)
            logger.info(f"Phase 4: Found {len(cve_findings)} CVEs")

            # Phase 5: Nuclei vulnerability scanning (if deep scan)
            if target.scan_depth == "deep":
                nuclei_findings = await self._nuclei_scan(all_targets)
                report.findings.extend(nuclei_findings)
                logger.info(f"Phase 5: Nuclei found {len(nuclei_findings)} vulnerabilities")

            # Phase 6: Calculate risk score
            report.risk_score = self._calculate_risk_score(report.findings)

            # Phase 7: Generate statistics
            report.statistics = self._generate_statistics(report.findings)

            # Phase 8: Generate recommendations
            report.recommendations = self._generate_recommendations(report.findings, report.risk_score)

            # Mark complete
            report.status = WorkflowStatus.COMPLETED
            report.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Attack surface mapping completed: {len(report.findings)} findings, risk_score={report.risk_score:.2f}")

        except Exception as e:
            logger.error(f"Attack surface workflow failed: {e}")
            report.status = WorkflowStatus.FAILED
            report.error = str(e)
            report.completed_at = datetime.utcnow().isoformat()

        return report

    async def _enumerate_subdomains(self, domain: str, include_subdomains: bool) -> List[Finding]:
        """Enumerate subdomains using passive DNS (simulated).

        Args:
            domain: Target domain
            include_subdomains: Whether to include subdomain enumeration

        Returns:
            List of subdomain findings
        """
        if not include_subdomains:
            return []

        # Simulate passive DNS enumeration
        # In production: Call Offensive Orchestrator Recon Agent (passive phase)
        await asyncio.sleep(0.5)

        common_subdomains = ["www", "mail", "ftp", "admin", "api", "dev", "staging"]
        findings = []

        for subdomain_prefix in common_subdomains:
            subdomain = f"{subdomain_prefix}.{domain}"
            findings.append(Finding(
                finding_id=str(uuid4()),
                finding_type="subdomain",
                severity=RiskLevel.INFO,
                target=domain,
                details={
                    "subdomain": subdomain,
                    "source": "passive_dns",
                    "confidence": 0.8,
                },
                timestamp=datetime.utcnow().isoformat(),
                confidence=0.8,
            ))

        return findings

    async def _scan_ports(self, targets: List[str], port_range: Optional[str]) -> List[Finding]:
        """Scan ports on targets using Nmap/Masscan.

        Args:
            targets: List of targets to scan
            port_range: Port range specification

        Returns:
            List of open port findings
        """
        # Simulate port scanning
        # In production: Call Network Recon Service (Nmap/Masscan)
        await asyncio.sleep(1.0)

        common_ports = [80, 443, 22, 21, 25, 3306, 5432, 6379, 8080, 8443]
        if port_range:
            # Parse port range (simplified)
            common_ports = [80, 443, 22]

        findings = []
        for target in targets[:3]:  # Limit for simulation
            for port in common_ports[:5]:  # Top 5 ports
                findings.append(Finding(
                    finding_id=str(uuid4()),
                    finding_type="open_port",
                    severity=RiskLevel.LOW if port in [80, 443] else RiskLevel.MEDIUM,
                    target=target,
                    details={
                        "port": port,
                        "protocol": "tcp",
                        "state": "open",
                        "scanner": "nmap",
                    },
                    timestamp=datetime.utcnow().isoformat(),
                ))

        return findings

    async def _detect_services(self, port_findings: List[Finding]) -> List[Finding]:
        """Detect services and versions on open ports.

        Args:
            port_findings: Open port findings

        Returns:
            List of service findings
        """
        # Simulate service detection
        # In production: Call Network Recon Service (service detection)
        await asyncio.sleep(0.8)

        service_map = {
            80: ("nginx", "1.18.0"),
            443: ("nginx", "1.18.0"),
            22: ("OpenSSH", "8.2p1"),
            21: ("vsftpd", "3.0.3"),
            3306: ("MySQL", "5.7.33"),
        }

        findings = []
        for port_finding in port_findings:
            port = port_finding.details.get("port")
            if port in service_map:
                service_name, version = service_map[port]
                findings.append(Finding(
                    finding_id=str(uuid4()),
                    finding_type="service",
                    severity=RiskLevel.INFO,
                    target=port_finding.target,
                    details={
                        "port": port,
                        "service": service_name,
                        "version": version,
                        "banner": f"{service_name}/{version}",
                    },
                    timestamp=datetime.utcnow().isoformat(),
                ))

        return findings

    async def _correlate_cves(self, service_findings: List[Finding]) -> List[Finding]:
        """Correlate CVEs with detected services.

        Args:
            service_findings: Service findings

        Returns:
            List of CVE findings
        """
        # Simulate CVE correlation
        # In production: Call Vuln Intel Service (CVE correlator)
        await asyncio.sleep(0.5)

        findings = []
        for service_finding in service_findings:
            service = service_finding.details.get("service", "").lower()
            version = service_finding.details.get("version", "")

            # Simulate CVE lookup
            if "nginx" in service and version.startswith("1.18"):
                findings.append(Finding(
                    finding_id=str(uuid4()),
                    finding_type="vulnerability",
                    severity=RiskLevel.MEDIUM,
                    target=service_finding.target,
                    details={
                        "cve_id": "CVE-2021-23017",
                        "service": service,
                        "version": version,
                        "description": "nginx DNS resolver off-by-one heap write",
                        "cvss_score": 6.4,
                        "exploit_available": False,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                ))

            if "openssh" in service:
                findings.append(Finding(
                    finding_id=str(uuid4()),
                    finding_type="vulnerability",
                    severity=RiskLevel.HIGH,
                    target=service_finding.target,
                    details={
                        "cve_id": "CVE-2023-38408",
                        "service": service,
                        "version": version,
                        "description": "OpenSSH remote code execution",
                        "cvss_score": 8.1,
                        "exploit_available": True,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                ))

        return findings

    async def _nuclei_scan(self, targets: List[str]) -> List[Finding]:
        """Run Nuclei vulnerability scanner.

        Args:
            targets: List of targets

        Returns:
            List of vulnerability findings
        """
        # Simulate Nuclei scan
        # In production: Call Vuln Scanner Service (Nuclei wrapper)
        await asyncio.sleep(2.0)

        findings = []
        for target in targets[:2]:  # Limit for simulation
            findings.append(Finding(
                finding_id=str(uuid4()),
                finding_type="vulnerability",
                severity=RiskLevel.MEDIUM,
                target=target,
                details={
                    "template": "http-missing-security-headers",
                    "name": "Missing Security Headers",
                    "matched_at": f"https://{target}",
                    "scanner": "nuclei",
                },
                timestamp=datetime.utcnow().isoformat(),
            ))

        return findings

    def _calculate_risk_score(self, findings: List[Finding]) -> float:
        """Calculate overall risk score.

        Args:
            findings: All findings

        Returns:
            Risk score (0-100)
        """
        severity_weights = {
            RiskLevel.CRITICAL: 10.0,
            RiskLevel.HIGH: 7.0,
            RiskLevel.MEDIUM: 4.0,
            RiskLevel.LOW: 1.0,
            RiskLevel.INFO: 0.1,
        }

        total_score = sum(severity_weights.get(f.severity, 0) for f in findings)

        # Normalize to 0-100 scale
        max_possible = len(findings) * 10.0 if findings else 1
        risk_score = min(100.0, (total_score / max_possible) * 100.0)

        return round(risk_score, 2)

    def _generate_statistics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate statistics from findings.

        Args:
            findings: All findings

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_findings": len(findings),
            "by_type": {},
            "by_severity": {},
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "info_count": 0,
        }

        for finding in findings:
            # Count by type
            ftype = finding.finding_type
            stats["by_type"][ftype] = stats["by_type"].get(ftype, 0) + 1

            # Count by severity
            severity = finding.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            # Count specific severities
            if finding.severity == RiskLevel.CRITICAL:
                stats["critical_count"] += 1
            elif finding.severity == RiskLevel.HIGH:
                stats["high_count"] += 1
            elif finding.severity == RiskLevel.MEDIUM:
                stats["medium_count"] += 1
            elif finding.severity == RiskLevel.LOW:
                stats["low_count"] += 1
            elif finding.severity == RiskLevel.INFO:
                stats["info_count"] += 1

        return stats

    def _generate_recommendations(self, findings: List[Finding], risk_score: float) -> List[str]:
        """Generate remediation recommendations.

        Args:
            findings: All findings
            risk_score: Overall risk score

        Returns:
            List of recommendations
        """
        recommendations = []

        # High-level recommendations based on risk score
        if risk_score >= 70:
            recommendations.append("CRITICAL: Immediate remediation required - attack surface highly vulnerable")
        elif risk_score >= 50:
            recommendations.append("HIGH: Prioritize patching identified vulnerabilities")
        elif risk_score >= 30:
            recommendations.append("MEDIUM: Schedule remediation for identified issues")
        else:
            recommendations.append("LOW: Maintain current security posture, monitor for changes")

        # Specific recommendations based on findings
        vuln_findings = [f for f in findings if f.finding_type == "vulnerability"]
        if vuln_findings:
            high_severity = [f for f in vuln_findings if f.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]]
            if high_severity:
                recommendations.append(f"Patch {len(high_severity)} high/critical vulnerabilities immediately")

            exploitable = [f for f in vuln_findings if f.details.get("exploit_available")]
            if exploitable:
                recommendations.append(f"URGENT: {len(exploitable)} vulnerabilities have public exploits available")

        # Service-specific recommendations
        service_findings = [f for f in findings if f.finding_type == "service"]
        outdated_services = [f for f in service_findings if "nginx" in f.details.get("service", "").lower()]
        if outdated_services:
            recommendations.append("Update web servers to latest stable versions")

        # Port exposure recommendations
        port_findings = [f for f in findings if f.finding_type == "open_port"]
        sensitive_ports = [f for f in port_findings if f.details.get("port") in [21, 23, 3389]]
        if sensitive_ports:
            recommendations.append(f"Close {len(sensitive_ports)} sensitive ports or restrict access")

        # Subdomain recommendations
        subdomain_findings = [f for f in findings if f.finding_type == "subdomain"]
        if len(subdomain_findings) > 10:
            recommendations.append("Review subdomain inventory - reduce attack surface by decommissioning unused domains")

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
            "target": report.target,
            "findings_count": len(report.findings),
            "risk_score": report.risk_score,
            "started_at": report.started_at,
            "completed_at": report.completed_at,
        }
