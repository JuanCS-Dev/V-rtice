"""Pytest configuration and fixtures for verdict engine tests."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from cache import VerdictCache
from config import Settings
from models import Verdict, VerdictStats
from verdict_repository import VerdictRepository
from websocket_manager import ConnectionManager


@pytest.fixture
def test_settings():
    """Test settings override."""
    return Settings(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
        postgres_user="test_user",
        postgres_password="test_pass",
        redis_url="redis://localhost:6379/15",  # Use different DB for tests
        kafka_bootstrap_servers="localhost:9092",
        log_level="DEBUG",
    )


@pytest.fixture
def sample_verdict():
    """Sample verdict for testing."""
    return Verdict(
        id=uuid4(),
        timestamp=datetime.utcnow(),
        category="DECEPTION",
        severity="CRITICAL",
        title="Critical deception detected in Agent Alpha",
        agents_involved=["agent-alpha", "agent-beta"],
        target="agent-gamma",
        evidence_chain=["msg-001", "msg-002", "msg-003"],
        confidence=Decimal("0.95"),
        recommended_action="ISOLATE",
        status="ACTIVE",
        mitigation_command_id=None,
        color="#DC2626",
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_verdict_data():
    """Sample verdict as dict (for Kafka simulation)."""
    return {
        "id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "category": "ALLIANCE",
        "severity": "MEDIUM",
        "title": "Alliance detected between agents",
        "agents_involved": ["agent-1", "agent-2"],
        "target": None,
        "evidence_chain": ["msg-100", "msg-101"],
        "confidence": 0.82,
        "recommended_action": "MONITOR",
        "status": "ACTIVE",
        "mitigation_command_id": None,
        "color": "#F59E0B",
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_stats():
    """Sample verdict statistics."""
    return VerdictStats(
        total_count=100,
        by_severity={"CRITICAL": 5, "HIGH": 15, "MEDIUM": 40, "LOW": 40},
        by_status={"ACTIVE": 70, "MITIGATED": 20, "DISMISSED": 10},
        by_category={
            "ALLIANCE": 30,
            "DECEPTION": 25,
            "THREAT": 20,
            "INCONSISTENCY": 15,
            "COLLUSION": 10,
        },
        critical_active=5,
        last_updated=datetime.utcnow(),
    )


@pytest_asyncio.fixture
async def mock_repository(mocker):
    """Mock verdict repository."""
    repo = mocker.AsyncMock(spec=VerdictRepository)
    repo.pool = mocker.MagicMock()  # Simulate connected pool
    return repo


@pytest_asyncio.fixture
async def mock_cache(mocker):
    """Mock verdict cache."""
    cache = mocker.AsyncMock(spec=VerdictCache)
    cache.client = mocker.MagicMock()  # Simulate connected client
    return cache


@pytest.fixture
def ws_manager():
    """Real WebSocket manager for testing."""
    return ConnectionManager()
