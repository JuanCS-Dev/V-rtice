"""
Event Model - Targeted Coverage Tests

Objetivo: Cobrir consciousness/episodic_memory/event.py (149 lines, 0% → 75%+)

Testa Event dataclass, importance calculation, serialization, temporal decay

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
from datetime import datetime, timedelta

from consciousness.episodic_memory.event import Event, EventType, Salience


# ===== EVENT TYPE TESTS =====

def test_event_type_enum_values():
    """
    SCENARIO: EventType enum defines 7 event categories
    EXPECTED: PERCEPTION, ACTION, DECISION, EMOTION, THOUGHT, INTERACTION, SYSTEM
    """
    assert EventType.PERCEPTION.value == "perception"
    assert EventType.ACTION.value == "action"
    assert EventType.DECISION.value == "decision"
    assert EventType.EMOTION.value == "emotion"
    assert EventType.THOUGHT.value == "thought"
    assert EventType.INTERACTION.value == "interaction"
    assert EventType.SYSTEM.value == "system"


# ===== SALIENCE ENUM TESTS =====

def test_salience_enum_values():
    """
    SCENARIO: Salience enum defines 5 importance levels
    EXPECTED: CRITICAL=5, HIGH=4, MEDIUM=3, LOW=2, TRIVIAL=1
    """
    assert Salience.CRITICAL.value == 5
    assert Salience.HIGH.value == 4
    assert Salience.MEDIUM.value == 3
    assert Salience.LOW.value == 2
    assert Salience.TRIVIAL.value == 1


# ===== EVENT INITIALIZATION TESTS =====

def test_event_default_initialization():
    """
    SCENARIO: Event created with no arguments
    EXPECTED: All defaults (EventType.SYSTEM, Salience.MEDIUM, etc.)
    """
    event = Event()

    assert event.type == EventType.SYSTEM
    assert event.salience == Salience.MEDIUM
    assert event.emotional_valence == 0.0
    assert event.confidence == 1.0
    assert event.consolidated is False
    assert event.access_count == 0
    assert event.last_accessed is None


def test_event_custom_initialization():
    """
    SCENARIO: Event created with custom values
    EXPECTED: All custom values preserved
    """
    now = datetime.now()
    event = Event(
        id="test-123",
        timestamp=now,
        type=EventType.DECISION,
        content={"data": "test"},
        description="Test decision",
        module="test_module",
        related_events=["event-1", "event-2"],
        tags=["tag1", "tag2"],
        salience=Salience.CRITICAL,
        emotional_valence=0.5,
        confidence=0.9,
    )

    assert event.id == "test-123"
    assert event.timestamp == now
    assert event.type == EventType.DECISION
    assert event.content == {"data": "test"}
    assert event.description == "Test decision"
    assert event.module == "test_module"
    assert event.related_events == ["event-1", "event-2"]
    assert event.tags == ["tag1", "tag2"]
    assert event.salience == Salience.CRITICAL
    assert event.emotional_valence == 0.5
    assert event.confidence == 0.9


# ===== VALIDATION TESTS =====

def test_event_emotional_valence_out_of_range_raises():
    """
    SCENARIO: Event created with emotional_valence > 1.0
    EXPECTED: ValueError raised
    """
    with pytest.raises(ValueError, match="Emotional valence must be between -1 and 1"):
        Event(emotional_valence=1.5)


def test_event_emotional_valence_negative_out_of_range_raises():
    """
    SCENARIO: Event created with emotional_valence < -1.0
    EXPECTED: ValueError raised
    """
    with pytest.raises(ValueError, match="Emotional valence must be between -1 and 1"):
        Event(emotional_valence=-1.5)


def test_event_confidence_out_of_range_raises():
    """
    SCENARIO: Event created with confidence > 1.0
    EXPECTED: ValueError raised
    """
    with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
        Event(confidence=1.5)


def test_event_confidence_negative_out_of_range_raises():
    """
    SCENARIO: Event created with confidence < 0.0
    EXPECTED: ValueError raised
    """
    with pytest.raises(ValueError, match="Confidence must be between 0 and 1"):
        Event(confidence=-0.5)


# ===== MARK_ACCESSED TESTS =====

def test_mark_accessed_increments_count():
    """
    SCENARIO: Event.mark_accessed() called
    EXPECTED: access_count increments, last_accessed updated
    """
    event = Event()
    assert event.access_count == 0
    assert event.last_accessed is None

    event.mark_accessed()

    assert event.access_count == 1
    assert event.last_accessed is not None


def test_mark_accessed_multiple_times():
    """
    SCENARIO: Event.mark_accessed() called 3 times
    EXPECTED: access_count = 3
    """
    event = Event()

    event.mark_accessed()
    event.mark_accessed()
    event.mark_accessed()

    assert event.access_count == 3


# ===== IMPORTANCE CALCULATION TESTS =====

def test_calculate_importance_trivial_event():
    """
    SCENARIO: Event with Salience.TRIVIAL (1/5 = 0.2 base)
    EXPECTED: Low importance score (~0.2 + recency)
    """
    event = Event(salience=Salience.TRIVIAL, emotional_valence=0.0)

    importance = event.calculate_importance()

    assert 0.2 <= importance <= 0.5  # Base + recency


def test_calculate_importance_critical_event():
    """
    SCENARIO: Event with Salience.CRITICAL (5/5 = 1.0 base)
    EXPECTED: High importance score (~1.0)
    """
    event = Event(salience=Salience.CRITICAL, emotional_valence=0.0)

    importance = event.calculate_importance()

    assert importance >= 1.0  # Capped at 1.0


def test_calculate_importance_with_strong_emotion():
    """
    SCENARIO: Event with strong emotional_valence (0.8)
    EXPECTED: Emotion boost (0.8 * 0.2 = 0.16)
    """
    event = Event(salience=Salience.MEDIUM, emotional_valence=0.8)

    importance = event.calculate_importance()

    # Base (3/5=0.6) + emotion (0.16) + recency = ~0.76+
    assert importance > 0.7


def test_calculate_importance_with_frequent_access():
    """
    SCENARIO: Event accessed 10 times
    EXPECTED: Access boost (min(10*0.05, 0.3) = 0.3)
    """
    event = Event(salience=Salience.MEDIUM)

    for _ in range(10):
        event.mark_accessed()

    importance = event.calculate_importance()

    # Base (3/5=0.6) + access (0.3) + recency = ~0.9+
    assert importance > 0.8


def test_calculate_importance_temporal_decay():
    """
    SCENARIO: Old event (30 days ago)
    EXPECTED: Recency factor = 0.0 (full decay)
    """
    old_timestamp = datetime.now() - timedelta(days=30)
    event = Event(salience=Salience.MEDIUM, timestamp=old_timestamp)

    importance = event.calculate_importance()

    # Base (3/5=0.6) + minimal recency = ~0.6
    assert 0.5 <= importance <= 0.7


# ===== SERIALIZATION TESTS =====

def test_to_dict_serialization():
    """
    SCENARIO: Event.to_dict() serializes all fields
    EXPECTED: Dict with 15+ fields including importance
    """
    event = Event(
        id="test-456",
        type=EventType.PERCEPTION,
        content={"data": "test"},
        description="Test event",
        module="test_module",
        tags=["tag1"],
        salience=Salience.HIGH,
        emotional_valence=0.3,
        confidence=0.85,
    )

    data = event.to_dict()

    assert data["id"] == "test-456"
    assert data["type"] == "perception"
    assert data["content"] == {"data": "test"}
    assert data["description"] == "Test event"
    assert data["module"] == "test_module"
    assert data["tags"] == ["tag1"]
    assert data["salience"] == 4  # HIGH = 4
    assert data["emotional_valence"] == 0.3
    assert data["confidence"] == 0.85
    assert "importance" in data
    assert "timestamp" in data


def test_from_dict_deserialization():
    """
    SCENARIO: Event.from_dict() deserializes from dict
    EXPECTED: Event instance with all fields restored
    """
    data = {
        "id": "test-789",
        "timestamp": "2025-10-23T12:00:00",
        "type": "action",
        "content": {"key": "value"},
        "description": "Test action",
        "module": "test_module",
        "related_events": ["event-1"],
        "tags": ["tag1"],
        "salience": 3,
        "emotional_valence": 0.5,
        "confidence": 0.9,
        "consolidated": False,
        "access_count": 2,
        "last_accessed": "2025-10-23T12:30:00",
    }

    event = Event.from_dict(data)

    assert event.id == "test-789"
    assert event.type == EventType.ACTION
    assert event.content == {"key": "value"}
    assert event.description == "Test action"
    assert event.module == "test_module"
    assert event.related_events == ["event-1"]
    assert event.tags == ["tag1"]
    assert event.salience == Salience.MEDIUM
    assert event.emotional_valence == 0.5
    assert event.confidence == 0.9
    assert event.access_count == 2


def test_round_trip_serialization():
    """
    SCENARIO: Event → to_dict() → from_dict() → to_dict()
    EXPECTED: Final dict matches (except importance recalculation)
    """
    original = Event(
        type=EventType.THOUGHT,
        description="Original thought",
        salience=Salience.HIGH,
        emotional_valence=0.7,
    )

    dict1 = original.to_dict()
    restored = Event.from_dict(dict1)
    dict2 = restored.to_dict()

    # Core fields should match
    assert dict1["type"] == dict2["type"]
    assert dict1["description"] == dict2["description"]
    assert dict1["salience"] == dict2["salience"]
    assert dict1["emotional_valence"] == dict2["emotional_valence"]


# ===== REPR TESTS =====

def test_event_repr():
    """
    SCENARIO: Event.__repr__() for debugging
    EXPECTED: Includes id, type, timestamp, importance
    """
    event = Event(type=EventType.EMOTION)

    repr_str = repr(event)

    assert "Event(" in repr_str
    assert "type=emotion" in repr_str
    assert "importance=" in repr_str
    assert "timestamp=" in repr_str


def test_docstring_episodic_memory():
    """
    SCENARIO: Module documents episodic memory functionality
    EXPECTED: Mentions indexing, retrieval, consolidation, narrative
    """
    import consciousness.episodic_memory.event as module

    assert "discrete events" in module.__doc__
    assert "consciousness timeline" in module.__doc__
