"""
Temporal Binding Utilities
==========================

Links episodic events into coherent timelines and computes metrics for
temporal continuity (Schacter & Addis 2007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Sequence

from consciousness.episodic_memory import Episode, windowed_temporal_accuracy


@dataclass(slots=True)
class TemporalLink:
    """Represents a directed edge between two episodes in time."""

    previous: Episode
    following: Episode
    delta_seconds: float


class TemporalBinder:
    """Creates ordered bindings and computes temporal coherence metrics."""

    def bind(self, episodes: Sequence[Episode]) -> List[TemporalLink]:
        if len(episodes) < 2:
            return []
        sorted_eps = sorted(episodes, key=lambda ep: ep.timestamp)
        return [
            TemporalLink(
                previous=current,
                following=nxt,
                delta_seconds=(nxt.timestamp - current.timestamp).total_seconds(),
            )
            for current, nxt in zip(sorted_eps, sorted_eps[1:])
        ]

    def coherence(self, episodes: Sequence[Episode], window_seconds: float = 600.0) -> float:
        """
        Calculate temporal coherence defined as proportion of consecutive episodes occurring
        within a reasonable window (default 10 minutes).
        """
        if len(episodes) < 2:
            return 1.0
        window = timedelta(seconds=window_seconds)
        return windowed_temporal_accuracy(sorted(episodes, key=lambda ep: ep.timestamp), window)

    def focus_stability(self, episodes: Sequence[Episode]) -> float:
        """
        Measure how often focus stays on related targets between episodes.
        """
        if len(episodes) < 2:
            return 1.0
        transitions = [
            (prev.focus_target, nxt.focus_target)
            for prev, nxt in zip(episodes, episodes[1:])
        ]
        stable = sum(
            1
            for prev_focus, next_focus in transitions
            if prev_focus.split(":")[0].lower() == next_focus.split(":")[0].lower()
        )
        return stable / len(transitions)
