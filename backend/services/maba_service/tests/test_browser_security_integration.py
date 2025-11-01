"""Tests for Browser Controller Security Integration.

Validates that BrowserController correctly enforces SecurityPolicy
and blocks unauthorized navigation attempts.

Biblical Foundation: Proverbs 4:23 - "Guard your heart above all else"

Author: Vértice Platform Team
License: Proprietary
"""

from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from core.browser_controller import BrowserController
from core.security_policy import SecurityPolicy
import pytest
import yaml

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_config_dir():
    """Temporary directory for test configs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def restrictive_whitelist_config(temp_config_dir):
    """Restrictive whitelist configuration."""
    config_path = temp_config_dir / "whitelist.yaml"
    config = {
        "allowed_domains": [
            "*.example.com",
            "google.com",
        ]
    }
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture
def permissive_whitelist_config(temp_config_dir):
    """Permissive whitelist (allow all public)."""
    config_path = temp_config_dir / "permissive.yaml"
    config = {"allowed_domains": ["*"]}
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture
def mock_playwright():
    """Mock Playwright for testing without real browser."""
    with patch("core.browser_controller.async_playwright") as mock:
        playwright_instance = AsyncMock()
        browser_instance = AsyncMock()
        context_instance = AsyncMock()
        page_instance = AsyncMock()

        # Setup mock chain
        mock.return_value.start = AsyncMock(return_value=playwright_instance)
        playwright_instance.chromium.launch = AsyncMock(return_value=browser_instance)
        browser_instance.new_context = AsyncMock(return_value=context_instance)
        context_instance.new_page = AsyncMock(return_value=page_instance)
        context_instance.pages = []
        context_instance.close = AsyncMock()

        # Mock page methods
        page_instance.goto = AsyncMock(return_value=MagicMock(status=200))
        page_instance.title = AsyncMock(return_value="Test Page")
        page_instance.url = "https://api.example.com/"

        yield {
            "playwright": playwright_instance,
            "browser": browser_instance,
            "context": context_instance,
            "page": page_instance,
        }


# ============================================================================
# TESTS: Initialization with Security Policy
# ============================================================================


class TestInitializationWithSecurity:
    """Test BrowserController initialization with SecurityPolicy."""

    def test_init_with_custom_security_policy(self, restrictive_whitelist_config):
        """
        GIVEN: Custom SecurityPolicy instance
        WHEN: BrowserController initialized with security_policy parameter
        THEN: Uses provided SecurityPolicy
        """
        policy = SecurityPolicy(whitelist_path=restrictive_whitelist_config)
        controller = BrowserController(security_policy=policy)

        assert controller.security_policy is policy
        assert len(controller.security_policy.whitelist) == 2

    def test_init_with_whitelist_path(self, restrictive_whitelist_config):
        """
        GIVEN: Path to whitelist config
        WHEN: BrowserController initialized with whitelist_path parameter
        THEN: Creates SecurityPolicy with provided path
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)

        assert controller.security_policy is not None
        assert len(controller.security_policy.whitelist) == 2
        assert "*.example.com" in controller.security_policy.whitelist

    def test_init_without_security_params_uses_default(self):
        """
        GIVEN: No security parameters provided
        WHEN: BrowserController initialized
        THEN: Creates default SecurityPolicy (permissive mode)
        """
        controller = BrowserController()

        assert controller.security_policy is not None
        # Default should be permissive (no config file exists)
        assert "*" in controller.security_policy.whitelist


# ============================================================================
# TESTS: Navigate with Security Enforcement
# ============================================================================


class TestNavigateWithSecurity:
    """Test navigate() method with SecurityPolicy enforcement."""

    @pytest.mark.asyncio
    async def test_navigate_allowed_domain(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: URL in whitelist
        WHEN: navigate() is called
        THEN: Navigation proceeds, returns success
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        # Create session
        session_id = await controller.create_session()

        # Navigate to allowed domain
        result = await controller.navigate(session_id, "https://api.example.com/")

        assert result["status"] == "success"
        assert "blocked" not in result["status"]
        assert "error" not in result or "Security policy" not in result.get("error", "")

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_navigate_blocked_private_network(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: URL with private network IP (security critical)
        WHEN: navigate() is called
        THEN: Navigation blocked BEFORE any network activity
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        # Try to navigate to private network
        result = await controller.navigate(session_id, "http://192.168.1.1/admin")

        assert result["status"] == "blocked"
        assert "Security policy violation" in result["error"]
        assert "blacklisted" in result["error"].lower()

        # Verify page.goto was NEVER called (security blocked it first)
        mock_page = mock_playwright["page"]
        mock_page.goto.assert_not_called()

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_navigate_blocked_localhost(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: URL with localhost (security critical)
        WHEN: navigate() is called
        THEN: Navigation blocked
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        result = await controller.navigate(session_id, "http://localhost:8080/")

        assert result["status"] == "blocked"
        assert "blacklisted" in result["error"].lower()

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_navigate_blocked_non_whitelisted_public(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: Public domain NOT in whitelist
        WHEN: navigate() is called
        THEN: Navigation blocked
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        result = await controller.navigate(session_id, "https://evil-site.com/")

        assert result["status"] == "blocked"
        assert "not in whitelist" in result["error"].lower()

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_navigate_permissive_mode_allows_public(
        self, permissive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: Permissive whitelist (allow all public)
        WHEN: navigate() is called for public domain
        THEN: Navigation allowed
        """
        controller = BrowserController(whitelist_path=permissive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        result = await controller.navigate(session_id, "https://any-site.com/")

        assert result["status"] == "success"

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_navigate_permissive_mode_blocks_private(
        self, permissive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: Permissive whitelist (allow all public)
        WHEN: navigate() is called for private network
        THEN: Navigation blocked (blacklist takes precedence)
        """
        controller = BrowserController(whitelist_path=permissive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        result = await controller.navigate(session_id, "http://10.0.0.1/")

        assert result["status"] == "blocked"
        assert "blacklisted" in result["error"].lower()

        await controller.shutdown()


# ============================================================================
# TESTS: Multiple Navigation Attempts
# ============================================================================


class TestMultipleNavigationAttempts:
    """Test multiple navigation attempts with mixed allowed/blocked."""

    @pytest.mark.asyncio
    async def test_mixed_navigation_attempts(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: Multiple URLs (some allowed, some blocked)
        WHEN: Multiple navigate() calls made
        THEN: Each correctly allowed or blocked
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        # Test allowed
        result1 = await controller.navigate(session_id, "https://api.example.com/")
        assert result1["status"] == "success"

        # Test blocked - private network
        result2 = await controller.navigate(session_id, "http://192.168.1.1/")
        assert result2["status"] == "blocked"

        # Test blocked - non-whitelisted
        result3 = await controller.navigate(session_id, "https://bad-site.com/")
        assert result3["status"] == "blocked"

        # Test allowed - exact match
        result4 = await controller.navigate(session_id, "https://google.com/")
        assert result4["status"] == "success"

        await controller.shutdown()


# ============================================================================
# TESTS: Metrics and Logging
# ============================================================================


class TestMetricsAndLogging:
    """Test that blocked navigation updates metrics correctly."""

    @pytest.mark.asyncio
    async def test_blocked_navigation_updates_metrics(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: Navigation blocked by security policy
        WHEN: navigate() returns blocked status
        THEN: Prometheus metrics updated with status="blocked"
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        # Mock the metrics counter
        with patch.object(controller.actions_total, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            result = await controller.navigate(session_id, "http://localhost/")

            assert result["status"] == "blocked"

            # Verify metrics called with status="blocked"
            mock_labels.assert_called_once_with(
                action_type="navigate", status="blocked"
            )
            mock_counter.inc.assert_called_once()

        await controller.shutdown()

    @pytest.mark.asyncio
    async def test_blocked_navigation_logs_warning(
        self, restrictive_whitelist_config, mock_playwright, caplog
    ):
        """
        GIVEN: Navigation blocked by security policy
        WHEN: navigate() is called
        THEN: Warning logged with blocked URL and reason
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)
        await controller.initialize()

        session_id = await controller.create_session()

        with caplog.at_level("WARNING"):
            result = await controller.navigate(session_id, "http://192.168.1.1/")

            assert result["status"] == "blocked"
            # Check log contains blocked message
            assert any(
                "Blocked navigation" in record.message for record in caplog.records
            )

        await controller.shutdown()


# ============================================================================
# INTEGRATION TEST: Full Security Workflow
# ============================================================================


class TestFullSecurityWorkflow:
    """Test complete browser security workflow."""

    @pytest.mark.asyncio
    async def test_full_browser_security_workflow(
        self, restrictive_whitelist_config, mock_playwright
    ):
        """
        GIVEN: BrowserController with SecurityPolicy
        WHEN: Multiple operations performed
        THEN: Security enforced throughout session lifecycle
        """
        controller = BrowserController(whitelist_path=restrictive_whitelist_config)

        # Step 1: Initialize
        success = await controller.initialize()
        assert success is True

        # Step 2: Create session
        session_id = await controller.create_session()
        assert session_id is not None

        # Step 3: Navigate to allowed domain
        result1 = await controller.navigate(session_id, "https://api.example.com/data")
        assert result1["status"] == "success"

        # Step 4: Try to navigate to private network (should be blocked)
        result2 = await controller.navigate(session_id, "http://10.0.0.1/admin")
        assert result2["status"] == "blocked"
        assert "blacklisted" in result2["error"].lower()

        # Step 5: Try to navigate to non-whitelisted domain (should be blocked)
        result3 = await controller.navigate(
            session_id, "https://unauthorized-site.com/"
        )
        assert result3["status"] == "blocked"
        assert "not in whitelist" in result3["error"].lower()

        # Step 6: Navigate to another allowed domain
        result4 = await controller.navigate(session_id, "https://google.com/search")
        assert result4["status"] == "success"

        # Step 7: Close session
        await controller.close_session(session_id)

        # Step 8: Shutdown
        await controller.shutdown()

        # Verify security policy statistics
        stats = controller.security_policy.get_stats()
        assert stats["whitelist_size"] == 2
        assert stats["permissive_mode"] is False
