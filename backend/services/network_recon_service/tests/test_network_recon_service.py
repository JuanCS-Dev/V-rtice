"""Unit tests for Network Reconnaissance Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Start reconnaissance task (nmap, masscan)
- Get task status (found/not found)
- Get task results (found/not found)
- Get service metrics
- Request validation
- Edge cases and boundary conditions

Note: ReconEngine and MetricsCollector are mocked in tests to isolate
API logic (test infrastructure mocking, not production code).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the FastAPI app
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/network_recon_service")
from api import app
from models import ReconStatus, ReconTask, ReconResult


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_recon_engine():
    """Mock ReconEngine for testing."""
    with patch('api.recon_engine') as mock_engine:
        # Mock methods
        mock_engine.start_recon_task = AsyncMock()
        mock_engine.get_task = MagicMock(return_value=None)  # Default: not found
        mock_engine.get_task_results = MagicMock(return_value=None)  # Default: not found
        yield mock_engine


@pytest_asyncio.fixture
async def mock_metrics_collector():
    """Mock MetricsCollector for testing."""
    with patch('api.metrics_collector') as mock_metrics:
        mock_metrics.get_all_metrics = MagicMock(return_value={
            "total_scans": 100,
            "active_scans": 5,
            "completed_scans": 95
        })
        yield mock_metrics


def create_recon_task(task_id="task-123", target="192.168.1.0/24", status=ReconStatus.PENDING):
    """Helper to create ReconTask object."""
    return ReconTask(
        id=task_id,
        target=target,
        scan_type="nmap_full",
        parameters={"ports": "1-1000"},
        start_time=datetime.now().isoformat(),
        status=status
    )


def create_recon_result(task_id="task-123"):
    """Helper to create ReconResult object."""
    return ReconResult(
        task_id=task_id,
        status="success",
        output={"hosts_found": 10, "open_ports": [22, 80, 443]},
        timestamp=datetime.now().isoformat()
    )


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


# ==================== START RECON TESTS ====================


@pytest.mark.asyncio
class TestStartReconEndpoint:
    """Test start reconnaissance endpoint."""

    async def test_start_recon_nmap_scan(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting nmap reconnaissance scan."""
        payload = {
            "target": "192.168.1.0/24",
            "scan_type": "nmap_full",
            "parameters": {"ports": "1-1000"}
        }

        response = await client.post("/start_recon", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "id" in data
        assert data["target"] == "192.168.1.0/24"
        assert data["scan_type"] == "nmap_full"
        assert data["parameters"]["ports"] == "1-1000"
        assert data["status"] == "pending"
        assert "start_time" in data

        # ReconEngine should have been called
        assert mock_recon_engine.start_recon_task.called

    async def test_start_recon_masscan_scan(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting masscan reconnaissance scan."""
        payload = {
            "target": "10.0.0.1",
            "scan_type": "masscan_ports",
            "parameters": {"ports": "80,443,8080"}
        }

        response = await client.post("/start_recon", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["scan_type"] == "masscan_ports"
        assert data["target"] == "10.0.0.1"

    async def test_start_recon_without_parameters(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan without optional parameters."""
        payload = {
            "target": "example.com",
            "scan_type": "nmap_quick"
            # No parameters field
        }

        response = await client.post("/start_recon", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should default to empty dict
        assert data["parameters"] == {}

    async def test_start_recon_generates_unique_task_id(self, client, mock_recon_engine, mock_metrics_collector):
        """Test that each scan gets a unique task ID (UUID)."""
        payload = {
            "target": "192.168.1.1",
            "scan_type": "nmap_full"
        }

        response1 = await client.post("/start_recon", json=payload)
        response2 = await client.post("/start_recon", json=payload)

        task_id1 = response1.json()["id"]
        task_id2 = response2.json()["id"]

        # UUIDs should be different
        assert task_id1 != task_id2
        # Should be valid UUID format
        assert len(task_id1) == 36  # UUID string format
        assert "-" in task_id1

    async def test_start_recon_task_created_in_background(self, client, mock_recon_engine, mock_metrics_collector):
        """Test that recon task is started in background (asyncio.create_task)."""
        payload = {
            "target": "192.168.1.1",
            "scan_type": "nmap_full"
        }

        response = await client.post("/start_recon", json=payload)

        # API should return immediately (not wait for scan to complete)
        assert response.status_code == 200
        # Engine's start_recon_task should have been called
        assert mock_recon_engine.start_recon_task.called


# ==================== GET TASK STATUS TESTS ====================


@pytest.mark.asyncio
class TestGetTaskStatusEndpoint:
    """Test get task status endpoint."""

    async def test_get_task_status_found(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting status of existing task."""
        task = create_recon_task(task_id="task-found", status=ReconStatus.RUNNING)
        mock_recon_engine.get_task.return_value = task

        response = await client.get("/recon_task/task-found/status")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "task-found"
        assert data["status"] == "running"
        assert data["target"] == "192.168.1.0/24"

        # Engine's get_task should have been called
        mock_recon_engine.get_task.assert_called_once_with("task-found")

    async def test_get_task_status_not_found(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting status of non-existent task."""
        mock_recon_engine.get_task.return_value = None

        response = await client.get("/recon_task/nonexistent/status")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_task_status_different_states(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting task status in different states."""
        states = [
            (ReconStatus.PENDING, "pending"),
            (ReconStatus.RUNNING, "running"),
            (ReconStatus.COMPLETED, "completed"),
            (ReconStatus.FAILED, "failed"),
            (ReconStatus.CANCELLED, "cancelled")
        ]

        for status_enum, status_str in states:
            task = create_recon_task(status=status_enum)
            mock_recon_engine.get_task.return_value = task

            response = await client.get("/recon_task/test-id/status")

            assert response.status_code == 200
            assert response.json()["status"] == status_str


# ==================== GET TASK RESULTS TESTS ====================


@pytest.mark.asyncio
class TestGetTaskResultsEndpoint:
    """Test get task results endpoint."""

    async def test_get_task_results_found(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting results of completed task."""
        result = create_recon_result(task_id="task-complete")
        mock_recon_engine.get_task_results.return_value = result

        response = await client.get("/recon_task/task-complete/results")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-complete"
        assert data["status"] == "success"
        assert "hosts_found" in data["output"]
        assert data["output"]["hosts_found"] == 10

        # Engine's get_task_results should have been called
        mock_recon_engine.get_task_results.assert_called_once_with("task-complete")

    async def test_get_task_results_not_found(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting results of non-existent or incomplete task."""
        mock_recon_engine.get_task_results.return_value = None

        response = await client.get("/recon_task/nonexistent/results")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower() or "not yet available" in data["detail"].lower()

    async def test_get_task_results_with_complex_output(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting results with complex nested output."""
        result = ReconResult(
            task_id="task-complex",
            status="success",
            output={
                "hosts": [
                    {"ip": "192.168.1.1", "ports": [22, 80], "services": ["ssh", "http"]},
                    {"ip": "192.168.1.2", "ports": [443], "services": ["https"]}
                ],
                "summary": {"total_hosts": 2, "total_ports": 3}
            },
            timestamp=datetime.now().isoformat()
        )
        mock_recon_engine.get_task_results.return_value = result

        response = await client.get("/recon_task/task-complex/results")

        assert response.status_code == 200
        data = response.json()
        assert len(data["output"]["hosts"]) == 2
        assert data["output"]["summary"]["total_hosts"] == 2


# ==================== GET METRICS TESTS ====================


@pytest.mark.asyncio
class TestGetMetricsEndpoint:
    """Test get service metrics endpoint."""

    async def test_get_metrics_returns_stats(self, client, mock_recon_engine, mock_metrics_collector):
        """Test that metrics endpoint returns service statistics."""
        response = await client.get("/metrics")

        assert response.status_code == 200
        data = response.json()

        # Should return mocked metrics
        assert data["total_scans"] == 100
        assert data["active_scans"] == 5
        assert data["completed_scans"] == 95

        # Metrics collector should have been called
        mock_metrics_collector.get_all_metrics.assert_called_once()

    async def test_get_metrics_with_empty_stats(self, client, mock_recon_engine, mock_metrics_collector):
        """Test metrics endpoint with no activity."""
        mock_metrics_collector.get_all_metrics.return_value = {
            "total_scans": 0,
            "active_scans": 0,
            "completed_scans": 0
        }

        response = await client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 0


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_start_recon_missing_target_returns_422(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan without target."""
        payload = {
            "scan_type": "nmap_full"
            # Missing target
        }

        response = await client.post("/start_recon", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_start_recon_missing_scan_type_returns_422(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan without scan_type."""
        payload = {
            "target": "192.168.1.1"
            # Missing scan_type
        }

        response = await client.post("/start_recon", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_start_recon_empty_target_accepted(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan with empty target string."""
        payload = {
            "target": "",
            "scan_type": "nmap_quick"
        }

        response = await client.post("/start_recon", json=payload)

        # Should be accepted (validation happens in recon engine)
        assert response.status_code == 200


# ==================== MODEL VALIDATION TESTS ====================


class TestModels:
    """Test Pydantic models."""

    def test_recon_status_enum_values(self):
        """Test ReconStatus enum has expected values."""
        assert ReconStatus.PENDING.value == "pending"
        assert ReconStatus.RUNNING.value == "running"
        assert ReconStatus.COMPLETED.value == "completed"
        assert ReconStatus.FAILED.value == "failed"
        assert ReconStatus.CANCELLED.value == "cancelled"

    def test_recon_task_creation(self):
        """Test creating ReconTask model."""
        task = ReconTask(
            id="task-001",
            target="192.168.1.0/24",
            scan_type="nmap_full",
            parameters={"ports": "1-1000"},
            start_time="2025-10-07T12:00:00",
            status=ReconStatus.PENDING
        )

        assert task.id == "task-001"
        assert task.target == "192.168.1.0/24"
        assert task.status == ReconStatus.PENDING

    def test_recon_task_default_start_time(self):
        """Test ReconTask generates default start_time."""
        task = ReconTask(
            id="task-002",
            target="10.0.0.1",
            scan_type="masscan",
            parameters={}
        )

        # Should have generated timestamp
        assert task.start_time is not None
        datetime.fromisoformat(task.start_time)

    def test_recon_result_creation(self):
        """Test creating ReconResult model."""
        result = ReconResult(
            task_id="task-001",
            status="success",
            output={"hosts": 5},
            timestamp="2025-10-07T12:30:00"
        )

        assert result.task_id == "task-001"
        assert result.status == "success"
        assert result.output["hosts"] == 5


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_start_recon_multiple_targets_format(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan with different target formats."""
        targets = [
            "192.168.1.1",           # Single IP
            "192.168.1.0/24",        # CIDR range
            "example.com",            # Domain
            "192.168.1.1-254",       # IP range
        ]

        for target in targets:
            payload = {
                "target": target,
                "scan_type": "nmap_quick"
            }
            response = await client.post("/start_recon", json=payload)
            assert response.status_code == 200
            assert response.json()["target"] == target

    async def test_start_recon_different_scan_types(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting different scan types."""
        scan_types = [
            "nmap_full",
            "nmap_quick",
            "masscan_ports",
            "custom_scan"
        ]

        for scan_type in scan_types:
            payload = {
                "target": "192.168.1.1",
                "scan_type": scan_type
            }
            response = await client.post("/start_recon", json=payload)
            assert response.status_code == 200
            assert response.json()["scan_type"] == scan_type

    async def test_start_recon_complex_parameters(self, client, mock_recon_engine, mock_metrics_collector):
        """Test starting scan with complex nested parameters."""
        payload = {
            "target": "192.168.1.0/24",
            "scan_type": "nmap_full",
            "parameters": {
                "ports": "1-65535",
                "timing": "aggressive",
                "scripts": ["vuln", "default", "discovery"],
                "options": {
                    "os_detection": True,
                    "service_version": True,
                    "traceroute": False
                }
            }
        }

        response = await client.post("/start_recon", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["parameters"]["scripts"] == ["vuln", "default", "discovery"]
        assert data["parameters"]["options"]["os_detection"] is True

    async def test_get_task_status_with_special_characters_in_id(self, client, mock_recon_engine, mock_metrics_collector):
        """Test getting task status with special characters in ID."""
        task_ids = [
            "task-with-dashes",
            "task_with_underscores",
            "TASK-UPPERCASE",
            "task.with.dots"
        ]

        for task_id in task_ids:
            task = create_recon_task(task_id=task_id)
            mock_recon_engine.get_task.return_value = task

            response = await client.get(f"/recon_task/{task_id}/status")
            assert response.status_code == 200
            assert response.json()["id"] == task_id

    async def test_concurrent_scan_requests(self, client, mock_recon_engine, mock_metrics_collector):
        """Test handling multiple concurrent scan requests."""
        import asyncio

        payload = {
            "target": "192.168.1.1",
            "scan_type": "nmap_quick"
        }

        # Send 5 concurrent requests
        responses = await asyncio.gather(*[
            client.post("/start_recon", json=payload)
            for _ in range(5)
        ])

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should have unique IDs
        task_ids = [r.json()["id"] for r in responses]
        assert len(set(task_ids)) == 5  # All unique
