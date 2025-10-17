"""Database client for Ethical Audit Service.

This module handles all database operations for ethical decisions,
human overrides, and compliance logs using asyncpg and raw SQL for performance.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

# Configure logging
logger = logging.getLogger(__name__)

from backend.services.ethical_audit_service.models import (
    ComplianceCheckRequest,
    DecisionHistoryQuery,
    EthicalDecisionLog,
    EthicalMetrics,
    FrameworkPerformance,
    HumanOverrideRequest,
)


class EthicalAuditDatabase:
    """PostgreSQL database client for ethical audit service."""

    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database client.

        Args:
            connection_string: PostgreSQL connection string. If None, reads from env.
        """
        self.connection_string = connection_string or os.getenv(
            "POSTGRES_URL", "postgresql://postgres:postgres@postgres:5432/aurora"
        )
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create database connection pool."""
        self.pool = await asyncpg.create_pool(self.connection_string, min_size=5, max_size=20, command_timeout=60)
        print("✅ Connected to PostgreSQL (Ethical Audit Database)")

    async def disconnect(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            print("🔌 Disconnected from PostgreSQL")

    async def initialize_schema(self):
        """Initialize database schema from schema.sql file."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

        async with self.pool.acquire() as conn:
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            await conn.execute(schema_sql)

        print("✅ Database schema initialized")

    # ========================================================================
    # ETHICAL DECISIONS
    # ========================================================================

    async def log_decision(self, decision: EthicalDecisionLog) -> uuid.UUID:
        """Log an ethical decision to the database.

        Args:
            decision: EthicalDecisionLog object

        Returns:
            UUID of the logged decision
        """
        async with self.pool.acquire() as conn:
            decision_id = await conn.fetchval(
                """
                INSERT INTO ethical_decisions (
                    id, timestamp, decision_type, action_description, system_component,
                    input_context, kantian_result, consequentialist_result,
                    virtue_ethics_result, principialism_result,
                    final_decision, final_confidence, decision_explanation,
                    total_latency_ms, kantian_latency_ms, consequentialist_latency_ms,
                    virtue_ethics_latency_ms, principialism_latency_ms,
                    risk_level, automated, operator_id, session_id, environment
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                    $14, $15, $16, $17, $18, $19, $20, $21, $22, $23
                ) RETURNING id
            """,
                decision.id,
                decision.timestamp,
                decision.decision_type.value,
                decision.action_description,
                decision.system_component,
                json.dumps(decision.input_context),
                (json.dumps(decision.kantian_result) if decision.kantian_result else None),
                (json.dumps(decision.consequentialist_result) if decision.consequentialist_result else None),
                (json.dumps(decision.virtue_ethics_result) if decision.virtue_ethics_result else None),
                (json.dumps(decision.principialism_result) if decision.principialism_result else None),
                decision.final_decision.value,
                decision.final_confidence,
                decision.decision_explanation,
                decision.total_latency_ms,
                decision.kantian_latency_ms,
                decision.consequentialist_latency_ms,
                decision.virtue_ethics_latency_ms,
                decision.principialism_latency_ms,
                decision.risk_level.value,
                decision.automated,
                decision.operator_id,
                decision.session_id,
                decision.environment,
            )

        return decision_id

    async def get_decision(self, decision_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Retrieve a decision by ID.

        Args:
            decision_id: UUID of the decision

        Returns:
            Decision dict or None if not found
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM ethical_decisions WHERE id = $1
            """,
                decision_id,
            )

        if row:
            return dict(row)
        return None

    async def query_decisions(self, query: DecisionHistoryQuery) -> Tuple[List[Dict[str, Any]], int]:
        """Query decisions with filters.

        Args:
            query: DecisionHistoryQuery with filters

        Returns:
            Tuple of (list of decisions, total count)
        """
        # Build dynamic WHERE clause
        where_clauses = []
        params = []
        param_idx = 1

        if query.start_time:
            where_clauses.append(f"timestamp >= ${param_idx}")
            params.append(query.start_time)
            param_idx += 1

        if query.end_time:
            where_clauses.append(f"timestamp <= ${param_idx}")
            params.append(query.end_time)
            param_idx += 1

        if query.decision_type:
            where_clauses.append(f"decision_type = ${param_idx}")
            params.append(query.decision_type.value)
            param_idx += 1

        if query.system_component:
            where_clauses.append(f"system_component = ${param_idx}")
            params.append(query.system_component)
            param_idx += 1

        if query.final_decision:
            where_clauses.append(f"final_decision = ${param_idx}")
            params.append(query.final_decision.value)
            param_idx += 1

        if query.risk_level:
            where_clauses.append(f"risk_level = ${param_idx}")
            params.append(query.risk_level.value)
            param_idx += 1

        if query.min_confidence is not None:
            where_clauses.append(f"final_confidence >= ${param_idx}")
            params.append(query.min_confidence)
            param_idx += 1

        if query.max_confidence is not None:
            where_clauses.append(f"final_confidence <= ${param_idx}")
            params.append(query.max_confidence)
            param_idx += 1

        if query.automated_only is not None:
            where_clauses.append(f"automated = ${param_idx}")
            params.append(query.automated_only)
            param_idx += 1

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        async with self.pool.acquire() as conn:
            # Get total count
            count_query = f"SELECT COUNT(*) FROM ethical_decisions WHERE {where_sql}"
            total_count = await conn.fetchval(count_query, *params)

            # Get paginated results
            data_query = f"""
                SELECT * FROM ethical_decisions
                WHERE {where_sql}
                ORDER BY timestamp DESC
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([query.limit, query.offset])
            rows = await conn.fetch(data_query, *params)

        decisions = [dict(row) for row in rows]
        return decisions, total_count

    # ========================================================================
    # HUMAN OVERRIDES
    # ========================================================================

    async def log_override(self, override: HumanOverrideRequest) -> uuid.UUID:
        """Log a human override.

        Args:
            override: HumanOverrideRequest object

        Returns:
            UUID of the logged override
        """
        async with self.pool.acquire() as conn:
            override_id = await conn.fetchval(
                """
                INSERT INTO human_overrides (
                    decision_id, operator_id, operator_role,
                    original_decision, override_decision, justification,
                    override_reason, urgency_level, ip_address, user_agent
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """,
                override.decision_id,
                override.operator_id,
                override.operator_role.value,
                override.original_decision.value,
                override.override_decision.value,
                override.justification,
                override.override_reason.value,
                override.urgency_level.value,
                override.ip_address,
                override.user_agent,
            )

        return override_id

    async def get_overrides_by_decision(self, decision_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get all overrides for a decision.

        Args:
            decision_id: UUID of the decision

        Returns:
            List of override dicts
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM human_overrides
                WHERE decision_id = $1
                ORDER BY timestamp DESC
            """,
                decision_id,
            )

        return [dict(row) for row in rows]

    # ========================================================================
    # COMPLIANCE LOGS
    # ========================================================================

    async def log_compliance_check(self, check: ComplianceCheckRequest) -> uuid.UUID:
        """Log a compliance check.

        Args:
            check: ComplianceCheckRequest object

        Returns:
            UUID of the logged compliance check
        """
        async with self.pool.acquire() as conn:
            compliance_id = await conn.fetchval(
                """
                INSERT INTO compliance_logs (
                    regulation, requirement_id, check_type, check_result,
                    evidence, findings, decision_id, audit_cycle, auditor_id,
                    remediation_required, remediation_plan, remediation_deadline
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING id
            """,
                check.regulation.value,
                check.requirement_id,
                check.check_type,
                check.check_result.value,
                json.dumps(check.evidence),
                check.findings,
                check.decision_id,
                check.audit_cycle,
                check.auditor_id,
                check.remediation_required,
                check.remediation_plan,
                check.remediation_deadline,
            )

        return compliance_id

    # ========================================================================
    # METRICS & ANALYTICS
    # ========================================================================

    async def get_metrics(self) -> EthicalMetrics:
        """Get real-time ethical KPIs.

        Returns:
            EthicalMetrics object with current metrics
        """
        async with self.pool.acquire() as conn:
            # Last 24h decisions
            last_24h = datetime.utcnow() - timedelta(hours=24)

            decisions_24h = await conn.fetch(
                """
                SELECT
                    COUNT(*) as total,
                    AVG(final_confidence) as avg_confidence,
                    SUM(CASE WHEN final_decision = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN final_decision = 'REJECTED' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN final_decision = 'ESCALATED_HITL' THEN 1 ELSE 0 END) as escalated,
                    SUM(CASE WHEN automated = FALSE THEN 1 ELSE 0 END) as hitl_count,
                    AVG(total_latency_ms) as avg_latency,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total_latency_ms) as p95_latency,
                    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total_latency_ms) as p99_latency
                FROM ethical_decisions
                WHERE timestamp >= $1
            """,
                last_24h,
            )

            row = decisions_24h[0]
            total = row["total"] or 0
            approved = row["approved"] or 0
            rejected = row["rejected"] or 0
            escalated = row["escalated"] or 0

            # Framework agreement rate
            agreement_rate = (
                await conn.fetchval(
                    """
                SELECT
                    COUNT(*) FILTER (
                        WHERE (kantian_result->>'approved')::boolean = TRUE
                        AND (consequentialist_result->>'approved')::boolean = TRUE
                        AND (virtue_ethics_result->>'approved')::boolean = TRUE
                        AND (principialism_result->>'approved')::boolean = TRUE
                    )::float / NULLIF(COUNT(*), 0)
                FROM ethical_decisions
                WHERE timestamp >= $1
                AND kantian_result IS NOT NULL
                AND consequentialist_result IS NOT NULL
                AND virtue_ethics_result IS NOT NULL
                AND principialism_result IS NOT NULL
            """,
                    last_24h,
                )
                or 0.0
            )

            # Kantian veto rate
            kantian_veto_rate = (
                await conn.fetchval(
                    """
                SELECT COUNT(*) FILTER (WHERE (kantian_result->>'veto')::boolean = TRUE)::float / NULLIF(COUNT(*), 0)
                FROM ethical_decisions
                WHERE timestamp >= $1 AND kantian_result IS NOT NULL
            """,
                    last_24h,
                )
                or 0.0
            )

            # Human overrides
            overrides = await conn.fetch(
                """
                SELECT COUNT(*) as total, override_reason
                FROM human_overrides
                WHERE timestamp >= $1
                GROUP BY override_reason
            """,
                last_24h,
            )

            override_reasons = {row["override_reason"]: row["total"] for row in overrides}
            total_overrides = sum(override_reasons.values())

            # Compliance (last week)
            last_week = datetime.utcnow() - timedelta(days=7)
            compliance = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN check_result = 'COMPLIANT' THEN 1 ELSE 0 END) as compliant,
                    SUM(CASE WHEN check_result = 'NON_COMPLIANT' AND
                        (SELECT severity FROM compliance_requirements
                         WHERE regulation = compliance_logs.regulation
                         AND requirement_id = compliance_logs.requirement_id) = 'critical'
                        THEN 1 ELSE 0 END) as critical_violations
                FROM compliance_logs
                WHERE timestamp >= $1
            """,
                last_week,
            )

            # Risk distribution
            risk_dist = await conn.fetch(
                """
                SELECT risk_level, COUNT(*) as count
                FROM ethical_decisions
                WHERE timestamp >= $1
                GROUP BY risk_level
            """,
                last_24h,
            )

            risk_distribution = {row["risk_level"]: row["count"] for row in risk_dist}

        return EthicalMetrics(
            total_decisions_last_24h=total,
            approval_rate=approved / total if total > 0 else 0.0,
            rejection_rate=rejected / total if total > 0 else 0.0,
            hitl_escalation_rate=escalated / total if total > 0 else 0.0,
            avg_latency_ms=float(row["avg_latency"] or 0.0),
            p95_latency_ms=float(row["p95_latency"] or 0.0),
            p99_latency_ms=float(row["p99_latency"] or 0.0),
            framework_agreement_rate=float(agreement_rate),
            kantian_veto_rate=float(kantian_veto_rate),
            total_overrides_last_24h=total_overrides,
            override_rate=total_overrides / total if total > 0 else 0.0,
            override_reasons=override_reasons,
            compliance_checks_last_week=compliance["total"] or 0,
            compliance_pass_rate=(compliance["compliant"] / compliance["total"] if compliance["total"] > 0 else 0.0),
            critical_violations=compliance["critical_violations"] or 0,
            risk_distribution=risk_distribution,
        )

    async def get_framework_performance(self, hours: int = 24) -> List[FrameworkPerformance]:
        """Get performance metrics for each framework.

        Args:
            hours: Number of hours to look back

        Returns:
            List of FrameworkPerformance objects
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        async with self.pool.acquire() as conn:
            frameworks = [
                "kantian",
                "consequentialist",
                "virtue_ethics",
                "principialism",
            ]
            performance_data = []

            for framework in frameworks:
                result_col = f"{framework}_result"
                latency_col = f"{framework}_latency_ms"

                row = await conn.fetchrow(
                    f"""
                    SELECT
                        COUNT(*) as total,
                        AVG({latency_col}) as avg_latency,
                        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {latency_col}) as p95_latency,
                        SUM(CASE WHEN ({result_col}->>'approved')::boolean = TRUE THEN 1 ELSE 0 END) as approved,
                        AVG(({result_col}->>'confidence')::float) as avg_confidence
                    FROM ethical_decisions
                    WHERE timestamp >= $1 AND {result_col} IS NOT NULL
                """,
                    since,
                )

                if row and row["total"] > 0:
                    performance_data.append(
                        FrameworkPerformance(
                            framework_name=framework,
                            total_decisions=row["total"],
                            avg_latency_ms=float(row["avg_latency"] or 0.0),
                            p95_latency_ms=float(row["p95_latency"] or 0.0),
                            approval_rate=(row["approved"] / row["total"] if row["total"] > 0 else 0.0),
                            avg_confidence=float(row["avg_confidence"] or 0.0),
                        )
                    )

        return performance_data
