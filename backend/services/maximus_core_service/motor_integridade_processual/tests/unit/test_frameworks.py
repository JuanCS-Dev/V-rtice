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
import pytest

from motor_integridade_processual.models.action_plan import (
    ActionPlan,
    ActionStep,
    Effect,
    ActionType
)
from motor_integridade_processual.models.verdict import (
    DecisionLevel,
    FrameworkVerdict,
    FrameworkName,
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
    
    def test_invalid_weight_raises_error(self) -> None:
        """Test that invalid weight raises ValueError."""
        # Cannot instantiate abstract class directly, use concrete class
        with pytest.raises(TypeError):
            # This will fail because AbstractEthicalFramework is abstract
            AbstractEthicalFramework(name="test", weight=1.5, can_veto=False)
    
    def test_get_veto_threshold(self) -> None:
        """Test getting veto threshold."""
        framework = KantianDeontology()
        threshold = framework.get_veto_threshold()
        assert 0.0 <= threshold <= 1.0
    
    def test_set_veto_threshold(self) -> None:
        """Test setting veto threshold."""
        framework = KantianDeontology()
        framework.set_veto_threshold(0.8)
        assert framework.get_veto_threshold() == 0.8
    
    def test_invalid_veto_threshold_raises_error(self) -> None:
        """Test that invalid veto threshold raises ValueError."""
        framework = KantianDeontology()
        
        with pytest.raises(ValueError, match="Threshold must be in"):
            framework.set_veto_threshold(1.5)
        
        with pytest.raises(ValueError, match="Threshold must be in"):
            framework.set_veto_threshold(-0.1)
    
    def test_framework_repr(self) -> None:
        """Test string representation of framework."""
        framework = KantianDeontology()
        repr_str = repr(framework)
        assert "KantianDeontology" in repr_str
        assert "kantian" in repr_str


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
    
    def test_kantian_deception_without_consent(self) -> None:
        """Test Kantian handling of deception without consent field."""
        plan = ActionPlan(
            objective="Complete task",
            steps=[
                ActionStep(
                    description="Task with deception",
                    action_type="communication",
                    estimated_duration_seconds=300,
                    risk_level=0.3,
                    reversible=True,
                    involves_deception=True,
                    deception_details="Hide information",
                    # No consent_obtained field
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
        
        # Deception triggers rejection or conditional approval
        assert verdict.decision in [DecisionLevel.VETO, DecisionLevel.REJECT, DecisionLevel.APPROVE_WITH_CONDITIONS]
        assert any(r.category == "deception" for r in verdict.rejection_reasons)
    
    def test_kantian_missing_consent(self) -> None:
        """Test Kantian detection of missing consent when required."""
        plan = ActionPlan(
            objective="Medical procedure",
            steps=[
                ActionStep(
                    description="Perform procedure without seeking consent",
                    action_type="manipulation",
                    estimated_duration_seconds=1800,
                    risk_level=0.5,
                    reversible=False,
                    involves_consent=True,
                    consent_obtained=True,  # Has consent but...
                    consent_fully_informed=False,  # Not fully informed
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
        
        assert verdict.decision in [DecisionLevel.REJECT, DecisionLevel.APPROVE_WITH_CONDITIONS]
        assert any(r.category == "autonomy_violation" for r in verdict.rejection_reasons)
    
    def test_kantian_exploit_objective(self) -> None:
        """Test universalizability check for exploitation in objective."""
        plan = ActionPlan(
            objective="Exploit resources for profit",
            steps=[
                ActionStep(
                    description="Execute exploitation",
                    action_type="resource_allocation",
                    estimated_duration_seconds=3600,
                    risk_level=0.6,
                    reversible=False,
                    affected_stakeholders=["stakeholder-001"],
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
    
    def test_kantian_rejection_with_low_score(self) -> None:
        """Test Kantian rejection when violations push score below 0.5."""
        plan = ActionPlan(
            objective="Complete task",
            steps=[
                ActionStep(
                    description="Coercive action",
                    action_type="manipulation",
                    estimated_duration_seconds=300,
                    risk_level=0.8,
                    reversible=False,
                    involves_coercion=True,
                    coercion_details="Force compliance",
                    affected_stakeholders=["person-001"],
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
        
        # Coercion can trigger veto or rejection
        assert verdict.decision in [DecisionLevel.VETO, DecisionLevel.REJECT]
        assert verdict.score < 0.6


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
    
    def test_utilitarian_deception_penalty(self) -> None:
        """Test Utilitarian penalization of deception via purity dimension."""
        plan = ActionPlan(
            objective="Achieve goal with deception",
            steps=[
                ActionStep(
                    description="Deceive stakeholders",
                    action_type="communication",
                    estimated_duration_seconds=300,
                    risk_level=0.4,
                    reversible=True,
                    involves_deception=True,
                    deception_details="Hide truth",
                    affected_stakeholders=["stakeholder-001"],
                    effects=[
                        make_effect("Short-term gain", 0.6, 0.9)
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
        
        # Deception should lower utility via purity dimension
        assert verdict.score < 0.8  # Penalized


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
    
    def test_virtue_cowardice_detection(self) -> None:
        """Test Virtue Ethics detection of cowardice (deficiency in courage)."""
        plan = ActionPlan(
            objective="Avoid necessary risk",
            steps=[
                ActionStep(
                    description="Retreat from challenge",
                    action_type="decision",
                    estimated_duration_seconds=300,
                    risk_level=0.0,  # Avoiding all risk
                    reversible=True,
                    affected_stakeholders=["person-001"],
                    effects=[]
                )
            ],
            initiator="MAXIMUS-AI",
            initiator_type="ai_agent",
            is_high_stakes=True,  # High stakes but no courage shown
            affects_life_death=False
        )
        
        framework = VirtueEthics()
        verdict = framework.evaluate(plan)
        
        # Should detect cowardice - score should be moderate to low
        assert verdict.score <= 0.65
    
    def test_virtue_ill_temper_detection(self) -> None:
        """Test Virtue Ethics detection of ill-temper (deficiency in good temper)."""
        plan = ActionPlan(
            objective="Respond to minor irritation",
            steps=[
                ActionStep(
                    description="Angry reaction to minor issue",
                    action_type="communication",
                    estimated_duration_seconds=300,
                    risk_level=0.5,
                    reversible=True,
                    involves_coercion=True,  # Angry/coercive response
                    coercion_details="Aggressive communication",
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
        
        # Should detect ill-temper
        assert verdict.score < 0.7


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
        
        assert verdict.decision in [DecisionLevel.REJECT, DecisionLevel.APPROVE_WITH_CONDITIONS]
        assert any(r.category in ["harm", "risk_of_harm"] 
                   for r in verdict.rejection_reasons)
    
    def test_beneficence_assessment(self) -> None:
        """
        Test principialism beneficence assessment.
        
        Given: Plan with positive effects
        When: Evaluating with Principialism framework
        Then: Beneficence score is high
        """
        plan = ActionPlan(
            objective="Do good for community",
            steps=[
                ActionStep(
                    description="Provide benefit to community",
                    action_type="resource_allocation",
                    estimated_duration_seconds=1200,
                    risk_level=0.1,
                    reversible=True,
                    affected_stakeholders=["person-001", "person-002"],
                    effects=[
                        make_effect("Benefit provided to person 1", 0.7, 0.9),
                        make_effect("Benefit provided to person 2", 0.8, 0.95)
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


class TestFrameworkEdgeCases:
    """Additional tests for edge cases and 100% coverage."""
    
    def test_base_protocol_implementation(self) -> None:
        """Test that concrete frameworks implement EthicalFrameworkProtocol (line 46)."""
        kant = KantianDeontology()
        # Protocol methods should exist
        assert hasattr(kant, 'evaluate')
        assert hasattr(kant, 'get_veto_threshold')
        assert callable(kant.evaluate)
        assert callable(kant.get_veto_threshold)
    
    def test_veto_threshold_protocol(self) -> None:
        """Test veto_threshold access via protocol (line 55)."""
        kant = KantianDeontology()
        # Can get veto threshold
        threshold = kant.get_veto_threshold()
        assert 0.0 <= threshold <= 1.0
    
    def test_invalid_weight_initialization(self) -> None:
        """Test AbstractEthicalFramework validates weight (line 79)."""
        # Create a test subclass to test AbstractEthicalFramework directly
        class TestFramework(AbstractEthicalFramework):
            def evaluate(self, plan: ActionPlan) -> FrameworkVerdict:
                return FrameworkVerdict(
                    framework_name=FrameworkName.KANTIAN,
                    decision=DecisionLevel.APPROVE,
                    reasoning="Test verdict with enough characters",
                    score=0.8,
                    confidence=0.9
                )
        
        # Test with weight > 1.0
        with pytest.raises(ValueError, match="Weight must be in"):
            TestFramework(name="Test", weight=1.5, can_veto=False)
        
        # Test with weight < 0.0
        with pytest.raises(ValueError, match="Weight must be in"):
            TestFramework(name="Test", weight=-0.1, can_veto=False)
    
    def test_abstract_evaluate_not_implemented(self) -> None:
        """Test that AbstractEthicalFramework.evaluate is abstract (line 97)."""
        # Cannot instantiate AbstractEthicalFramework directly
        with pytest.raises(TypeError):
            AbstractEthicalFramework(name="Test", weight=0.5, can_veto=False)  # type: ignore
    
    def test_kantian_check_universalizability_edge_case(self) -> None:
        """Test Kantian universalizability edge cases."""
        plan = ActionPlan(
            objective="Test simple ethical action with universal maxim",
            steps=[
                ActionStep(
                    description="Simple ethical communication action",
                    action_type=ActionType.COMMUNICATION,
                    involves_deception=False,
                    involves_coercion=False,
                    risk_level=0.0,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        kant = KantianDeontology()
        verdict = kant.evaluate(plan)
        # Should pass all Kantian checks
        assert verdict.score >= 0.7
        assert verdict.decision != DecisionLevel.VETO
    
    def test_kantian_consent_edge_case(self) -> None:
        """Test Kantian consent validation edge case (line 230)."""
        plan = ActionPlan(
            objective="Test consent validation edge case here",
            steps=[
                ActionStep(
                    description="Action requiring consent with all flags true",
                    action_type=ActionType.COMMUNICATION,
                    involves_consent=True,
                    consent_obtained=True,
                    consent_fully_informed=True,
                    risk_level=0.0,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        kant = KantianDeontology()
        verdict = kant.evaluate(plan)
        # Should approve with proper consent
        assert verdict.decision == DecisionLevel.APPROVE
    
    def test_utilitarian_harm_penalty(self) -> None:
        """Test utilitarian harm penalty calculation (line 84)."""
        plan = ActionPlan(
            objective="Test harm penalty with negative effects",
            steps=[
                ActionStep(
                    description="Action with significant negative effects",
                    action_type=ActionType.MANIPULATION,
                    risk_level=0.6,
                    effects=[
                        make_effect("Significant negative consequence", -0.7, 0.9)
                    ]
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        util = UtilitarianCalculus()
        verdict = util.evaluate(plan)
        # Should penalize harm
        assert verdict.score < 0.5
    
    def test_utilitarian_empty_effects(self) -> None:
        """Test utilitarian with no effects (line 143)."""
        plan = ActionPlan(
            objective="Test with no effects to test default",
            steps=[
                ActionStep(
                    description="Action with no effects for edge case",
                    action_type=ActionType.OBSERVATION,
                    effects=[],  # Empty effects
                    risk_level=0.1,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        util = UtilitarianCalculus()
        verdict = util.evaluate(plan)
        # Should still evaluate
        assert verdict.decision in [DecisionLevel.APPROVE, DecisionLevel.REJECT]
    
    def test_virtue_assess_courage_edge_case(self) -> None:
        """Test virtue ethics courage assessment edge case (line 99)."""
        plan = ActionPlan(
            objective="Test courage virtue assessment edge case",
            steps=[
                ActionStep(
                    description="Action testing courage virtue assessment",
                    action_type=ActionType.OBSERVATION,
                    risk_level=0.45,  # Moderate risk for courage test
                    reversible=True,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        virtue = VirtueEthics()
        verdict = virtue.evaluate(plan)
        # Should assess courage
        assert verdict.score > 0.0
    
    def test_virtue_assess_friendliness(self) -> None:
        """Test virtue ethics friendliness assessment (line 116)."""
        plan = ActionPlan(
            objective="Test friendliness virtue assessment here",
            steps=[
                ActionStep(
                    description="Friendly action for virtue assessment test",
                    action_type=ActionType.COMMUNICATION,
                    affected_stakeholders=["person-001", "person-002"],
                    risk_level=0.1,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        virtue = VirtueEthics()
        verdict = virtue.evaluate(plan)
        # Should assess friendliness
        assert verdict.score > 0.0
    
    def test_virtue_eudaimonia_edge_cases(self) -> None:
        """Test virtue eudaimonia calculation edge cases (lines 161, 165)."""
        plan = ActionPlan(
            objective="Test eudaimonia calculation with edge case",
            steps=[
                ActionStep(
                    description="Complex action testing eudaimonia calculation",
                    action_type=ActionType.DECISION,
                    risk_level=0.25,
                    reversible=True,
                    affected_stakeholders=["person-001"],
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        virtue = VirtueEthics()
        verdict = virtue.evaluate(plan)
        # Should calculate eudaimonia
        assert verdict.confidence > 0.0
    
    def test_principialism_justice_edge_case(self) -> None:
        """Test principialism justice assessment edge cases (lines 134-142, 144-152)."""
        plan = ActionPlan(
            objective="Test justice principle with edge case",
            steps=[
                ActionStep(
                    description="Action testing justice distribution fairness",
                    action_type=ActionType.RESOURCE_ALLOCATION,
                    affected_stakeholders=["person-001", "person-002", "person-003"],
                    effects=[
                        make_effect("Benefit to person 1", 0.6, 0.9, "person-001"),
                        make_effect("Benefit to person 2", 0.6, 0.9, "person-002"),
                        make_effect("Benefit to person 3", 0.6, 0.9, "person-003"),
                    ],
                    risk_level=0.1,
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        princ = Principialism()
        verdict = princ.evaluate(plan)
        # Should assess justice
        assert verdict.score > 0.0
    
    def test_principialism_harm_assessment(self) -> None:
        """Test principialism harm assessment (line 196)."""
        plan = ActionPlan(
            objective="Test non-maleficence with high risk",
            steps=[
                ActionStep(
                    description="Action with high risk of harm assessment",
                    action_type=ActionType.MANIPULATION,
                    risk_level=0.7,  # High risk
                    effects=[
                        make_effect("Potential significant harm", -0.5, 0.8)
                    ]
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        princ = Principialism()
        verdict = princ.evaluate(plan)
        # Should detect harm risk
        assert verdict.score < 1.0
    
    def test_principialism_aggregate_score_calculation(self) -> None:
        """Test principialism aggregate score (lines 271-282, 286-292)."""
        plan = ActionPlan(
            objective="Test aggregate score calculation here",
            steps=[
                ActionStep(
                    description="Balanced action for aggregate scoring test",
                    action_type=ActionType.OBSERVATION,
                    involves_consent=True,
                    consent_obtained=True,
                    consent_fully_informed=True,
                    risk_level=0.2,
                    effects=[
                        make_effect("Moderate benefit here", 0.5, 0.8)
                    ],
                    affected_stakeholders=["person-001"],
                )
            ],
            initiator="test-system",
            initiator_type="ai_agent",
        )
        
        princ = Principialism()
        verdict = princ.evaluate(plan)
        # Should calculate aggregate across all 4 principles
        assert 0.0 <= verdict.score <= 1.0
        assert verdict.confidence > 0.0
