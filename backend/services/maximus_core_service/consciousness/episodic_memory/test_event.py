"""
Tests for Episodic Memory Event Model
"""
import pytest
from datetime import datetime, timedelta
from consciousness.episodic_memory import Event, EventType, Salience


def test_event_creation():
    """Test basic event creation"""
    event = Event(
        type=EventType.PERCEPTION,
        description="Detected anomaly in network traffic",
        module="network_monitor",
        salience=Salience.HIGH
    )
    
    assert event.type == EventType.PERCEPTION
    assert event.description == "Detected anomaly in network traffic"
    assert event.salience == Salience.HIGH
    assert event.id is not None
    assert isinstance(event.timestamp, datetime)


def test_event_importance_calculation():
    """Test importance score calculation"""
    # Low salience event
    event = Event(
        type=EventType.SYSTEM,
        salience=Salience.LOW,
        emotional_valence=0.0
    )
    importance = event.calculate_importance()
    assert 0.0 <= importance <= 1.0
    assert importance < 0.7  # Low salience should have low importance
    
    # High salience event
    event_high = Event(
        type=EventType.DECISION,
        salience=Salience.CRITICAL,
        emotional_valence=0.8  # Strong positive emotion
    )
    importance_high = event_high.calculate_importance()
    assert importance_high > 0.7  # Critical + emotion should be high


def test_event_access_tracking():
    """Test access count tracking"""
    event = Event(type=EventType.THOUGHT)
    
    assert event.access_count == 0
    assert event.last_accessed is None
    
    event.mark_accessed()
    assert event.access_count == 1
    assert event.last_accessed is not None
    
    event.mark_accessed()
    assert event.access_count == 2


def test_event_validation():
    """Test event validation"""
    # Valid event
    event = Event(emotional_valence=0.5, confidence=0.9)
    assert event.emotional_valence == 0.5
    
    # Invalid emotional valence
    with pytest.raises(ValueError):
        Event(emotional_valence=1.5)
    
    with pytest.raises(ValueError):
        Event(emotional_valence=-1.5)
    
    # Invalid confidence
    with pytest.raises(ValueError):
        Event(confidence=1.5)


def test_event_serialization():
    """Test event to/from dict"""
    original = Event(
        type=EventType.ACTION,
        description="Executed security scan",
        module="scanner",
        tags=["security", "scan"],
        salience=Salience.HIGH,
        emotional_valence=0.3
    )
    
    # Serialize
    data = original.to_dict()
    assert data["type"] == "action"
    assert data["description"] == "Executed security scan"
    assert "importance" in data
    
    # Deserialize
    restored = Event.from_dict(data)
    assert restored.type == original.type
    assert restored.description == original.description
    assert restored.module == original.module
    assert restored.tags == original.tags


def test_event_temporal_decay():
    """Test that old events have lower importance due to temporal decay"""
    # Recent event
    recent = Event(salience=Salience.MEDIUM)
    recent_importance = recent.calculate_importance()
    
    # Old event (simulate by setting old timestamp)
    old = Event(salience=Salience.MEDIUM)
    old.timestamp = datetime.now() - timedelta(days=60)
    old_importance = old.calculate_importance()
    
    # Recent should have higher importance due to recency
    assert recent_importance >= old_importance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
