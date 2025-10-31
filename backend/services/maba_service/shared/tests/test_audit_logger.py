"""
Comprehensive tests for audit_logger.py
Targeting: 100% coverage (106 stmts, 20 branches)
"""

import json
from unittest.mock import Mock, patch

import pytest

from backend.shared.audit_logger import (
    AuditConfig,
    AuditLogger,
    audit_context,
    get_audit_logger,
)

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def mock_psycopg2():
    """Mock psycopg2 module."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", True):
        with patch("backend.shared.audit_logger.psycopg2") as mock_pg:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_pg.connect.return_value = mock_conn
            yield mock_pg, mock_conn, mock_cursor


@pytest.fixture
def mock_psycopg2_unavailable():
    """Mock psycopg2 unavailable."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        yield


@pytest.fixture
def audit_logger_no_db():
    """AuditLogger without DB connection."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        logger = AuditLogger(log_to_file=False)
        yield logger
        logger.close()


@pytest.fixture
def audit_logger_with_db(mock_psycopg2):
    """AuditLogger with mocked DB."""
    mock_pg, mock_conn, mock_cursor = mock_psycopg2
    logger = AuditLogger(log_to_file=False)
    logger.db_connection = mock_conn
    yield logger, mock_conn, mock_cursor
    logger.close()


# ==============================================================================
# TEST: AuditConfig
# ==============================================================================


def test_audit_config_defaults():
    """Test AuditConfig default values."""
    assert AuditConfig.DB_HOST == "localhost"
    assert AuditConfig.DB_PORT == 5432
    assert AuditConfig.DB_NAME == "vertice_audit"
    assert AuditConfig.DB_USER == "vertice"
    assert AuditConfig.DB_PASSWORD == "changeme"
    assert AuditConfig.TABLE_NAME == "audit_logs"
    assert AuditConfig.RETENTION_DAYS == 365
    assert AuditConfig.LOG_TO_FILE is True
    assert AuditConfig.LOG_FILE == "/var/log/vertice/audit.log"
    assert AuditConfig.FAIL_OPEN is True


# ==============================================================================
# TEST: AuditLogger.__init__
# ==============================================================================


def test_init_default_config(mock_psycopg2_unavailable):
    """Test AuditLogger initialization with default config."""
    logger = AuditLogger(log_to_file=False)
    assert logger.db_config is not None
    assert logger.db_config["host"] == AuditConfig.DB_HOST
    assert logger.db_config["port"] == AuditConfig.DB_PORT
    assert logger.log_to_file is False
    logger.close()


def test_init_custom_config(mock_psycopg2_unavailable):
    """Test AuditLogger initialization with custom config."""
    custom_config = {
        "host": "custom.host",
        "port": 5433,
        "dbname": "custom_db",
        "user": "custom_user",
        "password": "custom_pass",
    }
    logger = AuditLogger(db_config=custom_config, log_to_file=False)
    assert logger.db_config == custom_config
    logger.close()


def test_init_with_file_logging():
    """Test AuditLogger initialization with file logging."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with patch("logging.FileHandler") as mock_handler:
            logger = AuditLogger(log_to_file=True)
            assert logger.log_to_file is True
            assert logger.file_logger is not None
            logger.close()


def test_init_file_logger_already_has_handlers():
    """Test file logger when handlers already exist."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with patch("logging.FileHandler") as mock_handler:
            logger1 = AuditLogger(log_to_file=True)
            # Second logger should not add handler again
            logger2 = AuditLogger(log_to_file=True)
            logger1.close()
            logger2.close()


# ==============================================================================
# TEST: Database Connection
# ==============================================================================


def test_connect_db_success(mock_psycopg2):
    """Test successful database connection."""
    mock_pg, mock_conn, _ = mock_psycopg2
    logger = AuditLogger(log_to_file=False)
    assert logger.db_connection is not None
    mock_pg.connect.assert_called_once()
    logger.close()


def test_connect_db_failure_fail_open(mock_psycopg2):
    """Test DB connection failure with FAIL_OPEN=True."""
    mock_pg, _, _ = mock_psycopg2
    mock_pg.connect.side_effect = Exception("Connection error")

    with patch.object(AuditConfig, "FAIL_OPEN", True):
        logger = AuditLogger(log_to_file=False)
        assert logger.db_connection is None
        logger.close()


def test_connect_db_failure_fail_closed(mock_psycopg2):
    """Test DB connection failure with FAIL_OPEN=False."""
    mock_pg, _, _ = mock_psycopg2
    mock_pg.connect.side_effect = Exception("Connection error")

    with patch.object(AuditConfig, "FAIL_OPEN", False):
        with pytest.raises(Exception, match="Connection error"):
            AuditLogger(log_to_file=False)


def test_connect_db_postgres_unavailable():
    """Test DB connection when psycopg2 not available."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        logger = AuditLogger(log_to_file=False)
        assert logger.db_connection is None
        logger.close()


# ==============================================================================
# TEST: _log_to_db
# ==============================================================================


def test_log_to_db_success(audit_logger_with_db):
    """Test successful database logging."""
    logger, mock_conn, mock_cursor = audit_logger_with_db

    audit_entry = {
        "timestamp": "2025-01-01T00:00:00",
        "event_type": "test_event",
        "user_id": 123,
        "username": "testuser",
        "ip_address": "192.168.1.1",
        "action": "test_action",
        "resource": "test_resource",
        "details": {"key": "value"},
        "success": True,
        "severity": "info",
        "session_id": "session123",
        "request_id": "req123",
        "user_agent": "TestAgent/1.0",
    }

    result = logger._log_to_db(audit_entry)
    assert result is True
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_log_to_db_no_connection(audit_logger_no_db):
    """Test database logging when no connection."""
    audit_entry = {"event_type": "test"}
    result = audit_logger_no_db._log_to_db(audit_entry)
    assert result is False


def test_log_to_db_failure_fail_open(audit_logger_with_db):
    """Test DB logging failure with FAIL_OPEN=True."""
    logger, mock_conn, mock_cursor = audit_logger_with_db
    mock_cursor.execute.side_effect = Exception("DB error")

    with patch.object(AuditConfig, "FAIL_OPEN", True):
        audit_entry = {"event_type": "test"}
        result = logger._log_to_db(audit_entry)
        assert result is False


def test_log_to_db_failure_fail_closed(audit_logger_with_db):
    """Test DB logging failure with FAIL_OPEN=False."""
    logger, mock_conn, mock_cursor = audit_logger_with_db
    mock_cursor.execute.side_effect = Exception("DB error")

    with patch.object(AuditConfig, "FAIL_OPEN", False):
        audit_entry = {"event_type": "test"}
        with pytest.raises(Exception, match="DB error"):
            logger._log_to_db(audit_entry)


# ==============================================================================
# TEST: _log_to_file_backup
# ==============================================================================


def test_log_to_file_backup_success():
    """Test file backup logging."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with patch("logging.FileHandler"):
            logger = AuditLogger(log_to_file=True)
            logger.file_logger = Mock()

            audit_entry = {"event_type": "test", "user_id": 123}
            logger._log_to_file_backup(audit_entry)

            logger.file_logger.info.assert_called_once()
            args = logger.file_logger.info.call_args[0]
            assert json.loads(args[0]) == audit_entry
            logger.close()


def test_log_to_file_backup_disabled(audit_logger_no_db):
    """Test file backup when disabled."""
    audit_entry = {"event_type": "test"}
    # Should not raise
    audit_logger_no_db._log_to_file_backup(audit_entry)


def test_log_to_file_backup_failure():
    """Test file backup logging failure."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with patch("logging.FileHandler"):
            logger = AuditLogger(log_to_file=True)
            logger.file_logger = Mock()
            logger.file_logger.info.side_effect = Exception("File error")

            audit_entry = {"event_type": "test"}
            # Should not raise (error logged internally)
            logger._log_to_file_backup(audit_entry)
            logger.close()


# ==============================================================================
# TEST: log (generic)
# ==============================================================================


def test_log_generic(audit_logger_no_db):
    """Test generic log method."""
    with patch.object(audit_logger_no_db, "_log_to_db") as mock_db:
        with patch.object(audit_logger_no_db, "_log_to_file_backup") as mock_file:
            audit_logger_no_db.log(
                event_type="test_event",
                user_id=123,
                username="testuser",
                ip_address="192.168.1.1",
                action="test_action",
                resource="test_resource",
                details={"key": "value"},
                success=True,
                severity="warning",
                session_id="session123",
                request_id="req123",
                user_agent="TestAgent/1.0",
            )

            mock_db.assert_called_once()
            mock_file.assert_called_once()

            audit_entry = mock_db.call_args[0][0]
            assert audit_entry["event_type"] == "test_event"
            assert audit_entry["user_id"] == 123
            assert audit_entry["severity"] == "warning"


def test_log_severity_levels(audit_logger_no_db):
    """Test all severity levels."""
    for severity in ["info", "warning", "error", "critical"]:
        with patch.object(audit_logger_no_db, "_log_to_db"):
            with patch.object(audit_logger_no_db, "_log_to_file_backup"):
                audit_logger_no_db.log(event_type="test", severity=severity)


def test_log_unknown_severity(audit_logger_no_db):
    """Test unknown severity (defaults to info)."""
    with patch.object(audit_logger_no_db, "_log_to_db"):
        with patch.object(audit_logger_no_db, "_log_to_file_backup"):
            audit_logger_no_db.log(event_type="test", severity="unknown_severity")


# ==============================================================================
# TEST: Authentication Events
# ==============================================================================


def test_log_auth_attempt_success(audit_logger_no_db):
    """Test successful authentication log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_auth_attempt(
            username="testuser",
            ip_address="192.168.1.1",
            success=True,
            method="password",
            details={"extra": "info"},
        )

        mock_log.assert_called_once()
        kwargs = mock_log.call_args[1]
        assert kwargs["username"] == "testuser"
        assert kwargs["success"] is True
        assert kwargs["severity"] == "info"


def test_log_auth_attempt_failure(audit_logger_no_db):
    """Test failed authentication log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_auth_attempt(
            username="testuser", ip_address="192.168.1.1", success=False
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["success"] is False
        assert kwargs["severity"] == "warning"


def test_log_logout(audit_logger_no_db):
    """Test logout log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_logout(username="testuser", session_id="session123")

        kwargs = mock_log.call_args[1]
        assert kwargs["username"] == "testuser"
        assert kwargs["action"] == "logout"
        assert kwargs["session_id"] == "session123"


# ==============================================================================
# TEST: Data Access Events
# ==============================================================================


def test_log_data_access_sensitive(audit_logger_no_db):
    """Test sensitive data access log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_data_access(
            user_id=123,
            resource="api_keys",
            action="read",
            sensitive=True,
            details={"record_id": 456},
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["severity"] == "warning"
        assert kwargs["details"]["sensitive"] is True


def test_log_data_access_non_sensitive(audit_logger_no_db):
    """Test non-sensitive data access log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_data_access(
            user_id=123, resource="public_data", action="read", sensitive=False
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["severity"] == "info"


# ==============================================================================
# TEST: Configuration Events
# ==============================================================================


def test_log_config_change(audit_logger_no_db):
    """Test configuration change log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_config_change(
            user_id=123,
            config_key="max_retries",
            old_value=3,
            new_value=5,
            details={"reason": "performance"},
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["action"] == "update"
        assert kwargs["details"]["old_value"] == "3"
        assert kwargs["details"]["new_value"] == "5"
        assert kwargs["severity"] == "warning"


# ==============================================================================
# TEST: Tool Execution Events
# ==============================================================================


def test_log_tool_execution(audit_logger_no_db):
    """Test tool execution log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_tool_execution(
            user_id=123,
            tool_name="nmap",
            target="192.168.1.0/24",
            success=True,
            details={"duration": 120},
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["action"] == "execute"
        assert kwargs["resource"] == "nmap"
        assert kwargs["details"]["target"] == "192.168.1.0/24"
        assert kwargs["severity"] == "warning"


# ==============================================================================
# TEST: Security Events
# ==============================================================================


def test_log_security_event(audit_logger_no_db):
    """Test security event log."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_security_event(
            event_type="suspicious_activity",
            severity="high",
            details={"attempts": 10, "source_ip": "1.2.3.4"},
            user_id=123,
            ip_address="1.2.3.4",
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["action"] == "suspicious_activity"
        assert kwargs["severity"] == "high"
        assert kwargs["details"]["attempts"] == 10


# ==============================================================================
# TEST: API Events
# ==============================================================================


def test_log_api_call_success(audit_logger_no_db):
    """Test API call log (success)."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_api_call(
            user_id=123,
            endpoint="/api/v1/users",
            method="GET",
            status_code=200,
            ip_address="192.168.1.1",
            request_id="req123",
            duration_ms=42.5,
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["success"] is True
        assert kwargs["details"]["status_code"] == 200


def test_log_api_call_failure(audit_logger_no_db):
    """Test API call log (failure)."""
    with patch.object(audit_logger_no_db, "log") as mock_log:
        audit_logger_no_db.log_api_call(
            user_id=123, endpoint="/api/v1/users", method="POST", status_code=500
        )

        kwargs = mock_log.call_args[1]
        assert kwargs["success"] is False


# ==============================================================================
# TEST: Close
# ==============================================================================


def test_close_with_connection(audit_logger_with_db):
    """Test close with active connection."""
    logger, mock_conn, _ = audit_logger_with_db
    logger.close()
    mock_conn.close.assert_called_once()


def test_close_without_connection(audit_logger_no_db):
    """Test close without connection."""
    # Should not raise
    audit_logger_no_db.close()


# ==============================================================================
# TEST: Context Manager
# ==============================================================================


def test_audit_context():
    """Test audit_context context manager."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with audit_context() as logger:
            assert isinstance(logger, AuditLogger)


def test_audit_context_closes_on_exit():
    """Test audit_context closes logger on exit."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        with patch.object(AuditLogger, "close") as mock_close:
            with audit_context() as logger:
                pass
            mock_close.assert_called_once()


# ==============================================================================
# TEST: Global Instance
# ==============================================================================


def test_get_audit_logger_singleton():
    """Test get_audit_logger returns singleton."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        # Reset global
        import backend.shared.audit_logger as module

        module._global_audit_logger = None

        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2
        logger1.close()


def test_get_audit_logger_creates_instance():
    """Test get_audit_logger creates instance on first call."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        # Reset global
        import backend.shared.audit_logger as module

        module._global_audit_logger = None

        logger = get_audit_logger()
        assert logger is not None
        assert isinstance(logger, AuditLogger)
        logger.close()


# ==============================================================================
# TEST: __all__
# ==============================================================================


def test_module_exports():
    """Test module __all__ exports."""
    from backend.shared import audit_logger

    assert "AuditLogger" in audit_logger.__all__
    assert "AuditConfig" in audit_logger.__all__
    assert "audit_context" in audit_logger.__all__
    assert "get_audit_logger" in audit_logger.__all__


# ==============================================================================
# TEST: Edge Cases - Import Error & Early Return
# ==============================================================================


def test_import_error_path():
    """Test psycopg2 ImportError path (lines 86-89)."""
    import importlib
    import sys

    # Temporarily remove psycopg2 from sys.modules
    original_psycopg2 = sys.modules.get("psycopg2")
    original_extras = sys.modules.get("psycopg2.extras")

    if "psycopg2" in sys.modules:
        del sys.modules["psycopg2"]
    if "psycopg2.extras" in sys.modules:
        del sys.modules["psycopg2.extras"]

    # Block import
    sys.modules["psycopg2"] = None

    try:
        # Force reimport to trigger except block
        import backend.shared.audit_logger as test_module

        importlib.reload(test_module)

        # Verify POSTGRES_AVAILABLE is False
        assert test_module.POSTGRES_AVAILABLE is False
        assert test_module.psycopg2 is None
        assert test_module.Json is None
    finally:
        # Restore
        if original_psycopg2 is not None:
            sys.modules["psycopg2"] = original_psycopg2
        elif "psycopg2" in sys.modules:
            del sys.modules["psycopg2"]

        if original_extras is not None:
            sys.modules["psycopg2.extras"] = original_extras
        elif "psycopg2.extras" in sys.modules:
            del sys.modules["psycopg2.extras"]

        # Reload to restore normal state
        importlib.reload(test_module)


def test_connect_db_early_return():
    """Test _connect_db early return when POSTGRES_AVAILABLE=False (line 172)."""
    with patch("backend.shared.audit_logger.POSTGRES_AVAILABLE", False):
        logger = AuditLogger(log_to_file=False)

        # Call _connect_db directly - should return early
        result = logger._connect_db()
        assert result is None
        assert logger.db_connection is None
        logger.close()
