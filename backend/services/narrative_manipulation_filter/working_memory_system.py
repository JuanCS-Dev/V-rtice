"""
Working Memory System for Cognitive Defense (Prefrontal Cortex).

Multi-tiered memory system for context management:
- L1 Cache (Redis): Hot data, <1ms latency
- L2 Storage (PostgreSQL): Historical data, <100ms
- L3 Graph (Seriema): Relationship data, <500ms

Data stored:
- Analysis history (per source, per claim)
- Source reputation profiles
- Verified claims cache
- Argumentation graphs
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import asyncio

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from db_models import SourceProfile, AnalysisRecord, VerifiedClaim
from cache_manager import cache_manager, CacheCategory
from seriema_graph_client import seriema_graph_client
from utils import hash_text
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class SourceReputation:
    """Source reputation metadata."""

    domain: str
    score: float
    analyses_count: int
    manipulation_flags: int = 0
    last_updated: Optional[datetime] = None


@dataclass
class AnalysisContext:
    """Context for current analysis."""

    source_domain: str
    source_reputation: SourceReputation
    recent_analyses: List[Dict[str, Any]]
    related_arguments: List[Dict[str, Any]]
    timestamp: datetime


class WorkingMemorySystem:
    """
    Multi-tiered memory system for context management.

    Mimics prefrontal cortex working memory:
    - Maintains temporary information storage
    - Provides context for ongoing tasks
    - Enables information manipulation
    - Buffers results for quick access
    """

    def __init__(self):
        """Initialize working memory system."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize memory layers."""
        if self._initialized:
            return

        # Ensure database tables exist
        # (tables created via db_models.py and Alembic migrations)

        # Initialize Seriema Graph client
        await seriema_graph_client.initialize()

        self._initialized = True
        logger.info("✅ Working memory system initialized")

    async def load_context(
        self,
        content: str,
        source_info: Dict[str, Any]
    ) -> AnalysisContext:
        """
        Load relevant context for current analysis.

        Parallel queries:
        - Source reputation from PostgreSQL
        - Recent analyses from Redis
        - Related arguments from Seriema Graph

        Args:
            content: Content being analyzed
            source_info: Source metadata (url, domain, etc.)

        Returns:
            AnalysisContext with loaded data
        """
        if not self._initialized:
            await self.initialize()

        source_domain = self._extract_domain(source_info.get("url", ""))

        logger.debug(f"Loading context for domain: {source_domain}")

        # Parallel context loading (3 layers)
        reputation, recent_analyses, related_args = await asyncio.gather(
            self._load_source_reputation(source_domain),
            self._load_recent_analyses(source_domain),
            self._load_related_arguments(content),
            return_exceptions=True
        )

        # Handle exceptions
        if isinstance(reputation, Exception):
            logger.warning(f"Failed to load reputation: {reputation}")
            reputation = SourceReputation(domain=source_domain, score=0.5, analyses_count=0)

        if isinstance(recent_analyses, Exception):
            logger.warning(f"Failed to load recent analyses: {recent_analyses}")
            recent_analyses = []

        if isinstance(related_args, Exception):
            logger.warning(f"Failed to load related arguments: {related_args}")
            related_args = []

        context = AnalysisContext(
            source_domain=source_domain,
            source_reputation=reputation,
            recent_analyses=recent_analyses,
            related_arguments=related_args,
            timestamp=datetime.utcnow()
        )

        logger.info(
            f"Context loaded: reputation={reputation.score:.2f}, "
            f"recent={len(recent_analyses)}, related={len(related_args)}"
        )

        return context

    async def store_analysis(
        self,
        report: Dict[str, Any]
    ) -> None:
        """
        Persist analysis results across all memory layers.

        Actions:
        - Cache report in Redis (7 day TTL)
        - Store in PostgreSQL for historical analysis
        - Update source reputation profile
        - Store argumentation graph in Seriema (if arguments present)

        Args:
            report: Analysis report dict
        """
        if not self._initialized:
            await self.initialize()

        content_hash = report.get("content_hash") or hash_text(report.get("content", ""))
        source_domain = report.get("source_domain", "unknown")

        logger.debug(f"Storing analysis for {source_domain}")

        # L1: Redis cache (fast access)
        await self._cache_analysis(content_hash, source_domain, report)

        # L2: PostgreSQL (historical data)
        await self._store_analysis_record(content_hash, report)

        # L3: Seriema Graph (argumentation networks)
        if report.get("arguments"):
            await self._store_argumentation_graph(report)

        # Update source profile
        await self._update_source_profile(source_domain, report)

        logger.info(f"Analysis stored: {content_hash[:16]}... (domain={source_domain})")

    async def _load_source_reputation(self, domain: str) -> SourceReputation:
        """
        Load historical reputation from PostgreSQL.

        Args:
            domain: Source domain

        Returns:
            SourceReputation
        """
        async with get_db_session() as session:
            result = await session.execute(
                select(SourceProfile).where(SourceProfile.domain == domain)
            )

            profile = result.scalar_one_or_none()

            if not profile:
                # Unknown domain - neutral reputation
                return SourceReputation(
                    domain=domain,
                    score=0.5,
                    analyses_count=0,
                    manipulation_flags=0,
                    last_updated=None
                )

            return SourceReputation(
                domain=domain,
                score=profile.avg_credibility,
                analyses_count=profile.total_analyses,
                manipulation_flags=profile.manipulation_flags,
                last_updated=profile.updated_at
            )

    async def _load_recent_analyses(
        self,
        domain: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Load recent analyses from Redis cache.

        Args:
            domain: Source domain
            limit: Max number of analyses to return

        Returns:
            List of recent analysis dicts
        """
        # Query Redis for analysis keys matching domain
        cache_key_pattern = f"analysis:{domain}:*"

        # Get all matching keys (simplified - in production use SCAN)
        analyses = []

        # Try to get cached analyses list
        cached_list_key = f"recent_analyses:{domain}"
        cached_list = await cache_manager.get(CacheCategory.ANALYSIS, cached_list_key)

        if cached_list:
            return cached_list[:limit]

        # If no cached list, query PostgreSQL
        async with get_db_session() as session:
            result = await session.execute(
                select(AnalysisRecord)
                .where(AnalysisRecord.source_domain == domain)
                .order_by(AnalysisRecord.timestamp.desc())
                .limit(limit)
            )

            records = result.scalars().all()

            analyses = [
                {
                    "content_hash": r.content_hash,
                    "manipulation_score": r.manipulation_score,
                    "credibility_score": r.credibility_score,
                    "emotional_score": r.emotional_score,
                    "fallacy_count": r.fallacy_count,
                    "verification_result": r.verification_result,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None
                }
                for r in records
            ]

            # Cache the list for 1 hour
            if analyses:
                await cache_manager.set(
                    CacheCategory.ANALYSIS,
                    cached_list_key,
                    analyses
                )

        return analyses

    async def _load_related_arguments(
        self,
        content: str,
        similarity_threshold: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Load semantically similar arguments from Seriema Graph.

        Args:
            content: Content text
            similarity_threshold: Min cosine similarity
            limit: Max number of arguments to return

        Returns:
            List of related argument dicts
        """
        # This is a simplified version - in production, use vector embeddings
        # For now, return empty list (graph queries can be added later)

        # Note: Full implementation would:
        # 1. Compute content embedding (sentence-transformers)
        # 2. Query Seriema for similar argument nodes (vector similarity)
        # 3. Return top matches above threshold

        return []

    async def _cache_analysis(
        self,
        content_hash: str,
        source_domain: str,
        report: Dict[str, Any]
    ) -> None:
        """Cache analysis in Redis (L1)."""
        cache_key = f"analysis:{source_domain}:{content_hash}"

        await cache_manager.set(
            CacheCategory.ANALYSIS,
            cache_key,
            report
        )

        logger.debug(f"Cached analysis: {cache_key}")

    async def _store_analysis_record(
        self,
        content_hash: str,
        report: Dict[str, Any]
    ) -> None:
        """Store analysis in PostgreSQL (L2)."""
        async with get_db_session() as session:
            record = AnalysisRecord(
                content_hash=content_hash,
                source_domain=report.get("source_domain", "unknown"),
                manipulation_score=report.get("manipulation_score", 0.0),
                credibility_score=report.get("credibility_score", 0.5),
                emotional_score=report.get("emotional_score", 0.0),
                fallacy_count=len(report.get("fallacies", [])),
                verification_result=report.get("verification_result", "unverified"),
                full_report=report,
                timestamp=datetime.utcnow()
            )

            session.add(record)
            await session.commit()

            logger.debug(f"Stored analysis record: {content_hash[:16]}...")

    async def _store_argumentation_graph(
        self,
        report: Dict[str, Any]
    ) -> None:
        """Store argumentation graph in Seriema (L3)."""
        # This would store argumentation frameworks in Seriema Graph
        # Implementation depends on Seriema Graph client capabilities

        # For now, log intent
        logger.debug("Argumentation graph storage (Seriema integration pending)")

    async def _update_source_profile(
        self,
        domain: str,
        report: Dict[str, Any]
    ) -> None:
        """
        Update source reputation profile.

        Args:
            domain: Source domain
            report: Analysis report
        """
        async with get_db_session() as session:
            # Get or create profile
            result = await session.execute(
                select(SourceProfile).where(SourceProfile.domain == domain)
            )

            profile = result.scalar_one_or_none()

            manipulation_score = report.get("manipulation_score", 0.0)
            credibility_score = report.get("credibility_score", 0.5)

            if not profile:
                # Create new profile
                profile = SourceProfile(
                    domain=domain,
                    avg_credibility=credibility_score,
                    total_analyses=1,
                    manipulation_flags=1 if manipulation_score > 0.7 else 0,
                    last_analysis=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                session.add(profile)
            else:
                # Update existing profile (running average)
                total = profile.total_analyses
                new_total = total + 1

                # Running average for credibility
                new_avg_cred = (
                    (profile.avg_credibility * total + credibility_score) / new_total
                )

                # Increment manipulation flags if high score
                new_manip_flags = profile.manipulation_flags
                if manipulation_score > 0.7:
                    new_manip_flags += 1

                # Update
                await session.execute(
                    update(SourceProfile)
                    .where(SourceProfile.domain == domain)
                    .values(
                        avg_credibility=new_avg_cred,
                        total_analyses=new_total,
                        manipulation_flags=new_manip_flags,
                        last_analysis=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                )

            await session.commit()

            logger.debug(f"Updated source profile: {domain}")

    @staticmethod
    def _extract_domain(url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL or domain

        Returns:
            Domain string
        """
        if not url:
            return "unknown"

        # Remove protocol
        url = url.replace("https://", "").replace("http://", "")

        # Remove path
        domain = url.split("/")[0]

        # Remove www
        domain = domain.replace("www.", "")

        return domain

    async def get_source_statistics(
        self,
        domain: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a source.

        Args:
            domain: Source domain

        Returns:
            Statistics dict
        """
        async with get_db_session() as session:
            # Get profile
            result = await session.execute(
                select(SourceProfile).where(SourceProfile.domain == domain)
            )

            profile = result.scalar_one_or_none()

            if not profile:
                return {
                    "domain": domain,
                    "found": False
                }

            # Get recent analysis stats
            result = await session.execute(
                select(
                    func.avg(AnalysisRecord.manipulation_score).label("avg_manipulation"),
                    func.avg(AnalysisRecord.credibility_score).label("avg_credibility"),
                    func.avg(AnalysisRecord.emotional_score).label("avg_emotional"),
                    func.count(AnalysisRecord.id).label("total_analyses")
                )
                .where(AnalysisRecord.source_domain == domain)
            )

            stats = result.one()

            return {
                "domain": domain,
                "found": True,
                "avg_credibility": float(profile.avg_credibility),
                "total_analyses": profile.total_analyses,
                "manipulation_flags": profile.manipulation_flags,
                "last_analysis": profile.last_analysis.isoformat() if profile.last_analysis else None,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "recent_stats": {
                    "avg_manipulation": float(stats.avg_manipulation or 0),
                    "avg_credibility": float(stats.avg_credibility or 0),
                    "avg_emotional": float(stats.avg_emotional or 0),
                    "total": int(stats.total_analyses or 0)
                }
            }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

working_memory = WorkingMemorySystem()
