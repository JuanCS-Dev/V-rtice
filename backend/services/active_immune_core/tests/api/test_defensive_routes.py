"""
Tests for Defensive Tools API Routes.

Validates endpoints, request/response models, and integration with analyzers.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# Test será executado com app real do immune core
pytestmark = pytest.mark.asyncio


class TestBehavioralEndpoints:
    """Test behavioral analyzer endpoints."""
    
    def test_analyze_behavior_event(self, client: TestClient):
        """Test single event analysis."""
        request_data = {
            "entity_id": "user_test123",
            "event_type": "login",
            "metadata": {"ip": "192.168.1.100", "user_agent": "Mozilla/5.0"}
        }
        
        response = client.post("/api/defensive/behavioral/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "is_anomalous" in data
        assert "anomaly_score" in data
        assert "risk_level" in data
        assert "explanation" in data
        assert "entity_id" in data
        assert data["entity_id"] == "user_test123"
    
    def test_analyze_behavior_batch(self, client: TestClient):
        """Test batch event analysis."""
        request_data = {
            "events": [
                {"entity_id": "user1", "event_type": "login", "metadata": {}},
                {"entity_id": "user2", "event_type": "file_access", "metadata": {}},
                {"entity_id": "user3", "event_type": "network", "metadata": {}}
            ]
        }
        
        response = client.post("/api/defensive/behavioral/analyze-batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Validate all results
        for result in data:
            assert "is_anomalous" in result
            assert "anomaly_score" in result
    
    def test_get_baseline_status(self, client: TestClient):
        """Test baseline status endpoint."""
        response = client.get("/api/defensive/behavioral/baseline-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_trained" in data
        assert "training_samples" in data
        assert "feature_count" in data
    
    def test_get_behavioral_metrics(self, client: TestClient):
        """Test metrics endpoint."""
        response = client.get("/api/defensive/behavioral/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_analyzed" in data
        assert "anomalies_detected" in data


class TestTrafficEndpoints:
    """Test traffic analyzer endpoints."""
    
    def test_analyze_traffic_pattern(self, client: TestClient):
        """Test single traffic pattern analysis."""
        request_data = {
            "source_ip": "192.168.1.100",
            "dest_ip": "203.0.113.42",
            "source_port": 54321,
            "dest_port": 443,
            "protocol": "TCP",
            "packet_count": 100,
            "byte_count": 150000,
            "duration_seconds": 5.0,
            "flags": "PSH,ACK"
        }
        
        response = client.post("/api/defensive/traffic/analyze", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "is_threat" in data
        assert "threat_score" in data
        assert "confidence_level" in data
        assert "threat_types" in data
        assert "explanation" in data
        assert data["source_ip"] == "192.168.1.100"
    
    def test_analyze_traffic_batch(self, client: TestClient):
        """Test batch traffic analysis."""
        request_data = {
            "patterns": [
                {
                    "source_ip": "192.168.1.100",
                    "dest_ip": "203.0.113.42",
                    "source_port": 54321,
                    "dest_port": 443,
                    "protocol": "TCP",
                    "packet_count": 100,
                    "byte_count": 150000,
                    "duration_seconds": 5.0,
                    "flags": "PSH,ACK"
                },
                {
                    "source_ip": "192.168.1.101",
                    "dest_ip": "203.0.113.43",
                    "source_port": 12345,
                    "dest_port": 80,
                    "protocol": "TCP",
                    "packet_count": 50,
                    "byte_count": 75000,
                    "duration_seconds": 2.0,
                    "flags": "SYN"
                }
            ]
        }
        
        response = client.post("/api/defensive/traffic/analyze-batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Validate all results
        for result in data:
            assert "is_threat" in result
            assert "threat_score" in result
    
    def test_get_traffic_metrics(self, client: TestClient):
        """Test traffic metrics endpoint."""
        response = client.get("/api/defensive/traffic/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_analyzed" in data
        assert "anomalies_detected" in data


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_defensive_health(self, client: TestClient):
        """Test defensive tools health check."""
        response = client.get("/api/defensive/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "tools" in data
        assert data["status"] == "healthy"


class TestValidation:
    """Test input validation."""
    
    def test_invalid_entity_id(self, client: TestClient):
        """Test validation for invalid entity_id."""
        request_data = {
            "entity_id": "ab",  # Too short
            "event_type": "login",
            "metadata": {}
        }
        
        response = client.post("/api/defensive/behavioral/analyze", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_port(self, client: TestClient):
        """Test validation for invalid port."""
        request_data = {
            "source_ip": "192.168.1.100",
            "dest_ip": "203.0.113.42",
            "source_port": 99999,  # Invalid port
            "dest_port": 443,
            "protocol": "TCP",
            "packet_count": 100,
            "byte_count": 150000
        }
        
        response = client.post("/api/defensive/traffic/analyze", json=request_data)
        
        assert response.status_code == 422  # Validation error


# Fixture para client (será definido no conftest.py do immune core)
@pytest.fixture
def client():
    """Create test client."""
    from api.main import create_app
    app = create_app()
    return TestClient(app)
