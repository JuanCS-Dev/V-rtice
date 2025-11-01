"""Decision Audit Logger - Append-Only Sophia Engine Decision Trail.

Implements comprehensive audit logging for all Sophia Engine healing decisions.
Provides immutable record of automated decision-making for compliance and learning.

Audit Trail Principle: Transparent, traceable autonomous decisions
Biblical Foundation: Proverbs 4:11 - "I guide you in the way of wisdom"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
from datetime import datetime
import json
import logging
from typing import Any
from uuid import uuid4

from prometheus_client import Counter, Histogram

from models import InterventionDecision

logger = logging.getLogger(__name__)


class DecisionAuditLogger:
    """Append-only audit log for all Sophia Engine healing decisions.

    Records every decision made by the Sophia Engine with complete context:
    - Decision rationale and wisdom applied
    - Risk assessment and factors considered
    - Precedents consulted and similarity scores
    - Input anomaly details
    - Timestamp and unique identifiers

    Architecture:
    - Dual storage: Database (queryable) + Loki (monitoring)
    - Structured JSON for easy parsing and analysis
    - Thread-safe with asyncio.Lock
    - Prometheus metrics for decision tracking
    - Immutable records (no updates, only inserts)

    Storage Strategy:
    - Primary: In-memory list (for testing/development)
    - Production: PostgreSQL table with indexes
    - Monitoring: Loki via structured logging

    Biblical Principle: Wisdom leaves a trail (Proverbs 4:11)
    """

    # Prometheus metrics
    decisions_logged_total = Counter(
        "penelope_decisions_logged_total",
        "Total Sophia Engine decisions logged",
        ["decision_type"],  # observe, intervene, escalate
    )

    decision_logging_duration = Histogram(
        "penelope_decision_logging_duration_seconds",
        "Time to log decision to audit trail",
    )

    risk_score_distribution = Histogram(
        "penelope_decision_risk_scores",
        "Distribution of risk scores in decisions",
        buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    )

    def __init__(self, pool: Any | None = None):
        """Initialize Decision Audit Logger.

        Args:
            pool: Optional asyncpg connection pool for PostgreSQL storage
                 If None, uses in-memory storage (for testing)
        """
        self.pool = pool

        # In-memory storage for testing/fallback
        self.audit_trail: list[dict[str, Any]] = []

        # Thread safety
        self._lock = asyncio.Lock()

        logger.info("Decision Audit Logger initialized (Sophia Engine decisions)")

    async def log_decision(
        self,
        anomaly_id: str,
        decision: InterventionDecision,
        reasoning: str,
        risk_assessment: dict[str, Any],
        precedents: list[dict[str, Any]],
        sophia_wisdom: str,
        anomaly_details: dict[str, Any] | None = None,
    ) -> str:
        """Log Sophia Engine decision to immutable audit trail.

        Args:
            anomaly_id: Unique identifier for the anomaly being evaluated
            decision: Decision made (OBSERVE_AND_WAIT, INTERVENE, HUMAN_CONSULTATION_REQUIRED)
            reasoning: Human-readable explanation of decision
            risk_assessment: Risk analysis dict with risk_score and risk_factors
            precedents: List of historical precedents consulted
            sophia_wisdom: Biblical wisdom/principle applied
            anomaly_details: Optional additional context about the anomaly

        Returns:
            Unique audit entry ID
        """
        start_time = datetime.utcnow()
        audit_id = str(uuid4())

        # Extract risk metrics
        risk_score = risk_assessment.get("risk_score", 0.0)
        risk_factors = risk_assessment.get("risk_factors", [])

        # Find best precedent similarity
        best_precedent_similarity = None
        if precedents:
            best_precedent_similarity = max(
                (p.get("similarity", 0.0) for p in precedents), default=None
            )

        # Build audit entry
        audit_entry = {
            "audit_id": audit_id,
            "timestamp": start_time.isoformat(),
            "anomaly_id": anomaly_id,
            "decision": decision.value,
            "reasoning": reasoning,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "precedents_count": len(precedents),
            "best_precedent_similarity": best_precedent_similarity,
            "sophia_wisdom": sophia_wisdom,
            "decision_maker": "sophia_engine_v1.0",
            "anomaly_details": anomaly_details or {},
        }

        async with self._lock:
            # Store in memory
            self.audit_trail.append(audit_entry)

            # Log to Loki with structured labels
            logger.info(
                "SOPHIA_DECISION",
                extra={
                    "labels": {
                        "component": "sophia_engine",
                        "decision": decision.value,
                        "anomaly_id": anomaly_id,
                        "audit_id": audit_id,
                    },
                    "audit": audit_entry,
                },
            )

            # Store in database (if available)
            if self.pool:
                try:
                    await self._store_to_database(audit_entry)
                except Exception as e:
                    logger.error(
                        f"Failed to store audit entry to database: {e}. "
                        f"Entry preserved in memory: {audit_id}"
                    )

        # Update metrics
        self.decisions_logged_total.labels(decision_type=decision.value).inc()
        self.risk_score_distribution.observe(risk_score)

        duration = (datetime.utcnow() - start_time).total_seconds()
        self.decision_logging_duration.observe(duration)

        logger.debug(
            f"✅ Logged Sophia decision: {decision.value} for anomaly {anomaly_id} "
            f"(audit_id: {audit_id}, risk: {risk_score:.2f})"
        )

        return audit_id

    async def _store_to_database(self, audit_entry: dict[str, Any]) -> None:
        """Store audit entry to PostgreSQL database.

        Args:
            audit_entry: Complete audit entry dictionary
        """
        if not self.pool:
            return

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO decision_audit_log (
                    audit_id, anomaly_id, decision, reasoning,
                    risk_score, risk_assessment, precedents,
                    sophia_wisdom, decision_maker, anomaly_details, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                audit_entry["audit_id"],
                audit_entry["anomaly_id"],
                audit_entry["decision"],
                audit_entry["reasoning"],
                audit_entry["risk_score"],
                json.dumps(
                    {
                        "risk_score": audit_entry["risk_score"],
                        "risk_factors": audit_entry["risk_factors"],
                    }
                ),
                json.dumps(
                    [
                        {
                            "similarity": p.get("similarity"),
                            "outcome": p.get("outcome"),
                            "case_id": p.get("case_id"),
                        }
                        for p in audit_entry.get("precedents", [])
                    ]
                ),
                audit_entry["sophia_wisdom"],
                audit_entry["decision_maker"],
                json.dumps(audit_entry["anomaly_details"]),
                datetime.fromisoformat(audit_entry["timestamp"]),
            )

    async def get_decisions(
        self,
        anomaly_id: str | None = None,
        decision_type: InterventionDecision | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit trail for decisions.

        Args:
            anomaly_id: Filter by specific anomaly ID
            decision_type: Filter by decision type
            since: Filter for decisions after this timestamp
            limit: Maximum number of results (default: 100)

        Returns:
            List of audit entries matching filters
        """
        async with self._lock:
            results = self.audit_trail.copy()

            # Apply filters
            if anomaly_id:
                results = [r for r in results if r["anomaly_id"] == anomaly_id]

            if decision_type:
                results = [r for r in results if r["decision"] == decision_type.value]

            if since:
                since_iso = since.isoformat()
                results = [r for r in results if r["timestamp"] >= since_iso]

            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x["timestamp"], reverse=True)

            # Limit results
            return results[:limit]

    async def get_decision_by_id(self, audit_id: str) -> dict[str, Any] | None:
        """Retrieve specific decision by audit ID.

        Args:
            audit_id: Unique audit entry identifier

        Returns:
            Audit entry dict or None if not found
        """
        async with self._lock:
            for entry in self.audit_trail:
                if entry["audit_id"] == audit_id:
                    return entry.copy()
            return None

    async def get_decision_stats(self, since: datetime | None = None) -> dict[str, Any]:
        """Get statistical summary of decisions.

        Args:
            since: Calculate stats from this timestamp onwards

        Returns:
            Dict with decision counts, avg risk, precedent usage
        """
        async with self._lock:
            decisions = self.audit_trail.copy()

            if since:
                since_iso = since.isoformat()
                decisions = [d for d in decisions if d["timestamp"] >= since_iso]

            if not decisions:
                return {
                    "total_decisions": 0,
                    "decision_breakdown": {},
                    "avg_risk_score": 0.0,
                    "precedents_used_pct": 0.0,
                }

            # Count by decision type
            decision_breakdown = {}
            for decision_type in InterventionDecision:
                count = sum(
                    1 for d in decisions if d["decision"] == decision_type.value
                )
                decision_breakdown[decision_type.value] = count

            # Calculate average risk
            risk_scores = [d["risk_score"] for d in decisions if d["risk_score"] > 0]
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            # Precedent usage
            decisions_with_precedents = sum(
                1 for d in decisions if d["precedents_count"] > 0
            )
            precedent_pct = (
                (decisions_with_precedents / len(decisions) * 100) if decisions else 0.0
            )

            return {
                "total_decisions": len(decisions),
                "decision_breakdown": decision_breakdown,
                "avg_risk_score": avg_risk,
                "precedents_used_pct": precedent_pct,
                "time_range": {
                    "since": since.isoformat() if since else None,
                    "until": datetime.utcnow().isoformat(),
                },
            }

    async def get_high_risk_decisions(
        self, risk_threshold: float = 0.7, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get decisions with high risk scores.

        Args:
            risk_threshold: Minimum risk score to include (default: 0.7)
            limit: Maximum results (default: 50)

        Returns:
            List of high-risk decisions, sorted by risk (highest first)
        """
        async with self._lock:
            high_risk = [
                entry
                for entry in self.audit_trail
                if entry["risk_score"] >= risk_threshold
            ]

            # Sort by risk score (highest first)
            high_risk.sort(key=lambda x: x["risk_score"], reverse=True)

            return high_risk[:limit]

    async def export_audit_trail(
        self, since: datetime | None = None, format: str = "json"
    ) -> str:
        """Export complete audit trail for compliance/analysis.

        Args:
            since: Export decisions from this timestamp onwards
            format: Output format ('json' or 'csv')

        Returns:
            Serialized audit trail
        """
        decisions = await self.get_decisions(since=since, limit=10000)

        if format == "json":
            return json.dumps(
                {"exported_at": datetime.utcnow().isoformat(), "decisions": decisions},
                indent=2,
            )
        elif format == "csv":
            # Basic CSV export
            if not decisions:
                return "No decisions found"

            csv_lines = [
                "timestamp,audit_id,anomaly_id,decision,risk_score,reasoning,sophia_wisdom"
            ]
            for d in decisions:
                csv_lines.append(
                    f"{d['timestamp']},{d['audit_id']},{d['anomaly_id']},"
                    f"{d['decision']},{d['risk_score']},{d['reasoning']},{d['sophia_wisdom']}"
                )
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def count_decisions(self) -> int:
        """Get total count of logged decisions.

        Returns:
            Total number of decisions in audit trail
        """
        async with self._lock:
            return len(self.audit_trail)

    async def clear_audit_trail(self) -> int:
        """Clear all decisions from memory (for testing only).

        Warning: This is destructive and should only be used in tests.

        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self.audit_trail)
            self.audit_trail.clear()
            logger.warning(
                f"⚠️  Audit trail CLEARED: {count} decisions removed (testing only)"
            )
            return count
