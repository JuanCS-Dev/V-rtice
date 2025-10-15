"""
Governance Module - Audit Infrastructure Test Suite

Comprehensive tests for AuditLogger, schema management, retention policies,
and audit trail integrity.

Coverage target: 100%

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from .audit_infrastructure import (
    PSYCOPG2_AVAILABLE,
    SCHEMA_SQL,
    AuditLogger,
)
from .base import (
    AuditLogLevel,
    GovernanceAction,
    GovernanceConfig,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def config():
    """Create test configuration."""
    return GovernanceConfig(
        db_host="localhost",
        db_port=5432,
        db_name="test_governance",
        db_user="test_user",
        db_password="test_pass",
        audit_retention_days=2555,  # 7 years
    )


@pytest.fixture
def mock_psycopg2():
    """Mock psycopg2 module."""
    if not PSYCOPG2_AVAILABLE:
        pytest.skip("psycopg2 not available")

    with patch("governance.audit_infrastructure.psycopg2") as mock:
        # Setup mock connection
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [0]  # Default return
        mock_cursor.fetchall.return_value = []  # Default return
        mock.connect.return_value = mock_conn

        yield mock


@pytest.fixture
def audit_logger(config, mock_psycopg2):
    """Create AuditLogger instance."""
    logger = AuditLogger(config)
    return logger


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================


class TestAuditLoggerInit:
    """Test AuditLogger initialization."""

    def test_init_without_psycopg2(self, config):
        """Test initialization fails without psycopg2."""
        with patch("governance.audit_infrastructure.PSYCOPG2_AVAILABLE", False):
            with pytest.raises(ImportError, match="psycopg2 is required"):
                AuditLogger(config)

    def test_init_with_valid_config(self, config, mock_psycopg2):
        """Test successful initialization."""
        logger = AuditLogger(config)

        assert logger.config == config
        assert logger.connection_params["host"] == "localhost"
        assert logger.connection_params["port"] == 5432
        assert logger.connection_params["database"] == "test_governance"
        assert logger.connection_params["user"] == "test_user"
        assert logger.connection_params["password"] == "test_pass"


# ============================================================================
# SCHEMA INITIALIZATION TESTS
# ============================================================================


class TestSchemaInitialization:
    """Test database schema initialization."""

    def test_initialize_schema(self, audit_logger, mock_psycopg2):
        """Test schema initialization executes SQL."""
        audit_logger.initialize_schema()

        # Verify connection was established
        mock_psycopg2.connect.assert_called_once()

        # Verify SQL was executed
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.execute.assert_called_once()

        # Verify SCHEMA_SQL was used
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert executed_sql == SCHEMA_SQL

    def test_schema_creates_all_tables(self):
        """Test schema SQL creates all required tables."""
        required_tables = [
            "audit_logs",
            "policy_violations",
            "whistleblower_reports",
            "erb_decisions",
            "erb_meetings",
            "erb_members",
            "policies",
        ]

        for table in required_tables:
            assert f"CREATE TABLE IF NOT EXISTS {table}" in SCHEMA_SQL

    def test_schema_creates_indexes(self):
        """Test schema creates performance indexes."""
        required_indexes = [
            "idx_audit_logs_timestamp",
            "idx_audit_logs_action",
            "idx_audit_logs_actor",
            "idx_violations_severity",
            "idx_erb_members_active",
        ]

        for index in required_indexes:
            assert index in SCHEMA_SQL


# ============================================================================
# LOGGING TESTS
# ============================================================================


class TestLogging:
    """Test audit logging functionality."""

    def test_log_governance_action(self, audit_logger, mock_psycopg2):
        """Test logging governance action."""
        log_id = audit_logger.log(
            action=GovernanceAction.POLICY_CREATED,
            actor="test_user",
            description="Test policy created",
            target_entity_type="policy",
            target_entity_id="pol-123",
            log_level=AuditLogLevel.INFO,
        )

        assert log_id is not None

        # Verify INSERT was executed
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.execute.assert_called_once()

        # Verify SQL contains required fields
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO audit_logs" in sql_call
        assert "checksum" in sql_call

    def test_log_with_checksum(self, audit_logger):
        """Test checksum calculation for audit log."""
        from governance.base import AuditLog

        log = AuditLog(
            timestamp=datetime(2025, 10, 14, 12, 0, 0),
            action=GovernanceAction.POLICY_CREATED,
            actor="test_user",
            description="Test",
        )

        checksum = audit_logger._calculate_checksum(log)

        # Verify checksum is SHA-256 (64 hex chars)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify deterministic
        checksum2 = audit_logger._calculate_checksum(log)
        assert checksum == checksum2

    def test_log_policy_violation(self, audit_logger, mock_psycopg2):
        """Test logging policy violation."""
        log_id = audit_logger.log(
            action=GovernanceAction.POLICY_VIOLATED,
            actor="system",
            description="Ethical use policy violated",
            target_entity_type="policy_violation",
            target_entity_id="vio-456",
            log_level=AuditLogLevel.WARNING,
            details={"severity": "high", "rule": "RULE-EU-001"},
            ip_address="192.168.1.100",
        )

        assert log_id is not None

    def test_log_erb_decision(self, audit_logger, mock_psycopg2):
        """Test logging ERB decision."""
        log_id = audit_logger.log(
            action=GovernanceAction.ERB_DECISION_MADE,
            actor="erb_chair",
            description="Decision approved",
            target_entity_type="erb_decision",
            target_entity_id="dec-789",
            log_level=AuditLogLevel.INFO,
            details={"decision_type": "approved", "votes_for": 5},
            correlation_id="meeting-123",
        )

        assert log_id is not None

    def test_log_whistleblower_report(self, audit_logger, mock_psycopg2):
        """Test logging whistleblower report."""
        log_id = audit_logger.log(
            action=GovernanceAction.WHISTLEBLOWER_REPORT,
            actor="anonymous",
            description="Ethical violation reported",
            target_entity_type="whistleblower_report",
            target_entity_id="wb-999",
            log_level=AuditLogLevel.CRITICAL,
            details={"severity": "critical", "anonymous": True},
            session_id="session-456",
        )

        assert log_id is not None


# ============================================================================
# QUERYING TESTS
# ============================================================================


class TestQuerying:
    """Test audit log querying."""

    def test_query_logs_no_filters(self, audit_logger, mock_psycopg2):
        """Test querying logs without filters."""
        # Setup mock return
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs()

        assert isinstance(logs, list)

        # Verify query was executed
        mock_cursor.execute.assert_called_once()
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "SELECT * FROM audit_logs" in sql_call
        assert "LIMIT" in sql_call

    def test_query_logs_with_date_range(self, audit_logger, mock_psycopg2):
        """Test querying logs with date range."""
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 14)

        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs(start_date=start_date, end_date=end_date)

        # Verify date filters in SQL
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "timestamp >= %s" in sql_call
        assert "timestamp <= %s" in sql_call

        # Verify parameters
        params = mock_cursor.execute.call_args[0][1]
        assert start_date in params
        assert end_date in params

    def test_query_logs_with_action_filter(self, audit_logger, mock_psycopg2):
        """Test querying logs with action filter."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs(action=GovernanceAction.POLICY_CREATED)

        # Verify action filter
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "action = %s" in sql_call

        params = mock_cursor.execute.call_args[0][1]
        assert "policy_created" in params

    def test_query_logs_with_actor_filter(self, audit_logger, mock_psycopg2):
        """Test querying logs with actor filter."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs(actor="test_user")

        # Verify actor filter
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "actor = %s" in sql_call

        params = mock_cursor.execute.call_args[0][1]
        assert "test_user" in params

    def test_query_logs_with_log_level_filter(self, audit_logger, mock_psycopg2):
        """Test querying logs with log level filter."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs(log_level=AuditLogLevel.CRITICAL)

        # Verify log level filter
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "log_level = %s" in sql_call

        params = mock_cursor.execute.call_args[0][1]
        assert "critical" in params

    def test_query_logs_pagination(self, audit_logger, mock_psycopg2):
        """Test query pagination with limit."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        logs = audit_logger.query_logs(limit=50)

        # Verify limit parameter
        params = mock_cursor.execute.call_args[0][1]
        assert 50 in params


# ============================================================================
# INTEGRITY TESTS
# ============================================================================


class TestIntegrity:
    """Test audit log integrity verification."""

    def test_verify_integrity_valid(self, audit_logger, mock_psycopg2):
        """Test integrity verification for valid log."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [True]

        is_valid = audit_logger.verify_integrity("log-123")

        assert is_valid is True

        # Verify function was called
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "verify_audit_log_integrity" in sql_call

    def test_verify_integrity_tampered(self, audit_logger, mock_psycopg2):
        """Test integrity verification detects tampering."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [False]

        is_valid = audit_logger.verify_integrity("log-456")

        assert is_valid is False

    def test_calculate_checksum_deterministic(self, audit_logger):
        """Test checksum calculation is deterministic."""
        from governance.base import AuditLog

        log = AuditLog(
            timestamp=datetime(2025, 10, 14, 12, 0, 0),
            action=GovernanceAction.POLICY_CREATED,
            actor="test_user",
            description="Test policy",
        )

        checksum1 = audit_logger._calculate_checksum(log)
        checksum2 = audit_logger._calculate_checksum(log)

        assert checksum1 == checksum2

    def test_calculate_checksum_different_inputs(self, audit_logger):
        """Test different inputs produce different checksums."""
        from governance.base import AuditLog

        log1 = AuditLog(
            timestamp=datetime(2025, 10, 14, 12, 0, 0),
            action=GovernanceAction.POLICY_CREATED,
            actor="user1",
            description="Test 1",
        )

        log2 = AuditLog(
            timestamp=datetime(2025, 10, 14, 12, 0, 0),
            action=GovernanceAction.POLICY_CREATED,
            actor="user2",
            description="Test 2",
        )

        checksum1 = audit_logger._calculate_checksum(log1)
        checksum2 = audit_logger._calculate_checksum(log2)

        assert checksum1 != checksum2


# ============================================================================
# RETENTION POLICY TESTS
# ============================================================================


class TestRetention:
    """Test GDPR 7-year retention policy."""

    def test_apply_retention_policy(self, audit_logger, mock_psycopg2):
        """Test retention policy execution."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [42]  # 42 logs deleted

        deleted_count = audit_logger.apply_retention_policy()

        assert deleted_count == 42

        # Verify function was called
        sql_call = mock_cursor.execute.call_args[0][0]
        assert "apply_retention_policy" in sql_call

    def test_retention_deletes_old_logs(self):
        """Test retention policy targets 7-year old logs."""
        # Verify SCHEMA_SQL contains 7-year retention
        assert "7 years" in SCHEMA_SQL
        assert "INTERVAL '7 years'" in SCHEMA_SQL

    def test_retention_no_logs_to_delete(self, audit_logger, mock_psycopg2):
        """Test retention policy with no old logs."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = [0]  # No logs deleted

        deleted_count = audit_logger.apply_retention_policy()

        assert deleted_count == 0


# ============================================================================
# EXPORT TESTS
# ============================================================================


class TestExport:
    """Test audit log export for external auditors."""

    def test_export_json_format(self, audit_logger, mock_psycopg2):
        """Test export in JSON format."""
        # Setup mock data
        mock_logs = [
            {
                "log_id": "log-1",
                "timestamp": datetime(2025, 10, 14),
                "action": "policy_created",
                "actor": "user1",
            },
            {
                "log_id": "log-2",
                "timestamp": datetime(2025, 10, 13),
                "action": "policy_violated",
                "actor": "system",
            },
        ]

        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = mock_logs

        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 14)

        export_data = audit_logger.export_for_auditor(
            start_date=start_date, end_date=end_date, output_format="json"
        )

        # Verify JSON format
        parsed = json.loads(export_data)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]["log_id"] == "log-1"

    def test_export_csv_format(self, audit_logger, mock_psycopg2):
        """Test export in CSV format."""
        mock_logs = [
            {"log_id": "log-1", "action": "policy_created", "actor": "user1"},
            {"log_id": "log-2", "action": "policy_violated", "actor": "system"},
        ]

        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = mock_logs

        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 14)

        export_data = audit_logger.export_for_auditor(
            start_date=start_date, end_date=end_date, output_format="csv"
        )

        # Verify CSV format
        lines = export_data.split("\n")
        assert len(lines) >= 2  # Header + data rows
        assert "log_id" in lines[0]
        assert "log-1" in lines[1]

    def test_export_csv_empty_data(self, audit_logger, mock_psycopg2):
        """Test CSV export with no data."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 14)

        export_data = audit_logger.export_for_auditor(
            start_date=start_date, end_date=end_date, output_format="csv"
        )

        assert export_data == ""

    def test_export_invalid_format(self, audit_logger, mock_psycopg2):
        """Test export with invalid format raises error."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []

        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 14)

        with pytest.raises(ValueError, match="Unsupported format"):
            audit_logger.export_for_auditor(
                start_date=start_date, end_date=end_date, output_format="xml"
            )


# ============================================================================
# STATISTICS TESTS
# ============================================================================


class TestStatistics:
    """Test audit log statistics generation."""

    def test_get_statistics(self, audit_logger, mock_psycopg2):
        """Test statistics generation."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        # Mock multiple queries
        mock_cursor.fetchone.side_effect = [
            [1000],  # total_logs
            [150],  # logs_last_30_days
        ]

        mock_cursor.fetchall.side_effect = [
            [("policy_created", 50), ("policy_violated", 30)],  # top_actions
            [("user1", 100), ("user2", 80)],  # top_actors
        ]

        stats = audit_logger.get_statistics()

        # Verify structure
        assert "total_logs" in stats
        assert "logs_last_30_days" in stats
        assert "top_actions" in stats
        assert "top_actors" in stats

    def test_get_statistics_empty_database(self, audit_logger, mock_psycopg2):
        """Test statistics with empty database."""
        mock_conn = mock_psycopg2.connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        mock_cursor.fetchone.side_effect = [
            [0],  # total_logs
            [0],  # logs_last_30_days
        ]

        mock_cursor.fetchall.side_effect = [
            [],  # top_actions
            [],  # top_actors
        ]

        stats = audit_logger.get_statistics()

        assert stats["total_logs"] == 0
        assert stats["logs_last_30_days"] == 0
        assert stats["top_actions"] == {}
        assert stats["top_actors"] == {}


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
