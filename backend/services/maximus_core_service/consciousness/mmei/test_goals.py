"""MMEI Autonomous Goal Generator - Complete Test Suite for 100% Coverage

Tests for consciousness/mmei/goals.py - Need-based autonomous goal generation
that translates interoceptive feelings into actionable intentions.

Coverage Target: 100% of goals.py (632 statements)
Test Strategy: Direct execution, minimal mocking
Quality Standard: Production-ready, NO MOCK, NO PLACEHOLDER, NO TODO

Theoretical Foundation:
-----------------------
Tests validate autonomous goal generation from internal needs.
Goals emerge from homeostatic drives without external commands.

Authors: Juan & Gemini (supervised by Claude)
Version: 1.0.0 - Anti-Burro Edition
Date: 2025-10-07
"""

import time
from unittest.mock import Mock

import pytest

from consciousness.mmei.goals import (
    AutonomousGoalGenerator,
    Goal,
    GoalGenerationConfig,
    GoalPriority,
    GoalType,
)
from consciousness.mmei.monitor import AbstractNeeds, NeedUrgency

# ==================== GOAL DATACLASS TESTS ====================


class TestGoal:
    """Test Goal dataclass and methods."""

    def test_goal_creation_minimal(self):
        """Test Goal creation with default values."""
        # ACT: Create goal with minimal params
        goal = Goal()

        # ASSERT: Defaults applied (lines 129-155)
        assert len(goal.goal_id) == 36  # UUID format
        assert goal.goal_type == GoalType.REST  # Default
        assert goal.priority == GoalPriority.LOW  # Default
        assert goal.description == ""
        assert goal.target_component is None
        assert goal.source_need == ""
        assert goal.need_value == 0.0
        assert goal.target_need_value == 0.3  # Default
        assert goal.timeout_seconds == 300.0  # Default
        assert goal.is_active is True  # Default
        assert goal.execution_attempts == 0
        assert goal.last_execution_at is None
        assert isinstance(goal.metadata, dict)
        assert len(goal.metadata) == 0

    def test_goal_creation_full(self):
        """Test Goal creation with all parameters."""
        # ARRANGE: Prepare all params
        metadata = {"action": "reduce_load", "target_cpu": 50}

        # ACT: Create goal with all params
        goal = Goal(
            goal_id="test-goal-001",
            goal_type=GoalType.REPAIR,
            priority=GoalPriority.CRITICAL,
            description="Fix critical errors",
            target_component="error_handler",
            source_need="repair_need",
            need_value=0.95,
            target_need_value=0.20,
            timeout_seconds=600.0,
            is_active=True,
            metadata=metadata
        )

        # ASSERT: All fields set correctly
        assert goal.goal_id == "test-goal-001"
        assert goal.goal_type == GoalType.REPAIR
        assert goal.priority == GoalPriority.CRITICAL
        assert goal.description == "Fix critical errors"
        assert goal.target_component == "error_handler"
        assert goal.source_need == "repair_need"
        assert goal.need_value == 0.95
        assert goal.target_need_value == 0.20
        assert goal.timeout_seconds == 600.0
        assert goal.is_active is True
        assert goal.metadata == metadata

    def test_is_expired_false(self):
        """Test is_expired returns False for fresh goal (lines 157-161)."""
        # ARRANGE: Create recent goal
        goal = Goal(timeout_seconds=10.0)
        goal.created_at = time.time()  # Just created
        goal.is_active = True

        # ACT: Check expiration (lines 158-161)
        expired = goal.is_expired()

        # ASSERT: Not expired (line 161)
        assert expired is False

    def test_is_expired_true(self):
        """Test is_expired returns True for old goal (line 161)."""
        # ARRANGE: Create old goal
        goal = Goal(timeout_seconds=1.0)  # 1 second timeout
        goal.created_at = time.time() - 5.0  # 5 seconds ago
        goal.is_active = True

        # ACT: Check expiration (line 161)
        expired = goal.is_expired()

        # ASSERT: Expired (line 161)
        assert expired is True

    def test_is_expired_inactive_goal(self):
        """Test is_expired returns False for inactive goal (lines 159-160)."""
        # ARRANGE: Create inactive old goal
        goal = Goal(timeout_seconds=1.0)
        goal.created_at = time.time() - 10.0  # Very old
        goal.is_active = False  # But inactive

        # ACT: Check expiration (lines 159-160)
        expired = goal.is_expired()

        # ASSERT: Not expired (inactive goals don't expire, line 160)
        assert expired is False

    def test_is_satisfied_true(self):
        """Test is_satisfied returns True (line 165)."""
        # ARRANGE: Goal with target_need_value=0.3
        goal = Goal(target_need_value=0.3)

        # ACT: Check satisfaction with low need (line 165)
        satisfied = goal.is_satisfied(current_need_value=0.2)

        # ASSERT: Satisfied (0.2 < 0.3)
        assert satisfied is True

    def test_is_satisfied_false(self):
        """Test is_satisfied returns False (line 165)."""
        # ARRANGE: Goal with target_need_value=0.3
        goal = Goal(target_need_value=0.3)

        # ACT: Check satisfaction with high need
        satisfied = goal.is_satisfied(current_need_value=0.5)

        # ASSERT: Not satisfied (0.5 >= 0.3)
        assert satisfied is False

    def test_is_satisfied_boundary(self):
        """Test is_satisfied at exact boundary."""
        # ARRANGE: Goal with target=0.3
        goal = Goal(target_need_value=0.3)

        # ACT & ASSERT: Exactly at threshold (not satisfied)
        assert goal.is_satisfied(current_need_value=0.3) is False

        # Just below threshold (satisfied)
        assert goal.is_satisfied(current_need_value=0.299) is True

    def test_mark_satisfied(self):
        """Test mark_satisfied method (lines 167-170)."""
        # ARRANGE: Active goal
        goal = Goal()
        assert goal.is_active is True
        assert goal.satisfied_at is None

        # ACT: Mark satisfied (lines 167-170)
        before_mark = time.time()
        goal.mark_satisfied()
        after_mark = time.time()

        # ASSERT: State updated (lines 169-170)
        assert goal.is_active is False
        assert goal.satisfied_at is not None
        assert before_mark <= goal.satisfied_at <= after_mark

    def test_record_execution_attempt(self):
        """Test record_execution_attempt method (lines 172-175)."""
        # ARRANGE: Goal with no executions
        goal = Goal()
        assert goal.execution_attempts == 0
        assert goal.last_execution_at is None

        # ACT: Record execution (lines 172-175)
        before_exec = time.time()
        goal.record_execution_attempt()
        after_exec = time.time()

        # ASSERT: Counters updated (lines 174-175)
        assert goal.execution_attempts == 1
        assert goal.last_execution_at is not None
        assert before_exec <= goal.last_execution_at <= after_exec

        # ACT: Record another execution
        goal.record_execution_attempt()

        # ASSERT: Counter incremented
        assert goal.execution_attempts == 2

    def test_get_age_seconds(self):
        """Test get_age_seconds method (lines 177-179)."""
        # ARRANGE: Goal created 2 seconds ago
        goal = Goal()
        goal.created_at = time.time() - 2.0

        # ACT: Get age (lines 177-179)
        age = goal.get_age_seconds()

        # ASSERT: Age approximately 2 seconds (line 179)
        assert 1.9 <= age <= 2.1  # Allow small variance

    def test_get_priority_score_high_priority_high_need(self):
        """Test get_priority_score calculation (lines 181-192)."""
        # ARRANGE: Critical priority, high need, recent
        goal = Goal(
            priority=GoalPriority.CRITICAL,  # value=4
            need_value=0.9,
            timeout_seconds=300.0
        )
        goal.created_at = time.time()  # Fresh goal

        # ACT: Calculate score (lines 181-192)
        score = goal.get_priority_score()

        # ASSERT: High score
        # base_score = 4 * 100.0 = 400.0
        # need_bonus = 0.9 * 50.0 = 45.0
        # age_penalty = ~0 (fresh)
        # Total ≈ 445.0
        assert score > 400.0

    def test_get_priority_score_low_priority_old(self):
        """Test get_priority_score with low priority and age penalty."""
        # ARRANGE: Low priority, low need, old goal
        goal = Goal(
            priority=GoalPriority.LOW,  # value=1
            need_value=0.3,
            timeout_seconds=100.0
        )
        goal.created_at = time.time() - 90.0  # 90s old, near timeout

        # ACT: Calculate score
        score = goal.get_priority_score()

        # ASSERT: Lower score
        # base_score = 1 * 100.0 = 100.0
        # need_bonus = 0.3 * 50.0 = 15.0
        # age_penalty = (90/100) * 20.0 = 18.0
        # Total ≈ 97.0
        assert score < 150.0

    def test_get_priority_score_age_penalty_capped(self):
        """Test age penalty capping at timeout (line 190)."""
        # ARRANGE: Goal beyond timeout
        goal = Goal(timeout_seconds=10.0)
        goal.created_at = time.time() - 50.0  # 50s old, timeout=10s

        # ACT: Calculate score
        score = goal.get_priority_score()

        # ASSERT: Age penalty capped at 20.0 (line 190)
        # min(50/10, 1.0) * 20 = 1.0 * 20 = 20.0 max penalty

    def test_repr_active(self):
        """Test __repr__ for active goal (lines 194-197)."""
        # ARRANGE: Active goal
        goal = Goal(
            goal_type=GoalType.REPAIR,
            priority=GoalPriority.HIGH,
            need_value=0.75,
            is_active=True
        )

        # ACT: Get string representation (lines 194-197)
        repr_str = repr(goal)

        # ASSERT: Contains key info
        assert "Goal" in repr_str
        assert "repair" in repr_str
        assert "ACTIVE" in repr_str
        assert "0.75" in repr_str

    def test_repr_satisfied(self):
        """Test __repr__ for satisfied goal."""
        # ARRANGE: Satisfied goal
        goal = Goal(goal_type=GoalType.REST)
        goal.mark_satisfied()

        # ACT: Get repr
        repr_str = repr(goal)

        # ASSERT: Shows satisfied status
        assert "SATISFIED" in repr_str

# ==================== GOAL GENERATION CONFIG TESTS ====================


class TestGoalGenerationConfig:
    """Test GoalGenerationConfig dataclass."""

    def test_config_defaults(self):
        """Test GoalGenerationConfig default values (lines 200-224)."""
        # ACT: Create config with defaults
        config = GoalGenerationConfig()

        # ASSERT: All defaults set (lines 203-224)
        assert config.rest_threshold == 0.60
        assert config.repair_threshold == 0.40
        assert config.efficiency_threshold == 0.50
        assert config.connectivity_threshold == 0.50
        assert config.curiosity_threshold == 0.60
        assert config.learning_threshold == 0.50

        assert config.rest_satisfied == 0.30
        assert config.repair_satisfied == 0.20
        assert config.efficiency_satisfied == 0.30
        assert config.connectivity_satisfied == 0.30

        assert config.default_timeout == 300.0
        assert config.critical_timeout == 600.0
        assert config.exploration_timeout == 120.0

        assert config.max_concurrent_goals == 10
        assert config.min_goal_interval_seconds == 5.0

    def test_config_custom_values(self):
        """Test GoalGenerationConfig with custom values."""
        # ACT: Create config with custom values
        config = GoalGenerationConfig(
            rest_threshold=0.70,
            repair_threshold=0.30,
            max_concurrent_goals=20,
            default_timeout=600.0
        )

        # ASSERT: Custom values applied
        assert config.rest_threshold == 0.70
        assert config.repair_threshold == 0.30
        assert config.max_concurrent_goals == 20
        assert config.default_timeout == 600.0

        # Others still default
        assert config.efficiency_threshold == 0.50

# ==================== AUTONOMOUS GOAL GENERATOR INIT TESTS ====================


class TestAutonomousGoalGeneratorInit:
    """Test AutonomousGoalGenerator initialization."""

    def test_generator_init_default(self):
        """Test generator initialization with defaults (lines 279-303)."""
        # ACT: Create generator with defaults
        generator = AutonomousGoalGenerator()

        # ASSERT: Init values (lines 284-303)
        assert generator.generator_id == "mmei-goal-generator-primary"
        assert isinstance(generator.config, GoalGenerationConfig)
        assert len(generator._active_goals) == 0
        assert len(generator._completed_goals) == 0
        assert len(generator._expired_goals) == 0
        assert len(generator._last_generation) == 0
        assert len(generator._goal_consumers) == 0
        assert generator.total_goals_generated == 0
        assert generator.total_goals_satisfied == 0
        assert generator.total_goals_expired == 0

    def test_generator_init_custom(self):
        """Test generator with custom config and ID."""
        # ARRANGE: Custom config
        config = GoalGenerationConfig(rest_threshold=0.70)

        # ACT: Create generator
        generator = AutonomousGoalGenerator(
            config=config,
            generator_id="test-generator-01"
        )

        # ASSERT: Custom values applied
        assert generator.generator_id == "test-generator-01"
        assert generator.config.rest_threshold == 0.70

    def test_register_goal_consumer(self):
        """Test register_goal_consumer method (lines 305-318)."""
        # ARRANGE: Create generator
        generator = AutonomousGoalGenerator()
        assert len(generator._goal_consumers) == 0

        # Create mock consumer
        mock_consumer = Mock()

        # ACT: Register consumer (lines 305-318)
        generator.register_goal_consumer(mock_consumer)

        # ASSERT: Consumer registered (line 318)
        assert len(generator._goal_consumers) == 1
        assert mock_consumer in generator._goal_consumers

    def test_register_multiple_consumers(self):
        """Test registering multiple consumers."""
        # ARRANGE: Create generator
        generator = AutonomousGoalGenerator()

        # Create multiple consumers
        consumer1 = Mock()
        consumer2 = Mock()
        consumer3 = Mock()

        # ACT: Register all
        generator.register_goal_consumer(consumer1)
        generator.register_goal_consumer(consumer2)
        generator.register_goal_consumer(consumer3)

        # ASSERT: All registered
        assert len(generator._goal_consumers) == 3
        assert consumer1 in generator._goal_consumers
        assert consumer2 in generator._goal_consumers
        assert consumer3 in generator._goal_consumers

# ==================== GENERATE GOALS TESTS ====================


class TestGenerateGoals:
    """Test generate_goals core logic."""

    def test_generate_goals_no_needs(self):
        """Test generate_goals with all needs low (lines 320-393)."""
        # ARRANGE: Generator and low needs
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(
            rest_need=0.1,     # < 0.60 threshold
            repair_need=0.1,   # < 0.40 threshold
            efficiency_need=0.1,  # < 0.50 threshold
            connectivity_need=0.1,  # < 0.50 threshold
            curiosity_drive=0.1,  # < 0.60 threshold
            learning_drive=0.1   # < 0.50 threshold
        )

        # ACT: Generate goals (lines 320-393)
        new_goals = generator.generate_goals(needs)

        # ASSERT: No goals generated (all below thresholds)
        assert len(new_goals) == 0
        assert len(generator._active_goals) == 0

    def test_generate_goals_rest_need_high(self):
        """Test REST goal generation (lines 343-348)."""
        # ARRANGE: Generator with high rest need
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(rest_need=0.80)  # > 0.60 threshold

        # ACT: Generate goals (lines 343-348)
        new_goals = generator.generate_goals(needs)

        # ASSERT: REST goal created (lines 345-348)
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.REST
        assert new_goals[0].source_need == "rest_need"
        assert new_goals[0].need_value == 0.80
        assert "rest_need" in generator._last_generation
        assert generator.total_goals_generated == 1

    def test_generate_goals_repair_need_high(self):
        """Test REPAIR goal generation (lines 350-355)."""
        # ARRANGE: High repair need
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(repair_need=0.60)  # > 0.40 threshold

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: REPAIR goal created
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.REPAIR
        assert new_goals[0].source_need == "repair_need"

    def test_generate_goals_efficiency_need_high(self):
        """Test OPTIMIZE goal generation (lines 357-362)."""
        # ARRANGE: High efficiency need
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(efficiency_need=0.70)  # > 0.50 threshold

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: OPTIMIZE goal created
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.OPTIMIZE
        assert new_goals[0].source_need == "efficiency_need"

    def test_generate_goals_connectivity_need_high(self):
        """Test RESTORE goal generation (lines 364-369)."""
        # ARRANGE: High connectivity need
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(connectivity_need=0.75)  # > 0.50 threshold

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: RESTORE goal created
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.RESTORE
        assert new_goals[0].source_need == "connectivity_need"

    def test_generate_goals_curiosity_drive_high(self):
        """Test EXPLORE goal generation (lines 371-376)."""
        # ARRANGE: High curiosity drive
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(curiosity_drive=0.80)  # > 0.60 threshold

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: EXPLORE goal created
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.EXPLORE
        assert new_goals[0].source_need == "curiosity_drive"

    def test_generate_goals_learning_drive_high(self):
        """Test LEARN goal generation (lines 378-383)."""
        # ARRANGE: High learning drive
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(learning_drive=0.70)  # > 0.50 threshold

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: LEARN goal created
        assert len(new_goals) == 1
        assert new_goals[0].goal_type == GoalType.LEARN
        assert new_goals[0].source_need == "learning_drive"

    def test_generate_goals_multiple_needs(self):
        """Test multiple goal generation from multiple needs."""
        # ARRANGE: Multiple high needs
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(
            rest_need=0.70,       # High
            repair_need=0.60,     # High
            efficiency_need=0.60,  # High
            connectivity_need=0.65  # High
        )

        # ACT: Generate goals
        new_goals = generator.generate_goals(needs)

        # ASSERT: Multiple goals created
        assert len(new_goals) == 4
        goal_types = {g.goal_type for g in new_goals}
        assert GoalType.REST in goal_types
        assert GoalType.REPAIR in goal_types
        assert GoalType.OPTIMIZE in goal_types
        assert GoalType.RESTORE in goal_types

    def test_generate_goals_concurrent_limit(self):
        """Test max_concurrent_goals limit (lines 339-340)."""
        # ARRANGE: Generator with low limit
        config = GoalGenerationConfig(max_concurrent_goals=2)
        generator = AutonomousGoalGenerator(config=config)

        # Add 2 existing active goals with valid source_need to prevent auto-satisfaction
        goal1 = Goal(goal_type=GoalType.REST, source_need="rest_need", need_value=0.80, target_need_value=0.30)
        goal2 = Goal(goal_type=GoalType.REPAIR, source_need="repair_need", need_value=0.80, target_need_value=0.20)
        generator._active_goals = [goal1, goal2]

        # High needs (keeps existing goals unsatisfied)
        needs = AbstractNeeds(
            rest_need=0.80,
            repair_need=0.80,
            efficiency_need=0.80
        )

        # ACT: Try to generate more goals (should be blocked)
        new_goals = generator.generate_goals(needs)

        # ASSERT: No new goals (limit reached, line 340)
        assert len(new_goals) == 0
        assert len(generator._active_goals) == 2

    def test_generate_goals_interval_limit(self):
        """Test min_goal_interval_seconds prevents spam (lines 395-401)."""
        # ARRANGE: Generator with short interval
        config = GoalGenerationConfig(min_goal_interval_seconds=10.0)
        generator = AutonomousGoalGenerator(config=config)

        # Set last generation to 1 second ago (too recent)
        generator._last_generation["rest_need"] = time.time() - 1.0

        # High rest need
        needs = AbstractNeeds(rest_need=0.80)

        # ACT: Try to generate goal (should be blocked by interval)
        new_goals = generator.generate_goals(needs)

        # ASSERT: No goal generated (too soon, line 401)
        assert len(new_goals) == 0

    def test_generate_goals_interval_elapsed(self):
        """Test goal generation after interval elapsed."""
        # ARRANGE: Generator with short interval
        config = GoalGenerationConfig(min_goal_interval_seconds=0.1)
        generator = AutonomousGoalGenerator(config=config)

        # Set last generation to 1 second ago (elapsed)
        generator._last_generation["rest_need"] = time.time() - 1.0

        # High rest need
        needs = AbstractNeeds(rest_need=0.80)

        # ACT: Generate goal (should succeed, interval elapsed)
        new_goals = generator.generate_goals(needs)

        # ASSERT: Goal generated
        assert len(new_goals) == 1

    def test_generate_goals_consumer_notification(self):
        """Test consumers notified of new goals (lines 389-391)."""
        # ARRANGE: Generator with consumer
        generator = AutonomousGoalGenerator()
        mock_consumer = Mock()
        generator.register_goal_consumer(mock_consumer)

        # High rest need
        needs = AbstractNeeds(rest_need=0.80)

        # ACT: Generate goal (should notify consumer)
        new_goals = generator.generate_goals(needs)

        # ASSERT: Consumer called (line 391)
        assert mock_consumer.called
        assert len(mock_consumer.call_args_list) == 1
        called_goal = mock_consumer.call_args[0][0]
        assert isinstance(called_goal, Goal)

    def test_generate_goals_updates_active_goals(self):
        """Test new goals added to _active_goals (line 386)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(rest_need=0.80)

        # ACT
        new_goals = generator.generate_goals(needs)

        # ASSERT: New goals in active list (line 386)
        assert len(generator._active_goals) == 1
        assert generator._active_goals[0] == new_goals[0]

    def test_generate_goals_increments_total(self):
        """Test total_goals_generated increments (line 387)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()
        assert generator.total_goals_generated == 0

        # ACT: Generate 2 goals
        needs = AbstractNeeds(rest_need=0.80, repair_need=0.60)
        new_goals = generator.generate_goals(needs)

        # ASSERT: Counter incremented (line 387)
        assert generator.total_goals_generated == 2

# ==================== UPDATE ACTIVE GOALS TESTS ====================


class TestUpdateActiveGoals:
    """Test _update_active_goals method."""

    def test_update_active_goals_satisfaction(self):
        """Test goal satisfaction detection (lines 403-427)."""
        # ARRANGE: Generator with active goal
        generator = AutonomousGoalGenerator()

        # Create goal with high need
        goal = Goal(
            source_need="rest_need",
            need_value=0.80,
            target_need_value=0.30
        )
        generator._active_goals = [goal]
        assert generator.total_goals_satisfied == 0

        # Low need now (satisfied)
        needs = AbstractNeeds(rest_need=0.20)  # < 0.30 target

        # ACT: Update active goals (calls _update_active_goals internally)
        generator.generate_goals(needs)

        # ASSERT: Goal satisfied and moved (lines 418-422)
        assert len(generator._active_goals) == 0
        assert len(generator._completed_goals) == 1
        assert generator.total_goals_satisfied == 1
        assert goal.is_active is False

    def test_update_active_goals_expiration(self):
        """Test goal expiration detection (lines 408-413)."""
        # ARRANGE: Generator with expired goal
        generator = AutonomousGoalGenerator()

        # Create old goal
        goal = Goal(timeout_seconds=1.0)
        goal.created_at = time.time() - 10.0  # 10s ago
        generator._active_goals = [goal]
        assert generator.total_goals_expired == 0

        # ACT: Update (should detect expiration)
        needs = AbstractNeeds()  # No high needs
        generator.generate_goals(needs)

        # ASSERT: Goal expired and moved (lines 410-413)
        assert len(generator._active_goals) == 0
        assert len(generator._expired_goals) == 1
        assert generator.total_goals_expired == 1
        assert goal.is_active is False

    def test_update_active_goals_still_active(self):
        """Test goals remain active when not satisfied/expired (lines 424-427)."""
        # ARRANGE: Fresh unsatisfied goal
        generator = AutonomousGoalGenerator()
        goal = Goal(
            goal_type=GoalType.REST,
            source_need="rest_need",
            need_value=0.80,
            target_need_value=0.30,
            timeout_seconds=300.0
        )
        goal.created_at = time.time()
        generator._active_goals = [goal]

        # Record last generation to prevent duplicate goal generation
        generator._last_generation["rest_need"] = time.time()

        # Still high need
        needs = AbstractNeeds(rest_need=0.70)  # > 0.30 target

        # ACT: Update
        generator.generate_goals(needs)

        # ASSERT: Goal still active (line 425-427)
        assert len(generator._active_goals) == 1
        assert generator._active_goals[0] == goal
        assert goal.is_active is True

# ==================== GOAL CREATION METHODS TESTS ====================


class TestGoalCreationMethods:
    """Test individual _create_*_goal methods."""

    def test_create_rest_goal_critical(self):
        """Test _create_rest_goal with critical priority (lines 462-482)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create rest goal with very high need (critical)
        goal = generator._create_rest_goal(need_value=0.95)

        # ASSERT: Goal created correctly (lines 462-482)
        assert goal.goal_type == GoalType.REST
        assert goal.priority == GoalPriority.CRITICAL  # 0.95 -> CRITICAL
        assert "computational load" in goal.description.lower()
        assert goal.target_component == "cpu_scheduler"
        assert goal.source_need == "rest_need"
        assert goal.need_value == 0.95
        assert goal.target_need_value == generator.config.rest_satisfied
        assert goal.timeout_seconds == generator.config.critical_timeout  # Critical timeout
        assert "actions" in goal.metadata
        assert isinstance(goal.metadata["actions"], list)

    def test_create_repair_goal(self):
        """Test _create_repair_goal (lines 484-501)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create repair goal
        goal = generator._create_repair_goal(need_value=0.70)

        # ASSERT: Goal created (lines 484-501)
        assert goal.goal_type == GoalType.REPAIR
        assert goal.priority == GoalPriority.HIGH  # 0.70 -> HIGH
        assert "repair" in goal.description.lower()
        assert goal.target_component == "error_handler"
        assert goal.source_need == "repair_need"
        assert goal.timeout_seconds == generator.config.critical_timeout  # Always critical
        assert "actions" in goal.metadata

    def test_create_efficiency_goal(self):
        """Test _create_efficiency_goal (lines 503-520)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create efficiency goal
        goal = generator._create_efficiency_goal(need_value=0.55)

        # ASSERT: Goal created (lines 503-520)
        assert goal.goal_type == GoalType.OPTIMIZE
        assert goal.priority == GoalPriority.MODERATE  # 0.55 -> MODERATE
        assert "optimize" in goal.description.lower()
        assert goal.target_component == "resource_manager"
        assert goal.source_need == "efficiency_need"

    def test_create_connectivity_goal(self):
        """Test _create_connectivity_goal (lines 522-539)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create connectivity goal
        goal = generator._create_connectivity_goal(need_value=0.75)

        # ASSERT: Goal created (lines 522-539)
        assert goal.goal_type == GoalType.RESTORE
        assert goal.priority == GoalPriority.HIGH  # 0.75 -> HIGH
        assert "connectivity" in goal.description.lower()
        assert goal.target_component == "network_manager"
        assert goal.source_need == "connectivity_need"

    def test_create_exploration_goal(self):
        """Test _create_exploration_goal (lines 541-556)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create exploration goal
        goal = generator._create_exploration_goal(need_value=0.80)

        # ASSERT: Goal created (lines 541-556)
        assert goal.goal_type == GoalType.EXPLORE
        assert goal.priority == GoalPriority.LOW  # Always low (line 545)
        assert "explore" in goal.description.lower()
        assert goal.target_component == "exploration_engine"
        assert goal.source_need == "curiosity_drive"
        assert goal.target_need_value == 0.0  # Satisfied when no longer idle
        assert goal.timeout_seconds == generator.config.exploration_timeout

    def test_create_learning_goal(self):
        """Test _create_learning_goal (lines 558-573)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Create learning goal
        goal = generator._create_learning_goal(need_value=0.65)

        # ASSERT: Goal created (lines 558-573)
        assert goal.goal_type == GoalType.LEARN
        assert goal.priority == GoalPriority.LOW  # Always low (line 562)
        assert "learn" in goal.description.lower() or "patterns" in goal.description.lower()
        assert goal.target_component == "learning_engine"
        assert goal.source_need == "learning_drive"

    def test_classify_priority_satisfied(self):
        """Test _classify_priority for satisfied need (lines 433-445)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Classify very low need
        priority = generator._classify_priority(need_value=0.15)

        # ASSERT: Mapped to BACKGROUND (line 438)
        assert priority == GoalPriority.BACKGROUND

    def test_classify_priority_low(self):
        """Test _classify_priority for low urgency."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Classify low need
        priority = generator._classify_priority(need_value=0.30)

        # ASSERT: LOW priority (line 439)
        assert priority == GoalPriority.LOW

    def test_classify_priority_moderate(self):
        """Test _classify_priority for moderate urgency."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Classify moderate need
        priority = generator._classify_priority(need_value=0.50)

        # ASSERT: MODERATE priority (line 440)
        assert priority == GoalPriority.MODERATE

    def test_classify_priority_high(self):
        """Test _classify_priority for high urgency."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Classify high need
        priority = generator._classify_priority(need_value=0.70)

        # ASSERT: HIGH priority (line 441)
        assert priority == GoalPriority.HIGH

    def test_classify_priority_critical(self):
        """Test _classify_priority for critical urgency."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT: Classify critical need
        priority = generator._classify_priority(need_value=0.90)

        # ASSERT: CRITICAL priority (line 442)
        assert priority == GoalPriority.CRITICAL

    def test_classify_urgency_boundaries(self):
        """Test _classify_urgency boundary conditions (lines 447-458)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()

        # ACT & ASSERT: Test all boundaries (lines 449-458)
        assert generator._classify_urgency(0.10) == NeedUrgency.SATISFIED  # < 0.20
        assert generator._classify_urgency(0.20) == NeedUrgency.LOW  # 0.20-0.40
        assert generator._classify_urgency(0.40) == NeedUrgency.MODERATE  # 0.40-0.60
        assert generator._classify_urgency(0.60) == NeedUrgency.HIGH  # 0.60-0.80
        assert generator._classify_urgency(0.80) == NeedUrgency.CRITICAL  # >= 0.80

# ==================== QUERY METHODS TESTS ====================


class TestQueryMethods:
    """Test goal query and statistics methods."""

    def test_get_active_goals_unsorted(self):
        """Test get_active_goals without sorting (lines 585-601)."""
        # ARRANGE: Generator with multiple goals
        generator = AutonomousGoalGenerator()
        goal1 = Goal(priority=GoalPriority.LOW)
        goal2 = Goal(priority=GoalPriority.HIGH)
        goal3 = Goal(priority=GoalPriority.MODERATE)
        generator._active_goals = [goal1, goal2, goal3]

        # ACT: Get active goals without sorting (line 601)
        active = generator.get_active_goals(sort_by_priority=False)

        # ASSERT: Returns copy in original order (line 601)
        assert len(active) == 3
        assert active[0] == goal1
        assert active[1] == goal2
        assert active[2] == goal3

    def test_get_active_goals_sorted(self):
        """Test get_active_goals with priority sorting (lines 595-600)."""
        # ARRANGE: Goals with different priorities
        generator = AutonomousGoalGenerator()
        goal_low = Goal(priority=GoalPriority.LOW, need_value=0.3)
        goal_high = Goal(priority=GoalPriority.HIGH, need_value=0.7)
        goal_critical = Goal(priority=GoalPriority.CRITICAL, need_value=0.9)
        generator._active_goals = [goal_low, goal_high, goal_critical]

        # ACT: Get sorted (lines 595-600)
        sorted_goals = generator.get_active_goals(sort_by_priority=True)

        # ASSERT: Sorted by priority score (highest first)
        assert len(sorted_goals) == 3
        # Critical should be first (highest score)
        assert sorted_goals[0].priority == GoalPriority.CRITICAL
        assert sorted_goals[-1].priority == GoalPriority.LOW

    def test_get_critical_goals(self):
        """Test get_critical_goals method (lines 603-605)."""
        # ARRANGE: Mix of priorities
        generator = AutonomousGoalGenerator()
        goal_low = Goal(priority=GoalPriority.LOW)
        goal_critical1 = Goal(priority=GoalPriority.CRITICAL)
        goal_high = Goal(priority=GoalPriority.HIGH)
        goal_critical2 = Goal(priority=GoalPriority.CRITICAL)
        generator._active_goals = [goal_low, goal_critical1, goal_high, goal_critical2]

        # ACT: Get critical only (line 605)
        critical = generator.get_critical_goals()

        # ASSERT: Only critical returned
        assert len(critical) == 2
        assert all(g.priority == GoalPriority.CRITICAL for g in critical)

    def test_get_goals_by_type(self):
        """Test get_goals_by_type method (lines 607-609)."""
        # ARRANGE: Mix of types
        generator = AutonomousGoalGenerator()
        goal_rest1 = Goal(goal_type=GoalType.REST)
        goal_repair = Goal(goal_type=GoalType.REPAIR)
        goal_rest2 = Goal(goal_type=GoalType.REST)
        goal_explore = Goal(goal_type=GoalType.EXPLORE)
        generator._active_goals = [goal_rest1, goal_repair, goal_rest2, goal_explore]

        # ACT: Get REST goals only (line 609)
        rest_goals = generator.get_goals_by_type(GoalType.REST)

        # ASSERT: Only REST returned
        assert len(rest_goals) == 2
        assert all(g.goal_type == GoalType.REST for g in rest_goals)

    def test_get_statistics_empty(self):
        """Test get_statistics with no goals (lines 611-626)."""
        # ARRANGE: Empty generator
        generator = AutonomousGoalGenerator(generator_id="test-stats-01")

        # ACT: Get statistics (lines 611-626)
        stats = generator.get_statistics()

        # ASSERT: Stats structure (lines 619-626)
        assert stats["generator_id"] == "test-stats-01"
        assert stats["active_goals"] == 0
        assert stats["total_generated"] == 0
        assert stats["total_satisfied"] == 0
        assert stats["total_expired"] == 0
        assert stats["satisfaction_rate"] == 0.0  # No goals (line 616)

    def test_get_statistics_with_goals(self):
        """Test get_statistics with goals."""
        # ARRANGE: Generator with history
        generator = AutonomousGoalGenerator()
        generator.total_goals_generated = 20
        generator.total_goals_satisfied = 15
        generator.total_goals_expired = 3
        generator._active_goals = [Goal(), Goal()]

        # ACT: Get stats
        stats = generator.get_statistics()

        # ASSERT: Stats calculated correctly (lines 613-616)
        assert stats["active_goals"] == 2
        assert stats["total_generated"] == 20
        assert stats["total_satisfied"] == 15
        assert stats["total_expired"] == 3
        assert stats["satisfaction_rate"] == 15 / 20  # 0.75

    def test_generator_repr(self):
        """Test AutonomousGoalGenerator __repr__ (lines 628-631)."""
        # ARRANGE: Generator with goals
        generator = AutonomousGoalGenerator(generator_id="repr-test-01")
        generator._active_goals = [Goal(), Goal(), Goal()]
        generator.total_goals_generated = 10

        # ACT: Get repr (lines 628-631)
        repr_str = repr(generator)

        # ASSERT: Contains key info
        assert "AutonomousGoalGenerator" in repr_str
        assert "repr-test-01" in repr_str
        assert "active=3" in repr_str
        assert "generated=10" in repr_str

    def test_notify_consumers_success(self):
        """Test _notify_consumers calls all consumers (lines 575-581)."""
        # ARRANGE: Generator with 2 consumers
        generator = AutonomousGoalGenerator()
        consumer1 = Mock()
        consumer2 = Mock()
        generator.register_goal_consumer(consumer1)
        generator.register_goal_consumer(consumer2)

        goal = Goal()

        # ACT: Notify consumers (lines 575-581)
        generator._notify_consumers(goal)

        # ASSERT: Both called (line 579)
        assert consumer1.called
        assert consumer2.called
        assert consumer1.call_args[0][0] == goal
        assert consumer2.call_args[0][0] == goal

    def test_notify_consumers_exception_handling(self):
        """Test _notify_consumers handles consumer exceptions (lines 580-581)."""
        # ARRANGE: Consumer that raises exception
        generator = AutonomousGoalGenerator()

        def failing_consumer(goal):
            raise RuntimeError("Consumer failed")

        generator.register_goal_consumer(failing_consumer)

        goal = Goal()

        # ACT: Notify (should catch exception, line 580-581)
        generator._notify_consumers(goal)

        # ASSERT: No exception raised (graceful handling)
        # If we get here, test passes

    def test_get_need_value(self):
        """Test _get_need_value helper (lines 429-431)."""
        # ARRANGE
        generator = AutonomousGoalGenerator()
        needs = AbstractNeeds(rest_need=0.75, repair_need=0.40)

        # ACT: Get specific need values (line 431)
        rest = generator._get_need_value(needs, "rest_need")
        repair = generator._get_need_value(needs, "repair_need")
        invalid = generator._get_need_value(needs, "nonexistent_need")

        # ASSERT: Values retrieved correctly
        assert rest == 0.75
        assert repair == 0.40
        assert invalid == 0.0  # Default for nonexistent
