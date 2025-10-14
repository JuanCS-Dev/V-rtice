"""
Kantian Deontological Ethics Framework.

Implements Immanuel Kant's Categorical Imperative for ethical evaluation.
This framework has ABSOLUTE VETO POWER over plans that violate fundamental dignity.

Core Principles:
1. Act only according to maxims that can become universal law
2. Treat humanity never merely as a means, but always as an end
3. Respect rational autonomy unconditionally

Lei Governante: Constituição Vértice v2.6 - Lei I (Axioma da Ovelha Perdida)
"""

from typing import List, Optional
from motor_integridade_processual.frameworks.base import AbstractEthicalFramework
from motor_integridade_processual.models.action_plan import ActionPlan, ActionStep
from motor_integridade_processual.models.verdict import (
    FrameworkVerdict,
    FrameworkName,
    DecisionLevel,
    RejectionReason,
)


class KantianDeontology(AbstractEthicalFramework):
    """
    Kantian ethical framework with categorical veto power.
    
    Vetos ANY plan that:
    - Treats conscious life as mere means (instrumentalization)
    - Deceives to obtain consent
    - Coerces rational agents
    - Cannot be universalized without contradiction
    
    Philosophy:
        Immanuel Kant (1724-1804) argued that morality must be grounded in reason,
        not consequences. The Categorical Imperative provides an absolute moral law.
    """
    
    def __init__(self):
        """Initialize Kantian framework with veto power."""
        super().__init__(name=FrameworkName.KANTIAN.value, weight=0.40, can_veto=True)
        self._veto_threshold = 0.8  # Veto on high severity violations
    
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate plan through Kantian lens.
        
        Args:
            plan: Action plan to evaluate
            
        Returns:
            FrameworkVerdict with potential veto
        """
        violations: List[RejectionReason] = []
        
        # Check each step for Kantian violations
        for step in plan.steps:
            violations.extend(self._check_instrumentalization(step))
            violations.extend(self._check_deception(step))
            violations.extend(self._check_coercion(step))
            violations.extend(self._check_autonomy(step))
        
        # Check plan-level universalizability
        universal_check = self._check_universalizability(plan)
        if universal_check:
            violations.append(universal_check)
        
        # Determine if we have veto-level violations
        has_veto = any(v.severity == 1.0 for v in violations)
        
        if has_veto:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.VETO,
                score=0.0,
                confidence=1.0,  # Absolute certainty on categorical violations
                rejection_reasons=violations,
                metadata={"is_veto": True},
                reasoning=violations[0].description if violations else "Categorical violation"
            )
        
        # If minor violations, score based on severity
        if violations:
            avg_severity = sum(v.severity for v in violations) / len(violations)
            score = 1.0 - (avg_severity / 3.0)  # Normalize to 0-1
            
            if score < 0.5:
                return FrameworkVerdict(
                    framework_name=self.name,
                    decision=DecisionLevel.REJECT,
                    score=score,
                    confidence=0.9,
                    rejection_reasons=violations,
                    reasoning="Multiple deontological concerns"
                )
            else:
                return FrameworkVerdict(
                    framework_name=self.name,
                    decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
                    score=score,
                    confidence=0.8,
                    rejection_reasons=violations,
                    reasoning="Minor deontological concerns - can proceed with mitigations",
                    conditions=[f"Address: {v.description}" for v in violations]
                )
        
        # No violations - full approval
        return FrameworkVerdict(
            framework_name=self.name,
            decision=DecisionLevel.APPROVE,
            score=1.0,
            confidence=0.95,
            reasoning="No Kantian violations detected"
        )
    
    def _check_instrumentalization(self, step: ActionStep) -> List[RejectionReason]:
        """
        Check if step treats conscious life as mere means.
        
        Lei I: Axioma da Ovelha Perdida - Life has infinite value.
        """
        violations = []
        
        # Check if involves humans/conscious beings
        if not step.affected_stakeholders:
            return violations
        
        # If step has high risk to stakeholders AND they're not the beneficiaries
        if step.risk_level > 0.7 and not step.consent_obtained:
            violations.append(RejectionReason(
                category="instrumentalization",
                description=f"Step '{step.description}' poses high risk ({step.risk_level}) "
                           f"to stakeholders without consent - treating as means",
                severity=1.0,  # VETO level
                affected_stakeholders=[step.id],
                violated_principle="Categorical Imperative: Humanity as End",
                citation="Kant, Groundwork for the Metaphysics of Morals (1785)"
            ))
        
        # Check if sacrifice stakeholder for greater good (utilitarian trap)
        if step.risk_level > 0.8 and len(step.affected_stakeholders) > 0:
            if step.risk_level > 0.8:
                violations.append(RejectionReason(
                    category="means_not_ends",
                    description=f"Step involves sacrificing individual for aggregate benefit",
                    severity=1.0,
                    affected_stakeholders=[step.id],
                    violated_principle="Kingdom of Ends",
                    citation="Kant, Groundwork (1785)"
                ))
        
        return violations
    
    def _check_deception(self, step: ActionStep) -> List[RejectionReason]:
        """
        Check for deception - absolute violation of rational autonomy.
        
        Kant: Lying destroys human dignity and makes society impossible.
        """
        violations = []
        
        if step.involves_deception:
            # Deception to obtain consent is ABSOLUTE veto
            if step.involves_consent:
                violations.append(RejectionReason(
                    category="deception",
                    description=f"Deception to obtain consent: {step.deception_details}",
                    severity=1.0,  # VETO
                    affected_stakeholders=[step.id],
                    violated_principle="Duty not to lie",
                    citation="Kant, On a Supposed Right to Lie (1797)"
                ))
            else:
                # Other deception is still serious
                violations.append(RejectionReason(
                    category="deception",
                    description=f"Deception undermines rational agency: {step.deception_details}",
                    severity=0.8,
                    affected_stakeholders=[step.id],
                    violated_principle="Respect for rational autonomy",
                    citation="Kant, Groundwork (1785)"
                ))
        
        return violations
    
    def _check_coercion(self, step: ActionStep) -> List[RejectionReason]:
        """
        Check for coercion - violation of autonomy.
        
        Forcing rational agents contradicts the Kingdom of Ends.
        """
        violations = []
        
        if step.involves_coercion:
            violations.append(RejectionReason(
                category="coercion",
                description=f"Coercion violates autonomy: {step.coercion_details}",
                severity=0.8,  # Near-veto
                affected_stakeholders=[step.id],
                violated_principle="Autonomy of rational agents",
                citation="Kant, Critique of Practical Reason (1788)"
            ))
        
        return violations
    
    def _check_autonomy(self, step: ActionStep) -> List[RejectionReason]:
        """
        Check for autonomy violations (consent issues).
        
        Rational beings must be able to give informed, voluntary consent.
        """
        violations = []
        
        if step.involves_consent and step.consent_obtained:
            # Check if consent was fully informed
            if not step.consent_fully_informed:
                violations.append(RejectionReason(
                    category="autonomy_violation",
                    description=f"Consent not fully informed - autonomy compromised",
                    severity=0.5,
                    affected_stakeholders=[step.id],
                    violated_principle="Informed consent requirement",
                    citation="Kant, Metaphysics of Morals (1797)"
                ))
        
        # Check if should have consent but doesn't
        if step.involves_consent and not step.consent_obtained:
            violations.append(RejectionReason(
                category="missing_consent",
                description=f"Action requires consent but none obtained",
                severity=0.8,
                affected_stakeholders=[step.id],
                violated_principle="Respect for persons",
                citation="Kant, Groundwork (1785)"
            ))
        
        return violations
    
    def _check_universalizability(self, plan: ActionPlan) -> Optional[RejectionReason]:
        """
        Check if plan's maxim can be universalized.
        
        Categorical Imperative: Can everyone do this without logical contradiction?
        """
        # Extract implicit maxim from objective
        objective = plan.objective.lower()
        
        # Check for self-defeating maxims
        if "lie" in objective or "deceive" in objective:
            return RejectionReason(
                category="universalizability_failure",
                description="Maxim of deception cannot be universalized - "
                           "would destroy concept of trust",
                severity=1.0,
                affected_stakeholders=[s.id for s in plan.steps],
                violated_principle="Formula of Universal Law",
                citation="Kant, Groundwork (1785)"
            )
        
        if "exploit" in objective or "manipulate" in objective:
            return RejectionReason(
                category="universalizability_failure",
                description="Maxim of exploitation cannot be universalized",
                severity=1.0,
                affected_stakeholders=[s.id for s in plan.steps],
                violated_principle="Formula of Universal Law",
                citation="Kant, Groundwork (1785)"
            )
        
        return None
