"""Tests for MABA Pydantic models and MABAService.

Author: Vértice Platform Team
License: Proprietary
"""

import pytest
from pydantic import ValidationError
from models import (
    BrowserAction,
    BrowserActionRequest,
    BrowserActionResponse,
    BrowserSessionRequest,
    ClickRequest,
    CognitiveMapQueryRequest,
    CognitiveMapQueryResponse,
    ExtractRequest,
    MABAService,
    NavigationRequest,
    PageAnalysisRequest,
    PageAnalysisResponse,
    ScreenshotRequest,
    TypeRequest,
)


class TestNavigationRequest:
    """Test NavigationRequest model validation."""

    def test_valid_navigation_request(self):
        """Test creating valid navigation request."""
        req = NavigationRequest(
            url="https://example.com", wait_until="networkidle", timeout_ms=30000
        )
        assert req.url == "https://example.com"
        assert req.wait_until == "networkidle"
        assert req.timeout_ms == 30000

    def test_invalid_url_validation(self):
        """Test URL validation rejects invalid URLs."""
        with pytest.raises(ValidationError) as exc_info:
            NavigationRequest(url="invalid-url")

        assert "URL must start with http:// or https://" in str(exc_info.value)

    def test_default_values(self):
        """Test default values are applied."""
        req = NavigationRequest(url="https://example.com")
        assert req.wait_until == "networkidle"
        assert req.timeout_ms == 30000


class TestClickRequest:
    """Test ClickRequest model."""

    def test_valid_click_request(self):
        """Test creating valid click request."""
        req = ClickRequest(selector="#button")
        assert req.selector == "#button"
        assert req.button == "left"
        assert req.click_count == 1

    def test_custom_values(self):
        """Test custom values."""
        req = ClickRequest(
            selector=".btn", button="right", click_count=2, timeout_ms=5000
        )
        assert req.button == "right"
        assert req.click_count == 2


class TestTypeRequest:
    """Test TypeRequest model."""

    def test_valid_type_request(self):
        """Test creating valid type request."""
        req = TypeRequest(selector="input", text="hello")
        assert req.selector == "input"
        assert req.text == "hello"
        assert req.delay_ms == 0


class TestScreenshotRequest:
    """Test ScreenshotRequest model."""

    def test_valid_screenshot_request(self):
        """Test creating valid screenshot request."""
        req = ScreenshotRequest(full_page=True)
        assert req.full_page is True
        assert req.format == "png"

    def test_with_selector(self):
        """Test screenshot with specific selector."""
        req = ScreenshotRequest(selector=".content", format="jpeg")
        assert req.selector == ".content"
        assert req.format == "jpeg"


class TestExtractRequest:
    """Test ExtractRequest model."""

    def test_valid_extract_request(self):
        """Test creating valid extract request."""
        req = ExtractRequest(selectors={"title": "h1", "price": ".price"})
        assert "title" in req.selectors
        assert req.extract_all is False


class TestBrowserSessionRequest:
    """Test BrowserSessionRequest model."""

    def test_default_session_request(self):
        """Test default session request values."""
        req = BrowserSessionRequest()
        assert req.headless is True
        assert req.viewport_width == 1920
        assert req.viewport_height == 1080
        assert req.user_agent is None

    def test_custom_session_request(self):
        """Test custom session request."""
        req = BrowserSessionRequest(
            headless=False,
            viewport_width=1024,
            viewport_height=768,
            user_agent="Mozilla/5.0",
        )
        assert req.headless is False
        assert req.viewport_width == 1024


class TestBrowserActionRequest:
    """Test BrowserActionRequest model."""

    def test_valid_action_request(self):
        """Test creating valid action request."""
        req = BrowserActionRequest(
            action=BrowserAction.CLICK, parameters={"selector": "#btn"}
        )
        assert req.action == BrowserAction.CLICK
        assert req.parameters["selector"] == "#btn"


class TestBrowserActionResponse:
    """Test BrowserActionResponse model."""

    def test_valid_action_response(self):
        """Test creating valid action response."""
        resp = BrowserActionResponse(
            status="success", result={"clicked": True}, execution_time_ms=123.45
        )
        assert resp.status == "success"
        assert resp.result["clicked"] is True
        assert resp.execution_time_ms == 123.45
        assert resp.timestamp is not None


class TestCognitiveMapQueryRequest:
    """Test CognitiveMapQueryRequest model."""

    def test_find_element_query(self):
        """Test find_element query request."""
        req = CognitiveMapQueryRequest(
            query_type="find_element",
            parameters={"url": "https://example.com", "description": "login"},
        )
        assert req.query_type == "find_element"
        assert "url" in req.parameters

    def test_get_path_query(self):
        """Test get_path query request."""
        req = CognitiveMapQueryRequest(
            domain="example.com",
            query_type="get_path",
            parameters={"from_url": "https://a.com", "to_url": "https://b.com"},
        )
        assert req.domain == "example.com"
        assert req.query_type == "get_path"


class TestCognitiveMapQueryResponse:
    """Test CognitiveMapQueryResponse model."""

    def test_found_response(self):
        """Test response when element found."""
        resp = CognitiveMapQueryResponse(
            found=True, result={"selector": "#login"}, confidence=0.95
        )
        assert resp.found is True
        assert resp.confidence == 0.95

    def test_not_found_response(self):
        """Test response when element not found."""
        resp = CognitiveMapQueryResponse(found=False, result=None, confidence=0.0)
        assert resp.found is False
        assert resp.result is None


class TestPageAnalysisRequest:
    """Test PageAnalysisRequest model."""

    def test_general_analysis(self):
        """Test general page analysis request."""
        req = PageAnalysisRequest()
        assert req.analysis_type == "general"
        assert req.url is None

    def test_specific_analysis(self):
        """Test specific page analysis."""
        req = PageAnalysisRequest(
            url="https://example.com",
            analysis_type="form",
            instructions="Find all input fields",
        )
        assert req.analysis_type == "form"
        assert req.instructions == "Find all input fields"


class TestPageAnalysisResponse:
    """Test PageAnalysisResponse model."""

    def test_analysis_response(self):
        """Test page analysis response."""
        resp = PageAnalysisResponse(
            analysis="Page contains login form",
            structured_data={"forms": 1},
            recommendations=["Use secure password"],
        )
        assert "login" in resp.analysis
        assert resp.structured_data["forms"] == 1
        assert len(resp.recommendations) == 1


class TestBrowserAction:
    """Test BrowserAction enum."""

    def test_action_values(self):
        """Test all browser action enum values."""
        assert BrowserAction.NAVIGATE == "navigate"
        assert BrowserAction.CLICK == "click"
        assert BrowserAction.TYPE == "type"
        assert BrowserAction.SCROLL == "scroll"
        assert BrowserAction.SCREENSHOT == "screenshot"
        assert BrowserAction.EXTRACT == "extract"
        assert BrowserAction.WAIT == "wait"
        assert BrowserAction.GO_BACK == "go_back"
        assert BrowserAction.GO_FORWARD == "go_forward"
        assert BrowserAction.REFRESH == "refresh"


class TestMABAService:
    """Test MABAService class initialization."""

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test MABA service initialization."""
        service = MABAService(
            service_name="MABA",
            service_version="1.0.0",
            maximus_endpoint="http://localhost:8000",
        )

        assert service.service_name == "MABA"
        assert service.service_version == "1.0.0"
        assert service.browser_controller is None
        assert service.cognitive_map is None

    @pytest.mark.asyncio
    async def test_service_without_endpoint(self):
        """Test service initialization without maximus endpoint."""
        service = MABAService(service_name="MABA", service_version="1.0.0")

        assert service.service_name == "MABA"

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization."""
        from unittest.mock import AsyncMock, MagicMock, patch

        service = MABAService(service_name="MABA", service_version="1.0.0")

        with (
            patch("models.BrowserController") as mock_browser_cls,
            patch("models.CognitiveMapEngine") as mock_map_cls,
        ):

            # Mock BrowserController
            mock_browser = MagicMock()
            mock_browser.initialize = AsyncMock(return_value=None)
            mock_browser_cls.return_value = mock_browser

            # Mock CognitiveMapEngine
            mock_map = MagicMock()
            mock_map.initialize = AsyncMock(return_value=None)
            mock_map_cls.return_value = mock_map

            # Mock register_tools_with_maximus
            service.register_tools_with_maximus = AsyncMock(return_value=None)

            result = await service.initialize()

            assert result is True
            assert service.browser_controller is not None
            assert service.cognitive_map is not None

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """Test service initialization failure."""
        from unittest.mock import patch

        service = MABAService(service_name="MABA", service_version="1.0.0")

        with patch("models.BrowserController") as mock_browser_cls:
            # Mock BrowserController to raise exception
            mock_browser_cls.side_effect = Exception("Browser init failed")

            result = await service.initialize()

            assert result is False

    @pytest.mark.asyncio
    async def test_shutdown_with_components(self):
        """Test service shutdown with components initialized."""
        from unittest.mock import AsyncMock, MagicMock

        service = MABAService(service_name="MABA", service_version="1.0.0")

        # Mock components
        service.browser_controller = MagicMock()
        service.browser_controller.shutdown = AsyncMock(return_value=None)

        service.cognitive_map = MagicMock()
        service.cognitive_map.shutdown = AsyncMock(return_value=None)

        await service.shutdown()

        service.browser_controller.shutdown.assert_called_once()
        service.cognitive_map.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_with_error(self):
        """Test service shutdown with error."""
        from unittest.mock import AsyncMock, MagicMock

        service = MABAService(service_name="MABA", service_version="1.0.0")

        # Mock component that raises exception
        service.browser_controller = MagicMock()
        service.browser_controller.shutdown = AsyncMock(
            side_effect=Exception("Shutdown failed")
        )

        # Should not raise exception
        await service.shutdown()

    @pytest.mark.asyncio
    async def test_health_check_with_components(self):
        """Test health check with components initialized."""
        from unittest.mock import AsyncMock, MagicMock

        service = MABAService(service_name="MABA", service_version="1.0.0")

        # Mock get_base_health_info
        service.get_base_health_info = AsyncMock(
            return_value={"status": "healthy", "service": "MABA"}
        )

        # Mock browser controller
        service.browser_controller = MagicMock()
        service.browser_controller.health_check = AsyncMock(
            return_value={"status": "ok", "instances": 3}
        )

        # Mock cognitive map
        service.cognitive_map = MagicMock()
        service.cognitive_map.health_check = AsyncMock(
            return_value={"status": "ok", "pages": 100}
        )

        health = await service.health_check()

        assert "components" in health
        assert "browser_controller" in health["components"]
        assert "cognitive_map" in health["components"]
        assert health["components"]["browser_controller"]["status"] == "ok"
        assert health["components"]["cognitive_map"]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_check_without_components(self):
        """Test health check without components initialized."""
        from unittest.mock import AsyncMock

        service = MABAService(service_name="MABA", service_version="1.0.0")

        # Mock get_base_health_info
        service.get_base_health_info = AsyncMock(
            return_value={"status": "healthy", "service": "MABA"}
        )

        health = await service.health_check()

        assert "components" in health
        assert health["components"]["browser_controller"]["status"] == "not_initialized"
        assert health["components"]["cognitive_map"]["status"] == "not_initialized"

    def test_get_tool_manifest(self):
        """Test tool manifest generation."""
        service = MABAService(service_name="MABA", service_version="1.0.0")

        tools = service._get_tool_manifest()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check first tool (navigate_url)
        navigate_tool = tools[0]
        assert navigate_tool["name"] == "navigate_url"
        assert navigate_tool["category"] == "browser"
        assert "url" in navigate_tool["parameters"]

        # Check second tool (click_element)
        click_tool = tools[1]
        assert click_tool["name"] == "click_element"
        assert click_tool["category"] == "browser"
        assert "selector" in click_tool["parameters"]
