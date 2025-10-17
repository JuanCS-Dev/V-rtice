"""Tests for Pydantic models."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from models import (
    HealthResponse,
    Verdict,
    VerdictFilter,
    VerdictStats,
    VerdictSummary,
    WebSocketMessage,
)


def test_verdict_base_valid():
    """Test VerdictBase validation with valid data."""
    verdict = Verdict(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        category="DECEPTION",
        severity="CRITICAL",
        title="Test verdict",
        agents_involved=["agent-1"],
        evidence_chain=["msg-1"],
        confidence=Decimal("0.95"),
        recommended_action="ISOLATE",
        color="#DC2626",
        created_at=datetime.utcnow(),
    )

    assert verdict.category == "DECEPTION"
    assert verdict.severity == "CRITICAL"
    assert verdict.confidence == Decimal("0.95")


def test_verdict_confidence_conversion():
    """Test confidence conversion from float to Decimal."""
    verdict = Verdict(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        category="ALLIANCE",
        severity="LOW",
        title="Test",
        agents_involved=["a1"],
        evidence_chain=["m1"],
        confidence=0.75,  # Float input
        recommended_action="MONITOR",
        color="#10B981",
        created_at=datetime.utcnow(),
    )

    assert isinstance(verdict.confidence, Decimal)
    assert verdict.confidence == Decimal("0.75")


def test_verdict_invalid_color():
    """Test verdict with invalid color hex."""
    with pytest.raises(ValidationError) as exc_info:
        Verdict(
            id=uuid4(),
            timestamp=datetime.utcnow(),
            category="THREAT",
            severity="HIGH",
            title="Test",
            agents_involved=["a1"],
            evidence_chain=["m1"],
            confidence=Decimal("0.9"),
            recommended_action="REVOKE_ACCESS",
            color="invalid_color",  # Invalid
            created_at=datetime.utcnow(),
        )

    assert "color" in str(exc_info.value)


def test_verdict_filter_defaults():
    """Test VerdictFilter default values."""
    filters = VerdictFilter()

    assert filters.status is None
    assert filters.severity is None
    assert filters.limit == 50
    assert filters.offset == 0


def test_verdict_filter_limits():
    """Test VerdictFilter limit validation."""
    with pytest.raises(ValidationError):
        VerdictFilter(limit=1000)  # Exceeds max 500

    with pytest.raises(ValidationError):
        VerdictFilter(limit=0)  # Below min 1


def test_verdict_stats():
    """Test VerdictStats model."""
    stats = VerdictStats(
        total_count=100,
        by_severity={"CRITICAL": 10},
        by_status={"ACTIVE": 90},
        by_category={"THREAT": 50},
        critical_active=5,
        last_updated=datetime.utcnow(),
    )

    assert stats.total_count == 100
    assert stats.by_severity["CRITICAL"] == 10


def test_verdict_summary():
    """Test VerdictSummary lightweight model."""
    summary = VerdictSummary(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        category="ALLIANCE",
        severity="MEDIUM",
        title="Test alliance",
        status="ACTIVE",
        color="#F59E0B",
        agents_count=3,
    )

    assert summary.agents_count == 3


def test_websocket_message_verdict():
    """Test WebSocketMessage with verdict data."""
    verdict = Verdict(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        category="DECEPTION",
        severity="HIGH",
        title="WS Test",
        agents_involved=["a1"],
        evidence_chain=["m1"],
        confidence=Decimal("0.88"),
        recommended_action="MUTE",
        color="#EA580C",
        created_at=datetime.utcnow(),
    )

    msg = WebSocketMessage(type="verdict", data=verdict)

    assert msg.type == "verdict"
    assert msg.data == verdict


def test_websocket_message_stats():
    """Test WebSocketMessage with stats data."""
    stats = VerdictStats(
        total_count=50,
        by_severity={},
        by_status={},
        by_category={},
        critical_active=2,
        last_updated=datetime.utcnow(),
    )

    msg = WebSocketMessage(type="stats", data=stats)

    assert msg.type == "stats"
    assert msg.data.critical_active == 2


def test_websocket_message_ping():
    """Test WebSocketMessage ping type."""
    msg = WebSocketMessage(type="ping", data={"status": "ok"})

    assert msg.type == "ping"
    assert msg.data["status"] == "ok"


def test_health_response_healthy():
    """Test HealthResponse healthy status."""
    health = HealthResponse(
        status="healthy",
        dependencies={"postgres": True, "redis": True},
    )

    assert health.status == "healthy"
    assert all(health.dependencies.values())


def test_health_response_degraded():
    """Test HealthResponse degraded status."""
    health = HealthResponse(
        status="degraded",
        dependencies={"postgres": True, "redis": False},
    )

    assert health.status == "degraded"
    assert not all(health.dependencies.values())
