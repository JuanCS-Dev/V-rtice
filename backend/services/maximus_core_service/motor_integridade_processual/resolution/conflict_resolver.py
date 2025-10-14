"""
Conflict Resolution Engine.

Resolves conflicts between ethical frameworks when they disagree.
Implements weighted aggregation, precedence rules, and escalation logic.

Lei Governante: Constituição Vértice v2.6
"""

from typing import List, Dict, Optional, Tuple
from motor_integridade_processual.models.verdict import (
    FrameworkVerdict,
    FrameworkName,
    EthicalVerdict,
    DecisionLevel,
    RejectionReason
)
from motor_integridade_processual.models.action_plan import ActionPlan


class ConflictResolver:
    """
    Resolves conflicts between framework verdicts.
    
    Strategy:
    1. Check for vetoes (Kantian has absolute veto power)
    2. Detect conflicts (frameworks disagreeing)
    3. Apply weighted aggregation
    4. Escalate if confidence too low or conflicts unresolvable
    
    Attributes:
        weights: Framework weights for aggregation
        escalation_threshold: Confidence below this triggers HITL
        conflict_threshold: Score variance above this indicates conflict
    """
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        escalation_threshold: float = 0.6,
        conflict_threshold: float = 0.3
    ):
        """
        Initialize conflict resolver.
        
        Args:
            weights: Framework weights (must sum to 1.0)
            escalation_threshold: Confidence threshold for HITL
            conflict_threshold: Score variance threshold for conflict detection
        """
        self.weights = weights or {
            FrameworkName.KANTIAN.value: 0.40,
            FrameworkName.UTILITARIAN.value: 0.30,
            FrameworkName.VIRTUE_ETHICS.value: 0.20,
            FrameworkName.PRINCIPIALISM.value: 0.10
        }
        self.escalation_threshold = escalation_threshold
        self.conflict_threshold = conflict_threshold
        
        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def resolve(
        self,
        framework_verdicts: List[FrameworkVerdict],
        plan: ActionPlan
    ) -> EthicalVerdict:
        """
        Resolve conflicts between framework verdicts.
        
        Args:
            framework_verdicts: List of verdicts from each framework
            plan: The action plan being evaluated
            
        Returns:
            Unified ethical verdict
        """
        # 1. Check for vetoes (absolute rejection)
        for verdict in framework_verdicts:
            if verdict.decision == DecisionLevel.VETO:
                return self._build_veto_verdict(verdict, framework_verdicts, plan)
        
        # 2. Detect conflicts
        has_conflict, conflict_details = self._detect_conflicts(framework_verdicts)
        
        # 3. Calculate aggregate score
        aggregate_score = self._calculate_aggregate_score(framework_verdicts)
        
        # 4. Calculate confidence
        confidence = self._calculate_confidence(framework_verdicts, has_conflict)
        
        # 5. Decide if escalation needed
        if self._should_escalate(aggregate_score, confidence, has_conflict, plan):
            return self._build_escalated_verdict(
                framework_verdicts, plan, aggregate_score, confidence, conflict_details
            )
        
        # 6. Build final verdict based on score
        return self._build_final_verdict(
            framework_verdicts, plan, aggregate_score, confidence, has_conflict
        )
    
    def _detect_conflicts(
        self, verdicts: List[FrameworkVerdict]
    ) -> Tuple[bool, List[str]]:
        """
        Detect if frameworks are in conflict.
        
        Returns:
            (has_conflict, conflict_details)
        """
        decisions = [v.decision for v in verdicts]
        scores = [v.score for v in verdicts if v.score is not None]
        
        # Check for decision conflicts
        approvals = sum(1 for d in decisions if d in [
            DecisionLevel.APPROVE, DecisionLevel.APPROVE_WITH_CONDITIONS
        ])
        rejections = sum(1 for d in decisions if d in [
            DecisionLevel.REJECT, DecisionLevel.VETO
        ])
        
        details = []
        
        # Conflict if some approve and some reject
        if approvals > 0 and rejections > 0:
            details.append(f"{approvals} frameworks approve, {rejections} reject")
        
        # Check score variance
        if len(scores) >= 2:
            variance = max(scores) - min(scores)
            if variance > self.conflict_threshold:
                details.append(f"High score variance: {variance:.2f}")
        
        has_conflict = len(details) > 0
        return has_conflict, details
    
    def _calculate_aggregate_score(self, verdicts: List[FrameworkVerdict]) -> float:
        """
        Calculate weighted aggregate score.
        
        Args:
            verdicts: Framework verdicts
            
        Returns:
            Aggregate score [0.0, 1.0]
        """
        total_score = 0.0
        total_weight = 0.0
        
        for verdict in verdicts:
            if verdict.score is not None:
                weight = self.weights.get(verdict.framework_name.value, 0.25)
                total_score += verdict.score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.5  # Neutral
        
        return total_score / total_weight
    
    def _calculate_confidence(
        self, verdicts: List[FrameworkVerdict], has_conflict: bool
    ) -> float:
        """
        Calculate overall confidence in the decision.
        
        Confidence reduced if:
        - Frameworks have low individual confidence
        - Frameworks are in conflict
        - Novel situation (no precedents)
        """
        # Average framework confidences
        confidences = [v.confidence for v in verdicts]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        
        # Penalize for conflict
        if has_conflict:
            avg_confidence *= 0.7
        
        return max(0.0, min(avg_confidence, 1.0))
    
    def _should_escalate(
        self,
        score: float,
        confidence: float,
        has_conflict: bool,
        plan: ActionPlan
    ) -> bool:
        """
        Determine if decision should be escalated to human.
        
        Escalate if:
        - Confidence below threshold
        - Score near decision boundary (0.5)
        - Significant conflict exists
        - High-stakes decision
        """
        # Low confidence
        if confidence < self.escalation_threshold:
            return True
        
        # Score near boundary (ambiguous)
        if 0.45 <= score <= 0.55:
            return True
        
        # Unresolved conflict
        if has_conflict and confidence < 0.75:
            return True
        
        # High-stakes always escalate if not clear approval
        if plan.is_high_stakes and score < 0.75:
            return True
        
        return False
    
    def _build_veto_verdict(
        self,
        veto_verdict: FrameworkVerdict,
        all_verdicts: List[FrameworkVerdict],
        plan: ActionPlan
    ) -> EthicalVerdict:
        """Build verdict for veto case."""
        # Convert list to dict
        verdicts_dict = {
            FrameworkName(v.framework_name.value): v 
            for v in all_verdicts
        }
        
        return EthicalVerdict(
            action_plan_id=str(plan.id),
            final_decision=DecisionLevel.VETO,
            confidence=1.0,  # Absolute certainty on veto
            framework_verdicts=verdicts_dict,
            resolution_method="kantian_veto",
            primary_reasons=[f"VETO by {veto_verdict.framework_name.value}: {veto_verdict.reasoning}"],
            requires_monitoring=False,
            processing_time_ms=0.0,
            metadata={"veto_framework": veto_verdict.framework_name.value}
        )
    
    def _build_escalated_verdict(
        self,
        verdicts: List[FrameworkVerdict],
        plan: ActionPlan,
        score: float,
        confidence: float,
        conflict_details: List[str]
    ) -> EthicalVerdict:
        """Build verdict for escalated case."""
        # Convert list to dict
        verdicts_dict = {
            FrameworkName(v.framework_name.value): v 
            for v in verdicts
        }
        
        escalation_reason = f"Conflicts: {conflict_details}. Confidence: {confidence:.2f}" if conflict_details else "Low confidence"
        
        return EthicalVerdict(
            action_plan_id=str(plan.id),
            final_decision=DecisionLevel.ESCALATE_TO_HITL,
            confidence=confidence,
            framework_verdicts=verdicts_dict,
            resolution_method="escalation",
            primary_reasons=[escalation_reason],
            requires_monitoring=True,
            processing_time_ms=0.0,
            metadata={"conflict_details": conflict_details, "aggregate_score": score}
        )
    
    def _build_final_verdict(
        self,
        verdicts: List[FrameworkVerdict],
        plan: ActionPlan,
        score: float,
        confidence: float,
        has_conflict: bool
    ) -> EthicalVerdict:
        """Build final verdict based on aggregate score."""
        # Convert list to dict
        verdicts_dict = {
            FrameworkName(v.framework_name.value): v 
            for v in verdicts
        }
        
        # Determine decision level
        if score >= 0.75:
            decision = DecisionLevel.APPROVE
            reason = f"Strong ethical approval (score: {score:.2f})"
        elif score >= 0.60:
            decision = DecisionLevel.APPROVE_WITH_CONDITIONS
            reason = f"Conditional approval (score: {score:.2f})"
        else:
            decision = DecisionLevel.REJECT
            reason = f"Ethical concerns outweigh benefits (score: {score:.2f})"
        
        return EthicalVerdict(
            action_plan_id=str(plan.id),
            final_decision=decision,
            confidence=confidence,
            framework_verdicts=verdicts_dict,
            resolution_method="weighted_aggregation",
            primary_reasons=[reason],
            requires_monitoring=has_conflict,
            processing_time_ms=0.0,
            metadata={"aggregate_score": score, "has_conflict": has_conflict}
        )
