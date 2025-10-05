"""
Source Reputation Repository for Cognitive Defense System.

Data access layer for source credibility tracking with Bayesian updates.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import SourceReputation, FactCheckCache
from ..database import BaseRepository

logger = logging.getLogger(__name__)


class SourceReputationRepository(BaseRepository):
    """Repository for source reputation management."""

    async def get_by_domain(
        self,
        domain: str
    ) -> Optional[SourceReputation]:
        """
        Get source reputation by domain.

        Args:
            domain: Domain name

        Returns:
            SourceReputation or None
        """
        stmt = select(SourceReputation).where(SourceReputation.domain == domain)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        domain: str,
        newsguard_score: Optional[float] = None,
        newsguard_rating: Optional[str] = None,
        newsguard_nutrition_label: Optional[Dict] = None,
        prior_credibility: float = 0.5,
        alpha: float = 1.0,
        beta: float = 1.0,
        domain_fingerprint: Optional[str] = None
    ) -> SourceReputation:
        """
        Create or update source reputation.

        Args:
            domain: Domain name
            newsguard_score: NewsGuard score (0-100)
            newsguard_rating: NewsGuard categorical rating
            newsguard_nutrition_label: Full nutrition label
            prior_credibility: Initial credibility (0-1)
            alpha: Beta distribution alpha
            beta: Beta distribution beta
            domain_fingerprint: MinHash fingerprint

        Returns:
            Created or updated SourceReputation
        """
        existing = await self.get_by_domain(domain)

        if existing:
            # Update existing
            existing.newsguard_score = newsguard_score or existing.newsguard_score
            existing.newsguard_rating = newsguard_rating or existing.newsguard_rating
            existing.newsguard_last_updated = datetime.utcnow()
            existing.newsguard_nutrition_label = newsguard_nutrition_label or existing.newsguard_nutrition_label
            existing.domain_fingerprint = domain_fingerprint or existing.domain_fingerprint
            existing.last_analyzed = datetime.utcnow()

            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        else:
            # Create new
            source = SourceReputation(
                domain=domain,
                newsguard_score=newsguard_score,
                newsguard_rating=newsguard_rating,
                newsguard_last_updated=datetime.utcnow() if newsguard_score else None,
                newsguard_nutrition_label=newsguard_nutrition_label,
                prior_credibility=prior_credibility,
                posterior_credibility=prior_credibility,
                alpha=alpha,
                beta=beta,
                domain_fingerprint=domain_fingerprint,
                first_seen=datetime.utcnow(),
                last_analyzed=datetime.utcnow()
            )

            await self.add(source)
            await self.session.flush()
            await self.session.refresh(source)
            return source

    async def update_bayesian_parameters(
        self,
        domain: str,
        new_alpha: float,
        new_beta: float,
        is_reliable: bool
    ) -> SourceReputation:
        """
        Update Bayesian credibility parameters.

        Args:
            domain: Domain name
            new_alpha: Updated alpha parameter
            new_beta: Updated beta parameter
            is_reliable: Whether this update is for reliable content

        Returns:
            Updated SourceReputation
        """
        source = await self.get_by_domain(domain)
        if not source:
            raise ValueError(f"Source not found: {domain}")

        # Update Beta parameters
        source.alpha = new_alpha
        source.beta = new_beta

        # Calculate new posterior credibility (mean of Beta distribution)
        source.posterior_credibility = new_alpha / (new_alpha + new_beta)

        # Update statistics
        source.total_analyses += 1
        if is_reliable:
            source.true_content_count += 1
        else:
            source.false_content_count += 1
            source.last_false_content_date = datetime.utcnow()

        source.last_analyzed = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def add_similar_domains(
        self,
        domain: str,
        similar_domains: List[str],
        cluster_id: str
    ) -> SourceReputation:
        """
        Add similar domains for domain hopping detection.

        Args:
            domain: Primary domain
            similar_domains: List of similar domains
            cluster_id: Cluster identifier

        Returns:
            Updated SourceReputation
        """
        source = await self.get_by_domain(domain)
        if not source:
            raise ValueError(f"Source not found: {domain}")

        source.similar_domains = similar_domains
        source.cluster_id = cluster_id

        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def get_cluster_members(
        self,
        cluster_id: str
    ) -> List[SourceReputation]:
        """
        Get all domains in a cluster.

        Args:
            cluster_id: Cluster identifier

        Returns:
            List of SourceReputation in cluster
        """
        stmt = select(SourceReputation).where(
            SourceReputation.cluster_id == cluster_id
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unreliable_domains(
        self,
        threshold: float = 0.3,
        min_analyses: int = 3
    ) -> List[SourceReputation]:
        """
        Get domains with low credibility.

        Args:
            threshold: Maximum posterior credibility (0-1)
            min_analyses: Minimum number of analyses

        Returns:
            List of unreliable SourceReputation
        """
        stmt = select(SourceReputation).where(
            and_(
                SourceReputation.posterior_credibility <= threshold,
                SourceReputation.total_analyses >= min_analyses
            )
        ).order_by(SourceReputation.posterior_credibility.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_top_credible_domains(
        self,
        limit: int = 100,
        min_analyses: int = 5
    ) -> List[SourceReputation]:
        """
        Get most credible domains.

        Args:
            limit: Maximum number of results
            min_analyses: Minimum number of analyses

        Returns:
            List of top credible SourceReputation
        """
        stmt = select(SourceReputation).where(
            SourceReputation.total_analyses >= min_analyses
        ).order_by(
            SourceReputation.posterior_credibility.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_recently_analyzed(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[SourceReputation]:
        """
        Get recently analyzed domains.

        Args:
            hours: Time window in hours
            limit: Maximum results

        Returns:
            List of recent SourceReputation
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        stmt = select(SourceReputation).where(
            SourceReputation.last_analyzed >= since
        ).order_by(
            SourceReputation.last_analyzed.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_pattern(
        self,
        pattern: str
    ) -> List[SourceReputation]:
        """
        Search domains by pattern.

        Args:
            pattern: SQL LIKE pattern (e.g., "%news%")

        Returns:
            Matching SourceReputation
        """
        stmt = select(SourceReputation).where(
            SourceReputation.domain.like(pattern)
        ).order_by(SourceReputation.domain)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics.

        Returns:
            Dict with aggregate statistics
        """
        # Total domains
        total_stmt = select(func.count()).select_from(SourceReputation)
        total_result = await self.session.execute(total_stmt)
        total_domains = total_result.scalar()

        # Credibility distribution
        trusted_stmt = select(func.count()).select_from(SourceReputation).where(
            SourceReputation.posterior_credibility >= 0.7
        )
        trusted_result = await self.session.execute(trusted_stmt)
        trusted_count = trusted_result.scalar()

        unreliable_stmt = select(func.count()).select_from(SourceReputation).where(
            SourceReputation.posterior_credibility <= 0.3
        )
        unreliable_result = await self.session.execute(unreliable_stmt)
        unreliable_count = unreliable_result.scalar()

        # Average credibility
        avg_stmt = select(func.avg(SourceReputation.posterior_credibility))
        avg_result = await self.session.execute(avg_stmt)
        avg_credibility = avg_result.scalar() or 0.0

        # Clusters
        cluster_stmt = select(func.count(func.distinct(SourceReputation.cluster_id))).where(
            SourceReputation.cluster_id.isnot(None)
        )
        cluster_result = await self.session.execute(cluster_stmt)
        total_clusters = cluster_result.scalar()

        return {
            "total_domains": total_domains,
            "trusted_count": trusted_count,
            "unreliable_count": unreliable_count,
            "neutral_count": total_domains - trusted_count - unreliable_count,
            "average_credibility": float(avg_credibility),
            "total_clusters": total_clusters
        }

    async def cache_fact_check(
        self,
        claim_text: str,
        claim_hash: str,
        verification_status: str,
        confidence: float,
        source_api: str,
        api_response: Dict[str, Any],
        expires_in_days: int = 30,
        source_url: Optional[str] = None,
        rating_text: Optional[str] = None
    ) -> FactCheckCache:
        """
        Cache fact-check result.

        Args:
            claim_text: Claim text
            claim_hash: SHA256 hash of claim
            verification_status: Verification status
            confidence: Confidence score (0-1)
            source_api: API source ("google_factcheck", "claimbuster")
            api_response: Full API response
            expires_in_days: Cache expiration (days)
            source_url: Source URL
            rating_text: Rating text

        Returns:
            Created FactCheckCache
        """
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        cache_entry = FactCheckCache(
            claim_text_hash=claim_hash,
            claim_text=claim_text,
            verification_status=verification_status,
            confidence=confidence,
            source_api=source_api,
            source_url=source_url,
            rating_text=rating_text,
            api_response_json=api_response,
            expires_at=expires_at
        )

        await self.add(cache_entry)
        await self.session.flush()
        await self.session.refresh(cache_entry)
        return cache_entry

    async def get_cached_fact_check(
        self,
        claim_hash: str
    ) -> Optional[FactCheckCache]:
        """
        Get cached fact-check result.

        Args:
            claim_hash: SHA256 hash of claim

        Returns:
            FactCheckCache or None
        """
        now = datetime.utcnow()

        stmt = select(FactCheckCache).where(
            and_(
                FactCheckCache.claim_text_hash == claim_hash,
                FactCheckCache.expires_at > now
            )
        )

        result = await self.session.execute(stmt)
        cache_entry = result.scalar_one_or_none()

        if cache_entry:
            # Update hit count and last accessed
            cache_entry.hit_count += 1
            cache_entry.last_accessed = now
            await self.session.flush()

        return cache_entry

    async def cleanup_expired_cache(self) -> int:
        """
        Delete expired fact-check cache entries.

        Returns:
            Number of deleted entries
        """
        now = datetime.utcnow()

        stmt = delete(FactCheckCache).where(
            FactCheckCache.expires_at <= now
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        return result.rowcount
