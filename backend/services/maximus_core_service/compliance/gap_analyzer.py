"""
Gap Analyzer

Compliance gap analysis and remediation planning. Identifies gaps between
current state and regulatory requirements, prioritizes remediation efforts,
and generates actionable remediation plans.

Features:
- Automated gap identification
- Gap prioritization (severity, impact, effort)
- Remediation plan generation
- Progress tracking
- Effort estimation
- Risk-based prioritization

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import uuid

from .base import (
    ComplianceConfig,
    ComplianceResult,
    ComplianceStatus,
    Control,
    Gap,
    GapAnalysisResult,
    RegulationType,
    RemediationAction,
    RemediationPlan,
    RemediationStatus,
    ViolationSeverity,
    ControlCategory,
)
from .compliance_engine import ComplianceCheckResult
from .regulations import get_regulation

logger = logging.getLogger(__name__)


# Effort estimation (hours) by gap type and control category
EFFORT_ESTIMATES: Dict[Tuple[str, ControlCategory], int] = {
    # Missing controls - high effort
    ("missing_control", ControlCategory.TECHNICAL): 80,
    ("missing_control", ControlCategory.SECURITY): 60,
    ("missing_control", ControlCategory.GOVERNANCE): 40,
    ("missing_control", ControlCategory.ORGANIZATIONAL): 40,
    ("missing_control", ControlCategory.DOCUMENTATION): 20,
    ("missing_control", ControlCategory.MONITORING): 60,
    ("missing_control", ControlCategory.TESTING): 40,
    ("missing_control", ControlCategory.PRIVACY): 60,
    # Partial implementation - medium effort
    ("partial_implementation", ControlCategory.TECHNICAL): 40,
    ("partial_implementation", ControlCategory.SECURITY): 30,
    ("partial_implementation", ControlCategory.GOVERNANCE): 20,
    ("partial_implementation", ControlCategory.ORGANIZATIONAL): 20,
    ("partial_implementation", ControlCategory.DOCUMENTATION): 10,
    ("partial_implementation", ControlCategory.MONITORING): 30,
    ("partial_implementation", ControlCategory.TESTING): 20,
    ("partial_implementation", ControlCategory.PRIVACY): 30,
    # Outdated - low effort
    ("outdated", ControlCategory.TECHNICAL): 20,
    ("outdated", ControlCategory.SECURITY): 15,
    ("outdated", ControlCategory.GOVERNANCE): 10,
    ("outdated", ControlCategory.ORGANIZATIONAL): 10,
    ("outdated", ControlCategory.DOCUMENTATION): 5,
    ("outdated", ControlCategory.MONITORING): 15,
    ("outdated", ControlCategory.TESTING): 10,
    ("outdated", ControlCategory.PRIVACY): 15,
    # Insufficient evidence - very low effort
    ("insufficient_evidence", ControlCategory.TECHNICAL): 8,
    ("insufficient_evidence", ControlCategory.SECURITY): 8,
    ("insufficient_evidence", ControlCategory.GOVERNANCE): 4,
    ("insufficient_evidence", ControlCategory.ORGANIZATIONAL): 4,
    ("insufficient_evidence", ControlCategory.DOCUMENTATION): 2,
    ("insufficient_evidence", ControlCategory.MONITORING): 8,
    ("insufficient_evidence", ControlCategory.TESTING): 4,
    ("insufficient_evidence", ControlCategory.PRIVACY): 8,
}


class GapAnalyzer:
    """
    Compliance gap analyzer and remediation planner.

    Identifies compliance gaps and generates prioritized remediation plans.
    """

    def __init__(self, config: Optional[ComplianceConfig] = None):
        """
        Initialize gap analyzer.

        Args:
            config: Compliance configuration
        """
        self.config = config or ComplianceConfig()
        logger.info("Gap analyzer initialized")

    def analyze_compliance_gaps(
        self,
        compliance_result: ComplianceCheckResult,
    ) -> GapAnalysisResult:
        """
        Analyze compliance gaps for a regulation.

        Args:
            compliance_result: Compliance check result

        Returns:
            Gap analysis result
        """
        logger.info(f"Analyzing compliance gaps for {compliance_result.regulation_type.value}")

        regulation = get_regulation(compliance_result.regulation_type)
        gaps: List[Gap] = []

        # Analyze each control result
        for result in compliance_result.results:
            control = regulation.get_control(result.control_id)
            if not control:
                continue

            # Identify gap based on status
            gap = self._identify_gap(control, result)
            if gap:
                gaps.append(gap)

        # Sort gaps by priority (severity, then mandatory, then category)
        gaps_sorted = sorted(
            gaps,
            key=lambda g: (
                self._severity_to_priority(g.severity),
                0 if regulation.get_control(g.control_id).mandatory else 1,
                g.priority,
            ),
        )

        # Calculate metrics
        total_controls = compliance_result.total_controls
        compliant = compliance_result.compliant
        non_compliant = compliance_result.non_compliant
        partially_compliant = compliance_result.partially_compliant

        # Estimate total remediation effort
        total_effort = sum(gap.estimated_effort_hours or 0 for gap in gaps)

        # Create result
        analysis = GapAnalysisResult(
            regulation_type=compliance_result.regulation_type,
            total_controls=total_controls,
            compliant_controls=compliant,
            non_compliant_controls=non_compliant,
            partially_compliant_controls=partially_compliant,
            gaps=gaps_sorted,
            estimated_remediation_hours=total_effort,
            next_review_date=datetime.utcnow() + timedelta(days=90),
        )

        logger.info(
            f"Gap analysis complete: {len(gaps)} gaps identified, "
            f"{total_effort}h estimated effort, "
            f"{analysis.compliance_percentage:.1f}% compliant"
        )

        return analysis

    def create_remediation_plan(
        self,
        gap_analysis: GapAnalysisResult,
        target_completion_days: int = 180,
        created_by: str = "gap_analyzer",
    ) -> RemediationPlan:
        """
        Create remediation plan from gap analysis.

        Args:
            gap_analysis: Gap analysis result
            target_completion_days: Days to complete remediation
            created_by: Plan creator

        Returns:
            Remediation plan
        """
        logger.info(
            f"Creating remediation plan for {gap_analysis.regulation_type.value}, "
            f"{len(gap_analysis.gaps)} gaps"
        )

        # Create remediation actions for each gap
        actions: List[RemediationAction] = []
        regulation = get_regulation(gap_analysis.regulation_type)

        for gap in gap_analysis.gaps:
            control = regulation.get_control(gap.control_id)
            if not control:
                continue

            # Generate action for gap
            action = self._create_remediation_action(
                gap, control, target_completion_days
            )
            actions.append(action)

        # Create plan
        plan = RemediationPlan(
            regulation_type=gap_analysis.regulation_type,
            created_by=created_by,
            gaps=gap_analysis.gaps,
            actions=actions,
            target_completion_date=datetime.utcnow() + timedelta(days=target_completion_days),
            status="draft",
        )

        # Link to gap analysis
        gap_analysis.remediation_plan = plan

        logger.info(
            f"Remediation plan created: {plan.plan_id}, "
            f"{len(actions)} actions, "
            f"target: {target_completion_days} days"
        )

        return plan

    def prioritize_gaps(
        self,
        gaps: List[Gap],
        criteria: str = "risk",  # risk, effort, impact
    ) -> List[Gap]:
        """
        Prioritize gaps based on criteria.

        Args:
            gaps: List of gaps to prioritize
            criteria: Prioritization criteria (risk, effort, impact)

        Returns:
            Prioritized list of gaps
        """
        if criteria == "risk":
            # Prioritize by severity + mandatory status
            return sorted(
                gaps,
                key=lambda g: (
                    self._severity_to_priority(g.severity),
                    0,  # All gaps are important
                    g.priority,
                ),
            )
        elif criteria == "effort":
            # Prioritize by effort (quick wins first)
            return sorted(
                gaps,
                key=lambda g: (g.estimated_effort_hours or 999, g.priority),
            )
        elif criteria == "impact":
            # Prioritize by impact (severity + effort ratio)
            return sorted(
                gaps,
                key=lambda g: (
                    self._severity_to_priority(g.severity) * 10
                    / max(g.estimated_effort_hours or 1, 1),
                    g.priority,
                ),
                reverse=True,
            )
        else:
            return gaps

    def track_remediation_progress(
        self,
        plan: RemediationPlan,
    ) -> Dict[str, any]:
        """
        Track remediation plan progress.

        Args:
            plan: Remediation plan

        Returns:
            Progress metrics dict
        """
        total_actions = len(plan.actions)
        if total_actions == 0:
            return {
                "completion_percentage": 100.0,
                "status": "completed",
                "actions_completed": 0,
                "actions_in_progress": 0,
                "actions_not_started": 0,
                "actions_blocked": 0,
                "overdue_actions": 0,
            }

        # Count action statuses
        completed = sum(
            1 for a in plan.actions if a.status == RemediationStatus.COMPLETED
        )
        in_progress = sum(
            1 for a in plan.actions if a.status == RemediationStatus.IN_PROGRESS
        )
        not_started = sum(
            1 for a in plan.actions if a.status == RemediationStatus.NOT_STARTED
        )
        blocked = sum(
            1 for a in plan.actions if a.status == RemediationStatus.BLOCKED
        )
        overdue = len(plan.get_overdue_actions())

        # Calculate completion percentage
        completion = plan.get_completion_percentage()

        # Determine overall status
        if completion >= 100:
            status = "completed"
        elif completion > 0:
            status = "in_progress"
        else:
            status = "not_started"

        return {
            "completion_percentage": completion,
            "status": status,
            "actions_completed": completed,
            "actions_in_progress": in_progress,
            "actions_not_started": not_started,
            "actions_blocked": blocked,
            "overdue_actions": overdue,
            "total_actions": total_actions,
        }

    def estimate_remediation_effort(
        self,
        gaps: List[Gap],
    ) -> Dict[str, any]:
        """
        Estimate total remediation effort.

        Args:
            gaps: List of gaps

        Returns:
            Effort estimation dict
        """
        total_hours = sum(gap.estimated_effort_hours or 0 for gap in gaps)

        # Estimate by severity
        critical_hours = sum(
            gap.estimated_effort_hours or 0
            for gap in gaps
            if gap.severity == ViolationSeverity.CRITICAL
        )
        high_hours = sum(
            gap.estimated_effort_hours or 0
            for gap in gaps
            if gap.severity == ViolationSeverity.HIGH
        )
        medium_hours = sum(
            gap.estimated_effort_hours or 0
            for gap in gaps
            if gap.severity == ViolationSeverity.MEDIUM
        )
        low_hours = sum(
            gap.estimated_effort_hours or 0
            for gap in gaps
            if gap.severity == ViolationSeverity.LOW
        )

        # Estimate timeline (assuming 40 hours/week, 1 engineer)
        weeks = total_hours / 40 if total_hours > 0 else 0

        return {
            "total_hours": total_hours,
            "estimated_weeks": round(weeks, 1),
            "by_severity": {
                "critical": critical_hours,
                "high": high_hours,
                "medium": medium_hours,
                "low": low_hours,
            },
            "total_gaps": len(gaps),
        }

    def _identify_gap(
        self,
        control: Control,
        result: ComplianceResult,
    ) -> Optional[Gap]:
        """
        Identify compliance gap from control and result.

        Args:
            control: Control definition
            result: Compliance check result

        Returns:
            Gap or None if compliant
        """
        # Compliant - no gap
        if result.status == ComplianceStatus.COMPLIANT:
            return None

        # Not applicable - no gap
        if result.status == ComplianceStatus.NOT_APPLICABLE:
            return None

        # Determine gap type
        if result.status == ComplianceStatus.NON_COMPLIANT:
            gap_type = "missing_control"
            current_state = "Not implemented"
            required_state = control.description
        elif result.status == ComplianceStatus.PARTIALLY_COMPLIANT:
            gap_type = "partial_implementation"
            current_state = "Partially implemented"
            required_state = control.description
        elif result.status == ComplianceStatus.EVIDENCE_REQUIRED:
            gap_type = "insufficient_evidence"
            current_state = "Implemented but evidence missing"
            required_state = f"Evidence required: {[e.value for e in control.evidence_required]}"
        else:  # PENDING_REVIEW
            gap_type = "pending_review"
            current_state = "Awaiting manual review"
            required_state = control.description

        # Determine severity
        severity = self._determine_gap_severity(control)

        # Estimate effort
        effort = self._estimate_gap_effort(gap_type, control.category)

        # Determine priority (1-5)
        priority = self._determine_gap_priority(control, severity)

        # Create gap
        gap = Gap(
            control_id=control.control_id,
            regulation_type=control.regulation_type,
            title=f"Gap in {control.title}",
            description=f"{gap_type.replace('_', ' ').title()}: {control.description[:200]}",
            severity=severity,
            current_state=current_state,
            required_state=required_state,
            gap_type=gap_type,
            estimated_effort_hours=effort,
            priority=priority,
        )

        return gap

    def _create_remediation_action(
        self,
        gap: Gap,
        control: Control,
        target_days: int,
    ) -> RemediationAction:
        """
        Create remediation action for gap.

        Args:
            gap: Gap to remediate
            control: Control definition
            target_days: Days to complete

        Returns:
            Remediation action
        """
        # Determine due date based on priority
        if gap.priority == 1:  # Highest priority
            due_offset = min(30, target_days // 4)
        elif gap.priority == 2:
            due_offset = min(60, target_days // 2)
        elif gap.priority == 3:
            due_offset = min(90, target_days * 3 // 4)
        else:
            due_offset = target_days

        # Generate action description
        if gap.gap_type == "missing_control":
            description = f"Implement {control.title}. {control.description}"
        elif gap.gap_type == "partial_implementation":
            description = f"Complete implementation of {control.title}. Current gaps: {gap.current_state}"
        elif gap.gap_type == "insufficient_evidence":
            description = f"Collect evidence for {control.title}. Required: {gap.required_state}"
        elif gap.gap_type == "outdated":
            description = f"Update {control.title} to current standards."
        else:
            description = f"Review and remediate {control.title}."

        # Add test procedure to description
        if control.test_procedure:
            description += f"\n\nTest Procedure: {control.test_procedure}"

        action = RemediationAction(
            gap_id=gap.gap_id,
            title=f"Remediate: {control.title}",
            description=description,
            due_date=datetime.utcnow() + timedelta(days=due_offset),
            estimated_hours=gap.estimated_effort_hours,
            status=RemediationStatus.NOT_STARTED,
        )

        return action

    def _determine_gap_severity(self, control: Control) -> ViolationSeverity:
        """Determine severity of gap based on control."""
        # Security and privacy controls are high/critical
        if control.category in [ControlCategory.SECURITY, ControlCategory.PRIVACY]:
            return ViolationSeverity.HIGH if control.mandatory else ViolationSeverity.MEDIUM

        # Governance and technical controls are medium
        if control.category in [ControlCategory.GOVERNANCE, ControlCategory.TECHNICAL]:
            return ViolationSeverity.MEDIUM if control.mandatory else ViolationSeverity.LOW

        # Others are low
        return ViolationSeverity.LOW

    def _estimate_gap_effort(self, gap_type: str, category: ControlCategory) -> int:
        """Estimate effort hours for gap."""
        key = (gap_type, category)
        return EFFORT_ESTIMATES.get(key, 40)  # Default 40 hours

    def _determine_gap_priority(
        self,
        control: Control,
        severity: ViolationSeverity,
    ) -> int:
        """Determine gap priority (1=highest, 5=lowest)."""
        # Critical severity = priority 1
        if severity == ViolationSeverity.CRITICAL:
            return 1

        # High severity mandatory = priority 1
        if severity == ViolationSeverity.HIGH and control.mandatory:
            return 1

        # High severity optional = priority 2
        if severity == ViolationSeverity.HIGH:
            return 2

        # Medium severity mandatory = priority 2
        if severity == ViolationSeverity.MEDIUM and control.mandatory:
            return 2

        # Medium severity optional = priority 3
        if severity == ViolationSeverity.MEDIUM:
            return 3

        # Low severity mandatory = priority 3
        if severity == ViolationSeverity.LOW and control.mandatory:
            return 3

        # Low severity optional = priority 4
        if severity == ViolationSeverity.LOW:
            return 4

        # Informational = priority 5
        return 5

    @staticmethod
    def _severity_to_priority(severity: ViolationSeverity) -> int:
        """Convert severity to priority number (lower = higher priority)."""
        return {
            ViolationSeverity.CRITICAL: 0,
            ViolationSeverity.HIGH: 1,
            ViolationSeverity.MEDIUM: 2,
            ViolationSeverity.LOW: 3,
            ViolationSeverity.INFORMATIONAL: 4,
        }.get(severity, 5)
