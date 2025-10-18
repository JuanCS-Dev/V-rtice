"""
Episodic Memory Store
=====================

Manages time-indexed conscious episodes for MAXIMUS. Each episode captures
attentional focus, salience, self-narrative, and contextual metadata that
enable mental time travel (Tulving 2002) and autobiographical coherence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence
from uuid import uuid4

from consciousness.mea.attention_schema import AttentionState
from consciousness.mea.self_model import IntrospectiveSummary


@dataclass(slots=True)
class Episode:
    """Represents a single conscious episode."""

    episode_id: str
    timestamp: datetime
    focus_target: str
    salience: float
    confidence: float
    narrative: str
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        """Serialize episode to dictionary for storage or logging."""
        return {
            "episode_id": self.episode_id,
            "timestamp": self.timestamp.isoformat(),
            "focus_target": self.focus_target,
            "salience": self.salience,
            "confidence": self.confidence,
            "narrative": self.narrative,
            "metadata": self.metadata,
        }


class EpisodicMemory:
    """
    Stores and retrieves conscious episodes with temporal guarantees.
    """

    def __init__(self, retention: int = 1000):
        self._episodes: List[Episode] = []
        self._retention = retention

    # ------------------------------------------------------------------ #
    # Recording
    # ------------------------------------------------------------------ #

    def record(
        self,
        attention_state: AttentionState,
        summary: IntrospectiveSummary,
        *,
        context: Optional[Dict[str, object]] = None,
    ) -> Episode:
        """
        Record a new episode derived from MEA attention + self narrative.
        """
        episode = Episode(
            episode_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            focus_target=attention_state.focus_target,
            salience=attention_state.salience_order[0][1]
            if attention_state.salience_order
            else attention_state.confidence,
            confidence=summary.confidence,
            narrative=summary.narrative,
            metadata={
                "modalities": attention_state.modality_weights,
                "baseline_intensity": attention_state.baseline_intensity,
                "perspective_viewpoint": summary.perspective.viewpoint,
                "perspective_orientation": summary.perspective.orientation,
                "boundary_stability": summary.boundary_stability,
                **(context or {}),
            },
        )

        self._episodes.append(episode)
        if len(self._episodes) > self._retention:
            self._episodes.pop(0)
        return episode

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #

    def latest(self, limit: int = 10) -> List[Episode]:
        """Return most recent episodes."""
        return list(self._episodes[-limit:])

    def between(self, start: datetime, end: datetime) -> List[Episode]:
        """Return episodes within a time range."""
        return [episode for episode in self._episodes if start <= episode.timestamp <= end]

    def by_focus(self, target: str, limit: int = 20) -> List[Episode]:
        """Return episodes that match focus target."""
        target_lower = target.lower()
        return [
            episode
            for episode in reversed(self._episodes)
            if target_lower in episode.focus_target.lower()
        ][:limit]

    def episodic_accuracy(self, focuses: Sequence[str]) -> float:
        """
        Compute retrieval accuracy compared to expected sequence of focuses.
        """
        if not focuses:
            return 0.0
        episodes = self.latest(len(focuses))
        matches = sum(
            1 for episode, expected in zip(episodes, focuses) if expected.lower() in episode.focus_target.lower()
        )
        return matches / len(focuses)

    def temporal_order_preserved(self, window: int = 20) -> bool:
        """Validate that timestamps are strictly non-decreasing in recent window."""
        episodes = self.latest(window)
        return all(
            earlier.timestamp <= later.timestamp
            for earlier, later in zip(episodes, episodes[1:])
        )

    def coherence_score(self, window: int = 20) -> float:
        """
        Compute autobiographical coherence: weighted average of salience*confidence
        normalized by number of episodes.
        """
        episodes = self.latest(window)
        if not episodes:
            return 0.0
        total = sum(ep.salience * ep.confidence for ep in episodes)
        return max(0.0, min(1.0, total / len(episodes)))

    def timeline(self) -> List[Episode]:
        """Return all episodes in chronological order."""
        return list(self._episodes)


def windowed_temporal_accuracy(
    episodes: Sequence[Episode],
    window: timedelta,
) -> float:
    """
    Compute proportion of episodes whose successor occurs within the expected window.
    """
    if len(episodes) < 2:
        return 1.0
    compliant = sum(
        1
        for current, nxt in zip(episodes, episodes[1:])
        if timedelta(0) <= (nxt.timestamp - current.timestamp) <= window
    )
    return compliant / (len(episodes) - 1)
