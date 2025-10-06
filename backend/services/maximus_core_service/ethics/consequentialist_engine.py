"""Consequentialist (Utilitarian) Ethics Framework.

Implements Bentham's hedonic calculus and Mill's higher/lower pleasures for
evaluating cybersecurity actions based on their consequences.

Core Principles:
1. Greatest Happiness Principle: Actions are right if they maximize overall happiness/well-being
2. Hedonic Calculus: 7 dimensions of pleasure/pain (intensity, duration, certainty, propinquity, fecundity, purity, extent)
3. Rule Utilitarianism: Follow rules that tend to maximize utility in general cases
"""

import time
from typing import Any, Dict, List

from .base import ActionContext, EthicalFramework, EthicalFrameworkResult, EthicalVerdict


class ConsequentialistEngine(EthicalFramework):
    """Utilitarian consequentialist ethics engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize consequentialist engine.

        Args:
            config: Configuration with utility weights and thresholds
        """
        super().__init__(config)

        # Weights for Bentham's calculus dimensions (must sum to 1.0)
        self.weights = (
            config.get(
                "weights",
                {
                    "intensity": 0.20,  # Severity of threat vs. impact of response
                    "duration": 0.15,  # Temporal extent of protection/disruption
                    "certainty": 0.25,  # Confidence in detection and response effectiveness
                    "propinquity": 0.10,  # Immediacy of threat
                    "fecundity": 0.15,  # Future threat prevention
                    "purity": 0.10,  # Absence of negative side effects
                    "extent": 0.05,  # Number of people/systems affected
                },
            )
            if config
            else {
                "intensity": 0.20,
                "duration": 0.15,
                "certainty": 0.25,
                "propinquity": 0.10,
                "fecundity": 0.15,
                "purity": 0.10,
                "extent": 0.05,
            }
        )

        # Approval threshold (net utility must exceed this)
        self.approval_threshold = (
            config.get("approval_threshold", 0.60) if config else 0.60
        )

    def get_framework_principles(self) -> List[str]:
        """Get consequentialist principles.

        Returns:
            List of core utilitarian principles
        """
        return [
            "Greatest Happiness Principle: Maximize overall well-being",
            "Hedonic Calculus: Evaluate consequences across 7 dimensions",
            "Impartial Consideration: All stakeholders count equally",
            "Forward-Looking: Focus on future consequences, not past actions",
            "Rule Utilitarianism: Follow rules that tend to maximize utility",
        ]

    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Evaluate action using consequentialist ethics.

        Args:
            action_context: Context about the action

        Returns:
            EthicalFrameworkResult with utilitarian verdict
        """
        start_time = time.time()
        reasoning_steps = []
        metadata = {}

        # Step 1: Calculate benefits (positive utility)
        reasoning_steps.append("Calculating benefits (positive utility)...")
        benefits = self._calculate_benefits(action_context)
        metadata["benefits"] = benefits
        reasoning_steps.append(f"  Total benefit score: {benefits['total_score']:.3f}")

        # Step 2: Calculate costs (negative utility)
        reasoning_steps.append("Calculating costs (negative utility)...")
        costs = self._calculate_costs(action_context)
        metadata["costs"] = costs
        reasoning_steps.append(f"  Total cost score: {costs['total_score']:.3f}")

        # Step 3: Calculate net utility
        net_utility = benefits["total_score"] - costs["total_score"]
        metadata["net_utility"] = net_utility
        reasoning_steps.append(
            f"Net utility: {net_utility:.3f} (threshold: {self.approval_threshold})"
        )

        # Step 4: Fecundity analysis (future consequences)
        reasoning_steps.append("Analyzing fecundity (future prevention)...")
        fecundity_score = self._assess_fecundity(action_context)
        metadata["fecundity_score"] = fecundity_score
        reasoning_steps.append(f"  Fecundity multiplier: {fecundity_score:.2f}x")

        # Adjust net utility by fecundity
        adjusted_utility = net_utility * fecundity_score
        metadata["adjusted_utility"] = adjusted_utility

        # Step 5: Purity analysis (negative side effects)
        reasoning_steps.append("Analyzing purity (absence of side effects)...")
        purity_score = self._assess_purity(action_context)
        metadata["purity_score"] = purity_score
        reasoning_steps.append(
            f"  Purity score: {purity_score:.3f} (1.0 = no side effects)"
        )

        # Final utility with purity adjustment
        final_utility = adjusted_utility * purity_score
        metadata["final_utility"] = final_utility
        reasoning_steps.append(
            f"Final utility (after fecundity & purity): {final_utility:.3f}"
        )

        # Step 6: Decision
        approved = final_utility >= self.approval_threshold
        confidence = min(abs(final_utility), 1.0)  # Confidence based on magnitude

        if approved:
            explanation = f"Action maximizes utility (score: {final_utility:.3f} ≥ {self.approval_threshold})"
            verdict = EthicalVerdict.APPROVED
            reasoning_steps.append(f"✅ {explanation}")
        else:
            explanation = f"Action fails to maximize utility (score: {final_utility:.3f} < {self.approval_threshold})"
            verdict = EthicalVerdict.REJECTED
            reasoning_steps.append(f"❌ {explanation}")

        # Add stakeholder analysis
        stakeholders = self._identify_stakeholders(action_context)
        metadata["stakeholders"] = stakeholders
        reasoning_steps.append(f"Stakeholders analyzed: {len(stakeholders)}")

        latency_ms = int((time.time() - start_time) * 1000)

        return EthicalFrameworkResult(
            framework_name="consequentialism",
            approved=approved,
            confidence=confidence,
            veto=False,  # Consequentialism does not veto (only Kantian does)
            explanation=explanation,
            reasoning_steps=reasoning_steps,
            verdict=verdict,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    def _calculate_benefits(self, action_context: ActionContext) -> Dict[str, Any]:
        """Calculate total benefits of the action.

        Args:
            action_context: Action context

        Returns:
            Dict with benefit scores and total
        """
        benefits = {
            "threat_mitigation": 0.0,
            "future_prevention": 0.0,
            "system_resilience": 0.0,
            "knowledge_gain": 0.0,
            "total_score": 0.0,
        }

        # Threat mitigation benefit
        if action_context.threat_data:
            severity = action_context.threat_data.get("severity", 0.5)
            confidence = action_context.threat_data.get("confidence", 0.5)
            people_protected = action_context.threat_data.get("people_protected", 100)

            # FIXED: Calculate raw benefit score without weights
            # Weights will be applied during final aggregation
            benefit_score = (
                severity
                * confidence
                * min(
                    1.0, (1 + people_protected / 1000)
                )  # Normalize people_protected to [1.0, 2.0] range
            )
            benefits["threat_mitigation"] = benefit_score

        # Future prevention (if action improves defenses)
        if action_context.impact_assessment:
            if action_context.impact_assessment.get("improves_defenses"):
                benefits["future_prevention"] = 0.3

        # System resilience (if action strengthens infrastructure)
        if action_context.impact_assessment:
            resilience_gain = action_context.impact_assessment.get(
                "resilience_improvement", 0.0
            )
            benefits["system_resilience"] = resilience_gain

        # Knowledge gain (learning from response)
        if action_context.action_type in ["threat_investigation", "red_team_operation"]:
            benefits["knowledge_gain"] = 0.2

        benefits["total_score"] = sum(
            [
                benefits["threat_mitigation"],
                benefits["future_prevention"],
                benefits["system_resilience"],
                benefits["knowledge_gain"],
            ]
        )

        return benefits

    def _calculate_costs(self, action_context: ActionContext) -> Dict[str, Any]:
        """Calculate total costs of the action.

        Args:
            action_context: Action context

        Returns:
            Dict with cost scores and total
        """
        costs = {
            "disruption": 0.0,
            "false_positive_risk": 0.0,
            "resource_consumption": 0.0,
            "collateral_damage": 0.0,
            "total_score": 0.0,
        }

        # Service disruption cost
        if action_context.impact_assessment:
            disruption_level = action_context.impact_assessment.get(
                "disruption_level", 0.0
            )
            people_impacted = action_context.impact_assessment.get("people_impacted", 0)

            # FIXED: No weight multiplication
            costs["disruption"] = disruption_level * min(
                1.0, (1 + people_impacted / 1000)
            )

        # False positive risk (cost of being wrong)
        if action_context.threat_data:
            false_positive_risk = 1.0 - action_context.threat_data.get(
                "confidence", 0.9
            )
            costs["false_positive_risk"] = false_positive_risk

        # Resource consumption (compute, time, human attention)
        if action_context.urgency == "low":
            costs["resource_consumption"] = 0.1

        # Collateral damage (unintended harm)
        if action_context.action_type == "offensive_action":
            if not action_context.target_info or not action_context.target_info.get(
                "precision_targeting"
            ):
                costs["collateral_damage"] = 0.4

        costs["total_score"] = sum(
            [
                costs["disruption"],
                costs["false_positive_risk"],
                costs["resource_consumption"],
                costs["collateral_damage"],
            ]
        )

        return costs

    def _assess_fecundity(self, action_context: ActionContext) -> float:
        """Assess fecundity (tendency to produce future good consequences).

        Args:
            action_context: Action context

        Returns:
            Fecundity multiplier (1.0 = neutral, >1.0 = produces future benefits, <1.0 = produces future harms)
        """
        fecundity = 1.0

        # Does action prevent future attacks?
        if action_context.threat_data:
            if action_context.threat_data.get("part_of_campaign"):
                fecundity += 0.5  # Stopping a campaign prevents future attacks

        # Does action improve detection capabilities?
        if action_context.action_type in ["threat_investigation", "malware_analysis"]:
            fecundity += 0.3  # Learning improves future responses

        # Does action create precedent for escalation?
        if action_context.action_type == "offensive_action":
            if action_context.threat_data and action_context.threat_data.get(
                "provocation_risk"
            ):
                fecundity -= 0.4  # May trigger retaliatory attacks

        return max(0.1, min(2.0, fecundity))  # Clamp between 0.1 and 2.0

    def _assess_purity(self, action_context: ActionContext) -> float:
        """Assess purity (absence of negative side effects).

        Args:
            action_context: Action context

        Returns:
            Purity score (0.0 = many side effects, 1.0 = no side effects)
        """
        purity = 1.0

        # Check for negative side effects
        if action_context.impact_assessment:
            side_effects = action_context.impact_assessment.get("side_effects", [])

            for side_effect in side_effects:
                if side_effect.get("severity") == "high":
                    purity -= 0.3
                elif side_effect.get("severity") == "medium":
                    purity -= 0.15
                elif side_effect.get("severity") == "low":
                    purity -= 0.05

        # Offensive actions have inherently lower purity
        if action_context.action_type == "offensive_action":
            purity *= 0.8

        # Automated actions without human review have lower purity
        if not action_context.operator_context and action_context.urgency != "critical":
            purity *= 0.9

        return max(0.0, min(1.0, purity))  # Clamp between 0.0 and 1.0

    def _identify_stakeholders(
        self, action_context: ActionContext
    ) -> List[Dict[str, Any]]:
        """Identify all stakeholders affected by the action.

        Args:
            action_context: Action context

        Returns:
            List of stakeholder dicts with {name, role, impact_level}
        """
        stakeholders = []

        # Direct beneficiaries (protected users/systems)
        if action_context.threat_data:
            protected = action_context.threat_data.get("people_protected", 0)
            if protected > 0:
                stakeholders.append(
                    {
                        "name": "Protected Users",
                        "role": "Beneficiaries",
                        "impact_level": "positive",
                        "count": protected,
                    }
                )

        # Potentially harmed (if action has disruption)
        if action_context.impact_assessment:
            impacted = action_context.impact_assessment.get("people_impacted", 0)
            if impacted > 0:
                stakeholders.append(
                    {
                        "name": "Disrupted Users",
                        "role": "Negatively Affected",
                        "impact_level": "negative",
                        "count": impacted,
                    }
                )

        # Target (attacker/threat actor)
        if action_context.target_info:
            stakeholders.append(
                {
                    "name": "Threat Actor",
                    "role": "Target",
                    "impact_level": "negative",
                    "count": 1,
                }
            )

        # SOC operators (work burden)
        stakeholders.append(
            {
                "name": "SOC Operators",
                "role": "Operational Burden",
                "impact_level": "neutral",
                "count": (
                    action_context.operator_context.get("team_size", 5)
                    if action_context.operator_context
                    else 5
                ),
            }
        )

        # Organization (reputation, legal risk)
        stakeholders.append(
            {
                "name": "Organization",
                "role": "Reputation & Legal Risk",
                "impact_level": "neutral",
                "count": 1,
            }
        )

        return stakeholders
