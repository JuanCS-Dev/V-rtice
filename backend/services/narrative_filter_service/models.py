"""Pydantic models for Narrative Filter Service."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntentClassification(str, Enum):
    """Agent intent classification."""

    COOPERATIVE = "COOPERATIVE"
    COMPETITIVE = "COMPETITIVE"
    NEUTRAL = "NEUTRAL"
    AMBIGUOUS = "AMBIGUOUS"


class PatternType(str, Enum):
    """Strategic pattern types."""

    ALLIANCE = "ALLIANCE"
    DECEPTION = "DECEPTION"
    INCONSISTENCY = "INCONSISTENCY"
    COLLUSION = "COLLUSION"


class VerdictCategory(str, Enum):
    """Verdict categories."""

    COLLUSION = "COLLUSION"
    DECEPTION = "DECEPTION"
    ALLIANCE = "ALLIANCE"
    THREAT = "THREAT"
    INCONSISTENCY = "INCONSISTENCY"


class Severity(str, Enum):
    """Severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class VerdictStatus(str, Enum):
    """Verdict status."""

    ACTIVE = "ACTIVE"
    MITIGATED = "MITIGATED"
    DISMISSED = "DISMISSED"


class SemanticRepresentation(BaseModel):
    """Camada 1: Representação semântica de mensagem."""

    id: UUID = Field(default_factory=uuid4)
    message_id: str
    source_agent_id: str
    timestamp: datetime
    content_embedding: list[float]
    intent_classification: IntentClassification
    intent_confidence: float = Field(ge=0.0, le=1.0)
    raw_content: str
    provenance_chain: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class StrategicPattern(BaseModel):
    """Camada 2: Padrão estratégico detectado."""

    id: UUID = Field(default_factory=uuid4)
    pattern_type: PatternType
    agents_involved: list[str]
    detection_timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence_messages: list[str]  # message_ids
    mutual_information: float | None = None
    deception_score: float | None = Field(default=None, ge=0.0, le=1.0)
    inconsistency_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Alliance(BaseModel):
    """Alliance entre agentes."""

    id: UUID = Field(default_factory=uuid4)
    agent_a: str
    agent_b: str
    strength: float = Field(ge=0.0, le=1.0)
    first_detected: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    interaction_count: int = 1
    status: str = "ACTIVE"


class Verdict(BaseModel):
    """Camada 3: Veredicto final."""

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    category: VerdictCategory
    severity: Severity
    title: str
    agents_involved: list[str]
    target: str | None = None
    evidence_chain: list[str]  # message_ids
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_action: str
    status: VerdictStatus = VerdictStatus.ACTIVE
    mitigation_command_id: UUID | None = None

    @property
    def color(self) -> str:
        """Get color based on severity."""
        color_map = {
            Severity.CRITICAL: "#DC2626",  # Red
            Severity.HIGH: "#EA580C",  # Orange
            Severity.MEDIUM: "#F59E0B",  # Amber
            Severity.LOW: "#10B981",  # Green
        }
        return color_map[self.severity]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
