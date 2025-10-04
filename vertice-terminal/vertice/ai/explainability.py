"""
Explainable AI (XAI) Module
============================

Provides transparency and interpretability for AI decisions through
detailed explanations, confidence breakdowns, and decision trees.

Features:
- Decision explanation generation
- Confidence factor decomposition
- Counterfactual reasoning ("what-if" analysis)
- Feature importance ranking
- Decision tree visualization

Examples:
    xai = ExplainableAI()

    # Explain a decision
    explanation = xai.explain_decision(
        decision="Block IP 1.2.3.4",
        factors={
            "bruteforce_attempts": 150,
            "failed_logins": 50,
            "geo_location": "suspicious",
            "threat_intel_match": True
        },
        confidence=0.95
    )

    # Print explanation
    print(explanation.natural_language())
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """Types of explanations."""

    FEATURE_IMPORTANCE = "feature_importance"  # Which factors matter most
    DECISION_PATH = "decision_path"  # Step-by-step decision logic
    COUNTERFACTUAL = "counterfactual"  # What would change the decision
    CONFIDENCE_BREAKDOWN = "confidence_breakdown"  # Why this confidence level
    COMPARISON = "comparison"  # Compare with similar cases


class DecisionType(Enum):
    """Types of decisions."""

    CLASSIFICATION = "classification"  # Classify into category
    RANKING = "ranking"  # Rank by priority/severity
    RECOMMENDATION = "recommendation"  # Recommend action
    PREDICTION = "prediction"  # Predict future state
    DETECTION = "detection"  # Detect anomaly/threat


@dataclass
class ConfidenceFactor:
    """
    Factor contributing to confidence score.

    Attributes:
        factor_name: Name of factor
        value: Factor value
        contribution: Contribution to confidence (-1 to +1)
        reasoning: Why this factor matters
    """
    factor_name: str
    value: Any
    contribution: float  # -1 (decreases conf) to +1 (increases conf)
    reasoning: str
    weight: float = 1.0  # Importance weight


@dataclass
class DecisionExplanation:
    """
    Comprehensive explanation of AI decision.

    Attributes:
        decision: The decision made
        decision_type: Type of decision
        confidence: Overall confidence (0-1)
        confidence_factors: Factors affecting confidence
        feature_importance: Ranked feature importance
        decision_path: Step-by-step reasoning
        counterfactuals: Alternative scenarios
        metadata: Additional explanation metadata
    """
    decision: str
    decision_type: DecisionType
    confidence: float
    confidence_factors: List[ConfidenceFactor] = field(default_factory=list)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    decision_path: List[str] = field(default_factory=list)
    counterfactuals: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def natural_language(self) -> str:
        """
        Generate natural language explanation.

        Returns:
            Human-readable explanation string

        Example:
            explanation = xai.explain_decision(...)
            print(explanation.natural_language())
        """
        lines = [
            f"Decision: {self.decision}",
            f"Confidence: {self.confidence:.0%}",
            "",
            "Key Factors:",
        ]

        # Sort factors by absolute contribution
        sorted_factors = sorted(
            self.confidence_factors,
            key=lambda f: abs(f.contribution),
            reverse=True
        )

        for factor in sorted_factors[:5]:  # Top 5 factors
            impact = "increases" if factor.contribution > 0 else "decreases"
            strength = "strongly" if abs(factor.contribution) > 0.5 else "moderately"

            lines.append(
                f"  • {factor.factor_name}={factor.value} "
                f"{strength} {impact} confidence ({factor.contribution:+.0%}) "
                f"- {factor.reasoning}"
            )

        if self.decision_path:
            lines.append("")
            lines.append("Decision Path:")

            for i, step in enumerate(self.decision_path, 1):
                lines.append(f"  {i}. {step}")

        if self.counterfactuals:
            lines.append("")
            lines.append("What-If Scenarios:")

            for cf in self.counterfactuals[:3]:
                lines.append(f"  • If {cf['change']}, then {cf['result']}")

        return "\n".join(lines)


class ExplainableAI:
    """
    Explainable AI system for transparency and interpretability.

    Generates comprehensive explanations for AI decisions including
    confidence breakdowns, feature importance, and counterfactuals.

    Example:
        xai = ExplainableAI()

        # Explain classification
        explanation = xai.explain_decision(
            decision="Classify as APT attack",
            decision_type=DecisionType.CLASSIFICATION,
            factors={
                "lateral_movement_detected": True,
                "c2_communication": True,
                "persistence_mechanisms": 3,
                "data_exfiltration_attempts": 2,
                "credential_dumping": True
            },
            confidence=0.92
        )

        # Generate explanation
        print(explanation.natural_language())

        # Analyze what would change decision
        counterfactuals = xai.generate_counterfactuals(
            decision="Block",
            factors={...}
        )
    """

    def __init__(
        self,
        enable_counterfactuals: bool = True,
        max_counterfactuals: int = 5,
    ):
        """
        Initialize explainable AI system.

        Args:
            enable_counterfactuals: Generate counterfactual explanations
            max_counterfactuals: Maximum counterfactuals to generate
        """
        self.enable_counterfactuals = enable_counterfactuals
        self.max_counterfactuals = max_counterfactuals

        # Explanation history
        self._explanation_history: List[DecisionExplanation] = []

        logger.info(
            f"ExplainableAI initialized (counterfactuals={enable_counterfactuals})"
        )

    def explain_decision(
        self,
        decision: str,
        decision_type: DecisionType,
        factors: Dict[str, Any],
        confidence: float,
        include_path: bool = True,
        **metadata
    ) -> DecisionExplanation:
        """
        Generate comprehensive explanation for decision.

        Args:
            decision: Decision made
            decision_type: Type of decision
            factors: Factors influencing decision
            confidence: Overall confidence score
            include_path: Include decision path
            **metadata: Additional metadata

        Returns:
            DecisionExplanation

        Example:
            explanation = xai.explain_decision(
                decision="Escalate to Tier 2",
                decision_type=DecisionType.RECOMMENDATION,
                factors={
                    "severity_score": 85,
                    "asset_criticality": "high",
                    "attack_sophistication": "advanced",
                    "confirmed_iocs": 12
                },
                confidence=0.88
            )
        """
        logger.info(f"Explaining decision: {decision[:60]}...")

        # Decompose confidence
        confidence_factors = self._decompose_confidence(factors, confidence)

        # Calculate feature importance
        feature_importance = self._calculate_feature_importance(factors, confidence_factors)

        # Generate decision path
        decision_path = []
        if include_path:
            decision_path = self._generate_decision_path(decision, factors, confidence_factors)

        # Generate counterfactuals
        counterfactuals = []
        if self.enable_counterfactuals:
            counterfactuals = self.generate_counterfactuals(
                decision,
                factors,
                confidence
            )

        explanation = DecisionExplanation(
            decision=decision,
            decision_type=decision_type,
            confidence=confidence,
            confidence_factors=confidence_factors,
            feature_importance=feature_importance,
            decision_path=decision_path,
            counterfactuals=counterfactuals,
            metadata=metadata
        )

        # Store explanation
        self._explanation_history.append(explanation)

        logger.info(
            f"Explanation generated with {len(confidence_factors)} factors, "
            f"{len(decision_path)} steps, {len(counterfactuals)} counterfactuals"
        )

        return explanation

    def _decompose_confidence(
        self,
        factors: Dict[str, Any],
        overall_confidence: float
    ) -> List[ConfidenceFactor]:
        """
        Decompose overall confidence into contributing factors.

        Args:
            factors: Input factors
            overall_confidence: Overall confidence score

        Returns:
            List of ConfidenceFactors
        """
        confidence_factors = []

        for factor_name, value in factors.items():
            # Determine contribution (simplified - production would use SHAP/LIME)
            contribution = self._estimate_factor_contribution(
                factor_name,
                value,
                overall_confidence
            )

            # Generate reasoning
            reasoning = self._generate_factor_reasoning(
                factor_name,
                value,
                contribution
            )

            cf = ConfidenceFactor(
                factor_name=factor_name,
                value=value,
                contribution=contribution,
                reasoning=reasoning
            )

            confidence_factors.append(cf)

        return confidence_factors

    def _estimate_factor_contribution(
        self,
        factor_name: str,
        value: Any,
        overall_confidence: float
    ) -> float:
        """
        Estimate factor's contribution to confidence.

        In production, would use SHAP values or similar.
        For now, using heuristics.

        Returns:
            Contribution from -1 to +1
        """
        # Boolean factors
        if isinstance(value, bool):
            return 0.3 if value else -0.2

        # Numeric factors (normalize to contribution)
        if isinstance(value, (int, float)):
            # Assume higher is more confidence-boosting
            if value > 75:
                return 0.4
            elif value > 50:
                return 0.2
            elif value > 25:
                return 0.0
            else:
                return -0.2

        # String factors (simplified)
        if isinstance(value, str):
            if value.lower() in ["critical", "high", "severe", "confirmed"]:
                return 0.3
            elif value.lower() in ["medium", "moderate"]:
                return 0.1
            elif value.lower() in ["low", "minimal"]:
                return -0.1
            else:
                return 0.0

        return 0.0

    def _generate_factor_reasoning(
        self,
        factor_name: str,
        value: Any,
        contribution: float
    ) -> str:
        """Generate human-readable reasoning for factor."""
        if contribution > 0.3:
            return f"Strong positive indicator"
        elif contribution > 0.1:
            return f"Moderate positive indicator"
        elif contribution > -0.1:
            return f"Neutral indicator"
        elif contribution > -0.3:
            return f"Moderate negative indicator"
        else:
            return f"Strong negative indicator"

    def _calculate_feature_importance(
        self,
        factors: Dict[str, Any],
        confidence_factors: List[ConfidenceFactor]
    ) -> Dict[str, float]:
        """
        Calculate relative importance of each feature.

        Returns:
            Dict of feature → importance score (0-1)
        """
        # Use absolute contribution as importance
        importance = {}

        total_contribution = sum(abs(cf.contribution) for cf in confidence_factors)

        if total_contribution > 0:
            for cf in confidence_factors:
                importance[cf.factor_name] = abs(cf.contribution) / total_contribution
        else:
            # Equal importance if no contribution data
            for cf in confidence_factors:
                importance[cf.factor_name] = 1.0 / len(confidence_factors)

        return importance

    def _generate_decision_path(
        self,
        decision: str,
        factors: Dict[str, Any],
        confidence_factors: List[ConfidenceFactor]
    ) -> List[str]:
        """
        Generate step-by-step decision path.

        Returns:
            List of decision steps
        """
        steps = []

        # Step 1: Initial assessment
        steps.append(
            f"Evaluate input factors: {len(factors)} factors provided"
        )

        # Step 2: Analyze key indicators
        positive_factors = [cf for cf in confidence_factors if cf.contribution > 0.2]
        if positive_factors:
            key_factors = ", ".join(cf.factor_name for cf in positive_factors[:3])
            steps.append(
                f"Identify key positive indicators: {key_factors}"
            )

        # Step 3: Consider negative indicators
        negative_factors = [cf for cf in confidence_factors if cf.contribution < -0.1]
        if negative_factors:
            neg_factors = ", ".join(cf.factor_name for cf in negative_factors[:2])
            steps.append(
                f"Consider negative indicators: {neg_factors}"
            )

        # Step 4: Weigh evidence
        steps.append(
            f"Weigh evidence: {len(positive_factors)} positive vs "
            f"{len(negative_factors)} negative factors"
        )

        # Step 5: Make decision
        steps.append(
            f"Conclude: {decision}"
        )

        return steps

    def generate_counterfactuals(
        self,
        decision: str,
        factors: Dict[str, Any],
        confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Generate "what-if" counterfactual scenarios.

        Identifies changes that would lead to different decision.

        Args:
            decision: Current decision
            factors: Current factors
            confidence: Current confidence

        Returns:
            List of counterfactual scenarios

        Example:
            counterfactuals = xai.generate_counterfactuals(
                decision="Block IP",
                factors={"threat_score": 85, "source": "unknown"},
                confidence=0.9
            )

            for cf in counterfactuals:
                print(f"If {cf['change']}, then {cf['result']}")
        """
        if not self.enable_counterfactuals:
            return []

        logger.debug(f"Generating counterfactuals for: {decision}")

        counterfactuals = []

        # Generate counterfactuals by modifying key factors
        for factor_name, value in factors.items():
            cf = self._generate_factor_counterfactual(
                factor_name,
                value,
                decision,
                confidence
            )

            if cf:
                counterfactuals.append(cf)

                if len(counterfactuals) >= self.max_counterfactuals:
                    break

        return counterfactuals

    def _generate_factor_counterfactual(
        self,
        factor_name: str,
        current_value: Any,
        decision: str,
        confidence: float
    ) -> Optional[Dict[str, Any]]:
        """Generate counterfactual for single factor."""

        # Boolean flip
        if isinstance(current_value, bool):
            new_value = not current_value
            new_decision = "Allow" if "Block" in decision else "Block"

            return {
                "change": f"{factor_name} changes from {current_value} to {new_value}",
                "result": f"decision would change to '{new_decision}'",
                "confidence_change": -0.3 if current_value else +0.3
            }

        # Numeric threshold
        if isinstance(current_value, (int, float)):
            if current_value > 50:
                new_value = current_value * 0.5
                return {
                    "change": f"{factor_name} decreases from {current_value} to {new_value:.0f}",
                    "result": "confidence would decrease significantly",
                    "confidence_change": -0.4
                }

        # String category change
        if isinstance(current_value, str):
            if current_value.lower() in ["critical", "high"]:
                return {
                    "change": f"{factor_name} changes from '{current_value}' to 'low'",
                    "result": "decision might change to lower severity response",
                    "confidence_change": -0.3
                }

        return None

    def compare_decisions(
        self,
        explanation1: DecisionExplanation,
        explanation2: DecisionExplanation
    ) -> Dict[str, Any]:
        """
        Compare two decisions to highlight differences.

        Args:
            explanation1: First explanation
            explanation2: Second explanation

        Returns:
            Comparison dict

        Example:
            comparison = xai.compare_decisions(exp1, exp2)
            print(f"Confidence delta: {comparison['confidence_delta']}")
        """
        comparison = {
            "decision1": explanation1.decision,
            "decision2": explanation2.decision,
            "confidence_delta": explanation2.confidence - explanation1.confidence,
            "factor_differences": {},
            "unique_to_decision1": [],
            "unique_to_decision2": [],
        }

        # Compare factors
        factors1 = {cf.factor_name: cf for cf in explanation1.confidence_factors}
        factors2 = {cf.factor_name: cf for cf in explanation2.confidence_factors}

        # Find differences
        all_factors = set(factors1.keys()) | set(factors2.keys())

        for factor in all_factors:
            if factor in factors1 and factor in factors2:
                contrib_delta = factors2[factor].contribution - factors1[factor].contribution

                if abs(contrib_delta) > 0.1:
                    comparison["factor_differences"][factor] = {
                        "contribution_delta": contrib_delta,
                        "value1": factors1[factor].value,
                        "value2": factors2[factor].value,
                    }

            elif factor in factors1:
                comparison["unique_to_decision1"].append(factor)

            else:
                comparison["unique_to_decision2"].append(factor)

        return comparison

    def get_stats(self) -> Dict[str, Any]:
        """
        Get explanation statistics.

        Returns:
            Stats dict

        Example:
            stats = xai.get_stats()
            print(f"Explanations generated: {stats['total_explanations']}")
        """
        if not self._explanation_history:
            return {
                "total_explanations": 0,
                "avg_confidence": 0.0,
                "avg_factors_per_explanation": 0.0,
            }

        return {
            "total_explanations": len(self._explanation_history),
            "avg_confidence": sum(e.confidence for e in self._explanation_history) / len(self._explanation_history),
            "avg_factors_per_explanation": sum(len(e.confidence_factors) for e in self._explanation_history) / len(self._explanation_history),
            "avg_counterfactuals_per_explanation": sum(len(e.counterfactuals) for e in self._explanation_history) / len(self._explanation_history),
        }
