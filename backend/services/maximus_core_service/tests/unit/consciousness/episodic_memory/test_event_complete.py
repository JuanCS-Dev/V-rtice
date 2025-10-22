"""
Complete tests for consciousness/episodic_memory/event.py

Target: 71.9% → 95%+ coverage (16 missing lines)
Zero mocks - Padrão Pagani Absoluto
"""

from datetime import datetime, timedelta
import pytest

from consciousness.episodic_memory.event import Event, EventType, Salience


class TestEventValidation:
    """Test Event validation and edge cases."""

    def test_emotional_valence_validation_negative_boundary(self):
        """Test emotional valence at negative boundary."""
        event = Event(emotional_valence=-1.0)
        assert event.emotional_valence == -1.0

    def test_emotional_valence_validation_positive_boundary(self):
        """Test emotional valence at positive boundary."""
        event = Event(emotional_valence=1.0)
        assert event.emotional_valence == 1.0

    def test_emotional_valence_validation_below_range(self):
        """Test emotional valence below valid range raises ValueError."""
        with pytest.raises(ValueError, match="Emotional valence must be between"):
            Event(emotional_valence=-1.1)

    def test_emotional_valence_validation_above_range(self):
        """Test emotional valence above valid range raises ValueError."""
        with pytest.raises(ValueError, match="Emotional valence must be between"):
            Event(emotional_valence=1.1)

    def test_confidence_validation_negative(self):
        """Test confidence below valid range raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            Event(confidence=-0.1)

    def test_confidence_validation_above_one(self):
        """Test confidence above valid range raises ValueError."""
        with pytest.raises(ValueError, match="Confidence must be between"):
            Event(confidence=1.1)

    def test_confidence_validation_zero_boundary(self):
        """Test confidence at zero boundary."""
        event = Event(confidence=0.0)
        assert event.confidence == 0.0

    def test_confidence_validation_one_boundary(self):
        """Test confidence at one boundary."""
        event = Event(confidence=1.0)
        assert event.confidence == 1.0


class TestEventMarkAccessed:
    """Test mark_accessed functionality."""

    def test_mark_accessed_increments_count(self):
        """Test that mark_accessed increments access_count."""
        event = Event()
        assert event.access_count == 0

        event.mark_accessed()
        assert event.access_count == 1

        event.mark_accessed()
        assert event.access_count == 2

    def test_mark_accessed_updates_timestamp(self):
        """Test that mark_accessed updates last_accessed timestamp."""
        event = Event()
        assert event.last_accessed is None

        event.mark_accessed()
        assert event.last_accessed is not None
        assert isinstance(event.last_accessed, datetime)

        first_access = event.last_accessed
        event.mark_accessed()
        assert event.last_accessed >= first_access


class TestEventImportanceCalculation:
    """Test calculate_importance method."""

    def test_calculate_importance_base(self):
        """Test base importance from salience."""
        event = Event(salience=Salience.MEDIUM)
        importance = event.calculate_importance()
        # MEDIUM = 3, base = 3/5 = 0.6
        assert 0.6 <= importance <= 1.0

    def test_calculate_importance_with_emotion(self):
        """Test importance boost from strong emotions."""
        event = Event(
            salience=Salience.LOW,
            emotional_valence=1.0  # Max positive emotion
        )
        importance = event.calculate_importance()
        # Should be higher than base LOW (2/5 = 0.4)
        assert importance > 0.4

    def test_calculate_importance_with_access_count(self):
        """Test importance boost from frequent access."""
        event = Event(salience=Salience.LOW)
        base_importance = event.calculate_importance()

        # Access multiple times
        for _ in range(10):
            event.mark_accessed()

        boosted_importance = event.calculate_importance()
        assert boosted_importance > base_importance

    def test_calculate_importance_temporal_decay(self):
        """Test temporal decay for old events."""
        # Recent event
        recent_event = Event(salience=Salience.HIGH)
        recent_importance = recent_event.calculate_importance()

        # Old event (30+ days ago)
        old_event = Event(
            salience=Salience.HIGH,
            timestamp=datetime.now() - timedelta(days=35)
        )
        old_importance = old_event.calculate_importance()

        # Recent should be slightly higher due to recency factor
        assert recent_importance >= old_importance

    def test_calculate_importance_capped_at_one(self):
        """Test that importance is capped at 1.0."""
        event = Event(
            salience=Salience.CRITICAL,
            emotional_valence=1.0,
            access_count=100  # Very high access count
        )
        importance = event.calculate_importance()
        assert importance <= 1.0

    def test_calculate_importance_never_negative(self):
        """Test that importance is never negative."""
        event = Event(
            salience=Salience.TRIVIAL,
            emotional_valence=-1.0,
            timestamp=datetime.now() - timedelta(days=365)  # Very old
        )
        importance = event.calculate_importance()
        assert importance >= 0.0


class TestEventSerialization:
    """Test to_dict and from_dict methods."""

    def test_to_dict_includes_importance(self):
        """Test that to_dict includes calculated importance."""
        event = Event(salience=Salience.HIGH)
        data = event.to_dict()

        assert "importance" in data
        assert isinstance(data["importance"], float)
        assert 0.0 <= data["importance"] <= 1.0

    def test_to_dict_with_last_accessed(self):
        """Test to_dict serializes last_accessed correctly."""
        event = Event()
        event.mark_accessed()

        data = event.to_dict()
        assert data["last_accessed"] is not None
        assert isinstance(data["last_accessed"], str)  # ISO format

    def test_to_dict_without_last_accessed(self):
        """Test to_dict handles None last_accessed."""
        event = Event()
        data = event.to_dict()

        assert data["last_accessed"] is None

    def test_from_dict_with_last_accessed(self):
        """Test from_dict deserializes last_accessed correctly."""
        now = datetime.now()
        data = {
            "timestamp": now.isoformat(),
            "type": "system",
            "last_accessed": now.isoformat()
        }

        event = Event.from_dict(data)
        assert event.last_accessed is not None
        assert isinstance(event.last_accessed, datetime)

    def test_from_dict_without_last_accessed(self):
        """Test from_dict handles missing last_accessed."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "type": "system"
        }

        event = Event.from_dict(data)
        assert event.last_accessed is None

    def test_roundtrip_serialization_with_accessed_event(self):
        """Test full roundtrip with accessed event."""
        original = Event(
            description="Test event",
            salience=Salience.HIGH,
            emotional_valence=0.5
        )
        original.mark_accessed()

        data = original.to_dict()
        restored = Event.from_dict(data)

        assert restored.description == original.description
        assert restored.salience == original.salience
        assert restored.emotional_valence == original.emotional_valence
        assert restored.access_count == original.access_count
        assert restored.last_accessed is not None


class TestEventRepr:
    """Test string representation."""

    def test_repr_includes_id_prefix(self):
        """Test that __repr__ includes first 8 chars of ID."""
        event = Event()
        repr_str = repr(event)

        assert "id=" in repr_str
        assert event.id[:8] in repr_str

    def test_repr_includes_type(self):
        """Test that __repr__ includes event type."""
        event = Event(type=EventType.ACTION)
        repr_str = repr(event)

        assert "type=action" in repr_str

    def test_repr_includes_importance(self):
        """Test that __repr__ includes calculated importance."""
        event = Event()
        repr_str = repr(event)

        assert "importance=" in repr_str
        # Should match calculate_importance() format with 2 decimals
        importance = event.calculate_importance()
        assert f"{importance:.2f}" in repr_str
