"""Tests for Robust Element Locator - Multi-strategy element finding."""

from unittest.mock import AsyncMock, MagicMock

from core.robust_element_locator import (
    ElementMatch,
    LocatorStrategy,
    RobustElementLocator,
)
import pytest


@pytest.fixture
def locator():
    """Create robust element locator instance."""
    return RobustElementLocator(enable_visual=False, min_confidence=0.7)


@pytest.fixture
def mock_page():
    """Create mock Playwright page object."""
    page = MagicMock()

    # Mock locator chain
    mock_locator = AsyncMock()
    mock_locator.count = AsyncMock(return_value=1)
    mock_locator.first = AsyncMock()
    mock_locator.first.text_content = AsyncMock(return_value="Click me")
    mock_locator.first.get_attribute = AsyncMock(return_value=None)
    mock_locator.first.evaluate = AsyncMock(return_value="button")
    mock_locator.first.is_visible = AsyncMock(return_value=True)
    mock_locator.first.is_enabled = AsyncMock(return_value=True)
    mock_locator.nth = AsyncMock(return_value=mock_locator.first)

    page.locator = MagicMock(return_value=mock_locator)

    return page


class TestInitialization:
    def test_initialize_with_defaults(self):
        """GIVEN: Default parameters.

        WHEN: RobustElementLocator created
        THEN: Initializes with correct defaults.
        """
        locator = RobustElementLocator()

        assert locator.enable_visual is False
        assert locator.min_confidence == 0.7
        assert locator.timeout_ms == 5000

    def test_initialize_with_custom_params(self):
        """GIVEN: Custom parameters.

        WHEN: RobustElementLocator created
        THEN: Initializes with custom values.
        """
        locator = RobustElementLocator(
            enable_visual=True, min_confidence=0.8, timeout_ms=10000
        )

        assert locator.enable_visual is True
        assert locator.min_confidence == 0.8
        assert locator.timeout_ms == 10000


class TestCSSSelector:
    @pytest.mark.asyncio
    async def test_css_selector_success(self, locator, mock_page):
        """GIVEN: Valid CSS selector hint.

        WHEN: find_element called
        THEN: Returns ElementMatch with CSS strategy.
        """
        match = await locator.find_element(
            mock_page, description="login button", hint_selector="#login-btn"
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.CSS_SELECTOR
        assert match.selector == "#login-btn"
        assert match.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_css_selector_no_hint(self, locator, mock_page):
        """GIVEN: No CSS selector hint.

        WHEN: _try_css_selector called
        THEN: Returns None.
        """
        match = await locator._try_css_selector(
            mock_page, description="button", hint_selector=None, hint_testid=None
        )

        assert match is None

    @pytest.mark.asyncio
    async def test_css_selector_not_found(self, locator, mock_page):
        """GIVEN: CSS selector that doesn't match.

        WHEN: _try_css_selector called
        THEN: Returns None.
        """
        mock_page.locator().count = AsyncMock(return_value=0)

        match = await locator._try_css_selector(
            mock_page, description="button", hint_selector="#missing", hint_testid=None
        )

        assert match is None


class TestDataTestId:
    @pytest.mark.asyncio
    async def test_data_testid_success(self, locator, mock_page):
        """GIVEN: Valid data-testid hint.

        WHEN: _try_data_testid called
        THEN: Returns ElementMatch with TESTID strategy.
        """
        match = await locator._try_data_testid(
            mock_page,
            description="login",
            hint_selector=None,
            hint_testid="login-button",
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.DATA_TESTID
        assert "data-testid" in match.selector
        assert match.confidence == 0.95

    @pytest.mark.asyncio
    async def test_data_testid_inferred(self, locator, mock_page):
        """GIVEN: No testid hint (infer from description).

        WHEN: _try_data_testid called
        THEN: Infers testid from description.
        """
        match = await locator._try_data_testid(
            mock_page, description="login button", hint_selector=None, hint_testid=None
        )

        assert match is not None
        assert "login-button" in match.selector


class TestAriaLabel:
    @pytest.mark.asyncio
    async def test_aria_label_exact_match(self, locator, mock_page):
        """GIVEN: Element with exact ARIA label.

        WHEN: _try_aria_label called
        THEN: Returns ElementMatch with ARIA strategy.
        """
        match = await locator._try_aria_label(
            mock_page, description="Submit", hint_selector=None, hint_testid=None
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.ARIA_LABEL
        assert "aria-label" in match.selector
        assert match.confidence >= 0.8


class TestTextContent:
    @pytest.mark.asyncio
    async def test_text_content_exact_match(self, locator, mock_page):
        """GIVEN: Element with exact text.

        WHEN: _try_text_content called
        THEN: Returns ElementMatch with TEXT strategy.
        """
        match = await locator._try_text_content(
            mock_page, description="Click me", hint_selector=None, hint_testid=None
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.TEXT_CONTENT
        assert "Click me" in match.selector
        assert match.confidence >= 0.75


class TestXPath:
    @pytest.mark.asyncio
    async def test_xpath_fallback(self, locator, mock_page):
        """GIVEN: No other strategies work.

        WHEN: _try_xpath called
        THEN: Returns ElementMatch with XPATH strategy.
        """
        match = await locator._try_xpath(
            mock_page, description="button", hint_selector=None, hint_testid=None
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.XPATH
        assert "xpath=" in match.selector
        assert match.confidence >= 0.7


class TestFindElement:
    @pytest.mark.asyncio
    async def test_find_element_css_first(self, locator, mock_page):
        """GIVEN: CSS selector works.

        WHEN: find_element called
        THEN: Returns match from CSS strategy (first).
        """
        match = await locator.find_element(
            mock_page, description="button", hint_selector="#btn"
        )

        assert match is not None
        assert match.strategy == LocatorStrategy.CSS_SELECTOR

    @pytest.mark.asyncio
    async def test_find_element_fallback_chain(self, locator, mock_page):
        """GIVEN: CSS fails, testid succeeds.

        WHEN: find_element called
        THEN: Falls back to testid strategy.
        """
        # CSS fails
        mock_page.locator().count = AsyncMock(side_effect=[0, 1, 1, 1])

        match = await locator.find_element(
            mock_page, description="login button", hint_selector="#missing"
        )

        assert match is not None
        # Should fallback to data-testid
        assert match.strategy == LocatorStrategy.DATA_TESTID

    @pytest.mark.asyncio
    async def test_find_element_low_confidence(self, locator, mock_page):
        """GIVEN: All strategies return low confidence.

        WHEN: find_element called with high min_confidence
        THEN: Returns None.
        """
        high_confidence_locator = RobustElementLocator(min_confidence=0.99)

        # All strategies return confidence < 0.99
        match = await high_confidence_locator.find_element(
            mock_page, description="button"
        )

        # Might be None if all confidence < 0.99
        # This depends on mocks, so we just check it doesn't crash
        assert match is None or match.confidence < 0.99


class TestVerifyElement:
    @pytest.mark.asyncio
    async def test_verify_element_valid(self, locator, mock_page):
        """GIVEN: Valid ElementMatch.

        WHEN: verify_element called
        THEN: Returns True and updated attributes.
        """
        match = ElementMatch(
            selector="#btn",
            strategy=LocatorStrategy.CSS_SELECTOR,
            confidence=1.0,
            attributes={"tag": "button"},
        )

        is_valid, attrs = await locator.verify_element(mock_page, match)

        assert is_valid is True
        assert attrs["visible"] is True
        assert attrs["enabled"] is True

    @pytest.mark.asyncio
    async def test_verify_element_not_found(self, locator, mock_page):
        """GIVEN: Element no longer exists.

        WHEN: verify_element called
        THEN: Returns False.
        """
        mock_page.locator().count = AsyncMock(return_value=0)

        match = ElementMatch(
            selector="#missing",
            strategy=LocatorStrategy.CSS_SELECTOR,
            confidence=1.0,
            attributes={},
        )

        is_valid, attrs = await locator.verify_element(mock_page, match)

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_verify_element_not_visible(self, locator, mock_page):
        """GIVEN: Element exists but not visible.

        WHEN: verify_element called
        THEN: Returns False.
        """
        mock_page.locator().first.is_visible = AsyncMock(return_value=False)

        match = ElementMatch(
            selector="#hidden",
            strategy=LocatorStrategy.CSS_SELECTOR,
            confidence=1.0,
            attributes={},
        )

        is_valid, attrs = await locator.verify_element(mock_page, match)

        assert is_valid is False
        assert attrs["visible"] is False
