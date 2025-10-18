"""
Guardian Coordinator - Orchestration of Constitutional Enforcement

Coordinates all Guardian Agents to ensure comprehensive Constitutional
compliance across the Vértice-MAXIMUS ecosystem.

This implements the mandate from Anexo D: A Doutrina da "Execução Constitucional"
providing centralized orchestration, conflict resolution, and reporting.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .article_ii_guardian import ArticleIIGuardian
from .article_iii_guardian import ArticleIIIGuardian
from .article_iv_guardian import ArticleIVGuardian
from .article_v_guardian import ArticleVGuardian
from .base import (
    ConstitutionalViolation,
    GuardianAgent,
    GuardianIntervention,
    GuardianPriority,
    VetoAction,
)


@dataclass
class CoordinatorMetrics:
    """Metrics for Guardian Coordinator performance."""

    total_violations_detected: int = 0
    violations_by_article: dict[str, int] = field(default_factory=dict)
    violations_by_severity: dict[str, int] = field(default_factory=dict)
    interventions_made: int = 0
    vetos_enacted: int = 0
    compliance_score: float = 100.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_violations_detected": self.total_violations_detected,
            "violations_by_article": self.violations_by_article,
            "violations_by_severity": self.violations_by_severity,
            "interventions_made": self.interventions_made,
            "vetos_enacted": self.vetos_enacted,
            "compliance_score": self.compliance_score,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class ConflictResolution:
    """Resolution for conflicts between Guardian decisions."""

    conflict_id: str
    guardian1_id: str
    guardian2_id: str
    violation1: ConstitutionalViolation
    violation2: ConstitutionalViolation
    resolution: str
    rationale: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class GuardianCoordinator:
    """
    Central coordinator for all Guardian Agents.

    Responsibilities:
    - Start/stop all Guardians
    - Aggregate and prioritize violations
    - Resolve conflicts between Guardians
    - Generate unified compliance reports
    - Manage veto escalations
    - Provide API for external systems
    """

    def __init__(self, guardians: dict[str, GuardianAgent] | None = None):
        """Initialize Guardian Coordinator.

        Args:
            guardians: Optional dict of guardian agents. If not provided, creates default instances.
        """
        self.coordinator_id = "guardian-coordinator-central"

        # Initialize all Guardian Agents
        self.guardians: dict[str, GuardianAgent] = guardians or {
            "article_ii": ArticleIIGuardian(),
            "article_iii": ArticleIIIGuardian(),
            "article_iv": ArticleIVGuardian(),
            "article_v": ArticleVGuardian(),
        }

        # Tracking
        self.all_violations: list[ConstitutionalViolation] = []
        self.all_interventions: list[GuardianIntervention] = []
        self.all_vetos: list[VetoAction] = []
        self.conflict_resolutions: list[ConflictResolution] = []
        self.metrics = CoordinatorMetrics()

        # State
        self._is_active = False
        self._coordination_task: asyncio.Task | None = None
        self._monitor_interval = 30  # seconds

        # Configuration
        self.veto_escalation_threshold = 3  # Number of vetos before escalation
        self.critical_alert_channels = []  # External alert channels

    # -------------------------------------------------------------------------
    # Lifecycle Management
    # -------------------------------------------------------------------------

    async def start(self):
        """Start all Guardian Agents and coordinator."""
        if self._is_active:
            return

        self._is_active = True

        # Start all Guardian Agents
        for guardian_id, guardian in self.guardians.items():
            # Register callbacks to receive notifications
            guardian.register_violation_callback(self._handle_violation)
            guardian.register_intervention_callback(self._handle_intervention)
            guardian.register_veto_callback(self._handle_veto)

            # Start the guardian
            await guardian.start()

        # Start coordination loop
        self._coordination_task = asyncio.create_task(self._coordination_loop())

        print(f"[{datetime.utcnow().isoformat()}] Guardian Coordinator started")

    async def stop(self):
        """Stop all Guardian Agents and coordinator."""
        self._is_active = False

        # Stop coordination task
        if self._coordination_task:
            self._coordination_task.cancel()
            try:
                await self._coordination_task
            except asyncio.CancelledError:
                pass

        # Stop all Guardian Agents
        for guardian in self.guardians.values():
            await guardian.stop()

        print(f"[{datetime.utcnow().isoformat()}] Guardian Coordinator stopped")

    # -------------------------------------------------------------------------
    # Coordination Loop
    # -------------------------------------------------------------------------

    async def _coordination_loop(self):
        """Main coordination loop."""
        while self._is_active:
            try:
                # Analyze recent violations for patterns
                await self._analyze_violation_patterns()

                # Check for conflicts between Guardians
                await self._resolve_conflicts()

                # Update metrics
                self._update_metrics()

                # Check if critical thresholds are breached
                await self._check_critical_thresholds()

                await asyncio.sleep(self._monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Coordination error: {e}")

    # -------------------------------------------------------------------------
    # Violation Handling
    # -------------------------------------------------------------------------

    async def _handle_violation(self, violation: ConstitutionalViolation):
        """Handle violation from a Guardian."""
        self.all_violations.append(violation)

        # Update metrics
        article = violation.article.value
        self.metrics.violations_by_article[article] = (
            self.metrics.violations_by_article.get(article, 0) + 1
        )

        severity = violation.severity.value
        self.metrics.violations_by_severity[severity] = (
            self.metrics.violations_by_severity.get(severity, 0) + 1
        )

        self.metrics.total_violations_detected += 1

        # Alert if critical
        if violation.severity == GuardianPriority.CRITICAL:
            await self._send_critical_alert(violation)

    async def _handle_intervention(self, intervention: GuardianIntervention):
        """Handle intervention from a Guardian."""
        self.all_interventions.append(intervention)
        self.metrics.interventions_made += 1

    async def _handle_veto(self, veto: VetoAction):
        """Handle veto from a Guardian."""
        self.all_vetos.append(veto)
        self.metrics.vetos_enacted += 1

        # Check for escalation
        recent_vetos = [
            v for v in self.all_vetos
            if v.enacted_at > datetime.utcnow() - timedelta(hours=1)
        ]

        if len(recent_vetos) >= self.veto_escalation_threshold:
            await self._escalate_vetos(recent_vetos)

    # -------------------------------------------------------------------------
    # Conflict Resolution
    # -------------------------------------------------------------------------

    async def _resolve_conflicts(self):
        """Resolve conflicts between Guardian decisions."""
        # Group violations by target
        violations_by_target = defaultdict(list)

        recent_violations = [
            v for v in self.all_violations
            if v.detected_at > datetime.utcnow() - timedelta(minutes=5)
        ]

        for violation in recent_violations:
            target = violation.context.get("file", "unknown")
            violations_by_target[target].append(violation)

        # Check for conflicts (multiple violations on same target)
        for target, violations in violations_by_target.items():
            if len(violations) > 1:
                # Sort by severity and article precedence
                violations.sort(
                    key=lambda v: (
                        self._get_severity_priority(v.severity),
                        self._get_article_precedence(v.article.value),
                    )
                )

                # Highest priority violation wins
                primary = violations[0]

                for secondary in violations[1:]:
                    if self._is_conflicting(primary, secondary):
                        resolution = ConflictResolution(
                            conflict_id=f"conflict_{datetime.utcnow().timestamp()}",
                            guardian1_id=f"guardian-{primary.article.value.lower()}",
                            guardian2_id=f"guardian-{secondary.article.value.lower()}",
                            violation1=primary,
                            violation2=secondary,
                            resolution=f"Prioritized {primary.article.value} over {secondary.article.value}",
                            rationale=(
                                f"Higher severity ({primary.severity.value}) and "
                                f"article precedence"
                            ),
                        )
                        self.conflict_resolutions.append(resolution)

    def _is_conflicting(
        self,
        v1: ConstitutionalViolation,
        v2: ConstitutionalViolation
    ) -> bool:
        """Check if two violations conflict."""
        # Violations conflict if they recommend opposite actions
        if v1.recommended_action == v2.recommended_action:
            return False

        # Check for specific conflicts
        if "allow" in v1.recommended_action.lower() and "block" in v2.recommended_action.lower():
            return True
        if "block" in v1.recommended_action.lower() and "allow" in v2.recommended_action.lower():
            return True

        return False

    def _get_severity_priority(self, severity: GuardianPriority) -> int:
        """Get numeric priority for severity."""
        priorities = {
            GuardianPriority.CRITICAL: 0,
            GuardianPriority.HIGH: 1,
            GuardianPriority.MEDIUM: 2,
            GuardianPriority.LOW: 3,
            GuardianPriority.INFO: 4,
        }
        return priorities.get(severity, 5)

    def _get_article_precedence(self, article: str) -> int:
        """Get precedence order for articles."""
        # Article V (Prior Legislation) has highest precedence
        # Then Article III (Zero Trust)
        # Then Article II (Quality)
        # Then Article IV (Antifragility)
        precedence = {
            "ARTICLE_V": 0,  # Prior Legislation - most important
            "ARTICLE_III": 1,  # Zero Trust - security critical
            "ARTICLE_II": 2,  # Quality Standard
            "ARTICLE_IV": 3,  # Antifragility
            "ARTICLE_I": 4,  # Hybrid Cell (not enforced by Guardians)
        }
        return precedence.get(article, 5)

    # -------------------------------------------------------------------------
    # Analysis and Reporting
    # -------------------------------------------------------------------------

    async def _analyze_violation_patterns(self):
        """Analyze violations for patterns and trends."""
        if len(self.all_violations) < 10:
            return

        # Time-based analysis
        recent_violations = [
            v for v in self.all_violations
            if v.detected_at > datetime.utcnow() - timedelta(hours=1)
        ]

        # Pattern detection
        patterns = defaultdict(int)

        for violation in recent_violations:
            # Count by rule
            patterns[violation.rule] += 1
            # Count by affected system
            for system in violation.affected_systems:
                patterns[f"system:{system}"] += 1

        # Identify hot spots (rules/systems with multiple violations)
        hot_spots = {k: v for k, v in patterns.items() if v >= 3}

        if hot_spots:
            # Create meta-violation for pattern
            pattern_violation = ConstitutionalViolation(
                article=self.all_violations[-1].article,  # Use latest article
                clause="Coordinator Pattern Detection",
                rule="Repeated violations detected",
                description=f"Pattern detected: {list(hot_spots.keys())}",
                severity=GuardianPriority.HIGH,
                evidence=[f"{k}: {v} occurrences" for k, v in hot_spots.items()],
                affected_systems=["pattern_detection"],
                recommended_action="Review and address systematic issues",
            )
            await self._handle_violation(pattern_violation)

    def _update_metrics(self):
        """Update coordinator metrics."""
        # Calculate compliance score
        total_checks = self.metrics.total_violations_detected + 1000  # Assume 1000 successful checks
        if total_checks > 0:
            self.metrics.compliance_score = (
                (total_checks - self.metrics.total_violations_detected) / total_checks
            ) * 100

        self.metrics.last_updated = datetime.utcnow()

    async def _check_critical_thresholds(self):
        """Check if critical thresholds are breached."""
        # Check compliance score
        if self.metrics.compliance_score < 80:
            await self._send_critical_alert(
                ConstitutionalViolation(
                    article=self.all_violations[-1].article if self.all_violations else None,
                    clause="System Compliance",
                    rule="Compliance below threshold",
                    description=f"System compliance at {self.metrics.compliance_score:.1f}%",
                    severity=GuardianPriority.CRITICAL,
                    evidence=["Compliance score below 80%"],
                    affected_systems=["entire_ecosystem"],
                    recommended_action="Emergency review required",
                )
            )

        # Check veto rate
        recent_vetos = [
            v for v in self.all_vetos
            if v.enacted_at > datetime.utcnow() - timedelta(hours=1)
        ]

        if len(recent_vetos) > 5:
            await self._send_critical_alert(
                ConstitutionalViolation(
                    article=self.all_violations[-1].article if self.all_violations else None,
                    clause="Veto Threshold",
                    rule="Excessive vetos",
                    description=f"{len(recent_vetos)} vetos in past hour",
                    severity=GuardianPriority.CRITICAL,
                    evidence=[f"Veto IDs: {[v.veto_id for v in recent_vetos[:3]]}"],
                    affected_systems=["veto_system"],
                    recommended_action="Human intervention required",
                )
            )

    # -------------------------------------------------------------------------
    # External Communication
    # -------------------------------------------------------------------------

    async def _send_critical_alert(self, violation: ConstitutionalViolation):
        """Send critical alert to external channels."""
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": "CRITICAL",
            "violation": violation.to_dict(),
            "coordinator_id": self.coordinator_id,
        }

        # In production, would send to:
        # - Slack/Discord
        # - PagerDuty
        # - Email
        # - SIEM

        print(f"[CRITICAL ALERT] {violation.description}")

        # Log to file
        alert_file = Path("/tmp/guardian_critical_alerts.json")
        alerts = []

        if alert_file.exists():
            try:
                alerts = json.loads(alert_file.read_text())
            except Exception:
                pass

        alerts.append(alert)
        alert_file.write_text(json.dumps(alerts, indent=2))

    async def _escalate_vetos(self, vetos: list[VetoAction]):
        """Escalate multiple vetos to human oversight."""
        escalation = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "veto_escalation",
            "veto_count": len(vetos),
            "vetos": [v.to_dict() for v in vetos],
            "message": "Multiple vetos require human review",
        }

        print(f"[ESCALATION] {len(vetos)} vetos require human review")

        # In production, would trigger:
        # - HITL interface
        # - ERB notification
        # - Emergency response team

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Get coordinator status."""
        return {
            "coordinator_id": self.coordinator_id,
            "is_active": self._is_active,
            "guardians": {
                name: {
                    "id": guardian.guardian_id,
                    "active": guardian.is_active(),
                    "stats": guardian.get_statistics(),
                }
                for name, guardian in self.guardians.items()
            },
            "metrics": self.metrics.to_dict(),
            "active_vetos": len([v for v in self.all_vetos if v.is_active()]),
            "recent_violations": len([
                v for v in self.all_violations
                if v.detected_at > datetime.utcnow() - timedelta(hours=1)
            ]),
        }

    def generate_compliance_report(
        self,
        period_hours: int = 24
    ) -> dict[str, Any]:
        """Generate unified compliance report."""
        period_start = datetime.utcnow() - timedelta(hours=period_hours)

        # Aggregate reports from all Guardians
        guardian_reports = {}
        for name, guardian in self.guardians.items():
            guardian_reports[name] = guardian.generate_report(period_hours).to_dict()

        # Filter coordinator data for period
        period_violations = [
            v for v in self.all_violations
            if v.detected_at > period_start
        ]

        period_interventions = [
            i for i in self.all_interventions
            if i.timestamp > period_start
        ]

        period_vetos = [
            v for v in self.all_vetos
            if v.enacted_at > period_start
        ]

        return {
            "report_id": f"compliance_{datetime.utcnow().timestamp()}",
            "period_start": period_start.isoformat(),
            "period_end": datetime.utcnow().isoformat(),
            "coordinator_metrics": self.metrics.to_dict(),
            "guardian_reports": guardian_reports,
            "summary": {
                "total_violations": len(period_violations),
                "total_interventions": len(period_interventions),
                "total_vetos": len(period_vetos),
                "compliance_score": self.metrics.compliance_score,
                "critical_violations": len([
                    v for v in period_violations
                    if v.severity == GuardianPriority.CRITICAL
                ]),
            },
            "top_violations": self._get_top_violations(period_violations),
            "recommendations": self._generate_recommendations(period_violations),
        }

    def _get_top_violations(
        self,
        violations: list[ConstitutionalViolation]
    ) -> list[dict[str, Any]]:
        """Get top violations by frequency."""
        violation_counts = defaultdict(int)

        for v in violations:
            key = f"{v.article.value}:{v.rule}"
            violation_counts[key] += 1

        sorted_violations = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"violation": k, "count": v}
            for k, v in sorted_violations[:10]
        ]

    def _generate_recommendations(
        self,
        violations: list[ConstitutionalViolation]
    ) -> list[str]:
        """Generate recommendations based on violations."""
        recommendations = []

        # Check for quality issues
        quality_violations = [
            v for v in violations
            if v.article.value == "ARTICLE_II"
        ]
        if len(quality_violations) > 10:
            recommendations.append(
                "High number of quality violations. "
                "Implement code review and testing requirements."
            )

        # Check for security issues
        security_violations = [
            v for v in violations
            if v.article.value == "ARTICLE_III"
        ]
        if len(security_violations) > 5:
            recommendations.append(
                "Multiple Zero Trust violations. "
                "Conduct security audit and implement authentication."
            )

        # Check for resilience issues
        resilience_violations = [
            v for v in violations
            if v.article.value == "ARTICLE_IV"
        ]
        if len(resilience_violations) > 5:
            recommendations.append(
                "System lacks antifragility. "
                "Implement chaos engineering and resilience patterns."
            )

        # Check for governance issues
        governance_violations = [
            v for v in violations
            if v.article.value == "ARTICLE_V"
        ]
        if len(governance_violations) > 3:
            recommendations.append(
                "Governance violations detected. "
                "Review Prior Legislation principle and implement controls."
            )

        if not recommendations:
            recommendations.append(
                "System is generally compliant. "
                "Continue monitoring and improvement."
            )

        return recommendations

    async def override_veto(
        self,
        veto_id: str,
        override_reason: str,
        approver_id: str
    ) -> bool:
        """
        Override a Guardian veto (requires authorization).

        Args:
            veto_id: ID of veto to override
            override_reason: Justification for override
            approver_id: ID of human approver

        Returns:
            True if override successful
        """
        # Find the veto
        veto = next((v for v in self.all_vetos if v.veto_id == veto_id), None)

        if not veto:
            return False

        if not veto.override_allowed:
            print(f"Veto {veto_id} cannot be overridden")
            return False

        # Check override requirements
        # In production, would verify approver authorization

        # Mark as overridden
        veto.metadata["overridden"] = True
        veto.metadata["override_reason"] = override_reason
        veto.metadata["override_approver"] = approver_id
        veto.metadata["override_time"] = datetime.utcnow().isoformat()

        print(f"Veto {veto_id} overridden by {approver_id}: {override_reason}")

        return True