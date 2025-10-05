"""
NewsGuard API Client for Cognitive Defense System.

Integrates with NewsGuard's journalist-vetted source credibility database
covering 35,000+ domains with 9-criteria "Nutrition Label" ratings.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import get_settings
from .cache_manager import cache_manager, CacheCategory
from .models import CredibilityRating

logger = logging.getLogger(__name__)

settings = get_settings()


class NewsGuardClient:
    """Client for NewsGuard API with caching and error handling."""

    # NewsGuard API endpoints (hypothetical - adjust to actual API)
    BASE_URL = "https://api.newsguardtech.com/v2"

    # NewsGuard 9 Criteria (0-100 points each)
    CRITERIA_WEIGHTS = {
        "does_not_repeatedly_publish_false_content": 22,
        "gathers_and_presents_info_responsibly": 18,
        "regularly_corrects_errors": 12.5,
        "handles_difference_between_news_opinion": 12.5,
        "avoids_deceptive_headlines": 10,
        "website_discloses_ownership": 7.5,
        "clearly_labels_advertising": 7.5,
        "reveals_whos_in_charge": 5,
        "provides_names_of_content_creators": 5
    }

    def __init__(self):
        """Initialize NewsGuard client."""
        self.api_key = settings.NEWSGUARD_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self._enabled = bool(self.api_key and self.api_key != "your_newsguard_key_here")

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "User-Agent": f"CognitiveDefense/{settings.VERSION}"
                },
                timeout=timeout
            )
            logger.info("✅ NewsGuard client initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("✅ NewsGuard client closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def get_domain_rating(
        self,
        domain: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get NewsGuard rating for a domain.

        Args:
            domain: Domain name (e.g., "example.com")
            use_cache: Whether to use cache (default True)

        Returns:
            NewsGuard nutrition label dict or None if not found
        """
        if not self._enabled:
            logger.warning("NewsGuard API key not configured, using fallback")
            return await self._fallback_rating(domain)

        # Check cache first
        if use_cache:
            cache_key = f"domain:{domain}"
            cached = await cache_manager.get(CacheCategory.NEWSGUARD, cache_key)
            if cached:
                logger.debug(f"NewsGuard cache hit: {domain}")
                return cached

        # Query API
        try:
            if not self.session:
                await self.initialize()

            url = f"{self.BASE_URL}/domains/{domain}"

            async with self.session.get(url) as response:
                if response.status == 404:
                    logger.info(f"NewsGuard: Domain not in database: {domain}")
                    return None

                if response.status != 200:
                    logger.error(f"NewsGuard API error {response.status}: {await response.text()}")
                    return await self._fallback_rating(domain)

                data = await response.json()

                # Parse NewsGuard response
                nutrition_label = self._parse_nutrition_label(data)

                # Cache for 7 days
                if use_cache:
                    cache_key = f"domain:{domain}"
                    await cache_manager.set(
                        CacheCategory.NEWSGUARD,
                        cache_key,
                        nutrition_label
                    )

                return nutrition_label

        except aiohttp.ClientError as e:
            logger.error(f"NewsGuard API connection error: {e}")
            return await self._fallback_rating(domain)
        except Exception as e:
            logger.error(f"NewsGuard API unexpected error: {e}", exc_info=True)
            return await self._fallback_rating(domain)

    def _parse_nutrition_label(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse NewsGuard API response into standardized nutrition label.

        Args:
            api_response: Raw API response

        Returns:
            Parsed nutrition label with scores
        """
        # Extract scores for 9 criteria
        criteria_scores = {}
        for criterion, max_points in self.CRITERIA_WEIGHTS.items():
            # Normalize to 0-1 range
            raw_score = api_response.get("criteria", {}).get(criterion, 0)
            criteria_scores[criterion] = raw_score / max_points if max_points > 0 else 0.0

        # Calculate overall score (weighted sum)
        overall_score = sum(
            criteria_scores[k] * w
            for k, w in self.CRITERIA_WEIGHTS.items()
        )

        # Determine rating
        if overall_score >= 80:
            rating = CredibilityRating.TRUSTED
        elif overall_score >= 60:
            rating = CredibilityRating.GENERALLY_RELIABLE
        elif overall_score >= 40:
            rating = CredibilityRating.PROCEED_WITH_CAUTION
        elif overall_score >= 20:
            rating = CredibilityRating.UNRELIABLE
        else:
            rating = CredibilityRating.HIGHLY_UNRELIABLE

        return {
            "domain": api_response.get("domain"),
            "overall_score": overall_score,
            "rating": rating.value,
            "criteria_scores": criteria_scores,
            "last_updated": api_response.get("last_updated", datetime.utcnow().isoformat()),
            "full_response": api_response
        }

    async def _fallback_rating(self, domain: str) -> Dict[str, Any]:
        """
        Fallback rating when API is unavailable.

        Uses simple heuristics based on known trusted/untrusted domains.

        Args:
            domain: Domain name

        Returns:
            Fallback nutrition label
        """
        # Known trusted domains
        TRUSTED_DOMAINS = {
            "wikipedia.org", "gov", "edu", "reuters.com", "apnews.com",
            "bbc.com", "bbc.co.uk", "nytimes.com", "washingtonpost.com",
            "theguardian.com", "ft.com", "wsj.com", "bloomberg.com"
        }

        # Known unreliable patterns
        UNRELIABLE_PATTERNS = [
            "fake", "news", "conspiracy", "truth", "expose", "leaked",
            "shocking", "urgent", "breaking", "alert"
        ]

        domain_lower = domain.lower()

        # Check trusted
        if any(trusted in domain_lower for trusted in TRUSTED_DOMAINS):
            score = 90.0
            rating = CredibilityRating.TRUSTED
        # Check unreliable patterns
        elif any(pattern in domain_lower for pattern in UNRELIABLE_PATTERNS):
            score = 20.0
            rating = CredibilityRating.UNRELIABLE
        # Unknown - neutral
        else:
            score = 50.0
            rating = CredibilityRating.PROCEED_WITH_CAUTION

        # Equal distribution across criteria
        criteria_scores = {
            criterion: score / 100.0
            for criterion in self.CRITERIA_WEIGHTS.keys()
        }

        return {
            "domain": domain,
            "overall_score": score,
            "rating": rating.value,
            "criteria_scores": criteria_scores,
            "last_updated": datetime.utcnow().isoformat(),
            "full_response": None,
            "fallback": True
        }

    async def bulk_get_ratings(
        self,
        domains: List[str],
        use_cache: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get ratings for multiple domains efficiently.

        Args:
            domains: List of domain names
            use_cache: Whether to use cache

        Returns:
            Dict mapping domain to nutrition label
        """
        results = {}

        # Check cache first
        if use_cache:
            cache_keys = {domain: f"domain:{domain}" for domain in domains}
            cached_results = await cache_manager.get_many(
                CacheCategory.NEWSGUARD,
                list(cache_keys.values())
            )

            # Map back to domains
            for domain, cache_key in cache_keys.items():
                if cache_key in cached_results:
                    results[domain] = cached_results[cache_key]

        # Query API for uncached domains
        uncached_domains = [d for d in domains if d not in results]

        if uncached_domains:
            # Parallel requests (with rate limiting)
            import asyncio
            tasks = [
                self.get_domain_rating(domain, use_cache=False)
                for domain in uncached_domains
            ]
            ratings = await asyncio.gather(*tasks, return_exceptions=True)

            for domain, rating in zip(uncached_domains, ratings):
                if isinstance(rating, Exception):
                    logger.error(f"Error getting rating for {domain}: {rating}")
                    rating = await self._fallback_rating(domain)
                results[domain] = rating

        return results

    def score_to_rating(self, score: float) -> CredibilityRating:
        """
        Convert numerical score to categorical rating.

        Args:
            score: Score 0-100

        Returns:
            CredibilityRating enum
        """
        if score >= 80:
            return CredibilityRating.TRUSTED
        elif score >= 60:
            return CredibilityRating.GENERALLY_RELIABLE
        elif score >= 40:
            return CredibilityRating.PROCEED_WITH_CAUTION
        elif score >= 20:
            return CredibilityRating.UNRELIABLE
        else:
            return CredibilityRating.HIGHLY_UNRELIABLE


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

newsguard_client = NewsGuardClient()
