"""Unit tests for HCL Planner Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Plan generation with fuzzy controller
- Plan generation with RL agent intervention
- Planner status endpoint
- Request validation
- Edge cases and boundary conditions

Note: FuzzyController and RLAgent are mocked in tests to isolate
planner service logic (test infrastructure mocking, not production code).
"""

# Import the FastAPI app
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/hcl_planner_service")
from backend.services.hcl_planner_service.main import app

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_fuzzy_controller():
    """Mock FuzzyController for testing."""
    with patch("main.fuzzy_controller") as mock_fc:
        mock_fc.generate_actions = MagicMock(return_value=[{"type": "scale_up", "target": "service_a", "replicas": 3}])
        mock_fc.get_status = MagicMock(return_value="operational")
        yield mock_fc


@pytest_asyncio.fixture
async def mock_rl_agent():
    """Mock RLAgent for testing."""
    with patch("main.rl_agent") as mock_rl:
        mock_rl.recommend_actions = AsyncMock(return_value=[{"type": "restart", "target": "service_b"}])
        mock_rl.get_status = AsyncMock(return_value="ready")
        yield mock_rl


def create_plan_request(health_score=1.0, cpu_usage=50.0, requires_intervention=False):
    """Helper to create PlanRequest payload."""
    return {
        "analysis_result": {
            "overall_health_score": health_score,
            "requires_intervention": requires_intervention,
            "anomalies": [],
        },
        "current_state": {"cpu_usage": cpu_usage, "memory_usage": 50.0},
        "operational_goals": {"performance_priority": 0.5, "cost_efficiency": 0.5},
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


# ==================== GENERATE PLAN TESTS ====================


@pytest.mark.asyncio
class TestGeneratePlanEndpoint:
    """Test plan generation endpoint."""

    async def test_generate_plan_healthy_system(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test generating plan for healthy system."""
        payload = create_plan_request(health_score=1.0, requires_intervention=False)

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Check plan structure
        assert "plan_id" in data
        assert data["plan_id"].startswith("plan-")
        assert data["status"] == "generated"
        assert "timestamp" in data
        assert "actions" in data
        assert "plan_details" in data
        assert "estimated_impact" in data

        # Fuzzy controller should be called
        assert mock_fuzzy_controller.generate_actions.called

        # RL agent should NOT be called (no intervention needed)
        assert not mock_rl_agent.recommend_actions.called

    async def test_generate_plan_with_intervention(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test generating plan when intervention is required."""
        payload = create_plan_request(health_score=0.5, requires_intervention=True)

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Both fuzzy controller and RL agent should be called
        assert mock_fuzzy_controller.generate_actions.called
        assert mock_rl_agent.recommend_actions.called

        # Plan should include actions from both
        assert len(data["actions"]) >= 2
        assert "RL agent" in data["plan_details"]

    async def test_generate_plan_actions_aggregated(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that actions from fuzzy and RL are aggregated."""
        mock_fuzzy_controller.generate_actions.return_value = [{"type": "scale_up", "target": "service_a"}]
        mock_rl_agent.recommend_actions.return_value = [{"type": "restart", "target": "service_b"}]

        payload = create_plan_request(requires_intervention=True)
        response = await client.post("/generate_plan", json=payload)

        data = response.json()
        assert len(data["actions"]) == 2
        assert data["actions"][0]["type"] == "scale_up"
        assert data["actions"][1]["type"] == "restart"

    async def test_generate_plan_fuzzy_called_with_correct_params(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that fuzzy controller is called with correct parameters."""
        payload = create_plan_request(health_score=0.75, cpu_usage=80.0)
        payload["operational_goals"]["performance_priority"] = 0.8

        await client.post("/generate_plan", json=payload)

        # Check fuzzy controller was called with correct args
        mock_fuzzy_controller.generate_actions.assert_called_once_with(
            0.75,  # health_score
            80.0,  # cpu_usage
            0.8,  # performance_priority
        )

    async def test_generate_plan_rl_called_with_state_and_analysis(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that RL agent is called with full state and analysis."""
        payload = create_plan_request(requires_intervention=True)

        await client.post("/generate_plan", json=payload)

        # Check RL agent was called with current_state and analysis_result
        call_args = mock_rl_agent.recommend_actions.call_args
        assert call_args is not None
        assert call_args[0][0] == payload["current_state"]
        assert call_args[0][1] == payload["analysis_result"]
        assert call_args[0][2] == payload["operational_goals"]

    async def test_generate_plan_estimated_impact_included(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that plan includes estimated impact."""
        payload = create_plan_request()
        response = await client.post("/generate_plan", json=payload)

        data = response.json()
        assert "estimated_impact" in data
        assert "performance_boost" in data["estimated_impact"]
        assert "cost_reduction" in data["estimated_impact"]

    async def test_generate_plan_id_format(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that plan ID follows correct format."""
        payload = create_plan_request()

        response = await client.post("/generate_plan", json=payload)

        plan_id = response.json()["plan_id"]

        # ID should follow format: plan-YYYYMMDDHHmmSS
        assert plan_id.startswith("plan-")
        assert len(plan_id) == 19  # "plan-" (5) + YYYYMMDDHHMMSS (14)


# ==================== PLANNER STATUS TESTS ====================


@pytest.mark.asyncio
class TestPlannerStatusEndpoint:
    """Test planner status endpoint."""

    async def test_planner_status_returns_component_status(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that status endpoint returns component status."""
        response = await client.get("/planner_status")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "active"
        assert "fuzzy_controller_status" in data
        assert "rl_agent_status" in data

        # Mocked statuses should be returned
        assert data["fuzzy_controller_status"] == "operational"
        assert data["rl_agent_status"] == "ready"

    async def test_planner_status_calls_component_methods(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that status endpoint calls component status methods."""
        await client.get("/planner_status")

        assert mock_fuzzy_controller.get_status.called
        assert mock_rl_agent.get_status.called


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_generate_plan_missing_fields_returns_422(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with missing required fields."""
        payload = {
            "analysis_result": {"overall_health_score": 1.0}
            # Missing current_state and operational_goals
        }

        response = await client.post("/generate_plan", json=payload)

        # Pydantic validation should fail
        assert response.status_code == 422

    async def test_generate_plan_empty_analysis_result(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with empty analysis_result."""
        payload = {"analysis_result": {}, "current_state": {}, "operational_goals": {}}

        response = await client.post("/generate_plan", json=payload)

        # Should succeed (empty dicts are valid)
        assert response.status_code == 200


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_generate_plan_with_zero_health_score(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with health score at 0 (worst case)."""
        payload = create_plan_request(health_score=0.0, requires_intervention=True)

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        # Should handle gracefully

    async def test_generate_plan_with_perfect_health_score(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with health score at 1.0 (perfect)."""
        payload = create_plan_request(health_score=1.0, requires_intervention=False)

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200

    async def test_generate_plan_with_extreme_cpu_usage(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with extreme CPU usage."""
        payload = create_plan_request(cpu_usage=100.0)

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        # Fuzzy controller should handle extreme values

    async def test_generate_plan_fuzzy_returns_empty_actions(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation when fuzzy controller returns no actions."""
        mock_fuzzy_controller.generate_actions.return_value = []

        payload = create_plan_request(requires_intervention=False)
        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should still return valid plan (empty actions list is valid)
        assert "actions" in data
        assert len(data["actions"]) == 0

    async def test_generate_plan_rl_returns_empty_recommendations(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation when RL agent returns no recommendations."""
        mock_rl_agent.recommend_actions.return_value = []

        payload = create_plan_request(requires_intervention=True)
        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should include fuzzy actions only
        assert len(data["actions"]) == 1  # Only fuzzy action

    async def test_generate_plan_with_missing_nested_keys(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation when nested keys are missing (uses defaults)."""
        payload = {
            "analysis_result": {},  # No overall_health_score
            "current_state": {},  # No cpu_usage
            "operational_goals": {},  # No performance_priority
        }

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        # Should use default values from .get() calls
        # fuzzy_controller.generate_actions(1.0, 0.0, 0.5)
        mock_fuzzy_controller.generate_actions.assert_called_once_with(1.0, 0.0, 0.5)

    async def test_generate_plan_with_complex_nested_data(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test plan generation with complex nested data structures."""
        payload = {
            "analysis_result": {
                "overall_health_score": 0.75,
                "requires_intervention": True,
                "anomalies": [{"type": "spike", "metric": "cpu"}, {"type": "trend", "metric": "memory"}],
                "trends": {"cpu": "increasing", "memory": "stable"},
            },
            "current_state": {
                "cpu_usage": 85.0,
                "memory_usage": 60.0,
                "services": {"api": "healthy", "db": "degraded"},
            },
            "operational_goals": {
                "performance_priority": 0.8,
                "cost_efficiency": 0.2,
                "constraints": ["max_cost_100", "min_latency_50ms"],
            },
        }

        response = await client.post("/generate_plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "plan_id" in data
        assert len(data["actions"]) >= 2  # Both fuzzy and RL

    async def test_generate_plan_details_format(self, client, mock_fuzzy_controller, mock_rl_agent):
        """Test that plan_details is properly formatted."""
        payload = create_plan_request(requires_intervention=True)
        response = await client.post("/generate_plan", json=payload)

        data = response.json()
        plan_details = data["plan_details"]

        # Should include both fuzzy and RL mentions
        assert "Fuzzy controller" in plan_details
        assert "RL agent" in plan_details
        # Should be stripped (no trailing spaces)
        assert plan_details == plan_details.strip()
