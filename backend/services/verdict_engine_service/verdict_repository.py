"""PostgreSQL repository for verdicts.

Reads from verdicts table (owned by narrative_filter_service).
100% async, connection pooling, type-safe queries.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg

from config import settings
from models import Verdict, VerdictFilter, VerdictStats


class VerdictRepository:
    """Repository for verdict queries."""

    def __init__(self) -> None:
        """Initialize repository."""
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(
            settings.postgres_dsn,
            min_size=5,
            max_size=20,
            command_timeout=30,
        )

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_active_verdicts(self, filters: VerdictFilter) -> list[Verdict]:
        """Get active verdicts with optional filters."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        query_parts = ["SELECT * FROM verdicts WHERE 1=1"]
        params: list[Any] = []
        param_count = 1

        if filters.status:
            query_parts.append(f" AND status = ${param_count}")
            params.append(filters.status)
            param_count += 1

        if filters.severity:
            query_parts.append(f" AND severity = ${param_count}")
            params.append(filters.severity)
            param_count += 1

        if filters.category:
            query_parts.append(f" AND category = ${param_count}")
            params.append(filters.category)
            param_count += 1

        if filters.agent_id:
            query_parts.append(f" AND ${param_count} = ANY(agents_involved)")
            params.append(filters.agent_id)
            param_count += 1

        query_parts.append(" ORDER BY timestamp DESC")
        query_parts.append(f" LIMIT ${param_count}")
        params.append(filters.limit)
        param_count += 1

        query_parts.append(f" OFFSET ${param_count}")
        params.append(filters.offset)

        query = "".join(query_parts)

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [Verdict(**dict(row)) for row in rows]

    async def get_verdict_by_id(self, verdict_id: UUID) -> Verdict | None:
        """Get single verdict by ID."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        query = "SELECT * FROM verdicts WHERE id = $1"

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, verdict_id)
            return Verdict(**dict(row)) if row else None

    async def get_stats(self) -> VerdictStats:
        """Get aggregated verdict statistics."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        async with self.pool.acquire() as conn:
            # Total count
            total_count = await conn.fetchval("SELECT COUNT(*) FROM verdicts")

            # By severity
            severity_rows = await conn.fetch(
                "SELECT severity, COUNT(*) as count FROM verdicts GROUP BY severity"
            )
            by_severity = {row["severity"]: row["count"] for row in severity_rows}

            # By status
            status_rows = await conn.fetch(
                "SELECT status, COUNT(*) as count FROM verdicts GROUP BY status"
            )
            by_status = {row["status"]: row["count"] for row in status_rows}

            # By category
            category_rows = await conn.fetch(
                "SELECT category, COUNT(*) as count FROM verdicts GROUP BY category"
            )
            by_category = {row["category"]: row["count"] for row in category_rows}

            # Critical active
            critical_active = await conn.fetchval(
                "SELECT COUNT(*) FROM verdicts "
                "WHERE severity = 'CRITICAL' AND status = 'ACTIVE'"
            )

            return VerdictStats(
                total_count=total_count or 0,
                by_severity=by_severity,
                by_status=by_status,
                by_category=by_category,
                critical_active=critical_active or 0,
                last_updated=datetime.utcnow(),
            )

    async def update_verdict_status(
        self, verdict_id: UUID, new_status: str, mitigation_id: UUID | None = None
    ) -> bool:
        """Update verdict status (for C2L integration)."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")

        query = """
            UPDATE verdicts
            SET status = $2, mitigation_command_id = $3
            WHERE id = $1
        """

        async with self.pool.acquire() as conn:
            result = await conn.execute(query, verdict_id, new_status, mitigation_id)
            return result.split()[-1] == "1"
