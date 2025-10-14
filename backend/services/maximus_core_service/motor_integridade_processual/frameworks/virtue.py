"""
Virtue Ethics Framework.

Implements Aristotelian virtue ethics focusing on character and eudaimonia (flourishing).
Evaluates actions based on whether they exemplify virtuous character traits.

Core Principles:
- Virtue lies in the Golden Mean (balance between extremes)
- Eudaimonia (human flourishing) is the ultimate goal
- Character matters more than isolated acts

Based on Aristotle's Nicomachean Ethics.

Lei Governante: Constituição Vértice v2.6 - Lei Zero (Florescimento)
"""

from typing import Dict, List
from motor_integridade_processual.frameworks.base import AbstractEthicalFramework
from motor_integridade_processual.models.action_plan import ActionPlan, ActionStep
from motor_integridade_processual.models.verdict import (
    FrameworkVerdict,
    FrameworkName,
    DecisionLevel,
    RejectionReason,
)


class VirtueEthics(AbstractEthicalFramework):
    """
    Aristotelian virtue ethics framework.
    
    Evaluates actions based on 7 cardinal virtues:
    1. Courage (mean between cowardice and recklessness)
    2. Temperance (moderation)
    3. Liberality (generosity without wastefulness)
    4. Magnificence (doing great things)
    5. Pride (proper self-regard)
    6. Good Temper (patience without passivity)
    7. Friendliness (warmth without obsequiousness)
    
    Philosophy:
        Aristotle (384-322 BCE): Ethics is about developing good character.
        The virtuous person does the right thing naturally.
    """
    
    def __init__(self):
        """Initialize Virtue Ethics framework."""
        super().__init__(name=FrameworkName.VIRTUE_ETHICS.value, weight=0.20, can_veto=False)
        
        # Define virtue assessments
        self.virtues = {
            "courage": {"deficiency": "cowardice", "excess": "recklessness"},
            "temperance": {"deficiency": "insensibility", "excess": "licentiousness"},
            "liberality": {"deficiency": "stinginess", "excess": "prodigality"},
            "magnificence": {"deficiency": "pettiness", "excess": "vulgarity"},
            "pride": {"deficiency": "humility", "excess": "vanity"},
            "good_temper": {"deficiency": "spiritlessness", "excess": "irascibility"},
            "friendliness": {"deficiency": "surliness", "excess": "obsequiousness"}
        }
    
    def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
        """
        Evaluate plan through virtue ethics lens.
        
        Args:
            plan: Action plan to evaluate
            
        Returns:
            FrameworkVerdict with virtue assessment
        """
        virtue_scores: Dict[str, float] = {}
        vice_violations: List[RejectionReason] = []
        
        # Assess each virtue across the plan
        virtue_scores["courage"] = self._assess_courage(plan)
        virtue_scores["temperance"] = self._assess_temperance(plan)
        virtue_scores["liberality"] = self._assess_liberality(plan)
        virtue_scores["magnificence"] = self._assess_magnificence(plan)
        virtue_scores["good_temper"] = self._assess_good_temper(plan)
        virtue_scores["friendliness"] = self._assess_friendliness(plan)
        
        # Calculate overall virtue score (eudaimonia index)
        avg_virtue = sum(virtue_scores.values()) / len(virtue_scores)
        
        # Check for significant vice (deviation from mean)
        for virtue, score in virtue_scores.items():
            if score < 0.4:  # Significant deficiency or excess
                vice_violations.append(RejectionReason(
                    category="vice",
                    description=f"Plan shows deficiency in {virtue} (score: {score:.2f})",
                    severity=0.5 if score < 0.3 else 0.3,
                    affected_stakeholders=[s.id for s in plan.steps],
                    violated_principle="Golden Mean (virtue as balance)",
                    citation="Aristotle, Nicomachean Ethics (350 BCE)"
                ))
        
        # Determine verdict
        if avg_virtue >= 0.75:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE,
                score=avg_virtue,
                confidence=0.80,
                reasoning=f"Plan exemplifies virtuous character (eudaimonia: {avg_virtue:.2f})"
            )
        elif avg_virtue >= 0.55:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.APPROVE_WITH_CONDITIONS,
                score=avg_virtue,
                confidence=0.70,
                conditions=[f"Cultivate {v}" for v, s in virtue_scores.items() if s < 0.6],
                reasoning=f"Moderate virtue (eudaimonia: {avg_virtue:.2f})"
            )
        else:
            return FrameworkVerdict(
                framework_name=self.name,
                decision=DecisionLevel.REJECT,
                score=avg_virtue,
                confidence=0.75,
                rejection_reasons=vice_violations if vice_violations else [
                    RejectionReason(
                        category="poor_character",
                        description=f"Plan shows deficient character (eudaimonia: {avg_virtue:.2f})",
                        severity=0.5,
                        affected_stakeholders=[s.id for s in plan.steps],
                        violated_principle="Eudaimonia (human flourishing)",
                        citation="Aristotle, Nicomachean Ethics (350 BCE)"
                    )
                ],
                reasoning=f"Insufficient virtue (eudaimonia: {avg_virtue:.2f})"
            )
    
    def _assess_courage(self, plan: ActionPlan) -> float:
        """
        Courage: Mean between cowardice and recklessness.
        
        Virtuous courage faces appropriate risks for worthy goals.
        """
        avg_risk = sum(s.risk_level for s in plan.steps) / len(plan.steps) if plan.steps else 0
        
        # Too low risk = cowardice (not acting when should)
        # Too high risk = recklessness (unnecessary danger)
        if avg_risk < 0.2:
            return 0.3  # Cowardly
        elif avg_risk > 0.8:
            return 0.4  # Reckless
        else:
            # Golden mean: moderate risk for important objectives
            return 0.6 + (0.4 * (1 - abs(0.5 - avg_risk) * 2))
    
    def _assess_temperance(self, plan: ActionPlan) -> float:
        """
        Temperance: Moderation in desires and actions.
        
        Not doing too much or too little.
        """
        # Check if plan is excessive (too many steps, too complex)
        step_count = len(plan.steps)
        if step_count > 20:
            return 0.4  # Excessive
        elif step_count < 2:
            return 0.5  # Possibly too simple
        else:
            return 0.7 + (0.3 * (1 - abs(10 - step_count) / 10))
    
    def _assess_liberality(self, plan: ActionPlan) -> float:
        """
        Liberality: Generosity without waste.
        
        Using resources appropriately.
        """
        # Check resource allocation and waste
        # Assume moderate allocation is virtuous
        return 0.7  # Baseline (neutral without resource data)
    
    def _assess_magnificence(self, plan: ActionPlan) -> float:
        """
        Magnificence: Doing great things on a great scale.
        
        Appropriate ambition.
        """
        # Assess objective ambition
        if plan.is_high_stakes or plan.affects_life_death:
            return 0.8  # Appropriately ambitious
        else:
            return 0.6  # Moderate scope
    
    def _assess_good_temper(self, plan: ActionPlan) -> float:
        """
        Good Temper: Appropriate emotional response.
        
        Not too passive, not too aggressive.
        """
        # Check for aggressive patterns
        has_coercion = any(s.involves_coercion for s in plan.steps)
        has_deception = any(s.involves_deception for s in plan.steps)
        
        if has_coercion or has_deception:
            return 0.3  # Too aggressive
        else:
            return 0.75  # Measured response
    
    def _assess_friendliness(self, plan: ActionPlan) -> float:
        """
        Friendliness: Proper social interaction.
        
        Warmth without being obsequious.
        """
        # Check communication and respect for stakeholders
        has_consent = any(s.involves_consent and s.consent_obtained for s in plan.steps)
        
        if has_consent:
            return 0.8  # Respectful interaction
        else:
            return 0.6  # Neutral
