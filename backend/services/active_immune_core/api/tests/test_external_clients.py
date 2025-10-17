"""
Tests for external service clients.

Tests graceful degradation and real service integration.

NO MOCKS - Tests use REAL services or graceful degradation.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
import pytest_asyncio

from active_immune_core.api.clients import (
    AdaptiveImmunityClient,
    GovernanceClient,
    IPIntelClient,
    MemoryClient,
    TregClient,
)
from active_immune_core.api.clients.governance_client import RiskLevel

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def treg_client():
    """Treg client fixture."""
    client = TregClient(enable_degraded_mode=True)
    await client.initialize()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def memory_client():
    """Memory client fixture."""
    client = MemoryClient(enable_degraded_mode=True)
    await client.initialize()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def adaptive_client():
    """Adaptive Immunity client fixture."""
    client = AdaptiveImmunityClient(enable_degraded_mode=True)
    await client.initialize()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def governance_client():
    """Governance client fixture."""
    client = GovernanceClient(enable_degraded_mode=True)
    await client.initialize()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def ip_intel_client():
    """IP Intelligence client fixture."""
    client = IPIntelClient(enable_degraded_mode=True)
    await client.initialize()
    yield client
    await client.close()


# ==================== TREG CLIENT TESTS ====================


@pytest.mark.asyncio
async def test_treg_client_initialization(treg_client):
    """Test Treg client initializes."""
    assert treg_client is not None
    assert treg_client.base_url == "http://localhost:8018"


@pytest.mark.asyncio
async def test_treg_request_suppression(treg_client):
    """Test suppression request (real service or degraded)."""
    result = await treg_client.request_suppression(
        agent_id="test_agent_001", threat_level=0.5, current_load=0.8, reason="test_suppression"
    )

    assert result is not None
    assert "status" in result or "suppression_active" in result


@pytest.mark.asyncio
async def test_treg_check_tolerance(treg_client):
    """Test tolerance check."""
    result = await treg_client.check_tolerance("test_threat_signature")

    assert result is not None


@pytest.mark.asyncio
async def test_treg_get_service_metrics(treg_client):
    """Test service metrics retrieval (HTTP request to service)."""
    result = await treg_client.get_metrics()

    assert result is not None


# ==================== MEMORY CLIENT TESTS ====================


@pytest.mark.asyncio
async def test_memory_client_initialization(memory_client):
    """Test Memory client initializes."""
    assert memory_client is not None
    assert memory_client.base_url == "http://localhost:8019"


@pytest.mark.asyncio
async def test_memory_consolidate(memory_client):
    """Test memory consolidation."""
    result = await memory_client.consolidate_memory(
        threat_signature="test_threat_abc123",
        threat_type="malware",
        response_success=True,
        antibody_profile={"signature": "test"},
    )

    assert result is not None
    assert "memory_id" in result or "status" in result


@pytest.mark.asyncio
async def test_memory_recall(memory_client):
    """Test memory recall."""
    result = await memory_client.recall_memory(threat_signature="test_threat_abc123", similarity_threshold=0.8)

    assert result is not None


@pytest.mark.asyncio
async def test_memory_search(memory_client):
    """Test memory search."""
    result = await memory_client.search_memories(query="test", limit=10)

    assert result is not None


# ==================== ADAPTIVE IMMUNITY CLIENT TESTS ====================


@pytest.mark.asyncio
async def test_adaptive_client_initialization(adaptive_client):
    """Test Adaptive client initializes."""
    assert adaptive_client is not None
    assert adaptive_client.base_url == "http://localhost:8020"


@pytest.mark.asyncio
async def test_adaptive_analyze_threat(adaptive_client):
    """Test threat analysis."""
    result = await adaptive_client.analyze_threat(threat_data={"payload": "test_payload"}, threat_type="network_attack")

    assert result is not None
    assert "status" in result or "threat_type" in result


@pytest.mark.asyncio
async def test_adaptive_optimize_response(adaptive_client):
    """Test response optimization."""
    result = await adaptive_client.optimize_response(
        threat_signature="test_signature", current_antibody={"config": "v1"}, success_rate=0.75
    )

    assert result is not None


@pytest.mark.asyncio
async def test_adaptive_get_antibodies(adaptive_client):
    """Test antibody retrieval."""
    result = await adaptive_client.get_antibodies(min_affinity=0.5, limit=10)

    assert result is not None


# ==================== GOVERNANCE CLIENT TESTS ====================


@pytest.mark.asyncio
async def test_governance_client_initialization(governance_client):
    """Test Governance client initializes."""
    assert governance_client is not None
    assert governance_client.base_url == "http://localhost:8002"


@pytest.mark.asyncio
async def test_governance_submit_low_risk_decision(governance_client):
    """Test submitting low-risk decision."""
    result = await governance_client.submit_decision(
        decision_type="test_decision",
        description="Test low-risk decision",
        risk_level=RiskLevel.LOW,
        context={"test": "data"},
        recommended_action="approve",
    )

    assert result is not None

    # In degraded mode, low-risk should be auto-approved
    if result.get("degraded_mode"):
        assert result["decision"] == "approved"


@pytest.mark.asyncio
async def test_governance_submit_high_risk_decision(governance_client):
    """Test submitting high-risk decision."""
    result = await governance_client.submit_decision(
        decision_type="critical_action",
        description="Test high-risk decision",
        risk_level=RiskLevel.HIGH,
        context={"impact": "critical"},
        recommended_action="execute",
    )

    assert result is not None

    # In degraded mode, high-risk should be auto-rejected (safety first)
    if result.get("degraded_mode"):
        assert result["decision"] == "rejected"


@pytest.mark.asyncio
async def test_governance_get_pending_stats(governance_client):
    """Test getting pending stats."""
    result = await governance_client.get_pending_stats()

    assert result is not None


# ==================== GRACEFUL DEGRADATION TESTS ====================


@pytest.mark.asyncio
async def test_graceful_degradation_on_unavailable_service():
    """Test graceful degradation when service is unavailable."""
    # Create client pointing to non-existent service
    client = TregClient(
        base_url="http://localhost:9999",  # Non-existent port
        enable_degraded_mode=True,
        max_retries=1,  # Fast failure
    )

    await client.initialize()

    # Should not be available
    assert not client.is_available()

    # But should still work (degraded mode)
    result = await client.request_suppression(agent_id="test", threat_level=0.5, current_load=0.8)

    assert result is not None
    assert result.get("degraded_mode") is True

    await client.close()


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures."""
    client = TregClient(
        base_url="http://localhost:9999",
        enable_degraded_mode=True,
        circuit_breaker_threshold=3,
        max_retries=0,  # Fail immediately
    )

    await client.initialize()

    # Make requests until circuit opens
    for i in range(5):
        await client.request_suppression(agent_id="test", threat_level=0.5, current_load=0.8)

    # Circuit should be open
    # Call base class method to get local metrics (not async)
    metrics = super(type(client), client).get_metrics()
    assert metrics["circuit_open"] is True

    await client.close()


# ==================== CLIENT METRICS TESTS ====================


@pytest.mark.asyncio
async def test_client_local_metrics(treg_client):
    """Test client local metrics (from base_client)."""
    # Call base class method directly to get local client metrics
    metrics = super(type(treg_client), treg_client).get_metrics()

    assert metrics is not None
    assert "service" in metrics
    assert "base_url" in metrics
    assert "available" in metrics
    assert "circuit_open" in metrics
    assert "failures" in metrics


@pytest.mark.asyncio
async def test_client_repr(treg_client):
    """Test client string representation."""
    repr_str = repr(treg_client)

    assert "TregClient" in repr_str
    assert "base_url" in repr_str
    assert "available" in repr_str


# ==================== IP INTELLIGENCE CLIENT TESTS ====================


@pytest.mark.asyncio
async def test_ip_intel_client_initialization(ip_intel_client):
    """Test IP Intel client initializes."""
    assert ip_intel_client is not None
    assert ip_intel_client.base_url == "http://localhost:8022"


@pytest.mark.asyncio
async def test_ip_intel_lookup(ip_intel_client):
    """Test IP lookup."""
    result = await ip_intel_client.lookup_ip("8.8.8.8")

    assert result is not None
    assert "ip_address" in result or "status" in result


@pytest.mark.asyncio
async def test_ip_intel_check_reputation(ip_intel_client):
    """Test reputation check."""
    result = await ip_intel_client.check_reputation("1.1.1.1")

    assert result is not None


@pytest.mark.asyncio
async def test_ip_intel_batch_lookup(ip_intel_client):
    """Test batch lookup."""
    result = await ip_intel_client.batch_lookup(["8.8.8.8", "1.1.1.1"])

    assert result is not None
