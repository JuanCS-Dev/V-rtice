"""Unit tests for HCL Executor Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Plan execution with action executor
- Kubernetes status endpoint
- Execution status aggregation (completed vs completed_with_errors)
- Request validation
- Edge cases and boundary conditions

Note: ActionExecutor and KubernetesController are mocked in tests to isolate
executor service logic (test infrastructure mocking, not production code).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import the FastAPI app
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/hcl_executor_service")
from main import app


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_action_executor():
    """Mock ActionExecutor for testing."""
    with patch('main.action_executor') as mock_ae:
        mock_ae.execute_actions = AsyncMock(return_value=[
            {"action": "scale_up", "status": "success"},
            {"action": "restart", "status": "success"}
        ])
        yield mock_ae


@pytest_asyncio.fixture
async def mock_k8s_controller():
    """Mock KubernetesController for testing."""
    with patch('main.k8s_controller') as mock_k8s:
        mock_k8s.get_cluster_status = AsyncMock(return_value={
            "nodes": 3,
            "pods_running": 50,
            "status": "healthy"
        })
        yield mock_k8s


def create_execute_plan_request(plan_id="plan-001", num_actions=2, priority=5):
    """Helper to create ExecutePlanRequest payload."""
    return {
        "plan_id": plan_id,
        "actions": [
            {"type": "scale_up", "target": "service_a", "replicas": 3},
            {"type": "restart", "target": "service_b"}
        ][:num_actions],
        "priority": priority
    }


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


# ==================== EXECUTE PLAN TESTS ====================


@pytest.mark.asyncio
class TestExecutePlanEndpoint:
    """Test plan execution endpoint."""

    async def test_execute_plan_success(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with all actions succeeding."""
        payload = create_execute_plan_request()

        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "timestamp" in data
        assert data["plan_id"] == "plan-001"
        assert data["status"] == "completed"
        assert "action_results" in data
        assert len(data["action_results"]) == 2

        # Action executor should have been called
        mock_action_executor.execute_actions.assert_called_once_with(
            "plan-001",
            payload["actions"],
            5
        )

    async def test_execute_plan_with_errors(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with some actions failing."""
        # Mock action executor to return mixed results
        mock_action_executor.execute_actions.return_value = [
            {"action": "scale_up", "status": "success"},
            {"action": "restart", "status": "failed", "error": "Pod not found"}
        ]

        payload = create_execute_plan_request()
        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Status should be "completed_with_errors" because not all actions succeeded
        assert data["status"] == "completed_with_errors"
        assert len(data["action_results"]) == 2

    async def test_execute_plan_all_actions_fail(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan where all actions fail."""
        mock_action_executor.execute_actions.return_value = [
            {"action": "scale_up", "status": "failed", "error": "Connection timeout"},
            {"action": "restart", "status": "failed", "error": "Permission denied"}
        ]

        payload = create_execute_plan_request()
        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Status should be "completed_with_errors"
        assert data["status"] == "completed_with_errors"

    async def test_execute_plan_with_priority(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with custom priority."""
        payload = create_execute_plan_request(priority=10)

        await client.post("/execute_plan", json=payload)

        # Should pass priority to executor
        call_args = mock_action_executor.execute_actions.call_args
        assert call_args[0][2] == 10  # priority argument

    async def test_execute_plan_default_priority(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with default priority (5)."""
        payload = {
            "plan_id": "plan-001",
            "actions": [{"type": "scale_up"}]
            # No priority specified
        }

        await client.post("/execute_plan", json=payload)

        # Should use default priority 5
        call_args = mock_action_executor.execute_actions.call_args
        assert call_args[0][2] == 5

    async def test_execute_plan_empty_actions(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with no actions."""
        mock_action_executor.execute_actions.return_value = []

        payload = {
            "plan_id": "plan-002",
            "actions": [],
            "priority": 5
        }

        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"  # All (0) actions succeeded
        assert len(data["action_results"]) == 0

    async def test_execute_plan_many_actions(self, client, mock_action_executor, mock_k8s_controller):
        """Test executing plan with many actions."""
        mock_action_executor.execute_actions.return_value = [
            {"action": f"action_{i}", "status": "success"}
            for i in range(20)
        ]

        payload = {
            "plan_id": "plan-large",
            "actions": [{"type": f"action_{i}"} for i in range(20)],
            "priority": 5
        }

        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["action_results"]) == 20

    async def test_execute_plan_action_results_preserved(self, client, mock_action_executor, mock_k8s_controller):
        """Test that action executor results are preserved in response."""
        mock_action_executor.execute_actions.return_value = [
            {
                "action": "scale_up",
                "status": "success",
                "details": "Scaled to 5 replicas",
                "duration_ms": 250
            }
        ]

        payload = create_execute_plan_request(num_actions=1)
        response = await client.post("/execute_plan", json=payload)

        data = response.json()
        # All details from action executor should be preserved
        assert data["action_results"][0]["details"] == "Scaled to 5 replicas"
        assert data["action_results"][0]["duration_ms"] == 250


# ==================== KUBERNETES STATUS TESTS ====================


@pytest.mark.asyncio
class TestKubernetesStatusEndpoint:
    """Test Kubernetes status endpoint."""

    async def test_k8s_status_returns_cluster_info(self, client, mock_action_executor, mock_k8s_controller):
        """Test that K8s status endpoint returns cluster information."""
        response = await client.get("/k8s_status")

        assert response.status_code == 200
        data = response.json()

        # Should return mocked K8s status
        assert data["nodes"] == 3
        assert data["pods_running"] == 50
        assert data["status"] == "healthy"

        # K8s controller should have been called
        mock_k8s_controller.get_cluster_status.assert_called_once()

    async def test_k8s_status_calls_controller(self, client, mock_action_executor, mock_k8s_controller):
        """Test that K8s status calls the controller method."""
        await client.get("/k8s_status")

        # Should call get_cluster_status
        assert mock_k8s_controller.get_cluster_status.called


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_execute_plan_missing_plan_id_returns_422(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with missing plan_id."""
        payload = {
            "actions": [{"type": "scale_up"}],
            # Missing plan_id
        }

        response = await client.post("/execute_plan", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_execute_plan_missing_actions_returns_422(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with missing actions."""
        payload = {
            "plan_id": "plan-001",
            # Missing actions
        }

        response = await client.post("/execute_plan", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_execute_plan_invalid_priority_returns_422(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with invalid priority type."""
        payload = {
            "plan_id": "plan-001",
            "actions": [],
            "priority": "high"  # Should be int
        }

        response = await client.post("/execute_plan", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_execute_plan_priority_boundaries(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with boundary priority values (1 and 10)."""
        # Priority 1 (lowest)
        payload1 = create_execute_plan_request(priority=1)
        response1 = await client.post("/execute_plan", json=payload1)
        assert response1.status_code == 200

        # Priority 10 (highest)
        payload10 = create_execute_plan_request(priority=10)
        response10 = await client.post("/execute_plan", json=payload10)
        assert response10.status_code == 200

    async def test_execute_plan_priority_outside_range(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with priority outside 1-10 range (should still work)."""
        # Priority 0
        payload0 = create_execute_plan_request(priority=0)
        response0 = await client.post("/execute_plan", json=payload0)
        assert response0.status_code == 200

        # Priority 100
        payload100 = create_execute_plan_request(priority=100)
        response100 = await client.post("/execute_plan", json=payload100)
        assert response100.status_code == 200

    async def test_execute_plan_special_plan_ids(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with special plan IDs."""
        special_ids = [
            "plan-with-dashes-and-numbers-123",
            "PLAN_UPPERCASE",
            "plan.with.dots",
            "plan_underscore",
            ""  # Empty string (should be accepted by model)
        ]

        for plan_id in special_ids:
            payload = create_execute_plan_request(plan_id=plan_id)
            response = await client.post("/execute_plan", json=payload)
            assert response.status_code == 200

    async def test_execute_plan_complex_action_structure(self, client, mock_action_executor, mock_k8s_controller):
        """Test execution with complex nested action structures."""
        mock_action_executor.execute_actions.return_value = [
            {"action": "complex", "status": "success"}
        ]

        payload = {
            "plan_id": "plan-complex",
            "actions": [
                {
                    "type": "scale",
                    "target": "service_a",
                    "replicas": 5,
                    "metadata": {
                        "reason": "high_load",
                        "constraints": ["max_cost_100", "min_latency_50ms"]
                    },
                    "rollback": {
                        "enabled": True,
                        "threshold_error_rate": 0.05
                    }
                }
            ],
            "priority": 8
        }

        response = await client.post("/execute_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_execute_plan_status_logic_edge_cases(self, client, mock_action_executor, mock_k8s_controller):
        """Test status aggregation logic with edge cases."""
        # Case 1: Single successful action
        mock_action_executor.execute_actions.return_value = [
            {"action": "a1", "status": "success"}
        ]
        payload = create_execute_plan_request(num_actions=1)
        response = await client.post("/execute_plan", json=payload)
        assert response.json()["status"] == "completed"

        # Case 2: Single failed action
        mock_action_executor.execute_actions.return_value = [
            {"action": "a1", "status": "failed"}
        ]
        response = await client.post("/execute_plan", json=payload)
        assert response.json()["status"] == "completed_with_errors"

        # Case 3: Mixed case-sensitive status values
        mock_action_executor.execute_actions.return_value = [
            {"action": "a1", "status": "Success"},  # Capital S
            {"action": "a2", "status": "success"}
        ]
        payload2 = create_execute_plan_request(num_actions=2)
        response = await client.post("/execute_plan", json=payload2)
        # "Success" != "success", so should be "completed_with_errors"
        assert response.json()["status"] == "completed_with_errors"

    async def test_k8s_status_with_degraded_cluster(self, client, mock_action_executor, mock_k8s_controller):
        """Test K8s status when cluster is degraded."""
        mock_k8s_controller.get_cluster_status.return_value = {
            "nodes": 3,
            "nodes_ready": 2,
            "pods_running": 50,
            "pods_pending": 10,
            "status": "degraded"
        }

        response = await client.get("/k8s_status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["nodes_ready"] == 2

    async def test_plan_id_preserved_in_response(self, client, mock_action_executor, mock_k8s_controller):
        """Test that plan_id from request is preserved in response."""
        unique_id = "plan-unique-12345"
        payload = create_execute_plan_request(plan_id=unique_id)

        response = await client.post("/execute_plan", json=payload)

        data = response.json()
        assert data["plan_id"] == unique_id
