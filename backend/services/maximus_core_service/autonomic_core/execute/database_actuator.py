"""Database Actuator - PostgreSQL/pgBouncer Connection Pool Management"""

import logging
from typing import Any, Dict, List, Optional

import asyncpg
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logger = logging.getLogger(__name__)


class DatabaseActuator:
    """Manage database connection pools and query optimization."""

    def __init__(
        self,
        db_url: str = "postgresql://localhost:5432/vertice",
        pgbouncer_admin_url: str = "postgresql://localhost:6432/pgbouncer",
        dry_run_mode: bool = True,
    ):
        self.db_url = db_url
        self.pgbouncer_admin_url = pgbouncer_admin_url
        self.dry_run_mode = dry_run_mode
        self.action_log = []

    async def adjust_connection_pool(
        self, database: str, pool_size: int, pool_mode: str = "transaction"
    ) -> Dict:
        """Adjust pgBouncer connection pool size and mode.

        Args:
            database: Database name
            pool_size: Max connections (10-100)
            pool_mode: 'session', 'transaction', or 'statement'
        """
        if self.dry_run_mode:
            logger.info(
                f"DRY-RUN: Set {database} pool_size={pool_size}, pool_mode={pool_mode}"
            )
            self.action_log.append(
                {
                    "action": "adjust_pool",
                    "database": database,
                    "pool_size": pool_size,
                    "pool_mode": pool_mode,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            # Validate inputs
            if not isinstance(pool_size, int) or not (10 <= pool_size <= 100):
                raise ValueError(f"Invalid pool_size: {pool_size}. Must be int 10-100.")

            if pool_mode not in ("session", "transaction", "statement"):
                raise ValueError(f"Invalid pool_mode: {pool_mode}. Must be 'session', 'transaction', or 'statement'.")

            # Connect to pgBouncer admin console
            conn = await asyncpg.connect(self.pgbouncer_admin_url)

            # Update pool configuration (safe: validated as int and enum)
            await conn.execute(
                f"""
                SET default_pool_size = {pool_size};
                SET pool_mode = '{pool_mode}';
            """
            )

            # Reload configuration
            await conn.execute("RELOAD;")

            await conn.close()

            self.action_log.append(
                {
                    "action": "adjust_pool",
                    "database": database,
                    "pool_size": pool_size,
                    "pool_mode": pool_mode,
                    "executed": True,
                    "success": True,
                }
            )

            logger.info(
                f"Pool adjusted: {database} -> {pool_size} connections ({pool_mode} mode)"
            )

            return {
                "success": True,
                "database": database,
                "pool_size": pool_size,
                "pool_mode": pool_mode,
            }

        except Exception as e:
            logger.error(f"Pool adjustment error: {e}")
            return {"success": False, "error": str(e)}

    async def kill_idle_connections(self, idle_threshold_seconds: int = 300) -> Dict:
        """Terminate idle connections to free resources.

        Args:
            idle_threshold_seconds: Kill connections idle for this duration (default 5min)
        """
        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Kill connections idle >{idle_threshold_seconds}s")
            self.action_log.append(
                {
                    "action": "kill_idle",
                    "threshold": idle_threshold_seconds,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            conn = await asyncpg.connect(self.db_url)

            # Get idle connections
            idle_conns = await conn.fetch(
                f"""
                SELECT pid, usename, state, state_change
                FROM pg_stat_activity
                WHERE state = 'idle'
                  AND state_change < NOW() - INTERVAL '{idle_threshold_seconds} seconds'
                  AND pid != pg_backend_pid()
            """
            )

            # Terminate idle connections
            killed_count = 0
            for row in idle_conns:
                try:
                    # Validate PID is integer before using
                    pid = int(row['pid'])
                    await conn.execute("SELECT pg_terminate_backend($1)", pid)
                    killed_count += 1
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid PID {row['pid']}: {e}")
                except Exception as e:
                    logger.warning(f"Failed to kill PID {row['pid']}: {e}")

            await conn.close()

            self.action_log.append(
                {
                    "action": "kill_idle",
                    "threshold": idle_threshold_seconds,
                    "killed_count": killed_count,
                    "executed": True,
                    "success": True,
                }
            )

            logger.info(f"Killed {killed_count} idle connections")

            return {
                "success": True,
                "killed_count": killed_count,
                "threshold_seconds": idle_threshold_seconds,
            }

        except Exception as e:
            logger.error(f"Connection termination error: {e}")
            return {"success": False, "error": str(e)}

    async def vacuum_analyze(self, table: str, analyze_only: bool = False) -> Dict:
        """Run VACUUM ANALYZE to reclaim space and update statistics.

        Args:
            table: Table name to vacuum
            analyze_only: If True, only update statistics (ANALYZE)
        """
        if self.dry_run_mode:
            action = "ANALYZE" if analyze_only else "VACUUM ANALYZE"
            logger.info(f"DRY-RUN: {action} {table}")
            self.action_log.append(
                {
                    "action": "vacuum_analyze",
                    "table": table,
                    "analyze_only": analyze_only,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            # Validate table name (alphanumeric + underscore only)
            if not table or not table.replace('_', '').replace('.', '').isalnum():
                raise ValueError(f"Invalid table name: {table}. Must be alphanumeric with underscores/dots only.")

            # Use psycopg2 for VACUUM (asyncpg doesn't support it)
            sync_conn = psycopg2.connect(self.db_url)
            sync_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = sync_conn.cursor()

            if analyze_only:
                # Use sql.Identifier to safely quote table name
                query = sql.SQL("ANALYZE {}").format(sql.Identifier(table))
                cursor.execute(query)
                logger.info(f"ANALYZE completed for {table}")
            else:
                # Use sql.Identifier to safely quote table name
                query = sql.SQL("VACUUM ANALYZE {}").format(sql.Identifier(table))
                cursor.execute(query)
                logger.info(f"VACUUM ANALYZE completed for {table}")

            cursor.close()
            sync_conn.close()

            self.action_log.append(
                {
                    "action": "vacuum_analyze",
                    "table": table,
                    "analyze_only": analyze_only,
                    "executed": True,
                    "success": True,
                }
            )

            return {
                "success": True,
                "table": table,
                "operation": "ANALYZE" if analyze_only else "VACUUM ANALYZE",
            }

        except Exception as e:
            logger.error(f"VACUUM error: {e}")
            return {"success": False, "error": str(e)}

    async def get_database_stats(self) -> Dict:
        """Get database performance statistics."""
        try:
            conn = await asyncpg.connect(self.db_url)

            # Connection stats
            conn_stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                    COUNT(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                FROM pg_stat_activity
                WHERE pid != pg_backend_pid()
            """
            )

            # Cache hit ratio
            cache_stats = await conn.fetchrow(
                """
                SELECT
                    SUM(blks_hit) as cache_hits,
                    SUM(blks_read) as disk_reads,
                    ROUND(
                        100.0 * SUM(blks_hit) / NULLIF(SUM(blks_hit) + SUM(blks_read), 0),
                        2
                    ) as cache_hit_ratio
                FROM pg_stat_database
            """
            )

            # Query performance
            slow_queries = await conn.fetch(
                """
                SELECT
                    query,
                    state,
                    EXTRACT(EPOCH FROM (NOW() - query_start)) as duration_seconds
                FROM pg_stat_activity
                WHERE state = 'active'
                  AND pid != pg_backend_pid()
                  AND query_start < NOW() - INTERVAL '5 seconds'
                ORDER BY duration_seconds DESC
                LIMIT 5
            """
            )

            # Database size
            db_size = await conn.fetchrow(
                """
                SELECT pg_database_size(current_database()) as size_bytes
            """
            )

            await conn.close()

            return {
                "success": True,
                "connections": {
                    "total": conn_stats["total_connections"],
                    "active": conn_stats["active_connections"],
                    "idle": conn_stats["idle_connections"],
                    "waiting": conn_stats["waiting_connections"],
                },
                "cache": {
                    "hit_ratio_percent": float(cache_stats["cache_hit_ratio"] or 0),
                    "hits": cache_stats["cache_hits"],
                    "disk_reads": cache_stats["disk_reads"],
                },
                "slow_queries": [
                    {
                        "query": q["query"][:200],
                        "duration_seconds": float(q["duration_seconds"]),
                    }
                    for q in slow_queries
                ],
                "database_size_mb": round(db_size["size_bytes"] / (1024 * 1024), 2),
            }

        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {"success": False, "error": str(e)}

    async def adjust_work_mem(self, work_mem_mb: int) -> Dict:
        """Adjust work_mem for current session (affects sort/hash operations).

        Args:
            work_mem_mb: Memory for query operations in MB (4-256)
        """
        if self.dry_run_mode:
            logger.info(f"DRY-RUN: SET work_mem = {work_mem_mb}MB")
            self.action_log.append(
                {
                    "action": "adjust_work_mem",
                    "work_mem_mb": work_mem_mb,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            # Validate work_mem_mb is integer in valid range
            if not isinstance(work_mem_mb, int) or not (4 <= work_mem_mb <= 256):
                raise ValueError(f"Invalid work_mem_mb: {work_mem_mb}. Must be int 4-256.")

            conn = await asyncpg.connect(self.db_url)

            # Set work_mem for this session (safe: validated as int, explicitly cast)
            work_mem_value = f"{int(work_mem_mb)}MB"
            await conn.execute(f"SET work_mem = '{work_mem_value}';")

            # Verify setting
            result = await conn.fetchval("SHOW work_mem;")

            await conn.close()

            self.action_log.append(
                {
                    "action": "adjust_work_mem",
                    "work_mem_mb": work_mem_mb,
                    "executed": True,
                    "success": True,
                }
            )

            logger.info(f"work_mem set to {result}")

            return {"success": True, "work_mem": result}

        except Exception as e:
            logger.error(f"work_mem adjustment error: {e}")
            return {"success": False, "error": str(e)}

    def get_action_log(self) -> List[Dict]:
        """Return action history for audit."""
        return self.action_log
