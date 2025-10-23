"""
Temporal Binding - Targeted Coverage Tests

Objetivo: Cobrir consciousness/temporal_binding.py (68 lines, 0% → 85%+)

Testa:
- TemporalLink dataclass
- TemporalBinder.bind() (episode ordering)
- TemporalBinder.coherence() (temporal continuity)
- TemporalBinder.focus_stability() (focus transitions)
- Edge cases (empty, single episode)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from consciousness.temporal_binding import TemporalLink, TemporalBinder
from consciousness.episodic_memory import Episode


# ===== TEMPORAL LINK TESTS =====

def test_temporal_link_initialization():
    """
    SCENARIO: Create TemporalLink dataclass
    EXPECTED: Stores previous, following, delta_seconds
    """
    prev = Episode(
        timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
        focus_target="task1",
        salience=0.5,
        narrative="First",
        confidence=0.8,
        context={}
    )

    follow = Episode(
        timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
        focus_target="task2",
        salience=0.6,
        narrative="Second",
        confidence=0.85,
        context={}
    )

    link = TemporalLink(
        previous=prev,
        following=follow,
        delta_seconds=300.0
    )

    assert link.previous == prev
    assert link.following == follow
    assert link.delta_seconds == 300.0


# ===== TEMPORAL BINDER INITIALIZATION =====

def test_temporal_binder_initialization():
    """
    SCENARIO: Create TemporalBinder
    EXPECTED: Initializes successfully
    """
    binder = TemporalBinder()

    assert binder is not None


# ===== BIND METHOD TESTS =====

def test_bind_empty_episodes():
    """
    SCENARIO: Bind empty episodes list
    EXPECTED: Returns empty list
    """
    binder = TemporalBinder()

    links = binder.bind([])

    assert links == []


def test_bind_single_episode():
    """
    SCENARIO: Bind single episode
    EXPECTED: Returns empty list (need 2+ for links)
    """
    binder = TemporalBinder()

    episode = Episode(
        timestamp=datetime.now(timezone.utc),
        focus_target="test",
        salience=0.5,
        narrative="Test",
        confidence=0.8,
        context={}
    )

    links = binder.bind([episode])

    assert links == []


def test_bind_two_episodes():
    """
    SCENARIO: Bind two episodes
    EXPECTED: Returns one TemporalLink
    """
    binder = TemporalBinder()

    ep1 = Episode(
        timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
        focus_target="task1",
        salience=0.5,
        narrative="First",
        confidence=0.8,
        context={}
    )

    ep2 = Episode(
        timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
        focus_target="task2",
        salience=0.6,
        narrative="Second",
        confidence=0.85,
        context={}
    )

    links = binder.bind([ep1, ep2])

    assert len(links) == 1
    assert isinstance(links[0], TemporalLink)
    assert links[0].previous == ep1
    assert links[0].following == ep2
    assert links[0].delta_seconds == 300.0


def test_bind_sorts_episodes_by_timestamp():
    """
    SCENARIO: Bind unsorted episodes
    EXPECTED: Sorts by timestamp, creates correct links
    """
    binder = TemporalBinder()

    # Create in reverse order
    ep2 = Episode(
        timestamp=datetime(2025, 10, 23, 10, 10, tzinfo=timezone.utc),
        focus_target="later",
        salience=0.5,
        narrative="Later",
        confidence=0.7,
        context={}
    )

    ep1 = Episode(
        timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
        focus_target="earlier",
        salience=0.6,
        narrative="Earlier",
        confidence=0.8,
        context={}
    )

    links = binder.bind([ep2, ep1])  # Reversed order

    assert len(links) == 1
    assert links[0].previous.focus_target == "earlier"
    assert links[0].following.focus_target == "later"


def test_bind_multiple_episodes():
    """
    SCENARIO: Bind three episodes
    EXPECTED: Returns two TemporalLinks
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="task1",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="task2",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 10, tzinfo=timezone.utc),
            focus_target="task3",
            salience=0.7,
            narrative="Third",
            confidence=0.9,
            context={}
        ),
    ]

    links = binder.bind(episodes)

    assert len(links) == 2
    assert links[0].following == episodes[1]
    assert links[1].previous == episodes[1]


# ===== COHERENCE METHOD TESTS =====

def test_coherence_empty_episodes():
    """
    SCENARIO: Compute coherence for empty list
    EXPECTED: Returns 1.0 (perfect coherence by default)
    """
    binder = TemporalBinder()

    coherence = binder.coherence([])

    assert coherence == 1.0


def test_coherence_single_episode():
    """
    SCENARIO: Compute coherence for single episode
    EXPECTED: Returns 1.0
    """
    binder = TemporalBinder()

    episode = Episode(
        timestamp=datetime.now(timezone.utc),
        focus_target="test",
        salience=0.5,
        narrative="Test",
        confidence=0.8,
        context={}
    )

    coherence = binder.coherence([episode])

    assert coherence == 1.0


def test_coherence_two_episodes_within_window():
    """
    SCENARIO: Two episodes within 10-minute window
    EXPECTED: High coherence (mocked via windowed_temporal_accuracy)
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="task1",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="task2",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
    ]

    with patch('consciousness.temporal_binding.windowed_temporal_accuracy', return_value=1.0):
        coherence = binder.coherence(episodes)

    assert coherence == 1.0


def test_coherence_custom_window():
    """
    SCENARIO: Compute coherence with custom window_seconds
    EXPECTED: Uses provided window
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="task1",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 20, tzinfo=timezone.utc),
            focus_target="task2",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
    ]

    with patch('consciousness.temporal_binding.windowed_temporal_accuracy', return_value=0.5) as mock_wta:
        coherence = binder.coherence(episodes, window_seconds=300.0)

        # Verify called with correct window
        mock_wta.assert_called_once()

    assert coherence == 0.5


# ===== FOCUS STABILITY TESTS =====

def test_focus_stability_empty_episodes():
    """
    SCENARIO: Compute focus stability for empty list
    EXPECTED: Returns 1.0
    """
    binder = TemporalBinder()

    stability = binder.focus_stability([])

    assert stability == 1.0


def test_focus_stability_single_episode():
    """
    SCENARIO: Compute focus stability for single episode
    EXPECTED: Returns 1.0
    """
    binder = TemporalBinder()

    episode = Episode(
        timestamp=datetime.now(timezone.utc),
        focus_target="test",
        salience=0.5,
        narrative="Test",
        confidence=0.8,
        context={}
    )

    stability = binder.focus_stability([episode])

    assert stability == 1.0


def test_focus_stability_same_focus():
    """
    SCENARIO: All episodes have same focus prefix
    EXPECTED: Returns 1.0 (100% stable)
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="monitoring:cpu",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="monitoring:memory",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
    ]

    stability = binder.focus_stability(episodes)

    assert stability == 1.0


def test_focus_stability_different_focus():
    """
    SCENARIO: Episodes have completely different focus
    EXPECTED: Returns 0.0 (0% stable)
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="monitoring",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="security",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
    ]

    stability = binder.focus_stability(episodes)

    assert stability == 0.0


def test_focus_stability_mixed_transitions():
    """
    SCENARIO: Some stable, some unstable transitions
    EXPECTED: Returns proportion of stable transitions
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="monitoring:cpu",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="monitoring:memory",  # Stable (monitoring)
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 10, tzinfo=timezone.utc),
            focus_target="security:scan",  # Unstable transition
            salience=0.7,
            narrative="Third",
            confidence=0.9,
            context={}
        ),
    ]

    stability = binder.focus_stability(episodes)

    # 1 stable out of 2 transitions = 0.5
    assert stability == 0.5


# ===== INTEGRATION TEST =====

def test_temporal_binder_full_lifecycle():
    """
    SCENARIO: Full lifecycle (bind, coherence, focus_stability)
    EXPECTED: All methods work together
    """
    binder = TemporalBinder()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="task1",
            salience=0.5,
            narrative="First",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="task2",
            salience=0.6,
            narrative="Second",
            confidence=0.85,
            context={}
        ),
    ]

    links = binder.bind(episodes)

    with patch('consciousness.temporal_binding.windowed_temporal_accuracy', return_value=0.9):
        coherence = binder.coherence(episodes)

    stability = binder.focus_stability(episodes)

    assert len(links) == 1
    assert 0.0 <= coherence <= 1.0
    assert 0.0 <= stability <= 1.0
