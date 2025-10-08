"""Neuromodulation Service - Production-Ready Serotonin Module

Bio-inspired serotonin modulator that implements:
1. **Outcome Tracking (Success/Failure)**
   - Tracks action outcomes over time
   - Success/failure ratios
   - Temporal patterns of performance

2. **Epsilon Modulation (Explore/Exploit)**
   - Adaptive epsilon-greedy strategy
   - High success rate → low epsilon (exploit)
   - Low success rate → high epsilon (explore)

3. **Failure Streak Detection**
   - Detects consecutive failures
   - Triggers exploration when stuck
   - Prevents local optima

Like biological serotonin: Regulates mood and risk-taking based on outcomes.
NO MOCKS - Production-ready implementation.
"""

import logging
from collections import deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ActionOutcome(Enum):
    """Action outcome types."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class SerotoninCore:
    """Production-ready Serotonin module for exploration/exploitation control.

    Modulates epsilon based on outcome history:
    - High success rate → Low epsilon (confident, exploit)
    - Low success rate → High epsilon (uncertain, explore)
    - Failure streak → Force exploration
    """

    def __init__(
        self,
        base_epsilon: float = 0.1,
        min_epsilon: float = 0.01,
        max_epsilon: float = 0.5,
        outcome_window_size: int = 100,
        failure_streak_threshold: int = 5,
    ):
        """Initialize Serotonin Core.

        Args:
            base_epsilon: Base exploration rate
            min_epsilon: Minimum epsilon
            max_epsilon: Maximum epsilon
            outcome_window_size: Window size for outcome tracking
            failure_streak_threshold: Consecutive failures before forced exploration
        """
        self.base_epsilon = base_epsilon
        self.min_epsilon = min_epsilon
        self.max_epsilon = max_epsilon
        self.failure_streak_threshold = failure_streak_threshold

        self.current_epsilon = base_epsilon
        self.outcome_history: deque = deque(maxlen=outcome_window_size)
        self.current_failure_streak = 0
        self.max_failure_streak = 0

        self.last_modulation_time: Optional[datetime] = None
        self.modulation_count = 0

        logger.info(f"SerotoninCore initialized (base_epsilon={base_epsilon}, range=[{min_epsilon}, {max_epsilon}])")

    def record_outcome(
        self,
        outcome: ActionOutcome,
        reward: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record action outcome.

        Args:
            outcome: Action outcome (success/failure/partial)
            reward: Reward received
            metadata: Additional outcome metadata
        """
        outcome_record = {
            "timestamp": datetime.now().isoformat(),
            "outcome": outcome.value,
            "reward": reward,
            "metadata": metadata or {},
        }

        self.outcome_history.append(outcome_record)

        # Update failure streak
        if outcome == ActionOutcome.FAILURE:
            self.current_failure_streak += 1
            self.max_failure_streak = max(self.max_failure_streak, self.current_failure_streak)
        else:
            self.current_failure_streak = 0

        logger.debug(
            f"Outcome recorded: {outcome.value} (reward={reward:.2f}, failure_streak={self.current_failure_streak})"
        )

    def modulate_epsilon(self, mood_stability: float = 0.7) -> float:
        """Modulate epsilon based on recent outcomes.

        Strategy:
        - High success rate → Low epsilon (exploit known strategies)
        - Low success rate → High epsilon (explore new strategies)
        - Failure streak detected → Force high epsilon

        Args:
            mood_stability: Mood stability factor (0-1)

        Returns:
            New epsilon value
        """
        if not self.outcome_history:
            return self.base_epsilon

        # Calculate success rate
        success_rate = self._compute_success_rate()

        # Check for failure streak (triggers exploration)
        if self.current_failure_streak >= self.failure_streak_threshold:
            logger.warning(f"Failure streak detected ({self.current_failure_streak}), forcing exploration")
            epsilon = self.max_epsilon
        else:
            # Inverse relationship: low success → high epsilon
            exploration_signal = 1.0 - success_rate

            # Modulate by mood stability (stable mood = lower epsilon variance)
            modulation_factor = exploration_signal * (1.0 - 0.5 * mood_stability)

            # Compute new epsilon
            epsilon_range = self.max_epsilon - self.min_epsilon
            epsilon = self.min_epsilon + epsilon_range * modulation_factor

        epsilon = max(self.min_epsilon, min(self.max_epsilon, epsilon))

        self.current_epsilon = epsilon
        self.last_modulation_time = datetime.now()
        self.modulation_count += 1

        logger.info(
            f"Epsilon modulated: {epsilon:.4f} (success_rate={success_rate:.2f}, "
            f"failure_streak={self.current_failure_streak})"
        )

        return epsilon

    def _compute_success_rate(self, window: Optional[int] = None) -> float:
        """Compute success rate from recent outcomes.

        Args:
            window: Window size (None = use all history)

        Returns:
            Success rate (0-1)
        """
        if not self.outcome_history:
            return 0.5  # Neutral

        outcomes = list(self.outcome_history)
        if window:
            outcomes = outcomes[-window:]

        successes = sum(1 for o in outcomes if o["outcome"] == ActionOutcome.SUCCESS.value)
        partials = sum(1 for o in outcomes if o["outcome"] == ActionOutcome.PARTIAL.value)

        # Count partials as 0.5 success
        success_score = successes + 0.5 * partials
        total = len(outcomes)

        return success_score / total if total > 0 else 0.5

    def should_explore(self, rng: Optional[Any] = None) -> bool:
        """Epsilon-greedy exploration decision.

        Args:
            rng: Random number generator (if None, uses random.random())

        Returns:
            True if should explore, False if should exploit
        """
        import random

        if rng is None:
            rng = random

        return rng.random() < self.current_epsilon

    def get_mood_assessment(self) -> str:
        """Get qualitative mood assessment based on outcomes.

        Returns:
            Mood description (optimistic/neutral/pessimistic/frustrated)
        """
        if not self.outcome_history:
            return "neutral"

        success_rate = self._compute_success_rate()

        if self.current_failure_streak >= self.failure_streak_threshold:
            return "frustrated"
        elif success_rate >= 0.7:
            return "optimistic"
        elif success_rate >= 0.4:
            return "neutral"
        else:
            return "pessimistic"

    def get_outcome_statistics(self, window: int = 100) -> Dict[str, Any]:
        """Get outcome statistics.

        Args:
            window: Window size for statistics

        Returns:
            Outcome statistics
        """
        if not self.outcome_history:
            return {"count": 0}

        recent_outcomes = list(self.outcome_history)[-window:]

        successes = sum(1 for o in recent_outcomes if o["outcome"] == ActionOutcome.SUCCESS.value)
        failures = sum(1 for o in recent_outcomes if o["outcome"] == ActionOutcome.FAILURE.value)
        partials = sum(1 for o in recent_outcomes if o["outcome"] == ActionOutcome.PARTIAL.value)

        total = len(recent_outcomes)

        return {
            "count": total,
            "successes": successes,
            "failures": failures,
            "partials": partials,
            "success_rate": successes / total if total > 0 else 0.0,
            "failure_rate": failures / total if total > 0 else 0.0,
            "current_failure_streak": self.current_failure_streak,
            "max_failure_streak": self.max_failure_streak,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Serotonin module status.

        Returns:
            Status dictionary
        """
        stats = self.get_outcome_statistics()
        mood = self.get_mood_assessment()

        return {
            "status": "operational",
            "current_epsilon": self.current_epsilon,
            "base_epsilon": self.base_epsilon,
            "epsilon_range": [self.min_epsilon, self.max_epsilon],
            "mood_assessment": mood,
            "modulation_count": self.modulation_count,
            "last_modulation": (self.last_modulation_time.isoformat() if self.last_modulation_time else "N/A"),
            "outcome_statistics": stats,
        }
