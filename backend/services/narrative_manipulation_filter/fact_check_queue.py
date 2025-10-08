"""
Fact-Check Queue for Asynchronous Tier 2 Verification.

Kafka-based queue system for deep verification:
- Producer: Enqueues claims that couldn't be verified in Tier 1
- Consumer: Worker pool for entity linking + KG verification
- Result aggregator: Caches and publishes verification results
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from cache_manager import CacheCategory, cache_manager
from config import get_settings
from entity_linker import entity_linker
from kafka_client import kafka_client
from kg_verifier import kg_verifier
from sparql_generator import sparql_generator
from utils import hash_text

logger = logging.getLogger(__name__)

settings = get_settings()


class FactCheckQueue:
    """
    Kafka-based asynchronous queue for Tier 2 deep verification.

    Topics:
    - claims_to_verify: Claims pending deep verification
    - verification_results: Completed verification results
    - verification_errors: Failed verification attempts

    Flow:
    1. Tier 1 publishes unverified claims to 'claims_to_verify'
    2. Worker pool consumes claims
    3. Each worker: entity linking → SPARQL generation → KG verification
    4. Results published to 'verification_results' topic
    5. Aggregator caches results and notifies subscribers
    """

    TOPIC_CLAIMS = "claims_to_verify"
    TOPIC_RESULTS = "verification_results"
    TOPIC_ERRORS = "verification_errors"

    def __init__(self):
        """Initialize fact-check queue."""
        self._initialized = False
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False

    async def initialize(self) -> None:
        """Initialize Kafka client and create topics."""
        if self._initialized:
            return

        # Initialize Kafka client
        await kafka_client.initialize()

        # Create topics if they don't exist
        await kafka_client.create_topic(self.TOPIC_CLAIMS, num_partitions=4)
        await kafka_client.create_topic(self.TOPIC_RESULTS, num_partitions=2)
        await kafka_client.create_topic(self.TOPIC_ERRORS, num_partitions=1)

        # Initialize verification components
        await entity_linker.initialize()
        await sparql_generator.initialize()
        await kg_verifier.initialize()

        self._initialized = True
        logger.info("✅ Fact-check queue initialized")

    async def enqueue_claim(
        self,
        claim: str,
        context: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
    ) -> bool:
        """
        Enqueue claim for Tier 2 deep verification.

        Args:
            claim: Claim text
            context: Additional context metadata
            priority: Priority level (high/normal/low)

        Returns:
            Success status
        """
        if not self._initialized:
            await self.initialize()

        try:
            message = {
                "claim": claim,
                "context": context or {},
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
                "claim_hash": hash_text(claim),
            }

            # Publish to Kafka
            await kafka_client.publish(
                topic=self.TOPIC_CLAIMS,
                message=message,
                key=hash_text(claim),  # Ensures same claim goes to same partition
            )

            logger.info(f"Enqueued claim for Tier 2 verification: {claim[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to enqueue claim: {e}", exc_info=True)
            return False

    async def start_workers(self, num_workers: int = 4) -> None:
        """
        Start worker pool for consuming and processing claims.

        Args:
            num_workers: Number of concurrent workers
        """
        if not self._initialized:
            await self.initialize()

        if self._running:
            logger.warning("Workers already running")
            return

        self._running = True

        # Start worker tasks
        for worker_id in range(num_workers):
            task = asyncio.create_task(self._worker(worker_id))
            self._worker_tasks.append(task)

        logger.info(f"✅ Started {num_workers} fact-check workers")

    async def stop_workers(self) -> None:
        """Stop all workers gracefully."""
        if not self._running:
            return

        self._running = False

        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()

        # Wait for cancellation
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()

        logger.info("✅ Stopped all fact-check workers")

    async def _worker(self, worker_id: int) -> None:
        """
        Worker process for consuming and verifying claims.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")

        try:
            # Subscribe to claims topic
            async for message in kafka_client.consume(topic=self.TOPIC_CLAIMS, group_id="fact_check_workers"):
                if not self._running:
                    break

                try:
                    # Parse message
                    data = message["value"]

                    claim = data["claim"]
                    context = data.get("context", {})
                    claim_hash = data.get("claim_hash")

                    logger.info(f"Worker {worker_id} processing: {claim[:50]}...")

                    # STEP 1: Generate SPARQL query
                    sparql_query = await sparql_generator.generate_from_claim(
                        claim=claim,
                        query_type="ask",  # Boolean verification
                    )

                    if not sparql_query:
                        # Could not generate query
                        await self._publish_error(
                            claim=claim,
                            error="Failed to generate SPARQL query",
                            worker_id=worker_id,
                        )
                        continue

                    # STEP 2: Verify via Knowledge Graph
                    result = await kg_verifier.verify_claim(
                        sparql_query=sparql_query,
                        use_cache=True,
                        fallback_to_dbpedia=True,
                    )

                    # STEP 3: Publish result
                    await self._publish_result(claim=claim, result=result, context=context, worker_id=worker_id)

                    # STEP 4: Cache result
                    await self._cache_result(claim_hash, result)

                    logger.info(
                        f"Worker {worker_id} completed: {claim[:50]} "
                        f"→ {result.verdict} (confidence={result.confidence:.3f})"
                    )

                except Exception as e:
                    logger.error(f"Worker {worker_id} processing error: {e}", exc_info=True)

                    await self._publish_error(
                        claim=data.get("claim", "unknown"),
                        error=str(e),
                        worker_id=worker_id,
                    )

        except asyncio.CancelledError:
            logger.info(f"Worker {worker_id} cancelled")
        except Exception as e:
            logger.error(f"Worker {worker_id} fatal error: {e}", exc_info=True)
        finally:
            logger.info(f"Worker {worker_id} stopped")

    async def _publish_result(self, claim: str, result: Any, context: Dict[str, Any], worker_id: int) -> None:
        """Publish verification result to results topic."""
        message = {
            "claim": claim,
            "verified": result.verified,
            "verification_status": (
                result.verification_status.value
                if hasattr(result.verification_status, "value")
                else str(result.verification_status)
            ),
            "confidence": result.confidence,
            "verdict": result.verdict,
            "evidence": result.evidence,
            "kg_source": result.kg_source,
            "actual_value": result.actual_value,
            "expected_value": result.expected_value,
            "context": context,
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat(),
            "tier": 2,
        }

        await kafka_client.publish(topic=self.TOPIC_RESULTS, message=message, key=hash_text(claim))

        logger.debug(f"Published result for: {claim[:50]}")

    async def _publish_error(self, claim: str, error: str, worker_id: int) -> None:
        """Publish verification error to errors topic."""
        message = {
            "claim": claim,
            "error": error,
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        await kafka_client.publish(topic=self.TOPIC_ERRORS, message=message, key=hash_text(claim))

        logger.debug(f"Published error for: {claim[:50]}")

    async def _cache_result(self, claim_hash: str, result: Any) -> None:
        """Cache verification result."""
        cache_key = f"tier2_result:{claim_hash}"

        cache_data = {
            "claim": result.claim,
            "verified": result.verified,
            "verification_status": (
                result.verification_status.value
                if hasattr(result.verification_status, "value")
                else str(result.verification_status)
            ),
            "confidence": result.confidence,
            "verdict": result.verdict,
            "evidence": result.evidence,
            "kg_source": result.kg_source,
            "actual_value": result.actual_value,
            "expected_value": result.expected_value,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None,
        }

        await cache_manager.set(category=CacheCategory.FACTCHECK, key=cache_key, value=cache_data)

    async def get_result(self, claim: str, wait_timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Get verification result for claim.

        Args:
            claim: Claim text
            wait_timeout: Max seconds to wait for result (None = check cache only)

        Returns:
            Verification result dict or None
        """
        claim_hash = hash_text(claim)

        # Check cache first
        cache_key = f"tier2_result:{claim_hash}"
        cached = await cache_manager.get(CacheCategory.FACTCHECK, cache_key)

        if cached:
            return cached

        # If wait_timeout specified, subscribe to results topic
        if wait_timeout is not None:
            logger.info(f"Waiting for result (timeout={wait_timeout}s): {claim[:50]}")

            start_time = asyncio.get_event_loop().time()

            async for message in kafka_client.consume(topic=self.TOPIC_RESULTS, group_id=f"result_waiter_{claim_hash}"):
                data = message["value"]

                if hash_text(data["claim"]) == claim_hash:
                    logger.info(f"Received result for: {claim[:50]}")
                    return data

                # Check timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > wait_timeout:
                    logger.warning(f"Result wait timeout for: {claim[:50]}")
                    break

        return None

    @asynccontextmanager
    async def worker_context(self, num_workers: int = 4):
        """
        Context manager for worker lifecycle.

        Usage:
            async with queue.worker_context(num_workers=4):
                # Workers running
                await asyncio.sleep(3600)
            # Workers stopped
        """
        await self.start_workers(num_workers)
        try:
            yield
        finally:
            await self.stop_workers()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

fact_check_queue = FactCheckQueue()
