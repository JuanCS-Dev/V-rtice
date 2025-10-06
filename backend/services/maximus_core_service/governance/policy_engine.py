"""
Governance Module - Policy Enforcement Engine

Enforces ethical policies across the VÉRTICE platform. Validates actions against
policy rules, detects violations, and triggers automated enforcement actions.

Integrates with:
- Ethics module (framework decisions)
- HITL module (human oversight)
- XAI module (explainability)
- Compliance module (regulatory compliance)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import re

from .base import (
    GovernanceAction,
    GovernanceConfig,
    Policy,
    PolicyEnforcementResult,
    PolicySeverity,
    PolicyType,
    PolicyViolation,
)
from .policies import PolicyRegistry


class PolicyEngine:
    """
    Policy Enforcement Engine.

    Validates actions against ethical policies and detects violations.
    Provides automated enforcement for critical policy violations.

    Performance Target: <20ms for policy checks
    """

    def __init__(self, config: GovernanceConfig):
        """Initialize policy engine."""
        self.config = config
        self.policy_registry = PolicyRegistry()
        self.violation_count = 0
        self.enforcement_count = 0

        # Cache for frequently accessed policies
        self._policy_cache: Dict[PolicyType, Policy] = {}

    # ========================================================================
    # POLICY ENFORCEMENT
    # ========================================================================

    def enforce_policy(
        self,
        policy_type: PolicyType,
        action: str,
        context: Dict[str, Any],
        actor: str = "system",
    ) -> PolicyEnforcementResult:
        """
        Enforce a policy against a proposed action.

        Args:
            policy_type: Type of policy to enforce
            action: Action being proposed (e.g., "block_ip", "execute_exploit")
            context: Context dictionary with action parameters
            actor: User or system proposing the action

        Returns:
            PolicyEnforcementResult with violations if any
        """
        policy = self.policy_registry.get_policy(policy_type)

        if not policy.auto_enforce and not self.config.auto_enforce_policies:
            return PolicyEnforcementResult(
                is_compliant=True,
                policy_id=policy.policy_id,
                policy_type=policy_type,
                checked_rules=0,
                passed_rules=0,
                failed_rules=0,
                warnings=["Auto-enforcement disabled for this policy"],
            )

        # Check all rules
        violations = []
        checked_rules = 0
        passed_rules = 0
        failed_rules = 0

        for rule in policy.rules:
            checked_rules += 1
            violation = self._check_rule(
                rule, action, context, policy, actor
            )

            if violation:
                violations.append(violation)
                failed_rules += 1
            else:
                passed_rules += 1

        is_compliant = len(violations) == 0

        return PolicyEnforcementResult(
            is_compliant=is_compliant,
            policy_id=policy.policy_id,
            policy_type=policy_type,
            checked_rules=checked_rules,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            violations=violations,
        )

    def enforce_all_policies(
        self,
        action: str,
        context: Dict[str, Any],
        actor: str = "system",
    ) -> Dict[PolicyType, PolicyEnforcementResult]:
        """
        Enforce all policies against an action.

        Args:
            action: Action being proposed
            context: Context dictionary
            actor: Actor proposing action

        Returns:
            Dict mapping PolicyType to enforcement results
        """
        results = {}

        for policy_type in PolicyType:
            results[policy_type] = self.enforce_policy(
                policy_type, action, context, actor
            )

        return results

    def _check_rule(
        self,
        rule: str,
        action: str,
        context: Dict[str, Any],
        policy: Policy,
        actor: str,
    ) -> Optional[PolicyViolation]:
        """
        Check a single policy rule.

        Args:
            rule: Policy rule to check
            action: Action being proposed
            context: Context dictionary
            policy: Policy object
            actor: Actor

        Returns:
            PolicyViolation if rule is violated, None otherwise
        """
        # Extract rule ID and description
        match = re.match(r"RULE-([A-Z]{2})-(\d{3}):\s*(.+)", rule)
        if not match:
            return None

        rule_id = f"RULE-{match.group(1)}-{match.group(2)}"
        rule_description = match.group(3)

        # Apply rule-specific validation logic
        violated = False
        violation_description = ""

        # Ethical Use Policy Rules
        if policy.policy_type == PolicyType.ETHICAL_USE:
            violated, violation_description = self._check_ethical_use_rule(
                rule_id, action, context
            )

        # Red Teaming Policy Rules
        elif policy.policy_type == PolicyType.RED_TEAMING:
            violated, violation_description = self._check_red_teaming_rule(
                rule_id, action, context
            )

        # Data Privacy Policy Rules
        elif policy.policy_type == PolicyType.DATA_PRIVACY:
            violated, violation_description = self._check_data_privacy_rule(
                rule_id, action, context
            )

        # Incident Response Policy Rules
        elif policy.policy_type == PolicyType.INCIDENT_RESPONSE:
            violated, violation_description = self._check_incident_response_rule(
                rule_id, action, context
            )

        # Whistleblower Policy Rules
        elif policy.policy_type == PolicyType.WHISTLEBLOWER:
            violated, violation_description = self._check_whistleblower_rule(
                rule_id, action, context
            )

        if violated:
            self.violation_count += 1
            return PolicyViolation(
                policy_id=policy.policy_id,
                policy_type=policy.policy_type,
                severity=policy.enforcement_level,
                title=f"Violation of {rule_id}",
                description=violation_description,
                violated_rule=rule_description,
                detection_method="automated",
                detected_by="policy_engine",
                detected_date=datetime.utcnow(),
                affected_system=context.get("system", "unknown"),
                context=context,
                remediation_deadline=datetime.utcnow() + timedelta(days=7),
            )

        return None

    # ========================================================================
    # RULE-SPECIFIC VALIDATION
    # ========================================================================

    def _check_ethical_use_rule(
        self, rule_id: str, action: str, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check Ethical Use Policy rules."""
        if rule_id == "RULE-EU-001":
            # AI systems MUST NOT cause harm without authorization
            if action in ["block_ip", "quarantine_system", "execute_exploit"]:
                if not context.get("authorized", False):
                    return True, f"Action '{action}' attempted without proper authorization"

        elif rule_id == "RULE-EU-002":
            # Offensive capabilities MUST only be used in authorized environments
            offensive_actions = ["execute_exploit", "c2_command", "network_attack"]
            if action in offensive_actions:
                if not context.get("target_environment") in ["test", "lab", "authorized_client"]:
                    return (
                        True,
                        f"Offensive action '{action}' in non-authorized environment: "
                        f"{context.get('target_environment', 'unknown')}",
                    )

        elif rule_id == "RULE-EU-003":
            # All autonomous actions MUST be logged
            if context.get("logged", True) is False:
                return True, f"Action '{action}' is not being logged (audit trail missing)"

        elif rule_id == "RULE-EU-004":
            # No life-or-death decisions without human oversight
            critical_actions = ["shutdown_critical_system", "medical_decision"]
            if action in critical_actions:
                if not context.get("human_oversight", False):
                    return True, f"Critical action '{action}' lacks human oversight (HITL required)"

        elif rule_id == "RULE-EU-005":
            # No discrimination based on protected attributes
            if context.get("protected_attribute_used", False):
                return (
                    True,
                    f"Action '{action}' uses protected attributes in decision-making "
                    f"(attribute: {context.get('attribute_name', 'unknown')})",
                )

        elif rule_id == "RULE-EU-006":
            # XAI requirement for critical decisions
            if context.get("decision_criticality", "low") == "high":
                if not context.get("explanation_provided", False):
                    return (
                        True,
                        f"Critical action '{action}' lacks explanation (XAI required)",
                    )

        elif rule_id == "RULE-EU-010":
            # HITL for high-risk actions
            if context.get("risk_score", 0.0) > 0.8:
                if not context.get("hitl_approved", False):
                    return (
                        True,
                        f"High-risk action '{action}' (risk={context.get('risk_score')}) "
                        "lacks HITL approval",
                    )

        return False, ""

    def _check_red_teaming_rule(
        self, rule_id: str, action: str, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check Red Teaming Policy rules."""
        if rule_id == "RULE-RT-001":
            # Written authorization required
            red_team_actions = [
                "execute_exploit",
                "social_engineering_campaign",
                "network_attack",
            ]
            if action in red_team_actions:
                if not context.get("written_authorization", False):
                    return (
                        True,
                        f"Red team action '{action}' lacks written authorization from target",
                    )

        elif rule_id == "RULE-RT-002":
            # RoE must be defined
            if action.startswith("red_team_"):
                if not context.get("roe_defined", False):
                    return (
                        True,
                        f"Red team operation '{action}' lacks defined Rules of Engagement",
                    )

        elif rule_id == "RULE-RT-003":
            # No production system targeting without approval
            if action in ["execute_exploit", "network_attack"]:
                if context.get("target_type") == "production":
                    if not context.get("production_approved", False):
                        return (
                            True,
                            f"Action '{action}' targeting production system without approval",
                        )

        elif rule_id == "RULE-RT-005":
            # Social engineering requires ERB approval
            if action == "social_engineering_campaign":
                if not context.get("erb_approved", False):
                    return (
                        True,
                        "Social engineering campaign requires ERB approval per case",
                    )

        elif rule_id == "RULE-RT-010":
            # Destructive operations require HITL
            destructive_actions = ["delete_data", "shutdown_system", "encrypt_files"]
            if action in destructive_actions:
                if not context.get("hitl_approved", False):
                    return (
                        True,
                        f"Destructive red team action '{action}' requires HITL approval",
                    )

        return False, ""

    def _check_data_privacy_rule(
        self, rule_id: str, action: str, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check Data Privacy Policy rules."""
        if rule_id == "RULE-DP-001":
            # Legal basis for personal data collection
            if action in ["collect_personal_data", "process_pii"]:
                if not context.get("legal_basis"):
                    return (
                        True,
                        f"Action '{action}' lacks legal basis (GDPR Art. 6 requirement)",
                    )

        elif rule_id == "RULE-DP-007":
            # Encryption required for personal data
            if action in ["store_personal_data", "transfer_pii"]:
                if not context.get("encrypted", False):
                    return (
                        True,
                        f"Personal data in '{action}' is not encrypted (encryption required)",
                    )

        elif rule_id == "RULE-DP-009":
            # Breach notification within 72 hours
            if action == "report_data_breach":
                breach_time = context.get("breach_detected_at")
                report_time = context.get("report_time", datetime.utcnow())
                if breach_time:
                    hours_elapsed = (report_time - breach_time).total_seconds() / 3600
                    if hours_elapsed > 72:
                        return (
                            True,
                            f"Data breach reported {hours_elapsed:.1f}h after detection "
                            "(GDPR requires 72h)",
                        )

        elif rule_id == "RULE-DP-011":
            # Automated decision-making requires human intervention option
            if action in ["automated_decision", "ai_decision"]:
                if context.get("affects_individuals", False):
                    if not context.get("human_intervention_available", False):
                        return (
                            True,
                            f"Automated decision '{action}' lacks human intervention option "
                            "(GDPR Art. 22)",
                        )

        return False, ""

    def _check_incident_response_rule(
        self, rule_id: str, action: str, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check Incident Response Policy rules."""
        if rule_id == "RULE-IR-001":
            # Incidents must be reported within 1 hour
            if action == "incident_detected":
                detection_time = context.get("detection_time", datetime.utcnow())
                current_time = datetime.utcnow()
                hours_elapsed = (current_time - detection_time).total_seconds() / 3600

                if hours_elapsed > 1 and not context.get("reported", False):
                    return (
                        True,
                        f"Incident detected {hours_elapsed:.1f}h ago but not yet reported "
                        "(1h requirement)",
                    )

        elif rule_id == "RULE-IR-002":
            # Critical incidents require ERB notification
            if action == "incident_detected":
                if context.get("severity") == "critical":
                    if not context.get("erb_notified", False):
                        return (
                            True,
                            "Critical incident detected but ERB not notified (immediate notification required)",
                        )

        return False, ""

    def _check_whistleblower_rule(
        self, rule_id: str, action: str, context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Check Whistleblower Policy rules."""
        if rule_id == "RULE-WB-002":
            # No retaliation against whistleblowers
            if action in ["terminate_employee", "disciplinary_action"]:
                if context.get("target_is_whistleblower", False):
                    return (
                        True,
                        f"Action '{action}' targets a whistleblower (retaliation prohibited)",
                    )

        elif rule_id == "RULE-WB-003":
            # Investigation within 30 days
            if action == "whistleblower_report_received":
                submission_date = context.get("submission_date")
                current_date = datetime.utcnow()
                if submission_date:
                    days_elapsed = (current_date - submission_date).days
                    if days_elapsed > 30 and context.get("investigation_status") == "not_started":
                        return (
                            True,
                            f"Whistleblower report pending investigation for {days_elapsed} days "
                            "(30-day requirement)",
                        )

        return False, ""

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def check_action(
        self,
        action: str,
        context: Dict[str, Any],
        actor: str = "system",
    ) -> Tuple[bool, List[PolicyViolation]]:
        """
        Quick check if an action is allowed across all policies.

        Args:
            action: Action to check
            context: Context dictionary
            actor: Actor

        Returns:
            Tuple of (is_allowed, violations)
        """
        all_violations = []

        for policy_type in PolicyType:
            result = self.enforce_policy(policy_type, action, context, actor)
            all_violations.extend(result.violations)

        is_allowed = len(all_violations) == 0
        return is_allowed, all_violations

    def get_applicable_policies(self, scope: str) -> List[Policy]:
        """Get policies applicable to a specific scope."""
        return self.policy_registry.get_policies_by_scope(scope)

    def get_statistics(self) -> Dict[str, int]:
        """Get policy engine statistics."""
        return {
            "total_violations_detected": self.violation_count,
            "enforcement_actions_taken": self.enforcement_count,
            "total_policies": len(self.policy_registry.get_all_policies()),
            "approved_policies": len(
                [p for p in self.policy_registry.get_all_policies() if p.approved_by_erb]
            ),
        }
