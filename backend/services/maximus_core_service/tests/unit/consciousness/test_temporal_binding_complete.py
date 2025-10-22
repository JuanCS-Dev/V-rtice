"""
Complete tests for consciousness/temporal_binding.py

Target: 51.9% → 95%+ coverage (13 missing lines)
Zero mocks - Padrão Pagani Absoluto
"""

from datetime import datetime, timedelta

import pytest

from consciousness.episodic_memory import Episode
from consciousness.temporal_binding import TemporalBinder, TemporalLink


@pytest.fixture
def sample_episodes():
    """Create sample episodes for testing."""
    base_time = datetime(2025, 10, 22, 12, 0, 0)
    return [
        Episode(
            episode_id="ep1",
            timestamp=base_time,
            focus_target="task:coding",
            salience=0.9,
            confidence=0.9,
            narrative="Writing tests",
        ),
        Episode(
            episode_id="ep2",
            timestamp=base_time + timedelta(minutes=5),
            focus_target="task:coding",
            salience=0.85,
            confidence=0.85,
            narrative="Running tests",
        ),
        Episode(
            episode_id="ep3",
            timestamp=base_time + timedelta(minutes=10),
            focus_target="task:debugging",
            salience=0.8,
            confidence=0.8,
            narrative="Fixing bugs",
        ),
    ]


@pytest.fixture
def binder():
    """Create temporal binder instance."""
    return TemporalBinder()


class TestTemporalLink:
    """Test TemporalLink dataclass."""

    def test_temporal_link_creation(self, sample_episodes):
        """Test creating a temporal link."""
        prev_ep, next_ep = sample_episodes[0], sample_episodes[1]
        delta = (next_ep.timestamp - prev_ep.timestamp).total_seconds()

        link = TemporalLink(
            previous=prev_ep,
            following=next_ep,
            delta_seconds=delta,
        )

        assert link.previous == prev_ep
        assert link.following == next_ep
        assert link.delta_seconds == 300.0  # 5 minutes


class TestTemporalBinder:
    """Test TemporalBinder functionality."""

    def test_bind_empty_list(self, binder):
        """Test binding with empty list."""
        result = binder.bind([])
        assert result == []

    def test_bind_single_episode(self, binder, sample_episodes):
        """Test binding with single episode."""
        result = binder.bind([sample_episodes[0]])
        assert result == []

    def test_bind_two_episodes(self, binder, sample_episodes):
        """Test binding two episodes."""
        result = binder.bind(sample_episodes[:2])

        assert len(result) == 1
        assert result[0].previous == sample_episodes[0]
        assert result[0].following == sample_episodes[1]
        assert result[0].delta_seconds == 300.0

    def test_bind_multiple_episodes(self, binder, sample_episodes):
        """Test binding multiple episodes."""
        result = binder.bind(sample_episodes)

        assert len(result) == 2
        assert result[0].previous == sample_episodes[0]
        assert result[0].following == sample_episodes[1]
        assert result[1].previous == sample_episodes[1]
        assert result[1].following == sample_episodes[2]

    def test_bind_unsorted_episodes(self, binder):
        """Test that bind sorts episodes by timestamp."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep3",
                timestamp=base_time + timedelta(minutes=10),
                focus_target="task:c",
                salience=0.8,
                confidence=0.8,
                narrative="C",
            ),
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:a",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="task:b",
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
        ]

        result = binder.bind(episodes)

        # Should be sorted by timestamp
        assert result[0].previous.narrative == "A"
        assert result[0].following.narrative == "B"
        assert result[1].previous.narrative == "B"
        assert result[1].following.narrative == "C"

    def test_coherence_empty_list(self, binder):
        """Test coherence with empty list."""
        result = binder.coherence([])
        assert result == 1.0

    def test_coherence_single_episode(self, binder, sample_episodes):
        """Test coherence with single episode."""
        result = binder.coherence([sample_episodes[0]])
        assert result == 1.0

    def test_coherence_within_window(self, binder, sample_episodes):
        """Test coherence when all episodes are within window."""
        # All episodes within 10 minutes (default window is 600 seconds)
        result = binder.coherence(sample_episodes)
        assert result == 1.0

    def test_coherence_outside_window(self, binder):
        """Test coherence when episodes exceed window."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:a",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=20),  # Outside default 10min window
                focus_target="task:b",
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
        ]

        result = binder.coherence(episodes, window_seconds=600.0)
        # Should be < 1.0 because gap exceeds window
        assert 0.0 <= result < 1.0

    def test_coherence_custom_window(self, binder, sample_episodes):
        """Test coherence with custom window."""
        # Use a very small window (1 minute = 60 seconds)
        result = binder.coherence(sample_episodes, window_seconds=60.0)
        # Episodes are 5 and 10 minutes apart, exceeds 1 minute window
        assert 0.0 <= result < 1.0

    def test_focus_stability_empty(self, binder):
        """Test focus stability with empty list."""
        result = binder.focus_stability([])
        assert result == 1.0

    def test_focus_stability_single_episode(self, binder, sample_episodes):
        """Test focus stability with single episode."""
        result = binder.focus_stability([sample_episodes[0]])
        assert result == 1.0

    def test_focus_stability_stable_focus(self, binder):
        """Test focus stability when focus is stable."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:coding",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="task:coding",  # Same prefix
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
            Episode(
                episode_id="ep3",
                timestamp=base_time + timedelta(minutes=10),
                focus_target="task:testing",  # Same prefix (task)
                salience=0.8,
                confidence=0.8,
                narrative="C",
            ),
        ]

        result = binder.focus_stability(episodes)
        # All transitions have same prefix "task"
        assert result == 1.0

    def test_focus_stability_unstable_focus(self, binder):
        """Test focus stability when focus changes."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:coding",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="user:input",  # Different prefix
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
            Episode(
                episode_id="ep3",
                timestamp=base_time + timedelta(minutes=10),
                focus_target="system:monitor",  # Different prefix
                salience=0.8,
                confidence=0.8,
                narrative="C",
            ),
        ]

        result = binder.focus_stability(episodes)
        # No stable transitions (0/2)
        assert result == 0.0

    def test_focus_stability_partial(self, binder):
        """Test focus stability with mixed stability."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="task:coding",
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="task:testing",  # Same prefix (stable)
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
            Episode(
                episode_id="ep3",
                timestamp=base_time + timedelta(minutes=10),
                focus_target="user:input",  # Different prefix (unstable)
                salience=0.8,
                confidence=0.8,
                narrative="C",
            ),
        ]

        result = binder.focus_stability(episodes)
        # 1 stable out of 2 transitions
        assert result == 0.5

    def test_focus_stability_case_insensitive(self, binder):
        """Test that focus stability is case-insensitive."""
        base_time = datetime(2025, 10, 22, 12, 0, 0)
        episodes = [
            Episode(
                episode_id="ep1",
                timestamp=base_time,
                focus_target="Task:Coding",  # Capital T
                salience=0.9,
                confidence=0.9,
                narrative="A",
            ),
            Episode(
                episode_id="ep2",
                timestamp=base_time + timedelta(minutes=5),
                focus_target="task:Testing",  # Lowercase t
                salience=0.85,
                confidence=0.85,
                narrative="B",
            ),
        ]

        result = binder.focus_stability(episodes)
        # Should treat "Task" and "task" as same prefix
        assert result == 1.0


class TestTemporalBinderIntegration:
    """Integration tests for complete workflows."""

    def test_bind_and_analyze_coherence(self, binder, sample_episodes):
        """Test binding episodes and analyzing coherence."""
        links = binder.bind(sample_episodes)
        coherence = binder.coherence(sample_episodes)
        stability = binder.focus_stability(sample_episodes)

        assert len(links) == 2
        assert coherence == 1.0  # All within window
        assert stability > 0.0  # Some focus stability

    def test_empty_episode_handling(self, binder):
        """Test handling of empty episode lists across all methods."""
        assert binder.bind([]) == []
        assert binder.coherence([]) == 1.0
        assert binder.focus_stability([]) == 1.0
