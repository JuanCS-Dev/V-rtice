"""Maximus OSINT Service - Social Media Scraper (Production-Hardened).

This module implements a production-grade Social Media Scraper with real API integrations,
observability, and resilience patterns.

Key improvements over legacy version:
- ✅ Real Twitter API v2 integration (via tweepy)
- ✅ Structured JSON logging (no print statements)
- ✅ Prometheus metrics (API calls, rate limit tracking, errors)
- ✅ Inherits from BaseTool (rate limiting, circuit breaker, caching, retries)
- ✅ Parallel API calls with asyncio.gather
- ✅ Comprehensive error handling
- ✅ Response normalization across platforms

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, real API integration
    - Article V (Prior Legislation): Observability first
    - Article VII (Antifragility): Circuit breakers, retries, graceful degradation
    - Article IX (Zero Trust): Input validation, API key security

Supported Platforms:
    - Twitter (via API v2)
    - LinkedIn (planned - requires LinkedIn API access)
    - Facebook (planned - requires Graph API access)

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 2.0.0
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import tweepy

from core.base_tool import BaseTool


class SocialScraperRefactored(BaseTool):
    """Production-grade social media scraper with real API integrations.

    Inherits from BaseTool to get:
    - Rate limiting (token bucket)
    - Circuit breaker (fail-fast on API errors)
    - Caching (Redis + in-memory)
    - Structured logging
    - Prometheus metrics
    - Automatic retries with exponential backoff

    Usage Example:
        scraper = SocialScraperRefactored(
            api_key=os.getenv("TWITTER_BEARER_TOKEN"),
            rate_limit=1.0,  # 1 request/second
            cache_ttl=3600,  # 1 hour cache
        )

        # Search Twitter for recent tweets
        result = await scraper.query(
            target="AI safety",
            platform="twitter",
            max_results=10
        )

        print(result["tweets"])  # List of tweet objects
    """

    SUPPORTED_PLATFORMS = ["twitter", "linkedin", "facebook"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 3600,
        cache_backend: str = "memory",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize SocialScraperRefactored with API credentials.

        Args:
            api_key: Twitter Bearer Token (from TWITTER_BEARER_TOKEN env var)
            rate_limit: Requests per second (Twitter API v2: 300 req/15min = 0.33/sec)
            timeout: HTTP timeout in seconds
            max_retries: Number of retry attempts
            cache_ttl: Cache time-to-live in seconds
            cache_backend: 'redis' or 'memory'
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting recovery
        """
        super().__init__(
            api_key=api_key,
            rate_limit=rate_limit,
            timeout=timeout,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            circuit_breaker_threshold=circuit_breaker_threshold,
            circuit_breaker_timeout=circuit_breaker_timeout,
        )

        # Twitter API client (API v2)
        self.twitter_client: Optional[tweepy.Client] = None
        if api_key:
            try:
                self.twitter_client = tweepy.Client(bearer_token=api_key)
                self.logger.info("twitter_client_initialized")
            except Exception as e:
                self.logger.error("twitter_client_init_failed", error=str(e))
                # Don't fail initialization - gracefully degrade
        else:
            self.logger.warning(
                "twitter_api_key_missing", message="Set TWITTER_BEARER_TOKEN env var"
            )

        # Statistics
        self.total_queries = 0
        self.total_tweets_fetched = 0
        self.total_profiles_fetched = 0

    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Implementation of query logic (called by BaseTool.query).

        This method is wrapped by BaseTool with:
        - Rate limiting
        - Circuit breaker
        - Caching
        - Retries
        - Metrics

        Args:
            target: Search query or username
            **params:
                - platform: 'twitter', 'linkedin', 'facebook', or 'all' (default: 'twitter')
                - max_results: Maximum number of results (default: 10)
                - search_type: 'recent' or 'user' (default: 'recent')

        Returns:
            Normalized result dictionary with platform-specific data

        Raises:
            ValueError: If platform is not supported or API key missing
            Exception: If API call fails
        """
        platform = params.get("platform", "twitter")
        max_results = params.get("max_results", 10)
        search_type = params.get("search_type", "recent")

        self.logger.info(
            "query_started",
            target=target,
            platform=platform,
            max_results=max_results,
            search_type=search_type,
        )

        # Validate platform
        if platform not in self.SUPPORTED_PLATFORMS and platform != "all":
            raise ValueError(
                f"Unsupported platform: {platform}. Supported: {self.SUPPORTED_PLATFORMS}"
            )

        # Route to platform-specific handler
        if platform == "twitter":
            result = await self._query_twitter(target, max_results, search_type)
        elif platform == "all":
            # Parallel queries across all platforms
            result = await self._query_all_platforms(target, max_results, search_type)
        else:
            # LinkedIn, Facebook not yet implemented - return empty results with warning
            self.logger.warning(
                f"⚠️ OSINT SCRAPER: Platform '{platform}' not yet supported. Only 'twitter' and 'all' available.",
                extra={"platform": platform, "supported_platforms": ["twitter", "all"]},
            )
            result = {
                "status": "unsupported_platform",
                "platform": platform,
                "message": f"Platform '{platform}' integration coming soon. Currently supported: twitter, all",
                "posts": [],
                "metadata": {
                    "total_results": 0,
                    "query_time": datetime.now(timezone.utc).isoformat(),
                    "platform_status": "not_implemented",
                },
            }

        self.total_queries += 1
        return result

    async def _query_twitter(
        self, target: str, max_results: int, search_type: str
    ) -> Dict[str, Any]:
        """Query Twitter API v2 for tweets or user information.

        Args:
            target: Search query or username
            max_results: Maximum tweets to fetch (API limit: 100)
            search_type: 'recent' (search tweets) or 'user' (get user profile)

        Returns:
            Dictionary with normalized Twitter data

        Raises:
            ValueError: If Twitter client not initialized
            Exception: If API call fails
        """
        if not self.twitter_client:
            # Graceful degradation: return empty result instead of failing
            self.logger.warning(
                "twitter_client_unavailable", message="Twitter API disabled (paid API)"
            )
            return {
                "platform": "twitter",
                "target": target,
                "search_type": search_type,
                "tweets": [],
                "user_profile": None,
                "total_results": 0,
                "api_available": False,
                "message": "Twitter API requires paid subscription - feature temporarily unavailable",
            }

        try:
            if search_type == "recent":
                # Search recent tweets (last 7 days)
                response = self.twitter_client.search_recent_tweets(
                    query=target,
                    max_results=min(max_results, 100),  # API limit
                    tweet_fields=["created_at", "author_id", "public_metrics", "lang"],
                )

                tweets = []
                if response.data:
                    for tweet in response.data:
                        tweets.append(
                            {
                                "id": tweet.id,
                                "text": tweet.text,
                                "created_at": (
                                    tweet.created_at.isoformat()
                                    if tweet.created_at
                                    else None
                                ),
                                "author_id": tweet.author_id,
                                "metrics": {
                                    "likes": (
                                        tweet.public_metrics.get("like_count", 0)
                                        if tweet.public_metrics
                                        else 0
                                    ),
                                    "retweets": (
                                        tweet.public_metrics.get("retweet_count", 0)
                                        if tweet.public_metrics
                                        else 0
                                    ),
                                    "replies": (
                                        tweet.public_metrics.get("reply_count", 0)
                                        if tweet.public_metrics
                                        else 0
                                    ),
                                },
                                "language": tweet.lang,
                            }
                        )

                self.total_tweets_fetched += len(tweets)

                self.logger.info(
                    "twitter_search_complete",
                    query=target,
                    tweets_found=len(tweets),
                )

                return {
                    "platform": "twitter",
                    "query": target,
                    "search_type": "recent",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "result_count": len(tweets),
                    "tweets": tweets,
                }

            elif search_type == "user":
                # Get user profile by username
                username = target.lstrip("@")  # Remove @ if present
                response = self.twitter_client.get_user(
                    username=username,
                    user_fields=[
                        "created_at",
                        "description",
                        "public_metrics",
                        "verified",
                    ],
                )

                if not response.data:
                    self.logger.warning("twitter_user_not_found", username=username)
                    return {
                        "platform": "twitter",
                        "query": target,
                        "search_type": "user",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "found": False,
                    }

                user = response.data
                self.total_profiles_fetched += 1

                self.logger.info(
                    "twitter_user_found", username=username, user_id=user.id
                )

                return {
                    "platform": "twitter",
                    "query": target,
                    "search_type": "user",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "found": True,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "name": user.name,
                        "description": user.description,
                        "created_at": (
                            user.created_at.isoformat() if user.created_at else None
                        ),
                        "verified": user.verified,
                        "metrics": {
                            "followers": (
                                user.public_metrics.get("followers_count", 0)
                                if user.public_metrics
                                else 0
                            ),
                            "following": (
                                user.public_metrics.get("following_count", 0)
                                if user.public_metrics
                                else 0
                            ),
                            "tweets": (
                                user.public_metrics.get("tweet_count", 0)
                                if user.public_metrics
                                else 0
                            ),
                        },
                    },
                }

            else:
                raise ValueError(
                    f"Invalid search_type: {search_type}. Use 'recent' or 'user'."
                )

        except tweepy.errors.TweepyException as e:
            self.logger.error(
                "twitter_api_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            self.metrics.increment_error(error_type="twitter_api_error")
            raise

    async def _query_all_platforms(
        self, target: str, max_results: int, search_type: str
    ) -> Dict[str, Any]:
        """Query all supported platforms in parallel.

        Args:
            target: Search query or username
            max_results: Maximum results per platform
            search_type: Search type (platform-specific)

        Returns:
            Dictionary with results from all platforms
        """
        self.logger.info(
            "parallel_query_started", target=target, platforms=self.SUPPORTED_PLATFORMS
        )

        # Launch parallel queries (only Twitter for now)
        tasks = []
        if self.twitter_client:
            tasks.append(self._query_twitter(target, max_results, search_type))

        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        aggregated = {
            "platform": "all",
            "query": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "platforms": {},
        }

        for result in results:
            if isinstance(result, Exception):
                self.logger.warning("platform_query_failed", error=str(result))
                continue
            platform_name = result.get("platform", "unknown")
            aggregated["platforms"][platform_name] = result

        self.logger.info(
            "parallel_query_complete",
            target=target,
            platforms_succeeded=len(aggregated["platforms"]),
        )

        return aggregated

    async def get_status(self) -> Dict[str, Any]:
        """Get scraper status and statistics.

        Returns:
            Status dictionary with metrics and API health
        """
        # Get base health check from BaseTool
        status = await self.health_check()

        # Add scraper-specific stats
        status.update(
            {
                "total_queries": self.total_queries,
                "total_tweets_fetched": self.total_tweets_fetched,
                "total_profiles_fetched": self.total_profiles_fetched,
                "twitter_api_available": self.twitter_client is not None,
            }
        )

        return status

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"SocialScraperRefactored(queries={self.total_queries}, "
            f"tweets={self.total_tweets_fetched}, "
            f"profiles={self.total_profiles_fetched})"
        )
