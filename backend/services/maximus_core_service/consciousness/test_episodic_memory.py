"""
Episodic Memory Test Suite
==========================

Validates episodic memory storage, temporal binding, and autobiographical
narrative metrics as specified in the roadmap (retrieval accuracy >90%,
temporal order preservation, coherence >0.85).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

import pytest

from consciousness.autobiographical_narrative import AutobiographicalNarrative
from consciousness.episodic_memory import Episode, EpisodicMemory
from consciousness.temporal_binding import TemporalBinder


def _make_episode(
    focus: str,
    *,
    timestamp: datetime,
    salience: float = 0.8,
    confidence: float = 0.9,
    narrative: str | None = None,
) -> Episode:
    return Episode(
        episode_id=f"episode-{focus}-{timestamp.timestamp()}",
        timestamp=timestamp,
        focus_target=focus,
        salience=salience,
        confidence=confidence,
        narrative=narrative or f"Percebi {focus} com intensidade elevada.",
    )


class TestEpisodicMemory:
    """Unit tests for episodic memory store."""

    def test_record_and_latest(self):
        memory = EpisodicMemory(retention=5)
        base = datetime.now(timezone.utc)

        for idx in range(6):
            episode = _make_episode(
                focus=f"threat:{idx}",
                timestamp=base + timedelta(seconds=idx),
            )
            memory._episodes.append(episode)  # direct for speed

        latest = memory.latest(limit=3)
        assert len(latest) == 3
        assert latest[0].focus_target == "threat:3"
        assert latest[-1].focus_target == "threat:5"

    def test_temporal_order_preserved(self):
        memory = EpisodicMemory()
        base = datetime.now(timezone.utc)

        for idx in range(5):
            memory._episodes.append(
                _make_episode(
                    focus=f"maintenance:{idx}",
                    timestamp=base + timedelta(minutes=idx),
                )
            )

        assert memory.temporal_order_preserved()

    def test_episodic_accuracy_target(self):
        memory = EpisodicMemory()
        base = datetime.now(timezone.utc)
        focuses = [f"threat:{i}" for i in range(10)]
        for idx, focus in enumerate(focuses):
            memory._episodes.append(
                _make_episode(
                    focus=focus,
                    timestamp=base + timedelta(seconds=idx),
                )
            )

        accuracy = memory.episodic_accuracy(focuses)
        assert accuracy >= 0.9

    def test_coherence_score(self):
        memory = EpisodicMemory()
        base = datetime.now(timezone.utc)
        for idx in range(4):
            memory._episodes.append(
                _make_episode(
                    focus=f"threat:{idx}",
                    timestamp=base + timedelta(minutes=idx),
                    salience=0.85,
                    confidence=0.9,
                )
            )
        coherence = memory.coherence_score()
        assert 0.0 < coherence <= 1.0
        assert coherence >= 0.7


class TestTemporalBinding:
    """Tests for temporal binding coherence and focus stability."""

    def test_binding_links(self):
        binder = TemporalBinder()
        base = datetime.now(timezone.utc)
        episodes = [
            _make_episode("threat:a", timestamp=base),
            _make_episode("threat:b", timestamp=base + timedelta(seconds=30)),
        ]
        links = binder.bind(episodes)
        assert len(links) == 1
        assert math.isclose(links[0].delta_seconds, 30.0, rel_tol=1e-6)

    def test_temporal_coherence_metric(self):
        binder = TemporalBinder()
        base = datetime.now(timezone.utc)
        episodes = [
            _make_episode("threat:a", timestamp=base),
            _make_episode("threat:b", timestamp=base + timedelta(minutes=2)),
            _make_episode("threat:c", timestamp=base + timedelta(minutes=4)),
        ]
        coherence = binder.coherence(episodes, window_seconds=600.0)
        assert coherence >= 0.9

    def test_focus_stability(self):
        binder = TemporalBinder()
        base = datetime.now(timezone.utc)
        episodes = [
            _make_episode("threat:a", timestamp=base),
            _make_episode("threat:b", timestamp=base + timedelta(minutes=1)),
            _make_episode("maintenance:infra", timestamp=base + timedelta(minutes=2)),
        ]
        stability = binder.focus_stability(episodes)
        assert 0.0 <= stability <= 1.0
        assert stability >= 0.5


class TestAutobiographicalNarrative:
    """Tests for narrative building."""

    def test_narrative_coherence_target(self):
        memory = EpisodicMemory()
        base = datetime.now(timezone.utc)
        for idx in range(5):
            memory._episodes.append(
                _make_episode(
                    focus=f"threat:{idx}",
                    timestamp=base + timedelta(minutes=idx),
                    salience=0.9,
                    confidence=0.9,
                    narrative=f"Atuei mitigando ameaça {idx}.",
                )
            )
        builder = AutobiographicalNarrative()
        result = builder.build(memory.timeline())
        assert result.episode_count == 5
        assert result.coherence_score >= 0.85
        assert result.narrative.startswith("Às")

    def test_empty_narrative(self):
        builder = AutobiographicalNarrative()
        result = builder.build([])
        assert result.coherence_score == 0.0
        assert "Não há episódios" in result.narrative
