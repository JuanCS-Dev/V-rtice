"""Database repository for semantic representations."""

from datetime import datetime
from uuid import UUID

import asyncpg
from asyncpg import Pool

from narrative_filter_service.config import settings
from narrative_filter_service.models import IntentClassification, SemanticRepresentation


class SemanticRepository:
    """Repository for semantic_representations table."""

    def __init__(self, pool: Pool) -> None:
        """Initialize repository with connection pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def create(self, representation: SemanticRepresentation) -> UUID:
        """Create a new semantic representation.

        Args:
            representation: SemanticRepresentation object

        Returns:
            UUID of created record
        """
        query = """
            INSERT INTO semantic_representations (
                id, message_id, source_agent_id, timestamp,
                content_embedding, intent_classification, intent_confidence,
                raw_content, provenance_chain
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                representation.id,
                representation.message_id,
                representation.source_agent_id,
                representation.timestamp,
                representation.content_embedding,
                representation.intent_classification.value,
                representation.intent_confidence,
                representation.raw_content,
                representation.provenance_chain,
            )
            return UUID(str(row["id"]))

    async def get_by_message_id(self, message_id: str) -> SemanticRepresentation | None:
        """Get semantic representation by message_id.

        Args:
            message_id: Message ID to lookup

        Returns:
            SemanticRepresentation or None if not found
        """
        query = """
            SELECT id, message_id, source_agent_id, timestamp,
                   content_embedding, intent_classification, intent_confidence,
                   raw_content, provenance_chain, created_at, updated_at
            FROM semantic_representations
            WHERE message_id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, message_id)
            if not row:
                return None

            return SemanticRepresentation(
                id=row["id"],
                message_id=row["message_id"],
                source_agent_id=row["source_agent_id"],
                timestamp=row["timestamp"],
                content_embedding=row["content_embedding"],
                intent_classification=IntentClassification(row["intent_classification"]),
                intent_confidence=float(row["intent_confidence"]),
                raw_content=row["raw_content"],
                provenance_chain=list(row["provenance_chain"]),
                created_at=row["created_at"],
            )

    async def get_by_agent(
        self, agent_id: str, limit: int = 100, since: datetime | None = None
    ) -> list[SemanticRepresentation]:
        """Get semantic representations by agent.

        Args:
            agent_id: Agent ID to filter by
            limit: Maximum number of results
            since: Optional datetime filter (only get messages after this)

        Returns:
            List of SemanticRepresentation objects
        """
        if since:
            query = """
                SELECT id, message_id, source_agent_id, timestamp,
                       content_embedding, intent_classification, intent_confidence,
                       raw_content, provenance_chain, created_at, updated_at
                FROM semantic_representations
                WHERE source_agent_id = $1 AND timestamp > $2
                ORDER BY timestamp DESC
                LIMIT $3
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, agent_id, since, limit)
        else:
            query = """
                SELECT id, message_id, source_agent_id, timestamp,
                       content_embedding, intent_classification, intent_confidence,
                       raw_content, provenance_chain, created_at, updated_at
                FROM semantic_representations
                WHERE source_agent_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, agent_id, limit)

        return [
            SemanticRepresentation(
                id=row["id"],
                message_id=row["message_id"],
                source_agent_id=row["source_agent_id"],
                timestamp=row["timestamp"],
                content_embedding=row["content_embedding"],
                intent_classification=IntentClassification(row["intent_classification"]),
                intent_confidence=float(row["intent_confidence"]),
                raw_content=row["raw_content"],
                provenance_chain=list(row["provenance_chain"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def batch_create(self, representations: list[SemanticRepresentation]) -> int:
        """Batch create semantic representations.

        Args:
            representations: List of SemanticRepresentation objects

        Returns:
            Number of records created
        """
        query = """
            INSERT INTO semantic_representations (
                id, message_id, source_agent_id, timestamp,
                content_embedding, intent_classification, intent_confidence,
                raw_content, provenance_chain
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        async with self.pool.acquire() as conn:
            await conn.executemany(
                query,
                [
                    (
                        rep.id,
                        rep.message_id,
                        rep.source_agent_id,
                        rep.timestamp,
                        rep.content_embedding,
                        rep.intent_classification.value,
                        rep.intent_confidence,
                        rep.raw_content,
                        rep.provenance_chain,
                    )
                    for rep in representations
                ],
            )
            return len(representations)


async def create_pool() -> Pool:
    """Create asyncpg connection pool.

    Returns:
        Connection pool
    """
    return await asyncpg.create_pool(dsn=settings.postgres_dsn, min_size=5, max_size=20)
