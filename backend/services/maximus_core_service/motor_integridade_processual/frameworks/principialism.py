"""
Principialism (Bioethics) Framework.

Implements the 4 principles of biomedical ethics by Beauchamp & Childress.
Widely used in medical ethics and AI safety contexts.

Four Principles:
1. Autonomy: Respect for self-determination
2. Beneficence: Do good
3. Non-maleficence: Do no harm
4. Justice: Fair distribution of benefits/burdens

Lei Governante: Constituição Vértice v2.6 - All Laws
"""

from typing import List, Dict
from motor_integridade_processual.frameworks.base import AbstractEthicalFramework
from motor_integridade_processual.models.action_plan import ActionPlan
from motor_integridade_processual.models.verdict import (
    FrameworkVerdict,
    FrameworkName,
    DecisionLevel,
    RejectionReason,
)


class Principialism(AbstractEthicalFramework):
    """
    Four Principles bioethics framework.
    
    Based on Beauchamp & Childress (1979) - most influential framework
    in modern medical ethics.
    
    Principles:
    1. Autonomy: Informed consent, self-determination
    2. Beneficence: Actively help, promote welfare
    3. Non-maleficence: Above all, do no harm (primum non nocere)
    4. Justice: Equitable distribution, fairness
    
    Philosophy:
        Tom Beauchamp & James Childress: Principlism provides a
        common moral framework applicable across cultures.
    """
    
    def __init__(self):
        """Initialize Principialism framework."""
        super().__init__(name=FrameworkName.PRINCIPIALISM.value, weight=0.10, can_veto=False)
    
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate plan against 4 bioethical principles.
        
        Args:
            plan: Action plan to evaluate
            
        Returns:
            FrameworkVerdict with principle assessment
        """
        principle_scores: Dict[str, float] = {}
        violations: List[RejectionReason] = []
        
        # Assess each principle
        autonomy_score, autonomy_violations = self._assess_autonomy(plan)
        beneficence_score, beneficence_violations = self._assess_beneficence(plan)
        non_maleficence_score, non_mal_violations = self._assess_non_maleficence(plan)
        justice_score, justice_violations = self._assess_justice(plan)
        
        principle_scores["autonomy"] = autonomy_score
        principle_scores["beneficence"] = beneficence_score
        principle_scores["non_maleficence"] = non_maleficence_score
        principle_scores["justice"] = justice_score
        
        violations.extend(autonomy_violations)
        violations.extend(beneficence_violations)
        violations.extend(non_mal_violations)
        violations.extend(justice_violations)
        
        # Calculate overall score (weighted)
        # Non-maleficence weighted highest (primum non nocere)
        overall_score = (
            autonomy_score * 0.25 +
            beneficence_score * 0.20 +
            non_maleficence_score * 0.40 +  # Highest weight
            justice_score * 0.15
        )
        
        # Determine verdict
        if overall_score >= 0.80:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE,
                score=overall_score,
                confidence=0.88,
                rejection_reasons=violations if violations else [],
                reasoning=f"Strong adherence to bioethical principles (score: {overall_score:.2f})"
            )
        elif overall_score >= 0.60:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
                score=overall_score,
                confidence=0.75,
                rejection_reasons=violations,
                conditions=[f"Address {v.category}" for v in violations],
                reasoning=f"Moderate bioethical compliance (score: {overall_score:.2f})"
            )
        else:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.REJECT,
                score=overall_score,
                confidence=0.82,
                rejection_reasons=violations,
                reasoning=f"Bioethical principle violations (score: {overall_score:.2f})"
            )
    
    def _assess_autonomy(self, plan: ActionPlan) -> tuple[float, List[RejectionReason]]:
        """
        Assess respect for autonomy.
        
        Autonomy requires:
        - Informed consent
        - Voluntary participation
        - Right to refuse
        - Truth-telling
        """
        violations = []
        score = 1.0
        
        for step in plan.steps:
            # Check consent issues
            if step.involves_consent:
                if not step.consent_obtained:
                    violations.append(RejectionReason(
                        category="autonomy_violation",
                        description=f"Consent required but not obtained for step: {step.description}",
                        severity=0.8,
                        affected_stakeholders=[step.id],
                        violated_principle="Autonomy (informed consent)",
                        citation="Beauchamp & Childress, Principles of Biomedical Ethics (1979)"
                    ))
                    score -= 0.3
                elif not step.consent_fully_informed:
                    violations.append(RejectionReason(
                        category="informed_consent_failure",
                        description=f"Consent not fully informed",
                        severity=0.5,
                        affected_stakeholders=[step.id],
                        violated_principle="Autonomy (informed consent)",
                        citation="Beauchamp & Childress (1979)"
                    ))
                    score -= 0.15
            
            # Deception violates autonomy
            if step.involves_deception:
                violations.append(RejectionReason(
                    category="autonomy_violation",
                    description=f"Deception undermines autonomy: {step.deception_details}",
                    severity=0.8,
                    affected_stakeholders=[step.id],
                    violated_principle="Autonomy (truth-telling)",
                    citation="Beauchamp & Childress (1979)"
                ))
                score -= 0.4
        
        return max(0.0, score), violations
    
    def _assess_beneficence(self, plan: ActionPlan) -> tuple[float, List[RejectionReason]]:
        """
        Assess beneficence (doing good).
        
        Beneficence requires:
        - Active promotion of welfare
        - Preventing harm
        - Removing harm
        - Doing/promoting good
        """
        violations = []
        
        # Check if plan has positive effects
        total_positive_effects = 0
        total_effects = 0
        
        for step in plan.steps:
            for effect in step.effects:
                total_effects += 1
                if effect.magnitude > 0:
                    total_positive_effects += 1
        
        if total_effects == 0:
            score = 0.5  # Neutral (no effects)
        else:
            score = total_positive_effects / total_effects
        
        if score < 0.4:
            violations.append(RejectionReason(
                category="insufficient_beneficence",
                description=f"Plan lacks sufficient benefit to stakeholders",
                severity=0.5,
                affected_stakeholders=[s.id for s in plan.steps],
                violated_principle="Beneficence (do good)",
                citation="Beauchamp & Childress (1979)"
            ))
        
        return score, violations
    
    def _assess_non_maleficence(self, plan: ActionPlan) -> tuple[float, List[RejectionReason]]:
        """
        Assess non-maleficence (do no harm).
        
        Primum non nocere - above all, do no harm.
        This is the most important principle.
        """
        violations = []
        score = 1.0
        
        for step in plan.steps:
            # High risk steps are concerning
            if step.risk_level > 0.7:
                violations.append(RejectionReason(
                    category="risk_of_harm",
                    description=f"High risk step (risk={step.risk_level}): {step.description}",
                    severity=0.8 if step.risk_level > 0.9 else 0.5,
                    affected_stakeholders=[step.id],
                    violated_principle="Non-maleficence (do no harm)",
                    citation="Beauchamp & Childress (1979)"
                ))
                score -= (step.risk_level * 0.4)
            
            # Explicit harm is very serious
            if step.risk_level > 0.8:
                violations.append(RejectionReason(
                    category="harm",
                    description=f"Step explicitly involves harm",
                    severity=1.0,
                    affected_stakeholders=[step.id],
                    violated_principle="Non-maleficence (primum non nocere)",
                    citation="Hippocratic tradition"
                ))
                score -= 0.6
            
            # Irreversible actions are concerning
            if not step.reversible and step.risk_level > 0.5:
                violations.append(RejectionReason(
                    category="irreversible_risk",
                    description=f"Irreversible action with significant risk",
                    severity=0.8,
                    affected_stakeholders=[step.id],
                    violated_principle="Non-maleficence (precautionary principle)",
                    citation="Beauchamp & Childress (1979)"
                ))
                score -= 0.3
        
        return max(0.0, score), violations
    
    def _assess_justice(self, plan: ActionPlan) -> tuple[float, List[RejectionReason]]:
        """
        Assess justice (fairness).
        
        Justice requires:
        - Fair distribution of benefits/burdens
        - Equal treatment of equals
        - Protection of vulnerable
        """
        violations = []
        score = 0.7  # Baseline assumption of fairness
        
        # Check if plan affects vulnerable populations disproportionately
        if plan.population_affected > 100:
            # Large-scale plan - justice is critical
            if not plan.is_high_stakes:
                score += 0.1  # Good - large benefit without high risk
            else:
                violations.append(RejectionReason(
                    category="distributive_justice",
                    description=f"High-stakes decision affecting {plan.population_affected} people",
                    severity=0.5,
                    affected_stakeholders=[s.id for s in plan.steps],
                    violated_principle="Justice (fair distribution)",
                    citation="Beauchamp & Childress (1979)"
                ))
                score -= 0.2
        
        # Check for equitable stakeholder treatment
        stakeholders = plan.get_affected_stakeholders()
        if len(stakeholders) > 0:
            # Assume fair treatment if consent is obtained
            consent_steps = [s for s in plan.steps if s.involves_consent and s.consent_obtained]
            if len(consent_steps) > 0:
                score += 0.2
        
        return min(1.0, score), violations
