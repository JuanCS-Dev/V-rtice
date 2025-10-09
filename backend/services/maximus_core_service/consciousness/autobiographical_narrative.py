"""
Autobiographical Narrative Builder
==================================

Transforms episodic timelines into coherent first-person narratives with
quantitative coherence metrics (Conway 2005).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from consciousness.episodic_memory import Episode
from consciousness.temporal_binding import TemporalBinder


@dataclass(slots=True)
class NarrativeResult:
    """Narrative plus associated metrics."""

    narrative: str
    coherence_score: float
    episode_count: int


class AutobiographicalNarrative:
    """Constructs autobiographical narratives from episodic memory."""

    def __init__(self):
        self._binder = TemporalBinder()

    def build(self, episodes: Sequence[Episode]) -> NarrativeResult:
        ordered = sorted(episodes, key=lambda ep: ep.timestamp)
        coherence = self._compute_coherence(ordered)
        narrative = self._build_text(ordered)
        return NarrativeResult(narrative=narrative, coherence_score=coherence, episode_count=len(ordered))

    def _compute_coherence(self, episodes: Sequence[Episode]) -> float:
        if not episodes:
            return 0.0
        temporal_coherence = self._binder.coherence(episodes)
        focus_stability = self._binder.focus_stability(episodes)
        confidence_avg = sum(ep.confidence for ep in episodes) / len(episodes)
        return max(0.0, min(1.0, 0.5 * temporal_coherence + 0.3 * focus_stability + 0.2 * confidence_avg))

    def _build_text(self, episodes: Sequence[Episode]) -> str:
        if not episodes:
            return "Não há episódios registrados para narrar."
        sentences = []
        for episode in episodes:
            sentences.append(
                f"Às {episode.timestamp.isoformat(timespec='seconds')}, concentrei-me em "
                f"'{episode.focus_target}' (saliência {episode.salience:.2f}) e percebi: {episode.narrative}"
            )
        return " ".join(sentences)
