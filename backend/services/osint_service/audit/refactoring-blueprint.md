## OSINT Service - Refactoring Blueprint (Phase 3)

**Generated:** 2025-10-14
**Status:** DESIGN APPROVED - Ready for Implementation
**Constitutional Compliance:** ✅ Article I (Clause 3.1) - Inflexible Plan Adherence

---

## PRIORITY ORDER (by criticality)

Based on Phase 1 audit findings, refactor tools in this order:

1. **SocialMediaScraper** - Highest usage, most visible
2. **UsernameHunter** - Critical for investigation workflows
3. **EmailAnalyzer** - Simple, good proof-of-concept
4. **PhoneAnalyzer** - Simple, similar to EmailAnalyzer
5. **ImageAnalyzer** - Complex, requires external libraries
6. **DiscordBotScraper** - Requires Discord API setup
7. **PatternDetector** - Low priority, simple logic
8. **AIProcessor** - Depends on LLM API integration
9. **ReportGenerator** - Low risk, cosmetic improvements
10. **AIOrchestrator** - Refactor AFTER all tools done
11. **GoogleOSINT** - Separate service, lower priority

---

## REFACTORING TEMPLATE (Follow for each tool)

### Step 1: Write Tests FIRST (TDD approach)

Create `tests/unit/test_<tool_name>_refactored.py`:

```python
import pytest
from core import BaseTool, ToolException

@pytest.mark.asyncio
async def test_tool_basic_query():
    """Test basic query with mocked API response."""
    async with MyToolRefactored(api_key="test_key", rate_limit=10.0) as tool:
        result = await tool.query("test_target")
        assert result is not None
        assert "data" in result

@pytest.mark.asyncio
async def test_tool_retry_on_timeout():
    """Test retry logic on transient failures."""
    # Mock API to fail 2 times, then succeed
    ...

@pytest.mark.asyncio
async def test_tool_circuit_breaker_opens():
    """Test circuit breaker opens after 5 failures."""
    ...

@pytest.mark.asyncio
async def test_tool_caching():
    """Test cache hit/miss behavior."""
    ...

@pytest.mark.asyncio
async def test_tool_rate_limiting():
    """Test rate limiter enforces limits."""
    ...
```

### Step 2: Create Refactored Tool

Create `<module>/<tool_name>_refactored.py`:

```python
"""Refactored <Tool Name> with production hardening."""

from typing import Any, Dict
from core import BaseTool

class <ToolName>Refactored(BaseTool):
    """
    Production-hardened version of <ToolName>.

    Improvements over original:
    - ✅ Retry logic with exponential backoff
    - ✅ Circuit breaker for fail-fast
    - ✅ Token bucket rate limiting
    - ✅ Multi-tier caching
    - ✅ Prometheus metrics
    - ✅ Structured JSON logging
    - ✅ Real API integration (no mocks)
    """

    BASE_URL = "https://api.example.com"

    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Core query logic (implements abstract method from BaseTool)."""
        url = f"{self.BASE_URL}/endpoint/{target}"

        # Add API key to params
        if self.api_key:
            params["api_key"] = self.api_key

        # Use BaseTool's _make_request (handles retry, circuit breaker, metrics)
        return await self._make_request(url, method="GET", params=params)
```

### Step 3: Run Tests

```bash
pytest tests/unit/test_<tool_name>_refactored.py -v --cov=<module> --cov-report=term-missing
```

**Acceptance Criteria:**
- ✅ All tests pass (green)
- ✅ Coverage ≥ 90%
- ✅ No print() statements
- ✅ No TODOs

### Step 4: Integration Test with Real API

Create `tests/integration/test_<tool_name>_live.py`:

```python
import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("API_KEY"), reason="No API key")
@pytest.mark.asyncio
async def test_tool_live_api():
    """Test with real API (requires API key in env)."""
    api_key = os.getenv("API_KEY")

    async with MyToolRefactored(api_key=api_key, rate_limit=1.0) as tool:
        result = await tool.query("real_target")
        assert result is not None
```

### Step 5: Update Orchestrator

Update `ai_orchestrator.py` to use refactored tool:

```python
# OLD
from scrapers.social_scraper import SocialMediaScraper

# NEW
from scrapers.social_scraper_refactored import SocialMediaScraperRefactored

class AIOrchestrator:
    def __init__(self):
        # OLD
        # self.social_scraper = SocialMediaScraper()

        # NEW
        self.social_scraper = SocialMediaScraperRefactored(
            api_key=os.getenv("TWITTER_API_KEY"),
            rate_limit=1.0,  # 1 req/sec for free tier
            cache_ttl=3600,
            circuit_breaker_threshold=5,
        )
```

### Step 6: Deprecate Old Tool

Rename old tool to `<tool_name>_legacy.py` with deprecation notice:

```python
"""
DEPRECATED: Use <tool_name>_refactored.py instead.

This file is kept for reference only and will be removed in Phase 4.
"""
```

---

## CONCRETE EXAMPLE: SocialMediaScraper Refactoring

### BEFORE (social_scraper.py - lines 26-67)

```python
class SocialMediaScraper(BaseScraper):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.scraped_profiles: Dict[str, Any] = {}
        self.last_scrape_time: Optional[datetime] = None
        self.current_status: str = "idle"

    async def scrape(self, query: str, platform: str = "all", depth: int = 1):
        print(f"[SocialMediaScraper] Scraping '{platform}' for query: '{query}'...")
        self.current_status = "scraping"
        await asyncio.sleep(0.5)  # ❌ MOCK

        results: List[Dict[str, Any]] = []

        if platform == "twitter" or platform == "all":
            results.extend(self._simulate_twitter_scrape(query, depth))  # ❌ MOCK
        if platform == "linkedin" or platform == "all":
            results.extend(self._simulate_linkedin_scrape(query, depth))  # ❌ MOCK

        return results
```

**Problems:**
- ❌ No real API integration (100% mock)
- ❌ No retry logic
- ❌ No rate limiting
- ❌ No caching
- ❌ No metrics
- ❌ print() statements
- ❌ Sequential API calls (inefficient)

---

### AFTER (social_scraper_refactored.py)

```python
"""Maximus OSINT Service - Social Media Scraper (Refactored).

Production-hardened version with real API integration for:
- Twitter (via tweepy)
- LinkedIn (via unofficial API)

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, no mocks
    - Article III (Zero Trust): All APIs can fail
    - Article IV (Antifragility): Survives API failures via circuit breaker

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 2.0.0
"""

import asyncio
from typing import Any, Dict, List, Optional

from core import BaseTool, ToolException

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False


class SocialMediaScraperRefactored(BaseTool):
    """
    Production-grade social media scraper with real API integration.

    Supported Platforms:
    - Twitter (requires Twitter API v2 Bearer Token)
    - LinkedIn (requires unofficial API or scraping)

    Improvements over legacy version:
    - ✅ Real Twitter API v2 integration (tweepy)
    - ✅ Retry with exponential backoff
    - ✅ Circuit breaker (fail-fast on repeated failures)
    - ✅ Rate limiting (1 req/sec for free tier)
    - ✅ Caching (reduces API calls)
    - ✅ Prometheus metrics
    - ✅ Structured logging
    - ✅ Parallel API calls (asyncio.gather)
    """

    TWITTER_API_URL = "https://api.twitter.com/2"

    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        linkedin_api_key: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Social Media Scraper with API credentials.

        Args:
            twitter_bearer_token: Twitter API v2 Bearer Token
            linkedin_api_key: LinkedIn API key (if available)
            **kwargs: Passed to BaseTool (rate_limit, cache_ttl, etc.)
        """
        super().__init__(api_key=twitter_bearer_token, **kwargs)

        self.twitter_bearer_token = twitter_bearer_token
        self.linkedin_api_key = linkedin_api_key

        # Initialize Twitter client
        if twitter_bearer_token and TWITTER_AVAILABLE:
            self.twitter_client = tweepy.Client(bearer_token=twitter_bearer_token)
        else:
            self.twitter_client = None
            self.logger.warning(
                "twitter_unavailable",
                reason="No bearer token or tweepy not installed"
            )

    async def _query_impl(self, username: str, platforms: List[str] = ["twitter"], **params) -> Dict[str, Any]:
        """Query social media platforms for user profile.

        Args:
            username: Target username
            platforms: List of platforms to query (default: ["twitter"])
            **params: Additional query parameters

        Returns:
            Aggregated results from all platforms
        """
        tasks = []

        if "twitter" in platforms and self.twitter_client:
            tasks.append(self._scrape_twitter(username))

        if "linkedin" in platforms and self.linkedin_api_key:
            tasks.append(self._scrape_linkedin(username))

        # Execute all API calls in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results (handle failures gracefully)
        aggregated = {
            "username": username,
            "platforms": {},
            "errors": [],
        }

        for i, result in enumerate(results):
            platform = platforms[i] if i < len(platforms) else f"platform_{i}"

            if isinstance(result, Exception):
                aggregated["errors"].append({
                    "platform": platform,
                    "error": str(result),
                })
                self.logger.error(
                    "platform_scrape_failed",
                    platform=platform,
                    username=username,
                    error=str(result),
                )
            else:
                aggregated["platforms"][platform] = result

        return aggregated

    async def _scrape_twitter(self, username: str) -> Dict[str, Any]:
        """Scrape Twitter user profile via Twitter API v2.

        Args:
            username: Twitter username (without @)

        Returns:
            User profile data

        Raises:
            ToolException: On API failure
        """
        if not self.twitter_client:
            raise ToolException("Twitter API not configured")

        try:
            # Get user by username
            user = self.twitter_client.get_user(
                username=username,
                user_fields=["created_at", "description", "public_metrics", "verified"]
            )

            if not user.data:
                raise ToolException(f"Twitter user not found: {username}")

            return {
                "id": user.data.id,
                "name": user.data.name,
                "username": user.data.username,
                "description": user.data.description,
                "followers": user.data.public_metrics["followers_count"],
                "following": user.data.public_metrics["following_count"],
                "tweets": user.data.public_metrics["tweet_count"],
                "verified": user.data.verified,
                "created_at": user.data.created_at.isoformat(),
            }

        except tweepy.TweepyException as e:
            self.logger.error("twitter_api_error", username=username, error=str(e))
            raise ToolException(f"Twitter API error: {e}", original_error=e)

    async def _scrape_linkedin(self, username: str) -> Dict[str, Any]:
        """Scrape LinkedIn profile.

        Args:
            username: LinkedIn username

        Returns:
            Profile data
        """
        # TODO: Implement LinkedIn API integration
        # For now, raise NotImplementedError
        raise NotImplementedError("LinkedIn API integration pending")
```

**Improvements:**
- ✅ Real Twitter API v2 integration via `tweepy`
- ✅ Inherits retry/circuit breaker/rate limiting from BaseTool
- ✅ Parallel API calls via `asyncio.gather`
- ✅ Graceful error handling (partial results if one platform fails)
- ✅ Structured logging (no print statements)
- ✅ Automatic caching via BaseTool.query()
- ✅ Prometheus metrics via BaseTool._make_request()

---

## TESTING STRATEGY PER TOOL

### Unit Tests (pytest-mock)

```python
@pytest.mark.asyncio
async def test_social_scraper_twitter_success(mocker):
    """Test successful Twitter scrape with mocked API."""
    # Mock tweepy client
    mock_client = mocker.Mock()
    mock_user = mocker.Mock()
    mock_user.data.id = "123"
    mock_user.data.name = "Test User"
    mock_user.data.username = "testuser"
    mock_client.get_user.return_value = mock_user

    scraper = SocialMediaScraperRefactored(twitter_bearer_token="fake")
    scraper.twitter_client = mock_client

    async with scraper:
        result = await scraper.query("testuser", platforms=["twitter"])

    assert result["platforms"]["twitter"]["username"] == "testuser"
```

### Integration Tests (pytest-vcr)

```python
@pytest.mark.integration
@pytest.mark.vcr  # Records HTTP interactions
@pytest.mark.asyncio
async def test_social_scraper_twitter_live():
    """Test with real Twitter API (recorded via VCR)."""
    token = os.getenv("TWITTER_BEARER_TOKEN")

    async with SocialMediaScraperRefactored(twitter_bearer_token=token) as scraper:
        result = await scraper.query("elonmusk", platforms=["twitter"])

    assert result["platforms"]["twitter"]["followers"] > 1000000
```

---

## DEPLOYMENT CHECKLIST PER TOOL

Before merging refactored tool:

- [ ] All unit tests pass (pytest)
- [ ] Coverage ≥ 90%
- [ ] Integration tests pass (with real API)
- [ ] No print() statements
- [ ] No TODOs
- [ ] Structured logging validated (JSON output)
- [ ] Prometheus metrics exposed (/metrics endpoint)
- [ ] Circuit breaker tested (manual failure injection)
- [ ] Rate limiter tested (1000 concurrent requests)
- [ ] Cache hit rate ≥ 60% (load test)
- [ ] Orchestrator updated to use refactored tool
- [ ] Legacy tool renamed to *_legacy.py
- [ ] Documentation updated

---

## ESTIMATED TIMELINE (Phase 3)

| Tool | Complexity | Est. Time | Dependencies |
|------|-----------|-----------|--------------|
| EmailAnalyzer | LOW | 0.5 days | None |
| PhoneAnalyzer | LOW | 0.5 days | None |
| SocialMediaScraper | HIGH | 2 days | Twitter API key |
| UsernameHunter | MEDIUM | 1.5 days | Multiple API keys |
| ImageAnalyzer | HIGH | 2 days | pytesseract, face_recognition |
| DiscordBotScraper | MEDIUM | 1.5 days | Discord bot token |
| PatternDetector | LOW | 0.5 days | None |
| AIProcessor | MEDIUM | 1 day | OpenAI API key |
| ReportGenerator | LOW | 0.5 days | None |
| AIOrchestrator | MEDIUM | 1 day | All tools done |
| GoogleOSINT | LOW | 0.5 days | Google API key |

**Total: 12 days (2.4 weeks)**

---

## NEXT STEPS

1. ✅ Phase 2 COMPLETE - Design approved
2. 🚀 Phase 3 START - Implement refactoring
   - Begin with EmailAnalyzer (easiest, proof-of-concept)
   - Then PhoneAnalyzer (similar to EmailAnalyzer)
   - Then SocialMediaScraper (highest priority, most complex)
3. ⏳ Phase 4 - Load testing and chaos engineering
4. ⏳ Phase 5 - Documentation and deployment

**Awaiting Chief Architect directive to proceed with Phase 3.**
