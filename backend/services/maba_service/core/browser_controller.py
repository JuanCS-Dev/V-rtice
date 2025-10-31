"""Browser Controller - Playwright Integration.

This module manages browser instances using Playwright, handling browser lifecycle,
session management, and basic browser automation operations.

Key Features:
- Browser instance pooling
- Session management
- Navigation and interaction
- Screenshot capture
- Resource optimization

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from typing import Any
from uuid import uuid4

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class BrowserController:
    """
    Playwright-based browser controller.

    Manages browser instances, sessions, and provides high-level automation APIs.

    Attributes:
        browser_type: Browser type (chromium, firefox, webkit)
        headless: Whether to run in headless mode
        max_instances: Maximum concurrent browser instances
        _playwright: Playwright instance
        _browser: Browser instance
        _sessions: Active browser sessions
    """

    # Prometheus metrics
    active_sessions = Gauge(
        "maba_active_browser_sessions", "Number of active browser sessions"
    )

    actions_total = Counter(
        "maba_browser_actions_total",
        "Total browser actions performed",
        ["action_type", "status"],
    )

    action_duration = Histogram(
        "maba_browser_action_duration_seconds",
        "Browser action duration",
        ["action_type"],
    )

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        max_instances: int = 5,
    ):
        """
        Initialize browser controller.

        Args:
            browser_type: Browser type (chromium, firefox, webkit)
            headless: Run in headless mode
            max_instances: Max concurrent instances
        """
        self.browser_type = browser_type
        self.headless = headless
        self.max_instances = max_instances

        self._playwright = None
        self._browser: Browser | None = None
        self._sessions: dict[str, BrowserContext] = {}
        self._initialized = False

        logger.info(
            f"Browser controller initialized: {browser_type} "
            f"(headless={headless}, max_instances={max_instances})"
        )

    async def initialize(self) -> bool:
        """
        Initialize Playwright and browser instance.

        Returns:
            True if initialization succeeded, False otherwise
        """
        if self._initialized:
            logger.warning("Browser controller already initialized")
            return True

        try:
            # Start Playwright
            self._playwright = await async_playwright().start()
            logger.debug("✅ Playwright started")

            # Launch browser
            if self.browser_type == "chromium":
                self._browser = await self._playwright.chromium.launch(
                    headless=self.headless
                )
            elif self.browser_type == "firefox":
                self._browser = await self._playwright.firefox.launch(
                    headless=self.headless
                )
            elif self.browser_type == "webkit":
                self._browser = await self._playwright.webkit.launch(
                    headless=self.headless
                )
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")

            logger.info(f"✅ Browser launched: {self.browser_type}")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize browser controller: {e}", exc_info=True)
            return False

    async def shutdown(self) -> None:
        """Shutdown browser controller and close all sessions."""
        if not self._initialized:
            return

        try:
            # Close all sessions
            for session_id in list(self._sessions.keys()):
                await self.close_session(session_id)

            # Close browser
            if self._browser:
                await self._browser.close()
                logger.debug("✅ Browser closed")

            # Stop Playwright
            if self._playwright:
                await self._playwright.stop()
                logger.debug("✅ Playwright stopped")

            self._initialized = False

        except Exception as e:
            logger.error(f"Error shutting down browser controller: {e}")

    async def create_session(
        self,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: str | None = None,
    ) -> str:
        """
        Create a new browser session (context).

        Args:
            viewport_width: Viewport width
            viewport_height: Viewport height
            user_agent: Custom user agent

        Returns:
            Session ID

        Raises:
            RuntimeError: If max instances reached or browser not initialized
        """
        if not self._initialized or not self._browser:
            raise RuntimeError("Browser controller not initialized")

        if len(self._sessions) >= self.max_instances:
            raise RuntimeError(f"Max browser instances ({self.max_instances}) reached")

        try:
            session_id = str(uuid4())

            # Create browser context
            context_options = {
                "viewport": {"width": viewport_width, "height": viewport_height}
            }
            if user_agent:
                context_options["user_agent"] = user_agent

            context = await self._browser.new_context(**context_options)
            self._sessions[session_id] = context

            self.active_sessions.set(len(self._sessions))

            logger.info(f"✅ Browser session created: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            raise

    async def close_session(self, session_id: str) -> None:
        """
        Close a browser session.

        Args:
            session_id: Session ID to close
        """
        if session_id not in self._sessions:
            logger.warning(f"Session {session_id} not found")
            return

        try:
            context = self._sessions[session_id]
            await context.close()
            del self._sessions[session_id]

            self.active_sessions.set(len(self._sessions))

            logger.info(f"✅ Browser session closed: {session_id}")

        except Exception as e:
            logger.error(f"Error closing session {session_id}: {e}")

    async def get_page(self, session_id: str) -> Page:
        """
        Get or create a page for a session.

        Args:
            session_id: Session ID

        Returns:
            Playwright Page object

        Raises:
            ValueError: If session not found
        """
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")

        context = self._sessions[session_id]
        pages = context.pages

        if not pages:
            # Create new page if none exist
            page = await context.new_page()
            logger.debug(f"Created new page for session {session_id}")
            return page

        # Return first page
        return pages[0]

    async def navigate(
        self,
        session_id: str,
        url: str,
        wait_until: str = "networkidle",
        timeout_ms: int = 30000,
    ) -> dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            session_id: Session ID
            url: Target URL
            wait_until: When to consider navigation complete
            timeout_ms: Navigation timeout

        Returns:
            Navigation result dict
        """
        with self.action_duration.labels(action_type="navigate").time():
            try:
                page = await self.get_page(session_id)
                response = await page.goto(
                    url, wait_until=wait_until, timeout=timeout_ms
                )

                self.actions_total.labels(
                    action_type="navigate", status="success"
                ).inc()

                return {
                    "status": "success",
                    "url": page.url,
                    "title": await page.title(),
                    "response_status": response.status if response else None,
                }

            except Exception as e:
                self.actions_total.labels(action_type="navigate", status="failed").inc()
                logger.error(f"Navigation failed: {e}")
                return {"status": "failed", "error": str(e)}

    async def click(
        self, session_id: str, selector: str, timeout_ms: int = 30000
    ) -> dict[str, Any]:
        """
        Click an element.

        Args:
            session_id: Session ID
            selector: CSS selector
            timeout_ms: Timeout

        Returns:
            Click result dict
        """
        with self.action_duration.labels(action_type="click").time():
            try:
                page = await self.get_page(session_id)
                await page.click(selector, timeout=timeout_ms)

                self.actions_total.labels(action_type="click", status="success").inc()

                return {"status": "success", "selector": selector}

            except Exception as e:
                self.actions_total.labels(action_type="click", status="failed").inc()
                logger.error(f"Click failed: {e}")
                return {"status": "failed", "error": str(e)}

    async def type_text(
        self, session_id: str, selector: str, text: str, delay_ms: int = 0
    ) -> dict[str, Any]:
        """
        Type text into an element.

        Args:
            session_id: Session ID
            selector: CSS selector
            text: Text to type
            delay_ms: Delay between keystrokes

        Returns:
            Type result dict
        """
        with self.action_duration.labels(action_type="type").time():
            try:
                page = await self.get_page(session_id)
                await page.type(selector, text, delay=delay_ms)

                self.actions_total.labels(action_type="type", status="success").inc()

                return {
                    "status": "success",
                    "selector": selector,
                    "text_length": len(text),
                }

            except Exception as e:
                self.actions_total.labels(action_type="type", status="failed").inc()
                logger.error(f"Type failed: {e}")
                return {"status": "failed", "error": str(e)}

    async def screenshot(
        self, session_id: str, full_page: bool = False, selector: str | None = None
    ) -> dict[str, Any]:
        """
        Take a screenshot.

        Args:
            session_id: Session ID
            full_page: Capture full scrollable page
            selector: CSS selector for specific element

        Returns:
            Screenshot result with base64 data
        """
        with self.action_duration.labels(action_type="screenshot").time():
            try:
                page = await self.get_page(session_id)

                if selector:
                    element = await page.query_selector(selector)
                    if not element:
                        raise ValueError(f"Element not found: {selector}")
                    screenshot_bytes = await element.screenshot()
                else:
                    screenshot_bytes = await page.screenshot(full_page=full_page)

                self.actions_total.labels(
                    action_type="screenshot", status="success"
                ).inc()

                import base64

                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                return {
                    "status": "success",
                    "screenshot": screenshot_b64,
                    "size_bytes": len(screenshot_bytes),
                }

            except Exception as e:
                self.actions_total.labels(
                    action_type="screenshot", status="failed"
                ).inc()
                logger.error(f"Screenshot failed: {e}")
                return {"status": "failed", "error": str(e)}

    async def extract_data(
        self, session_id: str, selectors: dict[str, str], extract_all: bool = False
    ) -> dict[str, Any]:
        """
        Extract data from page.

        Args:
            session_id: Session ID
            selectors: Map of field names to CSS selectors
            extract_all: Extract all matching elements

        Returns:
            Extracted data dict
        """
        with self.action_duration.labels(action_type="extract").time():
            try:
                page = await self.get_page(session_id)
                extracted_data = {}

                for field_name, selector in selectors.items():
                    if extract_all:
                        elements = await page.query_selector_all(selector)
                        extracted_data[field_name] = [
                            await el.text_content() for el in elements
                        ]
                    else:
                        element = await page.query_selector(selector)
                        if element:
                            extracted_data[field_name] = await element.text_content()
                        else:
                            extracted_data[field_name] = None

                self.actions_total.labels(action_type="extract", status="success").inc()

                return {"status": "success", "data": extracted_data}

            except Exception as e:
                self.actions_total.labels(action_type="extract", status="failed").inc()
                logger.error(f"Extract failed: {e}")
                return {"status": "failed", "error": str(e)}

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health status dict
        """
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "browser_type": self.browser_type,
            "headless": self.headless,
            "active_sessions": len(self._sessions),
            "max_instances": self.max_instances,
        }
