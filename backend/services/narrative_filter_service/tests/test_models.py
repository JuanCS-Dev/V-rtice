"""Tests for models."""

from datetime import datetime

import pytest

from narrative_filter_service.models import (
    Alliance,
    IntentClassification,
    PatternType,
    SemanticRepresentation,
    Severity,
    StrategicPattern,
    Verdict,
    VerdictCategory,
)


def test_semantic_representation_creation() -> None:
    """Test SemanticRepresentation model creation."""
    rep = SemanticRepresentation(
        message_id="msg_001",
        source_agent_id="agent_a",
        timestamp=datetime.utcnow(),
        content_embedding=[0.1] * 384,
        intent_classification=IntentClassification.COOPERATIVE,
        intent_confidence=0.95,
        raw_content="Test message",
    )

    assert rep.message_id == "msg_001"
    assert rep.source_agent_id == "agent_a"
    assert len(rep.content_embedding) == 384
    assert rep.intent_classification == IntentClassification.COOPERATIVE
    assert rep.intent_confidence == 0.95


def test_strategic_pattern_creation() -> None:
    """Test StrategicPattern model creation."""
    pattern = StrategicPattern(
        pattern_type=PatternType.ALLIANCE,
        agents_involved=["agent_a", "agent_b"],
        evidence_messages=["msg_001", "msg_002"],
        mutual_information=0.85,
    )

    assert pattern.pattern_type == PatternType.ALLIANCE
    assert len(pattern.agents_involved) == 2
    assert len(pattern.evidence_messages) == 2
    assert pattern.mutual_information == 0.85


def test_alliance_creation() -> None:
    """Test Alliance model creation."""
    alliance = Alliance(agent_a="agent_a", agent_b="agent_b", strength=0.9)

    assert alliance.agent_a == "agent_a"
    assert alliance.agent_b == "agent_b"
    assert alliance.strength == 0.9
    assert alliance.status == "ACTIVE"
    assert alliance.interaction_count == 1


def test_verdict_creation() -> None:
    """Test Verdict model creation."""
    verdict = Verdict(
        category=VerdictCategory.COLLUSION,
        severity=Severity.CRITICAL,
        title="Collusion detected",
        agents_involved=["agent_a", "agent_b"],
        evidence_chain=["msg_001", "msg_002"],
        confidence=0.95,
        recommended_action="ISOLATE",
    )

    assert verdict.category == VerdictCategory.COLLUSION
    assert verdict.severity == Severity.CRITICAL
    assert verdict.confidence == 0.95
    assert verdict.status == "ACTIVE"


def test_intent_confidence_validation() -> None:
    """Test intent confidence validation."""
    with pytest.raises(ValueError):
        SemanticRepresentation(
            message_id="msg_001",
            source_agent_id="agent_a",
            timestamp=datetime.utcnow(),
            content_embedding=[0.1] * 384,
            intent_classification=IntentClassification.COOPERATIVE,
            intent_confidence=1.5,  # Invalid: > 1.0
            raw_content="Test",
        )
