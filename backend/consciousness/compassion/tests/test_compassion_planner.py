"""
Tests for Compassion Planner Module

Comprehensive test coverage for CompassionPlan and CompassionPlanner classes.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4

from compassion.event_detector import EventType, SufferingEvent
from compassion.compassion_planner import (
    CompassionPlan,
    CompassionPlanner,
    InterventionType,
)


class TestCompassionPlan:
    """Tests for CompassionPlan dataclass."""

    def test_compassion_plan_creation_success(self):
        """Test successful creation of CompassionPlan."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=8,
            description="System error"
        )

        plan = CompassionPlan(
            plan_id=uuid4(),
            event=event,
            intervention_type=InterventionType.ESCALATION,
            actions=["Action 1", "Action 2"],
            priority=9,
            estimated_duration_minutes=15
        )

        assert plan.event == event
        assert plan.intervention_type == InterventionType.ESCALATION
        assert len(plan.actions) == 2
        assert plan.priority == 9
        assert plan.estimated_duration_minutes == 15
        assert isinstance(plan.created_at, datetime)
        assert isinstance(plan.plan_id, UUID)

    def test_compassion_plan_with_resources_and_criteria(self):
        """Test CompassionPlan with resources and success criteria."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.CONFUSION,
            severity=5,
            description="Agent confused"
        )

        plan = CompassionPlan(
            plan_id=uuid4(),
            event=event,
            intervention_type=InterventionType.GUIDANCE,
            actions=["Provide help"],
            priority=6,
            estimated_duration_minutes=10,
            resources_required=["knowledge_base"],
            success_criteria=["Agent understands task"]
        )

        assert plan.resources_required == ["knowledge_base"]
        assert plan.success_criteria == ["Agent understands task"]

    def test_compassion_plan_priority_validation_too_low(self):
        """Test priority validation rejects values below 1."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=5,
            description="Test"
        )

        with pytest.raises(ValueError, match="Priority must be 1-10"):
            CompassionPlan(
                plan_id=uuid4(),
                event=event,
                intervention_type=InterventionType.MONITORING,
                actions=["Monitor"],
                priority=0,
                estimated_duration_minutes=5
            )

    def test_compassion_plan_priority_validation_too_high(self):
        """Test priority validation rejects values above 10."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=5,
            description="Test"
        )

        with pytest.raises(ValueError, match="Priority must be 1-10"):
            CompassionPlan(
                plan_id=uuid4(),
                event=event,
                intervention_type=InterventionType.MONITORING,
                actions=["Monitor"],
                priority=11,
                estimated_duration_minutes=5
            )

    def test_compassion_plan_priority_must_be_int(self):
        """Test priority validation rejects non-integer values."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=5,
            description="Test"
        )

        with pytest.raises(ValueError, match="Priority must be int"):
            CompassionPlan(
                plan_id=uuid4(),
                event=event,
                intervention_type=InterventionType.MONITORING,
                actions=["Monitor"],
                priority=5.5,
                estimated_duration_minutes=5
            )

    def test_compassion_plan_intervention_type_must_be_enum(self):
        """Test intervention_type validation rejects strings."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=5,
            description="Test"
        )

        with pytest.raises(TypeError, match="intervention_type must be InterventionType enum"):
            CompassionPlan(
                plan_id=uuid4(),
                event=event,
                intervention_type="escalation",  # String instead of enum
                actions=["Monitor"],
                priority=5,
                estimated_duration_minutes=5
            )

    def test_compassion_plan_with_metadata(self):
        """Test CompassionPlan with custom metadata."""
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.ISOLATION,
            severity=7,
            description="No connections"
        )

        metadata = {"source": "network_monitor", "region": "us-west"}
        plan = CompassionPlan(
            plan_id=uuid4(),
            event=event,
            intervention_type=InterventionType.RESOURCE_ALLOCATION,
            actions=["Restore connections"],
            priority=8,
            estimated_duration_minutes=25,
            metadata=metadata
        )

        assert plan.metadata == metadata


class TestCompassionPlannerInit:
    """Tests for CompassionPlanner initialization."""

    def test_compassion_planner_initialization(self):
        """Test CompassionPlanner initializes correctly."""
        planner = CompassionPlanner()
        assert planner._plans == []

    def test_compassion_planner_repr(self):
        """Test CompassionPlanner string representation."""
        planner = CompassionPlanner()
        assert repr(planner) == "CompassionPlanner(plans=0)"


class TestPlanIntervention:
    """Tests for intervention planning."""

    def test_plan_intervention_for_high_severity_distress(self):
        """Test planning for high-severity distress event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=9,
            description="Critical system error"
        )

        plan = planner.plan_intervention(event)

        assert plan.event == event
        assert plan.intervention_type == InterventionType.ESCALATION
        assert any("alert human operator" in action.lower() for action in plan.actions)
        assert plan.priority == 10  # 9 + 1 (distress bonus) = 10
        assert len(plan.resources_required) > 0
        assert len(plan.success_criteria) > 0

    def test_plan_intervention_for_medium_severity_distress(self):
        """Test planning for medium-severity distress event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=6,
            description="System error"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.IMMEDIATE_SUPPORT
        assert "recovery" in " ".join(plan.actions).lower()
        assert 5 <= plan.priority <= 8

    def test_plan_intervention_for_low_severity_distress(self):
        """Test planning for low-severity distress event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=3,
            description="Minor error"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.MONITORING
        assert any("monitor" in action.lower() for action in plan.actions)
        assert plan.priority <= 5

    def test_plan_intervention_for_high_severity_confusion(self):
        """Test planning for high-severity confusion event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.CONFUSION,
            severity=8,
            description="Completely confused"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.GUIDANCE
        assert any("clarification" in action.lower() for action in plan.actions)
        assert "knowledge_base" in plan.resources_required

    def test_plan_intervention_for_medium_severity_confusion(self):
        """Test planning for medium-severity confusion event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.CONFUSION,
            severity=6,
            description="Somewhat confused"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.GUIDANCE
        assert any("help" in action.lower() for action in plan.actions)

    def test_plan_intervention_for_low_severity_confusion(self):
        """Test planning for low-severity confusion event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.CONFUSION,
            severity=3,
            description="Minor confusion"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.MONITORING

    def test_plan_intervention_for_high_severity_isolation(self):
        """Test planning for high-severity isolation event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.ISOLATION,
            severity=9,
            description="Completely isolated"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.RESOURCE_ALLOCATION
        assert any("connection" in action.lower() for action in plan.actions)
        assert "network_tools" in plan.resources_required

    def test_plan_intervention_for_medium_severity_isolation(self):
        """Test planning for medium-severity isolation event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.ISOLATION,
            severity=6,
            description="Connection issues"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.IMMEDIATE_SUPPORT
        assert any("reconnection" in action.lower() for action in plan.actions)

    def test_plan_intervention_for_low_severity_isolation(self):
        """Test planning for low-severity isolation event."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.ISOLATION,
            severity=3,
            description="Temporary disconnection"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.MONITORING

    def test_plan_intervention_for_unknown_event_type(self):
        """Test planning for unknown event type."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.UNKNOWN,
            severity=5,
            description="Unknown issue"
        )

        plan = planner.plan_intervention(event)

        assert plan.intervention_type == InterventionType.MONITORING
        assert any("monitor" in action.lower() for action in plan.actions)

    def test_plan_intervention_stores_plan(self):
        """Test that created plans are stored."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=7,
            description="Error"
        )

        plan = planner.plan_intervention(event)

        assert len(planner._plans) == 1
        assert planner._plans[0] == plan


class TestCategorizeSeverity:
    """Tests for severity categorization."""

    def test_categorize_severity_high(self):
        """Test high severity categorization (8-10)."""
        planner = CompassionPlanner()

        assert planner._categorize_severity(8) == "high_severity"
        assert planner._categorize_severity(9) == "high_severity"
        assert planner._categorize_severity(10) == "high_severity"

    def test_categorize_severity_medium(self):
        """Test medium severity categorization (5-7)."""
        planner = CompassionPlanner()

        assert planner._categorize_severity(5) == "medium_severity"
        assert planner._categorize_severity(6) == "medium_severity"
        assert planner._categorize_severity(7) == "medium_severity"

    def test_categorize_severity_low(self):
        """Test low severity categorization (1-4)."""
        planner = CompassionPlanner()

        assert planner._categorize_severity(1) == "low_severity"
        assert planner._categorize_severity(2) == "low_severity"
        assert planner._categorize_severity(3) == "low_severity"
        assert planner._categorize_severity(4) == "low_severity"


class TestCalculatePriority:
    """Tests for priority calculation."""

    def test_calculate_priority_base_severity(self):
        """Test priority equals severity for base cases."""
        planner = CompassionPlanner()

        priority = planner._calculate_priority(5, EventType.CONFUSION)
        assert priority == 5

    def test_calculate_priority_distress_bonus(self):
        """Test distress events get +1 priority."""
        planner = CompassionPlanner()

        priority = planner._calculate_priority(5, EventType.DISTRESS)
        assert priority == 6

    def test_calculate_priority_isolation_bonus(self):
        """Test isolation events get +0.5 priority (rounded)."""
        planner = CompassionPlanner()

        priority = planner._calculate_priority(5, EventType.ISOLATION)
        assert priority == 5  # 5.5 rounded down to 5

    def test_calculate_priority_clamped_at_max(self):
        """Test priority is clamped at 10."""
        planner = CompassionPlanner()

        priority = planner._calculate_priority(10, EventType.DISTRESS)
        assert priority == 10  # Would be 11, clamped to 10

    def test_calculate_priority_clamped_at_min(self):
        """Test priority is clamped at 1."""
        planner = CompassionPlanner()

        # This shouldn't happen with valid severity, but test the clamp
        priority = planner._calculate_priority(1, EventType.CONFUSION)
        assert priority >= 1


class TestGetPlan:
    """Tests for retrieving plans by ID."""

    def test_get_plan_found(self):
        """Test retrieving existing plan by ID."""
        planner = CompassionPlanner()
        event = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=7,
            description="Error"
        )

        plan = planner.plan_intervention(event)
        retrieved = planner.get_plan(plan.plan_id)

        assert retrieved == plan

    def test_get_plan_not_found(self):
        """Test retrieving non-existent plan returns None."""
        planner = CompassionPlanner()

        retrieved = planner.get_plan(uuid4())

        assert retrieved is None

    def test_get_plan_multiple_plans(self):
        """Test retrieving specific plan from multiple plans."""
        planner = CompassionPlanner()
        event1 = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.DISTRESS,
            severity=7,
            description="Error 1"
        )
        event2 = SufferingEvent(
            agent_id=uuid4(),
            event_type=EventType.CONFUSION,
            severity=5,
            description="Confusion"
        )

        plan1 = planner.plan_intervention(event1)
        plan2 = planner.plan_intervention(event2)

        assert planner.get_plan(plan1.plan_id) == plan1
        assert planner.get_plan(plan2.plan_id) == plan2


class TestGetPlansForAgent:
    """Tests for retrieving plans for specific agents."""

    def test_get_plans_for_agent_empty(self):
        """Test getting plans for agent with no plans."""
        planner = CompassionPlanner()

        plans = planner.get_plans_for_agent(uuid4())

        assert plans == []

    def test_get_plans_for_agent_filters_by_agent_id(self):
        """Test plans are filtered by agent ID."""
        planner = CompassionPlanner()
        agent1 = uuid4()
        agent2 = uuid4()

        event1 = SufferingEvent(agent1, EventType.DISTRESS, 7, "Agent 1 error")
        event2 = SufferingEvent(agent2, EventType.CONFUSION, 5, "Agent 2 confused")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)

        plans = planner.get_plans_for_agent(agent1)

        assert len(plans) == 1
        assert plans[0].event.agent_id == agent1

    def test_get_plans_for_agent_sorted_by_priority(self):
        """Test plans are sorted by priority descending."""
        planner = CompassionPlanner()
        agent_id = uuid4()

        event1 = SufferingEvent(agent_id, EventType.DISTRESS, 5, "Low priority")
        event2 = SufferingEvent(agent_id, EventType.DISTRESS, 9, "High priority")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)

        plans = planner.get_plans_for_agent(agent_id)

        assert len(plans) == 2
        assert plans[0].priority > plans[1].priority

    def test_get_plans_for_agent_active_only(self):
        """Test getting only active (high-priority) plans."""
        planner = CompassionPlanner()
        agent_id = uuid4()

        event1 = SufferingEvent(agent_id, EventType.DISTRESS, 5, "Low priority")
        event2 = SufferingEvent(agent_id, EventType.DISTRESS, 9, "High priority")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)

        plans = planner.get_plans_for_agent(agent_id, active_only=True)

        assert len(plans) == 1
        assert plans[0].priority >= 7


class TestGetHighPriorityPlans:
    """Tests for retrieving high-priority plans."""

    def test_get_high_priority_plans_default_threshold(self):
        """Test getting high-priority plans with default threshold."""
        planner = CompassionPlanner()

        event1 = SufferingEvent(uuid4(), EventType.DISTRESS, 5, "Low")
        event2 = SufferingEvent(uuid4(), EventType.DISTRESS, 9, "High")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)

        plans = planner.get_high_priority_plans()

        assert len(plans) == 1
        assert plans[0].priority >= 7

    def test_get_high_priority_plans_custom_threshold(self):
        """Test getting high-priority plans with custom threshold."""
        planner = CompassionPlanner()

        event1 = SufferingEvent(uuid4(), EventType.DISTRESS, 5, "Low")
        event2 = SufferingEvent(uuid4(), EventType.DISTRESS, 6, "Medium")
        event3 = SufferingEvent(uuid4(), EventType.DISTRESS, 9, "High")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)
        planner.plan_intervention(event3)

        plans = planner.get_high_priority_plans(threshold=6)

        # event1: priority 6 (5+1), event2: priority 7 (6+1), event3: priority 10 (9+1)
        # threshold=6 includes 6, 7, 10 = 3 plans
        assert len(plans) == 3

    def test_get_high_priority_plans_sorted_by_priority(self):
        """Test high-priority plans are sorted descending."""
        planner = CompassionPlanner()

        event1 = SufferingEvent(uuid4(), EventType.DISTRESS, 7, "Medium-high")
        event2 = SufferingEvent(uuid4(), EventType.DISTRESS, 9, "Critical")

        planner.plan_intervention(event1)
        planner.plan_intervention(event2)

        plans = planner.get_high_priority_plans()

        assert plans[0].priority > plans[1].priority

    def test_get_high_priority_plans_empty(self):
        """Test getting high-priority plans when none exist."""
        planner = CompassionPlanner()

        plans = planner.get_high_priority_plans()

        assert plans == []


class TestClearPlans:
    """Tests for clearing plans."""

    def test_clear_plans_empties_list(self):
        """Test clear_plans removes all plans."""
        planner = CompassionPlanner()
        event = SufferingEvent(uuid4(), EventType.DISTRESS, 7, "Error")

        planner.plan_intervention(event)
        assert len(planner._plans) == 1

        planner.clear_plans()

        assert len(planner._plans) == 0

    def test_clear_plans_on_empty_planner(self):
        """Test clear_plans on empty planner doesn't error."""
        planner = CompassionPlanner()

        planner.clear_plans()

        assert len(planner._plans) == 0


class TestCompassionPlannerIntegration:
    """Integration tests for CompassionPlanner."""

    def test_full_workflow_single_event(self):
        """Test complete workflow: event -> plan -> retrieve."""
        planner = CompassionPlanner()
        agent_id = uuid4()

        event = SufferingEvent(agent_id, EventType.DISTRESS, 8, "Critical error")
        plan = planner.plan_intervention(event)

        # Retrieve by ID
        retrieved = planner.get_plan(plan.plan_id)
        assert retrieved == plan

        # Retrieve by agent
        agent_plans = planner.get_plans_for_agent(agent_id)
        assert len(agent_plans) == 1

        # Retrieve high-priority
        high_priority = planner.get_high_priority_plans()
        assert plan in high_priority

    def test_full_workflow_multiple_agents(self):
        """Test workflow with multiple agents and priorities."""
        planner = CompassionPlanner()
        agent1 = uuid4()
        agent2 = uuid4()

        # Agent 1: High-severity distress
        event1 = SufferingEvent(agent1, EventType.DISTRESS, 9, "Critical")
        plan1 = planner.plan_intervention(event1)

        # Agent 2: Low-severity confusion
        event2 = SufferingEvent(agent2, EventType.CONFUSION, 3, "Minor confusion")
        plan2 = planner.plan_intervention(event2)

        # Check agent-specific plans
        assert len(planner.get_plans_for_agent(agent1)) == 1
        assert len(planner.get_plans_for_agent(agent2)) == 1

        # Check priority filtering
        high_priority = planner.get_high_priority_plans()
        assert plan1 in high_priority
        assert plan2 not in high_priority

    def test_full_workflow_with_clear(self):
        """Test workflow including clearing plans."""
        planner = CompassionPlanner()

        event = SufferingEvent(uuid4(), EventType.ISOLATION, 7, "Disconnected")
        planner.plan_intervention(event)

        assert len(planner._plans) == 1

        planner.clear_plans()

        assert len(planner._plans) == 0
        assert planner.get_high_priority_plans() == []
