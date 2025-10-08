"""
Fact-Check Aggregator for Cognitive Defense System.

Integrates multiple fact-checking APIs:
- Google Fact Check Tools API (ClaimReview aggregation)
- ClaimBuster API (check-worthiness + fact matching)
"""

import logging
from typing import Any, Dict, List, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from cache_manager import CacheCategory, cache_manager
from config import get_settings
from models import VerificationStatus
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class GoogleFactCheckClient:
    """Client for Google Fact Check Tools API."""

    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(self):
        """Initialize Google Fact Check client."""
        self.api_key = settings.GOOGLE_FACTCHECK_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self._enabled = bool(self.api_key and self.api_key != "your_google_key_here")

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("✅ Google Fact Check client initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_claims(
        self,
        query: str,
        language_code: str = "pt",
        max_results: int = 10,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for fact-checked claims.

        Args:
            query: Search query (claim text)
            language_code: Language code (default "pt" for Portuguese)
            max_results: Maximum results to return
            use_cache: Whether to use cache

        Returns:
            List of ClaimReview matches
        """
        if not self._enabled:
            logger.warning("Google Fact Check API key not configured")
            return []

        # Check cache
        if use_cache:
            cache_key = f"google:{hash_text(query)}"
            cached = await cache_manager.get(CacheCategory.FACTCHECK, cache_key)
            if cached:
                logger.debug(f"Fact-check cache hit: {query[:50]}")
                return cached

        try:
            if not self.session:
                await self.initialize()

            params = {
                "key": self.api_key,
                "query": query,
                "languageCode": language_code,
                "pageSize": max_results,
            }

            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    logger.error(f"Google Fact Check API error {response.status}: {await response.text()}")
                    return []

                data = await response.json()
                claims = data.get("claims", [])

                # Parse ClaimReview format
                parsed_claims = [self._parse_claim_review(claim) for claim in claims]

                # Cache for 30 days
                if use_cache and parsed_claims:
                    cache_key = f"google:{hash_text(query)}"
                    await cache_manager.set(CacheCategory.FACTCHECK, cache_key, parsed_claims)

                return parsed_claims

        except aiohttp.ClientError as e:
            logger.error(f"Google Fact Check API connection error: {e}")
            return []
        except Exception as e:
            logger.error(f"Google Fact Check API unexpected error: {e}", exc_info=True)
            return []

    def _parse_claim_review(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ClaimReview schema.org format."""
        claim_reviews = claim_data.get("claimReview", [])

        # Aggregate ratings from multiple fact-checkers
        all_ratings = []
        all_sources = []

        for review in claim_reviews:
            publisher = review.get("publisher", {}).get("name", "Unknown")
            rating_text = review.get("textualRating", "")
            rating_value = review.get("rating", {}).get("ratingValue")
            url = review.get("url", "")

            all_ratings.append(rating_text.lower())
            all_sources.append(
                {
                    "publisher": publisher,
                    "rating": rating_text,
                    "rating_value": rating_value,
                    "url": url,
                    "date": review.get("reviewDate"),
                }
            )

        # Determine consensus verification status
        status = self._determine_verification_status(all_ratings)

        return {
            "claim_text": claim_data.get("text", ""),
            "claimant": claim_data.get("claimant", ""),
            "claim_date": claim_data.get("claimDate"),
            "verification_status": status.value,
            "fact_checkers": all_sources,
            "consensus_confidence": self._calculate_consensus_confidence(all_ratings),
        }

    @staticmethod
    def _determine_verification_status(ratings: List[str]) -> VerificationStatus:
        """Determine verification status from ratings."""
        if not ratings:
            return VerificationStatus.UNVERIFIED

        # Count rating types
        false_keywords = ["false", "incorrect", "fake", "misleading", "pants on fire"]
        true_keywords = ["true", "correct", "accurate", "verified"]
        mixed_keywords = ["mixture", "mostly", "partially", "some"]

        false_count = sum(1 for r in ratings if any(k in r for k in false_keywords))
        true_count = sum(1 for r in ratings if any(k in r for k in true_keywords))
        mixed_count = sum(1 for r in ratings if any(k in r for k in mixed_keywords))

        total = len(ratings)

        # Majority vote with tie-breaking
        if false_count > total / 2:
            return VerificationStatus.VERIFIED_FALSE
        elif true_count > total / 2:
            return VerificationStatus.VERIFIED_TRUE
        elif mixed_count > 0 or (false_count > 0 and true_count > 0):
            return VerificationStatus.MIXED
        elif false_count > 0 or true_count > 0:
            return VerificationStatus.DISPUTED
        else:
            return VerificationStatus.UNVERIFIED

    @staticmethod
    def _calculate_consensus_confidence(ratings: List[str]) -> float:
        """Calculate consensus confidence from rating agreement."""
        if not ratings:
            return 0.0

        if len(ratings) == 1:
            return 0.6  # Single source - moderate confidence

        # Measure agreement using pairwise similarity
        from collections import Counter

        rating_counter = Counter(ratings)
        most_common_count = rating_counter.most_common(1)[0][1]

        # Agreement ratio
        agreement = most_common_count / len(ratings)

        return agreement


class ClaimBusterClient:
    """Client for ClaimBuster API (check-worthiness + fact matching)."""

    BASE_URL = "https://idir.uta.edu/claimbuster/api/v2"

    def __init__(self):
        """Initialize ClaimBuster client."""
        self.api_key = settings.CLAIMBUSTER_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self._enabled = bool(self.api_key and self.api_key != "your_claimbuster_key_here")

    async def initialize(self) -> None:
        """Initialize HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers={"x-api-key": self.api_key}, timeout=timeout)
            logger.info("✅ ClaimBuster client initialized")

    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def score_claim(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Score check-worthiness of text.

        Args:
            text: Text to analyze
            use_cache: Whether to use cache

        Returns:
            Dict with check-worthiness score and claims
        """
        if not self._enabled:
            logger.warning("ClaimBuster API key not configured")
            return {"score": 0.5, "claims": []}

        # Check cache
        if use_cache:
            cache_key = f"claimbuster:{hash_text(text)}"
            cached = await cache_manager.get(CacheCategory.FACTCHECK, cache_key)
            if cached:
                return cached

        try:
            if not self.session:
                await self.initialize()

            # Score API
            url = f"{self.BASE_URL}/score/text/"
            payload = {"input_text": text}

            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"ClaimBuster API error {response.status}")
                    return {"score": 0.5, "claims": []}

                data = await response.json()

                # Extract check-worthy sentences
                results = data.get("results", [])
                claims = [
                    {"text": result.get("text", ""), "score": result.get("score", 0.0)}
                    for result in results
                    if result.get("score", 0) >= settings.THRESHOLD_CHECK_WORTHINESS
                ]

                # Overall score (max of sentence scores)
                overall_score = max([c["score"] for c in claims], default=0.0)

                result = {"score": overall_score, "claims": claims}

                # Cache
                if use_cache:
                    cache_key = f"claimbuster:{hash_text(text)}"
                    await cache_manager.set(CacheCategory.FACTCHECK, cache_key, result)

                return result

        except Exception as e:
            logger.error(f"ClaimBuster API error: {e}", exc_info=True)
            return {"score": 0.5, "claims": []}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def match_claim(
        self, claim: str, similarity_threshold: float = 0.85, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Match claim against ClaimBuster's fact-checked database.

        Args:
            claim: Claim text to match
            similarity_threshold: Minimum similarity score (0-1)
            use_cache: Whether to use cache

        Returns:
            Best matching fact-check or None
        """
        if not self._enabled:
            logger.warning("ClaimBuster API key not configured")
            return None

        # Check cache
        if use_cache:
            cache_key = f"claimbuster_match:{hash_text(claim)}"
            cached = await cache_manager.get(CacheCategory.FACTCHECK, cache_key)
            if cached:
                return cached

        try:
            if not self.session:
                await self.initialize()

            # Fact matcher API
            url = f"{self.BASE_URL}/fact_matcher/"
            payload = {"input_claim": claim}

            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.warning(f"ClaimBuster fact_matcher API error {response.status}")
                    return None

                data = await response.json()
                matches = data.get("matches", [])

                if not matches:
                    return None

                # Get best match above threshold
                best_match = max(matches, key=lambda m: m.get("similarity", 0))

                if best_match.get("similarity", 0) < similarity_threshold:
                    return None

                result = {
                    "original_claim": claim,
                    "matched_claim": best_match.get("claim", ""),
                    "similarity": best_match.get("similarity", 0.0),
                    "verdict": best_match.get("verdict", "unverified"),  # true/false/mixed
                    "source": best_match.get("source", ""),
                    "url": best_match.get("url", ""),
                    "fact_checker": best_match.get("fact_checker", "ClaimBuster"),
                    "date": best_match.get("date"),
                }

                # Cache for 30 days
                if use_cache:
                    cache_key = f"claimbuster_match:{hash_text(claim)}"
                    await cache_manager.set(CacheCategory.FACTCHECK, cache_key, result)

                return result

        except Exception as e:
            logger.error(f"ClaimBuster fact_matcher API error: {e}", exc_info=True)
            return None


class FactCheckAggregator:
    """Aggregates results from multiple fact-checking APIs."""

    def __init__(self):
        """Initialize aggregator."""
        self.google_client = GoogleFactCheckClient()
        self.claimbuster_client = ClaimBusterClient()

    async def initialize(self) -> None:
        """Initialize all clients."""
        await self.google_client.initialize()
        await self.claimbuster_client.initialize()

    async def close(self) -> None:
        """Close all clients."""
        await self.google_client.close()
        await self.claimbuster_client.close()

    async def verify_claim(self, claim_text: str, check_worthiness_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Comprehensive claim verification (Tier 1).

        Args:
            claim_text: Claim to verify
            check_worthiness_threshold: Minimum score to fact-check

        Returns:
            Verification result dict
        """
        # Step 1: Check-worthiness scoring
        claimbuster_result = await self.claimbuster_client.score_claim(claim_text)
        check_worthiness = claimbuster_result["score"]

        if check_worthiness < check_worthiness_threshold:
            return {
                "claim_text": claim_text,
                "check_worthiness": check_worthiness,
                "verification_status": VerificationStatus.UNVERIFIED.value,
                "sources": [],
                "confidence": 0.0,
                "tier_used": 1,
                "matched_from": None,
            }

        # Step 2: Try ClaimBuster fact matching first (fast)
        claimbuster_match = await self.claimbuster_client.match_claim(claim_text)

        if claimbuster_match:
            verdict_map = {
                "true": VerificationStatus.VERIFIED_TRUE,
                "false": VerificationStatus.VERIFIED_FALSE,
                "mixed": VerificationStatus.MIXED,
            }

            status = verdict_map.get(claimbuster_match["verdict"].lower(), VerificationStatus.DISPUTED)

            return {
                "claim_text": claim_text,
                "check_worthiness": check_worthiness,
                "verification_status": status.value,
                "sources": [
                    {
                        "publisher": claimbuster_match["fact_checker"],
                        "url": claimbuster_match["url"],
                        "similarity": claimbuster_match["similarity"],
                    }
                ],
                "confidence": claimbuster_match["similarity"],
                "tier_used": 1,
                "matched_from": "claimbuster",
                "matched_claim": claimbuster_match["matched_claim"],
            }

        # Step 3: Fallback to Google Fact Check
        google_results = await self.google_client.search_claims(claim_text)

        if not google_results:
            return {
                "claim_text": claim_text,
                "check_worthiness": check_worthiness,
                "verification_status": VerificationStatus.UNVERIFIED.value,
                "sources": [],
                "confidence": 0.0,
                "tier_used": 1,
                "matched_from": None,
            }

        # Step 4: Aggregate Google results
        best_match = google_results[0]  # Highest relevance

        return {
            "claim_text": claim_text,
            "check_worthiness": check_worthiness,
            "verification_status": best_match["verification_status"],
            "sources": best_match["fact_checkers"],
            "confidence": best_match["consensus_confidence"],
            "tier_used": 1,
            "matched_from": "google_factcheck",
            "all_matches": google_results[:5],  # Top 5
        }

    async def batch_verify(self, claims: List[str]) -> List[Dict[str, Any]]:
        """Verify multiple claims in parallel."""
        import asyncio

        tasks = [self.verify_claim(claim) for claim in claims]
        return await asyncio.gather(*tasks)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

fact_check_aggregator = FactCheckAggregator()
