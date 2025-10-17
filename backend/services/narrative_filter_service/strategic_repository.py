"""Repository for strategic patterns and alliances."""

from uuid import UUID

from asyncpg import Pool

from models import Alliance, PatternType, StrategicPattern


class StrategicPatternRepository:
    """Repository for strategic_patterns table."""

    def __init__(self, pool: Pool) -> None:
        """Initialize repository with connection pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def create(self, pattern: StrategicPattern) -> UUID:
        """Create a new strategic pattern.

        Args:
            pattern: StrategicPattern object

        Returns:
            UUID of created record
        """
        query = """
            INSERT INTO strategic_patterns (
                id, pattern_type, agents_involved, detection_timestamp,
                evidence_messages, mutual_information, deception_score,
                inconsistency_score, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                pattern.id,
                pattern.pattern_type.value,
                pattern.agents_involved,
                pattern.detection_timestamp,
                pattern.evidence_messages,
                pattern.mutual_information,
                pattern.deception_score,
                pattern.inconsistency_score,
                pattern.metadata,
            )
            return row["id"]  # type: ignore[return-value]

    async def get_recent_patterns(
        self, pattern_type: PatternType | None = None, hours: int = 24, limit: int = 100
    ) -> list[StrategicPattern]:
        """Get recent strategic patterns.

        Args:
            pattern_type: Optional filter by pattern type
            hours: Number of hours to look back
            limit: Maximum results

        Returns:
            List of StrategicPattern objects
        """
        if pattern_type:
            query = """
                SELECT id, pattern_type, agents_involved, detection_timestamp,
                       evidence_messages, mutual_information, deception_score,
                       inconsistency_score, metadata, created_at
                FROM strategic_patterns
                WHERE pattern_type = $1
                  AND detection_timestamp >= NOW() - INTERVAL '1 hour' * $2
                ORDER BY detection_timestamp DESC
                LIMIT $3
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, pattern_type.value, hours, limit)
        else:
            query = """
                SELECT id, pattern_type, agents_involved, detection_timestamp,
                       evidence_messages, mutual_information, deception_score,
                       inconsistency_score, metadata, created_at
                FROM strategic_patterns
                WHERE detection_timestamp >= NOW() - INTERVAL '1 hour' * $1
                ORDER BY detection_timestamp DESC
                LIMIT $2
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, hours, limit)

        return [
            StrategicPattern(
                id=row["id"],
                pattern_type=PatternType(row["pattern_type"]),
                agents_involved=list(row["agents_involved"]),
                detection_timestamp=row["detection_timestamp"],
                evidence_messages=list(row["evidence_messages"]),
                mutual_information=float(row["mutual_information"]) if row["mutual_information"] else None,
                deception_score=float(row["deception_score"]) if row["deception_score"] else None,
                inconsistency_score=float(row["inconsistency_score"]) if row["inconsistency_score"] else None,
                metadata=dict(row["metadata"]) if row["metadata"] else {},
            )
            for row in rows
        ]

    async def batch_create(self, patterns: list[StrategicPattern]) -> int:
        """Batch create strategic patterns.

        Args:
            patterns: List of StrategicPattern objects

        Returns:
            Number of records created
        """
        query = """
            INSERT INTO strategic_patterns (
                id, pattern_type, agents_involved, detection_timestamp,
                evidence_messages, mutual_information, deception_score,
                inconsistency_score, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        async with self.pool.acquire() as conn:
            await conn.executemany(
                query,
                [
                    (
                        pattern.id,
                        pattern.pattern_type.value,
                        pattern.agents_involved,
                        pattern.detection_timestamp,
                        pattern.evidence_messages,
                        pattern.mutual_information,
                        pattern.deception_score,
                        pattern.inconsistency_score,
                        pattern.metadata,
                    )
                    for pattern in patterns
                ],
            )
            return len(patterns)


class AllianceRepository:
    """Repository for alliances table."""

    def __init__(self, pool: Pool) -> None:
        """Initialize repository with connection pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def upsert(self, alliance: Alliance) -> UUID:
        """Insert or update an alliance.

        Args:
            alliance: Alliance object

        Returns:
            UUID of created/updated record
        """
        query = """
            INSERT INTO alliances (
                id, agent_a, agent_b, strength, first_detected,
                last_activity, interaction_count, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (agent_a, agent_b)
            DO UPDATE SET
                strength = EXCLUDED.strength,
                last_activity = EXCLUDED.last_activity,
                interaction_count = EXCLUDED.interaction_count,
                status = EXCLUDED.status
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                alliance.id,
                alliance.agent_a,
                alliance.agent_b,
                alliance.strength,
                alliance.first_detected,
                alliance.last_activity,
                alliance.interaction_count,
                alliance.status,
            )
            return row["id"]  # type: ignore[return-value]

    async def get_active_alliances(self, agent_id: str | None = None) -> list[Alliance]:
        """Get active alliances.

        Args:
            agent_id: Optional filter by agent

        Returns:
            List of Alliance objects
        """
        if agent_id:
            query = """
                SELECT id, agent_a, agent_b, strength, first_detected,
                       last_activity, interaction_count, status, created_at
                FROM alliances
                WHERE (agent_a = $1 OR agent_b = $1)
                  AND status = 'ACTIVE'
                ORDER BY strength DESC
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, agent_id)
        else:
            query = """
                SELECT id, agent_a, agent_b, strength, first_detected,
                       last_activity, interaction_count, status, created_at
                FROM alliances
                WHERE status = 'ACTIVE'
                ORDER BY strength DESC
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)

        return [
            Alliance(
                id=row["id"],
                agent_a=row["agent_a"],
                agent_b=row["agent_b"],
                strength=float(row["strength"]),
                first_detected=row["first_detected"],
                last_activity=row["last_activity"],
                interaction_count=row["interaction_count"],
                status=row["status"],
            )
            for row in rows
        ]
