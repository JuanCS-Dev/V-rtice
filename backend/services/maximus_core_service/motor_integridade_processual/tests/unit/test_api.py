"""
Unit tests for FastAPI endpoints.

Tests cover:
- Health check
- Frameworks listing
- Action plan evaluation
- Metrics retrieval
- Error handling

Coverage Target: 100%
"""
import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/home/juan/vertice-dev/backend/services/maximus_core_service')

from motor_integridade_processual.api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test suite for health and info endpoints."""
    
    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Motor de Integridade Processual (MIP)"
        assert "version" in data
    
    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["frameworks_loaded"] == 4
        assert "timestamp" in data


class TestFrameworksEndpoint:
    """Test suite for frameworks listing."""
    
    def test_list_frameworks(self, client: TestClient) -> None:
        """Test frameworks endpoint returns all frameworks."""
        response = client.get("/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        
        # Check kantian has veto power
        kantian = next((f for f in data if f["name"] == "kantian"), None)
        assert kantian is not None
        assert kantian["can_veto"] is True
        assert kantian["weight"] == 0.40


class TestEvaluateEndpoint:
    """Test suite for action plan evaluation."""
    
    def test_evaluate_simple_plan(self, client: TestClient) -> None:
        """Test evaluation of simple ethical plan."""
        plan = {
            "action_plan": {
                "objective": "Test ethical evaluation endpoint",
                "steps": [
                    {
                        "description": "Execute test action for validation",
                        "action_type": "observation",
                        "affected_stakeholders": ["test_user"]
                    }
                ],
                "initiator": "test_system",
                "initiator_type": "ai_agent"
            }
        }
        
        response = client.post("/evaluate", json=plan)
        assert response.status_code == 200
        data = response.json()
        
        assert "verdict" in data
        assert "evaluation_time_ms" in data
        assert data["evaluation_time_ms"] > 0
        
        verdict = data["verdict"]
        assert "final_decision" in verdict
        assert "confidence" in verdict
        assert "framework_verdicts" in verdict
        assert len(verdict["framework_verdicts"]) == 4
    
    def test_evaluate_invalid_plan(self, client: TestClient) -> None:
        """Test evaluation with invalid action plan."""
        invalid_plan = {
            "action_plan": {
                "objective": "Short",  # Too short
                "steps": [],  # Empty
                "initiator": "test",
                "initiator_type": "ai_agent"
            }
        }
        
        response = client.post("/evaluate", json=invalid_plan)
        assert response.status_code == 422  # Validation error


class TestMetricsEndpoint:
    """Test suite for metrics endpoint."""
    
    def test_get_metrics_initial(self, client: TestClient) -> None:
        """Test metrics endpoint returns data."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_evaluations" in data
        assert "avg_evaluation_time_ms" in data
        assert "decision_breakdown" in data
    
    def test_metrics_after_evaluation(self, client: TestClient) -> None:
        """Test metrics update after evaluation."""
        # Get initial metrics
        initial_response = client.get("/metrics")
        initial_data = initial_response.json()
        initial_count = initial_data["total_evaluations"]
        
        # Perform evaluation
        plan = {
            "action_plan": {
                "objective": "Test metrics update after evaluation",
                "steps": [
                    {
                        "description": "Execute test action",
                        "action_type": "observation",
                        "affected_stakeholders": ["user"]
                    }
                ],
                "initiator": "test",
                "initiator_type": "ai_agent"
            }
        }
        eval_response = client.post("/evaluate", json=plan)
        assert eval_response.status_code == 200
        
        # Check metrics updated
        updated_response = client.get("/metrics")
        updated_data = updated_response.json()
        assert updated_data["total_evaluations"] == initial_count + 1
        assert len(updated_data["decision_breakdown"]) > 0
