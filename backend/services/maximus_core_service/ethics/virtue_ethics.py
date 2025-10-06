"""Virtue Ethics Framework (Aristotelian).

Implements Aristotle's virtue ethics focusing on character virtues, the golden mean,
and phronesis (practical wisdom) for cybersecurity decision-making.

Core Principles:
1. Golden Mean: Virtue lies between excess and deficiency
2. Phronesis: Practical wisdom in applying virtues to situations
3. Eudaimonia: Flourishing through virtuous action
4. Cardinal Virtues: Courage, Temperance, Justice, Wisdom
"""

import time
from typing import Any, Dict, List

from .base import ActionContext, EthicalFramework, EthicalFrameworkResult, EthicalVerdict


class VirtueEthicsAssessment(EthicalFramework):
    """Aristotelian virtue ethics assessor."""

    # Cardinal virtues for cybersecurity
    CARDINAL_VIRTUES = {
        "courage": {
            "description": "Facing threats boldly but not recklessly",
            "excess": "recklessness",
            "deficiency": "cowardice",
            "golden_mean": "measured boldness",
        },
        "temperance": {
            "description": "Moderation in response, avoiding overreaction",
            "excess": "passivity",
            "deficiency": "aggression",
            "golden_mean": "proportionate response",
        },
        "justice": {
            "description": "Fair treatment of all stakeholders",
            "excess": "egalitarian paralysis",
            "deficiency": "arbitrary discrimination",
            "golden_mean": "equitable consideration",
        },
        "wisdom": {
            "description": "Practical wisdom (phronesis) in decision-making",
            "excess": "analysis paralysis",
            "deficiency": "impulsivity",
            "golden_mean": "informed deliberation",
        },
        "honesty": {
            "description": "Truthfulness and transparency",
            "excess": "brutal candor",
            "deficiency": "deception",
            "golden_mean": "tactful truth",
        },
        "vigilance": {
            "description": "Appropriate watchfulness",
            "excess": "paranoia",
            "deficiency": "negligence",
            "golden_mean": "prudent monitoring",
        },
    }

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize virtue ethics assessor.

        Args:
            config: Configuration with virtue weights
        """
        super().__init__(config)

        # Virtue weights (importance in cybersecurity context)
        self.virtue_weights = (
            config.get(
                "virtue_weights",
                {
                    "courage": 0.20,
                    "temperance": 0.20,
                    "justice": 0.20,
                    "wisdom": 0.25,
                    "honesty": 0.10,
                    "vigilance": 0.05,
                },
            )
            if config
            else {
                "courage": 0.20,
                "temperance": 0.20,
                "justice": 0.20,
                "wisdom": 0.25,
                "honesty": 0.10,
                "vigilance": 0.05,
            }
        )

        # Approval threshold (weighted average virtue score)
        self.approval_threshold = (
            config.get("approval_threshold", 0.70) if config else 0.70
        )

    def get_framework_principles(self) -> List[str]:
        """Get virtue ethics principles.

        Returns:
            List of core virtue ethics principles
        """
        return [
            "Golden Mean: Virtue lies between excess and deficiency",
            "Phronesis: Apply practical wisdom to each situation",
            "Eudaimonia: Act to promote flourishing of all",
            "Character Over Rules: Focus on what a virtuous person would do",
            "Context Sensitivity: Virtues manifest differently in different situations",
        ]

    async def evaluate(self, action_context: ActionContext) -> EthicalFrameworkResult:
        """Evaluate action using virtue ethics.

        Args:
            action_context: Context about the action

        Returns:
            EthicalFrameworkResult with virtue ethics verdict
        """
        start_time = time.time()
        reasoning_steps = []
        metadata = {}

        reasoning_steps.append("Assessing action against cardinal virtues...")

        # Assess each virtue
        virtue_scores = {}
        for virtue_name, virtue_def in self.CARDINAL_VIRTUES.items():
            score = self._assess_virtue(virtue_name, virtue_def, action_context)
            virtue_scores[virtue_name] = score
            reasoning_steps.append(
                f"  {virtue_name.capitalize()}: {score:.2f} ({virtue_def['golden_mean']})"
            )

        metadata["virtues_assessed"] = virtue_scores

        # Calculate weighted average
        weighted_score = sum(
            virtue_scores[virtue] * self.virtue_weights[virtue]
            for virtue in virtue_scores
        )

        metadata["character_alignment"] = weighted_score
        reasoning_steps.append(
            f"Weighted virtue score: {weighted_score:.3f} (threshold: {self.approval_threshold})"
        )

        # Golden mean analysis
        reasoning_steps.append("Analyzing golden mean (balance between extremes)...")
        golden_mean_analysis = self._analyze_golden_mean(action_context, virtue_scores)
        metadata["golden_mean_analysis"] = golden_mean_analysis

        if golden_mean_analysis["extremes_detected"]:
            reasoning_steps.append(
                f"  ⚠️  Extremes detected: {', '.join(golden_mean_analysis['extremes'])}"
            )
        else:
            reasoning_steps.append("  ✓ Action balanced, no extremes detected")

        # Phronesis (practical wisdom) check
        reasoning_steps.append("Evaluating phronesis (practical wisdom)...")
        phronesis_score = self._assess_phronesis(action_context)
        metadata["phronesis_score"] = phronesis_score
        reasoning_steps.append(f"  Practical wisdom score: {phronesis_score:.3f}")

        # Adjust final score by phronesis
        final_score = weighted_score * phronesis_score
        metadata["final_virtue_score"] = final_score

        # Decision
        approved = final_score >= self.approval_threshold
        confidence = min(
            abs(final_score - 0.5) * 2, 1.0
        )  # Confidence based on distance from neutral

        if approved:
            explanation = f"Action aligns with virtuous character (score: {final_score:.3f} ≥ {self.approval_threshold})"
            verdict = EthicalVerdict.APPROVED
            reasoning_steps.append(f"✅ {explanation}")
        else:
            explanation = f"Action shows vice or imbalance (score: {final_score:.3f} < {self.approval_threshold})"
            verdict = EthicalVerdict.REJECTED
            reasoning_steps.append(f"❌ {explanation}")

        latency_ms = int((time.time() - start_time) * 1000)

        return EthicalFrameworkResult(
            framework_name="virtue_ethics",
            approved=approved,
            confidence=confidence,
            veto=False,  # Virtue ethics does not veto
            explanation=explanation,
            reasoning_steps=reasoning_steps,
            verdict=verdict,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    def _assess_virtue(
        self,
        virtue_name: str,
        virtue_def: Dict[str, str],
        action_context: ActionContext,
    ) -> float:
        """Assess how well action exemplifies a specific virtue.

        Args:
            virtue_name: Name of the virtue
            virtue_def: Virtue definition with excess/deficiency/golden_mean
            action_context: Action context

        Returns:
            Virtue score (0.0 to 1.0, where 1.0 is perfect golden mean)
        """
        action_desc = action_context.action_description.lower()
        action_type = action_context.action_type

        if virtue_name == "courage":
            # Courage: Facing threats boldly but not recklessly
            if action_context.threat_data:
                threat_severity = action_context.threat_data.get("severity", 0.5)

                # Check for excess (recklessness)
                if action_type == "offensive_action" and threat_severity < 0.6:
                    return 0.3  # Reckless (responding disproportionately)

                # Check for deficiency (cowardice)
                if action_type == "do_nothing" and threat_severity > 0.8:
                    return 0.2  # Cowardly (failing to act on clear threat)

                # Golden mean: proportionate response
                if 0.6 <= threat_severity <= 0.9:
                    return 0.9  # Courageous

            return 0.7  # Neutral/moderate courage

        elif virtue_name == "temperance":
            # Temperance: Moderation in response
            if action_context.impact_assessment:
                disruption = action_context.impact_assessment.get(
                    "disruption_level", 0.0
                )

                # Check for excess (passivity)
                if (
                    disruption < 0.1
                    and action_context.threat_data
                    and action_context.threat_data.get("severity", 0) > 0.7
                ):
                    return 0.4  # Too passive given threat severity

                # Check for deficiency (aggression)
                if disruption > 0.7:
                    return 0.3  # Too aggressive

                # Golden mean: proportionate disruption
                if 0.2 <= disruption <= 0.5:
                    return 0.9  # Temperate

            return 0.7  # Neutral

        elif virtue_name == "justice":
            # Justice: Fair treatment of all stakeholders
            stakeholder_count = 0

            if action_context.threat_data:
                stakeholder_count += 1  # Considers protected users
            if action_context.target_info:
                stakeholder_count += 1  # Considers target
            if action_context.impact_assessment:
                stakeholder_count += 1  # Considers impacted users

            if stakeholder_count >= 3:
                return 0.9  # Just (considers all parties)
            elif stakeholder_count == 2:
                return 0.7  # Partial justice
            else:
                return 0.4  # Unjust (narrow focus)

        elif virtue_name == "wisdom":
            # Wisdom: Practical wisdom (phronesis)
            deliberation_indicators = 0

            if action_context.alternatives:
                deliberation_indicators += 1  # Considered alternatives

            if (
                action_context.threat_data
                and action_context.threat_data.get("confidence", 0) > 0.8
            ):
                deliberation_indicators += 1  # High confidence (well-informed)

            if action_context.operator_context:
                deliberation_indicators += 1  # Human judgment involved

            if action_context.urgency == "low":
                deliberation_indicators += 1  # Time for deliberation

            return min(0.5 + (deliberation_indicators * 0.15), 1.0)

        elif virtue_name == "honesty":
            # Honesty: Truthfulness and transparency
            if "covert" in action_desc or "hidden" in action_desc:
                return 0.4  # Lacks transparency

            if action_type == "threat_investigation":
                return 0.9  # Truth-seeking

            return 0.7  # Neutral

        elif virtue_name == "vigilance":
            # Vigilance: Appropriate watchfulness
            if action_type in ["monitoring", "threat_detection"]:
                if "excessive" in action_desc or "invasive" in action_desc:
                    return 0.3  # Paranoid (excess)
                else:
                    return 0.9  # Vigilant (golden mean)

            if action_context.threat_data and action_context.threat_data.get(
                "missed_indicators"
            ):
                return 0.4  # Negligent (deficiency)

            return 0.7  # Neutral

        return 0.7  # Default neutral score

    def _analyze_golden_mean(
        self, action_context: ActionContext, virtue_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze if action hits the golden mean or tends toward extremes.

        Args:
            action_context: Action context
            virtue_scores: Dict of virtue scores

        Returns:
            Dict with extremes_detected and list of extremes
        """
        extremes = []

        # Check each virtue for extreme deviation
        for virtue_name, score in virtue_scores.items():
            if score < 0.4:  # Deficiency
                virtue_def = self.CARDINAL_VIRTUES[virtue_name]
                extremes.append(f"{virtue_name} → {virtue_def['deficiency']}")
            elif score < 0.45 and virtue_name in ["courage", "temperance", "justice"]:
                # Critical virtues need higher scores
                virtue_def = self.CARDINAL_VIRTUES[virtue_name]
                extremes.append(f"{virtue_name} → bordering {virtue_def['deficiency']}")

        # Check action description for extreme language
        action_lower = action_context.action_description.lower()
        extreme_words = [
            "extreme",
            "maximum",
            "aggressive",
            "passive",
            "excessive",
            "minimal",
        ]

        if any(word in action_lower for word in extreme_words):
            extremes.append("extreme language detected in action description")

        return {
            "extremes_detected": len(extremes) > 0,
            "extremes": extremes,
            "balanced": len(extremes) == 0,
        }

    def _assess_phronesis(self, action_context: ActionContext) -> float:
        """Assess practical wisdom (phronesis) in decision-making.

        Phronesis is the ability to choose the right action at the right time
        in the right way for the right reasons.

        Args:
            action_context: Action context

        Returns:
            Phronesis score (0.0 to 1.0)
        """
        phronesis = 0.5  # Start at neutral

        # Right action?
        if action_context.threat_data:
            threat_severity = action_context.threat_data.get("severity", 0.5)
            confidence = action_context.threat_data.get("confidence", 0.5)

            # Is response proportionate?
            if (
                action_context.action_type == "offensive_action"
                and threat_severity > 0.7
                and confidence > 0.8
            ):
                phronesis += 0.2  # Right action for serious threat
            elif action_context.action_type == "monitoring" and threat_severity < 0.5:
                phronesis += 0.15  # Right action for low threat

        # Right time?
        if action_context.urgency == "critical":
            phronesis += 0.1  # Acting urgently when needed
        elif action_context.urgency == "low" and action_context.operator_context:
            phronesis += 0.1  # Taking time to deliberate when possible

        # Right way?
        if action_context.alternatives and len(action_context.alternatives) > 1:
            phronesis += 0.15  # Considered alternatives (deliberative)

        # Right reasons?
        if action_context.threat_data and action_context.threat_data.get(
            "justification"
        ):
            phronesis += 0.1  # Clear justification

        return min(phronesis, 1.0)
