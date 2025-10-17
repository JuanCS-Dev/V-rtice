"""Repository for verdicts."""

from uuid import UUID

from asyncpg import Pool

from narrative_filter_service.models import Severity, Verdict, VerdictCategory, VerdictStatus


class VerdictRepository:
    """Repository for verdicts table."""

    def __init__(self, pool: Pool) -> None:
        """Initialize repository with connection pool.

        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    async def create(self, verdict: Verdict) -> UUID:
        """Create a new verdict.

        Args:
            verdict: Verdict object

        Returns:
            UUID of created record
        """
        query = """
            INSERT INTO verdicts (
                id, timestamp, category, severity, title,
                agents_involved, target, evidence_chain, confidence,
                recommended_action, status, color
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                verdict.id,
                verdict.timestamp,
                verdict.category.value,
                verdict.severity.value,
                verdict.title,
                verdict.agents_involved,
                verdict.target,
                verdict.evidence_chain,
                verdict.confidence,
                verdict.recommended_action,
                verdict.status.value,
                verdict.color,
            )
            return UUID(str(row["id"]))

    async def get_active_verdicts(
        self, severity: Severity | None = None, category: VerdictCategory | None = None, limit: int = 100
    ) -> list[Verdict]:
        """Get active verdicts with optional filters.

        Args:
            severity: Optional severity filter
            category: Optional category filter
            limit: Maximum results

        Returns:
            List of Verdict objects
        """
        conditions = ["status = 'ACTIVE'"]
        params: list[str | int] = []
        param_count = 0

        if severity:
            param_count += 1
            conditions.append(f"severity = ${param_count}")
            params.append(severity.value)

        if category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(category.value)

        param_count += 1
        params.append(limit)

        where_clause = " AND ".join(conditions)
        query = f"""
            SELECT id, timestamp, category, severity, title,
                   agents_involved, target, evidence_chain, confidence,
                   recommended_action, status, mitigation_command_id, color, created_at
            FROM verdicts
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${param_count}
        """

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        return [
            Verdict(
                id=row["id"],
                timestamp=row["timestamp"],
                category=VerdictCategory(row["category"]),
                severity=Severity(row["severity"]),
                title=row["title"],
                agents_involved=list(row["agents_involved"]),
                target=row["target"],
                evidence_chain=list(row["evidence_chain"]),
                confidence=float(row["confidence"]),
                recommended_action=row["recommended_action"],
                status=VerdictStatus(row["status"]),
                mitigation_command_id=row["mitigation_command_id"],
                # color é property computada
            )
            for row in rows
        ]

    async def update_status(self, verdict_id: UUID, status: VerdictStatus, command_id: UUID | None = None) -> bool:
        """Update verdict status.

        Args:
            verdict_id: Verdict UUID
            status: New status
            command_id: Optional mitigation command ID

        Returns:
            True if updated
        """
        query = """
            UPDATE verdicts
            SET status = $1, mitigation_command_id = $2
            WHERE id = $3
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, status.value, command_id, verdict_id)
            return bool(result != "UPDATE 0")

    async def batch_create(self, verdicts: list[Verdict]) -> int:
        """Batch create verdicts.

        Args:
            verdicts: List of Verdict objects

        Returns:
            Number of records created
        """
        query = """
            INSERT INTO verdicts (
                id, timestamp, category, severity, title,
                agents_involved, target, evidence_chain, confidence,
                recommended_action, status, color
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """

        async with self.pool.acquire() as conn:
            await conn.executemany(
                query,
                [
                    (
                        v.id,
                        v.timestamp,
                        v.category.value,
                        v.severity.value,
                        v.title,
                        v.agents_involved,
                        v.target,
                        v.evidence_chain,
                        v.confidence,
                        v.recommended_action,
                        v.status.value,
                        v.color,
                    )
                    for v in verdicts
                ],
            )
            return len(verdicts)
