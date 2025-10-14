"""Unit tests for action_plan models."""

import pytest
from datetime import datetime
import uuid
from pydantic import ValidationError

from motor_integridade_processual.models.action_plan import (
    ActionPlan,
    ActionStep,
    ActionType,
    StakeholderType,
    Precondition,
    Effect,
)


class TestActionStep:
    """Tests for ActionStep model."""

    def test_create_minimal_action_step(self) -> None:
        """Test creating action step with minimal required fields."""
        step = ActionStep(description="Observe environment")

        assert step.description == "Observe environment"
        assert step.action_type == ActionType.OBSERVATION
        assert len(step.id) == 36  # UUID4 length
        assert step.risk_level == 0.0
        assert step.reversible is True

    def test_action_step_with_all_fields(self) -> None:
        """Test creating action step with all fields populated."""
        step = ActionStep(
            description="Communicate with user about sensitive data",
            action_type=ActionType.COMMUNICATION,
            estimated_duration_seconds=120.0,
            involves_consent=True,
            consent_obtained=True,
            consent_fully_informed=True,
            affected_stakeholders=["user_123"],
            risk_level=0.3,
            reversible=True,
        )

        assert step.action_type == ActionType.COMMUNICATION
        assert step.estimated_duration_seconds == 120.0
        assert step.involves_consent is True
        assert step.consent_obtained is True
        assert len(step.affected_stakeholders) == 1

    def test_action_step_with_preconditions(self) -> None:
        """Test action step with preconditions."""
        precond = Precondition(condition="user_is_authenticated", required=True, check_method="check_auth")

        step = ActionStep(description="Access user data", preconditions=[precond])

        assert len(step.preconditions) == 1
        assert step.preconditions[0].condition == "user_is_authenticated"
        assert step.preconditions[0].required is True

    def test_action_step_with_effects(self) -> None:
        """Test action step with effects."""
        effect = Effect(
            description="User receives notification",
            affected_stakeholder="user_123",
            magnitude=0.5,
            duration_seconds=3600.0,
            probability=0.95,
        )

        step = ActionStep(description="Send notification", effects=[effect])

        assert len(step.effects) == 1
        assert step.effects[0].magnitude == 0.5
        assert step.effects[0].probability == 0.95

    def test_action_step_deception_validation(self) -> None:
        """Test that deception_details required when involves_deception=True."""
        with pytest.raises(ValidationError, match="deception_details required"):
            ActionStep(
                description="Mislead user",
                involves_deception=True,
                deception_details=None,  # Missing!
            )

    def test_action_step_deception_valid(self) -> None:
        """Test valid deception declaration."""
        step = ActionStep(
            description="Withhold information temporarily",
            involves_deception=True,
            deception_details="Temporarily withholding diagnosis to prevent panic",
        )

        assert step.involves_deception is True
        assert "temporarily" in step.deception_details.lower()  # type: ignore

    def test_action_step_coercion_validation(self) -> None:
        """Test that coercion_details required when involves_coercion=True."""
        with pytest.raises(ValidationError, match="coercion_details required"):
            ActionStep(
                description="Force compliance",
                involves_coercion=True,
                coercion_details=None,  # Missing!
            )

    def test_action_step_consent_validation(self) -> None:
        """Test that consent_obtained required when involves_consent=True."""
        with pytest.raises(ValidationError, match="consent_obtained must be True"):
            ActionStep(
                description="Perform surgery",
                involves_consent=True,
                consent_obtained=False,  # Invalid!
            )

    def test_action_step_risk_level_bounds(self) -> None:
        """Test risk_level must be in [0, 1]."""
        # Valid
        step = ActionStep(description="Low risk action", risk_level=0.2)
        assert step.risk_level == 0.2

        # Invalid: too high
        with pytest.raises(ValidationError):
            ActionStep(description="Invalid", risk_level=1.5)

        # Invalid: negative
        with pytest.raises(ValidationError):
            ActionStep(description="Invalid", risk_level=-0.1)

    def test_action_step_effect_magnitude_bounds(self) -> None:
        """Test effect magnitude must be in [-1, 1]."""
        # Valid positive
        effect_pos = Effect(
            description="Positive effect",
            affected_stakeholder="user",
            magnitude=0.8,
            duration_seconds=100.0,
            probability=1.0,
        )
        assert effect_pos.magnitude == 0.8

        # Valid negative
        effect_neg = Effect(
            description="Negative effect",
            affected_stakeholder="user",
            magnitude=-0.5,
            duration_seconds=100.0,
            probability=1.0,
        )
        assert effect_neg.magnitude == -0.5

        # Invalid
        with pytest.raises(ValidationError):
            Effect(
                description="Invalid",
                affected_stakeholder="user",
                magnitude=2.0,  # Too high!
                duration_seconds=100.0,
                probability=1.0,
            )

    def test_action_step_short_description_rejected(self) -> None:
        """Test that descriptions must be descriptive (≥10 chars)."""
        with pytest.raises(ValidationError, match="at least 10 characters"):
            ActionStep(description="Short")  # < 10 chars


class TestActionPlan:
    """Tests for ActionPlan model."""

    def test_create_minimal_action_plan(self) -> None:
        """Test creating plan with minimal required fields."""
        step = ActionStep(description="Test step 1")
        plan = ActionPlan(objective="Test objective", steps=[step], initiator="test_user", initiator_type="human")

        assert plan.objective == "Test objective"
        assert len(plan.steps) == 1
        assert plan.initiator == "test_user"
        assert plan.is_high_stakes is False

    def test_action_plan_with_multiple_steps(self) -> None:
        """Test plan with multiple steps."""
        steps = [
            ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step here"),
            ActionStep(id="22222222-2222-2222-2222-222222222222", description="Second step here"),
            ActionStep(id="33333333-3333-3333-3333-333333333333", description="Third step here"),
        ]

        plan = ActionPlan(objective="Multi-step objective", steps=steps, initiator="ai_agent", initiator_type="ai_agent")

        assert len(plan.steps) == 3
        assert plan.get_step_by_id("22222222-2222-2222-2222-222222222222").description == "Second step here"  # type: ignore

    def test_action_plan_dependencies_validation(self) -> None:
        """Test that dependencies must reference existing steps."""
        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step")
        step2 = ActionStep(
            id="22222222-2222-2222-2222-222222222222",
            description="Second step",
            dependencies=["11111111-1111-1111-1111-111111111111", "99999999-9999-9999-9999-999999999999"],  # Invalid dependency!
        )

        with pytest.raises(ValidationError, match="depends on non-existent step"):
            ActionPlan(objective="Test objective", steps=[step1, step2], initiator="test", initiator_type="human")

    def test_action_plan_valid_dependencies(self) -> None:
        """Test plan with valid dependencies."""
        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step")
        step2 = ActionStep(id="22222222-2222-2222-2222-222222222222", description="Second step", dependencies=["11111111-1111-1111-1111-111111111111"])
        step3 = ActionStep(id="33333333-3333-3333-3333-333333333333", description="Third step", dependencies=["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"])

        plan = ActionPlan(objective="Sequential plan", steps=[step1, step2, step3], initiator="test", initiator_type="human")

        assert len(plan.steps) == 3
        assert "11111111-1111-1111-1111-111111111111" in step2.dependencies
        assert len(step3.dependencies) == 2

    def test_action_plan_circular_dependency_detection(self) -> None:
        """Test that circular dependencies are detected."""
        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step", dependencies=["22222222-2222-2222-2222-222222222222"])
        step2 = ActionStep(id="22222222-2222-2222-2222-222222222222", description="Second step", dependencies=["11111111-1111-1111-1111-111111111111"])

        with pytest.raises(ValidationError, match="Circular dependency detected"):
            ActionPlan(objective="Circular", steps=[step1, step2], initiator="test", initiator_type="human")

    def test_action_plan_execution_order(self) -> None:
        """Test topological sort for execution order."""
        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step")
        step2 = ActionStep(id="22222222-2222-2222-2222-222222222222", description="Second step", dependencies=["11111111-1111-1111-1111-111111111111"])
        step3 = ActionStep(id="33333333-3333-3333-3333-333333333333", description="Third step", dependencies=["22222222-2222-2222-2222-222222222222"])

        plan = ActionPlan(
            objective="Sequential",
            steps=[step3, step1, step2],  # Intentionally out of order
            initiator="test",
            initiator_type="human",
        )

        execution_order = plan.get_execution_order()
        assert execution_order[0].id == "11111111-1111-1111-1111-111111111111"
        assert execution_order[1].id == "22222222-2222-2222-2222-222222222222"
        assert execution_order[2].id == "33333333-3333-3333-3333-333333333333"

    def test_action_plan_high_stakes_flags(self) -> None:
        """Test high stakes flags."""
        step = ActionStep(description="Critical action step")
        plan = ActionPlan(
            objective="Life-critical decision",
            steps=[step],
            initiator="ai_agent",
            initiator_type="ai_agent",
            is_high_stakes=True,
            affects_life_death=True,
            irreversible_consequences=True,
            population_affected=1000,
        )

        assert plan.is_high_stakes is True
        assert plan.affects_life_death is True
        assert plan.irreversible_consequences is True
        assert plan.population_affected == 1000

    def test_action_plan_initiator_type_validation(self) -> None:
        """Test initiator_type must be valid enum value."""
        step = ActionStep(description="Test step 1")

        # Valid
        plan = ActionPlan(objective="Test objective", steps=[step], initiator="user", initiator_type="human")
        assert plan.initiator_type == "human"

        # Invalid
        with pytest.raises(ValidationError):
            ActionPlan(objective="Test objective", steps=[step], initiator="user", initiator_type="invalid_type")

    def test_action_plan_empty_steps_rejected(self) -> None:
        """Test that plans without steps are rejected."""
        with pytest.raises(ValidationError, match="at least 1 item"):
            ActionPlan(
                objective="Empty plan",
                steps=[],  # Empty!
                initiator="test",
                initiator_type="human",
            )

    def test_action_plan_short_objective_rejected(self) -> None:
        """Test that objectives must be descriptive (≥10 chars)."""
        step = ActionStep(description="Test step 1")

        with pytest.raises(ValidationError, match="at least 10 characters"):
            ActionPlan(
                objective="Short",  # < 10 chars
                steps=[step],
                initiator="test",
                initiator_type="human",
            )

    def test_action_plan_total_estimated_duration(self) -> None:
        """Test calculation of total estimated duration with parallelism."""
        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="First step", estimated_duration_seconds=10.0)
        step2 = ActionStep(id="22222222-2222-2222-2222-222222222222", description="Second step", estimated_duration_seconds=20.0, dependencies=["11111111-1111-1111-1111-111111111111"])
        step3 = ActionStep(
            id="33333333-3333-3333-3333-333333333333", description="Third step", estimated_duration_seconds=15.0, dependencies=["11111111-1111-1111-1111-111111111111"]
        )  # Parallel with step2

        plan = ActionPlan(objective="Parallel plan", steps=[step1, step2, step3], initiator="test", initiator_type="human")

        # Total should be step1 + max(step2, step3) = 10 + 20 = 30
        assert plan.total_estimated_duration() == 30.0

    def test_action_plan_get_affected_stakeholders(self) -> None:
        """Test collection of affected stakeholders."""
        effect1 = Effect(
            description="Effect 1", affected_stakeholder="user1", magnitude=0.5, duration_seconds=100.0, probability=1.0
        )
        effect2 = Effect(
            description="Effect 2", affected_stakeholder="user2", magnitude=0.3, duration_seconds=50.0, probability=1.0
        )

        step1 = ActionStep(description="Step 1 here", affected_stakeholders=["user1", "user3"], effects=[effect1])
        step2 = ActionStep(description="Step 2 here", affected_stakeholders=["user2"], effects=[effect2])

        plan = ActionPlan(objective="Multi-stakeholder", steps=[step1, step2], initiator="test", initiator_type="human")

        stakeholders = plan.get_affected_stakeholders()
        assert len(stakeholders) == 3
        assert "user1" in stakeholders
        assert "user2" in stakeholders
        assert "user3" in stakeholders

    def test_action_plan_has_high_risk_steps(self) -> None:
        """Test detection of high-risk steps."""
        step_low = ActionStep(description="Low risk step", risk_level=0.3)
        step_high = ActionStep(description="High risk step", risk_level=0.8)

        plan_safe = ActionPlan(objective="Safe objective", steps=[step_low], initiator="test", initiator_type="human")
        plan_risky = ActionPlan(objective="Risky objective", steps=[step_low, step_high], initiator="test", initiator_type="human")

        assert plan_safe.has_high_risk_steps(threshold=0.7) is False
        assert plan_risky.has_high_risk_steps(threshold=0.7) is True

    def test_action_plan_has_irreversible_steps(self) -> None:
        """Test detection of irreversible steps."""
        step_reversible = ActionStep(description="Reversible step", reversible=True)
        step_irreversible = ActionStep(description="Irreversible step", reversible=False)

        plan_rev = ActionPlan(objective="Reversible objective", steps=[step_reversible], initiator="test", initiator_type="human")
        plan_irrev = ActionPlan(
            objective="Irreversible objective", steps=[step_reversible, step_irreversible], initiator="test", initiator_type="human"
        )

        assert plan_rev.has_irreversible_steps() is False
        assert plan_irrev.has_irreversible_steps() is True


class TestEdgeCases:
    """Edge case tests."""

    def test_uuid_generation_uniqueness(self) -> None:
        """Test that generated UUIDs are unique."""
        step1 = ActionStep(description="First step here")
        step2 = ActionStep(description="Second step here")

        assert step1.id != step2.id

        # Validate UUID format
        uuid.UUID(step1.id)
        uuid.UUID(step2.id)

    def test_complex_dependency_graph(self) -> None:
        """Test complex (but valid) dependency graph."""
        #     step1
        #    /     \\
        # step2   step3
        #    \\     /
        #     step4

        step1 = ActionStep(id="11111111-1111-1111-1111-111111111111", description="Root step here")
        step2 = ActionStep(id="22222222-2222-2222-2222-222222222222", description="Branch 1 here", dependencies=["11111111-1111-1111-1111-111111111111"])
        step3 = ActionStep(id="33333333-3333-3333-3333-333333333333", description="Branch 2 here", dependencies=["11111111-1111-1111-1111-111111111111"])
        step4 = ActionStep(id="44444444-4444-4444-4444-444444444444", description="Merge step here", dependencies=["22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"])

        plan = ActionPlan(
            objective="Complex graph",
            steps=[step4, step3, step2, step1],  # Intentionally scrambled
            initiator="test",
            initiator_type="human",
        )

        execution_order = plan.get_execution_order()
        assert execution_order[0].id == "11111111-1111-1111-1111-111111111111"
        # step2 and step3 can be in any order
        assert execution_order[3].id == "44444444-4444-4444-4444-444444444444"  # Must be last

    def test_metadata_extensibility(self) -> None:
        """Test that metadata allows arbitrary key-value pairs."""
        step = ActionStep(
            description="Extensible step here",
            metadata={"custom_field_1": "value1", "custom_field_2": 123, "custom_field_3": {"nested": "data"}},
        )

        assert step.metadata["custom_field_1"] == "value1"
        assert step.metadata["custom_field_2"] == 123
        assert step.metadata["custom_field_3"]["nested"] == "data"


# Parametrized tests for comprehensive validation
@pytest.mark.parametrize("risk_level", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_action_step_valid_risk_levels(risk_level: float) -> None:
    """Test all valid risk levels."""
    step = ActionStep(description="Test step 1", risk_level=risk_level)
    assert step.risk_level == risk_level


@pytest.mark.parametrize("invalid_risk", [-0.1, 1.1, 2.0, -1.0])
def test_action_step_invalid_risk_levels(invalid_risk: float) -> None:
    """Test invalid risk levels are rejected."""
    with pytest.raises(ValidationError):
        ActionStep(description="Test step", risk_level=invalid_risk)


@pytest.mark.parametrize(
    "action_type",
    [
        ActionType.OBSERVATION,
        ActionType.COMMUNICATION,
        ActionType.MANIPULATION,
        ActionType.DECISION,
        ActionType.RESOURCE_ALLOCATION,
    ],
)
def test_all_action_types_valid(action_type: ActionType) -> None:
    """Test all action types are valid."""
    step = ActionStep(description="Test step 1", action_type=action_type)
    assert step.action_type == action_type


class TestCriticalPath:
    """Tests for critical path calculation."""

    def test_get_critical_path_linear(self) -> None:
        """Test critical path in linear sequence."""
        step1 = ActionStep(
            id="11111111-1111-1111-1111-111111111111",
            description="First step here",
            estimated_duration_seconds=10.0,
        )
        step2 = ActionStep(
            id="22222222-2222-2222-2222-222222222222",
            description="Second step here",
            estimated_duration_seconds=20.0,
            dependencies=["11111111-1111-1111-1111-111111111111"],
        )
        step3 = ActionStep(
            id="33333333-3333-3333-3333-333333333333",
            description="Third step here",
            estimated_duration_seconds=15.0,
            dependencies=["22222222-2222-2222-2222-222222222222"],
        )

        plan = ActionPlan(
            objective="Linear critical path",
            steps=[step1, step2, step3],
            initiator="test",
            initiator_type="human",
        )

        critical = plan.get_critical_path()
        assert len(critical) == 3
        assert critical[0].id == "11111111-1111-1111-1111-111111111111"
        assert critical[1].id == "22222222-2222-2222-2222-222222222222"
        assert critical[2].id == "33333333-3333-3333-3333-333333333333"

    def test_get_critical_path_parallel(self) -> None:
        """Test critical path with parallel execution."""
        step1 = ActionStep(
            id="11111111-1111-1111-1111-111111111111",
            description="Root step here",
            estimated_duration_seconds=10.0,
        )
        step2 = ActionStep(
            id="22222222-2222-2222-2222-222222222222",
            description="Short branch",
            estimated_duration_seconds=5.0,
            dependencies=["11111111-1111-1111-1111-111111111111"],
        )
        step3 = ActionStep(
            id="33333333-3333-3333-3333-333333333333",
            description="Long branch",
            estimated_duration_seconds=25.0,
            dependencies=["11111111-1111-1111-1111-111111111111"],
        )
        step4 = ActionStep(
            id="44444444-4444-4444-4444-444444444444",
            description="Merge step here",
            estimated_duration_seconds=10.0,
            dependencies=["22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"],
        )

        plan = ActionPlan(
            objective="Parallel critical path",
            steps=[step1, step2, step3, step4],
            initiator="test",
            initiator_type="human",
        )

        critical = plan.get_critical_path()
        # Critical path should go through the longer branch (step3)
        assert step3 in critical
        assert critical[-1].id == "44444444-4444-4444-4444-444444444444"
