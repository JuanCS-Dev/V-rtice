"""
TimescaleDB client for Behavioral Analyzer Service.

Constitutional: Lei Zero - respects data retention and user consent (GDPR).

This module provides async database operations for behavioral analysis data,
replacing in-memory dictionaries with production-grade persistent storage.
"""

import logging
import os
from datetime import datetime
from typing import Any

import asyncpg
from asyncpg import Pool

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Pool | None = None


async def init_db_pool() -> Pool:
    """
    Initialize database connection pool.

    Constitutional: P2 (Validação Preventiva) - validates DB connection before use.

    Returns:
        AsyncPG connection pool

    Raises:
        ConnectionError: If database is unavailable
    """
    global _pool

    if _pool is not None:
        return _pool

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://vertice:vertice_secure_password@timescaledb:5432/behavioral_analysis",
    )

    try:
        _pool = await asyncpg.create_pool(
            db_url, min_size=5, max_size=20, command_timeout=60, timeout=30
        )
        logger.info(
            "✅ TimescaleDB connection pool initialized",
            extra={"db_url": db_url.split("@")[1] if "@" in db_url else "***"},
        )
        return _pool

    except Exception as e:
        logger.error(f"❌ Failed to initialize TimescaleDB pool: {e}", exc_info=True)
        raise ConnectionError(f"Database unavailable: {e}") from e


async def close_db_pool():
    """Close database connection pool gracefully."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("✅ TimescaleDB connection pool closed")


async def health_check() -> dict[str, Any]:
    """
    Check database health.

    Returns:
        Health status dict
    """
    if _pool is None:
        return {"healthy": False, "error": "Pool not initialized"}

    try:
        async with _pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            timescale_version = await conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
            )
            return {
                "healthy": True,
                "postgres_version": version.split(",")[0],
                "timescaledb_version": timescale_version,
                "pool_size": _pool.get_size(),
                "pool_free": _pool.get_idle_size(),
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"healthy": False, "error": str(e)}


# ============================================================================
# USER PROFILE OPERATIONS
# ============================================================================


async def create_user_profile(
    user_id: str,
    baseline_metrics: dict[str, Any],
    fingerprint: dict[str, Any],
    consent_given: bool = False,
    data_retention_days: int = 90,
) -> None:
    """
    Create or update user profile.

    Constitutional: Lei Zero - requires explicit consent, respects retention.

    Args:
        user_id: Unique user identifier
        baseline_metrics: User's normal behavior patterns
        fingerprint: Browser/device fingerprint
        consent_given: GDPR consent flag
        data_retention_days: Data retention period (default 90 days)
    """
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_profiles (
                user_id, baseline_metrics, fingerprint,
                consent_given, data_retention_days, consent_date
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE SET
                baseline_metrics = EXCLUDED.baseline_metrics,
                fingerprint = EXCLUDED.fingerprint,
                consent_given = EXCLUDED.consent_given,
                data_retention_days = EXCLUDED.data_retention_days,
                consent_date = EXCLUDED.consent_date,
                updated_at = NOW()
            """,
            user_id,
            baseline_metrics,
            fingerprint,
            consent_given,
            data_retention_days,
            datetime.utcnow() if consent_given else None,
        )
        logger.debug(f"✅ User profile created/updated: {user_id}")


async def get_user_profile(user_id: str) -> dict[str, Any] | None:
    """
    Get user profile by ID.

    Args:
        user_id: Unique user identifier

    Returns:
        User profile dict or None if not found
    """
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                user_id, baseline_metrics, fingerprint, risk_score,
                risk_level, total_events, anomaly_count, last_seen,
                created_at, updated_at, data_retention_days, consent_given
            FROM user_profiles
            WHERE user_id = $1
            """,
            user_id,
        )

        if not row:
            return None

        return {
            "user_id": row["user_id"],
            "baseline_metrics": row["baseline_metrics"],
            "fingerprint": row["fingerprint"],
            "risk_score": row["risk_score"],
            "risk_level": row["risk_level"],
            "total_events": row["total_events"],
            "anomaly_count": row["anomaly_count"],
            "last_seen": row["last_seen"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "data_retention_days": row["data_retention_days"],
            "consent_given": row["consent_given"],
        }


async def update_user_risk_score(
    user_id: str, risk_score: float, risk_level: str = None
) -> None:
    """
    Update user's risk score.

    Args:
        user_id: Unique user identifier
        risk_score: New risk score (0.0-1.0)
        risk_level: Risk level classification (low/medium/high/critical)
    """
    # Determine risk level if not provided
    if risk_level is None:
        if risk_score < 0.3:
            risk_level = "low"
        elif risk_score < 0.6:
            risk_level = "medium"
        elif risk_score < 0.85:
            risk_level = "high"
        else:
            risk_level = "critical"

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE user_profiles
            SET risk_score = $2, risk_level = $3, updated_at = NOW()
            WHERE user_id = $1
            """,
            user_id,
            risk_score,
            risk_level,
        )
        logger.debug(f"✅ Risk score updated: {user_id} → {risk_score} ({risk_level})")


async def list_high_risk_users(
    min_risk_score: float = 0.7, limit: int = 50
) -> list[dict[str, Any]]:
    """
    List users with high risk scores.

    Args:
        min_risk_score: Minimum risk score threshold
        limit: Maximum number of results

    Returns:
        List of high-risk user profiles
    """
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                user_id, risk_score, risk_level, anomaly_count,
                last_seen, updated_at
            FROM user_profiles
            WHERE risk_score >= $1
            ORDER BY risk_score DESC, updated_at DESC
            LIMIT $2
            """,
            min_risk_score,
            limit,
        )

        return [
            {
                "user_id": row["user_id"],
                "risk_score": row["risk_score"],
                "risk_level": row["risk_level"],
                "anomaly_count": row["anomaly_count"],
                "last_seen": row["last_seen"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


# ============================================================================
# BEHAVIORAL EVENT OPERATIONS
# ============================================================================


async def log_behavioral_event(
    event_id: str,
    user_id: str,
    event_type: str,
    resource: str | None,
    action: str | None,
    ip_address: str | None,
    user_agent: str | None,
    risk_score: float | None,
    anomaly_detected: bool,
    anomaly_reason: str | None = None,
    blocked: bool = False,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Log a behavioral event.

    Constitutional: P4 (Rastreabilidade Total) - every event is auditable.

    Args:
        event_id: Unique event identifier
        user_id: User performing the action
        event_type: Type of event (login, api_call, etc.)
        resource: Resource accessed
        action: Action performed
        ip_address: Client IP address
        user_agent: Client user agent
        risk_score: Calculated risk score
        anomaly_detected: Whether anomaly was detected
        anomaly_reason: Reason for anomaly detection
        blocked: Whether action was blocked
        metadata: Additional event metadata
    """
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO behavioral_events (
                event_id, user_id, event_type, resource, action,
                ip_address, user_agent, risk_score, anomaly_detected,
                anomaly_reason, blocked, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (event_id) DO NOTHING
            """,
            event_id,
            user_id,
            event_type,
            resource,
            action,
            ip_address,
            user_agent,
            risk_score,
            anomaly_detected,
            anomaly_reason,
            blocked,
            metadata or {},
        )
        logger.debug(
            f"✅ Event logged: {event_id} (user={user_id}, type={event_type}, "
            f"anomaly={anomaly_detected})"
        )


async def get_recent_events(
    user_id: str, limit: int = 100, event_type: str | None = None
) -> list[dict[str, Any]]:
    """
    Get recent events for user.

    Args:
        user_id: User identifier
        limit: Maximum number of events
        event_type: Filter by event type (optional)

    Returns:
        List of recent events
    """
    query = """
        SELECT
            event_id, user_id, timestamp, event_type, resource,
            action, ip_address, risk_score, anomaly_detected,
            anomaly_reason, blocked, metadata
        FROM behavioral_events
        WHERE user_id = $1
    """

    if event_type:
        query += " AND event_type = $3"

    query += " ORDER BY timestamp DESC LIMIT $2"

    async with _pool.acquire() as conn:
        if event_type:
            rows = await conn.fetch(query, user_id, limit, event_type)
        else:
            rows = await conn.fetch(query, user_id, limit)

        return [
            {
                "event_id": row["event_id"],
                "user_id": row["user_id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "resource": row["resource"],
                "action": row["action"],
                "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                "risk_score": row["risk_score"],
                "anomaly_detected": row["anomaly_detected"],
                "anomaly_reason": row["anomaly_reason"],
                "blocked": row["blocked"],
                "metadata": row["metadata"],
            }
            for row in rows
        ]


async def get_anomalous_events(
    hours_back: int = 24, min_risk_score: float = 0.5, limit: int = 100
) -> list[dict[str, Any]]:
    """
    Get recent anomalous events across all users.

    Args:
        hours_back: Look back N hours
        min_risk_score: Minimum risk score
        limit: Maximum results

    Returns:
        List of anomalous events
    """
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                event_id, user_id, timestamp, event_type, resource,
                action, ip_address, risk_score, anomaly_detected,
                anomaly_reason, blocked
            FROM behavioral_events
            WHERE anomaly_detected = true
              AND timestamp > NOW() - INTERVAL '$1 hours'
              AND risk_score >= $2
            ORDER BY risk_score DESC, timestamp DESC
            LIMIT $3
            """,
            hours_back,
            min_risk_score,
            limit,
        )

        return [
            {
                "event_id": row["event_id"],
                "user_id": row["user_id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "resource": row["resource"],
                "action": row["action"],
                "ip_address": str(row["ip_address"]) if row["ip_address"] else None,
                "risk_score": row["risk_score"],
                "anomaly_reason": row["anomaly_reason"],
                "blocked": row["blocked"],
            }
            for row in rows
        ]


# ============================================================================
# ANOMALY OPERATIONS
# ============================================================================


async def create_anomaly(
    anomaly_id: str,
    user_id: str,
    anomaly_type: str,
    severity: str,
    confidence: float,
    title: str,
    description: str,
    evidence: dict[str, Any],
    related_events: list[str] | None = None,
    baseline_deviation: float | None = None,
) -> None:
    """
    Record detected anomaly.

    Constitutional: Lei Zero - requires human review for high-severity anomalies.

    Args:
        anomaly_id: Unique anomaly identifier
        user_id: Affected user
        anomaly_type: Type of anomaly
        severity: Severity level (low/medium/high/critical)
        confidence: Detection confidence (0.0-1.0)
        title: Short title
        description: Detailed description
        evidence: Supporting evidence
        related_events: Related event IDs
        baseline_deviation: Statistical deviation from baseline
    """
    # Determine priority from severity
    priority_map = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    priority = priority_map.get(severity, 0)

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO anomalies (
                anomaly_id, user_id, anomaly_type, severity, confidence,
                title, description, evidence, related_events,
                baseline_deviation, priority
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (anomaly_id) DO NOTHING
            """,
            anomaly_id,
            user_id,
            anomaly_type,
            severity,
            confidence,
            title,
            description,
            evidence,
            related_events or [],
            baseline_deviation,
            priority,
        )
        logger.info(
            f"🚨 Anomaly created: {anomaly_id} (user={user_id}, "
            f"severity={severity}, confidence={confidence:.2f})"
        )


async def get_open_anomalies(
    severity: str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """
    Get open anomalies requiring investigation.

    Args:
        severity: Filter by severity (optional)
        limit: Maximum results

    Returns:
        List of open anomalies
    """
    query = """
        SELECT
            anomaly_id, user_id, detected_at, anomaly_type,
            severity, confidence, title, description, evidence,
            priority, status
        FROM anomalies
        WHERE status IN ('open', 'investigating')
    """

    if severity:
        query += " AND severity = $2"

    query += " ORDER BY priority DESC, detected_at DESC LIMIT $1"

    async with _pool.acquire() as conn:
        if severity:
            rows = await conn.fetch(query, limit, severity)
        else:
            rows = await conn.fetch(query, limit)

        return [
            {
                "anomaly_id": row["anomaly_id"],
                "user_id": row["user_id"],
                "detected_at": row["detected_at"],
                "anomaly_type": row["anomaly_type"],
                "severity": row["severity"],
                "confidence": row["confidence"],
                "title": row["title"],
                "description": row["description"],
                "evidence": row["evidence"],
                "priority": row["priority"],
                "status": row["status"],
            }
            for row in rows
        ]


async def update_anomaly_status(
    anomaly_id: str,
    status: str,
    resolution: str | None = None,
    false_positive: bool | None = None,
) -> None:
    """
    Update anomaly investigation status.

    Args:
        anomaly_id: Anomaly identifier
        status: New status (investigating/resolved/false_positive)
        resolution: Resolution notes
        false_positive: Mark as false positive
    """
    resolved_at = datetime.utcnow() if status == "resolved" else None

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE anomalies
            SET status = $2,
                resolution = COALESCE($3, resolution),
                false_positive = COALESCE($4, false_positive),
                resolved_at = COALESCE($5, resolved_at),
                investigated_at = CASE
                    WHEN investigated_at IS NULL THEN NOW()
                    ELSE investigated_at
                END
            WHERE anomaly_id = $1
            """,
            anomaly_id,
            status,
            resolution,
            false_positive,
            resolved_at,
        )
        logger.info(f"✅ Anomaly status updated: {anomaly_id} → {status}")


# ============================================================================
# STATISTICS & ANALYTICS
# ============================================================================


async def get_user_statistics(user_id: str) -> dict[str, Any]:
    """
    Get comprehensive user statistics.

    Args:
        user_id: User identifier

    Returns:
        Statistics dict
    """
    async with _pool.acquire() as conn:
        # Get profile
        profile = await conn.fetchrow(
            "SELECT * FROM user_profiles WHERE user_id = $1", user_id
        )

        if not profile:
            return {"error": "User not found"}

        # Get event statistics (last 30 days)
        event_stats = await conn.fetchrow(
            """
            SELECT
                COUNT(*) as total_events,
                COUNT(*) FILTER (WHERE anomaly_detected) as anomaly_events,
                COUNT(DISTINCT event_type) as unique_event_types,
                COUNT(DISTINCT ip_address) as unique_ips,
                AVG(risk_score) as avg_risk_score,
                MAX(risk_score) as max_risk_score
            FROM behavioral_events
            WHERE user_id = $1
              AND timestamp > NOW() - INTERVAL '30 days'
            """,
            user_id,
        )

        # Get open anomalies
        open_anomalies = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM anomalies
            WHERE user_id = $1 AND status IN ('open', 'investigating')
            """,
            user_id,
        )

        return {
            "user_id": user_id,
            "risk_score": profile["risk_score"],
            "risk_level": profile["risk_level"],
            "total_events_lifetime": profile["total_events"],
            "total_events_30d": event_stats["total_events"],
            "anomaly_count": event_stats["anomaly_events"],
            "unique_event_types": event_stats["unique_event_types"],
            "unique_ips": event_stats["unique_ips"],
            "avg_risk_score": (
                float(event_stats["avg_risk_score"])
                if event_stats["avg_risk_score"]
                else 0.0
            ),
            "max_risk_score": (
                float(event_stats["max_risk_score"])
                if event_stats["max_risk_score"]
                else 0.0
            ),
            "open_anomalies": open_anomalies,
            "last_seen": profile["last_seen"],
        }


async def get_system_statistics() -> dict[str, Any]:
    """
    Get system-wide statistics.

    Returns:
        System statistics dict
    """
    async with _pool.acquire() as conn:
        stats = await conn.fetchrow(
            """
            SELECT
                (SELECT COUNT(*) FROM user_profiles) as total_users,
                (SELECT COUNT(*) FROM user_profiles WHERE risk_score > 0.7) as high_risk_users,
                (SELECT COUNT(*) FROM behavioral_events WHERE timestamp > NOW() - INTERVAL '24 hours') as events_24h,
                (SELECT COUNT(*) FROM behavioral_events WHERE anomaly_detected AND timestamp > NOW() - INTERVAL '24 hours') as anomalies_24h,
                (SELECT COUNT(*) FROM anomalies WHERE status = 'open') as open_investigations
            """
        )

        return {
            "total_users": stats["total_users"],
            "high_risk_users": stats["high_risk_users"],
            "events_last_24h": stats["events_24h"],
            "anomalies_last_24h": stats["anomalies_24h"],
            "open_investigations": stats["open_investigations"],
            "timestamp": datetime.utcnow(),
        }
