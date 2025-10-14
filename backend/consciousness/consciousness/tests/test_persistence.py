"""
Tests for PFC decision persistence layer

Tests complete persistence flow: Save → Retrieve → Query
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from consciousness.prefrontal_cortex import PrefrontalCortex, OrchestratedDecision
from consciousness.tom_engine import EmotionalState
from consciousness.persistence import DecisionRepository, DecisionQueryService
from mip.models import ActionPlan, ActionStep, Stakeholder, StakeholderType, ActionCategory


class TestDecisionRepository:
    """Tests for DecisionRepository."""

    @pytest.fixture
    def mock_pool(self):
        """Create mock connection pool."""
        pool = Mock()
        conn = Mock()
        cursor = Mock()

        # Setup mock chain
        pool.getconn.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        cursor.fetchall.return_value = []

        return pool, conn, cursor

    def test_repository_initialization(self, mock_pool):
        """Test repository initializes correctly."""
        repo = DecisionRepository(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )

        assert repo.host == "localhost"
        assert repo.port == 5432
        assert repo.database == "test_db"
        assert not repo._initialized

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_repository_initialize_creates_pool(self, mock_pool_class):
        """Test initialize creates connection pool."""
        # Setup mock
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        repo = DecisionRepository()
        repo.initialize()

        assert repo._initialized
        assert repo.pool is not None
        mock_cursor.execute.assert_called()  # Schema creation

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_repository_close(self, mock_pool_class):
        """Test close shuts down pool."""
        mock_pool = Mock()
        mock_pool_class.return_value = mock_pool

        # Mock connection for initialize
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        repo = DecisionRepository()
        repo.initialize()
        repo.close()

        assert not repo._initialized
        mock_pool.closeall.assert_called_once()

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_save_decision_basic(self, mock_pool_class):
        """Test saving a basic decision."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        repo = DecisionRepository()
        repo.initialize()

        # Create simple decision
        decision = OrchestratedDecision(
            decision_id=uuid4(),
            user_id=uuid4(),
            mental_state=None,
            detected_events=[],
            planned_interventions=[],
            constitutional_check=None,
            final_decision="PROCEED",
            rationale="Test decision",
            requires_escalation=False,
            confidence=0.8,
            metadata={"test": "data"}
        )

        result = repo.save_decision(decision)

        assert result == decision.decision_id
        # Verify INSERT was called
        assert mock_cursor.execute.call_count >= 1
        # commit() called at least once (may be called in init + save)
        assert mock_conn.commit.call_count >= 1

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_save_decision_with_all_components(self, mock_pool_class):
        """Test saving decision with all components."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        repo = DecisionRepository()
        repo.initialize()

        # Create full decision using PFC
        pfc = PrefrontalCortex(enable_mip=False)  # Without MIP for simpler test
        user_id = uuid4()

        signals = {
            "error_count": 2,
            "retry_count": 0,
            "response_time_ms": 1000,
            "task_success": False
        }

        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals=signals,
            action_description="User experiencing errors"
        )

        result = repo.save_decision(decision)

        assert result == decision.decision_id
        # Should have multiple inserts (decision + mental_state + events + plans + constitutional_check)
        assert mock_cursor.execute.call_count >= 3
        # commit() called at least once (may be called in init + save)
        assert mock_conn.commit.call_count >= 1

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_save_decision_rollback_on_error(self, mock_pool_class):
        """Test save rolls back on error."""
        # Setup mocks to fail
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Let initialize() succeed, but make save fail
        call_count = [0]
        def side_effect_fn(*args, **kwargs):
            call_count[0] += 1
            # First 2 calls are from initialize (test connection + schema)
            if call_count[0] > 2:
                raise Exception("Database error")

        mock_cursor.execute.side_effect = side_effect_fn

        repo = DecisionRepository()
        repo.initialize()

        decision = OrchestratedDecision(
            decision_id=uuid4(),
            user_id=uuid4(),
            mental_state=None,
            detected_events=[],
            planned_interventions=[],
            constitutional_check=None,
            final_decision="PROCEED",
            rationale="Test",
            requires_escalation=False,
            confidence=0.8,
            metadata={}
        )

        with pytest.raises(Exception, match="Database error"):
            repo.save_decision(decision)

        mock_conn.rollback.assert_called_once()

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_get_decision(self, mock_pool_class):
        """Test retrieving decision by ID."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock decision data
        decision_id = uuid4()
        user_id = uuid4()

        mock_cursor.fetchone.return_value = {
            "decision_id": str(decision_id),
            "user_id": str(user_id),
            "final_decision": "PROCEED",
            "rationale": "Test rationale",
            "requires_escalation": False,
            "confidence": 0.8,
            "timestamp": datetime.utcnow(),
            "action_description": "Test action",
            "action_plan_id": None,
            "action_plan_name": None,
            "mip_enabled": False,
        }

        # Mock empty related data
        mock_cursor.fetchall.return_value = []

        repo = DecisionRepository()
        repo.initialize()

        result = repo.get_decision(decision_id)

        assert result is not None
        assert result["decision_id"] == str(decision_id)
        assert result["final_decision"] == "PROCEED"
        mock_cursor.execute.assert_called()  # SELECT query

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_get_decision_not_found(self, mock_pool_class):
        """Test get_decision returns None for non-existent ID."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        repo = DecisionRepository()
        repo.initialize()

        result = repo.get_decision(uuid4())

        assert result is None

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_get_decisions_for_user(self, mock_pool_class):
        """Test retrieving decisions for a user."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock multiple decisions
        user_id = uuid4()
        mock_cursor.fetchall.return_value = [
            {
                "decision_id": str(uuid4()),
                "user_id": str(user_id),
                "final_decision": "PROCEED",
                "rationale": "Test 1",
                "requires_escalation": False,
                "confidence": 0.8,
                "timestamp": datetime.utcnow(),
                "action_description": "Action 1",
                "action_plan_name": None,
            },
            {
                "decision_id": str(uuid4()),
                "user_id": str(user_id),
                "final_decision": "ASSIST",
                "rationale": "Test 2",
                "requires_escalation": False,
                "confidence": 0.7,
                "timestamp": datetime.utcnow(),
                "action_description": "Action 2",
                "action_plan_name": None,
            },
        ]

        repo = DecisionRepository()
        repo.initialize()

        results = repo.get_decisions_for_user(user_id, limit=10)

        assert len(results) == 2
        assert all(r["user_id"] == str(user_id) for r in results)

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_get_escalated_decisions(self, mock_pool_class):
        """Test retrieving escalated decisions."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock escalated decisions
        mock_cursor.fetchall.return_value = [
            {
                "decision_id": str(uuid4()),
                "user_id": str(uuid4()),
                "final_decision": "REJECT",
                "rationale": "Constitutional violation",
                "requires_escalation": True,
                "confidence": 0.95,
                "timestamp": datetime.utcnow(),
            },
            {
                "decision_id": str(uuid4()),
                "user_id": str(uuid4()),
                "final_decision": "ESCALATE",
                "rationale": "MIP escalated",
                "requires_escalation": True,
                "confidence": 0.85,
                "timestamp": datetime.utcnow(),
            },
        ]

        repo = DecisionRepository()
        repo.initialize()

        results = repo.get_escalated_decisions(limit=100)

        assert len(results) == 2
        assert all(r["requires_escalation"] is True for r in results)

    @patch('consciousness.persistence.decision_repository.ThreadedConnectionPool')
    def test_get_escalated_decisions_with_since_filter(self, mock_pool_class):
        """Test escalated decisions filtered by timestamp."""
        # Setup mocks
        mock_pool = Mock()
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_pool_class.return_value = mock_pool
        mock_pool.getconn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        repo = DecisionRepository()
        repo.initialize()

        since = datetime.utcnow() - timedelta(hours=1)
        results = repo.get_escalated_decisions(since=since, limit=50)

        # Verify query was called with timestamp filter
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        assert "timestamp > %s" in call_args[0]
        assert since in call_args[1]


class TestDecisionQueryService:
    """Tests for DecisionQueryService."""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository."""
        repo = Mock(spec=DecisionRepository)
        pool = Mock()
        conn = Mock()
        cursor = Mock()

        repo.pool = pool
        pool.getconn.return_value = conn
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = {
            "total_decisions": 100,
            "escalated": 10,
            "approved": 60,
            "rejected": 5,
            "interventions": 15,
            "assistance": 10,
            "avg_confidence": 0.75,
        }
        cursor.fetchall.return_value = []

        return repo, pool, conn, cursor

    def test_query_service_initialization(self, mock_repo):
        """Test query service initializes."""
        repo, _, _, _ = mock_repo
        service = DecisionQueryService(repo)

        assert service.repo == repo

    def test_get_decision_statistics(self, mock_repo):
        """Test decision statistics calculation."""
        repo, pool, conn, cursor = mock_repo

        service = DecisionQueryService(repo)
        stats = service.get_decision_statistics()

        assert stats["total_decisions"] == 100
        assert stats["escalated"] == 10
        assert stats["escalation_rate"] == 0.1
        assert stats["approval_rate"] == 0.6
        assert stats["avg_confidence"] == 0.75

        cursor.execute.assert_called_once()
        pool.putconn.assert_called_once_with(conn)

    def test_get_decision_statistics_with_filters(self, mock_repo):
        """Test statistics with user and timestamp filters."""
        repo, pool, conn, cursor = mock_repo

        service = DecisionQueryService(repo)
        user_id = uuid4()
        since = datetime.utcnow() - timedelta(days=7)

        stats = service.get_decision_statistics(user_id=user_id, since=since)

        # Verify query includes WHERE clauses
        call_args = cursor.execute.call_args[0]
        assert "WHERE" in call_args[0]
        assert "user_id = %s" in call_args[0]
        assert "timestamp > %s" in call_args[0]
        assert str(user_id) in call_args[1]
        assert since in call_args[1]

    def test_get_suffering_analytics(self, mock_repo):
        """Test suffering detection analytics."""
        repo, pool, conn, cursor = mock_repo

        # Mock suffering data
        cursor.fetchall.return_value = [
            {
                "total_events": 50,
                "affected_agents": 20,
                "avg_severity": 6.5,
                "max_severity": 10,
                "critical_events": 5,
                "event_type": "distress",
                "count_by_type": 30,
            },
            {
                "total_events": 50,
                "affected_agents": 20,
                "avg_severity": 6.5,
                "max_severity": 10,
                "critical_events": 5,
                "event_type": "confusion",
                "count_by_type": 20,
            },
        ]

        service = DecisionQueryService(repo)
        analytics = service.get_suffering_analytics()

        assert "by_type" in analytics
        assert len(analytics["by_type"]) == 2
        assert analytics["total_events"] == 50

        cursor.execute.assert_called_once()

    def test_get_suffering_analytics_with_since_filter(self, mock_repo):
        """Test suffering analytics with timestamp filter."""
        repo, pool, conn, cursor = mock_repo
        cursor.fetchall.return_value = []

        service = DecisionQueryService(repo)
        since = datetime.utcnow() - timedelta(days=1)

        analytics = service.get_suffering_analytics(since=since)

        # Verify query includes WHERE clause
        call_args = cursor.execute.call_args[0]
        assert "WHERE timestamp > %s" in call_args[0]
        assert since in call_args[1]


class TestPersistenceEndToEnd:
    """End-to-end persistence tests (requires real database)."""

    @pytest.mark.skip(reason="Requires PostgreSQL database - run manually")
    def test_e2e_save_and_retrieve_decision(self):
        """E2E test: save decision and retrieve it."""
        # Initialize real repository
        repo = DecisionRepository(
            host="localhost",
            port=5432,
            database="vertice_test",
            user="postgres",
            password="postgres"
        )
        repo.initialize()

        try:
            # Create decision via PFC
            pfc = PrefrontalCortex(enable_mip=False)
            user_id = uuid4()

            signals = {
                "error_count": 3,
                "retry_count": 2,
                "task_success": False
            }

            decision = pfc.orchestrate_decision(
                user_id=user_id,
                behavioral_signals=signals,
                action_description="Test action"
            )

            # Save to database
            saved_id = repo.save_decision(decision)
            assert saved_id == decision.decision_id

            # Retrieve from database
            retrieved = repo.get_decision(decision.decision_id)
            assert retrieved is not None
            assert retrieved["decision_id"] == str(decision.decision_id)
            assert retrieved["user_id"] == str(user_id)
            assert retrieved["final_decision"] == decision.final_decision

            # Clean up
            # (In production, would have proper cleanup/teardown)

        finally:
            repo.close()

    @pytest.mark.skip(reason="Requires PostgreSQL database - run manually")
    def test_e2e_query_statistics(self):
        """E2E test: query decision statistics."""
        repo = DecisionRepository(
            host="localhost",
            port=5432,
            database="vertice_test",
            user="postgres",
            password="postgres"
        )
        repo.initialize()

        try:
            service = DecisionQueryService(repo)

            # Get overall statistics
            stats = service.get_decision_statistics()

            assert "total_decisions" in stats
            assert "escalation_rate" in stats
            assert isinstance(stats["total_decisions"], int)

        finally:
            repo.close()
