"""Robust Element Locator - Multi-strategy element finding with fallbacks.

Implements intelligent element location with multiple fallback strategies
to handle dynamic web pages and flaky selectors.

Biblical Foundation:
- Proverbs 24:6: "For by wise guidance you can wage your war,
  and in abundance of counselors there is victory"

Fallback Strategies (in order):
1. Exact CSS selector (fastest, most specific)
2. data-testid attribute (test-friendly)
3. ARIA label (accessibility-based)
4. Text content (semantic matching)
5. XPath (structural fallback)
6. Visual position (AI vision - optional)

Author: Vértice Platform Team
Created: 2025-11-01
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class LocatorStrategy(str, Enum):
    """Element locator strategies."""

    CSS_SELECTOR = "css_selector"
    DATA_TESTID = "data_testid"
    ARIA_LABEL = "aria_label"
    TEXT_CONTENT = "text_content"
    XPATH = "xpath"
    VISUAL_POSITION = "visual_position"


@dataclass
class ElementMatch:
    """Represents a matched element with metadata."""

    selector: str
    strategy: LocatorStrategy
    confidence: float  # 0.0-1.0
    attributes: dict[str, Any]


# Prometheus metrics
element_locator_attempts = Counter(
    "maba_element_locator_attempts_total",
    "Element locator attempts by strategy",
    ["strategy", "success"],
)

element_locator_duration = Histogram(
    "maba_element_locator_duration_seconds",
    "Element locator duration by strategy",
    ["strategy"],
)


class RobustElementLocator:
    """Multi-strategy element locator with intelligent fallbacks.

    Tries multiple strategies to locate elements on dynamic web pages,
    falling back gracefully when primary selectors fail.

    Biblical Principle: Proverbs 24:6 - "In abundance of counselors there is victory"
    """

    def __init__(
        self,
        enable_visual: bool = False,
        min_confidence: float = 0.7,
        timeout_ms: int = 5000,
    ):
        """Initialize robust element locator.

        Args:
            enable_visual: Enable visual position strategy (requires AI)
            min_confidence: Minimum confidence score to accept match (0-1)
            timeout_ms: Timeout per strategy in milliseconds

        """
        self.enable_visual = enable_visual
        self.min_confidence = min_confidence
        self.timeout_ms = timeout_ms

        logger.info(
            f"RobustElementLocator initialized (visual={enable_visual}, min_confidence={min_confidence})"
        )

    async def find_element(
        self,
        page: Any,  # Playwright page object
        description: str,
        hint_selector: str | None = None,
        hint_testid: str | None = None,
    ) -> ElementMatch | None:
        """Find element using multi-strategy approach.

        Tries strategies in order until a match is found with sufficient confidence.

        Args:
            page: Playwright page object
            description: Human description of element (e.g., "login button")
            hint_selector: Optional CSS selector hint
            hint_testid: Optional data-testid hint

        Returns:
            ElementMatch if found, None if no match above min_confidence

        """
        strategies = [
            (LocatorStrategy.CSS_SELECTOR, self._try_css_selector),
            (LocatorStrategy.DATA_TESTID, self._try_data_testid),
            (LocatorStrategy.ARIA_LABEL, self._try_aria_label),
            (LocatorStrategy.TEXT_CONTENT, self._try_text_content),
            (LocatorStrategy.XPATH, self._try_xpath),
        ]

        if self.enable_visual:
            strategies.append((LocatorStrategy.VISUAL_POSITION, self._try_visual))

        for strategy_type, strategy_func in strategies:
            try:
                logger.debug(f"Trying strategy: {strategy_type}")

                match = await strategy_func(
                    page, description, hint_selector, hint_testid
                )

                if match and match.confidence >= self.min_confidence:
                    element_locator_attempts.labels(
                        strategy=strategy_type, success="true"
                    ).inc()
                    logger.info(
                        f"✅ Found element via {strategy_type} (confidence={match.confidence:.2f})"
                    )
                    return match

                element_locator_attempts.labels(
                    strategy=strategy_type, success="false"
                ).inc()

            except Exception as e:
                logger.warning(f"Strategy {strategy_type} failed: {e}")
                element_locator_attempts.labels(
                    strategy=strategy_type, success="error"
                ).inc()

        logger.warning(
            f"❌ No element found for '{description}' with min_confidence={self.min_confidence}"
        )
        return None

    async def _try_css_selector(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by exact CSS selector.

        Args:
            page: Playwright page object
            description: Element description
            hint_selector: CSS selector hint
            hint_testid: Unused for this strategy

        Returns:
            ElementMatch if found, None otherwise

        """
        if not hint_selector:
            return None

        try:
            locator = page.locator(hint_selector)
            count = await locator.count()

            if count == 0:
                return None

            if count > 1:
                logger.debug(
                    f"CSS selector '{hint_selector}' matched {count} elements (taking first)"
                )

            # Get attributes
            element = locator.first
            attrs = {}
            try:
                attrs["tag"] = await element.evaluate("el => el.tagName.toLowerCase()")
                attrs["text"] = (await element.text_content() or "").strip()
            except Exception:
                pass

            return ElementMatch(
                selector=hint_selector,
                strategy=LocatorStrategy.CSS_SELECTOR,
                confidence=1.0 if count == 1 else 0.9,  # Lower if multiple matches
                attributes=attrs,
            )

        except Exception as e:
            logger.debug(f"CSS selector failed: {e}")
            return None

    async def _try_data_testid(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by data-testid attribute.

        Args:
            page: Playwright page object
            description: Element description
            hint_selector: Unused for this strategy
            hint_testid: data-testid hint

        Returns:
            ElementMatch if found, None otherwise

        """
        if not hint_testid:
            # Try to infer testid from description
            # e.g., "login button" -> "login-button"
            hint_testid = description.lower().replace(" ", "-")

        selector = f'[data-testid="{hint_testid}"]'

        try:
            locator = page.locator(selector)
            count = await locator.count()

            if count == 0:
                return None

            element = locator.first
            attrs = {}
            try:
                attrs["tag"] = await element.evaluate("el => el.tagName.toLowerCase()")
                attrs["text"] = (await element.text_content() or "").strip()
                attrs["testid"] = hint_testid
            except Exception:
                pass

            return ElementMatch(
                selector=selector,
                strategy=LocatorStrategy.DATA_TESTID,
                confidence=0.95,  # High confidence for test IDs
                attributes=attrs,
            )

        except Exception as e:
            logger.debug(f"data-testid failed: {e}")
            return None

    async def _try_aria_label(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by ARIA label.

        Args:
            page: Playwright page object
            description: Element description
            hint_selector: Unused for this strategy
            hint_testid: Unused for this strategy

        Returns:
            ElementMatch if found, None otherwise

        """
        # Try exact match first
        selector = f'[aria-label="{description}"]'

        try:
            locator = page.locator(selector)
            count = await locator.count()

            if count > 0:
                element = locator.first
                attrs = {}
                try:
                    attrs["tag"] = await element.evaluate(
                        "el => el.tagName.toLowerCase()"
                    )
                    attrs["text"] = (await element.text_content() or "").strip()
                    attrs["aria_label"] = description
                except Exception:
                    pass

                return ElementMatch(
                    selector=selector,
                    strategy=LocatorStrategy.ARIA_LABEL,
                    confidence=0.9,
                    attributes=attrs,
                )

        except Exception:
            pass

        # Try partial match (contains)
        # Find all elements with aria-label and filter
        try:
            all_aria = page.locator("[aria-label]")
            count = await all_aria.count()

            for i in range(min(count, 20)):  # Limit search
                element = all_aria.nth(i)
                label = await element.get_attribute("aria-label")

                if label and description.lower() in label.lower():
                    attrs = {}
                    try:
                        attrs["tag"] = await element.evaluate(
                            "el => el.tagName.toLowerCase()"
                        )
                        attrs["text"] = (await element.text_content() or "").strip()
                        attrs["aria_label"] = label
                    except Exception:
                        pass

                    # Generate selector
                    partial_selector = f'[aria-label*="{description}"]'

                    return ElementMatch(
                        selector=partial_selector,
                        strategy=LocatorStrategy.ARIA_LABEL,
                        confidence=0.8,  # Lower for partial match
                        attributes=attrs,
                    )

        except Exception as e:
            logger.debug(f"ARIA label failed: {e}")

        return None

    async def _try_text_content(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by text content.

        Args:
            page: Playwright page object
            description: Element description (used as text to find)
            hint_selector: Unused for this strategy
            hint_testid: Unused for this strategy

        Returns:
            ElementMatch if found, None otherwise

        """
        # Try exact text match
        try:
            # Common clickable elements
            for tag in ["button", "a", "span", "div"]:
                selector = f'{tag}:text-is("{description}")'
                locator = page.locator(selector)
                count = await locator.count()

                if count > 0:
                    element = locator.first
                    attrs = {
                        "tag": tag,
                        "text": description,
                    }

                    return ElementMatch(
                        selector=selector,
                        strategy=LocatorStrategy.TEXT_CONTENT,
                        confidence=0.85,
                        attributes=attrs,
                    )

        except Exception:
            pass

        # Try partial text match
        try:
            for tag in ["button", "a", "span", "div"]:
                selector = f'{tag}:has-text("{description}")'
                locator = page.locator(selector)
                count = await locator.count()

                if count > 0:
                    element = locator.first
                    text = (await element.text_content() or "").strip()

                    attrs = {
                        "tag": tag,
                        "text": text,
                    }

                    return ElementMatch(
                        selector=selector,
                        strategy=LocatorStrategy.TEXT_CONTENT,
                        confidence=0.75,  # Lower for partial match
                        attributes=attrs,
                    )

        except Exception as e:
            logger.debug(f"Text content failed: {e}")

        return None

    async def _try_xpath(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by XPath.

        Args:
            page: Playwright page object
            description: Element description
            hint_selector: Unused for this strategy
            hint_testid: Unused for this strategy

        Returns:
            ElementMatch if found, None otherwise

        """
        # Generate XPath based on description
        # Try multiple XPath patterns

        patterns = [
            f"//button[contains(text(), '{description}')]",
            f"//a[contains(text(), '{description}')]",
            f"//*[@title='{description}']",
            f"//*[contains(@class, '{description.lower().replace(' ', '-')}')]",
        ]

        for xpath in patterns:
            try:
                locator = page.locator(f"xpath={xpath}")
                count = await locator.count()

                if count > 0:
                    element = locator.first
                    attrs = {}
                    try:
                        attrs["tag"] = await element.evaluate(
                            "el => el.tagName.toLowerCase()"
                        )
                        attrs["text"] = (await element.text_content() or "").strip()
                    except Exception:
                        pass

                    return ElementMatch(
                        selector=f"xpath={xpath}",
                        strategy=LocatorStrategy.XPATH,
                        confidence=0.7,
                        attributes=attrs,
                    )

            except Exception:
                continue

        logger.debug("XPath failed for all patterns")
        return None

    async def _try_visual(
        self,
        page: Any,
        description: str,
        hint_selector: str | None,
        hint_testid: str | None,
    ) -> ElementMatch | None:
        """Try to find element by visual position (AI vision).

        This is a placeholder for AI-based visual element detection.
        Would require integration with vision model (e.g., Claude Vision, GPT-4V).

        Args:
            page: Playwright page object
            description: Element description
            hint_selector: Unused for this strategy
            hint_testid: Unused for this strategy

        Returns:
            ElementMatch if found, None otherwise (currently always None)

        """
        logger.debug("Visual position strategy not yet implemented")
        # TODO: Implement AI vision-based element detection
        # 1. Take screenshot
        # 2. Send to vision model with prompt: "Find element: {description}"
        # 3. Get bounding box coordinates
        # 4. Convert to selector
        return None

    async def verify_element(
        self, page: Any, match: ElementMatch
    ) -> tuple[bool, dict[str, Any]]:
        """Verify that element is still valid and interactable.

        Args:
            page: Playwright page object
            match: ElementMatch to verify

        Returns:
            Tuple of (is_valid, updated_attributes)

        """
        try:
            locator = page.locator(match.selector)
            count = await locator.count()

            if count == 0:
                return False, {}

            element = locator.first

            # Check visibility and interactability
            is_visible = await element.is_visible()
            is_enabled = await element.is_enabled()

            attrs = match.attributes.copy()
            attrs["visible"] = is_visible
            attrs["enabled"] = is_enabled
            attrs["count"] = count

            is_valid = is_visible and is_enabled

            return is_valid, attrs

        except Exception as e:
            logger.debug(f"Element verification failed: {e}")
            return False, {}
