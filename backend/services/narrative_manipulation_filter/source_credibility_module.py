"""
Source Credibility Assessment Module (Module 1) for Cognitive Defense System.

Orchestrates:
- NewsGuard API integration
- Bayesian credibility scoring with temporal decay
- Domain fingerprinting for hopping detection
- Fact-check aggregation (Google + ClaimBuster)
- Two-tier verification (Tier 1: fast cache/API, Tier 2: deep KG)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .newsguard_client import newsguard_client
from .credibility_scorer import BayesianCredibilityScorer, CredibilityAggregator
from .domain_fingerprinter import domain_fingerprinter
from .fact_check_aggregator import fact_check_aggregator
from .repositories.source_repository import SourceReputationRepository
from .models import SourceCredibilityResult, CredibilityRating
from .utils import extract_domain, hash_text
from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class SourceCredibilityModule:
    """
    Module 1: Source Credibility Assessment.

    Implements multi-layered credibility analysis with Bayesian updates,
    domain hopping detection, and fact-check aggregation.
    """

    def __init__(self):
        """Initialize Module 1."""
        self.bayesian_scorer = BayesianCredibilityScorer(
            prior_alpha=1.0,
            prior_beta=1.0,
            decay_half_life_days=30
        )

    async def assess_source_credibility(
        self,
        text: str,
        source_url: Optional[str],
        db_session: AsyncSession,
        tier2_enabled: bool = True
    ) -> SourceCredibilityResult:
        """
        Assess source credibility with multi-tier analysis.

        Tier 1 (Fast - ~100ms):
        - Cache lookup
        - NewsGuard API
        - Historical Bayesian score
        - Domain fingerprinting

        Tier 2 (Deep - ~2s):
        - Fact-check aggregation (Google + ClaimBuster)
        - Knowledge graph verification (if needed)

        Args:
            text: Content text
            source_url: Source URL (optional)
            db_session: Database session
            tier2_enabled: Enable Tier 2 verification

        Returns:
            SourceCredibilityResult
        """
        tier_used = 1
        domain = extract_domain(source_url) if source_url else None

        if not domain:
            # No domain - return neutral score
            logger.warning("No domain provided, using neutral score")
            return self._neutral_result(source_url)

        # Repository
        repo = SourceReputationRepository(db_session)

        # ========== TIER 1: FAST ANALYSIS ==========

        # 1. Get or create source reputation
        source_reputation = await repo.get_by_domain(domain)

        # 2. NewsGuard API lookup
        newsguard_data = await newsguard_client.get_domain_rating(domain)

        # 3. Domain fingerprinting & hopping detection
        fingerprint = domain_fingerprinter.fingerprint_domain(
            domain,
            metadata={"newsguard_score": newsguard_data.get("overall_score") if newsguard_data else None}
        )
        hopping_analysis = domain_fingerprinter.detect_domain_hopping(domain)

        # 4. Initialize or update source
        if not source_reputation:
            # New domain - initialize from NewsGuard
            if newsguard_data:
                alpha, beta = self.bayesian_scorer.initialize_from_newsguard(
                    newsguard_data["overall_score"]
                )
            else:
                alpha, beta = 1.0, 1.0  # Uniform prior

            source_reputation = await repo.create_or_update(
                domain=domain,
                newsguard_score=newsguard_data.get("overall_score") if newsguard_data else None,
                newsguard_rating=newsguard_data.get("rating") if newsguard_data else None,
                newsguard_nutrition_label=newsguard_data,
                prior_credibility=alpha / (alpha + beta),
                alpha=alpha,
                beta=beta,
                domain_fingerprint=fingerprint
            )

        # 5. Update similar domains from hopping detection
        if hopping_analysis["similar_domains"]:
            similar_domain_names = [d["domain"] for d in hopping_analysis["similar_domains"]]
            await repo.add_similar_domains(
                domain,
                similar_domain_names,
                hopping_analysis["cluster_id"]
            )

        # 6. Calculate Tier 1 credibility
        bayesian_score = self.bayesian_scorer.get_credibility_score(
            source_reputation.alpha,
            source_reputation.beta
        )

        # Aggregate NewsGuard + Bayesian history
        if newsguard_data:
            uncertainty = self.bayesian_scorer.get_uncertainty(
                source_reputation.alpha,
                source_reputation.beta
            )
            confidence = 1.0 - uncertainty

            tier1_score = CredibilityAggregator.aggregate_newsguard_and_history(
                newsguard_score=newsguard_data["overall_score"],
                historical_score=bayesian_score,
                historical_confidence=confidence
            )
        else:
            tier1_score = bayesian_score
            confidence = 0.5

        # 7. Apply penalties
        if source_reputation.false_content_count > 0:
            tier1_score = CredibilityAggregator.penalty_for_false_content(
                tier1_score,
                source_reputation.false_content_count,
                source_reputation.total_analyses,
                severity=0.5
            )

        # 8. Adjust for domain hopping
        if hopping_analysis["is_likely_hopping"]:
            hopping_penalty = 0.2 if hopping_analysis["risk_level"] == "high" else 0.1
            tier1_score *= (1 - hopping_penalty)
            logger.warning(f"Domain hopping detected for {domain}, penalty applied: {hopping_penalty}")

        # ========== TIER 2: DEEP FACT-CHECK VERIFICATION ==========

        fact_check_matches = []
        tier2_score = None

        if tier2_enabled and settings.ENABLE_TIER2_VERIFICATION:
            # Check if Tier 2 is needed
            needs_tier2 = (
                tier1_score < settings.THRESHOLD_CREDIBILITY_LOW or
                tier1_score > settings.THRESHOLD_CREDIBILITY_HIGH or
                source_reputation.total_analyses < 5  # New sources need verification
            )

            if needs_tier2:
                tier_used = 2
                logger.info(f"Tier 2 verification triggered for {domain}")

                # Extract checkable claims
                from .utils import extract_sentences
                sentences = extract_sentences(text)[:5]  # Top 5 sentences

                # Verify claims
                for sentence in sentences:
                    try:
                        verification = await fact_check_aggregator.verify_claim(sentence)
                        if verification["check_worthiness"] >= settings.THRESHOLD_CHECK_WORTHINESS:
                            fact_check_matches.append(verification)

                            # Cache result
                            claim_hash = hash_text(sentence)
                            await repo.cache_fact_check(
                                claim_text=sentence,
                                claim_hash=claim_hash,
                                verification_status=verification["verification_status"],
                                confidence=verification["confidence"],
                                source_api="google_factcheck",
                                api_response=verification,
                                source_url=source_url
                            )
                    except Exception as e:
                        logger.error(f"Fact-check error: {e}")

                # Aggregate fact-check results
                if fact_check_matches:
                    false_claims = sum(
                        1 for fc in fact_check_matches
                        if fc["verification_status"] == "verified_false"
                    )
                    total_claims = len(fact_check_matches)

                    # Tier 2 score based on fact-checks
                    tier2_score = 1.0 - (false_claims / total_claims) if total_claims > 0 else tier1_score

                    # Combine Tier 1 + Tier 2 (weighted average)
                    final_score = tier1_score * 0.4 + tier2_score * 0.6
                else:
                    final_score = tier1_score
            else:
                final_score = tier1_score
        else:
            final_score = tier1_score

        # ========== FINAL ASSESSMENT ==========

        # Convert to 0-100 scale
        credibility_score_100 = final_score * 100

        # Determine rating
        uncertainty = self.bayesian_scorer.get_uncertainty(
            source_reputation.alpha,
            source_reputation.beta
        )
        rating = self.bayesian_scorer.categorize_credibility(final_score, uncertainty)

        # Build result
        result = SourceCredibilityResult(
            domain=domain,
            credibility_score=credibility_score_100,
            rating=rating,
            # NewsGuard 9 criteria (normalized)
            does_not_repeatedly_publish_false_content=newsguard_data["criteria_scores"].get("does_not_repeatedly_publish_false_content", 0.5) if newsguard_data else 0.5,
            gathers_and_presents_info_responsibly=newsguard_data["criteria_scores"].get("gathers_and_presents_info_responsibly", 0.5) if newsguard_data else 0.5,
            regularly_corrects_errors=newsguard_data["criteria_scores"].get("regularly_corrects_errors", 0.5) if newsguard_data else 0.5,
            handles_difference_between_news_opinion=newsguard_data["criteria_scores"].get("handles_difference_between_news_opinion", 0.5) if newsguard_data else 0.5,
            avoids_deceptive_headlines=newsguard_data["criteria_scores"].get("avoids_deceptive_headlines", 0.5) if newsguard_data else 0.5,
            website_discloses_ownership=newsguard_data["criteria_scores"].get("website_discloses_ownership", 0.5) if newsguard_data else 0.5,
            clearly_labels_advertising=newsguard_data["criteria_scores"].get("clearly_labels_advertising", 0.5) if newsguard_data else 0.5,
            reveals_whos_in_charge=newsguard_data["criteria_scores"].get("reveals_whos_in_charge", 0.5) if newsguard_data else 0.5,
            provides_names_of_content_creators=newsguard_data["criteria_scores"].get("provides_names_of_content_creators", 0.5) if newsguard_data else 0.5,
            # Additional signals
            newsguard_nutrition_label=newsguard_data,
            historical_reliability=bayesian_score,
            domain_fingerprint=fingerprint,
            similar_domains=[d["domain"] for d in hopping_analysis["similar_domains"]],
            fact_check_matches=[
                {
                    "claim": fc["claim_text"],
                    "status": fc["verification_status"],
                    "confidence": fc["confidence"],
                    "sources": fc.get("sources", [])
                }
                for fc in fact_check_matches
            ],
            tier_used=tier_used
        )

        logger.info(
            f"Source credibility assessed: {domain} = {credibility_score_100:.1f} "
            f"({rating.value}, tier {tier_used})"
        )

        return result

    def _neutral_result(self, source_url: Optional[str]) -> SourceCredibilityResult:
        """Generate neutral result when domain is unavailable."""
        return SourceCredibilityResult(
            domain=source_url or "unknown",
            credibility_score=50.0,
            rating=CredibilityRating.PROCEED_WITH_CAUTION,
            does_not_repeatedly_publish_false_content=0.5,
            gathers_and_presents_info_responsibly=0.5,
            regularly_corrects_errors=0.5,
            handles_difference_between_news_opinion=0.5,
            avoids_deceptive_headlines=0.5,
            website_discloses_ownership=0.5,
            clearly_labels_advertising=0.5,
            reveals_whos_in_charge=0.5,
            provides_names_of_content_creators=0.5,
            historical_reliability=0.5,
            tier_used=1
        )

    async def update_with_feedback(
        self,
        domain: str,
        is_reliable: bool,
        db_session: AsyncSession
    ) -> None:
        """
        Update source credibility with user/automated feedback.

        Args:
            domain: Domain name
            is_reliable: Whether content was reliable
            db_session: Database session
        """
        repo = SourceReputationRepository(db_session)
        source = await repo.get_by_domain(domain)

        if not source:
            logger.warning(f"Cannot update feedback for unknown domain: {domain}")
            return

        # Bayesian update
        new_alpha, new_beta = self.bayesian_scorer.update_with_observation(
            alpha=source.alpha,
            beta=source.beta,
            is_reliable=is_reliable,
            timestamp=datetime.utcnow(),
            weight=1.0
        )

        # Persist update
        await repo.update_bayesian_parameters(
            domain=domain,
            new_alpha=new_alpha,
            new_beta=new_beta,
            is_reliable=is_reliable
        )

        await db_session.commit()

        logger.info(
            f"Source credibility updated: {domain}, reliable={is_reliable}, "
            f"posterior={new_alpha / (new_alpha + new_beta):.3f}"
        )


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

source_credibility_module = SourceCredibilityModule()
