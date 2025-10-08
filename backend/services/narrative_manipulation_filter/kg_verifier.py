"""
Knowledge Graph Verifier for Claim Verification.

Executes SPARQL queries against Wikidata and DBpedia to verify factual claims.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from cache_manager import CacheCategory, cache_manager
from config import get_settings
from dbpedia_client import dbpedia_client
from entity_linker import Entity
from models import VerificationStatus
from sparql_generator import SPARQLQuery
from utils import hash_text
from wikidata_client import wikidata_client

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class VerificationResult:
    """Result of knowledge graph verification."""

    claim: str
    """Original claim text"""

    verified: bool
    """Whether claim was verified as TRUE"""

    verification_status: VerificationStatus
    """Detailed verification status"""

    confidence: float
    """Verification confidence (0-1)"""

    verdict: str
    """Human-readable verdict"""

    evidence: Dict[str, Any]
    """Evidence from knowledge graph"""

    sparql_query: str
    """SPARQL query used for verification"""

    kg_source: str
    """Knowledge graph source (wikidata/dbpedia)"""

    actual_value: Optional[str] = None
    """Actual value found in KG"""

    expected_value: Optional[str] = None
    """Expected value from claim"""

    timestamp: datetime = None

    def __post_init__(self):
        """Set default timestamp."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class KnowledgeGraphVerifier:
    """
    Verifies claims against Wikidata and DBpedia knowledge graphs.

    Process:
    1. Execute SPARQL query on Wikidata (primary source)
    2. If no result, fallback to DBpedia
    3. Compare result with expected value from claim
    4. Calculate verification confidence
    """

    def __init__(self):
        """Initialize KG verifier."""
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize knowledge graph clients."""
        if self._initialized:
            return

        await wikidata_client.initialize()
        await dbpedia_client.initialize()

        self._initialized = True
        logger.info("✅ Knowledge graph verifier initialized")

    async def verify_claim(
        self,
        sparql_query: SPARQLQuery,
        use_cache: bool = True,
        fallback_to_dbpedia: bool = True,
    ) -> VerificationResult:
        """
        Verify claim using generated SPARQL query.

        Args:
            sparql_query: Generated SPARQL query object
            use_cache: Whether to use cache
            fallback_to_dbpedia: Try DBpedia if Wikidata fails

        Returns:
            VerificationResult
        """
        if not self._initialized:
            await self.initialize()

        claim = sparql_query.original_claim

        # Check cache
        if use_cache:
            cache_key = f"kg_verify:{hash_text(claim)}"
            cached = await cache_manager.get(CacheCategory.FACTCHECK, cache_key)
            if cached:
                logger.debug(f"KG verification cache hit: {claim[:50]}")
                return VerificationResult(**cached)

        logger.info(f"Verifying claim via KG: {claim}")

        # PRIMARY: Try Wikidata first
        result = await self._verify_on_wikidata(sparql_query)

        # FALLBACK: Try DBpedia if Wikidata failed
        if not result.evidence and fallback_to_dbpedia:
            logger.debug("Wikidata verification failed, trying DBpedia...")
            result = await self._verify_on_dbpedia(sparql_query)

        # Cache result for 30 days
        if use_cache:
            cache_key = f"kg_verify:{hash_text(claim)}"
            cache_data = {
                "claim": result.claim,
                "verified": result.verified,
                "verification_status": (
                    result.verification_status.value
                    if isinstance(result.verification_status, VerificationStatus)
                    else result.verification_status
                ),
                "confidence": result.confidence,
                "verdict": result.verdict,
                "evidence": result.evidence,
                "sparql_query": result.sparql_query,
                "kg_source": result.kg_source,
                "actual_value": result.actual_value,
                "expected_value": result.expected_value,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None,
            }
            await cache_manager.set(CacheCategory.FACTCHECK, cache_key, cache_data)

        logger.info(
            f"KG verification complete: {result.verification_status.value if isinstance(result.verification_status, VerificationStatus) else result.verification_status} "
            f"(confidence={result.confidence:.3f})"
        )

        return result

    async def _verify_on_wikidata(self, sparql_query: SPARQLQuery) -> VerificationResult:
        """Execute SPARQL query on Wikidata."""
        try:
            # Execute query
            results = await wikidata_client.sparql_query(sparql_query.query)

            # Parse results based on query type
            if sparql_query.query_type == "ask":
                verified = results.get("boolean", False)

                if verified:
                    return VerificationResult(
                        claim=sparql_query.original_claim,
                        verified=True,
                        verification_status=VerificationStatus.VERIFIED_TRUE,
                        confidence=0.95,  # High confidence for KG data
                        verdict="TRUE",
                        evidence={"wikidata_result": "confirmed"},
                        sparql_query=sparql_query.query,
                        kg_source="wikidata",
                    )
                else:
                    return VerificationResult(
                        claim=sparql_query.original_claim,
                        verified=False,
                        verification_status=VerificationStatus.VERIFIED_FALSE,
                        confidence=0.90,
                        verdict="FALSE",
                        evidence={"wikidata_result": "not_found"},
                        sparql_query=sparql_query.query,
                        kg_source="wikidata",
                    )

            elif sparql_query.query_type == "select":
                bindings = results.get("results", {}).get("bindings", [])

                if not bindings:
                    # No data found
                    return VerificationResult(
                        claim=sparql_query.original_claim,
                        verified=False,
                        verification_status=VerificationStatus.UNVERIFIED,
                        confidence=0.70,
                        verdict="NO_DATA",
                        evidence={},
                        sparql_query=sparql_query.query,
                        kg_source="wikidata",
                    )

                # Extract actual value(s)
                actual_values = []
                for binding in bindings:
                    value = binding.get("value", {}).get("value", "")
                    label = binding.get("valueLabel", {}).get("value", value)

                    actual_values.append({"value": value, "label": label})

                # Compare with expected value (if provided)
                expected_entity = sparql_query.expected_result

                if expected_entity and isinstance(expected_entity, Entity):
                    # Check if expected entity is in actual values
                    expected_id = expected_entity.wikidata_id

                    matched = any(expected_id in v["value"] for v in actual_values)

                    if matched:
                        return VerificationResult(
                            claim=sparql_query.original_claim,
                            verified=True,
                            verification_status=VerificationStatus.VERIFIED_TRUE,
                            confidence=0.95,
                            verdict="TRUE",
                            evidence={"wikidata_values": actual_values},
                            sparql_query=sparql_query.query,
                            kg_source="wikidata",
                            actual_value=str(actual_values),
                            expected_value=expected_entity.text,
                        )
                    else:
                        return VerificationResult(
                            claim=sparql_query.original_claim,
                            verified=False,
                            verification_status=VerificationStatus.VERIFIED_FALSE,
                            confidence=0.92,
                            verdict="FALSE",
                            evidence={"wikidata_values": actual_values},
                            sparql_query=sparql_query.query,
                            kg_source="wikidata",
                            actual_value=str(actual_values),
                            expected_value=expected_entity.text,
                        )
                else:
                    # No expected value - return found values
                    return VerificationResult(
                        claim=sparql_query.original_claim,
                        verified=True,
                        verification_status=VerificationStatus.VERIFIED_TRUE,
                        confidence=0.85,
                        verdict="DATA_RETRIEVED",
                        evidence={"wikidata_values": actual_values},
                        sparql_query=sparql_query.query,
                        kg_source="wikidata",
                        actual_value=str(actual_values),
                    )

        except Exception as e:
            logger.error(f"Wikidata verification error: {e}", exc_info=True)
            return VerificationResult(
                claim=sparql_query.original_claim,
                verified=False,
                verification_status=VerificationStatus.UNVERIFIED,
                confidence=0.0,
                verdict="ERROR",
                evidence={"error": str(e)},
                sparql_query=sparql_query.query,
                kg_source="wikidata",
            )

    async def _verify_on_dbpedia(self, sparql_query: SPARQLQuery) -> VerificationResult:
        """Execute SPARQL query on DBpedia (fallback)."""
        try:
            # Adapt query for DBpedia (replace wd: prefixes)
            dbpedia_query = self._adapt_query_for_dbpedia(sparql_query.query)

            # Execute query
            results = await dbpedia_client.sparql_query(dbpedia_query)

            # Parse results (similar to Wikidata)
            if sparql_query.query_type == "ask":
                verified = results.get("boolean", False)

                return VerificationResult(
                    claim=sparql_query.original_claim,
                    verified=verified,
                    verification_status=(
                        VerificationStatus.VERIFIED_TRUE if verified else VerificationStatus.VERIFIED_FALSE
                    ),
                    confidence=0.85,  # Slightly lower confidence for DBpedia
                    verdict="TRUE" if verified else "FALSE",
                    evidence={"dbpedia_result": "confirmed" if verified else "not_found"},
                    sparql_query=dbpedia_query,
                    kg_source="dbpedia",
                )

            else:
                bindings = results.get("results", {}).get("bindings", [])

                if not bindings:
                    return VerificationResult(
                        claim=sparql_query.original_claim,
                        verified=False,
                        verification_status=VerificationStatus.UNVERIFIED,
                        confidence=0.60,
                        verdict="NO_DATA",
                        evidence={},
                        sparql_query=dbpedia_query,
                        kg_source="dbpedia",
                    )

                # Extract values
                actual_values = [binding.get("value", {}).get("value", "") for binding in bindings]

                return VerificationResult(
                    claim=sparql_query.original_claim,
                    verified=True,
                    verification_status=VerificationStatus.VERIFIED_TRUE,
                    confidence=0.80,
                    verdict="DATA_RETRIEVED",
                    evidence={"dbpedia_values": actual_values},
                    sparql_query=dbpedia_query,
                    kg_source="dbpedia",
                    actual_value=str(actual_values),
                )

        except Exception as e:
            logger.error(f"DBpedia verification error: {e}", exc_info=True)
            return VerificationResult(
                claim=sparql_query.original_claim,
                verified=False,
                verification_status=VerificationStatus.UNVERIFIED,
                confidence=0.0,
                verdict="ERROR",
                evidence={"error": str(e)},
                sparql_query=sparql_query.query,
                kg_source="dbpedia",
            )

    @staticmethod
    def _adapt_query_for_dbpedia(wikidata_query: str) -> str:
        """
        Adapt Wikidata SPARQL query for DBpedia.

        Replaces Wikidata-specific prefixes and URIs.

        Args:
            wikidata_query: Wikidata SPARQL query

        Returns:
            DBpedia-compatible SPARQL query
        """
        # Basic adaptations (simplified)
        query = wikidata_query

        # Replace Wikidata entity prefix
        query = query.replace("wd:", "dbr:")  # dbr = DBpedia resource

        # Replace Wikidata property prefix
        query = query.replace("wdt:", "dbo:")  # dbo = DBpedia ontology

        # Remove Wikidata-specific SERVICE clauses
        query = query.replace("SERVICE wikibase:label", "# SERVICE removed")

        return query

    async def batch_verify(self, sparql_queries: List[SPARQLQuery]) -> List[VerificationResult]:
        """Verify multiple claims in parallel."""
        import asyncio

        tasks = [self.verify_claim(query) for query in sparql_queries]

        return await asyncio.gather(*tasks)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

kg_verifier = KnowledgeGraphVerifier()
