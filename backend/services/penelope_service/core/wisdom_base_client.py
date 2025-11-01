"""Wisdom Base Client - PostgreSQL + pgvector for Historical Precedents.

Armazena decisões passadas e permite busca por similaridade.
Sophia Engine aprende com histórico de anomalias e suas resoluções.

Fundamento Bíblico: Provérbios 2:6
"Porque o SENHOR dá a sabedoria; da sua boca vem o conhecimento e o entendimento."

Author: Vértice Platform Team
License: Proprietary
"""

import hashlib
import json
import logging
from typing import Any

import asyncpg
from asyncpg.pool import Pool

logger = logging.getLogger(__name__)


class WisdomBaseClient:
    """PostgreSQL-based wisdom base with pgvector similarity search.

    Stores historical precedents: anomalies, interventions, outcomes.
    Enables Sophia Engine to learn from past decisions.

    Architecture:
    - PostgreSQL with pgvector extension
    - Embeddings using simple feature hashing (768 dims)
    - Cosine similarity search for precedent matching
    - Tracks success/failure of past interventions

    Biblical Principle: Learn from history (Deuteronomy 32:7)
    """

    def __init__(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "penelope_wisdom",
        db_user: str = "penelope",
        db_password: str = "penelope",  # noqa: S107
    ):
        """Initialize Wisdom Base client.

        Args:
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: Database name
            db_user: Database user
            db_password: Database password
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.pool: Pool | None = None

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            logger.info(
                f"✅ Connected to Wisdom Base: {self.db_host}:{self.db_port}/{self.db_name}"
            )

            # Ensure schema exists
            await self._ensure_schema()

        except Exception as e:
            logger.error(f"Failed to connect to Wisdom Base: {e}")
            raise

    async def close(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Wisdom Base connection closed")

    async def _ensure_schema(self) -> None:
        """Ensure database schema exists.

        Creates tables and pgvector extension if needed.
        """
        if not self.pool:
            raise RuntimeError("Connection pool not initialized. Call connect() first.")
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create precedents table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS precedents (
                    precedent_id TEXT PRIMARY KEY,
                    anomaly_id TEXT NOT NULL,
                    service TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity TEXT NOT NULL,

                    -- Anomaly details
                    metrics JSONB,
                    context JSONB,

                    -- Decision details
                    decision TEXT NOT NULL,
                    intervention_level TEXT,
                    reasoning TEXT,

                    -- Outcome details
                    outcome TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    duration_seconds FLOAT,
                    error_message TEXT,

                    -- Embedding for similarity search (768 dimensions)
                    embedding vector(768),

                    -- Metadata
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )

            # Create index for similarity search
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS precedents_embedding_idx
                ON precedents USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

            # Create indices for queries
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS precedents_service_idx ON precedents(service)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS precedents_anomaly_type_idx ON precedents(anomaly_type)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS precedents_created_at_idx ON precedents(created_at DESC)"
            )

            logger.info("✅ Wisdom Base schema ready")

    async def save_precedent(
        self,
        anomaly_id: str,
        service: str,
        anomaly_type: str,
        severity: str,
        metrics: dict[str, Any],
        context: dict[str, Any],
        decision: str,
        intervention_level: str | None,
        reasoning: str,
        outcome: str,
        success: bool,
        duration_seconds: float | None = None,
        error_message: str | None = None,
    ) -> str:
        """Save precedent to wisdom base.

        Args:
            anomaly_id: Anomaly identifier
            service: Service name
            anomaly_type: Type of anomaly
            severity: Severity level (P0, P1, P2, P3)
            metrics: Anomaly metrics
            context: Anomaly context
            decision: Decision made (INTERVENE, OBSERVE, etc.)
            intervention_level: Intervention level if applicable
            reasoning: Why this decision was made
            outcome: What happened (success, failure, rollback, etc.)
            success: Whether intervention succeeded
            duration_seconds: How long intervention took
            error_message: Error message if failed

        Returns:
            precedent_id: Unique precedent ID
        """
        try:
            # Generate precedent ID (hash of key fields)
            precedent_id = self._generate_precedent_id(
                anomaly_id, service, anomaly_type, decision
            )

            # Create embedding from features
            embedding = self._create_embedding(
                service=service,
                anomaly_type=anomaly_type,
                severity=severity,
                metrics=metrics,
                context=context,
            )

            if not self.pool:
                raise RuntimeError(
                    "Connection pool not initialized. Call connect() first."
                )
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO precedents (
                        precedent_id, anomaly_id, service, anomaly_type, severity,
                        metrics, context, decision, intervention_level, reasoning,
                        outcome, success, duration_seconds, error_message, embedding
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    ON CONFLICT (precedent_id) DO UPDATE SET
                        outcome = EXCLUDED.outcome,
                        success = EXCLUDED.success,
                        duration_seconds = EXCLUDED.duration_seconds,
                        error_message = EXCLUDED.error_message,
                        updated_at = NOW()
                    """,
                    precedent_id,
                    anomaly_id,
                    service,
                    anomaly_type,
                    severity,
                    json.dumps(metrics),
                    json.dumps(context),
                    decision,
                    intervention_level,
                    reasoning,
                    outcome,
                    success,
                    duration_seconds,
                    error_message,
                    embedding,
                )

            logger.info(
                f"✅ Saved precedent {precedent_id[:8]} for {service} ({anomaly_type})"
            )
            return precedent_id

        except Exception as e:
            logger.error(f"Failed to save precedent: {e}")
            raise

    async def query_precedents(
        self,
        anomaly_type: str,
        service: str,
        severity: str | None = None,
        metrics: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        similarity_threshold: float = 0.7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Query for similar historical precedents.

        Uses pgvector cosine similarity on embeddings.

        Args:
            anomaly_type: Type of anomaly
            service: Service name
            severity: Severity level (optional)
            metrics: Current anomaly metrics (optional)
            context: Current anomaly context (optional)
            similarity_threshold: Minimum similarity (0-1)
            limit: Max number of results

        Returns:
            precedents: List of similar precedents with similarity scores
        """
        try:
            # Create embedding for query
            query_embedding = self._create_embedding(
                service=service,
                anomaly_type=anomaly_type,
                severity=severity or "P2",
                metrics=metrics or {},
                context=context or {},
            )

            if not self.pool:
                raise RuntimeError(
                    "Connection pool not initialized. Call connect() first."
                )
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        precedent_id,
                        anomaly_id,
                        service,
                        anomaly_type,
                        severity,
                        metrics,
                        context,
                        decision,
                        intervention_level,
                        reasoning,
                        outcome,
                        success,
                        duration_seconds,
                        error_message,
                        created_at,
                        1 - (embedding <=> $1::vector) as similarity
                    FROM precedents
                    WHERE
                        service = $2
                        AND anomaly_type = $3
                        AND (1 - (embedding <=> $1::vector)) >= $4
                    ORDER BY embedding <=> $1::vector
                    LIMIT $5
                    """,
                    query_embedding,
                    service,
                    anomaly_type,
                    similarity_threshold,
                    limit,
                )

            precedents = []
            for row in rows:
                precedents.append(
                    {
                        "precedent_id": row["precedent_id"],
                        "anomaly_id": row["anomaly_id"],
                        "service": row["service"],
                        "anomaly_type": row["anomaly_type"],
                        "severity": row["severity"],
                        "metrics": json.loads(row["metrics"]),
                        "context": json.loads(row["context"]),
                        "decision": row["decision"],
                        "intervention_level": row["intervention_level"],
                        "reasoning": row["reasoning"],
                        "outcome": row["outcome"],
                        "success": row["success"],
                        "duration_seconds": row["duration_seconds"],
                        "error_message": row["error_message"],
                        "created_at": row["created_at"],
                        "similarity": float(row["similarity"]),
                    }
                )

            logger.info(
                f"Found {len(precedents)} similar precedents for {service}/{anomaly_type}"
            )
            return precedents

        except Exception as e:
            logger.error(f"Failed to query precedents: {e}")
            return []

    def _generate_precedent_id(
        self, anomaly_id: str, service: str, anomaly_type: str, decision: str
    ) -> str:
        """Generate unique precedent ID.

        Args:
            anomaly_id: Anomaly identifier
            service: Service name
            anomaly_type: Type of anomaly
            decision: Decision made

        Returns:
            precedent_id: SHA-256 hash
        """
        content = f"{anomaly_id}|{service}|{anomaly_type}|{decision}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _create_embedding(
        self,
        service: str,
        anomaly_type: str,
        severity: str,
        metrics: dict[str, Any],
        context: dict[str, Any],
    ) -> list[float]:
        """Create embedding vector from anomaly features.

        Simple feature hashing approach (768 dimensions).
        Production version should use transformer model.

        Args:
            service: Service name
            anomaly_type: Type of anomaly
            severity: Severity level
            metrics: Anomaly metrics
            context: Anomaly context

        Returns:
            embedding: 768-dimensional vector
        """
        # Combine features into string
        features = [
            f"service:{service}",
            f"type:{anomaly_type}",
            f"severity:{severity}",
        ]

        # Add key metrics
        for key, value in sorted(metrics.items()):
            if isinstance(value, (int, float)):
                # Bin numeric values
                bin_value = int(value / 100) * 100 if value > 100 else int(value)
                features.append(f"metric:{key}:{bin_value}")
            else:
                features.append(f"metric:{key}:{value}")

        # Add context keys
        for key in sorted(context.keys()):
            features.append(f"context:{key}")

        # Hash features to 768 dimensions
        embedding = [0.0] * 768

        for feature in features:
            # Hash feature to dimension index
            hash_value = int(
                hashlib.md5(  # noqa: S324
                    feature.encode(), usedforsecurity=False
                ).hexdigest(),
                16,
            )
            dim = hash_value % 768

            # Increment that dimension
            embedding[dim] += 1.0

        # Normalize to unit vector
        magnitude = sum(x * x for x in embedding) ** 0.5
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding

    async def get_success_rate(
        self, service: str, anomaly_type: str, decision: str
    ) -> dict[str, Any]:
        """Get historical success rate for a decision type.

        Args:
            service: Service name
            anomaly_type: Type of anomaly
            decision: Decision type (INTERVENE, OBSERVE, etc.)

        Returns:
            stats: Success rate and count
        """
        try:
            if not self.pool:
                raise RuntimeError(
                    "Connection pool not initialized. Call connect() first."
                )
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_count,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                        AVG(duration_seconds) as avg_duration
                    FROM precedents
                    WHERE service = $1 AND anomaly_type = $2 AND decision = $3
                    """,
                    service,
                    anomaly_type,
                    decision,
                )

            total = row["total_count"] or 0
            successes = row["success_count"] or 0
            success_rate = (successes / total) if total > 0 else 0.0

            return {
                "total_count": total,
                "success_count": successes,
                "success_rate": success_rate,
                "avg_duration_seconds": (
                    float(row["avg_duration"]) if row["avg_duration"] else None
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get success rate: {e}")
            return {
                "total_count": 0,
                "success_count": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": None,
            }

    def get_stats(self) -> dict[str, Any]:
        """Get wisdom base statistics (for compatibility)."""
        # This is a synchronous method for backward compatibility
        # Real stats should be queried from PostgreSQL
        return {
            "status": "connected" if self.pool else "disconnected",
            "db_host": self.db_host,
            "db_name": self.db_name,
        }
