"""
Episodic Memory Core - Targeted Coverage Tests

Objetivo: Cobrir consciousness/episodic_memory/core.py (164 lines, 0% → 70%+)

Testa EpisodicMemory store, retrieval, temporal order, autobiographical coherence

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from consciousness.episodic_memory.core import Episode, EpisodicMemory, windowed_temporal_accuracy


# ===== EPISODE TESTS =====

def test_episode_initialization():
    """
    SCENARIO: Episode dataclass created with all fields
    EXPECTED: All attributes preserved
    """
    now = datetime.now()
    episode = Episode(
        episode_id="ep-123",
        timestamp=now,
        focus_target="task1",
        salience=0.8,
        confidence=0.9,
        narrative="Test narrative",
        metadata={"key": "value"},
    )

    assert episode.episode_id == "ep-123"
    assert episode.timestamp == now
    assert episode.focus_target == "task1"
    assert episode.salience == 0.8
    assert episode.confidence == 0.9
    assert episode.narrative == "Test narrative"
    assert episode.metadata == {"key": "value"}


def test_episode_to_dict_serialization():
    """
    SCENARIO: Episode.to_dict() serializes all fields
    EXPECTED: Dict with episode_id, timestamp (ISO), focus_target, etc.
    """
    now = datetime.now()
    episode = Episode(
        episode_id="ep-456",
        timestamp=now,
        focus_target="task2",
        salience=0.7,
        confidence=0.85,
        narrative="Test",
        metadata={"data": 123},
    )

    data = episode.to_dict()

    assert data["episode_id"] == "ep-456"
    assert data["timestamp"] == now.isoformat()
    assert data["focus_target"] == "task2"
    assert data["salience"] == 0.7
    assert data["confidence"] == 0.85
    assert data["narrative"] == "Test"
    assert data["metadata"] == {"data": 123}


# ===== EPISODIC MEMORY TESTS =====

def test_episodic_memory_initialization():
    """
    SCENARIO: EpisodicMemory created with default retention
    EXPECTED: Empty episodes list, retention = 1000
    """
    memory = EpisodicMemory()

    assert memory._retention == 1000
    assert len(memory._episodes) == 0


def test_episodic_memory_custom_retention():
    """
    SCENARIO: EpisodicMemory created with custom retention=100
    EXPECTED: Retention set to 100
    """
    memory = EpisodicMemory(retention=100)

    assert memory._retention == 100


def test_record_creates_episode():
    """
    SCENARIO: EpisodicMemory.record() with AttentionState + IntrospectiveSummary
    EXPECTED: Episode created and stored
    """
    memory = EpisodicMemory()

    attention = Mock()
    attention.focus_target = "task1"
    attention.salience_order = [("task1", 0.9)]
    attention.confidence = 0.85
    attention.modality_weights = {"visual": 0.8}
    attention.baseline_intensity = 0.5

    perspective = Mock()
    perspective.viewpoint = (1.0, 2.0, 3.0)
    perspective.orientation = (0.1, 0.2, 0.3)

    summary = Mock()
    summary.confidence = 0.9
    summary.narrative = "Test narrative"
    summary.perspective = perspective
    summary.boundary_stability = 0.95

    episode = memory.record(attention, summary)

    assert episode.focus_target == "task1"
    assert episode.salience == 0.9
    assert episode.confidence == 0.9
    assert episode.narrative == "Test narrative"
    assert len(memory._episodes) == 1


def test_record_with_context():
    """
    SCENARIO: EpisodicMemory.record() with additional context dict
    EXPECTED: Context merged into episode metadata
    """
    memory = EpisodicMemory()

    attention = Mock()
    attention.focus_target = "task1"
    attention.salience_order = []
    attention.confidence = 0.8
    attention.modality_weights = {}
    attention.baseline_intensity = 0.5

    perspective = Mock()
    perspective.viewpoint = (0.0, 0.0, 0.0)
    perspective.orientation = (0.0, 0.0, 0.0)

    summary = Mock()
    summary.confidence = 0.9
    summary.narrative = "Test"
    summary.perspective = perspective
    summary.boundary_stability = 0.9

    episode = memory.record(attention, summary, context={"extra": "data"})

    assert "extra" in episode.metadata
    assert episode.metadata["extra"] == "data"


def test_record_retention_limit():
    """
    SCENARIO: EpisodicMemory with retention=3, record 5 episodes
    EXPECTED: Oldest 2 episodes evicted, only 3 remain
    """
    memory = EpisodicMemory(retention=3)

    attention = Mock()
    attention.focus_target = "task"
    attention.salience_order = []
    attention.confidence = 0.8
    attention.modality_weights = {}
    attention.baseline_intensity = 0.5

    perspective = Mock()
    perspective.viewpoint = (0.0, 0.0, 0.0)
    perspective.orientation = (0.0, 0.0, 0.0)

    summary = Mock()
    summary.confidence = 0.9
    summary.narrative = "Test"
    summary.perspective = perspective
    summary.boundary_stability = 0.9

    for i in range(5):
        memory.record(attention, summary)

    assert len(memory._episodes) == 3


# ===== RETRIEVAL TESTS =====

def test_latest_returns_most_recent():
    """
    SCENARIO: EpisodicMemory.latest(limit=2) with 5 episodes
    EXPECTED: Last 2 episodes returned
    """
    memory = EpisodicMemory()

    attention = Mock()
    attention.focus_target = "task"
    attention.salience_order = []
    attention.confidence = 0.8
    attention.modality_weights = {}
    attention.baseline_intensity = 0.5

    perspective = Mock()
    perspective.viewpoint = (0.0, 0.0, 0.0)
    perspective.orientation = (0.0, 0.0, 0.0)

    summary = Mock()
    summary.confidence = 0.9
    summary.narrative = "Test"
    summary.perspective = perspective
    summary.boundary_stability = 0.9

    for _ in range(5):
        memory.record(attention, summary)

    latest = memory.latest(limit=2)

    assert len(latest) == 2


def test_between_filters_by_time_range():
    """
    SCENARIO: EpisodicMemory.between() with start/end datetime
    EXPECTED: Only episodes within range returned
    """
    memory = EpisodicMemory()

    # Create episodes manually with specific timestamps
    now = datetime.now()
    memory._episodes = [
        Episode("e1", now - timedelta(hours=2), "t1", 0.8, 0.9, "n1"),
        Episode("e2", now - timedelta(hours=1), "t2", 0.8, 0.9, "n2"),
        Episode("e3", now, "t3", 0.8, 0.9, "n3"),
    ]

    start = now - timedelta(hours=1, minutes=30)
    end = now - timedelta(minutes=30)

    episodes = memory.between(start, end)

    assert len(episodes) == 1
    assert episodes[0].episode_id == "e2"


def test_by_focus_filters_by_target():
    """
    SCENARIO: EpisodicMemory.by_focus("auth") searches focus_target
    EXPECTED: Only matching episodes returned (case-insensitive)
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "Authentication", 0.8, 0.9, "n1"),
        Episode("e2", now, "Database", 0.8, 0.9, "n2"),
        Episode("e3", now, "Auth Module", 0.8, 0.9, "n3"),
    ]

    auth_episodes = memory.by_focus("auth", limit=10)

    assert len(auth_episodes) == 2
    assert all("auth" in ep.focus_target.lower() for ep in auth_episodes)


def test_by_focus_respects_limit():
    """
    SCENARIO: EpisodicMemory.by_focus() with limit=1 when 2 match
    EXPECTED: Only 1 episode returned
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "task", 0.8, 0.9, "n1"),
        Episode("e2", now, "task", 0.8, 0.9, "n2"),
    ]

    episodes = memory.by_focus("task", limit=1)

    assert len(episodes) == 1


# ===== EPISODIC ACCURACY TESTS =====

def test_episodic_accuracy_perfect_match():
    """
    SCENARIO: EpisodicMemory.episodic_accuracy() with perfect focus sequence
    EXPECTED: Accuracy = 1.0
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "task1", 0.8, 0.9, "n1"),
        Episode("e2", now, "task2", 0.8, 0.9, "n2"),
        Episode("e3", now, "task3", 0.8, 0.9, "n3"),
    ]

    accuracy = memory.episodic_accuracy(["task1", "task2", "task3"])

    assert accuracy == 1.0


def test_episodic_accuracy_partial_match():
    """
    SCENARIO: EpisodicMemory.episodic_accuracy() with 2/3 matches
    EXPECTED: Accuracy = 0.666...
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "task1", 0.8, 0.9, "n1"),
        Episode("e2", now, "task2", 0.8, 0.9, "n2"),
        Episode("e3", now, "wrong", 0.8, 0.9, "n3"),
    ]

    accuracy = memory.episodic_accuracy(["task1", "task2", "task3"])

    assert abs(accuracy - 0.6666) < 0.01


def test_episodic_accuracy_empty_focuses():
    """
    SCENARIO: EpisodicMemory.episodic_accuracy([])
    EXPECTED: Accuracy = 0.0
    """
    memory = EpisodicMemory()

    accuracy = memory.episodic_accuracy([])

    assert accuracy == 0.0


# ===== TEMPORAL ORDER TESTS =====

def test_temporal_order_preserved_true():
    """
    SCENARIO: Episodes have strictly non-decreasing timestamps
    EXPECTED: temporal_order_preserved() = True
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "t1", 0.8, 0.9, "n1"),
        Episode("e2", now + timedelta(seconds=1), "t2", 0.8, 0.9, "n2"),
        Episode("e3", now + timedelta(seconds=2), "t3", 0.8, 0.9, "n3"),
    ]

    assert memory.temporal_order_preserved() is True


def test_temporal_order_preserved_false():
    """
    SCENARIO: Episodes have out-of-order timestamps
    EXPECTED: temporal_order_preserved() = False
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "t1", 0.8, 0.9, "n1"),
        Episode("e2", now - timedelta(seconds=1), "t2", 0.8, 0.9, "n2"),  # OUT OF ORDER
    ]

    assert memory.temporal_order_preserved() is False


# ===== COHERENCE SCORE TESTS =====

def test_coherence_score_high_quality():
    """
    SCENARIO: Episodes with high salience*confidence
    EXPECTED: High coherence score (~0.8)
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "t1", 0.9, 0.9, "n1"),  # 0.81
        Episode("e2", now, "t2", 0.8, 0.8, "n2"),  # 0.64
    ]

    score = memory.coherence_score()

    # Average = (0.81 + 0.64) / 2 = 0.725
    assert 0.7 <= score <= 0.8


def test_coherence_score_empty():
    """
    SCENARIO: EpisodicMemory with no episodes
    EXPECTED: Coherence score = 0.0
    """
    memory = EpisodicMemory()

    score = memory.coherence_score()

    assert score == 0.0


# ===== TIMELINE TESTS =====

def test_timeline_returns_all_episodes():
    """
    SCENARIO: EpisodicMemory.timeline() with 3 episodes
    EXPECTED: All 3 episodes returned in chronological order
    """
    memory = EpisodicMemory()

    now = datetime.now()
    memory._episodes = [
        Episode("e1", now, "t1", 0.8, 0.9, "n1"),
        Episode("e2", now, "t2", 0.8, 0.9, "n2"),
        Episode("e3", now, "t3", 0.8, 0.9, "n3"),
    ]

    timeline = memory.timeline()

    assert len(timeline) == 3


# ===== WINDOWED TEMPORAL ACCURACY TESTS =====

def test_windowed_temporal_accuracy_compliant():
    """
    SCENARIO: windowed_temporal_accuracy() with episodes within window
    EXPECTED: Accuracy = 1.0
    """
    now = datetime.now()
    episodes = [
        Episode("e1", now, "t1", 0.8, 0.9, "n1"),
        Episode("e2", now + timedelta(seconds=5), "t2", 0.8, 0.9, "n2"),
        Episode("e3", now + timedelta(seconds=10), "t3", 0.8, 0.9, "n3"),
    ]

    accuracy = windowed_temporal_accuracy(episodes, window=timedelta(seconds=15))

    assert accuracy == 1.0


def test_windowed_temporal_accuracy_non_compliant():
    """
    SCENARIO: windowed_temporal_accuracy() with episodes outside window
    EXPECTED: Accuracy < 1.0
    """
    now = datetime.now()
    episodes = [
        Episode("e1", now, "t1", 0.8, 0.9, "n1"),
        Episode("e2", now + timedelta(seconds=100), "t2", 0.8, 0.9, "n2"),  # TOO FAR
    ]

    accuracy = windowed_temporal_accuracy(episodes, window=timedelta(seconds=10))

    assert accuracy == 0.0


def test_windowed_temporal_accuracy_single_episode():
    """
    SCENARIO: windowed_temporal_accuracy() with only 1 episode
    EXPECTED: Accuracy = 1.0 (trivially compliant)
    """
    episodes = [Episode("e1", datetime.now(), "t1", 0.8, 0.9, "n1")]

    accuracy = windowed_temporal_accuracy(episodes, window=timedelta(seconds=10))

    assert accuracy == 1.0


def test_docstring_tulving_reference():
    """
    SCENARIO: Module documents Tulving's mental time travel theory
    EXPECTED: Mentions "mental time travel", "Tulving 2002"
    """
    import consciousness.episodic_memory.core as module

    assert "mental time travel" in module.__doc__
    assert "Tulving 2002" in module.__doc__
    assert "autobiographical coherence" in module.__doc__
