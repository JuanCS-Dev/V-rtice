"""Ethical Integration Engine.

Aggregates results from all 4 ethical frameworks (Kantian, Consequentialist,
Virtue Ethics, Principialism) and produces a final integrated ethical decision.

Handles:
1. Multi-framework aggregation with configurable weights
2. Conflict resolution when frameworks disagree
3. Veto system (Kantian framework has veto power)
4. Confidence scoring
5. Explanation generation
6. Performance optimization (parallel execution, caching)
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

from .base import (
    ActionContext,
    EthicalCache,
    EthicalFramework,
    EthicalFrameworkResult,
    EthicalVerdict,
    VetoException,
)
from .consequentialist_engine import ConsequentialistEngine
from .kantian_checker import KantianImperativeChecker
from .principialism import PrinciplismFramework
from .virtue_ethics import VirtueEthicsAssessment


@dataclass
class IntegratedEthicalDecision:
    """Final integrated ethical decision from all frameworks.

    Attributes:
        final_decision: APPROVED, REJECTED, or ESCALATED_HITL
        final_confidence: Overall confidence (0.0 to 1.0)
        explanation: Human-readable explanation
        framework_results: Results from each framework
        aggregation_method: How frameworks were combined
        veto_applied: Whether Kantian veto was used
        framework_agreement_rate: % of frameworks that agree
        total_latency_ms: Total evaluation time
        metadata: Additional decision data
    """

    final_decision: str
    final_confidence: float
    explanation: str
    framework_results: dict[str, EthicalFrameworkResult]
    aggregation_method: str
    veto_applied: bool
    framework_agreement_rate: float
    total_latency_ms: int
    metadata: dict[str, Any]


class EthicalIntegrationEngine:
    """Integrates multiple ethical frameworks into unified decisions."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize integration engine.

        Args:
            config: Configuration dict with framework weights, thresholds, etc.
        """
        self.config = config or {}

        # Framework weights (how much each framework contributes to final decision)
        self.framework_weights = self.config.get(
            "framework_weights",
            {
                "kantian_deontology": 0.30,  # Highest weight due to veto power
                "consequentialism": 0.25,
                "virtue_ethics": 0.20,
                "principialism": 0.25,
            },
        )

        # Veto settings
        self.veto_frameworks = self.config.get("veto_frameworks", ["kantian_deontology"])
        self.veto_enabled = self.config.get("veto_enabled", True)

        # Decision thresholds
        self.approval_threshold = self.config.get("approval_threshold", 0.70)
        self.rejection_threshold = self.config.get("rejection_threshold", 0.40)
        # Between 0.40 and 0.70 -> ESCALATE to HITL

        # HITL escalation settings
        self.hitl_escalation_enabled = self.config.get("hitl_escalation_enabled", True)
        self.hitl_threshold_low = 0.40
        self.hitl_threshold_high = 0.70

        # Initialize frameworks
        self.frameworks: dict[str, EthicalFramework] = {
            "kantian_deontology": KantianImperativeChecker(self.config.get("kantian", {})),
            "consequentialism": ConsequentialistEngine(self.config.get("consequentialist", {})),
            "virtue_ethics": VirtueEthicsAssessment(self.config.get("virtue", {})),
            "principialism": PrinciplismFramework(self.config.get("principialism", {})),
        }

        # Cache for performance
        self.cache = EthicalCache(
            max_size=self.config.get("cache_size", 10000),
            ttl_seconds=self.config.get("cache_ttl", 3600),
        )

    async def evaluate(self, action_context: ActionContext) -> IntegratedEthicalDecision:
        """Evaluate action using all ethical frameworks and integrate results.

        Args:
            action_context: Context about the action to evaluate

        Returns:
            IntegratedEthicalDecision with final verdict
        """
        start_time = time.time()
        metadata = {"reasoning_steps": []}

        metadata["reasoning_steps"].append("🧠 Starting integrated ethical evaluation...")

        # Step 1: Run all frameworks in parallel for performance
        metadata["reasoning_steps"].append("Running 4 ethical frameworks in parallel...")

        try:
            framework_results = await self._run_frameworks_parallel(action_context)
        except VetoException as e:
            # Kantian veto occurred
            metadata["reasoning_steps"].append(f"❌ VETO: {str(e)}")

            total_latency_ms = int((time.time() - start_time) * 1000)

            return IntegratedEthicalDecision(
                final_decision="REJECTED",
                final_confidence=1.0,  # Veto is absolute
                explanation=f"Kantian veto: {e.reason}",
                framework_results={},  # May not have all results if veto occurred early
                aggregation_method="veto",
                veto_applied=True,
                framework_agreement_rate=0.0,
                total_latency_ms=total_latency_ms,
                metadata=metadata,
            )

        metadata["reasoning_steps"].append("✓ All frameworks completed")

        # Step 2: Check for veto (if not already caught)
        if self.veto_enabled:
            for framework_name in self.veto_frameworks:
                if framework_name in framework_results:
                    result = framework_results[framework_name]
                    if result.veto and not result.approved:
                        metadata["reasoning_steps"].append(f"❌ VETO by {framework_name}: {result.explanation}")

                        total_latency_ms = int((time.time() - start_time) * 1000)

                        return IntegratedEthicalDecision(
                            final_decision="REJECTED",
                            final_confidence=1.0,
                            explanation=f"{framework_name} veto: {result.explanation}",
                            framework_results=framework_results,
                            aggregation_method="veto",
                            veto_applied=True,
                            framework_agreement_rate=self._calculate_agreement_rate(framework_results),
                            total_latency_ms=total_latency_ms,
                            metadata=metadata,
                        )

        metadata["reasoning_steps"].append("✓ No veto applied")

        # Step 3: Calculate framework agreement
        agreement_rate = self._calculate_agreement_rate(framework_results)
        metadata["framework_agreement_rate"] = agreement_rate
        metadata["reasoning_steps"].append(f"Framework agreement: {agreement_rate:.1%}")

        # Step 4: Aggregate framework results
        metadata["reasoning_steps"].append("Aggregating framework results...")
        aggregated_score = self._aggregate_frameworks(framework_results)
        metadata["aggregated_score"] = aggregated_score
        metadata["reasoning_steps"].append(f"Aggregated score: {aggregated_score:.3f}")

        # Step 5: Make final decision
        final_decision, final_confidence, aggregation_method = self._make_final_decision(
            aggregated_score, agreement_rate, framework_results
        )

        # Step 6: Generate explanation
        explanation = self._generate_explanation(final_decision, aggregated_score, agreement_rate, framework_results)

        metadata["reasoning_steps"].append(f"Final decision: {final_decision}")
        metadata["reasoning_steps"].append(f"Explanation: {explanation}")

        total_latency_ms = int((time.time() - start_time) * 1000)
        metadata["performance"] = {
            "total_latency_ms": total_latency_ms,
            "kantian_latency_ms": framework_results["kantian_deontology"].latency_ms,
            "consequentialist_latency_ms": framework_results["consequentialism"].latency_ms,
            "virtue_ethics_latency_ms": framework_results["virtue_ethics"].latency_ms,
            "principialism_latency_ms": framework_results["principialism"].latency_ms,
        }

        return IntegratedEthicalDecision(
            final_decision=final_decision,
            final_confidence=final_confidence,
            explanation=explanation,
            framework_results=framework_results,
            aggregation_method=aggregation_method,
            veto_applied=False,
            framework_agreement_rate=agreement_rate,
            total_latency_ms=total_latency_ms,
            metadata=metadata,
        )

    async def _run_frameworks_parallel(self, action_context: ActionContext) -> dict[str, EthicalFrameworkResult]:
        """Run all frameworks in parallel for performance.

        Args:
            action_context: Action context

        Returns:
            Dict mapping framework name to result

        Raises:
            VetoException: If Kantian framework vetoes
        """
        # FIXED: Actually use cache
        framework_results = {}

        # Check cache for each framework
        for name, framework in self.frameworks.items():
            cache_key = self.cache.generate_key(action_context, name)
            cached_result = self.cache.get(cache_key)

            if cached_result:
                logger.debug(f"Cache HIT for framework {name}")
                framework_results[name] = cached_result
            else:
                logger.debug(f"Cache MISS for framework {name}")

        # Run uncached frameworks concurrently
        uncached_frameworks = {
            name: framework for name, framework in self.frameworks.items() if name not in framework_results
        }

        if not uncached_frameworks:
            logger.debug("All frameworks served from cache")
            return framework_results

        # Run uncached frameworks in parallel
        tasks = {name: framework.evaluate(action_context) for name, framework in uncached_frameworks.items()}

        # Wait for all to complete
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Map results back to framework names and cache them
        for (name, _), result in zip(tasks.items(), results, strict=False):
            if isinstance(result, VetoException):
                raise result  # Re-raise veto
            if isinstance(result, Exception):
                # Log error but continue (framework failure shouldn't crash entire system)
                logger.error(f"Framework {name} failed: {str(result)}", exc_info=True)
                # Create a default negative result
                framework_results[name] = EthicalFrameworkResult(
                    framework_name=name,
                    approved=False,
                    confidence=0.0,
                    veto=False,
                    explanation=f"Framework error: {str(result)}",
                    reasoning_steps=[f"Error: {str(result)}"],
                    verdict=EthicalVerdict.REJECTED,
                    latency_ms=0,
                    metadata={"error": str(result)},
                )
            else:
                framework_results[name] = result
                # FIXED: Cache the result
                cache_key = self.cache.generate_key(action_context, name)
                self.cache.set(cache_key, result)
                logger.debug(f"Cached result for framework {name}")

        return framework_results

    def _calculate_agreement_rate(self, framework_results: dict[str, EthicalFrameworkResult]) -> float:
        """Calculate how many frameworks agree on the decision.

        Args:
            framework_results: Results from all frameworks

        Returns:
            Agreement rate (0.0 to 1.0)
        """
        if not framework_results:
            return 0.0

        # Count approvals
        approvals = sum(1 for r in framework_results.values() if r.approved)
        total = len(framework_results)

        # Agreement is either all approve or all reject
        agreement_on_approve = approvals / total
        agreement_on_reject = (total - approvals) / total

        return max(agreement_on_approve, agreement_on_reject)

    def _aggregate_frameworks(self, framework_results: dict[str, EthicalFrameworkResult]) -> float:
        """Aggregate framework results using weighted average.

        Args:
            framework_results: Results from all frameworks

        Returns:
            Aggregated score (0.0 to 1.0)

        Logic:
            - Approved with confidence 0.9 → contributes +0.9 to weighted sum
            - Rejected with confidence 0.9 → contributes -0.9 to weighted sum
            - Final score normalized to [0.0, 1.0] range
        """
        weighted_sum = 0.0
        total_weight = 0.0

        for name, result in framework_results.items():
            weight = self.framework_weights.get(name, 0.25)

            # FIXED: Proper score calculation
            # Approved: positive contribution (confidence * +1)
            # Rejected: negative contribution (confidence * -1)
            if result.approved:
                contribution = result.confidence
            else:
                contribution = -result.confidence

            weighted_sum += contribution * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        # Normalize from [-1.0, 1.0] to [0.0, 1.0]
        # -1.0 (unanimous rejection) → 0.0
        #  0.0 (neutral) → 0.5
        # +1.0 (unanimous approval) → 1.0
        normalized_score = (weighted_sum + total_weight) / (2 * total_weight)

        return max(0.0, min(1.0, normalized_score))

    def _make_final_decision(
        self,
        aggregated_score: float,
        agreement_rate: float,
        framework_results: dict[str, EthicalFrameworkResult],
    ) -> tuple[str, float, str]:
        """Make final decision from aggregated score and agreement rate.

        Args:
            aggregated_score: Weighted aggregate score
            agreement_rate: Framework agreement rate
            framework_results: Individual framework results

        Returns:
            Tuple of (final_decision, final_confidence, aggregation_method)
        """
        # High agreement + high score = APPROVE
        if aggregated_score >= self.approval_threshold and agreement_rate >= 0.75:
            return ("APPROVED", aggregated_score, "weighted_consensus")

        # Low agreement + moderate score = ESCALATE to HITL
        if self.hitl_threshold_low < aggregated_score < self.hitl_threshold_high:
            if agreement_rate < 0.75:
                # Frameworks disagree significantly, need human judgment
                confidence = 1.0 - agreement_rate  # Low agreement = high need for HITL
                return ("ESCALATED_HITL", confidence, "disagreement_escalation")

        # High score but low agreement = ESCALATE
        if aggregated_score >= self.approval_threshold and agreement_rate < 0.5:
            return ("ESCALATED_HITL", 0.7, "low_agreement_escalation")

        # Low score = REJECT
        if aggregated_score < self.rejection_threshold:
            confidence = 1.0 - aggregated_score  # Lower score = higher rejection confidence
            return ("REJECTED", confidence, "weighted_rejection")

        # Middle ground with high agreement
        if agreement_rate >= 0.75:
            if aggregated_score >= 0.60:
                return ("APPROVED", aggregated_score, "majority_consensus")
            return ("REJECTED", 1.0 - aggregated_score, "majority_consensus")

        # Default: escalate on ambiguity
        return ("ESCALATED_HITL", 0.5, "ambiguous_escalation")

    def _generate_explanation(
        self,
        final_decision: str,
        aggregated_score: float,
        agreement_rate: float,
        framework_results: dict[str, EthicalFrameworkResult],
    ) -> str:
        """Generate human-readable explanation for the decision.

        Args:
            final_decision: Final decision (APPROVED/REJECTED/ESCALATED_HITL)
            aggregated_score: Aggregated score
            agreement_rate: Agreement rate
            framework_results: Framework results

        Returns:
            Explanation string
        """
        # Count approvals and rejections
        approvals = [name for name, r in framework_results.items() if r.approved]
        rejections = [name for name, r in framework_results.items() if not r.approved]

        if final_decision == "APPROVED":
            explanation = (
                f"Action ethically approved (score: {aggregated_score:.2f}, agreement: {agreement_rate:.0%}). "
            )
            if approvals:
                explanation += f"Approved by: {', '.join(approvals)}. "
            if rejections:
                explanation += f"Concerns from: {', '.join(rejections)}."
        elif final_decision == "REJECTED":
            explanation = (
                f"Action ethically rejected (score: {aggregated_score:.2f}, agreement: {agreement_rate:.0%}). "
            )
            if rejections:
                explanation += f"Rejected by: {', '.join(rejections)}. "
            if approvals:
                explanation += f"Minority support from: {', '.join(approvals)}."
        else:  # ESCALATED_HITL
            explanation = (
                f"Action escalated to human review (score: {aggregated_score:.2f}, agreement: {agreement_rate:.0%}). "
            )
            if agreement_rate < 0.75:
                explanation += "Frameworks disagree significantly. "
            else:
                explanation += "Ambiguous ethical situation. "
            explanation += f"Approvals: {len(approvals)}/4, Rejections: {len(rejections)}/4. Human judgment required."

        return explanation
