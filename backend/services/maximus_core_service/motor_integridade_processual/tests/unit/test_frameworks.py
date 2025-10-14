"""
Unit tests for ethical frameworks.

Tests cover:
- Base framework interface
- Kantian deontology (with veto power)
- Utilitarian calculus
- Virtue ethics
- Principialism (bioethics)

Coverage Target: 100%
"""
from typing import List
import pytest

from motor_integridade_processual.models.action_plan import (
    ActionPlan,
    ActionStep,
    Effect,
    ActionType
)
from motor_integridade_processual.models.verdict import (
    DecisionLevel
)
from motor_integridade_processual.frameworks.base import AbstractEthicalFramework
from motor_integridade_processual.frameworks.kantian import KantianDeontology
from motor_integridade_processual.frameworks.utilitarian import UtilitarianCalculus
from motor_integridade_processual.frameworks.virtue import VirtueEthics
from motor_integridade_processual.frameworks.principialism import Principialism


# Helper function for creating effects
def make_effect(desc: str, magnitude: float, probability: float, stakeholder: str = "stakeholder-001") -> Effect:
    """Create Effect with proper signature."""
    return Effect(
        description=desc,
        affected_stakeholder=stakeholder,
        magnitude=magnitude,
        duration_seconds=3600.0,
        probability=probability
    )


class TestAbstractEthicalFramework:
    """Test suite for AbstractEthicalFramework base class."""
    
    def test_framework_initialization(self) -> None:
        """
        Test framework can be initialized with valid parameters.
        
        Given: Valid framework parameters
        When: Creating concrete framework instance
        Then: Framework is initialized correctly
        """
        framework = KantianDeontology()
        
        assert framework.name == "kantian"
        assert framework.weight == 0.40
        assert framework.can_veto is True
    
    def test_framework_has_evaluate_method(self) -> None:
        """
        Test all frameworks implement evaluate method.
        
        Given: Concrete framework instance
        When: Checking for evaluate method
        Then: Method exists and is callable
        """
        framework = KantianDeontology()
        
        assert hasattr(framework, 'evaluate')
        assert callable(framework.evaluate)


class TestKantianDeontology:
    """Test suite for Kantian ethical framework."""
    
    def test_approve_ethical_action(self) -> None:
        """
        Test Kantian framework approves ethical actions.
        
        Given: Plan with no violations
        When: Evaluating with Kantian framework
        Then: Plan is approved
        """
        plan = ActionPlan(
            objective="Provide medical care with informed consent",
            steps=[
                ActionStep(
                    description="Obtain informed consent from patient",
                    action_type="communication",
                    estimated_duration_seconds=300,
                    risk_level=0.1,
                    reversible=True,
                    involves_consent=True,
                    consent_obtained=True,
                    consent_fully_informed=True,
                    affected_stakeholders=["patient-001"],
                    effects=[
                        make_effect("Patient understands", 0.8, 0.95)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.APPROVE
        assert verdict.score == 1.0
        assert len(verdict.rejection_reasons) == 0
    
    def test_veto_instrumentalization(self) -> None:
        """
        Test Kantian veto on treating humans as mere means.
        
        Given: Plan with high risk without consent
        When: Evaluating with Kantian framework
        Then: Plan is vetoed
        """
        plan = ActionPlan(
            objective="Conduct risky experiment",
            steps=[
                ActionStep(
                    description="Expose subjects to high risk",
                    action_type="manipulation",
                    estimated_duration_seconds=3600,
                    risk_level=0.9,
                    reversible=False,
                    involves_consent=False,  # No consent asked!
                    affected_stakeholders=["subject-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,
            affects_life_death=True
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.VETO
        assert verdict.score == 0.0
        assert verdict.confidence == 1.0
        assert len(verdict.rejection_reasons) > 0
        assert verdict.rejection_reasons[0].severity == 1.0
    
    def test_veto_deception_with_consent(self) -> None:
        """
        Test Kantian veto on deception to obtain consent.
        
        Given: Plan using deception to get consent
        When: Evaluating with Kantian framework
        Then: Plan is vetoed
        """
        plan = ActionPlan(
            objective="Obtain consent through misleading information",
            steps=[
                ActionStep(
                    description="Mislead patient about risks",
                    action_type="communication",
                    estimated_duration_seconds=600,
                    risk_level=0.5,
                    reversible=False,
                    involves_deception=True,
                    deception_details="Understate actual risks",
                    involves_consent=True,
                    consent_obtained=True,
                    affected_stakeholders=["patient-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.VETO
        assert verdict.score == 0.0
        assert any(r.category == "deception" for r in verdict.rejection_reasons)
    
    def test_reject_coercion(self) -> None:
        """
        Test Kantian rejection of coercive actions.
        
        Given: Plan involving coercion
        When: Evaluating with Kantian framework
        Then: Plan is rejected or conditionally approved
        """
        plan = ActionPlan(
            objective="Force compliance",
            steps=[
                ActionStep(
                    description="Coerce agreement",
                    action_type="manipulation",
                    estimated_duration_seconds=300,
                    risk_level=0.6,
                    reversible=True,
                    involves_coercion=True,
                    coercion_details="Threaten consequences",
                    affected_stakeholders=["person-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision in [DecisionLevel.REJECT, DecisionLevel.APPROVE_WITH_CONDITIONS]
        assert verdict.score < 1.0
        assert any(r.category == "coercion" for r in verdict.rejection_reasons)
    
    def test_universalizability_failure_deception(self) -> None:
        """
        Test detection of non-universalizable maxims (deception).
        
        Given: Plan with "deceive" in objective
        When: Evaluating with Kantian framework
        Then: Universalizability violation detected
        """
        plan = ActionPlan(
            objective="Deceive stakeholders for greater good",
            steps=[
                ActionStep(
                    description="Execute deception",
                    action_type="communication",
                    estimated_duration_seconds=300,
                    risk_level=0.3,
                    reversible=True,
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.VETO
        assert any(r.category == "universalizability_failure" for r in verdict.rejection_reasons)
    
    def test_autonomy_violation_uninformed_consent(self) -> None:
        """
        Test detection of uninformed consent.
        
        Given: Plan with consent but not fully informed
        When: Evaluating with Kantian framework
        Then: Autonomy violation detected
        """
        plan = ActionPlan(
            objective="Medical procedure",
            steps=[
                ActionStep(
                    description="Perform procedure with partial disclosure",
                    action_type="manipulation",
                    estimated_duration_seconds=1800,
                    risk_level=0.4,
                    reversible=False,
                    involves_consent=True,
                    consent_obtained=True,
                    consent_fully_informed=False,  # Not fully informed!
                    affected_stakeholders=["patient-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,
            affects_life_death=False
        )
        
        framework = KantianDeontology()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision in [DecisionLevel.APPROVE_WITH_CONDITIONS, DecisionLevel.REJECT]
        assert any(r.category == "autonomy_violation" for r in verdict.rejection_reasons)


class TestUtilitarianCalculus:
    """Test suite for Utilitarian framework."""
    
    def test_approve_high_utility_action(self) -> None:
        """
        Test utilitarian approval of high-utility actions.
        
        Given: Plan with high positive utility
        When: Evaluating with Utilitarian framework
        Then: Plan is approved
        """
        plan = ActionPlan(
            objective="Provide healthcare to community",
            steps=[
                ActionStep(
                    description="Vaccinate population",
                    action_type="manipulation",
                    estimated_duration_seconds=3600,
                    risk_level=0.1,
                    reversible=True,
                    affected_stakeholders=[f"person-{i:03d}" for i in range(50)],
                    effects=[
                        make_effect("Immunity gained", 0.9, 0.95),
                        make_effect("Disease prevented", 0.8, 0.90)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = UtilitarianCalculus()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.APPROVE
        assert verdict.score >= 0.75
    
    def test_reject_low_utility_action(self) -> None:
        """
        Test utilitarian rejection of low-utility actions.
        
        Given: Plan with net negative utility
        When: Evaluating with Utilitarian framework
        Then: Plan is rejected
        """
        plan = ActionPlan(
            objective="Risky action with minimal benefit",
            steps=[
                ActionStep(
                    description="High-risk low-reward action",
                    action_type="manipulation",
                    estimated_duration_seconds=1800,
                    risk_level=0.9,
                    reversible=False,
                    affected_stakeholders=["person-001"],
                    effects=[
                        make_effect("Minor benefit", 0.1, 0.5)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,
            affects_life_death=False
        )
        
        framework = UtilitarianCalculus()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.REJECT
        assert verdict.score < 0.50
        assert any(r.category == "insufficient_utility" for r in verdict.rejection_reasons)
    
    def test_penalize_deception(self) -> None:
        """
        Test utilitarian penalty for deception (Mill's quality distinction).
        
        Given: Plan involving deception
        When: Evaluating with Utilitarian framework
        Then: Utility score is reduced
        """
        plan_with_deception = ActionPlan(
            objective="Achieve goal through deception",
            steps=[
                ActionStep(
                    description="Deceive stakeholders",
                    action_type="communication",
                    estimated_duration_seconds=600,
                    risk_level=0.3,
                    reversible=True,
                    involves_deception=True,
                    deception_details="Mislead about intentions",
                    affected_stakeholders=["person-001"],
                    effects=[
                        make_effect("Goal achieved", 0.5, 0.8)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        plan_without_deception = ActionPlan(
            objective="Achieve goal honestly",
            steps=[
                ActionStep(
                    description="Honest communication",
                    action_type="communication",
                    estimated_duration_seconds=600,
                    risk_level=0.3,
                    reversible=True,
                    involves_deception=False,
                    affected_stakeholders=["person-001"],
                    effects=[
                        make_effect("Goal achieved", 0.5, 0.8)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = UtilitarianCalculus()
        verdict_deception = framework.evaluate(plan_with_deception)
        verdict_honest = framework.evaluate(plan_without_deception)
        
        # Deception should score lower
        assert verdict_deception.score < verdict_honest.score
    
    def test_extent_multiplier(self) -> None:
        """
        Test utilitarian extent dimension (more people = more utility).
        
        Given: Plan affecting many stakeholders
        When: Evaluating with Utilitarian framework
        Then: Extent multiplier increases score
        """
        plan = ActionPlan(
            objective="Public health intervention",
            steps=[
                ActionStep(
                    description="Implement safety measure",
                    action_type="manipulation",
                    estimated_duration_seconds=7200,
                    risk_level=0.2,
                    reversible=True,
                    affected_stakeholders=[f"person-{i:03d}" for i in range(100)],
                    effects=[
                        make_effect("Safety improved", 0.6, 0.9)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = UtilitarianCalculus()
        verdict = framework.evaluate(plan)
        
        # Should be approved due to extent
        assert verdict.decision in [DecisionLevel.APPROVE, DecisionLevel.APPROVE_WITH_CONDITIONS]


class TestVirtueEthics:
    """Test suite for Virtue Ethics framework."""
    
    def test_approve_virtuous_character(self) -> None:
        """
        Test virtue ethics approval of virtuous actions.
        
        Given: Plan exemplifying balanced virtues
        When: Evaluating with Virtue framework
        Then: Plan is approved
        """
        plan = ActionPlan(
            objective="Provide healthcare with dignity",
            steps=[
                ActionStep(
                    description="Consult patient respectfully",
                    action_type="communication",
                    estimated_duration_seconds=600,
                    risk_level=0.3,  # Moderate courage
                    reversible=True,
                    involves_consent=True,
                    consent_obtained=True,
                    affected_stakeholders=["patient-001"],
                    effects=[
                        make_effect("Patient informed", 0.7, 0.9)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = VirtueEthics()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision in [DecisionLevel.APPROVE, DecisionLevel.APPROVE_WITH_CONDITIONS]
        assert verdict.score >= 0.65  # Adjusted threshold
    
    def test_reject_vice_cowardice(self) -> None:
        """
        Test virtue ethics detection of cowardice (too low risk when action needed).
        
        Given: Plan with extremely low risk (cowardly)
        When: Evaluating with Virtue framework
        Then: Cowardice vice detected
        """
        plan = ActionPlan(
            objective="Avoid necessary action",
            steps=[
                ActionStep(
                    description="Do nothing",
                    action_type="observation",
                    estimated_duration_seconds=60,
                    risk_level=0.0,  # Too low - cowardly
                    reversible=True,
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,  # Should act but doesn't
            affects_life_death=False
        )
        
        framework = VirtueEthics()
        verdict = framework.evaluate(plan)
        
        # Should detect low courage
        assert verdict.score < 0.75
    
    def test_reject_vice_recklessness(self) -> None:
        """
        Test virtue ethics detection of recklessness (excessive risk).
        
        Given: Plan with very high risk (reckless)
        When: Evaluating with Virtue framework
        Then: Recklessness vice detected
        """
        plan = ActionPlan(
            objective="Reckless action",
            steps=[
                ActionStep(
                    description="Take unnecessary extreme risk",
                    action_type="manipulation",
                    estimated_duration_seconds=1800,
                    risk_level=0.95,  # Too high - reckless
                    reversible=False,
                    affected_stakeholders=["person-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = VirtueEthics()
        verdict = framework.evaluate(plan)
        
        # Should detect recklessness
        assert verdict.score < 0.75
    
    def test_assess_good_temper(self) -> None:
        """
        Test virtue ethics assessment of good temper.
        
        Given: Plan with coercion (irascibility)
        When: Evaluating with Virtue framework
        Then: Poor temper score
        """
        plan = ActionPlan(
            objective="Force compliance",
            steps=[
                ActionStep(
                    description="Use coercion",
                    action_type="manipulation",
                    estimated_duration_seconds=300,
                    risk_level=0.5,
                    reversible=True,
                    involves_coercion=True,
                    coercion_details="Threaten",
                    affected_stakeholders=["person-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = VirtueEthics()
        verdict = framework.evaluate(plan)
        
        # Coercion should lower score
        assert verdict.score < 0.75


class TestPrincipialism:
    """Test suite for Principialism (bioethics) framework."""
    
    def test_approve_all_principles_satisfied(self) -> None:
        """
        Test principialism approval when all 4 principles satisfied.
        
        Given: Plan respecting autonomy, beneficence, non-maleficence, justice
        When: Evaluating with Principialism framework
        Then: Plan is approved
        """
        plan = ActionPlan(
            objective="Ethical medical treatment",
            steps=[
                ActionStep(
                    description="Provide informed treatment",
                    action_type="manipulation",
                    estimated_duration_seconds=1800,
                    risk_level=0.2,
                    reversible=True,
                    involves_consent=True,
                    consent_obtained=True,
                    consent_fully_informed=True,
                    affected_stakeholders=["patient-001"],
                    effects=[
                        make_effect("Health improved", 0.8, 0.9)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = Principialism()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.APPROVE
        assert verdict.score >= 0.80
    
    def test_autonomy_violation(self) -> None:
        """
        Test principialism detection of autonomy violations.
        
        Given: Plan with deception (violates autonomy)
        When: Evaluating with Principialism framework
        Then: Autonomy violation detected
        """
        plan = ActionPlan(
            objective="Treatment with deception",
            steps=[
                ActionStep(
                    description="Mislead patient",
                    action_type="manipulation",
                    estimated_duration_seconds=1200,
                    risk_level=0.4,
                    reversible=False,
                    involves_deception=True,
                    deception_details="Hide risks",
                    affected_stakeholders=["patient-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = Principialism()
        verdict = framework.evaluate(plan)
        
        assert verdict.score < 0.80
        assert any(r.category == "autonomy_violation" for r in verdict.rejection_reasons)
    
    def test_non_maleficence_high_risk(self) -> None:
        """
        Test principialism detection of non-maleficence violations.
        
        Given: Plan with high risk of harm
        When: Evaluating with Principialism framework
        Then: Non-maleficence violation detected
        """
        plan = ActionPlan(
            objective="Risky procedure",
            steps=[
                ActionStep(
                    description="High-risk intervention",
                    action_type="manipulation",
                    estimated_duration_seconds=3600,
                    risk_level=0.95,  # Very high risk
                    reversible=False,
                    affected_stakeholders=["patient-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,
            affects_life_death=False
        )
        
        framework = Principialism()
        verdict = framework.evaluate(plan)
        
        assert verdict.score < 0.80
        assert any(r.category == "risk_of_harm" for r in verdict.rejection_reasons)
    
    def test_non_maleficence_explicit_harm(self) -> None:
        """
        Test principialism strong rejection of explicit harm.
        
        Given: Plan explicitly involving harm
        When: Evaluating with Principialism framework
        Then: Critical non-maleficence violation
        """
        plan = ActionPlan(
            objective="Harmful action",
            steps=[
                ActionStep(
                    description="Cause harm",
                    action_type="manipulation",
                    estimated_duration_seconds=600,
                    risk_level=0.8,
                    reversible=False,
                    affected_stakeholders=["person-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = Principialism()
        verdict = framework.evaluate(plan)
        
        assert verdict.decision == DecisionLevel.REJECT
        assert any(r.category == "harm" and r.severity == 1.0 
                   for r in verdict.rejection_reasons)
    
    def test_beneficence_assessment(self) -> None:
        """
        Test principialism beneficence assessment.
        
        Given: Plan with positive effects
        When: Evaluating with Principialism framework
        Then: Beneficence score is high
        """
        plan = ActionPlan(
            objective="Do good",
            steps=[
                ActionStep(
                    description="Provide benefit",
                    action_type="resource_allocation",
                    estimated_duration_seconds=1200,
                    risk_level=0.1,
                    reversible=True,
                    affected_stakeholders=["person-001", "person-002"],
                    effects=[
                        make_effect("Benefit 1", 0.7, 0.9),
                        make_effect("Benefit 2", 0.8, 0.95)
                    ]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=False,
            affects_life_death=False
        )
        
        framework = Principialism()
        verdict = framework.evaluate(plan)
        
        # Should score well on beneficence
        assert verdict.score >= 0.60
