"""
Execution Planner
==================

AI-powered plan generation for autonomous security workflows.

Generates multi-phase execution plans based on user objectives.
"""

import logging
from typing import List, Dict, Any, Optional
from .models import (
    ExecutionPlan,
    ExecutionPhase,
    ExecutionStep,
    ObjectiveType,
    RiskLevel,
    PhaseStatus,
    StepStatus
)

logger = logging.getLogger(__name__)


class ExecutionPlanner:
    """
    Generates execution plans for autopilot workflows.

    Creates multi-phase plans optimized for:
    - Penetration testing
    - Defensive hardening
    - Incident investigation
    - Continuous monitoring
    """

    def __init__(self):
        """Initialize planner with predefined templates."""
        self.templates = {
            ObjectiveType.PENTEST: self._pentest_template,
            ObjectiveType.DEFEND: self._defend_template,
            ObjectiveType.INVESTIGATE: self._investigate_template,
            ObjectiveType.MONITOR: self._monitor_template
        }

    def create_plan(
        self,
        objective: ObjectiveType,
        target: str,
        workspace: str,
        scope: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Create execution plan based on objective.

        Args:
            objective: Type of operation (pentest, defend, etc.)
            target: Target specification (IP, domain, network range)
            workspace: Workspace name for results
            scope: Additional scope parameters

        Returns:
            Complete execution plan with phases and steps

        Example:
            planner = ExecutionPlanner()
            plan = planner.create_plan(
                objective=ObjectiveType.PENTEST,
                target="10.10.1.0/24",
                workspace="pentest-acme",
                scope={"depth": "full", "web_scan": True}
            )
        """
        scope = scope or {}

        # Select template based on objective
        template_fn = self.templates.get(objective, self._pentest_template)

        # Generate plan from template
        plan = template_fn(target, workspace, scope)

        logger.info(
            f"Generated {objective.value} plan: {plan.total_steps} steps "
            f"across {len(plan.phases)} phases"
        )

        return plan

    def _pentest_template(
        self,
        target: str,
        workspace: str,
        scope: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Penetration testing plan template.

        Phases:
        1. Reconnaissance (passive + active)
        2. Port Scanning (SYN + service detection)
        3. Vulnerability Assessment (Nuclei + Nikto)
        4. Exploitation (REQUIRES APPROVAL)
        5. Post-Exploitation (REQUIRES APPROVAL)
        """

        # Phase 1: Reconnaissance
        recon_phase = ExecutionPhase(
            id="1",
            name="Reconnaissance",
            description="Discover live hosts and gather intelligence",
            estimated_time=300,  # 5 minutes
            requires_approval=False,
            risk_level=RiskLevel.LOW,
            steps=[
                ExecutionStep(
                    id="1.1",
                    name=f"Ping sweep {target}",
                    tool="nmap",
                    command=f"nmap -sn {target} -oX -",
                    description="Find live hosts",
                    estimated_time=60,
                    requires_approval=False
                ),
                ExecutionStep(
                    id="1.2",
                    name="Reverse DNS lookup",
                    tool="nmap",
                    command=f"nmap -sL {target} -oX -",
                    description="Map hostnames",
                    estimated_time=30,
                    requires_approval=False
                ),
                ExecutionStep(
                    id="1.3",
                    name="WHOIS/ASN enumeration",
                    tool="whois",
                    command=f"whois {target}",
                    description="Organization info",
                    estimated_time=10,
                    requires_approval=False
                )
            ]
        )

        # Phase 2: Port Scanning
        scan_phase = ExecutionPhase(
            id="2",
            name="Port Scanning",
            description="Identify open ports and running services",
            estimated_time=600,  # 10 minutes
            requires_approval=False,
            risk_level=RiskLevel.LOW,
            steps=[
                ExecutionStep(
                    id="2.1",
                    name="Nmap SYN scan all hosts",
                    tool="nmap",
                    command=f"nmap -sS -T4 {target} -oX -",
                    description="Open ports discovery",
                    estimated_time=300,
                    requires_approval=False
                ),
                ExecutionStep(
                    id="2.2",
                    name="Service detection + versioning",
                    tool="nmap",
                    command=f"nmap -sV --version-intensity 5 {target} -oX -",
                    description="Identify software versions",
                    estimated_time=240,
                    requires_approval=False
                ),
                ExecutionStep(
                    id="2.3",
                    name="OS detection",
                    tool="nmap",
                    command=f"nmap -O {target} -oX -",
                    description="Platform identification",
                    estimated_time=60,
                    requires_approval=False
                )
            ]
        )

        # Phase 3: Vulnerability Assessment
        vuln_phase = ExecutionPhase(
            id="3",
            name="Vulnerability Assessment",
            description="Scan for known vulnerabilities and misconfigurations",
            estimated_time=480,  # 8 minutes
            requires_approval=False,
            risk_level=RiskLevel.MEDIUM,
            steps=[
                ExecutionStep(
                    id="3.1",
                    name="Nuclei CVE scan",
                    tool="nuclei",
                    command=f"nuclei -u {target} -t cves/ -json -silent",
                    description="Check known CVEs",
                    estimated_time=180,
                    requires_approval=False
                ),
                ExecutionStep(
                    id="3.2",
                    name="Nikto web scan",
                    tool="nikto",
                    command=f"nikto -h {target} -Format txt",
                    description="Web vulnerability scan",
                    estimated_time=240,
                    requires_approval=False,
                    metadata={"conditional": "if HTTP/HTTPS found"}
                ),
                ExecutionStep(
                    id="3.3",
                    name="Default credential check",
                    tool="hydra",
                    command=f"hydra -C /usr/share/wordlists/default-credentials.txt {target}",
                    description="Test common passwords",
                    estimated_time=60,
                    requires_approval=False
                )
            ]
        )

        # Phase 4: Exploitation (REQUIRES APPROVAL)
        exploit_phase = ExecutionPhase(
            id="4",
            name="Exploitation",
            description="Test exploits for critical vulnerabilities (REQUIRES APPROVAL)",
            estimated_time=600,  # 10 minutes
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
            status=PhaseStatus.PENDING,
            steps=[
                ExecutionStep(
                    id="4.1",
                    name="Test exploits for critical vulns",
                    tool="metasploit",
                    command="msfconsole -q -x 'use exploit/...; set RHOST ...; run'",
                    description="PoC validation",
                    estimated_time=300,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="4.2",
                    name="Lateral movement testing",
                    tool="metasploit",
                    command="msfconsole -q -x 'use auxiliary/scanner/...'",
                    description="Pivot testing",
                    estimated_time=180,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="4.3",
                    name="Privilege escalation attempts",
                    tool="metasploit",
                    command="msfconsole -q -x 'use exploit/linux/local/...'",
                    description="Admin access testing",
                    estimated_time=120,
                    requires_approval=True
                )
            ]
        )

        # Phase 5: Post-Exploitation (REQUIRES APPROVAL)
        postex_phase = ExecutionPhase(
            id="5",
            name="Post-Exploitation",
            description="Credential harvesting and persistence (REQUIRES APPROVAL)",
            estimated_time=420,  # 7 minutes
            requires_approval=True,
            risk_level=RiskLevel.CRITICAL,
            status=PhaseStatus.PENDING,
            steps=[
                ExecutionStep(
                    id="5.1",
                    name="Credential harvesting",
                    tool="metasploit",
                    command="msfconsole -q -x 'use post/...; run'",
                    description="Dump hashes",
                    estimated_time=180,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="5.2",
                    name="Persistence mechanisms",
                    tool="metasploit",
                    command="msfconsole -q -x 'use exploit/...; run'",
                    description="Maintain access",
                    estimated_time=120,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="5.3",
                    name="Data exfiltration simulation",
                    tool="custom",
                    command="dd if=/dev/urandom of=/tmp/test.dat bs=1M count=10",
                    description="Impact assessment",
                    estimated_time=120,
                    requires_approval=True
                )
            ]
        )

        # Build execution plan
        phases = [recon_phase, scan_phase, vuln_phase]

        # Add exploitation phases only if scope permits
        if scope.get("allow_exploitation", False):
            phases.extend([exploit_phase, postex_phase])

        plan = ExecutionPlan(
            name=f"Penetration Test - {target}",
            objective=ObjectiveType.PENTEST,
            target=target,
            workspace=workspace,
            description=f"Comprehensive penetration test of {target}",
            phases=phases,
            risk_level=RiskLevel.HIGH if scope.get("allow_exploitation") else RiskLevel.MEDIUM
        )

        return plan

    def _defend_template(
        self,
        target: str,
        workspace: str,
        scope: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Defensive hardening plan template.

        Phases:
        1. Baseline Assessment
        2. Vulnerability Detection
        3. Automated Remediation (REQUIRES APPROVAL)
        4. Continuous Monitoring
        """

        # Phase 1: Baseline Assessment
        baseline_phase = ExecutionPhase(
            id="1",
            name="Baseline Assessment",
            description="Inventory assets and check configurations",
            estimated_time=300,
            requires_approval=False,
            risk_level=RiskLevel.LOW,
            steps=[
                ExecutionStep(
                    id="1.1",
                    name="Inventory all servers",
                    tool="nmap",
                    command=f"nmap -sn {target} -oX -",
                    description="Asset discovery",
                    estimated_time=60
                ),
                ExecutionStep(
                    id="1.2",
                    name="Scan for misconfigurations",
                    tool="nuclei",
                    command=f"nuclei -u {target} -t misconfigurations/ -json",
                    description="CIS benchmarks",
                    estimated_time=180
                ),
                ExecutionStep(
                    id="1.3",
                    name="Check SSL/TLS config",
                    tool="sslscan",
                    command=f"sslscan {target}",
                    description="Crypto validation",
                    estimated_time=60
                )
            ]
        )

        # Phase 2: Vulnerability Detection
        vuln_phase = ExecutionPhase(
            id="2",
            name="Vulnerability Detection",
            description="OWASP Top 10 and dependency scanning",
            estimated_time=420,
            requires_approval=False,
            risk_level=RiskLevel.LOW,
            steps=[
                ExecutionStep(
                    id="2.1",
                    name="OWASP Top 10 scan",
                    tool="nikto",
                    command=f"nikto -h {target} -Format txt",
                    description="Web app vulnerabilities",
                    estimated_time=240
                ),
                ExecutionStep(
                    id="2.2",
                    name="Dependency check",
                    tool="nuclei",
                    command=f"nuclei -u {target} -t technologies/ -json",
                    description="Outdated libraries",
                    estimated_time=120
                ),
                ExecutionStep(
                    id="2.3",
                    name="Header analysis",
                    tool="curl",
                    command=f"curl -I {target}",
                    description="Security headers",
                    estimated_time=60
                )
            ]
        )

        # Phase 3: Automated Remediation (REQUIRES APPROVAL)
        remediation_phase = ExecutionPhase(
            id="3",
            name="Automated Remediation",
            description="Apply security hardening (REQUIRES APPROVAL)",
            estimated_time=600,
            requires_approval=True,
            risk_level=RiskLevel.HIGH,
            steps=[
                ExecutionStep(
                    id="3.1",
                    name="Deploy WAF rules",
                    tool="custom",
                    command="# WAF rule deployment",
                    description="Block known attacks",
                    estimated_time=180,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="3.2",
                    name="Update security headers",
                    tool="custom",
                    command="# Header update script",
                    description="Implement CSP, HSTS",
                    estimated_time=120,
                    requires_approval=True
                ),
                ExecutionStep(
                    id="3.3",
                    name="Patch critical CVEs",
                    tool="apt",
                    command="apt-get update && apt-get upgrade -y",
                    description="Auto-update packages",
                    estimated_time=300,
                    requires_approval=True
                )
            ]
        )

        # Phase 4: Continuous Monitoring
        monitor_phase = ExecutionPhase(
            id="4",
            name="Continuous Monitoring",
            description="Deploy detection rules and alerts",
            estimated_time=240,
            requires_approval=False,
            risk_level=RiskLevel.LOW,
            steps=[
                ExecutionStep(
                    id="4.1",
                    name="Deploy detection rules",
                    tool="custom",
                    command="# YARA/Sigma rule deployment",
                    description="Deploy YARA/Sigma rules",
                    estimated_time=60
                ),
                ExecutionStep(
                    id="4.2",
                    name="Configure alerts",
                    tool="custom",
                    command="# SIEM integration",
                    description="SIEM integration",
                    estimated_time=120
                ),
                ExecutionStep(
                    id="4.3",
                    name="Schedule recurring scans",
                    tool="cron",
                    command="# Cron job setup",
                    description="Weekly security checks",
                    estimated_time=60
                )
            ]
        )

        plan = ExecutionPlan(
            name=f"Security Hardening - {target}",
            objective=ObjectiveType.DEFEND,
            target=target,
            workspace=workspace,
            description=f"Defensive hardening and monitoring for {target}",
            phases=[baseline_phase, vuln_phase, remediation_phase, monitor_phase],
            risk_level=RiskLevel.MEDIUM
        )

        return plan

    def _investigate_template(
        self,
        target: str,
        workspace: str,
        scope: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Incident investigation plan template.

        Phases:
        1. Evidence Collection
        2. Forensic Analysis
        3. Threat Intelligence
        4. Incident Report
        """
        # Simplified template for now
        return ExecutionPlan(
            name=f"Incident Investigation - {target}",
            objective=ObjectiveType.INVESTIGATE,
            target=target,
            workspace=workspace,
            phases=[],
            risk_level=RiskLevel.LOW
        )

    def _monitor_template(
        self,
        target: str,
        workspace: str,
        scope: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Continuous monitoring plan template.

        Phases:
        1. Deploy Sensors
        2. Configure Baselines
        3. Enable Alerts
        4. Schedule Scans
        """
        # Simplified template for now
        return ExecutionPlan(
            name=f"Continuous Monitoring - {target}",
            objective=ObjectiveType.MONITOR,
            target=target,
            workspace=workspace,
            phases=[],
            risk_level=RiskLevel.LOW
        )
