"""
Self-Reflection & Continuous Improvement System
================================================

Meta-learning system that enables AI to reflect on its decisions,
learn from mistakes, and improve over time.

Features:
- Action-outcome reflection
- Error pattern recognition
- Strategy adaptation
- Performance metrics tracking
- Knowledge base refinement

Examples:
    reflector = SelfReflector()

    # Reflect on action outcome
    reflection = reflector.reflect(
        action="Classified alert as false positive",
        outcome="Alert was actually a real attack",
        context={...}
    )

    # System learns and adapts
    improvements = reflector.get_improvements()
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class OutcomeType(Enum):
    """Types of action outcomes."""

    SUCCESS = "success"  # Action achieved desired outcome
    PARTIAL_SUCCESS = "partial_success"  # Partially achieved goal
    FAILURE = "failure"  # Action failed
    FALSE_POSITIVE = "false_positive"  # Incorrect positive classification
    FALSE_NEGATIVE = "false_negative"  # Missed detection
    SUBOPTIMAL = "suboptimal"  # Worked but better approach exists


class ReflectionType(Enum):
    """Types of reflections."""

    TACTICAL = "tactical"  # Specific action improvement
    STRATEGIC = "strategic"  # Overall approach improvement
    KNOWLEDGE = "knowledge"  # Knowledge gap identified
    CAPABILITY = "capability"  # Capability limitation identified


@dataclass
class ActionRecord:
    """
    Record of action taken and its outcome.

    Attributes:
        action: Description of action taken
        context: Context when action was taken
        expected_outcome: What was expected
        actual_outcome: What actually happened
        outcome_type: Classification of outcome
        timestamp: When action occurred
    """
    action: str
    context: Dict[str, Any]
    expected_outcome: str
    actual_outcome: str
    outcome_type: OutcomeType
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Reflection:
    """
    Self-reflection on action-outcome pair.

    Attributes:
        reflection_type: Type of reflection
        insight: Key insight from reflection
        what_went_wrong: Analysis of failures
        what_went_right: Analysis of successes
        improvement_suggestions: Concrete improvements
        confidence: Confidence in reflection (0-1)
    """
    reflection_type: ReflectionType
    insight: str
    what_went_wrong: Optional[str] = None
    what_went_right: Optional[str] = None
    improvement_suggestions: List[str] = field(default_factory=list)
    patterns_identified: List[str] = field(default_factory=list)
    confidence: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningInsight:
    """
    Actionable learning insight for system improvement.

    Attributes:
        insight_type: Type of insight
        description: Natural language description
        action_items: Concrete steps to implement
        priority: Priority score (0-1, higher = more important)
        evidence_count: Number of observations supporting this
    """
    insight_type: str
    description: str
    action_items: List[str]
    priority: float
    evidence_count: int
    first_observed: datetime
    last_observed: datetime


class SelfReflector:
    """
    Self-reflection and continuous improvement engine.

    Tracks actions, outcomes, and learns patterns to improve
    future decision-making.

    Example:
        reflector = SelfReflector()

        # Record action and outcome
        action_record = reflector.record_action(
            action="Blocked IP 1.2.3.4",
            context={"reason": "bruteforce", "attempts": 50},
            expected_outcome="Attack stopped",
            actual_outcome="Different IP continued attack",
            outcome_type=OutcomeType.PARTIAL_SUCCESS
        )

        # Reflect on outcome
        reflection = reflector.reflect(action_record)

        # Get improvement suggestions
        improvements = reflector.get_improvements()
    """

    def __init__(
        self,
        reflection_window_days: int = 30,
        min_pattern_occurrences: int = 3,
    ):
        """
        Initialize self-reflector.

        Args:
            reflection_window_days: Days of history to consider
            min_pattern_occurrences: Minimum occurrences to identify pattern
        """
        self.reflection_window_days = reflection_window_days
        self.min_pattern_occurrences = min_pattern_occurrences

        # State
        self._action_history: List[ActionRecord] = []
        self._reflection_history: List[Reflection] = []
        self._learning_insights: Dict[str, LearningInsight] = {}
        self._error_patterns: Dict[str, int] = defaultdict(int)
        self._success_patterns: Dict[str, int] = defaultdict(int)

        logger.info(
            f"SelfReflector initialized (window={reflection_window_days}d, "
            f"min_pattern={min_pattern_occurrences})"
        )

    def record_action(
        self,
        action: str,
        context: Dict[str, Any],
        expected_outcome: str,
        actual_outcome: str,
        outcome_type: OutcomeType,
        confidence: float = 0.5,
        **metadata
    ) -> ActionRecord:
        """
        Record action and its outcome for later reflection.

        Args:
            action: Action taken
            context: Context at decision time
            expected_outcome: Expected result
            actual_outcome: Actual result
            outcome_type: Classification of outcome
            confidence: Confidence in decision (0-1)
            **metadata: Additional metadata

        Returns:
            ActionRecord

        Example:
            record = reflector.record_action(
                action="Escalated alert to SOC",
                context={"severity": "high", "iocs": [...]},
                expected_outcome="Real incident",
                actual_outcome="False alarm - system update",
                outcome_type=OutcomeType.FALSE_POSITIVE
            )
        """
        record = ActionRecord(
            action=action,
            context=context,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            outcome_type=outcome_type,
            confidence=confidence,
            metadata=metadata
        )

        self._action_history.append(record)

        # Update pattern tracking
        if outcome_type in [OutcomeType.FAILURE, OutcomeType.FALSE_POSITIVE, OutcomeType.FALSE_NEGATIVE]:
            pattern_key = f"{action}:{outcome_type.value}"
            self._error_patterns[pattern_key] += 1

        elif outcome_type == OutcomeType.SUCCESS:
            pattern_key = f"{action}:success"
            self._success_patterns[pattern_key] += 1

        logger.debug(
            f"Action recorded: {action[:50]}... "
            f"(outcome={outcome_type.value}, conf={confidence:.2f})"
        )

        # Trigger automatic reflection
        reflection = self.reflect(record)

        return record

    def reflect(self, action_record: ActionRecord) -> Reflection:
        """
        Perform reflection on action-outcome pair.

        Args:
            action_record: Record to reflect on

        Returns:
            Reflection with insights

        Example:
            reflection = reflector.reflect(action_record)
            print(reflection.insight)
        """
        logger.info(f"Reflecting on: {action_record.action[:60]}...")

        # Determine reflection type
        if action_record.outcome_type in [OutcomeType.FAILURE, OutcomeType.FALSE_POSITIVE, OutcomeType.FALSE_NEGATIVE]:
            reflection = self._reflect_on_failure(action_record)

        elif action_record.outcome_type == OutcomeType.SUCCESS:
            reflection = self._reflect_on_success(action_record)

        else:
            reflection = self._reflect_on_partial_success(action_record)

        # Store reflection
        self._reflection_history.append(reflection)

        # Update learning insights
        self._update_learning_insights(action_record, reflection)

        logger.info(f"Reflection complete: {reflection.reflection_type.value}")

        return reflection

    def _reflect_on_failure(self, record: ActionRecord) -> Reflection:
        """Reflect on failed action."""

        # Analyze why it failed
        what_went_wrong = self._analyze_failure(record)

        # Identify patterns
        patterns = self._identify_patterns(record)

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(record, patterns)

        reflection = Reflection(
            reflection_type=ReflectionType.TACTICAL,
            insight=f"Action '{record.action}' led to {record.outcome_type.value}",
            what_went_wrong=what_went_wrong,
            improvement_suggestions=suggestions,
            patterns_identified=patterns,
            confidence=0.8,
            metadata={"original_confidence": record.confidence}
        )

        return reflection

    def _reflect_on_success(self, record: ActionRecord) -> Reflection:
        """Reflect on successful action."""

        what_went_right = (
            f"Action '{record.action}' achieved expected outcome. "
            f"Key factors: {', '.join(record.context.keys())}"
        )

        # Extract success patterns
        patterns = []
        for key, value in record.context.items():
            patterns.append(f"{key}={value}")

        reflection = Reflection(
            reflection_type=ReflectionType.TACTICAL,
            insight=f"Successful strategy: {record.action}",
            what_went_right=what_went_right,
            patterns_identified=patterns,
            improvement_suggestions=["Repeat similar approach in similar contexts"],
            confidence=0.9
        )

        return reflection

    def _reflect_on_partial_success(self, record: ActionRecord) -> Reflection:
        """Reflect on partially successful action."""

        reflection = Reflection(
            reflection_type=ReflectionType.STRATEGIC,
            insight=f"Action partially effective, explore optimizations",
            what_went_right="Action had some positive effect",
            what_went_wrong="Did not fully achieve intended outcome",
            improvement_suggestions=[
                "Investigate why outcome was only partial",
                "Consider complementary actions",
                "Adjust confidence thresholds"
            ],
            confidence=0.7
        )

        return reflection

    def _analyze_failure(self, record: ActionRecord) -> str:
        """Analyze why action failed."""

        if record.outcome_type == OutcomeType.FALSE_POSITIVE:
            return (
                f"Incorrectly classified as positive. "
                f"Expected: {record.expected_outcome}, "
                f"Got: {record.actual_outcome}. "
                f"Possible causes: insufficient context, overly sensitive rules, "
                f"missing environmental factors."
            )

        elif record.outcome_type == OutcomeType.FALSE_NEGATIVE:
            return (
                f"Missed detection. "
                f"Failed to identify threat that was present. "
                f"Possible causes: detection gap, insufficient visibility, "
                f"overly strict thresholds."
            )

        else:
            return (
                f"Action failed to achieve expected outcome. "
                f"Gap between expectation and reality suggests knowledge gap "
                f"or incorrect assumption."
            )

    def _identify_patterns(self, record: ActionRecord) -> List[str]:
        """Identify recurring patterns in failures."""

        patterns = []

        # Check if this action fails repeatedly
        pattern_key = f"{record.action}:{record.outcome_type.value}"

        if self._error_patterns[pattern_key] >= self.min_pattern_occurrences:
            patterns.append(
                f"RECURRING: Action '{record.action}' has failed {self._error_patterns[pattern_key]} times"
            )

        # Check context patterns
        for key, value in record.context.items():
            context_pattern = f"{key}={value}:{record.outcome_type.value}"

            if context_pattern in self._error_patterns and self._error_patterns[context_pattern] >= 2:
                patterns.append(
                    f"CONTEXT: Failures often occur when {key}={value}"
                )

        return patterns

    def _generate_improvement_suggestions(
        self,
        record: ActionRecord,
        patterns: List[str]
    ) -> List[str]:
        """Generate concrete improvement suggestions."""

        suggestions = []

        if record.outcome_type == OutcomeType.FALSE_POSITIVE:
            suggestions.extend([
                "Add additional validation checks before classification",
                "Increase confidence threshold for this action",
                "Incorporate more contextual signals",
                "Create exception rules for edge cases"
            ])

        elif record.outcome_type == OutcomeType.FALSE_NEGATIVE:
            suggestions.extend([
                "Lower detection thresholds",
                "Add additional detection signatures",
                "Increase monitoring coverage",
                "Review blind spots in visibility"
            ])

        elif record.outcome_type == OutcomeType.FAILURE:
            suggestions.extend([
                "Re-evaluate assumptions in decision logic",
                "Gather additional context before acting",
                "Consider alternative strategies",
                "Improve validation of expected outcomes"
            ])

        # Pattern-specific suggestions
        if patterns:
            suggestions.append(
                f"Investigate root cause of recurring pattern: {patterns[0][:100]}"
            )

        return suggestions

    def _update_learning_insights(
        self,
        record: ActionRecord,
        reflection: Reflection
    ) -> None:
        """Update accumulated learning insights."""

        for suggestion in reflection.improvement_suggestions:
            insight_key = suggestion[:100]  # Use first 100 chars as key

            if insight_key in self._learning_insights:
                # Update existing insight
                insight = self._learning_insights[insight_key]
                insight.evidence_count += 1
                insight.last_observed = datetime.now()

                # Increase priority with more evidence
                insight.priority = min(1.0, insight.priority + 0.05)

            else:
                # Create new insight
                self._learning_insights[insight_key] = LearningInsight(
                    insight_type=reflection.reflection_type.value,
                    description=suggestion,
                    action_items=[suggestion],
                    priority=0.5,
                    evidence_count=1,
                    first_observed=datetime.now(),
                    last_observed=datetime.now()
                )

    def get_improvements(
        self,
        min_priority: float = 0.6,
        limit: int = 10
    ) -> List[LearningInsight]:
        """
        Get prioritized improvement suggestions.

        Args:
            min_priority: Minimum priority threshold
            limit: Maximum number of suggestions

        Returns:
            List of LearningInsights sorted by priority

        Example:
            improvements = reflector.get_improvements(min_priority=0.7)

            for improvement in improvements:
                print(f"Priority {improvement.priority:.0%}: {improvement.description}")
        """
        # Filter by priority
        improvements = [
            insight for insight in self._learning_insights.values()
            if insight.priority >= min_priority
        ]

        # Sort by priority (descending)
        improvements.sort(key=lambda x: x.priority, reverse=True)

        return improvements[:limit]

    def get_error_patterns(self, min_occurrences: int = 3) -> Dict[str, int]:
        """
        Get recurring error patterns.

        Args:
            min_occurrences: Minimum occurrences to include

        Returns:
            Dict of pattern → occurrence count

        Example:
            patterns = reflector.get_error_patterns(min_occurrences=5)

            for pattern, count in patterns.items():
                print(f"{pattern}: {count} occurrences")
        """
        return {
            pattern: count
            for pattern, count in self._error_patterns.items()
            if count >= min_occurrences
        }

    def get_success_patterns(self, min_occurrences: int = 3) -> Dict[str, int]:
        """Get recurring success patterns."""
        return {
            pattern: count
            for pattern, count in self._success_patterns.items()
            if count >= min_occurrences
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get reflection statistics.

        Returns:
            Stats dict

        Example:
            stats = reflector.get_stats()
            print(f"Success rate: {stats['success_rate']:.1%}")
        """
        if not self._action_history:
            return {
                "total_actions": 0,
                "success_rate": 0.0,
                "reflections_generated": 0,
                "learning_insights": 0,
                "error_patterns": 0,
                "success_patterns": 0,
            }

        successes = sum(
            1 for record in self._action_history
            if record.outcome_type == OutcomeType.SUCCESS
        )

        return {
            "total_actions": len(self._action_history),
            "success_rate": successes / len(self._action_history),
            "reflections_generated": len(self._reflection_history),
            "learning_insights": len(self._learning_insights),
            "error_patterns": len([p for p in self._error_patterns.values() if p >= self.min_pattern_occurrences]),
            "success_patterns": len([p for p in self._success_patterns.values() if p >= self.min_pattern_occurrences]),
            "avg_confidence": sum(r.confidence for r in self._action_history) / len(self._action_history),
        }
