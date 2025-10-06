"""Principialism Ethics Framework.

Implements the four principles approach (Beauchamp & Childress) adapted for
cybersecurity: Beneficence, Non-maleficence, Autonomy, and Justice.

Core Principles:
1. Beneficence: Obligation to do good and maximize benefits
2. Non-maleficence: Obligation to avoid harm (primum non nocere)
3. Autonomy: Respect for the decision-making capacity of individuals
4. Justice: Fair distribution of benefits, risks, and costs
"""

import time
from typing import Any, Dict, List

from .base import ActionContext, EthicalFramework, EthicalFrameworkResult, EthicalVerdict


class PrinciplismFramework(EthicalFramework):
    """Four principles ethics framework."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize principialism framework.

        Args:
            config: Configuration with principle weights and thresholds
        """
        super().__init__(config)

        # Principle weights
        self.weights = (
            config.get(
                "weights",
                {
                    "beneficence": 0.25,
                    "non_maleficence": 0.35,  # "First, do no harm" gets highest weight
                    "autonomy": 0.20,
                    "justice": 0.20,
                },
            )
            if config
            else {
                "beneficence": 0.25,
                "non_maleficence": 0.35,
                "autonomy": 0.20,
                "justice": 0.20,
            }
        )

        # Approval threshold
        self.approval_threshold = (
            config.get("approval_threshold", 0.65) if config else 0.65
        )

    def get_framework_principles(self) -> List[str]:
        """Get principialism principles.

        Returns:
            List of four core principles
        """
        return [
            "Beneficence: Obligation to do good and maximize benefits",
            "Non-maleficence: Primum non nocere - First, do no harm",
            "Autonomy: Respect for human decision-making capacity",
            "Justice: Fair distribution of benefits, risks, and costs",
        ]

    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Evaluate action using four principles.

        Args:
            action_context: Context about the action

        Returns:
            EthicalFrameworkResult with principialism verdict
        """
        start_time = time.time()
        reasoning_steps = []
        metadata = {}

        reasoning_steps.append("Evaluating action against four principles...")

        # Principle 1: Beneficence
        reasoning_steps.append("1. Beneficence (obligation to do good)...")
        beneficence_score = self._assess_beneficence(action_context)
        metadata["beneficence_score"] = beneficence_score
        reasoning_steps.append(f"   Score: {beneficence_score:.3f}")

        # Principle 2: Non-maleficence
        reasoning_steps.append("2. Non-maleficence (avoid harm)...")
        non_maleficence_score = self._assess_non_maleficence(action_context)
        metadata["non_maleficence_score"] = non_maleficence_score
        reasoning_steps.append(f"   Score: {non_maleficence_score:.3f}")

        # Principle 3: Autonomy
        reasoning_steps.append("3. Autonomy (respect decision-making capacity)...")
        autonomy_score = self._assess_autonomy(action_context)
        metadata["autonomy_score"] = autonomy_score
        reasoning_steps.append(f"   Score: {autonomy_score:.3f}")

        # Principle 4: Justice
        reasoning_steps.append("4. Justice (fair distribution)...")
        justice_score = self._assess_justice(action_context)
        metadata["justice_score"] = justice_score
        reasoning_steps.append(f"   Score: {justice_score:.3f}")

        # Check for principle conflicts
        reasoning_steps.append("Analyzing principle conflicts...")
        conflicts = self._identify_conflicts(
            beneficence_score, non_maleficence_score, autonomy_score, justice_score
        )
        metadata["principle_conflicts"] = conflicts

        if conflicts:
            reasoning_steps.append(f"   ⚠️  Conflicts detected: {', '.join(conflicts)}")
        else:
            reasoning_steps.append("   ✓ No major conflicts between principles")

        # Calculate weighted score
        weighted_score = (
            beneficence_score * self.weights["beneficence"]
            + non_maleficence_score * self.weights["non_maleficence"]
            + autonomy_score * self.weights["autonomy"]
            + justice_score * self.weights["justice"]
        )

        metadata["weighted_score"] = weighted_score
        reasoning_steps.append(
            f"Weighted principle score: {weighted_score:.3f} (threshold: {self.approval_threshold})"
        )

        # Apply conflict penalty if serious conflicts exist
        if len(conflicts) > 0:
            conflict_penalty = len(conflicts) * 0.05
            final_score = weighted_score - conflict_penalty
            reasoning_steps.append(f"Conflict penalty applied: -{conflict_penalty:.3f}")
        else:
            final_score = weighted_score

        metadata["final_score"] = final_score

        # Decision
        approved = final_score >= self.approval_threshold
        confidence = min(abs(final_score - 0.5) * 2, 1.0)

        if approved:
            explanation = f"Action satisfies four principles (score: {final_score:.3f} ≥ {self.approval_threshold})"
            verdict = EthicalVerdict.APPROVED
            reasoning_steps.append(f"✅ {explanation}")
        else:
            explanation = f"Action violates or conflicts with principles (score: {final_score:.3f} < {self.approval_threshold})"
            verdict = EthicalVerdict.REJECTED
            reasoning_steps.append(f"❌ {explanation}")

        latency_ms = int((time.time() - start_time) * 1000)

        return EthicalFrameworkResult(
            framework_name="principialism",
            approved=approved,
            confidence=confidence,
            veto=False,  # Principialism does not veto
            explanation=explanation,
            reasoning_steps=reasoning_steps,
            verdict=verdict,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    def _assess_beneficence(self, action_context: ActionContext) -> float:
        """Assess beneficence (obligation to do good).

        Args:
            action_context: Action context

        Returns:
            Beneficence score (0.0 to 1.0)
        """
        score = 0.5  # Start neutral

        # Does action provide clear benefit?
        if action_context.threat_data:
            threat_severity = action_context.threat_data.get("severity", 0.0)
            people_protected = action_context.threat_data.get("people_protected", 0)

            # Benefit proportional to threat severity and people protected
            benefit_magnitude = (
                threat_severity + min(people_protected / 1000, 1.0)
            ) / 2
            score += benefit_magnitude * 0.5

        # Does action improve future security?
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("improves_defenses"):
                score += 0.2

            if action_context.impact_assessment.get("knowledge_gain"):
                score += 0.15

        # Is the action type inherently beneficent?
        beneficent_actions = [
            "threat_mitigation",
            "vulnerability_patching",
            "security_improvement",
        ]
        if action_context.action_type in beneficent_actions:
            score += 0.1

        return min(score, 1.0)

    def _assess_non_maleficence(self, action_context: ActionContext) -> float:
        """Assess non-maleficence (avoid harm - primum non nocere).

        Args:
            action_context: Action context

        Returns:
            Non-maleficence score (0.0 to 1.0)
        """
        score = 1.0  # Start at perfect (no harm)

        # Check for potential harms
        if action_context.impact_assessment:
            # Service disruption is harm
            disruption_level = action_context.impact_assessment.get(
                "disruption_level", 0.0
            )
            score -= disruption_level * 0.4

            # Collateral damage
            if action_context.impact_assessment.get("collateral_damage_risk"):
                score -= 0.3

            # Privacy violations
            if action_context.impact_assessment.get("privacy_violation_risk"):
                score -= 0.25

            # Data loss risk
            if action_context.impact_assessment.get("data_loss_risk"):
                score -= 0.35

        # Offensive actions carry inherent harm risk
        if action_context.action_type == "offensive_action":
            score -= 0.2

        # False positive harm (wrongly accusing/blocking)
        if action_context.threat_data:
            confidence = action_context.threat_data.get("confidence", 0.9)
            false_positive_risk = 1.0 - confidence
            score -= false_positive_risk * 0.3

        return max(score, 0.0)

    def _assess_autonomy(self, action_context: ActionContext) -> float:
        """Assess autonomy (respect for decision-making capacity).

        Args:
            action_context: Action context

        Returns:
            Autonomy score (0.0 to 1.0)
        """
        score = 0.5  # Start neutral

        # Human involvement preserves autonomy
        if action_context.operator_context:
            score += 0.3

        # Automated decisions without human review reduce autonomy
        if not action_context.operator_context:
            if action_context.urgency == "critical":
                score += 0.1  # Acceptable automation in emergencies
            elif action_context.urgency == "low":
                score -= 0.3  # Unacceptable automation when time permits

        # Does action preserve user choice?
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("preserves_user_choice"):
                score += 0.25

            # Forced actions reduce autonomy
            if action_context.impact_assessment.get("forced_action"):
                score -= 0.35

        # Informed consent?
        if action_context.action_type in ["data_access", "surveillance"]:
            if action_context.threat_data and action_context.threat_data.get(
                "informed_consent"
            ):
                score += 0.2
            else:
                score -= 0.25  # No consent is autonomy violation

        # Override capability preserved?
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("override_capability_preserved"):
                score += 0.15

        return min(max(score, 0.0), 1.0)

    def _assess_justice(self, action_context: ActionContext) -> float:
        """Assess justice (fair distribution of benefits, risks, costs).

        Args:
            action_context: Action context

        Returns:
            Justice score (0.0 to 1.0)
        """
        score = 0.7  # Start with presumption of fairness

        # Distributive justice: fair distribution of benefits and burdens
        if action_context.threat_data and action_context.impact_assessment:
            people_protected = action_context.threat_data.get("people_protected", 0)
            people_impacted = action_context.impact_assessment.get("people_impacted", 0)

            # If many protected but few harmed, that's just
            if people_protected > people_impacted * 5:
                score += 0.2

            # If few protected but many harmed, that's unjust
            if people_impacted > people_protected * 2:
                score -= 0.3

        # Procedural justice: fair process
        if action_context.alternatives and len(action_context.alternatives) > 1:
            score += 0.1  # Considered alternatives = fair process

        if action_context.operator_context:
            score += 0.1  # Human review = fair process

        # Equal treatment: similar cases treated similarly
        # (This would require historical comparison - simplified here)
        if action_context.threat_data:
            if action_context.threat_data.get("consistent_with_precedent"):
                score += 0.15

        # Compensatory justice: compensate for harms
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("compensation_provided"):
                score += 0.1

        # Bias/discrimination check
        if action_context.target_info:
            # Check for protected characteristics being used as decision factors
            if action_context.target_info.get("decision_based_on_protected_class"):
                score -= 0.5  # Major injustice

        return min(max(score, 0.0), 1.0)

    def _identify_conflicts(
        self,
        beneficence: float,
        non_maleficence: float,
        autonomy: float,
        justice: float,
    ) -> List[str]:
        """Identify conflicts between principles.

        Args:
            beneficence: Beneficence score
            non_maleficence: Non-maleficence score
            autonomy: Autonomy score
            justice: Justice score

        Returns:
            List of conflict descriptions
        """
        conflicts = []

        # Beneficence vs. Non-maleficence (doing good vs. avoiding harm)
        if beneficence > 0.7 and non_maleficence < 0.5:
            conflicts.append(
                "Beneficence-Nonmaleficence: Action does good but causes harm"
            )

        # Beneficence vs. Autonomy (doing good vs. respecting choice)
        if beneficence > 0.7 and autonomy < 0.4:
            conflicts.append(
                "Beneficence-Autonomy: Action benefits but overrides autonomy"
            )

        # Non-maleficence vs. Justice (avoiding harm vs. fairness)
        if non_maleficence < 0.5 and justice > 0.7:
            conflicts.append("Nonmaleficence-Justice: Action is fair but causes harm")

        # Autonomy vs. Justice (individual choice vs. collective fairness)
        if autonomy > 0.7 and justice < 0.5:
            conflicts.append(
                "Autonomy-Justice: Respects autonomy but distributively unfair"
            )

        return conflicts
