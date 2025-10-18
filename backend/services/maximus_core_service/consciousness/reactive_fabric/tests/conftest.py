"""Test fixtures for reactive_fabric module.

Provides mocked consciousness_system and subsystem components for testing.

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Sprint: Reactive Fabric Sprint 3 - Test Coverage
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock


# Helper for AsyncMock in tests
class Helpers:
    AsyncMock = AsyncMock


pytest.helpers = Helpers()


@pytest.fixture
def mock_tig_fabric():
    """Mock TIG Fabric subsystem."""
    mock = MagicMock()
    mock.nodes = list(range(10))  # 10 nodes
    mock.edge_count = 25

    # get_metrics() returns object with avg_latency_us
    mock_metrics = MagicMock()
    mock_metrics.avg_latency_us = 150.0
    mock.get_metrics.return_value = mock_metrics

    mock.get_coherence.return_value = 0.85
    return mock


@pytest.fixture
def mock_esgt_coordinator():
    """Mock ESGT Coordinator subsystem."""
    mock = MagicMock()
    mock.total_events = 100
    mock.get_success_rate.return_value = 0.92
    mock.get_recent_coherence.return_value = 0.88
    mock.ignition_timestamps = [time.time() - i for i in range(10)]

    # Mock event history for event_collector
    mock_esgt_event = MagicMock()
    mock_esgt_event.event_id = "test_esgt_001"
    mock_esgt_event.success = True
    mock_esgt_event.achieved_coherence = 0.88
    mock_esgt_event.timestamp_start = time.time()
    mock_esgt_event.total_duration_ms = 150.0
    mock_esgt_event.node_count = 8
    mock.event_history = [mock_esgt_event]

    # For orchestrator trigger execution
    mock.initiate_esgt = AsyncMock()
    mock_event = MagicMock()
    mock_event.success = True
    mock_event.event_id = "esgt_test_001"
    mock_event.achieved_coherence = 0.87
    mock.initiate_esgt.return_value = mock_event

    return mock


@pytest.fixture
def mock_arousal_controller():
    """Mock Arousal Controller subsystem."""
    mock = MagicMock()

    # get_current_arousal() returns ArousalState object
    arousal_state = MagicMock()
    arousal_state.arousal = 0.65
    arousal_state.level = MagicMock()
    arousal_state.level.value = "MODERATE"
    arousal_state.stress_contribution = 0.3
    arousal_state.need_contribution = 0.2

    mock.get_current_arousal.return_value = arousal_state
    return mock


@pytest.fixture
def mock_prefrontal_cortex():
    """Mock PFC (Prefrontal Cortex) subsystem."""
    mock = MagicMock()
    mock.get_status = AsyncMock(return_value={
        "total_signals_processed": 42,
        "total_actions_generated": 10,
        "approval_rate": 0.85,
    })
    return mock


@pytest.fixture
def mock_tom_engine():
    """Mock ToM (Theory of Mind) Engine subsystem."""
    mock = MagicMock()
    mock.get_stats = AsyncMock(return_value={
        "total_agents": 5,
        "memory": {
            "total_beliefs": 25,
        },
        "redis_cache": {
            "enabled": True,
            "hit_rate": 0.75,
        },
    })
    return mock


@pytest.fixture
def mock_safety_protocol():
    """Mock Safety Protocol subsystem."""
    mock = MagicMock()
    mock.violations = 0
    mock.kill_switch_active = False
    return mock


@pytest.fixture
def mock_consciousness_system(
    mock_tig_fabric,
    mock_esgt_coordinator,
    mock_arousal_controller,
    mock_prefrontal_cortex,
    mock_tom_engine,
    mock_safety_protocol,
):
    """Mock complete ConsciousnessSystem for testing.

    Provides all necessary subsystem mocks with realistic default values.
    """
    mock = MagicMock()

    # Subsystems
    mock.tig_fabric = mock_tig_fabric
    mock.esgt_coordinator = mock_esgt_coordinator
    mock.arousal_controller = mock_arousal_controller
    mock.prefrontal_cortex = mock_prefrontal_cortex
    mock.tom_engine = mock_tom_engine
    mock.safety_protocol = mock_safety_protocol

    # get_safety_status() is on the system itself
    mock.get_safety_status.return_value = {
        "active_violations": 0,
        "kill_switch_triggered": False,
    }

    # get_safety_violations() for event_collector
    mock_violation = MagicMock()
    mock_violation.violation_id = "vio_001"
    mock_violation.violation_type = MagicMock()
    mock_violation.violation_type.value = "THRESHOLD"
    mock_violation.severity = MagicMock()
    mock_violation.severity.value = "HIGH"
    mock_violation.timestamp = MagicMock()
    mock_violation.timestamp.timestamp.return_value = time.time()
    mock_violation.value_observed = 0.95
    mock_violation.threshold_violated = 0.80
    mock_violation.message = "Test violation"
    mock.get_safety_violations.return_value = [mock_violation]

    return mock


@pytest.fixture
def mock_consciousness_system_unhealthy(mock_consciousness_system):
    """Mock consciousness system in unhealthy state.

    High latency, low success rate, safety violations, etc.
    """
    # TIG Fabric issues - high latency
    mock_metrics = MagicMock()
    mock_metrics.avg_latency_us = 15000.0  # Very high latency
    mock_consciousness_system.tig_fabric.get_metrics.return_value = mock_metrics
    mock_consciousness_system.tig_fabric.get_coherence.return_value = 0.45

    # ESGT issues
    mock_consciousness_system.esgt_coordinator.get_success_rate.return_value = 0.55

    # Extreme arousal
    arousal_state = MagicMock()
    arousal_state.arousal = 0.95
    arousal_state.level = MagicMock()
    arousal_state.level.value = "EXTREME_HIGH"
    arousal_state.stress_contribution = 0.9
    arousal_state.need_contribution = 0.1
    mock_consciousness_system.arousal_controller.get_current_arousal.return_value = arousal_state

    # Safety violations
    mock_consciousness_system.get_safety_status.return_value = {
        "active_violations": 3,
        "kill_switch_triggered": False,
    }

    return mock_consciousness_system


@pytest.fixture
def mock_consciousness_system_critical(mock_consciousness_system):
    """Mock consciousness system in critical state.

    Kill switch active, multiple safety violations.
    """
    mock_consciousness_system.tig_fabric.get_coherence.return_value = 0.25
    mock_consciousness_system.esgt_coordinator.get_success_rate.return_value = 0.30

    # Critical safety state
    mock_consciousness_system.get_safety_status.return_value = {
        "active_violations": 5,
        "kill_switch_triggered": True,
    }

    return mock_consciousness_system
