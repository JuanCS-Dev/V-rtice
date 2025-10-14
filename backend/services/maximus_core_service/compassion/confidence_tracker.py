"""
Confidence Tracker - Temporal Decay for ToM Beliefs
====================================================

Tracks confidence in ToM beliefs using exponential temporal decay.
Implements GAP 2 from ToM Engine refinement directive (FASE 2).

Formula: confidence = max(e^(-λ * hours_since_update), min_confidence)

where:
- λ (lambda): Decay rate per hour (default: 0.01)
- min_confidence: Minimum confidence floor (default: 0.1)

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import math
from datetime import datetime, timedelta
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ConfidenceTracker:
    """Tracks confidence in ToM beliefs with exponential temporal decay.

    Beliefs decay over time according to e^(-λt) formula, representing
    decreasing certainty about stale mental state inferences.

    Attributes:
        decay_lambda: Decay rate per hour (default: 0.01)
        min_confidence: Minimum confidence floor (default: 0.1)
    """

    def __init__(self, decay_lambda: float = 0.01, min_confidence: float = 0.1):
        """Initialize ConfidenceTracker.

        Args:
            decay_lambda: Decay rate per hour (higher = faster decay)
            min_confidence: Minimum confidence threshold [0.0, 1.0]
        """
        if decay_lambda < 0.0:
            raise ValueError(f"decay_lambda must be >= 0, got {decay_lambda}")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(f"min_confidence must be in [0, 1], got {min_confidence}")

        self.decay_lambda = decay_lambda
        self.min_confidence = min_confidence

        # Storage: (agent_id, belief_key) → [timestamps]
        # We keep list of timestamps to track update history
        self._timestamps: Dict[Tuple[str, str], List[datetime]] = {}

        logger.info(
            f"ConfidenceTracker initialized: λ={decay_lambda}, min={min_confidence}"
        )

    async def record_belief(
        self, agent_id: str, belief_key: str, value: float
    ) -> None:
        """Record a belief update with current timestamp.

        Args:
            agent_id: Unique identifier for agent
            belief_key: Belief identifier (e.g., "confusion_history")
            value: Belief value [0.0, 1.0] (not used for confidence, just for API consistency)
        """
        key = (agent_id, belief_key)
        now = datetime.utcnow()

        if key not in self._timestamps:
            self._timestamps[key] = []

        self._timestamps[key].append(now)

        logger.debug(
            f"Recorded belief: agent={agent_id}, key={belief_key}, timestamp={now}"
        )

    def calculate_confidence(self, agent_id: str, belief_key: str) -> float:
        """Calculate current confidence for a belief using temporal decay.

        Formula: confidence = max(e^(-λ * hours_since_last_update), min_confidence)

        Args:
            agent_id: Agent identifier
            belief_key: Belief identifier

        Returns:
            Confidence score [min_confidence, 1.0]
        """
        key = (agent_id, belief_key)

        # Never recorded → minimum confidence
        if key not in self._timestamps or not self._timestamps[key]:
            return self.min_confidence

        # Get latest timestamp
        latest_timestamp = self._timestamps[key][-1]

        # Calculate hours since last update
        now = datetime.utcnow()
        hours_since = (now - latest_timestamp).total_seconds() / 3600.0

        # Apply exponential decay: e^(-λt)
        if self.decay_lambda == 0.0:
            # No decay
            confidence = 1.0
        else:
            confidence = math.exp(-self.decay_lambda * hours_since)

        # Clamp to minimum confidence
        confidence = max(confidence, self.min_confidence)

        logger.debug(
            f"Confidence: agent={agent_id}, key={belief_key}, "
            f"hours_since={hours_since:.2f}, confidence={confidence:.3f}"
        )

        return confidence

    def get_timestamps(self, agent_id: str, belief_key: str) -> List[datetime]:
        """Get all recorded timestamps for a belief.

        Args:
            agent_id: Agent identifier
            belief_key: Belief identifier

        Returns:
            List of timestamps (may be empty if never recorded)
        """
        key = (agent_id, belief_key)
        return self._timestamps.get(key, []).copy()

    def get_confidence_scores(self, agent_id: str) -> Dict[str, float]:
        """Get confidence scores for all beliefs of an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Dictionary mapping belief_key → confidence score
        """
        scores = {}

        for (aid, belief_key), timestamps in self._timestamps.items():
            if aid == agent_id:
                scores[belief_key] = self.calculate_confidence(agent_id, belief_key)

        return scores

    def clear_old_beliefs(self, max_age_hours: float) -> int:
        """Clear beliefs older than max_age_hours.

        Args:
            max_age_hours: Maximum age threshold in hours

        Returns:
            Number of beliefs cleared
        """
        now = datetime.utcnow()
        threshold = now - timedelta(hours=max_age_hours)

        keys_to_remove = []

        for key, timestamps in self._timestamps.items():
            # Remove if latest timestamp is older than threshold
            if timestamps and timestamps[-1] < threshold:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._timestamps[key]

        logger.info(f"Cleared {len(keys_to_remove)} old beliefs (>{max_age_hours}h)")

        return len(keys_to_remove)

    def __repr__(self) -> str:
        total_beliefs = len(self._timestamps)
        return (
            f"ConfidenceTracker(decay_lambda={self.decay_lambda}, "
            f"min_confidence={self.min_confidence}, "
            f"total_beliefs={total_beliefs})"
        )
