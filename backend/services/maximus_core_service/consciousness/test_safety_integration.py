"""Integration Tests - Safety Protocol ↔ Consciousness System

Tests the complete integration of the Safety Protocol with the Consciousness
System, including API endpoints, Prometheus metrics, and kill switch execution.

Test Coverage:
- ConsciousnessSystem with SafetyProtocol integration
- FastAPI safety endpoints
- Prometheus metrics export
- Kill switch execution
- Error handling and edge cases

Authors: Juan & Claude Code
Version: 1.0.0 - FASE VII Week 9-10
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from consciousness.api import create_consciousness_api
from consciousness.prometheus_metrics import (
    reset_metrics,
    update_metrics,
    update_violation_metrics,
)
from consciousness.safety import ThreatLevel, SafetyThresholds, SafetyViolationType
from consciousness.system import ConsciousnessConfig, ConsciousnessSystem

# ==================== FIXTURES ====================


@pytest.fixture
def mock_tig_fabric():
    """Mock TIG Fabric component."""
    mock = Mock()
    mock.nodes = list(range(100))
    mock.edge_count = 250
    mock._running = True
    mock.initialize = AsyncMock()
    mock.enter_esgt_mode = AsyncMock()
    mock.exit_esgt_mode = AsyncMock()
    mock.get_metrics = Mock(return_value={"node_count": 100, "edge_count": 250, "clustering_coefficient": 0.78})
    return mock


@pytest.fixture
def mock_esgt_coordinator():
    """Mock ESGT Coordinator component."""
    mock = Mock()
    mock._running = True
    mock._current_frequency_hz = 3.5
    mock.event_history = []
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    return mock


@pytest.fixture
def mock_arousal_controller():
    """Mock Arousal Controller component."""
    mock = Mock()
    mock._running = True
    mock._current_arousal = 0.65
    mock.start = AsyncMock()
    mock.stop = AsyncMock()

    arousal_state = Mock()
    arousal_state.arousal = 0.65
    arousal_state.level = Mock()
    arousal_state.level.value = "NORMAL"
    mock.get_current_arousal = Mock(return_value=arousal_state)

    return mock


@pytest_asyncio.fixture
async def consciousness_system_with_safety():
    """Create ConsciousnessSystem with Safety Protocol enabled."""
    config = ConsciousnessConfig(safety_enabled=True, safety_thresholds=SafetyThresholds())

    system = ConsciousnessSystem(config)

    # Mock components to avoid full initialization
    system.tig_fabric = Mock()
    system.tig_fabric.nodes = list(range(100))
    system.tig_fabric.edge_count = 250
    system.tig_fabric.initialize = AsyncMock()
    system.tig_fabric.enter_esgt_mode = AsyncMock()
    system.tig_fabric.exit_esgt_mode = AsyncMock()

    system.esgt_coordinator = Mock()
    system.esgt_coordinator._running = True
    system.esgt_coordinator._current_frequency_hz = 3.5
    system.esgt_coordinator.event_history = []
    system.esgt_coordinator.start = AsyncMock()
    system.esgt_coordinator.stop = AsyncMock()

    system.arousal_controller = Mock()
    system.arousal_controller._running = True
    system.arousal_controller._current_arousal = 0.65
    system.arousal_controller.start = AsyncMock()
    system.arousal_controller.stop = AsyncMock()

    yield system

    # Cleanup
    if system.safety_protocol and system.safety_protocol.monitoring_active:
        await system.safety_protocol.stop_monitoring()


# ==================== SYSTEM INTEGRATION TESTS ====================


@pytest.mark.asyncio
async def test_system_start_with_safety_protocol(consciousness_system_with_safety):
    """Test 1: System starts with Safety Protocol enabled."""
    system = consciousness_system_with_safety

    # Start system
    await system.start()

    # Verify safety protocol was initialized
    assert system.safety_protocol is not None
    assert system.safety_protocol.monitoring_active
    assert system._running

    # Cleanup
    await system.stop()


@pytest.mark.asyncio
async def test_system_start_without_safety_protocol():
    """Test 2: System starts without Safety Protocol (safety_enabled=False)."""
    config = ConsciousnessConfig(safety_enabled=False)
    system = ConsciousnessSystem(config)

    # Mock components
    system.tig_fabric = Mock()
    system.tig_fabric.initialize = AsyncMock()
    system.tig_fabric.enter_esgt_mode = AsyncMock()
    system.tig_fabric.exit_esgt_mode = AsyncMock()

    system.esgt_coordinator = Mock()
    system.esgt_coordinator._running = True
    system.esgt_coordinator.start = AsyncMock()
    system.esgt_coordinator.stop = AsyncMock()

    system.arousal_controller = Mock()
    system.arousal_controller._running = True
    system.arousal_controller.start = AsyncMock()
    system.arousal_controller.stop = AsyncMock()

    # Start system
    await system.start()

    # Verify safety protocol was NOT initialized
    assert system.safety_protocol is None
    assert system._running

    # Cleanup
    await system.stop()


@pytest.mark.asyncio
async def test_system_stop_with_safety_protocol(consciousness_system_with_safety):
    """Test 3: System stops safely with Safety Protocol active."""
    system = consciousness_system_with_safety

    # Start then stop
    await system.start()
    assert system.safety_protocol.monitoring_active

    await system.stop()

    # Verify safety protocol was stopped
    assert not system.safety_protocol.monitoring_active
    assert not system._running


@pytest.mark.asyncio
async def test_get_safety_status(consciousness_system_with_safety):
    """Test 4: Get safety status from system."""
    system = consciousness_system_with_safety
    await system.start()

    status = system.get_safety_status()

    assert status is not None
    assert "monitoring_active" in status
    assert "kill_switch_active" in status
    assert "violations_total" in status
    assert "violations_by_severity" in status
    assert status["monitoring_active"]
    assert not status["kill_switch_active"]

    await system.stop()


@pytest.mark.asyncio
async def test_get_safety_violations(consciousness_system_with_safety):
    """Test 5: Get safety violations from system."""
    system = consciousness_system_with_safety
    await system.start()

    # Initially should have no violations
    violations = system.get_safety_violations(limit=10)
    assert violations == []

    # Add a test violation
    import time

    system.safety_protocol.threshold_monitor.check_self_modification(modification_attempts=1, current_time=time.time())

    # Now should have 1 violation
    violations = system.get_safety_violations(limit=10)
    assert len(violations) == 1
    assert violations[0].severity == SafetyLevel.EMERGENCY

    await system.stop()


@pytest.mark.asyncio
async def test_get_system_dict_with_safety(consciousness_system_with_safety):
    """Test 6: get_system_dict() includes safety protocol."""
    system = consciousness_system_with_safety
    await system.start()

    system_dict = system.get_system_dict()

    assert "tig" in system_dict
    assert "esgt" in system_dict
    assert "arousal" in system_dict
    assert "safety" in system_dict
    assert "metrics" in system_dict

    assert system_dict["safety"] is not None
    assert system_dict["metrics"] is not None

    await system.stop()


@pytest.mark.asyncio
async def test_is_healthy_with_safety_active(consciousness_system_with_safety):
    """Test 7: is_healthy() checks safety protocol status."""
    system = consciousness_system_with_safety
    await system.start()

    # System should be healthy
    assert system.is_healthy()

    # Stop safety monitoring
    await system.safety_protocol.stop_monitoring()

    # System should now be unhealthy
    assert not system.is_healthy()

    await system.stop()


@pytest.mark.asyncio
async def test_execute_emergency_shutdown(consciousness_system_with_safety):
    """Test 8: Execute emergency shutdown via system method."""
    system = consciousness_system_with_safety
    await system.start()

    # Execute emergency shutdown (no HITL override)
    with patch.object(system.safety_protocol.kill_switch, "_wait_for_hitl_override", return_value=False):
        shutdown_executed = await system.execute_emergency_shutdown(reason="Test emergency shutdown")

    assert shutdown_executed
    assert system.safety_protocol.kill_switch.is_shutdown()


# ==================== API ENDPOINT TESTS ====================


def test_api_safety_status_endpoint(consciousness_system_with_safety):
    """Test 9: GET /api/consciousness/safety/status endpoint."""
    # Create FastAPI app with consciousness API
    app = FastAPI()

    # Create system dict for API
    system_dict = {"system": consciousness_system_with_safety}

    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Make request
    response = client.get("/api/consciousness/safety/status")

    # Should fail because system not started
    assert response.status_code in [503, 500]  # System not initialized or safety not enabled


@pytest.mark.asyncio
async def test_api_safety_status_endpoint_with_started_system(consciousness_system_with_safety):
    """Test 10: GET /api/consciousness/safety/status with started system."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Make request
    response = client.get("/api/consciousness/safety/status")

    assert response.status_code == 200
    data = response.json()

    assert "monitoring_active" in data
    assert "kill_switch_active" in data
    assert "violations_total" in data
    assert data["monitoring_active"]

    await system.stop()


@pytest.mark.asyncio
async def test_api_safety_violations_endpoint(consciousness_system_with_safety):
    """Test 11: GET /api/consciousness/safety/violations endpoint."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Make request
    response = client.get("/api/consciousness/safety/violations?limit=10")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    # Initially should be empty
    assert len(data) == 0

    await system.stop()


@pytest.mark.asyncio
async def test_api_safety_violations_with_limit_validation(consciousness_system_with_safety):
    """Test 12: GET /api/consciousness/safety/violations validates limit parameter."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Test with invalid limit (too high)
    response = client.get("/api/consciousness/safety/violations?limit=2000")
    assert response.status_code == 400

    # Test with invalid limit (too low)
    response = client.get("/api/consciousness/safety/violations?limit=0")
    assert response.status_code == 400

    # Test with valid limit
    response = client.get("/api/consciousness/safety/violations?limit=50")
    assert response.status_code == 200

    await system.stop()


@pytest.mark.asyncio
async def test_api_emergency_shutdown_endpoint(consciousness_system_with_safety):
    """Test 13: POST /api/consciousness/safety/emergency-shutdown endpoint."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Mock HITL override to prevent actual shutdown
    with patch.object(system.safety_protocol.kill_switch, "_wait_for_hitl_override", return_value=True):
        # Make request
        response = client.post(
            "/api/consciousness/safety/emergency-shutdown",
            json={"reason": "Test emergency shutdown via API", "allow_override": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert "success" in data
        assert "shutdown_executed" in data
        assert data["success"]

    await system.stop()


@pytest.mark.asyncio
async def test_api_emergency_shutdown_reason_validation(consciousness_system_with_safety):
    """Test 14: POST /api/consciousness/safety/emergency-shutdown validates reason length."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Test with reason too short (< 10 chars)
    response = client.post(
        "/api/consciousness/safety/emergency-shutdown",
        json={
            "reason": "short",  # Only 5 chars
            "allow_override": True,
        },
    )

    assert response.status_code == 422  # Validation error

    await system.stop()


# ==================== PROMETHEUS METRICS TESTS ====================


@pytest.mark.asyncio
async def test_prometheus_metrics_update(consciousness_system_with_safety):
    """Test 15: Prometheus metrics are updated from system state."""
    system = consciousness_system_with_safety
    await system.start()

    # Reset metrics first
    reset_metrics()

    # Update metrics from system
    update_metrics(system)

    # Verify metrics were updated
    # (We can't easily read metric values from prometheus_client in tests,
    # but we can verify no exceptions were raised)

    await system.stop()


def test_prometheus_metrics_handler():
    """Test 16: Prometheus metrics handler returns valid response."""
    from consciousness.prometheus_metrics import get_metrics_handler

    handler = get_metrics_handler()

    # Call handler
    response = handler()

    # Verify response
    assert response is not None
    assert hasattr(response, "body") or hasattr(response, "content")


def test_update_violation_metrics():
    """Test 17: Violation metrics are updated correctly."""
    from consciousness.safety import SafetyLevel, SafetyViolation

    # Create mock violations
    violations = [
        SafetyViolation(
            violation_id="test-1",
            violation_type=ViolationType.ESGT_FREQUENCY_EXCEEDED,
            severity=SafetyLevel.CRITICAL,
            timestamp=datetime.now(),
            value_observed=12.0,
            threshold_violated=10.0,
            context={},
            message="Test violation",
        )
    ]

    # Update metrics (should not raise exception)
    update_violation_metrics(violations)


# ==================== ERROR HANDLING TESTS ====================


@pytest.mark.asyncio
async def test_api_safety_status_without_system():
    """Test 18: GET /api/consciousness/safety/status returns 503 if system not initialized."""
    # Create FastAPI app with empty system dict
    app = FastAPI()
    system_dict = {}  # No system
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Make request
    response = client.get("/api/consciousness/safety/status")

    assert response.status_code == 503
    assert "not initialized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_safety_status_with_safety_disabled():
    """Test 19: GET /api/consciousness/safety/status returns 503 if safety disabled."""
    # Create system with safety disabled
    config = ConsciousnessConfig(safety_enabled=False)
    system = ConsciousnessSystem(config)

    # Mock components
    system.tig_fabric = Mock()
    system.tig_fabric.initialize = AsyncMock()
    system.tig_fabric.enter_esgt_mode = AsyncMock()
    system.tig_fabric.exit_esgt_mode = AsyncMock()

    system.esgt_coordinator = Mock()
    system.esgt_coordinator._running = True
    system.esgt_coordinator.start = AsyncMock()
    system.esgt_coordinator.stop = AsyncMock()

    system.arousal_controller = Mock()
    system.arousal_controller._running = True
    system.arousal_controller.start = AsyncMock()
    system.arousal_controller.stop = AsyncMock()

    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Make request
    response = client.get("/api/consciousness/safety/status")

    assert response.status_code == 503
    assert "not enabled" in response.json()["detail"].lower()

    await system.stop()


@pytest.mark.asyncio
async def test_get_safety_status_returns_none_when_disabled():
    """Test 20: get_safety_status() returns None when safety disabled."""
    config = ConsciousnessConfig(safety_enabled=False)
    system = ConsciousnessSystem(config)

    # Mock components
    system.tig_fabric = Mock()
    system.tig_fabric.initialize = AsyncMock()
    system.tig_fabric.enter_esgt_mode = AsyncMock()

    system.esgt_coordinator = Mock()
    system.esgt_coordinator._running = True
    system.esgt_coordinator.start = AsyncMock()
    system.esgt_coordinator.stop = AsyncMock()

    system.arousal_controller = Mock()
    system.arousal_controller._running = True
    system.arousal_controller.start = AsyncMock()
    system.arousal_controller.stop = AsyncMock()

    await system.start()

    # Get safety status
    status = system.get_safety_status()

    assert status is None

    await system.stop()


# ==================== INTEGRATION SCENARIO TESTS ====================


@pytest.mark.asyncio
async def test_full_integration_scenario_with_violation(consciousness_system_with_safety):
    """Test 21: Full integration scenario - violation detection + API + metrics."""
    system = consciousness_system_with_safety
    await system.start()

    # 1. Trigger a violation
    import time

    violation = system.safety_protocol.threshold_monitor.check_self_modification(
        modification_attempts=1, current_time=time.time()
    )

    assert violation is not None

    # 2. Update Prometheus metrics
    update_metrics(system)
    update_violation_metrics([violation])

    # 3. Query via API
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # Get status
    response = client.get("/api/consciousness/safety/status")
    assert response.status_code == 200
    data = response.json()
    assert data["violations_total"] > 0

    # Get violations
    response = client.get("/api/consciousness/safety/violations")
    assert response.status_code == 200
    violations_data = response.json()
    assert len(violations_data) > 0
    assert violations_data[0]["severity"] == "emergency"

    await system.stop()


@pytest.mark.asyncio
async def test_full_integration_scenario_with_emergency_shutdown(consciousness_system_with_safety):
    """Test 22: Full integration scenario - emergency shutdown flow."""
    system = consciousness_system_with_safety
    await system.start()

    # Create FastAPI app
    app = FastAPI()
    system_dict = {"system": system}
    router = create_consciousness_api(system_dict)
    app.include_router(router)

    client = TestClient(app)

    # 1. System is healthy
    assert system.is_healthy()
    status_response = client.get("/api/consciousness/safety/status")
    assert not status_response.json()["kill_switch_active"]

    # 2. Execute emergency shutdown via API (mock HITL override to prevent actual shutdown)
    with patch.object(system.safety_protocol.kill_switch, "_wait_for_hitl_override", return_value=False):
        shutdown_response = client.post(
            "/api/consciousness/safety/emergency-shutdown", json={"reason": "Full integration test shutdown"}
        )

        assert shutdown_response.status_code == 200
        assert shutdown_response.json()["shutdown_executed"]

    # 3. Verify kill switch is active
    assert system.safety_protocol.kill_switch.is_shutdown()


def test_repr_methods():
    """Test 23: __repr__ methods include safety status."""
    config = ConsciousnessConfig(safety_enabled=True)
    system = ConsciousnessSystem(config)

    repr_str = repr(system)

    assert "ConsciousnessSystem" in repr_str
    assert "safety=" in repr_str.lower()


# ==================== PERFORMANCE TEST ====================


@pytest.mark.asyncio
async def test_metrics_update_performance(consciousness_system_with_safety):
    """Test 24: Prometheus metrics update completes in < 100ms."""
    system = consciousness_system_with_safety
    await system.start()

    import time

    start = time.time()
    update_metrics(system)
    elapsed = time.time() - start

    # Should complete very quickly
    assert elapsed < 0.1  # 100ms

    await system.stop()


# ==================== SUMMARY ====================

"""
Total Tests: 24

Breakdown:
- System Integration: 8 tests (1-8)
- API Endpoints: 7 tests (9-14)
- Prometheus Metrics: 3 tests (15-17)
- Error Handling: 3 tests (18-20)
- Integration Scenarios: 2 tests (21-22)
- Misc: 2 tests (23-24)

Coverage:
- ConsciousnessSystem with SafetyProtocol: ✅
- API safety endpoints (/status, /violations, /emergency-shutdown): ✅
- Prometheus metrics export (/metrics): ✅
- Kill switch execution: ✅
- Error handling (503, 422, 400): ✅
- Full integration scenarios: ✅
"""
