"""
Decision Repository - PFC Persistence Layer

Repository pattern for PostgreSQL with CRUD operations for PFC decisions.

Components:
- DecisionRepository: Core CRUD operations
- DecisionQueryService: Specialized queries and analytics

Author: Juan Carlos de Souza
Lei Governante: Constituição Vértice v2.7
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID
import json

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from psycopg2.pool import ThreadedConnectionPool

from consciousness.prefrontal_cortex import OrchestratedDecision
from consciousness.tom_engine import UserMentalState, EmotionalState
from compassion.event_detector import SufferingEvent
from compassion.compassion_planner import CompassionPlan

logger = logging.getLogger(__name__)


class DecisionRepository:
    """
    Repository for PFC orchestrated decisions.

    Manages PostgreSQL connection and CRUD operations for:
    - Orchestrated decisions (ToM + Compassion + DDL + MIP)
    - User mental states
    - Suffering events
    - Compassion plans
    - Full decision history with audit trail

    Serves Lei II: Auditoria e rastreabilidade completas.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "vertice_consciousness",
        user: str = "postgres",
        password: str = "postgres",
        min_connections: int = 1,
        max_connections: int = 10,
    ):
        """
        Initialize repository with connection pool.

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Username
            password: Password
            min_connections: Minimum connections in pool
            max_connections: Maximum connections in pool
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

        self.pool: Optional[ThreadedConnectionPool] = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize connection pool and create schema.

        Raises:
            psycopg2.Error: If connection fails
        """
        if self._initialized:
            logger.warning("Decision repository already initialized")
            return

        try:
            logger.info(f"Connecting to PostgreSQL: {self.host}:{self.port}/{self.database}")

            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=10,
            )

            # Test connection
            conn = self.pool.getconn()
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            finally:
                self.pool.putconn(conn)

            self._initialized = True
            logger.info("✅ PostgreSQL connection pool established")

            # Create schema
            self._create_schema()

        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    def close(self) -> None:
        """Close all connections in pool."""
        if self.pool:
            self.pool.closeall()
            self._initialized = False
            logger.info("PostgreSQL connection pool closed")

    def _create_schema(self) -> None:
        """
        Create database schema for PFC decisions.

        Tables:
        - decisions: Main orchestrated decisions
        - mental_states: ToM inferences
        - suffering_events: Compassion detections
        - compassion_plans: Intervention plans
        - ethical_verdicts: MIP evaluation results (if available)
        """
        if not self.pool:
            return

        schema_sql = """
        -- Main decisions table
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            final_decision VARCHAR(50) NOT NULL,
            rationale TEXT NOT NULL,
            requires_escalation BOOLEAN NOT NULL,
            confidence FLOAT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            action_description TEXT,
            action_plan_id UUID,
            action_plan_name VARCHAR(255),
            mip_enabled BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Indexes
            CONSTRAINT decisions_confidence_check CHECK (confidence >= 0 AND confidence <= 1)
        );

        CREATE INDEX IF NOT EXISTS idx_decisions_user_id ON decisions(user_id);
        CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp DESC);
        CREATE INDEX IF NOT EXISTS idx_decisions_escalation ON decisions(requires_escalation) WHERE requires_escalation = TRUE;
        CREATE INDEX IF NOT EXISTS idx_decisions_action_plan ON decisions(action_plan_id) WHERE action_plan_id IS NOT NULL;

        -- Mental states table (ToM)
        CREATE TABLE IF NOT EXISTS mental_states (
            state_id UUID PRIMARY KEY,
            decision_id UUID REFERENCES decisions(decision_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            emotional_state VARCHAR(50) NOT NULL,
            intent VARCHAR(255),
            needs_assistance BOOLEAN NOT NULL,
            confidence FLOAT NOT NULL,
            timestamp TIMESTAMP NOT NULL,

            CONSTRAINT mental_states_confidence_check CHECK (confidence >= 0 AND confidence <= 1)
        );

        CREATE INDEX IF NOT EXISTS idx_mental_states_decision ON mental_states(decision_id);
        CREATE INDEX IF NOT EXISTS idx_mental_states_user ON mental_states(user_id);

        -- Suffering events table (Compassion)
        CREATE TABLE IF NOT EXISTS suffering_events (
            event_id UUID PRIMARY KEY,
            decision_id UUID REFERENCES decisions(decision_id) ON DELETE CASCADE,
            agent_id UUID NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            severity INT NOT NULL,
            description TEXT NOT NULL,
            detected_from VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            context JSONB,

            CONSTRAINT suffering_events_severity_check CHECK (severity >= 1 AND severity <= 10)
        );

        CREATE INDEX IF NOT EXISTS idx_suffering_events_decision ON suffering_events(decision_id);
        CREATE INDEX IF NOT EXISTS idx_suffering_events_severity ON suffering_events(severity DESC);

        -- Compassion plans table
        CREATE TABLE IF NOT EXISTS compassion_plans (
            plan_id UUID PRIMARY KEY,
            decision_id UUID REFERENCES decisions(decision_id) ON DELETE CASCADE,
            event_id UUID NOT NULL,
            intervention_type VARCHAR(50) NOT NULL,
            priority INT NOT NULL,
            description TEXT NOT NULL,
            expected_outcome TEXT,
            created_at TIMESTAMP NOT NULL,

            CONSTRAINT compassion_plans_priority_check CHECK (priority >= 1 AND priority <= 10)
        );

        CREATE INDEX IF NOT EXISTS idx_compassion_plans_decision ON compassion_plans(decision_id);
        CREATE INDEX IF NOT EXISTS idx_compassion_plans_priority ON compassion_plans(priority DESC);

        -- Constitutional checks table (DDL)
        CREATE TABLE IF NOT EXISTS constitutional_checks (
            check_id SERIAL PRIMARY KEY,
            decision_id UUID REFERENCES decisions(decision_id) ON DELETE CASCADE,
            compliant BOOLEAN NOT NULL,
            explanation TEXT,
            violations JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_constitutional_checks_decision ON constitutional_checks(decision_id);
        CREATE INDEX IF NOT EXISTS idx_constitutional_checks_violations ON constitutional_checks(compliant) WHERE compliant = FALSE;

        -- Ethical verdicts table (MIP) - optional
        CREATE TABLE IF NOT EXISTS ethical_verdicts (
            verdict_id UUID PRIMARY KEY,
            decision_id UUID REFERENCES decisions(decision_id) ON DELETE CASCADE,
            plan_id UUID NOT NULL,
            status VARCHAR(50) NOT NULL,
            aggregate_score FLOAT,
            confidence FLOAT NOT NULL,
            kantian_score FLOAT,
            utilitarian_score FLOAT,
            virtue_score FLOAT,
            principialism_score FLOAT,
            summary TEXT,
            detailed_reasoning TEXT,
            conflicts_detected JSONB,
            requires_human_review BOOLEAN DEFAULT FALSE,
            escalation_reason TEXT,
            evaluation_duration_ms FLOAT,
            evaluated_at TIMESTAMP NOT NULL,

            CONSTRAINT ethical_verdicts_confidence_check CHECK (confidence >= 0 AND confidence <= 1)
        );

        CREATE INDEX IF NOT EXISTS idx_ethical_verdicts_decision ON ethical_verdicts(decision_id);
        CREATE INDEX IF NOT EXISTS idx_ethical_verdicts_status ON ethical_verdicts(status);
        CREATE INDEX IF NOT EXISTS idx_ethical_verdicts_human_review ON ethical_verdicts(requires_human_review) WHERE requires_human_review = TRUE;
        """

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            cursor.close()
            logger.info("✅ Database schema created/verified")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Schema creation failed: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    # ============================================================================
    # DECISION OPERATIONS
    # ============================================================================

    def save_decision(self, decision: OrchestratedDecision) -> UUID:
        """
        Save complete orchestrated decision to database.

        Args:
            decision: OrchestratedDecision object

        Returns:
            UUID of saved decision

        Raises:
            psycopg2.Error: If save fails
        """
        if not self.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor()

            # 1. Insert main decision
            decision_sql = """
            INSERT INTO decisions (
                decision_id, user_id, final_decision, rationale,
                requires_escalation, confidence, timestamp,
                action_description, action_plan_id, action_plan_name,
                mip_enabled
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            cursor.execute(decision_sql, (
                str(decision.decision_id),
                str(decision.user_id),
                decision.final_decision,
                decision.rationale,
                decision.requires_escalation,
                decision.confidence,
                decision.timestamp,
                decision.metadata.get("action_description"),
                str(decision.metadata.get("action_plan_id")) if decision.metadata.get("action_plan_id") else None,
                decision.metadata.get("action_plan_name"),
                decision.metadata.get("mip_enabled", False),
            ))

            # 2. Insert mental state (ToM)
            if decision.mental_state:
                self._save_mental_state(cursor, decision.decision_id, decision.mental_state)

            # 3. Insert suffering events (Compassion)
            for event in decision.detected_events:
                self._save_suffering_event(cursor, decision.decision_id, event)

            # 4. Insert compassion plans
            for plan in decision.planned_interventions:
                self._save_compassion_plan(cursor, decision.decision_id, plan)

            # 5. Insert constitutional check (DDL)
            if decision.constitutional_check:
                self._save_constitutional_check(cursor, decision.decision_id, decision.constitutional_check)

            # 6. Insert ethical verdict (MIP) if available
            if decision.ethical_verdict:
                self._save_ethical_verdict(cursor, decision.decision_id, decision.ethical_verdict)

            conn.commit()
            cursor.close()

            logger.info(f"✅ Decision saved: {decision.decision_id}")
            return decision.decision_id

        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to save decision: {e}")
            raise
        finally:
            self.pool.putconn(conn)

    def _save_mental_state(self, cursor, decision_id: UUID, state: UserMentalState) -> None:
        """Save mental state to database."""
        sql = """
        INSERT INTO mental_states (
            state_id, decision_id, user_id, emotional_state, intent,
            needs_assistance, confidence, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            str(state.state_id),
            str(decision_id),
            str(state.user_id),
            state.emotional_state.value,
            state.intent,
            state.needs_assistance,
            state.confidence,
            state.inferred_at,  # UserMentalState uses 'inferred_at', not 'timestamp'
        ))

    def _save_suffering_event(self, cursor, decision_id: UUID, event: SufferingEvent) -> None:
        """Save suffering event to database."""
        sql = """
        INSERT INTO suffering_events (
            event_id, decision_id, agent_id, event_type, severity,
            description, detected_from, timestamp, context
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Infer detected_from based on context
        detected_from = "behavior" if "behavioral_signals" in event.context else "text"

        cursor.execute(sql, (
            str(event.event_id),
            str(decision_id),
            str(event.agent_id),
            event.event_type.value,
            event.severity,
            event.description,
            detected_from,
            event.timestamp,
            json.dumps(event.context),
        ))

    def _save_compassion_plan(self, cursor, decision_id: UUID, plan: CompassionPlan) -> None:
        """Save compassion plan to database."""
        sql = """
        INSERT INTO compassion_plans (
            plan_id, decision_id, event_id, intervention_type, priority,
            description, expected_outcome, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        # Adapt CompassionPlan fields to database schema
        description = "; ".join(plan.actions) if plan.actions else "No actions"
        expected_outcome = "; ".join(plan.success_criteria) if plan.success_criteria else "Improved state"

        cursor.execute(sql, (
            str(plan.plan_id),
            str(decision_id),
            str(plan.event.event_id),  # plan.event.event_id, not plan.event_id
            plan.intervention_type.value,
            plan.priority,
            description,
            expected_outcome,
            plan.created_at,
        ))

    def _save_constitutional_check(self, cursor, decision_id: UUID, check: Dict) -> None:
        """Save constitutional check to database."""
        sql = """
        INSERT INTO constitutional_checks (
            decision_id, compliant, explanation, violations
        ) VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql, (
            str(decision_id),
            check["compliant"],
            check["explanation"],
            json.dumps(check["violations"]),
        ))

    def _save_ethical_verdict(self, cursor, decision_id: UUID, verdict) -> None:
        """Save MIP ethical verdict to database."""
        sql = """
        INSERT INTO ethical_verdicts (
            verdict_id, decision_id, plan_id, status, aggregate_score, confidence,
            kantian_score, utilitarian_score, virtue_score, principialism_score,
            summary, detailed_reasoning, conflicts_detected,
            requires_human_review, escalation_reason, evaluation_duration_ms, evaluated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Extract framework scores
        kantian_score = verdict.kantian_score.overall_score if verdict.kantian_score else None
        utilitarian_score = verdict.utilitarian_score.overall_score if verdict.utilitarian_score else None
        virtue_score = verdict.virtue_score.overall_score if verdict.virtue_score else None
        principialism_score = verdict.principialism_score.overall_score if verdict.principialism_score else None

        cursor.execute(sql, (
            str(verdict.id),
            str(decision_id),
            str(verdict.plan_id),
            verdict.status.value,
            verdict.aggregate_score,
            verdict.confidence,
            kantian_score,
            utilitarian_score,
            virtue_score,
            principialism_score,
            verdict.summary,
            verdict.detailed_reasoning,
            json.dumps(verdict.conflicts_detected) if verdict.conflicts_detected else None,
            verdict.requires_human_review,
            verdict.escalation_reason,
            verdict.evaluation_duration_ms,
            verdict.evaluated_at,
        ))

    def get_decision(self, decision_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete decision by ID.

        Args:
            decision_id: Decision UUID

        Returns:
            Dict with full decision data or None
        """
        if not self.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Get main decision
            cursor.execute(
                "SELECT * FROM decisions WHERE decision_id = %s",
                (str(decision_id),)
            )
            decision = cursor.fetchone()

            if not decision:
                return None

            # Get related data
            decision = dict(decision)
            decision["mental_state"] = self._get_mental_state(cursor, decision_id)
            decision["detected_events"] = self._get_suffering_events(cursor, decision_id)
            decision["planned_interventions"] = self._get_compassion_plans(cursor, decision_id)
            decision["constitutional_check"] = self._get_constitutional_check(cursor, decision_id)
            decision["ethical_verdict"] = self._get_ethical_verdict(cursor, decision_id)

            cursor.close()
            return decision

        finally:
            self.pool.putconn(conn)

    def _get_mental_state(self, cursor, decision_id: UUID) -> Optional[Dict]:
        """Get mental state for decision."""
        cursor.execute(
            "SELECT * FROM mental_states WHERE decision_id = %s",
            (str(decision_id),)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def _get_suffering_events(self, cursor, decision_id: UUID) -> List[Dict]:
        """Get suffering events for decision."""
        cursor.execute(
            "SELECT * FROM suffering_events WHERE decision_id = %s",
            (str(decision_id),)
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_compassion_plans(self, cursor, decision_id: UUID) -> List[Dict]:
        """Get compassion plans for decision."""
        cursor.execute(
            "SELECT * FROM compassion_plans WHERE decision_id = %s ORDER BY priority DESC",
            (str(decision_id),)
        )
        return [dict(row) for row in cursor.fetchall()]

    def _get_constitutional_check(self, cursor, decision_id: UUID) -> Optional[Dict]:
        """Get constitutional check for decision."""
        cursor.execute(
            "SELECT * FROM constitutional_checks WHERE decision_id = %s",
            (str(decision_id),)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def _get_ethical_verdict(self, cursor, decision_id: UUID) -> Optional[Dict]:
        """Get ethical verdict for decision."""
        cursor.execute(
            "SELECT * FROM ethical_verdicts WHERE decision_id = %s",
            (str(decision_id),)
        )
        result = cursor.fetchone()
        return dict(result) if result else None

    def get_decisions_for_user(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get recent decisions for a user.

        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of decision summaries
        """
        if not self.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    decision_id, user_id, final_decision, rationale,
                    requires_escalation, confidence, timestamp,
                    action_description, action_plan_name
                FROM decisions
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """, (str(user_id), limit, offset))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)

    def get_escalated_decisions(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get decisions requiring escalation.

        Args:
            since: Only decisions after this timestamp
            limit: Maximum results

        Returns:
            List of escalated decisions
        """
        if not self.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if since:
                cursor.execute("""
                    SELECT * FROM decisions
                    WHERE requires_escalation = TRUE AND timestamp > %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (since, limit))
            else:
                cursor.execute("""
                    SELECT * FROM decisions
                    WHERE requires_escalation = TRUE
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

        finally:
            self.pool.putconn(conn)


class DecisionQueryService:
    """
    Service for specialized decision queries and analytics.

    Provides:
    - Decision statistics and metrics
    - Suffering detection analytics
    - Intervention effectiveness tracking
    - Ethical verdict analysis
    """

    def __init__(self, repo: DecisionRepository):
        """
        Initialize service.

        Args:
            repo: DecisionRepository instance
        """
        self.repo = repo

    def get_decision_statistics(
        self,
        user_id: Optional[UUID] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get decision statistics.

        Args:
            user_id: Filter by user (optional)
            since: Only decisions after this timestamp (optional)

        Returns:
            Dict with statistics
        """
        if not self.repo.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.repo.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Build query with filters
            where_clauses = []
            params = []

            if user_id:
                where_clauses.append("user_id = %s")
                params.append(str(user_id))

            if since:
                where_clauses.append("timestamp > %s")
                params.append(since)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN requires_escalation THEN 1 END) as escalated,
                    COUNT(CASE WHEN final_decision = 'APPROVE' THEN 1 END) as approved,
                    COUNT(CASE WHEN final_decision = 'REJECT' THEN 1 END) as rejected,
                    COUNT(CASE WHEN final_decision = 'INTERVENE' THEN 1 END) as interventions,
                    COUNT(CASE WHEN final_decision = 'ASSIST' THEN 1 END) as assistance,
                    AVG(confidence) as avg_confidence
                FROM decisions
                {where_sql}
            """, tuple(params))

            stats = dict(cursor.fetchone())

            # Calculate rates
            total = stats["total_decisions"]
            if total > 0:
                stats["escalation_rate"] = stats["escalated"] / total
                stats["approval_rate"] = stats["approved"] / total
                stats["rejection_rate"] = stats["rejected"] / total
                stats["intervention_rate"] = stats["interventions"] / total

            cursor.close()
            return stats

        finally:
            self.repo.pool.putconn(conn)

    def get_suffering_analytics(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get suffering detection analytics.

        Args:
            since: Only events after this timestamp (optional)

        Returns:
            Dict with suffering analytics
        """
        if not self.repo.pool:
            raise RuntimeError("Repository not initialized")

        conn = self.repo.pool.getconn()
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            where_sql = "WHERE timestamp > %s" if since else ""
            params = (since,) if since else ()

            cursor.execute(f"""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT agent_id) as affected_agents,
                    AVG(severity) as avg_severity,
                    MAX(severity) as max_severity,
                    COUNT(CASE WHEN severity >= 8 THEN 1 END) as critical_events,
                    event_type,
                    COUNT(*) as count_by_type
                FROM suffering_events
                {where_sql}
                GROUP BY event_type
            """, params)

            results = cursor.fetchall()
            cursor.close()

            analytics = {
                "by_type": [dict(row) for row in results],
                "total_events": sum(row["count_by_type"] for row in results),
            }

            return analytics

        finally:
            self.repo.pool.putconn(conn)
