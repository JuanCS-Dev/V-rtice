"""Unit tests for OSINT Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Start investigation (success/different types)
- Get investigation status (found/not found)
- Get investigation report (completed/not completed/not found)
- Request validation
- Edge cases and error handling

Note: AIOrchestrator is mocked in tests to isolate API logic
(test infrastructure mocking, not production code).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the FastAPI app
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/osint_service")
from api import app


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_ai_orchestrator():
    """Mock AIOrchestrator for testing."""
    with patch('api.ai_orchestrator') as mock_orchestrator:
        # Default: start_investigation returns investigation ID
        mock_orchestrator.start_investigation = AsyncMock(return_value={
            "investigation_id": "inv-001",
            "status": "started",
            "query": "test@example.com",
            "investigation_type": "person_recon"
        })

        # Default: get_investigation_status returns status
        mock_orchestrator.get_investigation_status = MagicMock(return_value={
            "investigation_id": "inv-001",
            "status": "in_progress",
            "query": "test@example.com",
            "investigation_type": "person_recon",
            "progress": 50
        })

        yield mock_orchestrator


def create_start_investigation_request(query="test@example.com",
                                       investigation_type="person_recon",
                                       parameters=None):
    """Helper to create StartInvestigationRequest payload."""
    return {
        "query": query,
        "investigation_type": investigation_type,
        "parameters": parameters
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


# ==================== START INVESTIGATION TESTS ====================


@pytest.mark.asyncio
class TestStartInvestigationEndpoint:
    """Test start investigation endpoint."""

    async def test_start_investigation_success(self, client, mock_ai_orchestrator):
        """Test starting investigation successfully."""
        payload = create_start_investigation_request()
        response = await client.post("/start_investigation", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == "inv-001"
        assert data["status"] == "started"
        assert data["query"] == "test@example.com"

        # Verify orchestrator was called
        mock_ai_orchestrator.start_investigation.assert_called_once_with(
            "test@example.com",
            "person_recon",
            None
        )

    async def test_start_investigation_with_parameters(self, client, mock_ai_orchestrator):
        """Test starting investigation with custom parameters."""
        payload = create_start_investigation_request(
            parameters={"depth": "deep", "sources": ["linkedin", "github"]}
        )
        response = await client.post("/start_investigation", json=payload)

        assert response.status_code == 200

        # Verify parameters were passed
        call_args = mock_ai_orchestrator.start_investigation.call_args
        assert call_args[0][2] == {"depth": "deep", "sources": ["linkedin", "github"]}

    async def test_start_investigation_different_types(self, client, mock_ai_orchestrator):
        """Test starting different investigation types."""
        investigation_types = [
            "person_recon",
            "domain_analysis",
            "company_intel",
            "threat_intel"
        ]

        for inv_type in investigation_types:
            payload = create_start_investigation_request(investigation_type=inv_type)
            response = await client.post("/start_investigation", json=payload)
            assert response.status_code == 200

    async def test_start_investigation_different_query_types(self, client, mock_ai_orchestrator):
        """Test starting investigation with different query formats."""
        queries = [
            "test@example.com",           # Email
            "example.com",                # Domain
            "@username",                  # Social handle
            "192.168.1.1",               # IP address
            "John Doe"                    # Name
        ]

        for query in queries:
            payload = create_start_investigation_request(query=query)
            response = await client.post("/start_investigation", json=payload)
            assert response.status_code == 200

    async def test_start_investigation_returns_investigation_id(self, client, mock_ai_orchestrator):
        """Test that investigation ID is returned."""
        mock_ai_orchestrator.start_investigation.return_value = {
            "investigation_id": "inv-unique-12345",
            "status": "started"
        }

        payload = create_start_investigation_request()
        response = await client.post("/start_investigation", json=payload)

        data = response.json()
        assert "investigation_id" in data
        assert data["investigation_id"] == "inv-unique-12345"


# ==================== GET INVESTIGATION STATUS TESTS ====================


@pytest.mark.asyncio
class TestGetInvestigationStatusEndpoint:
    """Test get investigation status endpoint."""

    async def test_get_status_investigation_found(self, client, mock_ai_orchestrator):
        """Test getting status of existing investigation."""
        response = await client.get("/investigation/inv-001/status")

        assert response.status_code == 200
        data = response.json()
        assert data["investigation_id"] == "inv-001"
        assert data["status"] == "in_progress"

        # Verify orchestrator was called
        mock_ai_orchestrator.get_investigation_status.assert_called_once_with("inv-001")

    async def test_get_status_investigation_not_found(self, client, mock_ai_orchestrator):
        """Test getting status of non-existent investigation."""
        mock_ai_orchestrator.get_investigation_status.return_value = None

        response = await client.get("/investigation/inv-999/status")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_status_different_investigation_states(self, client, mock_ai_orchestrator):
        """Test getting status for investigations in different states."""
        states = ["started", "in_progress", "completed", "failed"]

        for state in states:
            mock_ai_orchestrator.get_investigation_status.return_value = {
                "investigation_id": "inv-001",
                "status": state
            }

            response = await client.get("/investigation/inv-001/status")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == state

    async def test_get_status_with_progress_info(self, client, mock_ai_orchestrator):
        """Test getting status includes progress information."""
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "in_progress",
            "progress": 75,
            "current_step": "analyzing_data",
            "steps_completed": 3,
            "total_steps": 4
        }

        response = await client.get("/investigation/inv-001/status")
        data = response.json()
        assert data["progress"] == 75
        assert data["current_step"] == "analyzing_data"

    async def test_get_status_preserves_investigation_id(self, client, mock_ai_orchestrator):
        """Test that investigation ID from URL is preserved."""
        unique_id = "inv-test-12345"
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": unique_id,
            "status": "completed"
        }

        response = await client.get(f"/investigation/{unique_id}/status")
        data = response.json()
        assert data["investigation_id"] == unique_id


# ==================== GET INVESTIGATION REPORT TESTS ====================


@pytest.mark.asyncio
class TestGetInvestigationReportEndpoint:
    """Test get investigation report endpoint."""

    async def test_get_report_completed_investigation(self, client, mock_ai_orchestrator):
        """Test getting report for completed investigation."""
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "completed",
            "results": {
                "summary": "Investigation complete",
                "findings": ["Finding 1", "Finding 2"],
                "risk_score": 7.5
            }
        }

        response = await client.get("/investigation/inv-001/report")

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "findings" in data
        assert data["risk_score"] == 7.5

    async def test_get_report_investigation_not_found(self, client, mock_ai_orchestrator):
        """Test getting report for non-existent investigation."""
        mock_ai_orchestrator.get_investigation_status.return_value = None

        response = await client.get("/investigation/inv-999/report")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_get_report_investigation_not_completed(self, client, mock_ai_orchestrator):
        """Test getting report for investigation that's not completed."""
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "in_progress",
            "results": None
        }

        response = await client.get("/investigation/inv-001/report")

        assert response.status_code == 409
        data = response.json()
        assert "not yet completed" in data["detail"].lower()

    async def test_get_report_different_incomplete_states(self, client, mock_ai_orchestrator):
        """Test getting report for investigations in various incomplete states."""
        incomplete_states = ["started", "in_progress", "failed", "queued"]

        for state in incomplete_states:
            mock_ai_orchestrator.get_investigation_status.return_value = {
                "investigation_id": "inv-001",
                "status": state,
                "results": {}
            }

            response = await client.get("/investigation/inv-001/report")
            assert response.status_code == 409

    async def test_get_report_with_complex_results(self, client, mock_ai_orchestrator):
        """Test getting report with complex nested results."""
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "completed",
            "results": {
                "summary": "Comprehensive investigation",
                "target": {
                    "email": "test@example.com",
                    "name": "John Doe",
                    "aliases": ["johnd", "jdoe"]
                },
                "findings": [
                    {
                        "source": "linkedin",
                        "data": {"job_title": "Engineer", "company": "TechCorp"}
                    },
                    {
                        "source": "github",
                        "data": {"username": "johndoe", "repos": 42}
                    }
                ],
                "risk_assessment": {
                    "overall_risk": "medium",
                    "score": 5.5,
                    "factors": ["public_exposure", "data_leaks"]
                },
                "timestamp": "2024-01-01T12:00:00"
            }
        }

        response = await client.get("/investigation/inv-001/report")
        data = response.json()

        assert data["summary"] == "Comprehensive investigation"
        assert data["target"]["email"] == "test@example.com"
        assert len(data["findings"]) == 2
        assert data["risk_assessment"]["score"] == 5.5


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_start_investigation_missing_query_returns_422(self, client, mock_ai_orchestrator):
        """Test starting investigation without query."""
        payload = {
            "investigation_type": "person_recon"
            # Missing query
        }

        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 422

    async def test_start_investigation_missing_investigation_type_returns_422(self, client, mock_ai_orchestrator):
        """Test starting investigation without investigation_type."""
        payload = {
            "query": "test@example.com"
            # Missing investigation_type
        }

        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 422

    async def test_start_investigation_empty_query(self, client, mock_ai_orchestrator):
        """Test starting investigation with empty query string."""
        payload = create_start_investigation_request(query="")

        # Empty string is valid for Pydantic, but may be rejected by orchestrator
        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 200  # API accepts it

    async def test_start_investigation_empty_investigation_type(self, client, mock_ai_orchestrator):
        """Test starting investigation with empty investigation_type."""
        payload = create_start_investigation_request(investigation_type="")

        # Empty string is valid for Pydantic
        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 200  # API accepts it


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_get_status_special_investigation_ids(self, client, mock_ai_orchestrator):
        """Test getting status with special investigation IDs."""
        special_ids = [
            "inv-with-dashes-123",
            "INV_UPPERCASE",
            "inv.with.dots",
            "inv_underscore",
            "123456789"  # Numeric
        ]

        for inv_id in special_ids:
            mock_ai_orchestrator.get_investigation_status.return_value = {
                "investigation_id": inv_id,
                "status": "completed"
            }

            response = await client.get(f"/investigation/{inv_id}/status")
            assert response.status_code == 200

    async def test_get_report_alphanumeric_investigation_ids(self, client, mock_ai_orchestrator):
        """Test getting report with various alphanumeric investigation IDs."""
        inv_ids = ["inv-123", "inv_test", "INV-UPPER", "inv.dots"]

        for inv_id in inv_ids:
            mock_ai_orchestrator.get_investigation_status.return_value = {
                "investigation_id": inv_id,
                "status": "completed",
                "results": {"summary": "test"}
            }

            response = await client.get(f"/investigation/{inv_id}/report")
            assert response.status_code == 200

    async def test_start_investigation_with_null_parameters(self, client, mock_ai_orchestrator):
        """Test starting investigation with null parameters."""
        payload = create_start_investigation_request(parameters=None)
        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 200

    async def test_start_investigation_with_empty_parameters(self, client, mock_ai_orchestrator):
        """Test starting investigation with empty parameters dict."""
        payload = create_start_investigation_request(parameters={})
        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 200

    async def test_start_investigation_with_complex_parameters(self, client, mock_ai_orchestrator):
        """Test starting investigation with complex nested parameters."""
        payload = create_start_investigation_request(
            parameters={
                "sources": ["linkedin", "github", "twitter"],
                "depth": "deep",
                "options": {
                    "include_related": True,
                    "max_results": 100,
                    "filters": {
                        "date_range": "2020-2024",
                        "categories": ["professional", "social"]
                    }
                },
                "ai_settings": {
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            }
        )

        response = await client.post("/start_investigation", json=payload)
        assert response.status_code == 200

    async def test_get_report_status_exactly_completed(self, client, mock_ai_orchestrator):
        """Test that report only returns for status == 'completed'."""
        # Status "completed" (lowercase)
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "completed",
            "results": {"summary": "test"}
        }
        response = await client.get("/investigation/inv-001/report")
        assert response.status_code == 200

        # Status "Completed" (capitalized) should fail
        mock_ai_orchestrator.get_investigation_status.return_value = {
            "investigation_id": "inv-001",
            "status": "Completed",
            "results": {"summary": "test"}
        }
        response = await client.get("/investigation/inv-001/report")
        assert response.status_code == 409

    async def test_multiple_concurrent_status_checks(self, client, mock_ai_orchestrator):
        """Test multiple concurrent status checks for different investigations."""
        import asyncio

        async def check_status(inv_id):
            mock_ai_orchestrator.get_investigation_status.return_value = {
                "investigation_id": inv_id,
                "status": "in_progress"
            }
            response = await client.get(f"/investigation/{inv_id}/status")
            return response.status_code

        # Check multiple investigations concurrently
        inv_ids = ["inv-001", "inv-002", "inv-003", "inv-004", "inv-005"]
        results = await asyncio.gather(*[check_status(inv_id) for inv_id in inv_ids])

        # All should succeed
        assert all(status == 200 for status in results)

    async def test_start_investigation_preserves_query_format(self, client, mock_ai_orchestrator):
        """Test that query is passed to orchestrator without modification."""
        special_query = "user@domain.com WITH SPECIAL CHARS !@#$%"

        payload = create_start_investigation_request(query=special_query)
        await client.post("/start_investigation", json=payload)

        # Verify exact query was passed
        call_args = mock_ai_orchestrator.start_investigation.call_args
        assert call_args[0][0] == special_query
