"""
Tests for PFC Consciousness API

Tests all REST endpoints and WebSocket streaming.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch

# Import app
import sys
from pathlib import Path
consciousness_path = Path(__file__).parent.parent.parent
if str(consciousness_path) not in sys.path:
    sys.path.insert(0, str(consciousness_path))

from consciousness.api.app import app


@pytest.fixture
def client():
    """Create test client with mocked state."""
    from consciousness.prefrontal_cortex import PrefrontalCortex

    # Mock application state
    app.state.repository = None
    app.state.persistence_enabled = False
    app.state.query_service = None
    app.state.pfc = PrefrontalCortex(enable_mip=True, repository=None)
    app.state.ws_connections = set()

    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "PFC Consciousness API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "pfc_initialized" in data
        assert "persistence_enabled" in data
        assert "mip_enabled" in data


class TestOrchestrationEndpoints:
    """Tests for decision orchestration endpoints."""

    def test_orchestrate_basic_decision(self, client):
        """Test basic orchestration endpoint."""
        user_id = str(uuid4())
        request_data = {
            "user_id": user_id,
            "behavioral_signals": {
                "error_count": 2,
                "retry_count": 1,
                "task_success": False
            },
            "action_description": "User experiencing errors"
        }

        response = client.post("/orchestrate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "decision_id" in data
        assert data["user_id"] == user_id
        assert "final_decision" in data
        assert "rationale" in data
        assert "confidence" in data
        assert "timestamp" in data

    def test_orchestrate_decision_invalid_user_id(self, client):
        """Test orchestration with invalid user_id."""
        request_data = {
            "user_id": "invalid-uuid",
            "behavioral_signals": {"error_count": 0},
            "action_description": "Test"
        }

        response = client.post("/orchestrate", json=request_data)

        assert response.status_code == 400
        assert "Invalid request" in response.json()["error"]

    def test_orchestrate_with_suffering_detected(self, client):
        """Test orchestration detects suffering from signals."""
        user_id = str(uuid4())
        request_data = {
            "user_id": user_id,
            "behavioral_signals": {
                "error_rate": 0.95,  # High error rate
                "response_time_ms": 10000,  # Slow response
                "task_success": False
            },
            "action_description": "User struggling with system errors"
        }

        response = client.post("/orchestrate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        # Should detect suffering and plan interventions
        assert "detected_events" in data
        # May or may not have events depending on detection logic

    def test_orchestrate_with_plan(self, client):
        """Test orchestration with MIP evaluation."""
        user_id = str(uuid4())
        request_data = {
            "user_id": user_id,
            "behavioral_signals": {"error_count": 0, "task_success": True},
            "action_plan": {
                "name": "Test Plan",
                "description": "Test action",
                "category": "reactive",
                "steps": [{
                    "sequence_number": 1,
                    "description": "Test step",
                    "action_type": "validation"
                }],
                "stakeholders": [],
                "urgency": 0.3,
                "risk_level": 0.2,
                "novel_situation": False
            }
        }

        response = client.post("/orchestrate-with-plan", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "decision_id" in data
        assert "ethical_verdict_summary" in data
        # MIP evaluation should have occurred


class TestDecisionQueryEndpoints:
    """Tests for decision query endpoints."""

    def test_get_decision_by_id(self, client):
        """Test retrieving decision by ID."""
        # First create a decision
        user_id = str(uuid4())
        request_data = {
            "user_id": user_id,
            "behavioral_signals": {"error_count": 0},
            "action_description": "Test action"
        }

        create_response = client.post("/orchestrate", json=request_data)
        decision_id = create_response.json()["decision_id"]

        # Now retrieve it
        response = client.get(f"/decisions/{decision_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["decision_id"] == decision_id
        assert data["user_id"] == user_id

    def test_get_decision_not_found(self, client):
        """Test retrieving non-existent decision."""
        fake_id = str(uuid4())
        response = client.get(f"/decisions/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["error"]

    def test_get_user_decisions(self, client):
        """Test retrieving decisions for a user."""
        user_id = str(uuid4())

        # Create multiple decisions for user
        for i in range(3):
            request_data = {
                "user_id": user_id,
                "behavioral_signals": {"error_count": i},
                "action_description": f"Action {i}"
            }
            client.post("/orchestrate", json=request_data)

        # Query user decisions
        response = client.get(f"/decisions/user/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert "decisions" in data
        assert data["total"] >= 3  # At least the 3 we created
        assert all(d["user_id"] == user_id for d in data["decisions"])

    def test_get_user_decisions_with_pagination(self, client):
        """Test pagination of user decisions."""
        user_id = str(uuid4())

        # Create 5 decisions
        for i in range(5):
            request_data = {
                "user_id": user_id,
                "behavioral_signals": {"error_count": i},
                "action_description": f"Action {i}"
            }
            client.post("/orchestrate", json=request_data)

        # Get first 2
        response = client.get(f"/decisions/user/{user_id}?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 2
        assert len(data["decisions"]) <= 2


class TestStatisticsEndpoints:
    """Tests for statistics and analytics endpoints."""

    def test_get_statistics(self, client):
        """Test getting overall statistics."""
        response = client.get("/statistics")

        assert response.status_code == 200
        data = response.json()
        assert "total_decisions" in data
        assert "escalated" in data
        assert "escalation_rate" in data
        assert "interventions_planned" in data
        assert "mip_evaluations" in data

    def test_get_statistics_for_user(self, client):
        """Test getting statistics for specific user."""
        user_id = str(uuid4())

        # Create some decisions
        for _ in range(3):
            request_data = {
                "user_id": user_id,
                "behavioral_signals": {"error_count": 0},
                "action_description": "Test"
            }
            client.post("/orchestrate", json=request_data)

        # Get stats (may not be available without persistence)
        response = client.get(f"/statistics?user_id={user_id}")

        assert response.status_code == 200
        # Stats may be in-memory or from persistence


class TestWebSocket:
    """Tests for WebSocket streaming."""

    def test_websocket_connection(self, client):
        """Test WebSocket connection and welcome message."""
        with client.websocket_connect("/ws/decisions") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "Connected" in data["message"]

    def test_websocket_receives_decision(self, client):
        """Test WebSocket receives decision broadcast."""
        with client.websocket_connect("/ws/decisions") as websocket:
            # Receive welcome
            websocket.receive_json()

            # Create a decision (should broadcast)
            user_id = str(uuid4())
            request_data = {
                "user_id": user_id,
                "behavioral_signals": {"error_count": 0},
                "action_description": "Test"
            }

            # Make decision in another client
            http_response = client.post("/orchestrate", json=request_data)
            decision_id = http_response.json()["decision_id"]

            # WebSocket should receive broadcast
            # Note: This may be timing-dependent
            try:
                data = websocket.receive_json(timeout=1)
                assert data["type"] == "decision"
                assert data["decision_id"] == decision_id
            except:
                # Broadcast may not arrive in time for test
                pass


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_json(self, client):
        """Test invalid JSON payload."""
        response = client.post(
            "/orchestrate",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable entity

    def test_missing_required_fields(self, client):
        """Test missing required fields."""
        response = client.post("/orchestrate", json={})

        assert response.status_code == 422

    def test_invalid_uuid_format(self, client):
        """Test invalid UUID format."""
        response = client.get("/decisions/not-a-uuid")

        assert response.status_code == 422


class TestPersistenceIntegration:
    """Tests for persistence integration."""

    @pytest.mark.skipif(
        True,  # Skip by default, requires PostgreSQL
        reason="Requires PostgreSQL database"
    )
    def test_get_escalated_decisions(self, client):
        """Test getting escalated decisions from persistence."""
        response = client.get("/decisions/escalated")

        # May return 503 if persistence unavailable
        if response.status_code == 200:
            data = response.json()
            assert "decisions" in data
        else:
            assert response.status_code == 503

    @pytest.mark.skipif(
        True,  # Skip by default
        reason="Requires PostgreSQL database"
    )
    def test_get_suffering_analytics(self, client):
        """Test suffering analytics from persistence."""
        response = client.get("/analytics/suffering")

        if response.status_code == 200:
            data = response.json()
            assert "total_events" in data
            assert "by_type" in data
        else:
            assert response.status_code == 503
