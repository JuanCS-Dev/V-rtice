"""Unit tests for Web Attack Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint with component availability
- Burp Suite scan (success/not configured)
- OWASP ZAP scan (success/not configured)
- AI payload generation (success/not available)
- Request validation (Pydantic models)
- Edge cases and error handling

Note: AICoPilot, BurpSuiteWrapper, and ZAPWrapper are mocked in tests to isolate
API logic (test infrastructure mocking, not production code).
"""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Mock external dependencies before importing
sys.modules["zapv2"] = Mock()
sys.modules["google"] = Mock()
sys.modules["google.generativeai"] = Mock()
sys.modules["anthropic"] = Mock()

# Import the FastAPI app
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/web_attack_service")
from api import app
from models import *

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_ai_copilot():
    """Mock AICoPilot for testing."""
    with patch("api.ai_copilot") as mock_ai:
        mock_ai.generate_attack_vectors = AsyncMock(
            return_value={
                "analysis": "Test analysis",
                "attack_vectors": [],
                "recommendations": ["Test recommendation"],
                "provider_used": "gemini",
                "tokens_used": 100,
                "confidence": 0.95,
                "timestamp": datetime.now(),
            }
        )
        yield mock_ai


@pytest_asyncio.fixture
async def mock_burp_wrapper():
    """Mock BurpSuiteWrapper for testing."""
    with patch("api.burp_wrapper") as mock_burp:
        mock_burp.scan = AsyncMock(
            return_value={
                "scan_id": "burp-001",
                "target_url": "http://target.com",
                "scan_type": "active",
                "vulnerabilities_found": 5,
                "findings": [],
                "requests_made": 150,
                "pages_crawled": 20,
                "scan_duration": 120.5,
                "timestamp": datetime.now(),
            }
        )
        yield mock_burp


@pytest_asyncio.fixture
async def mock_zap_wrapper():
    """Mock ZAPWrapper for testing."""
    with patch("api.zap_wrapper") as mock_zap:
        mock_zap.scan = AsyncMock(
            return_value={
                "scan_id": "zap-001",
                "target_url": "http://target.com",
                "scan_type": "active",
                "alerts_count": 3,
                "alerts": [],
                "urls_found": 50,
                "scan_duration": 90.0,
                "timestamp": datetime.now(),
            }
        )
        yield mock_zap


def create_burp_scan_request(target_url="http://target.com", scan_type="active"):
    """Helper to create BurpScanRequest payload."""
    return {
        "target_url": target_url,
        "config": {
            "scan_type": scan_type,
            "crawl_depth": 3,
            "max_crawl_time": 600,
            "audit_checks": ["sql_injection", "cross_site_scripting"],
            "thread_count": 10,
            "throttle_ms": 0,
        },
        "enable_ai_copilot": True,
        "ai_provider": "auto",
    }


def create_zap_scan_request(target_url="http://target.com", scan_type="active"):
    """Helper to create ZAPScanRequest payload."""
    return {
        "target_url": target_url,
        "scan_type": scan_type,
        "policy": {"policy_name": "API-Security", "attack_strength": "MEDIUM", "alert_threshold": "MEDIUM"},
        "context_name": "default",
        "max_children": 0,
        "recurse": True,
        "subtree_only": False,
    }


def create_ai_copilot_request():
    """Helper to create AICoPilotRequest payload."""
    return {
        "vulnerability_context": {"url": "http://target.com/api/users"},
        "request_structure": {"method": "POST", "params": ["id", "name"]},
        "attack_type": "sql_injection",
        "provider": "auto",
        "temperature": 0.7,
        "max_tokens": 1000,
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
        assert data["service"] == "web_application_attack"
        assert "timestamp" in data

    async def test_health_check_includes_component_status(self, client):
        """Test health endpoint includes component availability."""
        response = await client.get("/health")

        data = response.json()
        assert "ai_copilot" in data
        assert "burp_suite" in data
        assert "zap" in data
        # Booleans indicating if components are initialized
        assert isinstance(data["ai_copilot"], bool)
        assert isinstance(data["burp_suite"], bool)
        assert isinstance(data["zap"], bool)

    async def test_health_check_timestamp_format(self, client):
        """Test that health check includes valid ISO timestamp."""
        response = await client.get("/health")

        data = response.json()
        assert "timestamp" in data
        # Verify ISO format
        datetime.fromisoformat(data["timestamp"])


# ==================== BURP SUITE SCAN TESTS ====================


@pytest.mark.asyncio
class TestBurpScanEndpoint:
    """Test Burp Suite scan endpoint."""

    async def test_burp_scan_success(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test successful Burp Suite scan."""
        # Ensure burp_wrapper is available
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = create_burp_scan_request()
            response = await client.post("/api/v1/scan/burp", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["scan_id"] == "burp-001"
            assert data["target_url"] == "http://target.com"
            assert data["vulnerabilities_found"] == 5

            # Verify wrapper was called
            mock_burp_wrapper.scan.assert_called_once()

    async def test_burp_scan_not_configured(self, client):
        """Test Burp scan when wrapper is not configured."""
        # Ensure burp_wrapper is None
        with patch("api.burp_wrapper", None):
            payload = create_burp_scan_request()
            response = await client.post("/api/v1/scan/burp", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "not configured" in data["detail"].lower()

    async def test_burp_scan_with_authentication(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test Burp scan with authentication credentials."""
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = create_burp_scan_request()
            payload["auth_type"] = "basic"
            payload["auth_credentials"] = {"username": "admin", "password": "secret"}

            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200

    async def test_burp_scan_with_custom_config(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test Burp scan with custom configuration."""
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = create_burp_scan_request()
            payload["config"]["crawl_depth"] = 5
            payload["config"]["thread_count"] = 20

            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200

    async def test_burp_scan_ai_copilot_integration(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test Burp scan with AI copilot enabled."""
        with patch("api.burp_wrapper", mock_burp_wrapper), patch("api.ai_copilot", mock_ai_copilot):
            payload = create_burp_scan_request()
            payload["enable_ai_copilot"] = True

            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200
            # AI copilot should be passed to scan method
            call_args = mock_burp_wrapper.scan.call_args
            assert call_args[0][1] == mock_ai_copilot


# ==================== ZAP SCAN TESTS ====================


@pytest.mark.asyncio
class TestZAPScanEndpoint:
    """Test OWASP ZAP scan endpoint."""

    async def test_zap_scan_success(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test successful ZAP scan."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request()
            response = await client.post("/api/v1/scan/zap", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["scan_id"] == "zap-001"
            assert data["target_url"] == "http://target.com"
            assert data["alerts_count"] == 3

            # Verify wrapper was called
            mock_zap_wrapper.scan.assert_called_once()

    async def test_zap_scan_not_configured(self, client):
        """Test ZAP scan when wrapper is not configured."""
        with patch("api.zap_wrapper", None):
            payload = create_zap_scan_request()
            response = await client.post("/api/v1/scan/zap", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "not configured" in data["detail"].lower()

    async def test_zap_scan_with_policy(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with custom policy."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request()
            payload["policy"]["attack_strength"] = "HIGH"
            payload["policy"]["alert_threshold"] = "LOW"

            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200

    async def test_zap_scan_with_context(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with context configuration."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request()
            payload["context_name"] = "custom_context"
            payload["include_in_context"] = ["http://target.com/api/*"]
            payload["exclude_from_context"] = ["http://target.com/admin/*"]

            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200

    async def test_zap_scan_with_authentication(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with authentication."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request()
            payload["auth_method"] = "form"
            payload["login_url"] = "http://target.com/login"
            payload["username"] = "testuser"
            payload["password"] = "testpass"

            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200

    async def test_zap_scan_passive_mode(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan in passive mode."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request(scan_type="passive")
            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200


# ==================== AI PAYLOAD GENERATION TESTS ====================


@pytest.mark.asyncio
class TestAIPayloadGenerationEndpoint:
    """Test AI payload generation endpoint."""

    async def test_generate_payloads_success(self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper):
        """Test successful AI payload generation."""
        with patch("api.ai_copilot", mock_ai_copilot):
            payload = create_ai_copilot_request()
            response = await client.post("/api/v1/ai/generate-payloads", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["analysis"] == "Test analysis"
            assert "attack_vectors" in data
            assert "recommendations" in data

            # Verify AI copilot was called
            mock_ai_copilot.generate_attack_vectors.assert_called_once()

    async def test_generate_payloads_not_available(self, client):
        """Test AI payload generation when copilot not available."""
        with patch("api.ai_copilot", None):
            payload = create_ai_copilot_request()
            response = await client.post("/api/v1/ai/generate-payloads", json=payload)

            assert response.status_code == 500
            data = response.json()
            assert "not available" in data["detail"].lower()

    async def test_generate_payloads_different_attack_types(
        self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper
    ):
        """Test payload generation for different attack types."""
        attack_types = ["sql_injection", "cross_site_scripting", "command_injection", "server_side_request_forgery"]

        with patch("api.ai_copilot", mock_ai_copilot):
            for attack_type in attack_types:
                payload = create_ai_copilot_request()
                payload["attack_type"] = attack_type

                response = await client.post("/api/v1/ai/generate-payloads", json=payload)
                assert response.status_code == 200

    async def test_generate_payloads_with_temperature(
        self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper
    ):
        """Test payload generation with different temperature settings."""
        with patch("api.ai_copilot", mock_ai_copilot):
            payload = create_ai_copilot_request()
            payload["temperature"] = 0.9

            response = await client.post("/api/v1/ai/generate-payloads", json=payload)
            assert response.status_code == 200

    async def test_generate_payloads_with_max_tokens(
        self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper
    ):
        """Test payload generation with max tokens limit."""
        with patch("api.ai_copilot", mock_ai_copilot):
            payload = create_ai_copilot_request()
            payload["max_tokens"] = 2000

            response = await client.post("/api/v1/ai/generate-payloads", json=payload)
            assert response.status_code == 200


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_burp_scan_missing_target_url_returns_422(self, client, mock_burp_wrapper):
        """Test Burp scan without target_url."""
        payload = {"config": {}}  # Missing target_url

        response = await client.post("/api/v1/scan/burp", json=payload)
        assert response.status_code == 422

    async def test_zap_scan_missing_target_url_returns_422(self, client, mock_zap_wrapper):
        """Test ZAP scan without target_url."""
        payload = {"scan_type": "active"}  # Missing target_url

        response = await client.post("/api/v1/scan/zap", json=payload)
        assert response.status_code == 422

    async def test_ai_copilot_missing_vulnerability_context_returns_422(self, client, mock_ai_copilot):
        """Test AI copilot without vulnerability_context."""
        payload = {
            "request_structure": {},
            "attack_type": "sql_injection",
            # Missing vulnerability_context
        }

        response = await client.post("/api/v1/ai/generate-payloads", json=payload)
        assert response.status_code == 422

    async def test_ai_copilot_missing_attack_type_returns_422(self, client, mock_ai_copilot):
        """Test AI copilot without attack_type."""
        payload = {
            "vulnerability_context": {},
            "request_structure": {},
            # Missing attack_type
        }

        response = await client.post("/api/v1/ai/generate-payloads", json=payload)
        assert response.status_code == 422

    async def test_burp_scan_invalid_url_returns_422(self, client, mock_burp_wrapper):
        """Test Burp scan with invalid URL format."""
        payload = create_burp_scan_request()
        payload["target_url"] = "not-a-valid-url"

        response = await client.post("/api/v1/scan/burp", json=payload)
        assert response.status_code == 422

    async def test_zap_scan_invalid_url_returns_422(self, client, mock_zap_wrapper):
        """Test ZAP scan with invalid URL format."""
        payload = create_zap_scan_request()
        payload["target_url"] = "invalid://url"

        response = await client.post("/api/v1/scan/zap", json=payload)
        assert response.status_code == 422


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_burp_scan_with_minimal_config(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test Burp scan with minimal configuration."""
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = {"target_url": "http://target.com"}
            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200

    async def test_zap_scan_with_minimal_config(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with minimal configuration."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = {"target_url": "http://target.com"}
            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200

    async def test_burp_scan_different_scan_types(self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper):
        """Test Burp scan with different scan types."""
        scan_types = ["active", "passive", "spider", "ajax_spider"]

        with patch("api.burp_wrapper", mock_burp_wrapper):
            for scan_type in scan_types:
                payload = create_burp_scan_request(scan_type=scan_type)
                response = await client.post("/api/v1/scan/burp", json=payload)
                assert response.status_code == 200

    async def test_zap_scan_different_scan_types(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with different scan types."""
        scan_types = ["active", "passive", "spider", "ajax_spider", "api_scan"]

        with patch("api.zap_wrapper", mock_zap_wrapper):
            for scan_type in scan_types:
                payload = create_zap_scan_request(scan_type=scan_type)
                response = await client.post("/api/v1/scan/zap", json=payload)
                assert response.status_code == 200

    async def test_burp_scan_with_special_characters_in_url(
        self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper
    ):
        """Test Burp scan with special characters in URL."""
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = create_burp_scan_request(target_url="http://example.com/path?param=value&foo=bar")
            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200

    async def test_zap_scan_with_https_url(self, client, mock_zap_wrapper, mock_ai_copilot, mock_burp_wrapper):
        """Test ZAP scan with HTTPS URL."""
        with patch("api.zap_wrapper", mock_zap_wrapper):
            payload = create_zap_scan_request(target_url="https://secure.example.com")
            response = await client.post("/api/v1/scan/zap", json=payload)
            assert response.status_code == 200

    async def test_ai_temperature_boundary_values(self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper):
        """Test AI payload generation with boundary temperature values."""
        with patch("api.ai_copilot", mock_ai_copilot):
            # Min temperature (0.0)
            payload_min = create_ai_copilot_request()
            payload_min["temperature"] = 0.0
            response_min = await client.post("/api/v1/ai/generate-payloads", json=payload_min)
            assert response_min.status_code == 200

            # Max temperature (1.0)
            payload_max = create_ai_copilot_request()
            payload_max["temperature"] = 1.0
            response_max = await client.post("/api/v1/ai/generate-payloads", json=payload_max)
            assert response_max.status_code == 200

    async def test_ai_max_tokens_boundary_values(self, client, mock_ai_copilot, mock_burp_wrapper, mock_zap_wrapper):
        """Test AI payload generation with boundary max_tokens values."""
        with patch("api.ai_copilot", mock_ai_copilot):
            # Min tokens (100)
            payload_min = create_ai_copilot_request()
            payload_min["max_tokens"] = 100
            response_min = await client.post("/api/v1/ai/generate-payloads", json=payload_min)
            assert response_min.status_code == 200

            # Max tokens (4000)
            payload_max = create_ai_copilot_request()
            payload_max["max_tokens"] = 4000
            response_max = await client.post("/api/v1/ai/generate-payloads", json=payload_max)
            assert response_max.status_code == 200

    async def test_burp_scan_with_complex_auth_structure(
        self, client, mock_burp_wrapper, mock_ai_copilot, mock_zap_wrapper
    ):
        """Test Burp scan with complex authentication structure."""
        with patch("api.burp_wrapper", mock_burp_wrapper):
            payload = create_burp_scan_request()
            payload["auth_type"] = "bearer"
            payload["auth_credentials"] = {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
            payload["session_cookies"] = {"PHPSESSID": "abc123", "auth_token": "xyz789"}
            payload["custom_headers"] = {"X-API-Key": "secret", "X-Request-ID": "12345"}

            response = await client.post("/api/v1/scan/burp", json=payload)
            assert response.status_code == 200

    async def test_health_check_components_initialization(self, client):
        """Test health check reflects actual component initialization."""
        response = await client.get("/health")
        data = response.json()

        # Component status should be consistent across multiple calls
        first_status = (data["ai_copilot"], data["burp_suite"], data["zap"])

        response2 = await client.get("/health")
        data2 = response2.json()
        second_status = (data2["ai_copilot"], data2["burp_suite"], data2["zap"])

        assert first_status == second_status  # Status should be consistent
