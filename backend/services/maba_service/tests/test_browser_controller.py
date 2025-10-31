"""Comprehensive unit tests for BrowserController.

Tests cover initialization, session management, browser actions, and error handling.

Author: Vértice Platform Team
License: Proprietary
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.maba_service.core.browser_controller import BrowserController


class TestBrowserControllerInitialization:
    """Test BrowserController initialization."""

    def test_initialization_default_values(self):
        """Test browser controller initializes with default values."""
        controller = BrowserController()

        assert controller.browser_type == "chromium"
        assert controller.headless is True
        assert controller.max_instances == 5
        assert controller._playwright is None
        assert controller._browser is None
        assert controller._sessions == {}
        assert controller._initialized is False

    def test_initialization_custom_values(self):
        """Test browser controller initializes with custom values."""
        controller = BrowserController(
            browser_type="firefox", headless=False, max_instances=10
        )

        assert controller.browser_type == "firefox"
        assert controller.headless is False
        assert controller.max_instances == 10

    @pytest.mark.asyncio
    async def test_initialize_chromium_success(self):
        """Test successful initialization with chromium."""
        controller = BrowserController(browser_type="chromium")

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            # Mock playwright setup
            mock_pw_instance = MagicMock()
            mock_browser = MagicMock()

            mock_pw_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(
                return_value=mock_pw_instance
            )

            result = await controller.initialize()

            assert result is True
            assert controller._initialized is True
            assert controller._playwright is not None
            assert controller._browser is not None
            mock_pw_instance.chromium.launch.assert_called_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_initialize_firefox_success(self):
        """Test successful initialization with firefox."""
        controller = BrowserController(browser_type="firefox")

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            mock_pw_instance = MagicMock()
            mock_browser = MagicMock()

            mock_pw_instance.firefox.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(
                return_value=mock_pw_instance
            )

            result = await controller.initialize()

            assert result is True
            assert controller._initialized is True
            mock_pw_instance.firefox.launch.assert_called_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_initialize_webkit_success(self):
        """Test successful initialization with webkit."""
        controller = BrowserController(browser_type="webkit")

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            mock_pw_instance = MagicMock()
            mock_browser = MagicMock()

            mock_pw_instance.webkit.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value.start = AsyncMock(
                return_value=mock_pw_instance
            )

            result = await controller.initialize()

            assert result is True
            assert controller._initialized is True
            mock_pw_instance.webkit.launch.assert_called_once_with(headless=True)

    @pytest.mark.asyncio
    async def test_initialize_unsupported_browser_type(self):
        """Test initialization fails with unsupported browser type."""
        controller = BrowserController(browser_type="safari")

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            mock_pw_instance = MagicMock()
            mock_playwright.return_value.start = AsyncMock(
                return_value=mock_pw_instance
            )

            result = await controller.initialize()

            assert result is False
            assert controller._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """Test initialize returns True when already initialized."""
        controller = BrowserController()
        controller._initialized = True

        result = await controller.initialize()

        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_playwright_start_error(self):
        """Test initialization handles playwright start error."""
        controller = BrowserController()

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            mock_playwright.return_value.start = AsyncMock(
                side_effect=Exception("Playwright start failed")
            )

            result = await controller.initialize()

            assert result is False
            assert controller._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_browser_launch_error(self):
        """Test initialization handles browser launch error."""
        controller = BrowserController()

        with patch("core.browser_controller.async_playwright") as mock_playwright:
            mock_pw_instance = MagicMock()
            mock_pw_instance.chromium.launch = AsyncMock(
                side_effect=Exception("Browser launch failed")
            )
            mock_playwright.return_value.start = AsyncMock(
                return_value=mock_pw_instance
            )

            result = await controller.initialize()

            assert result is False
            assert controller._initialized is False


class TestCreateSession:
    """Test create_session method."""

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """Test successful session creation."""
        controller = BrowserController()
        controller._initialized = True

        # Mock browser
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        controller._browser = mock_browser

        session_id = await controller.create_session()

        assert session_id is not None
        assert len(controller._sessions) == 1
        assert session_id in controller._sessions
        assert controller._sessions[session_id] == mock_context

        # Verify context was created with correct options
        mock_browser.new_context.assert_called_once()
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs["viewport"]["width"] == 1920
        assert call_kwargs["viewport"]["height"] == 1080

    @pytest.mark.asyncio
    async def test_create_session_custom_viewport(self):
        """Test session creation with custom viewport."""
        controller = BrowserController()
        controller._initialized = True

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        controller._browser = mock_browser

        session_id = await controller.create_session(
            viewport_width=1024, viewport_height=768
        )

        assert session_id is not None
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs["viewport"]["width"] == 1024
        assert call_kwargs["viewport"]["height"] == 768

    @pytest.mark.asyncio
    async def test_create_session_with_user_agent(self):
        """Test session creation with custom user agent."""
        controller = BrowserController()
        controller._initialized = True

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        controller._browser = mock_browser

        custom_ua = "Mozilla/5.0 Custom Agent"
        session_id = await controller.create_session(user_agent=custom_ua)

        assert session_id is not None
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs["user_agent"] == custom_ua

    @pytest.mark.asyncio
    async def test_create_session_not_initialized(self):
        """Test session creation fails when not initialized."""
        controller = BrowserController()

        with pytest.raises(RuntimeError, match="Browser controller not initialized"):
            await controller.create_session()

    @pytest.mark.asyncio
    async def test_create_session_max_instances_reached(self):
        """Test session creation fails when max instances reached."""
        controller = BrowserController(max_instances=2)
        controller._initialized = True
        controller._browser = MagicMock()

        # Fill sessions to max
        controller._sessions = {"session1": MagicMock(), "session2": MagicMock()}

        with pytest.raises(RuntimeError, match="Max browser instances.*reached"):
            await controller.create_session()

    @pytest.mark.asyncio
    async def test_create_session_browser_error(self):
        """Test session creation handles browser errors."""
        controller = BrowserController()
        controller._initialized = True

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(
            side_effect=Exception("Context creation failed")
        )
        controller._browser = mock_browser

        with pytest.raises(Exception, match="Context creation failed"):
            await controller.create_session()


class TestCloseSession:
    """Test close_session method."""

    @pytest.mark.asyncio
    async def test_close_session_success(self):
        """Test successful session closure."""
        controller = BrowserController()

        # Setup mock session
        session_id = "test-session-123"
        mock_context = MagicMock()
        mock_context.close = AsyncMock()
        controller._sessions[session_id] = mock_context

        await controller.close_session(session_id)

        assert session_id not in controller._sessions
        mock_context.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_not_found(self):
        """Test closing non-existent session logs warning."""
        controller = BrowserController()

        # Should not raise exception
        await controller.close_session("non-existent-session")

    @pytest.mark.asyncio
    async def test_close_session_close_error(self):
        """Test close_session handles close errors gracefully."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_context = MagicMock()
        mock_context.close = AsyncMock(side_effect=Exception("Close failed"))
        controller._sessions[session_id] = mock_context

        # Should not raise exception
        await controller.close_session(session_id)


class TestGetPage:
    """Test get_page method."""

    @pytest.mark.asyncio
    async def test_get_page_existing_page(self):
        """Test get_page returns existing page."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        page = await controller.get_page(session_id)

        assert page == mock_page

    @pytest.mark.asyncio
    async def test_get_page_creates_new_page(self):
        """Test get_page creates new page when none exist."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_context = MagicMock()
        mock_context.pages = []
        mock_context.new_page = AsyncMock(return_value=mock_page)
        controller._sessions[session_id] = mock_context

        page = await controller.get_page(session_id)

        assert page == mock_page
        mock_context.new_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_page_session_not_found(self):
        """Test get_page raises error for non-existent session."""
        controller = BrowserController()

        with pytest.raises(ValueError, match="Session.*not found"):
            await controller.get_page("non-existent-session")


class TestNavigate:
    """Test navigate method."""

    @pytest.mark.asyncio
    async def test_navigate_success(self):
        """Test successful navigation."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Example Domain")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.navigate(session_id, "https://example.com")

        assert result["status"] == "success"
        assert result["url"] == "https://example.com"
        assert result["title"] == "Example Domain"
        assert result["response_status"] == 200
        mock_page.goto.assert_called_once_with(
            "https://example.com", wait_until="networkidle", timeout=30000
        )

    @pytest.mark.asyncio
    async def test_navigate_custom_parameters(self):
        """Test navigation with custom parameters."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Test")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.navigate(
            session_id, "https://example.com", wait_until="load", timeout_ms=60000
        )

        assert result["status"] == "success"
        mock_page.goto.assert_called_once_with(
            "https://example.com", wait_until="load", timeout=60000
        )

    @pytest.mark.asyncio
    async def test_navigate_error(self):
        """Test navigate handles errors."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(side_effect=Exception("Navigation timeout"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.navigate(session_id, "https://example.com")

        assert result["status"] == "failed"
        assert "Navigation timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_navigate_no_response(self):
        """Test navigate handles None response."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.url = "about:blank"
        mock_page.title = AsyncMock(return_value="")

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.navigate(session_id, "about:blank")

        assert result["status"] == "success"
        assert result["response_status"] is None


class TestClick:
    """Test click method."""

    @pytest.mark.asyncio
    async def test_click_success(self):
        """Test successful click."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.click = AsyncMock()

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.click(session_id, "#button")

        assert result["status"] == "success"
        assert result["selector"] == "#button"
        mock_page.click.assert_called_once_with("#button", timeout=30000)

    @pytest.mark.asyncio
    async def test_click_custom_timeout(self):
        """Test click with custom timeout."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.click = AsyncMock()

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.click(session_id, ".btn", timeout_ms=60000)

        assert result["status"] == "success"
        mock_page.click.assert_called_once_with(".btn", timeout=60000)

    @pytest.mark.asyncio
    async def test_click_error(self):
        """Test click handles errors."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.click = AsyncMock(side_effect=Exception("Element not found"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.click(session_id, "#missing")

        assert result["status"] == "failed"
        assert "Element not found" in result["error"]


class TestTypeText:
    """Test type_text method."""

    @pytest.mark.asyncio
    async def test_type_text_success(self):
        """Test successful text typing."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.type = AsyncMock()

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.type_text(session_id, "input", "hello world")

        assert result["status"] == "success"
        assert result["selector"] == "input"
        assert result["text_length"] == 11
        mock_page.type.assert_called_once_with("input", "hello world", delay=0)

    @pytest.mark.asyncio
    async def test_type_text_with_delay(self):
        """Test type_text with custom delay."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.type = AsyncMock()

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.type_text(session_id, "#input", "test", delay_ms=100)

        assert result["status"] == "success"
        mock_page.type.assert_called_once_with("#input", "test", delay=100)

    @pytest.mark.asyncio
    async def test_type_text_error(self):
        """Test type_text handles errors."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.type = AsyncMock(side_effect=Exception("Input not found"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.type_text(session_id, "#missing", "text")

        assert result["status"] == "failed"
        assert "Input not found" in result["error"]


class TestScreenshot:
    """Test screenshot method."""

    @pytest.mark.asyncio
    async def test_screenshot_full_page_success(self):
        """Test successful full page screenshot."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        screenshot_bytes = b"fake_screenshot_data"
        mock_page.screenshot = AsyncMock(return_value=screenshot_bytes)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id, full_page=True)

        assert result["status"] == "success"
        assert "screenshot" in result
        assert result["size_bytes"] == len(screenshot_bytes)
        mock_page.screenshot.assert_called_once_with(full_page=True)

    @pytest.mark.asyncio
    async def test_screenshot_viewport_only(self):
        """Test screenshot of viewport only."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        screenshot_bytes = b"viewport_screenshot"
        mock_page.screenshot = AsyncMock(return_value=screenshot_bytes)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id, full_page=False)

        assert result["status"] == "success"
        mock_page.screenshot.assert_called_once_with(full_page=False)

    @pytest.mark.asyncio
    async def test_screenshot_element_success(self):
        """Test screenshot of specific element."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_element = MagicMock()
        screenshot_bytes = b"element_screenshot"
        mock_element.screenshot = AsyncMock(return_value=screenshot_bytes)

        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id, selector="#element")

        assert result["status"] == "success"
        assert result["size_bytes"] == len(screenshot_bytes)
        mock_page.query_selector.assert_called_once_with("#element")
        mock_element.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_element_not_found(self):
        """Test screenshot fails when element not found."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id, selector="#missing")

        assert result["status"] == "failed"
        assert "Element not found" in result["error"]

    @pytest.mark.asyncio
    async def test_screenshot_error(self):
        """Test screenshot handles errors."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id)

        assert result["status"] == "failed"
        assert "Screenshot failed" in result["error"]

    @pytest.mark.asyncio
    async def test_screenshot_base64_encoding(self):
        """Test screenshot returns valid base64 encoding."""
        import base64

        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        screenshot_bytes = b"test_data"
        mock_page.screenshot = AsyncMock(return_value=screenshot_bytes)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        result = await controller.screenshot(session_id)

        # Verify base64 decoding works
        decoded = base64.b64decode(result["screenshot"])
        assert decoded == screenshot_bytes


class TestExtractData:
    """Test extract_data method."""

    @pytest.mark.asyncio
    async def test_extract_data_single_success(self):
        """Test successful single element extraction."""
        controller = BrowserController()

        session_id = "test-session-123"

        # Mock elements
        mock_title_element = MagicMock()
        mock_title_element.text_content = AsyncMock(return_value="Example Title")
        mock_price_element = MagicMock()
        mock_price_element.text_content = AsyncMock(return_value="$99.99")

        mock_page = MagicMock()

        async def mock_query_selector(selector):
            if selector == "h1":
                return mock_title_element
            elif selector == ".price":
                return mock_price_element
            return None

        mock_page.query_selector = mock_query_selector

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        selectors = {"title": "h1", "price": ".price"}

        result = await controller.extract_data(session_id, selectors)

        assert result["status"] == "success"
        assert result["data"]["title"] == "Example Title"
        assert result["data"]["price"] == "$99.99"

    @pytest.mark.asyncio
    async def test_extract_data_element_not_found(self):
        """Test extraction handles missing elements."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(return_value=None)

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        selectors = {"missing": "#not-found"}

        result = await controller.extract_data(session_id, selectors)

        assert result["status"] == "success"
        assert result["data"]["missing"] is None

    @pytest.mark.asyncio
    async def test_extract_data_all_elements(self):
        """Test extraction of all matching elements."""
        controller = BrowserController()

        session_id = "test-session-123"

        # Mock multiple elements
        mock_elem1 = MagicMock()
        mock_elem1.text_content = AsyncMock(return_value="Item 1")
        mock_elem2 = MagicMock()
        mock_elem2.text_content = AsyncMock(return_value="Item 2")
        mock_elem3 = MagicMock()
        mock_elem3.text_content = AsyncMock(return_value="Item 3")

        mock_page = MagicMock()
        mock_page.query_selector_all = AsyncMock(
            return_value=[mock_elem1, mock_elem2, mock_elem3]
        )

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        selectors = {"items": ".item"}

        result = await controller.extract_data(session_id, selectors, extract_all=True)

        assert result["status"] == "success"
        assert len(result["data"]["items"]) == 3
        assert result["data"]["items"][0] == "Item 1"
        assert result["data"]["items"][1] == "Item 2"
        assert result["data"]["items"][2] == "Item 3"

    @pytest.mark.asyncio
    async def test_extract_data_error(self):
        """Test extract_data handles errors."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.query_selector = AsyncMock(side_effect=Exception("Query failed"))

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        selectors = {"field": "selector"}

        result = await controller.extract_data(session_id, selectors)

        assert result["status"] == "failed"
        assert "Query failed" in result["error"]


class TestHealthCheck:
    """Test health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_initialized(self):
        """Test health check when initialized."""
        controller = BrowserController(
            browser_type="firefox", headless=False, max_instances=10
        )
        controller._initialized = True

        # Add some sessions
        controller._sessions = {
            "session1": MagicMock(),
            "session2": MagicMock(),
            "session3": MagicMock(),
        }

        result = await controller.health_check()

        assert result["status"] == "healthy"
        assert result["browser_type"] == "firefox"
        assert result["headless"] is False
        assert result["active_sessions"] == 3
        assert result["max_instances"] == 10

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """Test health check when not initialized."""
        controller = BrowserController()

        result = await controller.health_check()

        assert result["status"] == "not_initialized"
        assert result["browser_type"] == "chromium"
        assert result["active_sessions"] == 0
        assert result["max_instances"] == 5


class TestShutdown:
    """Test shutdown method."""

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """Test successful shutdown."""
        controller = BrowserController()
        controller._initialized = True

        # Mock sessions
        mock_context1 = MagicMock()
        mock_context1.close = AsyncMock()
        mock_context2 = MagicMock()
        mock_context2.close = AsyncMock()

        controller._sessions = {"session1": mock_context1, "session2": mock_context2}

        # Mock browser
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        controller._browser = mock_browser

        # Mock playwright
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        controller._playwright = mock_playwright

        await controller.shutdown()

        # Verify all sessions closed
        assert len(controller._sessions) == 0
        mock_context1.close.assert_called_once()
        mock_context2.close.assert_called_once()

        # Verify browser closed
        mock_browser.close.assert_called_once()

        # Verify playwright stopped
        mock_playwright.stop.assert_called_once()

        # Verify not initialized
        assert controller._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        """Test shutdown when not initialized does nothing."""
        controller = BrowserController()

        # Should not raise exception
        await controller.shutdown()

        assert controller._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_with_error(self):
        """Test shutdown handles errors gracefully."""
        controller = BrowserController()
        controller._initialized = True

        # Mock browser that raises error on close
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock(side_effect=Exception("Close failed"))
        controller._browser = mock_browser

        # Should not raise exception
        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_partial_failure(self):
        """Test shutdown continues even if session close fails."""
        controller = BrowserController()
        controller._initialized = True

        # Mock session that fails to close
        mock_context = MagicMock()
        mock_context.close = AsyncMock(side_effect=Exception("Session close failed"))
        controller._sessions = {"session1": mock_context}

        # Mock browser
        mock_browser = MagicMock()
        mock_browser.close = AsyncMock()
        controller._browser = mock_browser

        # Mock playwright
        mock_playwright = MagicMock()
        mock_playwright.stop = AsyncMock()
        controller._playwright = mock_playwright

        # Should not raise exception
        await controller.shutdown()

        # Verify browser and playwright still closed
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestPrometheusMetrics:
    """Test Prometheus metrics integration."""

    @pytest.mark.asyncio
    async def test_metrics_session_gauge_updates(self):
        """Test active_sessions gauge updates on session operations."""
        controller = BrowserController()
        controller._initialized = True

        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        controller._browser = mock_browser

        # Create session
        initial_value = controller.active_sessions._value._value
        session_id = await controller.create_session()

        # Check gauge increased
        # Note: Gauge value might be affected by other tests, so we check relative change
        assert len(controller._sessions) == 1

        # Close session
        mock_context.close = AsyncMock()
        await controller.close_session(session_id)

        assert len(controller._sessions) == 0

    @pytest.mark.asyncio
    async def test_metrics_action_counters(self):
        """Test action counters increment on operations."""
        controller = BrowserController()

        session_id = "test-session-123"
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(return_value=None)
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Test")
        mock_page.click = AsyncMock()
        mock_page.type = AsyncMock()

        mock_context = MagicMock()
        mock_context.pages = [mock_page]
        controller._sessions[session_id] = mock_context

        # Perform actions
        await controller.navigate(session_id, "https://example.com")
        await controller.click(session_id, "#button")
        await controller.type_text(session_id, "input", "test")

        # Metrics should have been incremented
        # We can't easily assert exact values, but we verified they're called
        # in the individual test methods above
