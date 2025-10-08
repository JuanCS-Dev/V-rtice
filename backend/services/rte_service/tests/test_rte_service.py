"""Unit tests for RTE (Real-Time Execution) Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Execute real-time command (success/priority levels)
- Ingest data stream (processing/ML prediction/Hyperscan/playbook trigger)
- Request validation (Pydantic models)
- Edge cases and error handling

Note: FusionEngine, FastML, HyperscanMatcher, and RealTimePlaybookExecutor
are mocked in tests to isolate API logic (test infrastructure mocking, not production code).
"""

# Import the FastAPI app
import sys
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/rte_service")
from main import app

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_fusion_engine():
    """Mock FusionEngine for testing."""
    with patch("main.fusion_engine") as mock_fusion:
        mock_fusion.fuse_data = AsyncMock(return_value={"fused": True, "data_count": 1})
        yield mock_fusion


@pytest_asyncio.fixture
async def mock_fast_ml():
    """Mock FastML for testing."""
    with patch("main.fast_ml") as mock_ml:
        mock_ml.predict = AsyncMock(return_value={"prediction_value": 0.5, "confidence": 0.85})
        yield mock_ml


@pytest_asyncio.fixture
async def mock_hyperscan_matcher():
    """Mock HyperscanMatcher for testing."""
    with patch("main.hyperscan_matcher") as mock_hyperscan:
        mock_hyperscan.scan_data = AsyncMock(return_value=[])
        mock_hyperscan.compile_patterns = AsyncMock(return_value=True)
        yield mock_hyperscan


@pytest_asyncio.fixture
async def mock_playbook_executor():
    """Mock RealTimePlaybookExecutor for testing."""
    with patch("main.real_time_playbook_executor") as mock_executor:
        mock_executor.execute_command = AsyncMock(
            return_value={"status": "executed", "action": "command_executed", "duration_ms": 150}
        )
        yield mock_executor


def create_realtime_command(command_name="block_ip", priority=5, parameters=None):
    """Helper to create RealTimeCommand payload."""
    if parameters is None:
        parameters = {"ip_address": "192.168.1.100", "duration": 3600}
    return {"command_name": command_name, "parameters": parameters, "priority": priority}


def create_data_stream_ingest(stream_id="stream-001", data_type="network_packet", data=None):
    """Helper to create DataStreamIngest payload."""
    if data is None:
        data = {"source_ip": "10.0.0.1", "dest_ip": "10.0.0.2", "payload": "test_data"}
    return {"stream_id": stream_id, "data": data, "data_type": data_type}


# ==================== HEALTH CHECK TESTS ====================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns operational status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "operational" in data["message"].lower()


# ==================== EXECUTE REAL-TIME COMMAND TESTS ====================


@pytest.mark.asyncio
class TestExecuteRealtimeCommandEndpoint:
    """Test execute real-time command endpoint."""

    async def test_execute_command_success(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing real-time command successfully."""
        payload = create_realtime_command()
        response = await client.post("/execute_realtime_command", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "timestamp" in data
        assert "execution_result" in data
        assert data["execution_result"]["status"] == "executed"

        # Verify playbook executor was called
        mock_playbook_executor.execute_command.assert_called_once_with(
            "block_ip", {"ip_address": "192.168.1.100", "duration": 3600}
        )

    async def test_execute_command_different_priorities(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing commands with different priority levels."""
        priorities = [1, 3, 5, 7, 10]

        for priority in priorities:
            payload = create_realtime_command(priority=priority)
            response = await client.post("/execute_realtime_command", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    async def test_execute_command_different_command_types(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing different command types."""
        commands = [
            ("block_ip", {"ip_address": "10.0.0.1"}),
            ("isolate_process", {"pid": 1234, "host": "server01"}),
            ("quarantine_file", {"file_path": "/tmp/malware.exe"}),
            ("kill_connection", {"connection_id": "conn-123"}),
        ]

        for command_name, parameters in commands:
            payload = create_realtime_command(command_name=command_name, parameters=parameters)
            response = await client.post("/execute_realtime_command", json=payload)
            assert response.status_code == 200

    async def test_execute_command_timestamp_format(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test that execution result includes valid ISO timestamp."""
        payload = create_realtime_command()
        response = await client.post("/execute_realtime_command", json=payload)

        data = response.json()
        assert "timestamp" in data
        # Verify ISO format
        datetime.fromisoformat(data["timestamp"])

    async def test_execute_command_with_complex_parameters(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing command with complex nested parameters."""
        payload = create_realtime_command(
            command_name="advanced_mitigation",
            parameters={
                "target": {"type": "network", "identifiers": ["10.0.0.0/24", "192.168.1.0/24"]},
                "actions": ["block", "log", "alert"],
                "metadata": {"severity": "critical", "ttl": 7200, "auto_expire": True},
            },
        )

        response = await client.post("/execute_realtime_command", json=payload)
        assert response.status_code == 200


# ==================== INGEST DATA STREAM TESTS ====================


@pytest.mark.asyncio
class TestIngestDataStreamEndpoint:
    """Test ingest data stream endpoint."""

    async def test_ingest_stream_success(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting data stream successfully."""
        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert "timestamp" in data
        assert "fused_data_summary" in data
        assert "ml_prediction" in data
        assert "hyperscan_matches" in data
        assert "playbook_action" in data

        # Verify components were called in sequence
        mock_fusion_engine.fuse_data.assert_called_once()
        mock_fast_ml.predict.assert_called_once()
        mock_hyperscan_matcher.scan_data.assert_called_once()

    async def test_ingest_stream_no_threat_detected(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream when no threat detected (low ML score, no matches)."""
        # Configure mocks for low threat
        mock_fast_ml.predict = AsyncMock(return_value={"prediction_value": 0.3})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=[])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        data = response.json()
        assert data["status"] == "processed"
        # Playbook should not be triggered (or return no_action_needed)
        assert data["playbook_action"]["status"] == "no_action_needed"
        # execute_command should not be called for critical_threat_response
        assert mock_playbook_executor.execute_command.call_count == 0

    async def test_ingest_stream_high_ml_prediction_triggers_playbook(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with high ML prediction triggers playbook."""
        # Configure mocks for high threat (>0.7)
        mock_fast_ml.predict = AsyncMock(return_value={"prediction_value": 0.85})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=[])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        data = response.json()
        assert data["status"] == "processed"
        # Playbook should be triggered
        mock_playbook_executor.execute_command.assert_called_once()
        call_args = mock_playbook_executor.execute_command.call_args
        assert call_args[0][0] == "critical_threat_response"

    async def test_ingest_stream_hyperscan_matches_trigger_playbook(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with Hyperscan matches triggers playbook."""
        # Configure mocks for Hyperscan detection
        mock_fast_ml.predict = AsyncMock(return_value={"prediction_value": 0.3})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=[{"pattern": "malicious_pattern_1", "offset": 42}])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        data = response.json()
        assert data["status"] == "processed"
        # Playbook should be triggered due to Hyperscan matches
        mock_playbook_executor.execute_command.assert_called_once()

    async def test_ingest_stream_different_data_types(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting different data stream types."""
        data_types = ["network_packet", "log_entry", "sensor_reading", "http_request", "dns_query"]

        for data_type in data_types:
            payload = create_data_stream_ingest(data_type=data_type)
            response = await client.post("/ingest_data_stream", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processed"

    async def test_ingest_stream_fusion_engine_integration(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test that fusion engine receives data correctly."""
        mock_fusion_engine.fuse_data = AsyncMock(return_value={"fused": True, "enhanced_data": "test"})

        payload = create_data_stream_ingest(data={"metric1": 100, "metric2": 200})
        response = await client.post("/ingest_data_stream", json=payload)

        # Verify fusion engine was called with wrapped data
        call_args = mock_fusion_engine.fuse_data.call_args
        assert call_args[0][0] == [{"metric1": 100, "metric2": 200}]

    async def test_ingest_stream_ml_prediction_receives_fused_data(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test that ML prediction receives fused data."""
        mock_fusion_engine.fuse_data = AsyncMock(return_value={"fused_key": "fused_value"})

        payload = create_data_stream_ingest()
        await client.post("/ingest_data_stream", json=payload)

        # Verify ML predict was called with fused data
        call_args = mock_fast_ml.predict.call_args
        assert call_args[0][0] == {"fused_key": "fused_value"}
        assert call_args[0][1] == "threat_score"


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_execute_command_missing_command_name_returns_422(self, client, mock_playbook_executor):
        """Test executing command without command_name."""
        payload = {
            "parameters": {"test": "value"},
            "priority": 5,
            # Missing command_name
        }

        response = await client.post("/execute_realtime_command", json=payload)
        assert response.status_code == 422

    async def test_execute_command_missing_parameters_returns_422(self, client, mock_playbook_executor):
        """Test executing command without parameters."""
        payload = {
            "command_name": "block_ip",
            "priority": 5,
            # Missing parameters
        }

        response = await client.post("/execute_realtime_command", json=payload)
        assert response.status_code == 422

    async def test_ingest_stream_missing_stream_id_returns_422(self, client):
        """Test ingesting stream without stream_id."""
        payload = {
            "data": {"test": "value"},
            "data_type": "network_packet",
            # Missing stream_id
        }

        response = await client.post("/ingest_data_stream", json=payload)
        assert response.status_code == 422

    async def test_ingest_stream_missing_data_type_returns_422(self, client):
        """Test ingesting stream without data_type."""
        payload = {
            "stream_id": "stream-001",
            "data": {"test": "value"},
            # Missing data_type
        }

        response = await client.post("/ingest_data_stream", json=payload)
        assert response.status_code == 422

    async def test_execute_command_invalid_priority_type(self, client, mock_playbook_executor):
        """Test executing command with invalid priority type."""
        payload = {
            "command_name": "block_ip",
            "parameters": {},
            "priority": "high",  # Should be int
        }

        response = await client.post("/execute_realtime_command", json=payload)
        assert response.status_code == 422


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_execute_command_priority_boundaries(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing command with boundary priority values."""
        # Priority 1 (lowest)
        payload1 = create_realtime_command(priority=1)
        response1 = await client.post("/execute_realtime_command", json=payload1)
        assert response1.status_code == 200

        # Priority 10 (highest)
        payload10 = create_realtime_command(priority=10)
        response10 = await client.post("/execute_realtime_command", json=payload10)
        assert response10.status_code == 200

    async def test_execute_command_default_priority(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test executing command uses default priority (5)."""
        payload = {
            "command_name": "test_command",
            "parameters": {},
            # No priority specified (should default to 5)
        }

        response = await client.post("/execute_realtime_command", json=payload)
        assert response.status_code == 200

    async def test_ingest_stream_empty_data(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with empty data dict."""
        payload = create_data_stream_ingest(data={})
        response = await client.post("/ingest_data_stream", json=payload)
        assert response.status_code == 200

    async def test_ingest_stream_large_data_payload(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with large data payload."""
        large_data = {f"field_{i}": f"value_{i}" for i in range(100)}
        payload = create_data_stream_ingest(data=large_data)

        response = await client.post("/ingest_data_stream", json=payload)
        assert response.status_code == 200

    async def test_ingest_stream_ml_prediction_exactly_0_7(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with ML prediction exactly at threshold (0.7)."""
        # Test >0.7 triggers playbook
        mock_fast_ml.predict = AsyncMock(return_value={"prediction_value": 0.7})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=[])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        # 0.7 is NOT >0.7, so should not trigger
        data = response.json()
        assert data["playbook_action"]["status"] == "no_action_needed"

    async def test_ingest_stream_ml_prediction_just_above_threshold(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test ingesting stream with ML prediction just above threshold (0.71)."""
        mock_fast_ml.predict = AsyncMock(return_value={"prediction_value": 0.71})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=[])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        # 0.71 > 0.7, should trigger playbook
        mock_playbook_executor.execute_command.assert_called_once()

    async def test_execute_command_preserves_parameters(
        self, client, mock_playbook_executor, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher
    ):
        """Test that command parameters are passed without modification."""
        complex_params = {"string": "test", "number": 42, "bool": True, "list": [1, 2, 3], "nested": {"key": "value"}}

        payload = create_realtime_command(parameters=complex_params)
        await client.post("/execute_realtime_command", json=payload)

        # Verify exact parameters were passed
        call_args = mock_playbook_executor.execute_command.call_args
        assert call_args[0][1] == complex_params

    async def test_ingest_stream_response_includes_all_components(
        self, client, mock_fusion_engine, mock_fast_ml, mock_hyperscan_matcher, mock_playbook_executor
    ):
        """Test that ingest response includes data from all processing stages."""
        mock_fusion_engine.fuse_data = AsyncMock(return_value={"stage": "fusion"})
        mock_fast_ml.predict = AsyncMock(return_value={"stage": "ml", "prediction_value": 0.5})
        mock_hyperscan_matcher.scan_data = AsyncMock(return_value=["match1"])

        payload = create_data_stream_ingest()
        response = await client.post("/ingest_data_stream", json=payload)

        data = response.json()
        assert data["fused_data_summary"]["stage"] == "fusion"
        assert data["ml_prediction"]["stage"] == "ml"
        assert len(data["hyperscan_matches"]) == 1
