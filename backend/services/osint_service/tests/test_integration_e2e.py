"""End-to-end integration tests for OSINT Service with Frontend.

Tests the complete flow:
Frontend → API Gateway → OSINT Service → AIOrchestrator → Response

Validates contract compliance and proper data flow across the stack.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from api import app, ai_orchestrator


@pytest.fixture
def client():
    """Create test client for OSINT service."""
    return TestClient(app)


@pytest.mark.asyncio
class TestOSINTIntegrationE2E:
    """End-to-end integration tests for OSINT service."""

    def test_health_check(self, client):
        """Test service health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_automated_investigation_minimal_data(self, client):
        """Test automated investigation with minimal data (username only)."""
        payload = {
            "username": "test_user_123",
            "email": None,
            "phone": None,
            "name": None,
            "location": None,
            "context": None
        }

        with patch.object(
            ai_orchestrator, 
            'automated_investigation',
            new_callable=AsyncMock
        ) as mock_investigation:
            # Mock the response
            mock_investigation.return_value = {
                "investigation_id": "AUTO-test-123",
                "risk_assessment": {
                    "risk_level": "LOW",
                    "risk_score": 45,
                    "risk_factors": ["Limited online presence"]
                },
                "executive_summary": "Basic OSINT scan completed",
                "patterns_found": [],
                "recommendations": [],
                "data_sources": ["Username Databases"],
                "confidence_score": 67,
                "timestamp": "2025-10-12T20:00:00"
            }

            response = client.post("/api/investigate/auto", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["investigation_id"].startswith("AUTO-")
            assert "risk_assessment" in data["data"]

    def test_automated_investigation_full_data(self, client):
        """Test automated investigation with complete data."""
        payload = {
            "username": "john_doe_2024",
            "email": "john@example.com",
            "phone": "+5562999999999",
            "name": "John Doe",
            "location": "Goiânia, GO",
            "context": "Security investigation"
        }

        with patch.object(
            ai_orchestrator, 
            'automated_investigation',
            new_callable=AsyncMock
        ) as mock_investigation:
            # Mock comprehensive response
            mock_investigation.return_value = {
                "investigation_id": "AUTO-full-456",
                "risk_assessment": {
                    "risk_level": "MEDIUM",
                    "risk_score": 65,
                    "risk_factors": [
                        "Multiple online profiles",
                        "Email exposure",
                        "Phone number discoverable"
                    ]
                },
                "executive_summary": "Comprehensive OSINT investigation completed with 5 data sources analyzed",
                "patterns_found": [
                    {"type": "SOCIAL", "description": "Active on multiple social platforms"},
                    {"type": "DIGITAL", "description": "Significant digital footprint"},
                    {"type": "GEOLOCATION", "description": "Geographic presence in Goiânia, GO"}
                ],
                "recommendations": [
                    {"action": "Continuous Monitoring", "description": "Track online activities"},
                    {"action": "Enhanced Investigation", "description": "Deploy advanced OSINT"}
                ],
                "data_sources": [
                    "Username Databases",
                    "Social Media",
                    "Email Analysis",
                    "Phone Analysis"
                ],
                "confidence_score": 87,
                "timestamp": "2025-10-12T20:00:00",
                "target_identifiers": {
                    "username": "john_doe_2024",
                    "email": "john@example.com",
                    "phone": "+5562999999999",
                    "name": "John Doe",
                    "location": "Goiânia, GO"
                },
                "context": "Security investigation"
            }

            response = client.post("/api/investigate/auto", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            # Validate report structure
            report = data["data"]
            assert "investigation_id" in report
            assert "risk_assessment" in report
            assert "executive_summary" in report
            assert "patterns_found" in report
            assert "recommendations" in report
            assert "data_sources" in report
            assert "confidence_score" in report
            assert "timestamp" in report
            
            # Validate risk assessment structure
            risk = report["risk_assessment"]
            assert "risk_level" in risk
            assert "risk_score" in risk
            assert "risk_factors" in risk
            assert risk["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
            assert 0 <= risk["risk_score"] <= 100

    def test_automated_investigation_no_identifiers(self, client):
        """Test automated investigation with no identifiers (should fail)."""
        payload = {
            "username": None,
            "email": None,
            "phone": None,
            "name": None,
            "location": None,
            "context": None
        }

        response = client.post("/api/investigate/auto", json=payload)
        assert response.status_code == 400
        assert "identifier" in response.json()["detail"].lower()

    def test_automated_investigation_with_image(self, client):
        """Test automated investigation with image URL."""
        payload = {
            "username": None,
            "email": None,
            "phone": None,
            "name": None,
            "image_url": "https://example.com/profile.jpg"
        }

        with patch.object(
            ai_orchestrator, 
            'automated_investigation',
            new_callable=AsyncMock
        ) as mock_investigation:
            mock_investigation.return_value = {
                "investigation_id": "AUTO-img-789",
                "risk_assessment": {
                    "risk_level": "LOW",
                    "risk_score": 40,
                    "risk_factors": ["Image-only investigation"]
                },
                "executive_summary": "Image analysis completed",
                "patterns_found": [],
                "recommendations": [],
                "data_sources": ["Image Analysis"],
                "confidence_score": 55,
                "timestamp": "2025-10-12T20:00:00"
            }

            response = client.post("/api/investigate/auto", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_frontend_contract_compliance(self, client):
        """Test that API response matches frontend expectations.
        
        Frontend expects:
        - response.data.data (nested data object)
        - investigation_id
        - risk_assessment with risk_level, risk_score, risk_factors
        - executive_summary
        - patterns_found (array)
        - recommendations (array)
        - data_sources (array)
        - confidence_score
        - timestamp
        """
        payload = {
            "username": "contract_test",
            "email": None,
            "phone": None,
            "name": None
        }

        with patch.object(
            ai_orchestrator, 
            'automated_investigation',
            new_callable=AsyncMock
        ) as mock_investigation:
            mock_investigation.return_value = {
                "investigation_id": "AUTO-contract-999",
                "risk_assessment": {
                    "risk_level": "LOW",
                    "risk_score": 42,
                    "risk_factors": ["Test factor"]
                },
                "executive_summary": "Contract compliance test",
                "patterns_found": [
                    {"type": "TEST", "description": "Test pattern"}
                ],
                "recommendations": [
                    {"action": "Test action", "description": "Test description"}
                ],
                "data_sources": ["Test Source"],
                "confidence_score": 70,
                "timestamp": "2025-10-12T20:00:00"
            }

            response = client.post("/api/investigate/auto", json=payload)
            
            assert response.status_code == 200
            json_response = response.json()
            
            # Validate top-level structure
            assert "success" in json_response
            assert "data" in json_response
            assert "message" in json_response
            
            # Frontend accesses response.data.data
            report = json_response["data"]
            
            # Validate all required fields for frontend
            required_fields = [
                "investigation_id",
                "risk_assessment",
                "executive_summary",
                "patterns_found",
                "recommendations",
                "data_sources",
                "confidence_score",
                "timestamp"
            ]
            
            for field in required_fields:
                assert field in report, f"Missing required field: {field}"
            
            # Validate risk_assessment structure
            assert "risk_level" in report["risk_assessment"]
            assert "risk_score" in report["risk_assessment"]
            assert "risk_factors" in report["risk_assessment"]
            
            # Validate arrays
            assert isinstance(report["patterns_found"], list)
            assert isinstance(report["recommendations"], list)
            assert isinstance(report["data_sources"], list)
            
            # Validate pattern structure
            if report["patterns_found"]:
                pattern = report["patterns_found"][0]
                assert "type" in pattern
                assert "description" in pattern
            
            # Validate recommendation structure
            if report["recommendations"]:
                rec = report["recommendations"][0]
                assert "action" in rec
                assert "description" in rec


@pytest.mark.asyncio
class TestAIOrchestrator:
    """Direct tests for AIOrchestrator automated_investigation method."""

    async def test_orchestrator_username_investigation(self):
        """Test orchestrator with username only."""
        orchestrator = ai_orchestrator
        
        with patch.object(orchestrator.username_hunter, 'scrape', new_callable=AsyncMock) as mock_hunt:
            mock_hunt.return_value = {"platforms": ["github", "twitter"]}
            
            result = await orchestrator.automated_investigation(username="test_user")
            
            assert "investigation_id" in result
            assert result["investigation_id"].startswith("AUTO-")
            assert "risk_assessment" in result
            assert "confidence_score" in result

    async def test_orchestrator_multi_identifier(self):
        """Test orchestrator with multiple identifiers."""
        orchestrator = ai_orchestrator
        
        result = await orchestrator.automated_investigation(
            username="john_doe",
            email="john@test.com",
            phone="+1234567890"
        )
        
        assert "investigation_id" in result
        assert result["risk_assessment"]["risk_score"] > 50  # Should be higher with multiple identifiers
        assert len(result["data_sources"]) >= 1
