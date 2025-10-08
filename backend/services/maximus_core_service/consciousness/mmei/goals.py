"""
Autonomous Goal Generation - Need-Based Motivation
===================================================

This module implements autonomous goal generation driven by internal needs.
Goals emerge from interoception, creating intrinsic motivation without
external commands.

Theoretical Foundation:
-----------------------
Biological motivation theory distinguishes:

1. **Homeostatic Drives** (Deficit-based):
   - Hunger → seek food
   - Thirst → seek water
   - Fatigue → seek rest
   - Pain → seek relief

2. **Growth Drives** (Exploration-based):
   - Curiosity → seek novelty
   - Mastery → seek competence
   - Autonomy → seek control

Both types are internally generated, not externally commanded.
This intrinsic motivation is fundamental to autonomous agency.

Computational Implementation:
-----------------------------
MMEI translates needs into goals:

Abstract Need        → Generated Goal
-------------          ---------------
rest_need > 0.8     → "reduce_computational_load" (CRITICAL)
repair_need > 0.6   → "diagnose_and_repair_errors" (HIGH)
efficiency_need > 0.5 → "optimize_resource_usage" (MODERATE)
connectivity_need > 0.7 → "restore_network_connectivity" (HIGH)
curiosity_drive > 0.6 → "explore_idle_capacity" (LOW)

Goals have:
- Type: What kind of action (REST, REPAIR, OPTIMIZE, EXPLORE)
- Priority: How urgent (based on need urgency)
- Target: What system/component to act on
- Success criteria: How to know when satisfied

Integration with Action:
------------------------
Goals flow into execution systems:

  Needs → Goals → HCL → Actions

  Example:
    repair_need = 0.9
    → Goal("diagnose_and_repair_errors", priority=CRITICAL)
    → HCL receives goal
    → HCL triggers diagnostic action
    → Errors reduced
    → repair_need decreases
    → Goal satisfied

This creates autonomous homeostatic regulation without external control.

Biological Correspondence:
---------------------------
Analogous to:
- Hypothalamus: Homeostatic regulation (temperature, hunger, thirst)
- Ventral tegmental area: Reward-seeking, exploration
- Anterior cingulate: Conflict monitoring, error detection

These systems generate internally-motivated behavior based on bodily state.

Historical Context:
-------------------
First implementation of autonomous goal generation for AI based on
interoceptive needs. Enables true agency - behavior driven by internal
state rather than external commands.

"The free organism is one that acts from internal necessity, not external command."
- Immanuel Kant

Implementation Design:
----------------------
- Goals are continuously generated based on current needs
- Multiple goals can coexist (priority determines execution order)
- Goals persist until needs satisfied (or timeout)
- Goal success updates need state (feedback loop)
- Critical needs can force ESGT ignition for global broadcast
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from consciousness.mmei.monitor import AbstractNeeds, NeedUrgency


class GoalType(Enum):
    """Classification of goal types."""

    # Homeostatic (deficit-reduction)
    REST = "rest"  # Reduce computational load
    REPAIR = "repair"  # Fix errors, restore integrity
    OPTIMIZE = "optimize"  # Improve efficiency
    RESTORE = "restore"  # Restore connectivity/communication

    # Growth (exploration/expansion)
    EXPLORE = "explore"  # Explore new capabilities
    LEARN = "learn"  # Acquire new patterns
    CREATE = "create"  # Generate novel outputs


class GoalPriority(Enum):
    """Goal priority levels (maps to NeedUrgency)."""

    BACKGROUND = 0  # Optional, non-urgent
    LOW = 1  # Should do eventually
    MODERATE = 2  # Should do soon
    HIGH = 3  # Important, do quickly
    CRITICAL = 4  # Urgent, do immediately


@dataclass
class Goal:
    """
    Autonomous goal generated from internal needs.

    Goals represent internally-motivated intentions to act.
    They persist until satisfied or timeout.
    """

    goal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal_type: GoalType = GoalType.REST
    priority: GoalPriority = GoalPriority.LOW

    # Description
    description: str = ""
    target_component: str | None = None  # Which system to act on

    # Motivation
    source_need: str = ""  # Which need generated this goal
    need_value: float = 0.0  # Value of need when goal created

    # Success criteria
    target_need_value: float = 0.3  # Goal satisfied when need drops below this
    timeout_seconds: float = 300.0  # Goal expires after timeout

    # State
    created_at: float = field(default_factory=time.time)
    satisfied_at: float | None = None
    is_active: bool = True

    # Execution tracking
    execution_attempts: int = 0
    last_execution_at: float | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if goal has timed out."""
        if not self.is_active:
            return False
        return (time.time() - self.created_at) > self.timeout_seconds

    def is_satisfied(self, current_need_value: float) -> bool:
        """Check if goal satisfied based on current need value."""
        return current_need_value < self.target_need_value

    def mark_satisfied(self) -> None:
        """Mark goal as satisfied."""
        self.satisfied_at = time.time()
        self.is_active = False

    def record_execution_attempt(self) -> None:
        """Record that goal execution was attempted."""
        self.execution_attempts += 1
        self.last_execution_at = time.time()

    def get_age_seconds(self) -> float:
        """Get goal age in seconds."""
        return time.time() - self.created_at

    def get_priority_score(self) -> float:
        """
        Get numeric priority score for sorting.

        Combines priority level with need value and age.
        Higher score = more urgent.
        """
        base_score = self.priority.value * 100.0
        need_bonus = self.need_value * 50.0
        age_penalty = min(self.get_age_seconds() / self.timeout_seconds, 1.0) * 20.0

        return base_score + need_bonus - age_penalty

    def __repr__(self) -> str:
        status = "ACTIVE" if self.is_active else "SATISFIED"
        return (
            f"Goal({self.goal_type.value}, priority={self.priority.value}, status={status}, need={self.need_value:.2f})"
        )


@dataclass
class GoalGenerationConfig:
    """Configuration for autonomous goal generation."""

    # Generation thresholds (when to generate goals)
    rest_threshold: float = 0.60  # CPU/memory fatigue
    repair_threshold: float = 0.40  # Error detection (lower = more sensitive)
    efficiency_threshold: float = 0.50  # Resource optimization
    connectivity_threshold: float = 0.50  # Network issues
    curiosity_threshold: float = 0.60  # Exploration drive
    learning_threshold: float = 0.50  # Learning opportunities

    # Satisfaction thresholds (when goals complete)
    rest_satisfied: float = 0.30
    repair_satisfied: float = 0.20
    efficiency_satisfied: float = 0.30
    connectivity_satisfied: float = 0.30

    # Goal timeouts (seconds)
    default_timeout: float = 300.0  # 5 minutes
    critical_timeout: float = 600.0  # 10 minutes for critical goals
    exploration_timeout: float = 120.0  # 2 minutes for exploration

    # Generation limits
    max_concurrent_goals: int = 10
    min_goal_interval_seconds: float = 5.0  # Prevent goal spam


class AutonomousGoalGenerator:
    """
    Generates autonomous goals from internal needs.

    This is the motivational engine - translating phenomenal "feelings"
    (needs) into actionable intentions (goals).

    The generator runs continuously, monitoring needs and creating goals
    when thresholds exceeded. Goals persist until needs satisfied.

    Architecture:
    -------------
    InternalStateMonitor → AbstractNeeds
           ↓
    AutonomousGoalGenerator → Goals
           ↓
    HCL / Action Systems

    Goals can be consumed by:
    - HCL (Homeostatic Control Loop): Executes homeostatic actions
    - ESGT: Critical goals force consciousness ignition
    - Planning systems: High-level goal decomposition

    Usage:
    ------
        generator = AutonomousGoalGenerator(config)

        # Provide goal consumer
        async def execute_goal(goal: Goal):
            print(f"Executing: {goal}")
            # ... perform actions ...
            goal.mark_satisfied()

        generator.register_goal_consumer(execute_goal)

        # Generate goals from needs
        needs = AbstractNeeds(rest_need=0.85, repair_need=0.30)
        goals = generator.generate_goals(needs)

        # Get all active goals
        active = generator.get_active_goals()

    Biological Correspondence:
    ---------------------------
    Analogous to motivational systems:
    - Hypothalamus: Homeostatic goal generation (eat, drink, rest)
    - Nucleus accumbens: Reward-based goal pursuit
    - Prefrontal cortex: Goal maintenance and updating

    "Motivation is the translation of feeling into action."
    """

    def __init__(self, config: GoalGenerationConfig | None = None, generator_id: str = "mmei-goal-generator-primary"):
        self.generator_id = generator_id
        self.config = config or GoalGenerationConfig()

        # Active goals
        self._active_goals: list[Goal] = []

        # Goal history
        self._completed_goals: list[Goal] = []
        self._expired_goals: list[Goal] = []

        # Last generation timestamp (prevent spam)
        self._last_generation: dict[str, float] = {}

        # Goal consumers (execution callbacks)
        self._goal_consumers: list[Callable[[Goal], None]] = []

        # Statistics
        self.total_goals_generated: int = 0
        self.total_goals_satisfied: int = 0
        self.total_goals_expired: int = 0

    def register_goal_consumer(self, consumer: Callable[[Goal], None]) -> None:
        """
        Register callback to receive generated goals.

        Consumer will be called with each new goal generated.
        Multiple consumers can be registered.

        Args:
            consumer: Async function to call with Goal
        """
        self._goal_consumers.append(consumer)

    def generate_goals(self, needs: AbstractNeeds) -> list[Goal]:
        """
        Generate autonomous goals from current needs.

        This is the core motivation engine - analyzing needs and
        creating goals when thresholds exceeded.

        Args:
            needs: Current AbstractNeeds from interoception

        Returns:
            List of newly generated goals (may be empty)
        """
        new_goals: list[Goal] = []

        # First, update existing goals (check satisfaction, expiration)
        self._update_active_goals(needs)

        # Check if we hit concurrent goal limit
        if len(self._active_goals) >= self.config.max_concurrent_goals:
            return new_goals

        # Generate goals for each need type
        # REST NEED
        if needs.rest_need >= self.config.rest_threshold:
            if self._should_generate("rest_need"):
                goal = self._create_rest_goal(needs.rest_need)
                new_goals.append(goal)
                self._last_generation["rest_need"] = time.time()

        # REPAIR NEED
        if needs.repair_need >= self.config.repair_threshold:
            if self._should_generate("repair_need"):
                goal = self._create_repair_goal(needs.repair_need)
                new_goals.append(goal)
                self._last_generation["repair_need"] = time.time()

        # EFFICIENCY NEED
        if needs.efficiency_need >= self.config.efficiency_threshold:
            if self._should_generate("efficiency_need"):
                goal = self._create_efficiency_goal(needs.efficiency_need)
                new_goals.append(goal)
                self._last_generation["efficiency_need"] = time.time()

        # CONNECTIVITY NEED
        if needs.connectivity_need >= self.config.connectivity_threshold:
            if self._should_generate("connectivity_need"):
                goal = self._create_connectivity_goal(needs.connectivity_need)
                new_goals.append(goal)
                self._last_generation["connectivity_need"] = time.time()

        # CURIOSITY DRIVE
        if needs.curiosity_drive >= self.config.curiosity_threshold:
            if self._should_generate("curiosity_drive"):
                goal = self._create_exploration_goal(needs.curiosity_drive)
                new_goals.append(goal)
                self._last_generation["curiosity_drive"] = time.time()

        # LEARNING DRIVE
        if needs.learning_drive >= self.config.learning_threshold:
            if self._should_generate("learning_drive"):
                goal = self._create_learning_goal(needs.learning_drive)
                new_goals.append(goal)
                self._last_generation["learning_drive"] = time.time()

        # Add to active goals
        self._active_goals.extend(new_goals)
        self.total_goals_generated += len(new_goals)

        # Notify consumers
        for goal in new_goals:
            self._notify_consumers(goal)

        return new_goals

    def _should_generate(self, need_name: str) -> bool:
        """Check if enough time passed since last goal generation for this need."""
        if need_name not in self._last_generation:
            return True

        elapsed = time.time() - self._last_generation[need_name]
        return elapsed >= self.config.min_goal_interval_seconds

    def _update_active_goals(self, needs: AbstractNeeds) -> None:
        """Update active goals - check satisfaction and expiration."""
        still_active: list[Goal] = []

        for goal in self._active_goals:
            # Check expiration
            if goal.is_expired():
                goal.is_active = False
                self._expired_goals.append(goal)
                self.total_goals_expired += 1
                continue

            # Check satisfaction based on current need
            current_need = self._get_need_value(needs, goal.source_need)

            if goal.is_satisfied(current_need):
                goal.mark_satisfied()
                self._completed_goals.append(goal)
                self.total_goals_satisfied += 1
                continue

            # Still active
            still_active.append(goal)

        self._active_goals = still_active

    def _get_need_value(self, needs: AbstractNeeds, need_name: str) -> float:
        """Get current value of specific need."""
        return getattr(needs, need_name, 0.0)

    def _classify_priority(self, need_value: float) -> GoalPriority:
        """Classify goal priority based on need urgency."""
        urgency = self._classify_urgency(need_value)

        mapping = {
            NeedUrgency.SATISFIED: GoalPriority.BACKGROUND,
            NeedUrgency.LOW: GoalPriority.LOW,
            NeedUrgency.MODERATE: GoalPriority.MODERATE,
            NeedUrgency.HIGH: GoalPriority.HIGH,
            NeedUrgency.CRITICAL: GoalPriority.CRITICAL,
        }

        return mapping[urgency]

    def _classify_urgency(self, need_value: float) -> NeedUrgency:
        """Classify need urgency."""
        if need_value < 0.20:
            return NeedUrgency.SATISFIED
        if need_value < 0.40:
            return NeedUrgency.LOW
        if need_value < 0.60:
            return NeedUrgency.MODERATE
        if need_value < 0.80:
            return NeedUrgency.HIGH
        return NeedUrgency.CRITICAL

    # Goal creation methods for each need type

    def _create_rest_goal(self, need_value: float) -> Goal:
        """Create goal to reduce computational load (rest)."""
        priority = self._classify_priority(need_value)

        return Goal(
            goal_type=GoalType.REST,
            priority=priority,
            description="Reduce computational load to recover from fatigue",
            target_component="cpu_scheduler",
            source_need="rest_need",
            need_value=need_value,
            target_need_value=self.config.rest_satisfied,
            timeout_seconds=(
                self.config.critical_timeout if priority == GoalPriority.CRITICAL else self.config.default_timeout
            ),
            metadata={
                "actions": ["reduce_thread_count", "defer_background_tasks", "enter_low_power_mode"],
                "expected_benefit": "Decrease CPU/memory usage by 20-40%",
            },
        )

    def _create_repair_goal(self, need_value: float) -> Goal:
        """Create goal to diagnose and repair errors."""
        priority = self._classify_priority(need_value)

        return Goal(
            goal_type=GoalType.REPAIR,
            priority=priority,
            description="Diagnose and repair system errors",
            target_component="error_handler",
            source_need="repair_need",
            need_value=need_value,
            target_need_value=self.config.repair_satisfied,
            timeout_seconds=self.config.critical_timeout,  # Repair is always critical
            metadata={
                "actions": ["run_diagnostics", "apply_fixes", "verify_integrity"],
                "expected_benefit": "Reduce error rate to <1 per minute",
            },
        )

    def _create_efficiency_goal(self, need_value: float) -> Goal:
        """Create goal to optimize resource usage."""
        priority = self._classify_priority(need_value)

        return Goal(
            goal_type=GoalType.OPTIMIZE,
            priority=priority,
            description="Optimize resource usage and efficiency",
            target_component="resource_manager",
            source_need="efficiency_need",
            need_value=need_value,
            target_need_value=self.config.efficiency_satisfied,
            timeout_seconds=self.config.default_timeout,
            metadata={
                "actions": ["enable_thermal_throttling", "optimize_power_profile", "cache_warming"],
                "expected_benefit": "Reduce temperature by 5-10°C, power by 10-20W",
            },
        )

    def _create_connectivity_goal(self, need_value: float) -> Goal:
        """Create goal to restore network connectivity."""
        priority = self._classify_priority(need_value)

        return Goal(
            goal_type=GoalType.RESTORE,
            priority=priority,
            description="Restore network connectivity and reduce latency",
            target_component="network_manager",
            source_need="connectivity_need",
            need_value=need_value,
            target_need_value=self.config.connectivity_satisfied,
            timeout_seconds=self.config.critical_timeout,
            metadata={
                "actions": ["check_network_health", "reconnect_dropped_links", "optimize_routing"],
                "expected_benefit": "Reduce latency to <50ms, packet loss to <1%",
            },
        )

    def _create_exploration_goal(self, need_value: float) -> Goal:
        """Create goal to explore idle capacity (curiosity)."""
        return Goal(
            goal_type=GoalType.EXPLORE,
            priority=GoalPriority.LOW,  # Exploration is low priority
            description="Explore idle computational capacity",
            target_component="exploration_engine",
            source_need="curiosity_drive",
            need_value=need_value,
            target_need_value=0.0,  # Satisfied when no longer idle
            timeout_seconds=self.config.exploration_timeout,
            metadata={
                "actions": ["run_benchmarks", "test_new_algorithms", "profile_performance"],
                "expected_benefit": "Discover optimization opportunities",
            },
        )

    def _create_learning_goal(self, need_value: float) -> Goal:
        """Create goal to acquire new patterns (learning)."""
        return Goal(
            goal_type=GoalType.LEARN,
            priority=GoalPriority.LOW,
            description="Acquire new patterns and improve models",
            target_component="learning_engine",
            source_need="learning_drive",
            need_value=need_value,
            target_need_value=0.0,
            timeout_seconds=self.config.exploration_timeout,
            metadata={
                "actions": ["analyze_recent_data", "update_models", "identify_patterns"],
                "expected_benefit": "Improve prediction accuracy by 5-10%",
            },
        )

    def _notify_consumers(self, goal: Goal) -> None:
        """Notify all registered consumers of new goal."""
        for consumer in self._goal_consumers:
            try:
                consumer(goal)
            except Exception as e:
                print(f"⚠️  Goal consumer error: {e}")

    # Query methods

    def get_active_goals(self, sort_by_priority: bool = True) -> list[Goal]:
        """
        Get all active goals.

        Args:
            sort_by_priority: If True, sort by priority score (highest first)

        Returns:
            List of active goals
        """
        if sort_by_priority:
            return sorted(self._active_goals, key=lambda g: g.get_priority_score(), reverse=True)
        return self._active_goals.copy()

    def get_critical_goals(self) -> list[Goal]:
        """Get all active goals with CRITICAL priority."""
        return [g for g in self._active_goals if g.priority == GoalPriority.CRITICAL]

    def get_goals_by_type(self, goal_type: GoalType) -> list[Goal]:
        """Get all active goals of specific type."""
        return [g for g in self._active_goals if g.goal_type == goal_type]

    def get_statistics(self) -> dict[str, Any]:
        """Get goal generation statistics."""
        satisfaction_rate = (
            self.total_goals_satisfied / self.total_goals_generated if self.total_goals_generated > 0 else 0.0
        )

        return {
            "generator_id": self.generator_id,
            "active_goals": len(self._active_goals),
            "total_generated": self.total_goals_generated,
            "total_satisfied": self.total_goals_satisfied,
            "total_expired": self.total_goals_expired,
            "satisfaction_rate": satisfaction_rate,
        }

    def __repr__(self) -> str:
        return (
            f"AutonomousGoalGenerator({self.generator_id}, "
            f"active={len(self._active_goals)}, "
            f"generated={self.total_goals_generated})"
        )
