"""API routes smoke tests.

These tests validate critical API endpoints with basic happy path scenarios.
Full coverage (90%+) will be achieved incrementally in FASE 2-4 per TDD roadmap.

Author: Vértice Platform Team
License: Proprietary
"""

from fastapi import status


class TestBrowserSessionEndpoints:
    """Test suite for browser session management endpoints."""

    def test_create_session_success(self, client, mock_maba_service):
        """Test creating a browser session returns session ID."""
        response = client.post(
            "/api/v1/sessions", json={"headless": True, "user_agent": "test-agent"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"

    def test_close_session_success(self, client, mock_maba_service):
        """Test closing a browser session."""
        session_id = "test-session-123"

        response = client.delete(f"/api/v1/sessions/{session_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "closed"


class TestNavigationEndpoints:
    """Test suite for navigation endpoints."""

    def test_navigate_success(
        self, client, mock_maba_service, sample_navigation_request
    ):
        """Test navigation to URL returns success."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/navigate?session_id={session_id}", json=sample_navigation_request
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "execution_time_ms" in data
        assert isinstance(data["execution_time_ms"], (int, float))

    def test_navigate_without_session_fails(self, client, sample_navigation_request):
        """Test navigation without session ID fails."""
        response = client.post("/api/v1/navigate", json=sample_navigation_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCognitiveMapEndpoints:
    """Test suite for cognitive map endpoints."""

    def test_query_cognitive_map_find_element(
        self, client, mock_maba_service, sample_cognitive_map_query
    ):
        """Test querying cognitive map for element selector."""
        response = client.post(
            "/api/v1/cognitive-map/query", json=sample_cognitive_map_query
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "found" in data
        assert "result" in data
        assert "confidence" in data


class TestPageAnalysisEndpoints:
    """Test suite for page analysis endpoints."""

    def test_analyze_page_not_implemented(self, client):
        """Test page analysis endpoint returns 501 Not Implemented."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/analyze?session_id={session_id}",
            json={"prompt": "Analyze this page", "response_format": "json"},
        )

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"] == "Not Implemented"
        assert "alternative" in data["detail"]


class TestInteractionEndpoints:
    """Test suite for browser interaction endpoints (click, type)."""

    def test_click_element_success(self, client, mock_maba_service):
        """Test clicking an element on a page."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/click?session_id={session_id}",
            json={
                "selector": "#submit-button",
                "button": "left",
                "click_count": 1,
                "timeout_ms": 30000,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    def test_type_text_success(self, client, mock_maba_service):
        """Test typing text into an element."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/type?session_id={session_id}",
            json={
                "selector": "input[name='username']",
                "text": "test_user",
                "delay_ms": 50,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"


class TestDataExtractionEndpoints:
    """Test suite for data extraction endpoints (screenshot, extract)."""

    def test_screenshot_success(self, client, mock_maba_service):
        """Test taking a screenshot."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/screenshot?session_id={session_id}",
            json={"full_page": True, "format": "png"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    def test_extract_data_success(self, client, mock_maba_service):
        """Test extracting data from page."""
        session_id = "test-session-123"

        response = client.post(
            f"/api/v1/extract?session_id={session_id}",
            json={
                "selectors": {"title": "h1.page-title", "price": "span.price"},
                "extract_all": False,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"


class TestStatsEndpoints:
    """Test suite for stats endpoints."""

    def test_get_stats_success(self, client, mock_maba_service):
        """Test retrieving service statistics."""
        mock_maba_service.get_stats = MagicMock(
            return_value={
                "sessions_active": 2,
                "total_navigations": 150,
                "cognitive_maps_stored": 10,
            }
        )

        response = client.get("/api/v1/stats")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions_active" in data or "message" in data


class TestErrorHandling:
    """Test suite for error handling across all endpoints."""

    def test_navigate_error(self, client, mock_maba_service):
        """Test navigation error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.navigate = AsyncMock(
            side_effect=Exception("Navigation failed")
        )

        response = client.post(
            "/api/v1/navigate?session_id=test", json={"url": "https://example.com"}
        )

        assert response.status_code == 500

    def test_click_error(self, client, mock_maba_service):
        """Test click error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.click = AsyncMock(
            side_effect=Exception("Click failed")
        )

        response = client.post(
            "/api/v1/click?session_id=test", json={"selector": "#btn"}
        )

        assert response.status_code == 500

    def test_type_error(self, client, mock_maba_service):
        """Test type error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.type_text = AsyncMock(
            side_effect=Exception("Type failed")
        )

        response = client.post(
            "/api/v1/type?session_id=test", json={"selector": "input", "text": "test"}
        )

        assert response.status_code == 500

    def test_screenshot_error(self, client, mock_maba_service):
        """Test screenshot error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.screenshot = AsyncMock(
            side_effect=Exception("Screenshot failed")
        )

        response = client.post(
            "/api/v1/screenshot?session_id=test", json={"full_page": True}
        )

        assert response.status_code == 500

    def test_extract_error(self, client, mock_maba_service):
        """Test extract error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.extract_data = AsyncMock(
            side_effect=Exception("Extract failed")
        )

        response = client.post(
            "/api/v1/extract?session_id=test", json={"selectors": {"test": "div"}}
        )

        assert response.status_code == 500

    def test_create_session_error(self, client, mock_maba_service):
        """Test create session error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.create_session = AsyncMock(
            side_effect=Exception("Session creation failed")
        )

        response = client.post("/api/v1/sessions", json={"headless": True})

        assert response.status_code == 500

    def test_close_session_error(self, client, mock_maba_service):
        """Test close session error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.close_session = AsyncMock(
            side_effect=Exception("Close failed")
        )

        response = client.delete("/api/v1/sessions/test")

        assert response.status_code == 500

    def test_cognitive_map_error(self, client, mock_maba_service):
        """Test cognitive map query error handling."""
        from unittest.mock import AsyncMock

        mock_maba_service.cognitive_map.find_element = AsyncMock(
            side_effect=Exception("Query failed")
        )

        response = client.post(
            "/api/v1/cognitive-map/query",
            json={
                "query_type": "find_element",
                "parameters": {"url": "https://example.com", "description": "button"},
            },
        )

        assert response.status_code == 500

    def test_cognitive_map_get_path_success(self, client, mock_maba_service):
        """Test cognitive map get_path query type."""
        from unittest.mock import AsyncMock

        mock_maba_service.cognitive_map.get_navigation_path = AsyncMock(
            return_value=["https://a.com", "https://b.com"]
        )

        response = client.post(
            "/api/v1/cognitive-map/query",
            json={
                "query_type": "get_path",
                "parameters": {"from_url": "https://a.com", "to_url": "https://b.com"},
            },
        )

        assert response.status_code == 200
        assert response.json()["found"] is True

    def test_cognitive_map_get_path_not_found(self, client, mock_maba_service):
        """Test cognitive map get_path when path not found."""
        from unittest.mock import AsyncMock

        mock_maba_service.cognitive_map.get_navigation_path = AsyncMock(
            return_value=None
        )

        response = client.post(
            "/api/v1/cognitive-map/query",
            json={
                "query_type": "get_path",
                "parameters": {"from_url": "https://a.com", "to_url": "https://b.com"},
            },
        )

        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_stats_component_aggregation(self, client, mock_maba_service):
        """Test stats endpoint with component aggregation fallback."""
        from unittest.mock import AsyncMock, MagicMock

        # Remove get_stats to trigger component aggregation
        if hasattr(mock_maba_service, "get_stats"):
            delattr(mock_maba_service, "get_stats")

        mock_maba_service.cognitive_map.get_stats = AsyncMock(
            return_value={"pages": 10}
        )
        mock_maba_service.browser_controller.health_check = AsyncMock(
            return_value={"status": "ok"}
        )
        mock_maba_service.get_uptime_seconds = MagicMock(return_value=3600)

        response = client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert "cognitive_map" in data
        assert "browser" in data

    def test_stats_error(self, client, mock_maba_service):
        """Test stats error handling."""
        from unittest.mock import MagicMock

        mock_maba_service.get_stats = MagicMock(side_effect=Exception("Stats failed"))

        response = client.get("/api/v1/stats")

        assert response.status_code == 500

    def test_create_session_string_return(self, client, mock_maba_service):
        """Test create session when mock returns string (line 80)."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.create_session = AsyncMock(
            return_value="session-id-string"
        )

        response = client.post("/api/v1/sessions", json={"headless": True})

        assert response.status_code == 200
        assert response.json()["session_id"] == "session-id-string"
        assert response.json()["status"] == "created"

    def test_close_session_none_return(self, client, mock_maba_service):
        """Test close session when mock returns None (line 108)."""
        from unittest.mock import AsyncMock

        mock_maba_service.browser_controller.close_session = AsyncMock(
            return_value=None
        )

        response = client.delete("/api/v1/sessions/test-123")

        assert response.status_code == 200
        assert response.json()["status"] == "closed"
        assert "test-123" in response.json()["message"]

    def test_cognitive_map_find_element_not_found(self, client, mock_maba_service):
        """Test cognitive map when element not found (line 320)."""
        from unittest.mock import AsyncMock

        mock_maba_service.cognitive_map.find_element = AsyncMock(return_value=None)

        response = client.post(
            "/api/v1/cognitive-map/query",
            json={
                "query_type": "find_element",
                "parameters": {"url": "https://example.com", "description": "missing"},
            },
        )

        assert response.status_code == 200
        assert response.json()["found"] is False

    def test_cognitive_map_invalid_query_type(self, client, mock_maba_service):
        """Test cognitive map with invalid query type (line 346)."""
        response = client.post(
            "/api/v1/cognitive-map/query",
            json={"query_type": "invalid_type", "parameters": {}},
        )

        assert response.status_code == 500

    def test_stats_async_coroutine(self, client, mock_maba_service):
        """Test stats when get_stats returns coroutine (line 405)."""
        from unittest.mock import MagicMock

        async def async_stats():
            return {"async_stat": "value"}

        mock_maba_service.get_stats = MagicMock(return_value=async_stats())

        response = client.get("/api/v1/stats")

        assert response.status_code == 200


# Import for mock in test
from unittest.mock import MagicMock
