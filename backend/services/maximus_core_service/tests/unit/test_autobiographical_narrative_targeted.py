"""
Autobiographical Narrative - Targeted Coverage Tests

Objetivo: Cobrir consciousness/autobiographical_narrative.py (56 lines, 0% → 80%+)

Testa:
- NarrativeResult dataclass
- AutobiographicalNarrative initialization
- build() method (episodes → narrative)
- _compute_coherence() (temporal, focus, confidence)
- _build_text() (Portuguese narrative generation)
- Edge cases (empty episodes, single episode)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from consciousness.autobiographical_narrative import (
    NarrativeResult,
    AutobiographicalNarrative
)
from consciousness.episodic_memory import Episode


# ===== NARRATIVE RESULT TESTS =====

def test_narrative_result_initialization():
    """
    SCENARIO: Create NarrativeResult dataclass
    EXPECTED: Stores narrative, coherence_score, episode_count
    """
    result = NarrativeResult(
        narrative="Test narrative",
        coherence_score=0.85,
        episode_count=5
    )

    assert result.narrative == "Test narrative"
    assert result.coherence_score == 0.85
    assert result.episode_count == 5


def test_narrative_result_slots():
    """
    SCENARIO: Check NarrativeResult uses slots (memory optimization)
    EXPECTED: __slots__ defined
    """
    result = NarrativeResult("test", 0.5, 1)

    # Slots optimization - no __dict__
    assert hasattr(NarrativeResult, '__slots__')


# ===== AUTOBIOGRAPHICAL NARRATIVE INITIALIZATION =====

def test_autobiographical_narrative_initialization():
    """
    SCENARIO: Create AutobiographicalNarrative
    EXPECTED: Initializes with TemporalBinder
    """
    narrative_builder = AutobiographicalNarrative()

    assert narrative_builder._binder is not None


# ===== BUILD METHOD TESTS =====

def test_build_empty_episodes():
    """
    SCENARIO: Build narrative with empty episodes list
    EXPECTED: Returns narrative with coherence 0.0, episode_count 0
    """
    narrative_builder = AutobiographicalNarrative()

    result = narrative_builder.build([])

    assert result.episode_count == 0
    assert result.coherence_score == 0.0
    assert "Não há episódios" in result.narrative


def test_build_single_episode():
    """
    SCENARIO: Build narrative with single episode
    EXPECTED: Returns valid narrative with episode details
    """
    narrative_builder = AutobiographicalNarrative()

    episode = Episode(
        timestamp=datetime(2025, 10, 23, 10, 30, tzinfo=timezone.utc),
        focus_target="system_monitoring",
        salience=0.75,
        narrative="CPU usage increased to 85%",
        confidence=0.9,
        context={}
    )

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.8):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.7):
            result = narrative_builder.build([episode])

    assert result.episode_count == 1
    assert "system_monitoring" in result.narrative
    assert "saliência 0.75" in result.narrative
    assert "CPU usage increased" in result.narrative


def test_build_multiple_episodes():
    """
    SCENARIO: Build narrative with multiple episodes
    EXPECTED: Joins episodes into coherent narrative
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="target1",
            salience=0.6,
            narrative="Event 1",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="target2",
            salience=0.7,
            narrative="Event 2",
            confidence=0.85,
            context={}
        ),
    ]

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.75):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.65):
            result = narrative_builder.build(episodes)

    assert result.episode_count == 2
    assert "target1" in result.narrative
    assert "target2" in result.narrative
    assert "Event 1" in result.narrative
    assert "Event 2" in result.narrative


def test_build_sorts_episodes_by_timestamp():
    """
    SCENARIO: Build narrative with unsorted episodes
    EXPECTED: Episodes ordered by timestamp in narrative
    """
    narrative_builder = AutobiographicalNarrative()

    # Create episodes in reverse chronological order
    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 10, tzinfo=timezone.utc),
            focus_target="later",
            salience=0.5,
            narrative="Later event",
            confidence=0.7,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="earlier",
            salience=0.6,
            narrative="Earlier event",
            confidence=0.8,
            context={}
        ),
    ]

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.7):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.6):
            result = narrative_builder.build(episodes)

    # Check earlier event appears before later event
    earlier_pos = result.narrative.find("Earlier event")
    later_pos = result.narrative.find("Later event")

    assert earlier_pos < later_pos


# ===== COMPUTE COHERENCE TESTS =====

def test_compute_coherence_empty_episodes():
    """
    SCENARIO: Compute coherence for empty list
    EXPECTED: Returns 0.0
    """
    narrative_builder = AutobiographicalNarrative()

    coherence = narrative_builder._compute_coherence([])

    assert coherence == 0.0


def test_compute_coherence_formula():
    """
    SCENARIO: Compute coherence with mocked binder
    EXPECTED: Applies weighted formula (0.5*temporal + 0.3*focus + 0.2*confidence)
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="test",
            salience=0.5,
            narrative="Test",
            confidence=0.9,  # Average confidence = 0.9
            context={}
        )
    ]

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.8):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.6):
            coherence = narrative_builder._compute_coherence(episodes)

    # Expected: 0.5 * 0.8 + 0.3 * 0.6 + 0.2 * 0.9 = 0.4 + 0.18 + 0.18 = 0.76
    assert abs(coherence - 0.76) < 0.01


def test_compute_coherence_clamped_to_0_1():
    """
    SCENARIO: Compute coherence that would exceed [0, 1]
    EXPECTED: Clamped to 0.0-1.0 range
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime.now(timezone.utc),
            focus_target="test",
            salience=0.5,
            narrative="Test",
            confidence=1.0,
            context={}
        )
    ]

    # Mock extremely high values
    with patch.object(narrative_builder._binder, 'coherence', return_value=1.5):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=1.5):
            coherence = narrative_builder._compute_coherence(episodes)

    assert 0.0 <= coherence <= 1.0


def test_compute_coherence_multiple_episodes_average_confidence():
    """
    SCENARIO: Compute coherence with multiple episodes
    EXPECTED: Uses average confidence across all episodes
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="test",
            salience=0.5,
            narrative="Test",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 1, tzinfo=timezone.utc),
            focus_target="test",
            salience=0.5,
            narrative="Test",
            confidence=1.0,
            context={}
        ),
    ]

    # Average confidence = (0.8 + 1.0) / 2 = 0.9

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.5):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.5):
            coherence = narrative_builder._compute_coherence(episodes)

    # Expected: 0.5 * 0.5 + 0.3 * 0.5 + 0.2 * 0.9 = 0.25 + 0.15 + 0.18 = 0.58
    assert abs(coherence - 0.58) < 0.01


# ===== BUILD TEXT TESTS =====

def test_build_text_empty_episodes():
    """
    SCENARIO: Build text with empty episodes
    EXPECTED: Returns Portuguese message "Não há episódios"
    """
    narrative_builder = AutobiographicalNarrative()

    text = narrative_builder._build_text([])

    assert "Não há episódios" in text


def test_build_text_single_episode_format():
    """
    SCENARIO: Build text with single episode
    EXPECTED: Includes timestamp, focus_target, salience, narrative in Portuguese
    """
    narrative_builder = AutobiographicalNarrative()

    episode = Episode(
        timestamp=datetime(2025, 10, 23, 14, 30, 0, tzinfo=timezone.utc),
        focus_target="error_detection",
        salience=0.88,
        narrative="Detected critical error in module X",
        confidence=0.9,
        context={}
    )

    text = narrative_builder._build_text([episode])

    assert "Às 2025-10-23T14:30:00" in text
    assert "error_detection" in text
    assert "saliência 0.88" in text
    assert "Detected critical error" in text


def test_build_text_multiple_episodes_joined():
    """
    SCENARIO: Build text with multiple episodes
    EXPECTED: Sentences joined with spaces
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="task1",
            salience=0.5,
            narrative="First event",
            confidence=0.8,
            context={}
        ),
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 5, tzinfo=timezone.utc),
            focus_target="task2",
            salience=0.6,
            narrative="Second event",
            confidence=0.85,
            context={}
        ),
    ]

    text = narrative_builder._build_text(episodes)

    # Check both episodes present
    assert "task1" in text
    assert "task2" in text
    assert "First event" in text
    assert "Second event" in text

    # Check they're joined (no line breaks between sentences)
    assert "\n" not in text


# ===== INTEGRATION TESTS =====

def test_full_narrative_build_lifecycle():
    """
    SCENARIO: Full lifecycle (build with episodes)
    EXPECTED: Returns NarrativeResult with all fields populated
    """
    narrative_builder = AutobiographicalNarrative()

    episodes = [
        Episode(
            timestamp=datetime(2025, 10, 23, 10, 0, tzinfo=timezone.utc),
            focus_target="monitoring",
            salience=0.7,
            narrative="System started",
            confidence=0.9,
            context={}
        )
    ]

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.8):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.7):
            result = narrative_builder.build(episodes)

    assert isinstance(result, NarrativeResult)
    assert result.episode_count == 1
    assert result.coherence_score > 0.0
    assert len(result.narrative) > 0


def test_narrative_builder_reusable():
    """
    SCENARIO: Use same builder for multiple build() calls
    EXPECTED: Each call returns independent result
    """
    narrative_builder = AutobiographicalNarrative()

    episodes1 = [
        Episode(
            timestamp=datetime.now(timezone.utc),
            focus_target="test1",
            salience=0.5,
            narrative="Test 1",
            confidence=0.8,
            context={}
        )
    ]

    episodes2 = [
        Episode(
            timestamp=datetime.now(timezone.utc),
            focus_target="test2",
            salience=0.6,
            narrative="Test 2",
            confidence=0.9,
            context={}
        )
    ]

    with patch.object(narrative_builder._binder, 'coherence', return_value=0.7):
        with patch.object(narrative_builder._binder, 'focus_stability', return_value=0.6):
            result1 = narrative_builder.build(episodes1)
            result2 = narrative_builder.build(episodes2)

    assert "test1" in result1.narrative
    assert "test2" in result2.narrative
    assert result1.narrative != result2.narrative
