"""
Reality Distortion Module (Module 4) for Cognitive Defense System.

Two-tier claim verification architecture:
- TIER 1 (Fast): Check-worthiness → API matching (ClaimBuster, Google Fact Check)
- TIER 2 (Deep): Entity linking → SPARQL generation → Knowledge Graph verification

Orchestrates all verification components for comprehensive fact-checking.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import asyncio

from .fact_check_aggregator import fact_check_aggregator
from .entity_linker import entity_linker
from .sparql_generator import sparql_generator
from .kg_verifier import kg_verifier
from .fact_check_queue import fact_check_queue
from .models import VerificationStatus
from .cache_manager import cache_manager, CacheCategory
from .utils import hash_text
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class ProcessingMode(Enum):
    """Verification processing mode."""

    FAST_TRACK = "fast_track"
    """Tier 1 only - cached + API matching"""

    STANDARD = "standard"
    """Tier 1 synchronous"""

    DEEP_ANALYSIS = "deep_analysis"
    """Tier 1 + Tier 2 asynchronous"""


class RealityDistortionResult:
    """Result of reality distortion detection/verification."""

    def __init__(
        self,
        distortion_score: float,
        verification_status: VerificationStatus,
        confidence: float,
        tier_used: int,
        claims: List[Dict[str, Any]],
        verified_claims: List[Dict[str, Any]],
        unverified_claims: List[Dict[str, Any]],
        tier2_pending: bool = False,
        evidence: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize result.

        Args:
            distortion_score: Overall distortion score (0-1)
            verification_status: Aggregated verification status
            confidence: Verification confidence (0-1)
            tier_used: Tier level used (1 or 2)
            claims: All extracted claims
            verified_claims: Successfully verified claims
            unverified_claims: Unverified or false claims
            tier2_pending: Whether Tier 2 verification is pending
            evidence: Supporting evidence
        """
        self.distortion_score = distortion_score
        self.verification_status = verification_status
        self.confidence = confidence
        self.tier_used = tier_used
        self.claims = claims
        self.verified_claims = verified_claims
        self.unverified_claims = unverified_claims
        self.tier2_pending = tier2_pending
        self.evidence = evidence or {}


class RealityDistortionModule:
    """
    Module 4: Reality Distortion Verification.

    Multi-stage verification pipeline:
    1. Check-worthiness scoring (ClaimBuster)
    2. Tier 1: Fast API matching (ClaimBuster + Google Fact Check)
    3. Tier 2: Deep KG verification (Entity Linking + SPARQL + Wikidata/DBpedia)
    4. Result aggregation and scoring
    """

    def __init__(self):
        """Initialize Module 4."""
        self._initialized = False
        self._tier2_enabled = True

    async def initialize(
        self,
        enable_tier2: bool = True,
        start_tier2_workers: bool = False,
        num_workers: int = 4
    ) -> None:
        """
        Initialize verification components.

        Args:
            enable_tier2: Enable Tier 2 deep verification
            start_tier2_workers: Start Kafka workers immediately
            num_workers: Number of Tier 2 workers
        """
        if self._initialized:
            logger.warning("Reality distortion module already initialized")
            return

        try:
            logger.info("🚀 Initializing reality distortion verification...")

            # Initialize Tier 1 components
            await fact_check_aggregator.initialize()

            # Initialize Tier 2 components
            if enable_tier2:
                await entity_linker.initialize()
                await sparql_generator.initialize()
                await kg_verifier.initialize()
                await fact_check_queue.initialize()

                if start_tier2_workers:
                    await fact_check_queue.start_workers(num_workers)

            self._tier2_enabled = enable_tier2
            self._initialized = True

            logger.info("✅ Reality distortion module initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize reality distortion module: {e}", exc_info=True)
            raise

    async def verify_content(
        self,
        text: str,
        mode: ProcessingMode = ProcessingMode.STANDARD,
        tier2_timeout: Optional[float] = None
    ) -> RealityDistortionResult:
        """
        Comprehensive reality distortion verification.

        Args:
            text: Input text to verify
            mode: Processing mode (fast_track/standard/deep_analysis)
            tier2_timeout: Max seconds to wait for Tier 2 results (None = async only)

        Returns:
            RealityDistortionResult
        """
        if not self._initialized:
            await self.initialize()

        logger.info(f"Verifying content (mode={mode.value}): {text[:50]}...")

        # STEP 1: Extract claims from text (simple sentence splitting)
        claims = self._extract_claims(text)

        if not claims:
            logger.debug("No verifiable claims found in text")
            return RealityDistortionResult(
                distortion_score=0.0,
                verification_status=VerificationStatus.UNVERIFIED,
                confidence=1.0,
                tier_used=1,
                claims=[],
                verified_claims=[],
                unverified_claims=[],
                tier2_pending=False
            )

        logger.info(f"Extracted {len(claims)} potential claims")

        # STEP 2: Tier 1 verification (fast API matching)
        tier1_results = await self._tier1_verification(claims)

        # Filter verified vs unverified
        verified = [r for r in tier1_results if r["verification_status"] in [
            VerificationStatus.VERIFIED_TRUE.value,
            VerificationStatus.VERIFIED_FALSE.value,
            VerificationStatus.MIXED.value
        ]]

        unverified = [r for r in tier1_results if r["verification_status"] == VerificationStatus.UNVERIFIED.value]

        # STEP 3: Tier 2 verification for unverified claims (if enabled)
        tier2_pending = False

        if mode == ProcessingMode.DEEP_ANALYSIS and unverified and self._tier2_enabled:
            tier2_results = await self._tier2_verification(
                claims=[u["claim_text"] for u in unverified],
                wait_timeout=tier2_timeout
            )

            # Merge Tier 2 results
            if tier2_results:
                verified.extend(tier2_results)
                # Remove claims that were verified in Tier 2
                verified_claim_texts = {r["claim"] for r in tier2_results}
                unverified = [u for u in unverified if u["claim_text"] not in verified_claim_texts]
            elif tier2_timeout is None:
                # Async mode - results pending
                tier2_pending = True

        # STEP 4: Calculate distortion score
        distortion_score, overall_status, confidence = self._calculate_distortion_score(
            verified=verified,
            unverified=unverified,
            tier2_pending=tier2_pending
        )

        tier_used = 2 if (mode == ProcessingMode.DEEP_ANALYSIS and tier2_results) else 1

        result = RealityDistortionResult(
            distortion_score=distortion_score,
            verification_status=overall_status,
            confidence=confidence,
            tier_used=tier_used,
            claims=tier1_results,
            verified_claims=verified,
            unverified_claims=unverified,
            tier2_pending=tier2_pending,
            evidence={
                "tier1_results": tier1_results,
                "tier2_enabled": self._tier2_enabled,
                "processing_mode": mode.value
            }
        )

        logger.info(
            f"Verification complete: score={distortion_score:.3f}, "
            f"status={overall_status.value}, tier={tier_used}"
        )

        return result

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract potential factual claims from text.

        Simple heuristic: split by sentences and filter.

        Args:
            text: Input text

        Returns:
            List of claim sentences
        """
        import re

        # Split by sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)

        # Filter claims (sentences with facts, not questions or short fragments)
        claims = []

        for sentence in sentences:
            sentence = sentence.strip()

            # Skip if too short
            if len(sentence) < 10:
                continue

            # Skip questions
            if '?' in sentence:
                continue

            # Skip if no verb (heuristic for factual claim)
            if not any(word in sentence.lower() for word in ['é', 'foi', 'são', 'estar', 'ter', 'fazer', 'nascer', 'morrer']):
                continue

            claims.append(sentence)

        return claims

    async def _tier1_verification(
        self,
        claims: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Tier 1: Fast verification via API matching.

        Args:
            claims: List of claims to verify

        Returns:
            List of verification results
        """
        logger.info(f"Tier 1 verification for {len(claims)} claims...")

        # Verify all claims in parallel
        results = await fact_check_aggregator.batch_verify(claims)

        return results

    async def _tier2_verification(
        self,
        claims: List[str],
        wait_timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Tier 2: Deep verification via Knowledge Graphs.

        Args:
            claims: List of claims to verify
            wait_timeout: Max seconds to wait for results (None = async)

        Returns:
            List of verification results
        """
        logger.info(f"Tier 2 verification for {len(claims)} claims...")

        if wait_timeout is None:
            # Async mode: enqueue and return immediately
            for claim in claims:
                await fact_check_queue.enqueue_claim(
                    claim=claim,
                    context={},
                    priority="normal"
                )
            logger.info(f"Enqueued {len(claims)} claims for async Tier 2 verification")
            return []

        # Synchronous mode: enqueue and wait for results
        tasks = []

        for claim in claims:
            await fact_check_queue.enqueue_claim(claim=claim)
            tasks.append(fact_check_queue.get_result(claim=claim, wait_timeout=wait_timeout))

        results = await asyncio.gather(*tasks)

        # Filter None results
        return [r for r in results if r is not None]

    def _calculate_distortion_score(
        self,
        verified: List[Dict[str, Any]],
        unverified: List[Dict[str, Any]],
        tier2_pending: bool
    ) -> tuple:
        """
        Calculate overall distortion score and status.

        Args:
            verified: Verified claims
            unverified: Unverified claims
            tier2_pending: Whether Tier 2 results are pending

        Returns:
            (distortion_score, verification_status, confidence)
        """
        total_claims = len(verified) + len(unverified)

        if total_claims == 0:
            return 0.0, VerificationStatus.UNVERIFIED, 0.0

        # Count verification statuses
        false_count = sum(
            1 for v in verified
            if v.get("verification_status") == VerificationStatus.VERIFIED_FALSE.value
        )

        true_count = sum(
            1 for v in verified
            if v.get("verification_status") == VerificationStatus.VERIFIED_TRUE.value
        )

        mixed_count = sum(
            1 for v in verified
            if v.get("verification_status") == VerificationStatus.MIXED.value
        )

        unverified_count = len(unverified)

        # Calculate distortion score (0-1)
        # High score = high distortion (many false claims)
        false_ratio = false_count / total_claims
        mixed_ratio = mixed_count / total_claims
        unverified_ratio = unverified_count / total_claims

        distortion_score = (
            false_ratio * 1.0 +      # False claims contribute fully
            mixed_ratio * 0.6 +      # Mixed claims contribute partially
            unverified_ratio * 0.4   # Unverified claims contribute less
        )

        # Determine overall status
        if false_count > total_claims * 0.5:
            overall_status = VerificationStatus.VERIFIED_FALSE
        elif true_count > total_claims * 0.7:
            overall_status = VerificationStatus.VERIFIED_TRUE
        elif false_count > 0 or mixed_count > 0:
            overall_status = VerificationStatus.MIXED
        elif unverified_count > 0:
            overall_status = VerificationStatus.UNVERIFIED
        else:
            overall_status = VerificationStatus.VERIFIED_TRUE

        # Calculate confidence
        verified_ratio = len(verified) / total_claims if total_claims > 0 else 0

        if tier2_pending:
            confidence = verified_ratio * 0.7  # Lower confidence when Tier 2 pending
        else:
            confidence = verified_ratio * 0.9 + (1 - verified_ratio) * 0.3

        return distortion_score, overall_status, confidence

    def generate_verification_report(
        self,
        result: RealityDistortionResult
    ) -> str:
        """
        Generate human-readable verification report.

        Args:
            result: RealityDistortionResult

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Reality Distortion Verification Report",
            "",
            f"**Distortion Score**: {result.distortion_score:.2f}/1.00",
            f"**Overall Status**: {result.verification_status.value}",
            f"**Confidence**: {result.confidence:.2f}/1.00",
            f"**Tier Used**: {result.tier_used}",
            "",
            "## Claim Verification Summary",
            "",
            f"- **Total Claims**: {len(result.claims)}",
            f"- **Verified Claims**: {len(result.verified_claims)}",
            f"- **Unverified Claims**: {len(result.unverified_claims)}",
            ""
        ]

        if result.tier2_pending:
            lines.extend([
                "⏳ **Tier 2 Deep Verification Pending**",
                "",
                "Some claims are being verified asynchronously via knowledge graphs. "
                "Results will be available shortly.",
                ""
            ])

        if result.verified_claims:
            lines.extend([
                "## Verified Claims",
                ""
            ])

            for i, claim in enumerate(result.verified_claims, 1):
                status = claim.get("verification_status", "unknown")
                confidence = claim.get("confidence", 0.0)
                claim_text = claim.get("claim_text") or claim.get("claim", "")

                lines.extend([
                    f"### {i}. {status.upper()}",
                    "",
                    f"**Claim**: \"{claim_text[:100]}...\"",
                    f"**Confidence**: {confidence:.2f}",
                    ""
                ])

        if result.unverified_claims:
            lines.extend([
                "## Unverified Claims",
                "",
                "⚠️ The following claims could not be verified:"
                ""
            ])

            for i, claim in enumerate(result.unverified_claims, 1):
                claim_text = claim.get("claim_text", "")
                lines.append(f"{i}. \"{claim_text[:100]}...\"")

        return "\n".join(lines)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

reality_distortion_module = RealityDistortionModule()
