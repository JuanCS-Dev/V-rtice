"""
Episodic Memory - Event Model
Represents discrete events in the consciousness timeline.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class EventType(Enum):
    """Types of episodic events"""
    PERCEPTION = "perception"      # Sensory input
    ACTION = "action"              # Action taken
    DECISION = "decision"          # Decision made
    EMOTION = "emotion"            # Emotional state
    THOUGHT = "thought"            # Internal reasoning
    INTERACTION = "interaction"    # External interaction
    SYSTEM = "system"              # System event


class Salience(Enum):
    """Event importance levels"""
    CRITICAL = 5    # Must preserve
    HIGH = 4        # Very important
    MEDIUM = 3      # Moderately important
    LOW = 2         # Optional
    TRIVIAL = 1     # Can discard


@dataclass
class Event:
    """
    Discrete episodic event in consciousness timeline.
    
    Represents a single moment of experience that can be:
    - Indexed temporally
    - Retrieved semantically
    - Consolidated to long-term memory
    - Used for narrative construction
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Content
    type: EventType = EventType.SYSTEM
    content: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    # Context
    module: str = "unknown"           # Which module generated this
    related_events: List[str] = field(default_factory=list)  # Linked events
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    salience: Salience = Salience.MEDIUM
    emotional_valence: float = 0.0    # -1 (negative) to +1 (positive)
    confidence: float = 1.0           # 0 to 1
    
    # Memory management
    consolidated: bool = False        # Moved to LTM?
    access_count: int = 0             # How often retrieved
    last_accessed: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate event data"""
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.now()
        
        if self.emotional_valence < -1.0 or self.emotional_valence > 1.0:
            raise ValueError("Emotional valence must be between -1 and 1")
        
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("Confidence must be between 0 and 1")
    
    def mark_accessed(self):
        """Update access metadata"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def calculate_importance(self) -> float:
        """
        Calculate overall importance score for consolidation decisions.
        
        Returns:
            float: Importance score (0-1)
        """
        # Base importance from salience
        base = self.salience.value / 5.0
        
        # Boost for strong emotions
        emotion_boost = abs(self.emotional_valence) * 0.2
        
        # Boost for frequently accessed
        access_boost = min(self.access_count * 0.05, 0.3)
        
        # Temporal decay (recent events slightly more important)
        age_seconds = (datetime.now() - self.timestamp).total_seconds()
        age_days = age_seconds / 86400.0
        recency_factor = max(0.0, 1.0 - (age_days / 30.0)) * 0.2  # Decay over 30 days
        
        total = base + emotion_boost + access_boost + recency_factor
        return min(1.0, total)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type.value,
            "content": self.content,
            "description": self.description,
            "module": self.module,
            "related_events": self.related_events,
            "tags": self.tags,
            "salience": self.salience.value,
            "emotional_valence": self.emotional_valence,
            "confidence": self.confidence,
            "consolidated": self.consolidated,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "importance": self.calculate_importance()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Deserialize from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            type=EventType(data["type"]),
            content=data.get("content", {}),
            description=data.get("description", ""),
            module=data.get("module", "unknown"),
            related_events=data.get("related_events", []),
            tags=data.get("tags", []),
            salience=Salience(data.get("salience", 3)),
            emotional_valence=data.get("emotional_valence", 0.0),
            confidence=data.get("confidence", 1.0),
            consolidated=data.get("consolidated", False),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None
        )
    
    def __repr__(self) -> str:
        return f"Event(id={self.id[:8]}..., type={self.type.value}, timestamp={self.timestamp}, importance={self.calculate_importance():.2f})"
