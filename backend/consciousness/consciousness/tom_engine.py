"""
Theory of Mind Engine

Infers user mental states from behavior and context.
Simplified model focusing on emotional state and intent inference.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4


class EmotionalState(str, Enum):
    """User emotional states."""

    NEUTRAL = "neutral"
    STRESSED = "stressed"
    CONFUSED = "confused"
    SATISFIED = "satisfied"
    FRUSTRATED = "frustrated"


@dataclass
class UserMentalState:
    """
    Represents inferred user mental state.

    Attributes:
        user_id: UUID of the user
        emotional_state: Inferred emotional state
        intent: Inferred user intent/goal
        confidence: Confidence in inference (0-1)
        needs_assistance: Whether user likely needs help
        inferred_at: When state was inferred
        context: Context used for inference
        state_id: Unique identifier
    """

    user_id: UUID
    emotional_state: EmotionalState
    intent: str
    confidence: float
    needs_assistance: bool = False
    inferred_at: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, any] = field(default_factory=dict)
    state_id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        """Validate confidence range."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")
        if not isinstance(self.emotional_state, EmotionalState):
            raise TypeError("emotional_state must be EmotionalState enum")


class ToMEngine:
    """
    Theory of Mind Engine for user mental state inference.

    Uses behavioral signals and context to infer:
    - Emotional state (stressed, confused, satisfied, etc.)
    - Intent/goals
    - Whether user needs assistance
    """

    def __init__(self):
        """Initialize ToM engine."""
        self._state_history: List[UserMentalState] = []

    def infer_state(
        self,
        user_id: UUID,
        behavioral_signals: Dict[str, any]
    ) -> UserMentalState:
        """
        Infer user mental state from behavioral signals.

        Args:
            user_id: User identifier
            behavioral_signals: Signals like error_count, response_time, retries, etc.

        Returns:
            UserMentalState with inferred state
        """
        # Extract signals
        error_count = behavioral_signals.get("error_count", 0)
        retry_count = behavioral_signals.get("retry_count", 0)
        response_time_ms = behavioral_signals.get("response_time_ms", 0)
        task_success = behavioral_signals.get("task_success", True)
        user_query = behavioral_signals.get("user_query", "")

        # Infer emotional state
        emotional_state, confidence = self._infer_emotion(
            error_count=error_count,
            retry_count=retry_count,
            response_time_ms=response_time_ms,
            task_success=task_success
        )

        # Infer intent
        intent = self._infer_intent(user_query, behavioral_signals)

        # Determine if user needs assistance
        needs_assistance = self._needs_assistance(
            emotional_state=emotional_state,
            error_count=error_count,
            retry_count=retry_count
        )

        # Create mental state
        state = UserMentalState(
            user_id=user_id,
            emotional_state=emotional_state,
            intent=intent,
            confidence=confidence,
            needs_assistance=needs_assistance,
            context=behavioral_signals
        )

        self._state_history.append(state)
        return state

    def _infer_emotion(
        self,
        error_count: int,
        retry_count: int,
        response_time_ms: int,
        task_success: bool
    ) -> tuple[EmotionalState, float]:
        """
        Infer emotional state from behavioral signals.

        Args:
            error_count: Number of errors
            retry_count: Number of retries
            response_time_ms: Response time
            task_success: Whether task succeeded

        Returns:
            (EmotionalState, confidence)
        """
        # High errors + retries = frustrated
        if error_count >= 3 and retry_count >= 2:
            return EmotionalState.FRUSTRATED, 0.85

        # Multiple retries but few errors = confused
        if retry_count >= 3 and error_count < 3:
            return EmotionalState.CONFUSED, 0.80

        # High errors but no retries = stressed
        if error_count >= 2 and retry_count == 0:
            return EmotionalState.STRESSED, 0.75

        # Long response time = possibly stressed
        if response_time_ms > 5000:
            return EmotionalState.STRESSED, 0.65

        # Task success = satisfied
        if task_success and error_count == 0:
            return EmotionalState.SATISFIED, 0.90

        # Default: neutral
        return EmotionalState.NEUTRAL, 0.70

    def _infer_intent(self, query: str, signals: Dict[str, any]) -> str:
        """
        Infer user intent from query and signals.

        Args:
            query: User query text
            signals: Behavioral signals

        Returns:
            Inferred intent string
        """
        if not query:
            return "unknown_intent"

        query_lower = query.lower()

        # Pattern matching for common intents
        if any(kw in query_lower for kw in ["help", "how", "what", "why"]):
            return "seeking_information"

        if any(kw in query_lower for kw in ["fix", "error", "problem", "issue"]):
            return "troubleshooting"

        if any(kw in query_lower for kw in ["create", "make", "build", "generate"]):
            return "creation_task"

        if any(kw in query_lower for kw in ["delete", "remove", "cancel"]):
            return "deletion_task"

        return "general_query"

    def _needs_assistance(
        self,
        emotional_state: EmotionalState,
        error_count: int,
        retry_count: int
    ) -> bool:
        """
        Determine if user likely needs assistance.

        Args:
            emotional_state: Inferred emotional state
            error_count: Number of errors
            retry_count: Number of retries

        Returns:
            True if user likely needs help
        """
        # Negative emotional states indicate need for help
        if emotional_state in [EmotionalState.FRUSTRATED, EmotionalState.CONFUSED, EmotionalState.STRESSED]:
            return True

        # Multiple errors/retries even if emotion unclear
        if error_count >= 2 or retry_count >= 3:
            return True

        return False

    def get_recent_states(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[UserMentalState]:
        """
        Get recent mental states.

        Args:
            user_id: Filter by user ID
            limit: Maximum states to return

        Returns:
            List of recent states
        """
        states = self._state_history

        if user_id:
            states = [s for s in states if s.user_id == user_id]

        # Sort by timestamp descending
        states = sorted(states, key=lambda s: s.inferred_at, reverse=True)
        return states[:limit]

    def clear_history(self):
        """Clear state history."""
        self._state_history.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"ToMEngine(states={len(self._state_history)})"
