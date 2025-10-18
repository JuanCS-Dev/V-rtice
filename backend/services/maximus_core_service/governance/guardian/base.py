"""
Guardian Agents - Base Framework

Core infrastructure for Constitutional Guardian Agents that enforce
the Vértice Constitution through continuous monitoring and intervention.

This module implements:
- GuardianAgent: Abstract base for all Guardian agents
- Monitoring and detection capabilities
- Veto power and intervention mechanisms
- Audit trail and reporting

Author: Claude Code + JuanCS-Dev
Date: 2025-10-13
"""

import asyncio
import hashlib
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4


# ============================================================================
# ENUMS
# ============================================================================


class GuardianPriority(str, Enum):
    """Priority levels for Guardian interventions."""

    CRITICAL = "CRITICAL"  # Immediate action required
    HIGH = "HIGH"  # Urgent, within minutes
    MEDIUM = "MEDIUM"  # Important, within hours
    LOW = "LOW"  # Routine monitoring
    INFO = "INFO"  # Informational only


class InterventionType(str, Enum):
    """Types of Guardian interventions."""

    VETO = "VETO"  # Block an action completely
    ALERT = "ALERT"  # Raise awareness but don't block
    REMEDIATION = "REMEDIATION"  # Automatic fix applied
    ESCALATION = "ESCALATION"  # Escalate to human oversight
    MONITORING = "MONITORING"  # Increase monitoring level


class ConstitutionalArticle(str, Enum):
    """Constitutional Articles that Guardians enforce."""

    ARTICLE_I = "ARTICLE_I"  # Hybrid Development Cell
    ARTICLE_II = "ARTICLE_II"  # Sovereign Quality Standard
    ARTICLE_III = "ARTICLE_III"  # Zero Trust Principle
    ARTICLE_IV = "ARTICLE_IV"  # Deliberate Antifragility
    ARTICLE_V = "ARTICLE_V"  # Prior Legislation


# ============================================================================
# DATA STRUCTURES
# ============================================================================


@dataclass
class ConstitutionalViolation:
    """Represents a detected violation of the Constitution."""

    violation_id: str = field(default_factory=lambda: str(uuid4()))
    article: ConstitutionalArticle = ConstitutionalArticle.ARTICLE_II
    clause: str = ""  # e.g., "Cláusula 3.2"
    rule: str = ""  # Specific rule violated
    description: str = ""
    severity: GuardianPriority = GuardianPriority.MEDIUM
    detected_at: datetime = field(default_factory=datetime.utcnow)
    context: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)
    affected_systems: list[str] = field(default_factory=list)
    recommended_action: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "article": self.article.value,
            "clause": self.clause,
            "rule": self.rule,
            "description": self.description,
            "severity": self.severity.value,
            "detected_at": self.detected_at.isoformat(),
            "context": self.context,
            "evidence": self.evidence,
            "affected_systems": self.affected_systems,
            "recommended_action": self.recommended_action,
            "metadata": self.metadata,
        }

    def generate_hash(self) -> str:
        """Generate unique hash for violation tracking."""
        content = f"{self.article}{self.clause}{self.rule}{str(self.context)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class VetoAction:
    """Represents a veto action taken by a Guardian."""

    veto_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    target_action: str = ""  # What was vetoed
    target_system: str = ""  # Which system/service
    violation: ConstitutionalViolation | None = None
    reason: str = ""
    enacted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None  # Temporary vetos
    override_allowed: bool = False  # Can be overridden by human
    override_requirements: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if veto is still active."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "veto_id": self.veto_id,
            "guardian_id": self.guardian_id,
            "target_action": self.target_action,
            "target_system": self.target_system,
            "violation": self.violation.to_dict() if self.violation else None,
            "reason": self.reason,
            "enacted_at": self.enacted_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active(),
            "override_allowed": self.override_allowed,
            "override_requirements": self.override_requirements,
            "metadata": self.metadata,
        }


@dataclass
class GuardianIntervention:
    """Records an intervention taken by a Guardian."""

    intervention_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    intervention_type: InterventionType = InterventionType.ALERT
    priority: GuardianPriority = GuardianPriority.MEDIUM
    violation: ConstitutionalViolation | None = None
    action_taken: str = ""
    result: str = ""
    success: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intervention_id": self.intervention_id,
            "guardian_id": self.guardian_id,
            "intervention_type": self.intervention_type.value,
            "priority": self.priority.value,
            "violation": self.violation.to_dict() if self.violation else None,
            "action_taken": self.action_taken,
            "result": self.result,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GuardianDecision:
    """Represents a decision made by a Guardian Agent."""

    decision_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    decision_type: str = ""  # e.g., "allow", "block", "escalate"
    target: str = ""  # What the decision applies to
    reasoning: str = ""  # Constitutional basis for decision
    confidence: float = 0.0  # 0.0 to 1.0
    requires_validation: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "guardian_id": self.guardian_id,
            "decision_type": self.decision_type,
            "target": self.target,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "requires_validation": self.requires_validation,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class GuardianReport:
    """Periodic compliance report from Guardian Agents."""

    report_id: str = field(default_factory=lambda: str(uuid4()))
    guardian_id: str = ""
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    violations_detected: int = 0
    interventions_made: int = 0
    vetos_enacted: int = 0
    compliance_score: float = 100.0  # 0-100 percentage
    top_violations: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "report_id": self.report_id,
            "guardian_id": self.guardian_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "violations_detected": self.violations_detected,
            "interventions_made": self.interventions_made,
            "vetos_enacted": self.vetos_enacted,
            "compliance_score": self.compliance_score,
            "top_violations": self.top_violations,
            "recommendations": self.recommendations,
            "metrics": self.metrics,
            "generated_at": self.generated_at.isoformat(),
        }


# ============================================================================
# BASE GUARDIAN AGENT
# ============================================================================


class GuardianAgent(ABC):
    """
    Abstract base class for Constitutional Guardian Agents.

    Each Guardian enforces specific Articles of the Vértice Constitution
    through continuous monitoring, detection, and intervention.
    """

    def __init__(
        self,
        guardian_id: str,
        article: ConstitutionalArticle,
        name: str,
        description: str,
    ):
        """Initialize Guardian Agent."""
        self.guardian_id = guardian_id
        self.article = article
        self.name = name
        self.description = description

        # Monitoring state
        self._is_active = False
        self._monitor_task: asyncio.Task | None = None
        self._monitor_interval = 60  # seconds

        # Tracking
        self._violations: list[ConstitutionalViolation] = []
        self._interventions: list[GuardianIntervention] = []
        self._vetos: list[VetoAction] = []
        self._decisions: list[GuardianDecision] = []

        # Callbacks for external systems
        self._violation_callbacks: list[Callable[[ConstitutionalViolation], Awaitable[None]]] = []
        self._intervention_callbacks: list[Callable[[GuardianIntervention], Awaitable[None]]] = []
        self._veto_callbacks: list[Callable[[VetoAction], Awaitable[None]]] = []

    # -------------------------------------------------------------------------
    # Abstract Methods (Must be implemented by subclasses)
    # -------------------------------------------------------------------------

    @abstractmethod
    async def monitor(self) -> list[ConstitutionalViolation]:
        """
        Monitor the ecosystem for constitutional violations.

        Returns:
            List of detected violations
        """
        pass

    @abstractmethod
    async def analyze_violation(self, violation: ConstitutionalViolation) -> GuardianDecision:
        """
        Analyze a violation and decide on appropriate action.

        Args:
            violation: The detected violation

        Returns:
            Decision on how to handle the violation
        """
        pass

    @abstractmethod
    async def intervene(self, violation: ConstitutionalViolation) -> GuardianIntervention:
        """
        Take intervention action for a violation.

        Args:
            violation: The violation to address

        Returns:
            Record of intervention taken
        """
        pass

    @abstractmethod
    def get_monitored_systems(self) -> list[str]:
        """
        Get list of systems this Guardian monitors.

        Returns:
            List of system identifiers
        """
        pass

    # -------------------------------------------------------------------------
    # Core Methods
    # -------------------------------------------------------------------------

    async def start(self):
        """Start the Guardian Agent monitoring."""
        if self._is_active:
            return

        self._is_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop the Guardian Agent monitoring."""
        self._is_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._is_active:
            try:
                # Detect violations
                violations = await self.monitor()

                # Process each violation
                for violation in violations:
                    await self._process_violation(violation)

                # Wait before next cycle
                await asyncio.sleep(self._monitor_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                # Log error but continue monitoring
                await self._handle_monitor_error(e)

    async def _process_violation(self, violation: ConstitutionalViolation):
        """Process a detected violation."""
        # Record violation
        self._violations.append(violation)

        # Notify callbacks
        for callback in self._violation_callbacks:
            await callback(violation)

        # Analyze and decide
        decision = await self.analyze_violation(violation)
        self._decisions.append(decision)

        # Take intervention if needed
        if decision.decision_type in ["block", "veto", "remediate"]:
            intervention = await self.intervene(violation)
            self._interventions.append(intervention)

            # Notify intervention callbacks
            for callback in self._intervention_callbacks:
                await callback(intervention)

            # Create veto if applicable
            if intervention.intervention_type == InterventionType.VETO:
                veto = await self._create_veto(violation, decision)
                self._vetos.append(veto)

                # Notify veto callbacks
                for callback in self._veto_callbacks:
                    await callback(veto)

    async def _create_veto(
        self,
        violation: ConstitutionalViolation,
        decision: GuardianDecision
    ) -> VetoAction:
        """Create a veto action."""
        return VetoAction(
            guardian_id=self.guardian_id,
            target_action=decision.target,
            target_system=violation.affected_systems[0] if violation.affected_systems else "unknown",
            violation=violation,
            reason=decision.reasoning,
            override_allowed=decision.confidence < 0.95,  # Allow override for lower confidence
            override_requirements=[
                "Human architect approval",
                "ERB review if CRITICAL severity",
            ],
            metadata={
                "decision_id": decision.decision_id,
                "confidence": decision.confidence,
            }
        )

    async def _handle_monitor_error(self, error: Exception):
        """Handle monitoring errors."""
        # Create error violation
        violation = ConstitutionalViolation(
            article=self.article,
            clause="Guardian Monitoring",
            rule="Guardian must maintain continuous monitoring",
            description=f"Guardian monitoring error: {str(error)}",
            severity=GuardianPriority.HIGH,
            affected_systems=[self.guardian_id],
            recommended_action="Investigate and fix Guardian monitoring",
            metadata={"error_type": type(error).__name__}
        )

        # Process as normal violation
        await self._process_violation(violation)

    # -------------------------------------------------------------------------
    # Veto Power
    # -------------------------------------------------------------------------

    async def veto_action(
        self,
        action: str,
        system: str,
        reason: str,
        duration_hours: int | None = None
    ) -> VetoAction:
        """
        Exercise veto power to block an action.

        Args:
            action: Action to veto
            system: System where action occurs
            reason: Constitutional reason for veto
            duration_hours: Hours until veto expires (None = permanent)

        Returns:
            The veto action taken
        """
        veto = VetoAction(
            guardian_id=self.guardian_id,
            target_action=action,
            target_system=system,
            reason=reason,
            expires_at=(
                datetime.utcnow() + timedelta(hours=duration_hours)
                if duration_hours else None
            ),
            override_allowed=True,
            override_requirements=[
                f"Approval from {self.article.value} Guardian administrator",
                "Constitutional justification required",
            ]
        )

        self._vetos.append(veto)

        # Notify callbacks
        for callback in self._veto_callbacks:
            await callback(veto)

        return veto

    def get_active_vetos(self) -> list[VetoAction]:
        """Get all active vetos."""
        return [v for v in self._vetos if v.is_active()]

    # -------------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------------

    def generate_report(
        self,
        period_hours: int = 24
    ) -> GuardianReport:
        """
        Generate compliance report for specified period.

        Args:
            period_hours: Hours to include in report

        Returns:
            Guardian compliance report
        """
        period_start = datetime.utcnow() - timedelta(hours=period_hours)
        period_end = datetime.utcnow()

        # Filter data for period
        period_violations = [
            v for v in self._violations
            if period_start <= v.detected_at <= period_end
        ]
        period_interventions = [
            i for i in self._interventions
            if period_start <= i.timestamp <= period_end
        ]
        period_vetos = [
            v for v in self._vetos
            if period_start <= v.enacted_at <= period_end
        ]

        # Calculate compliance score
        total_checks = len(period_violations) + 100  # Assume 100 successful checks
        violations_count = len(period_violations)
        compliance_score = ((total_checks - violations_count) / total_checks) * 100

        # Get top violations
        violation_counts: dict[str, int] = {}
        for v in period_violations:
            key = f"{v.clause}: {v.rule}"
            violation_counts[key] = violation_counts.get(key, 0) + 1

        top_violations = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Generate recommendations
        recommendations = []
        if violations_count > 10:
            recommendations.append("High violation rate detected - review development practices")
        if len(period_vetos) > 0:
            recommendations.append(f"{len(period_vetos)} vetos enacted - ensure teams understand Constitution")
        if compliance_score < 90:
            recommendations.append("Compliance below target - mandatory Constitution training recommended")

        return GuardianReport(
            guardian_id=self.guardian_id,
            period_start=period_start,
            period_end=period_end,
            violations_detected=violations_count,
            interventions_made=len(period_interventions),
            vetos_enacted=len(period_vetos),
            compliance_score=compliance_score,
            top_violations=[f"{v[0]} ({v[1]} occurrences)" for v in top_violations],
            recommendations=recommendations,
            metrics={
                "average_confidence": sum(d.confidence for d in self._decisions) / len(self._decisions) if self._decisions else 0,
                "critical_violations": sum(1 for v in period_violations if v.severity == GuardianPriority.CRITICAL),
                "auto_remediated": sum(1 for i in period_interventions if i.intervention_type == InterventionType.REMEDIATION),
            }
        )

    # -------------------------------------------------------------------------
    # Callbacks
    # -------------------------------------------------------------------------

    def register_violation_callback(
        self,
        callback: Callable[[ConstitutionalViolation], Awaitable[None]]
    ):
        """Register callback for violation notifications."""
        self._violation_callbacks.append(callback)

    def register_intervention_callback(
        self,
        callback: Callable[[GuardianIntervention], Awaitable[None]]
    ):
        """Register callback for intervention notifications."""
        self._intervention_callbacks.append(callback)

    def register_veto_callback(
        self,
        callback: Callable[[VetoAction], Awaitable[None]]
    ):
        """Register callback for veto notifications."""
        self._veto_callbacks.append(callback)

    # -------------------------------------------------------------------------
    # Status Methods
    # -------------------------------------------------------------------------

    def is_active(self) -> bool:
        """Check if Guardian is actively monitoring."""
        return self._is_active

    def get_statistics(self) -> dict[str, Any]:
        """Get Guardian statistics."""
        return {
            "guardian_id": self.guardian_id,
            "name": self.name,
            "article": self.article.value,
            "is_active": self._is_active,
            "total_violations": len(self._violations),
            "total_interventions": len(self._interventions),
            "active_vetos": len(self.get_active_vetos()),
            "total_decisions": len(self._decisions),
            "monitored_systems": self.get_monitored_systems(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"GuardianAgent(id={self.guardian_id}, "
            f"name={self.name}, "
            f"article={self.article.value}, "
            f"active={self._is_active})"
        )