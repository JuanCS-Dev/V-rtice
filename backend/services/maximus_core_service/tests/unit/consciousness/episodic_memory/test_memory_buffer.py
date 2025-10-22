"""
Tests for Episodic Memory Buffer
"""
import pytest
from datetime import datetime, timedelta
from consciousness.episodic_memory import Event, EventType, Salience, EpisodicBuffer


def test_buffer_initialization():
    """Test buffer creation"""
    buffer = EpisodicBuffer(stm_capacity=100, consolidation_threshold=0.7)
    
    assert buffer.stm_capacity == 100
    assert buffer.consolidation_threshold == 0.7
    assert len(buffer.stm) == 0
    assert len(buffer.ltm) == 0


def test_add_event_to_stm():
    """Test adding events to short-term memory"""
    buffer = EpisodicBuffer(stm_capacity=10)
    
    event = Event(type=EventType.PERCEPTION, description="Test event")
    success = buffer.add_event(event)
    
    assert success
    assert len(buffer.stm) == 1
    assert buffer.stats["total_events"] == 1


def test_stm_overflow():
    """Test STM capacity limits"""
    buffer = EpisodicBuffer(stm_capacity=5)
    
    # Add 10 events (capacity is 5)
    for i in range(10):
        event = Event(description=f"Event {i}")
        buffer.add_event(event)
    
    # Should only have last 5
    assert len(buffer.stm) == 5
    assert buffer.stats["discarded"] == 5


def test_consolidation():
    """Test STM to LTM consolidation"""
    buffer = EpisodicBuffer(
        stm_capacity=100,
        consolidation_threshold=0.6
    )
    
    # Add high-importance event
    high_importance = Event(
        type=EventType.DECISION,
        salience=Salience.CRITICAL,
        emotional_valence=0.9,
        description="Critical decision"
    )
    buffer.add_event(high_importance)
    
    # Add low-importance event
    low_importance = Event(
        type=EventType.SYSTEM,
        salience=Salience.TRIVIAL,
        description="Minor system event"
    )
    buffer.add_event(low_importance)
    
    # Force consolidation
    consolidated = buffer.consolidate(force=True)
    
    # High importance should be consolidated
    assert consolidated >= 1
    assert len(buffer.ltm) >= 1
    
    # Check that high importance event is in LTM
    ltm_events = buffer.get_ltm_events()
    assert any(e.description == "Critical decision" for e in ltm_events)


def test_query_events():
    """Test event querying with filters"""
    buffer = EpisodicBuffer()
    
    # Add various events
    buffer.add_event(Event(type=EventType.PERCEPTION, tags=["security"]))
    buffer.add_event(Event(type=EventType.ACTION, tags=["network"]))
    buffer.add_event(Event(type=EventType.DECISION, tags=["security", "critical"]))
    
    # Query by type
    perceptions = buffer.query_events(event_type=EventType.PERCEPTION)
    assert len(perceptions) == 1
    
    # Query by tags
    security_events = buffer.query_events(tags=["security"])
    assert len(security_events) == 2
    
    # Query by importance
    important = buffer.query_events(min_importance=0.5)
    assert all(e.calculate_importance() >= 0.5 for e in important)


def test_query_by_time_range():
    """Test temporal queries"""
    buffer = EpisodicBuffer()
    
    now = datetime.now()
    
    # Add events with different timestamps
    old_event = Event(description="Old event")
    old_event.timestamp = now - timedelta(hours=2)
    buffer.add_event(old_event)
    
    recent_event = Event(description="Recent event")
    recent_event.timestamp = now - timedelta(minutes=5)
    buffer.add_event(recent_event)
    
    # Query last hour
    last_hour = buffer.query_events(
        start_time=now - timedelta(hours=1)
    )
    
    assert len(last_hour) == 1
    assert last_hour[0].description == "Recent event"


def test_get_recent_events():
    """Test retrieving recent events"""
    buffer = EpisodicBuffer()
    
    # Add 20 events
    for i in range(20):
        buffer.add_event(Event(description=f"Event {i}"))
    
    # Get last 5
    recent = buffer.get_recent_events(limit=5)
    
    assert len(recent) == 5
    # Should be in chronological order (most recent last)
    assert "Event 19" in recent[-1].description


def test_buffer_stats():
    """Test statistics tracking"""
    buffer = EpisodicBuffer(stm_capacity=10)
    
    # Add events
    for i in range(15):  # More than capacity
        buffer.add_event(Event())
    
    # Force consolidation
    buffer.consolidate(force=True)
    
    stats = buffer.get_stats()
    
    assert stats["total_events"] == 15
    assert stats["stm_events"] == 10  # Capacity limit
    assert stats["discarded"] == 5    # Overflow
    assert "consolidations" in stats


def test_clear_memories():
    """Test clearing STM and LTM"""
    buffer = EpisodicBuffer()
    
    # Add events
    for i in range(10):
        event = Event(salience=Salience.CRITICAL)
        buffer.add_event(event)
    
    # Consolidate
    buffer.consolidate(force=True)
    
    assert len(buffer.stm) > 0
    assert len(buffer.ltm) > 0
    
    # Clear STM
    buffer.clear_stm()
    assert len(buffer.stm) == 0
    
    # Clear LTM
    buffer.clear_ltm()
    assert len(buffer.ltm) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
