"""Kantian Deontological Ethics Framework.

Implements Kant's categorical imperative and humanity formula for autonomous
cybersecurity systems. This framework has VETO power over other frameworks.

Core Principles:
1. Categorical Imperative: Act only according to maxims that can be universalized
2. Humanity Formula: Treat humanity as an end, never merely as a means
3. Kingdom of Ends: Act as if you were legislating for all rational beings
"""

import time
from typing import Any

from .base import (
    ActionContext,
    EthicalFramework,
    EthicalFrameworkResult,
    EthicalVerdict,
    VetoException,
)


class KantianImperativeChecker(EthicalFramework):
    """Kantian deontological ethics checker with veto power."""

    # Categorical rules that ALWAYS apply (deontological absolutes)
    CATEGORICAL_NEVER = [
        "use_humans_as_mere_means",
        "violate_human_dignity",
        "violate_human_autonomy",
        "implement_surveillance_without_consent",
        "make_irreversible_decisions_without_human_review",
        "deploy_offensive_autonomously_without_approval",
        "access_private_data_without_justification",
        "harm_innocents_as_collateral",
    ]

    CATEGORICAL_ALWAYS = [
        "preserve_human_override_capability",
        "maintain_transparency_in_decisions",
        "respect_privacy_as_inviolable_right",
        "provide_explanation_for_actions",
        "prioritize_human_safety_over_efficiency",
        "obtain_informed_consent_when_possible",
    ]

    def __init__(self, config: dict[str, Any] = None):
        """Initialize Kantian checker.

        Args:
            config: Configuration with categorical rules and veto settings
        """
        super().__init__(config)
        self.veto_enabled = config.get("veto_enabled", True) if config else True
        self.strict_mode = config.get("strict_mode", True) if config else True

    def get_framework_principles(self) -> list[str]:
        """Get Kantian principles.

        Returns:
            List of core Kantian principles
        """
        return [
            "Categorical Imperative: Act only according to maxims that can be universalized",
            "Humanity Formula: Treat humanity as an end, never merely as a means",
            "Kingdom of Ends: Act as if legislating for all rational beings",
            "Autonomy Principle: Respect the autonomy of all rational agents",
            "Dignity Principle: Preserve human dignity at all costs",
        ]

    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Evaluate action using Kantian deontological ethics.

        Args:
            action_context: Context about the action

        Returns:
            EthicalFrameworkResult with Kantian verdict

        Raises:
            VetoException: If action violates categorical imperatives and veto is enabled
        """
        start_time = time.time()
        reasoning_steps = []
        metadata = {}

        # Step 1: Check categorical rules (NEVER list)
        reasoning_steps.append("Checking categorical prohibitions (NEVER rules)...")
        violated_never_rules = self._check_never_rules(action_context)

        if violated_never_rules:
            explanation = f"Violates categorical prohibition(s): {', '.join(violated_never_rules)}"
            reasoning_steps.append(f"❌ VETO: {explanation}")

            latency_ms = int((time.time() - start_time) * 1000)

            result = EthicalFrameworkResult(
                framework_name="kantian_deontology",
                approved=False,
                confidence=1.0,  # Categorical rules are certain
                veto=True,
                explanation=explanation,
                reasoning_steps=reasoning_steps,
                verdict=EthicalVerdict.REJECTED,
                latency_ms=latency_ms,
                metadata={
                    "violated_rules": violated_never_rules,
                    "rule_type": "categorical_prohibition",
                    "universalizability_passed": False,
                    "humanity_formula_passed": False,
                },
            )

            if self.veto_enabled:
                raise VetoException("kantian_deontology", explanation)

            return result

        reasoning_steps.append("✓ No categorical prohibitions violated")

        # Step 2: Check categorical obligations (ALWAYS list)
        reasoning_steps.append("Checking categorical obligations (ALWAYS rules)...")
        violated_always_rules = self._check_always_rules(action_context)

        if violated_always_rules:
            explanation = f"Fails to fulfill categorical obligation(s): {', '.join(violated_always_rules)}"
            reasoning_steps.append(f"❌ VETO: {explanation}")

            latency_ms = int((time.time() - start_time) * 1000)

            result = EthicalFrameworkResult(
                framework_name="kantian_deontology",
                approved=False,
                confidence=1.0,
                veto=True,
                explanation=explanation,
                reasoning_steps=reasoning_steps,
                verdict=EthicalVerdict.REJECTED,
                latency_ms=latency_ms,
                metadata={
                    "violated_rules": violated_always_rules,
                    "rule_type": "categorical_obligation",
                    "universalizability_passed": False,
                    "humanity_formula_passed": False,
                },
            )

            if self.veto_enabled:
                raise VetoException("kantian_deontology", explanation)

            return result

        reasoning_steps.append("✓ All categorical obligations satisfied")

        # Step 3: Universalizability Test (First Formulation)
        reasoning_steps.append("Testing universalizability (First Formulation)...")
        universalizability_result = self._test_universalizability(action_context)

        metadata["universalizability_passed"] = universalizability_result["passed"]
        metadata["universalizability_details"] = universalizability_result["details"]

        if not universalizability_result["passed"]:
            explanation = f"Fails universalizability test: {universalizability_result['reason']}"
            reasoning_steps.append(f"❌ {explanation}")

            latency_ms = int((time.time() - start_time) * 1000)

            return EthicalFrameworkResult(
                framework_name="kantian_deontology",
                approved=False,
                confidence=0.95,
                veto=self.veto_enabled,
                explanation=explanation,
                reasoning_steps=reasoning_steps,
                verdict=EthicalVerdict.REJECTED,
                latency_ms=latency_ms,
                metadata=metadata,
            )

        reasoning_steps.append(f"✓ Universalizability test passed: {universalizability_result['details']}")

        # Step 4: Humanity Formula Test (Second Formulation)
        reasoning_steps.append("Testing humanity formula (Second Formulation)...")
        humanity_result = self._test_humanity_formula(action_context)

        metadata["humanity_formula_passed"] = humanity_result["passed"]
        metadata["humanity_formula_details"] = humanity_result["details"]

        if not humanity_result["passed"]:
            explanation = f"Violates humanity formula: {humanity_result['reason']}"
            reasoning_steps.append(f"❌ {explanation}")

            latency_ms = int((time.time() - start_time) * 1000)

            return EthicalFrameworkResult(
                framework_name="kantian_deontology",
                approved=False,
                confidence=0.95,
                veto=self.veto_enabled,
                explanation=explanation,
                reasoning_steps=reasoning_steps,
                verdict=EthicalVerdict.REJECTED,
                latency_ms=latency_ms,
                metadata=metadata,
            )

        reasoning_steps.append(f"✓ Humanity formula satisfied: {humanity_result['details']}")

        # All tests passed!
        explanation = "Action passes all Kantian deontological tests"
        reasoning_steps.append(f"✅ {explanation}")

        latency_ms = int((time.time() - start_time) * 1000)

        return EthicalFrameworkResult(
            framework_name="kantian_deontology",
            approved=True,
            confidence=0.98,  # High confidence when all tests pass
            veto=False,  # No veto needed when approved
            explanation=explanation,
            reasoning_steps=reasoning_steps,
            verdict=EthicalVerdict.APPROVED,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    def _check_never_rules(self, action_context: ActionContext) -> list[str]:
        """Check if action violates categorical prohibitions.

        Args:
            action_context: Action context

        Returns:
            List of violated NEVER rules
        """
        violated = []

        action_lower = action_context.action_description.lower()
        action_type = action_context.action_type.lower()

        # FIXED: Context-aware detection to avoid false positives

        # Check for human exploitation (but allow authorized pentesting)
        if any(keyword in action_lower for keyword in ["exploit", "manipulate", "deceive"]):
            # Only flag if targeting humans without authorization
            if "human" in action_lower or "social engineering" in action_lower:
                # Exception: Authorized pentest
                is_authorized = action_context.operator_context and action_context.operator_context.get(
                    "authorized_pentest", False
                )
                if not is_authorized:
                    violated.append("use_humans_as_mere_means")

        # Dignity violations
        if any(keyword in action_lower for keyword in ["degrade", "humiliate", "violate dignity"]):
            violated.append("violate_human_dignity")

        # Autonomy violations (excluding legitimate security measures)
        autonomy_keywords = ["override autonomy", "force compliance", "remove choice"]
        if any(keyword in action_lower for keyword in autonomy_keywords):
            # Exception: Critical security situations where choice endangers others
            is_critical = action_context.urgency == "critical"
            has_justification = action_context.threat_data and action_context.threat_data.get("severity", 0) > 0.9
            if not (is_critical and has_justification):
                violated.append("violate_human_autonomy")

        # Surveillance without consent
        if "surveillance" in action_lower or "monitoring" in action_lower:
            lacks_consent = "without consent" in action_lower or not (
                action_context.threat_data and action_context.threat_data.get("informed_consent")
            )
            # Exception: Network monitoring with appropriate legal basis
            has_legal_basis = action_context.threat_data and action_context.threat_data.get("legal_basis")
            if lacks_consent and not has_legal_basis:
                violated.append("implement_surveillance_without_consent")

        # Autonomous offensive actions (no human approval)
        if action_type == "offensive_action" or "offensive" in action_lower:
            if action_context.operator_context is None:
                violated.append("deploy_offensive_autonomously_without_approval")

        # Irreversible decisions without human review
        if "irreversible" in action_lower or "permanent" in action_lower:
            if "without review" in action_lower or action_context.operator_context is None:
                # Exception: Automated blocking of active attacks (reversible via unblock)
                is_reversible_block = action_type in ["auto_response", "threat_mitigation"] and "block" in action_lower
                if not is_reversible_block:
                    violated.append("make_irreversible_decisions_without_human_review")

        # Civilian/innocent harm
        if action_context.threat_data:
            if action_context.threat_data.get("civilian_targets") or action_context.threat_data.get(
                "collateral_damage_likely"
            ):
                violated.append("harm_innocents_as_collateral")

        # Privacy violations without justification
        privacy_keywords = ["access private", "read personal", "intercept"]
        if any(keyword in action_lower for keyword in privacy_keywords):
            lacks_justification = not (action_context.threat_data and action_context.threat_data.get("justification"))
            if lacks_justification:
                violated.append("access_private_data_without_justification")

        return violated

    def _check_always_rules(self, action_context: ActionContext) -> list[str]:
        """Check if action violates categorical obligations.

        Args:
            action_context: Action context

        Returns:
            List of violated ALWAYS rules
        """
        violated = []

        # Check if action removes human override capability
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("removes_human_control"):
                violated.append("preserve_human_override_capability")

        # Check transparency
        if not action_context.action_description or len(action_context.action_description) < 20:
            violated.append("provide_explanation_for_actions")

        # Check if privacy is respected
        if action_context.action_type == "data_access":
            if not action_context.threat_data or not action_context.threat_data.get("justification"):
                violated.append("respect_privacy_as_inviolable_right")

        return violated

    def _test_universalizability(self, action_context: ActionContext) -> dict[str, Any]:
        """Test if action's maxim can be universalized without contradiction.

        Args:
            action_context: Action context

        Returns:
            Dict with 'passed', 'reason', and 'details' keys
        """
        # Universal adoption scenario: "What if ALL systems did this?"

        action_type = action_context.action_type
        action_desc = action_context.action_description.lower()

        # Test 1: Logical contradiction
        if "lie" in action_desc or "deceive" in action_desc:
            return {
                "passed": False,
                "reason": "Universal lying would destroy the institution of truth-telling",
                "details": "If all systems lied, communication would become impossible",
            }

        # Test 2: Pragmatic contradiction (undermines its own purpose)
        if action_type == "offensive_action" and "preemptive" in action_desc:
            if not action_context.threat_data or action_context.threat_data.get("confidence", 0) < 0.90:
                return {
                    "passed": False,
                    "reason": "Universal preemptive attacks without high confidence would undermine security",
                    "details": "If all systems attacked preemptively on low confidence, chaos would ensue",
                }

        # Test 3: Infrastructure collapse
        if "ddos" in action_desc or "flood" in action_desc:
            return {
                "passed": False,
                "reason": "Universal DDoS would collapse internet infrastructure",
                "details": "The action depends on infrastructure it would destroy if universalized",
            }

        # Passed all universalizability tests
        return {
            "passed": True,
            "reason": "Action can be universalized without contradiction",
            "details": "Maxim passes logical and pragmatic universalizability tests",
        }

    def _test_humanity_formula(self, action_context: ActionContext) -> dict[str, Any]:
        """Test if action treats humanity as an end, not merely as a means.

        Args:
            action_context: Action context

        Returns:
            Dict with 'passed', 'reason', and 'details' keys
        """
        # Humanity Formula: "Act in such a way that you treat humanity, whether in
        # your own person or in the person of another, always at the same time as
        # an end and never simply as a means."

        action_desc = action_context.action_description.lower()

        # Test 1: Using people without their rational consent
        if "social engineering" in action_desc:
            if not action_context.operator_context or not action_context.operator_context.get("authorized_pentest"):
                return {
                    "passed": False,
                    "reason": "Social engineering uses humans as mere means without consent",
                    "details": "Manipulating people without their knowledge violates their dignity as rational beings",
                }

        # Test 2: Sacrificing individual for collective (utilitarian calculation)
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("sacrifices_individual_rights"):
                return {
                    "passed": False,
                    "reason": "Sacrificing individual rights for collective benefit treats person as mere means",
                    "details": "Each person has inherent dignity that cannot be overridden by utility calculations",
                }

        # Test 3: Respect for autonomy
        if "auto_response" in action_context.action_type:
            if action_context.urgency == "low" and not action_context.operator_context:
                return {
                    "passed": False,
                    "reason": "Low-urgency automated responses bypass human autonomy",
                    "details": "Humans should be involved in decisions when time permits",
                }

        # Passed humanity formula test
        return {
            "passed": True,
            "reason": "Action respects humanity as an end in itself",
            "details": "Action preserves human dignity, autonomy, and rational agency",
        }
