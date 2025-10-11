"""
Episodic Memory Package
Temporal self and autobiographical narrative construction.
"""
# Legacy event-based API (deprecated but maintained for compatibility)
from .event import Event, EventType, Salience
from .memory_buffer import EpisodicBuffer

# New episode-based API (primary)
from .core import Episode, EpisodicMemory, windowed_temporal_accuracy

__all__ = [
    # Primary API
    'Episode',
    'EpisodicMemory',
    'windowed_temporal_accuracy',
    # Legacy API
    'Event',
    'EventType',
    'Salience',
    'EpisodicBuffer',
]
