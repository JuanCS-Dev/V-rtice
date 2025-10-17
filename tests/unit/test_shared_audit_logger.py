"""Tests for backend/shared/audit_logger.py - 100% ABSOLUTE coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from contextlib import contextmanager


class TestAuditConfig:
    """Test AuditConfig class."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        from backend.shared.audit_logger import AuditConfig
        
        assert AuditConfig.DB_HOST == "localhost"
        assert AuditConfig.DB_PORT == 5432
        assert AuditConfig.DB_NAME == "vertice_audit"
        assert AuditConfig.TABLE_NAME == "audit_logs"
        assert AuditConfig.RETENTION_DAYS == 365
        assert AuditConfig.LOG_TO_FILE is True
        assert isinstance(AuditConfig.LOG_FILE, str)
        assert AuditConfig.FAIL_OPEN is True


class TestAuditLoggerInit:
    """Test AuditLogger initialization - covers lines 136-163."""
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_init_without_postgres(self, mock_logging):
        """Test initialization when PostgreSQL not available."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        assert logger.db_connection is None
        assert logger.log_to_file is False
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging')
    def test_init_with_postgres_success(self, mock_logging, mock_psycopg2):
        """Test successful PostgreSQL connection - covers lines 157-163."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        assert logger.db_connection == mock_conn
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    def test_init_postgres_connection_failure(self, mock_log_error, mock_psycopg2):
        """Test PostgreSQL connection failure - covers lines 160-163."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_psycopg2.connect.side_effect = Exception("Connection failed")
        
        logger = AuditLogger(log_to_file=False)
        
        assert logger.db_connection is None
        assert mock_log_error.called
    
    @patch('backend.shared.audit_logger.logging.getLogger')
    @patch('backend.shared.audit_logger.logging.FileHandler')
    def test_init_file_logging_setup(self, mock_file_handler, mock_get_logger):
        """Test file logger setup - covers lines 146-154."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_logger = Mock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        
        logger = AuditLogger(log_to_file=True)
        
        assert mock_file_handler.called
        assert logger.file_logger == mock_logger
    
    @patch('backend.shared.audit_logger.logging.getLogger')
    def test_init_file_logger_already_has_handlers(self, mock_get_logger):
        """Test file logger with existing handlers - line 148 false branch."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_logger = Mock()
        mock_logger.handlers = [Mock()]  # Already has handlers
        mock_get_logger.return_value = mock_logger
        
        logger = AuditLogger(log_to_file=True)
        
        # Should not add new handlers
        assert logger.file_logger == mock_logger


class TestAuditLoggerHelperMethods:
    """Test helper methods."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_get_default_config(self, mock_logging):
        """Test _get_default_config - covers lines 165-173."""
        from backend.shared.audit_logger import AuditLogger, AuditConfig
        
        logger = AuditLogger(log_to_file=False)
        config = logger._get_default_config()
        
        assert isinstance(config, dict)
        assert config["host"] == AuditConfig.DB_HOST
        assert config["port"] == AuditConfig.DB_PORT
        assert config["dbname"] == AuditConfig.DB_NAME
        assert config["user"] == AuditConfig.DB_USER
        assert config["password"] == AuditConfig.DB_PASSWORD
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging')
    def test_connect_db_success(self, mock_logging, mock_psycopg2):
        """Test _connect_db success - covers lines 180-185."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        assert logger.db_connection == mock_conn
        assert logger.db_connection.autocommit is True
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    def test_connect_db_failure_fail_open_true(self, mock_log_error, mock_psycopg2):
        """Test _connect_db failure with FAIL_OPEN=True - covers lines 186-187."""
        from backend.shared.audit_logger import AuditLogger, AuditConfig
        
        mock_psycopg2.connect.side_effect = Exception("DB error")
        
        # FAIL_OPEN is True by default, should not raise
        logger = AuditLogger(log_to_file=False)
        
        assert logger.db_connection is None


class TestLogToDatabase:
    """Test _log_to_db method - covers lines 189-231."""
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_log_to_db_postgres_not_available(self, mock_logging):
        """Test _log_to_db when PostgreSQL not available - line 191."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        result = logger._log_to_db({"test": "data"})
        
        assert result is False
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging')
    @patch('backend.shared.audit_logger.Json')
    def test_log_to_db_success(self, mock_json, mock_logging, mock_psycopg2):
        """Test successful database insert - covers lines 194-225."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        audit_entry = {
            "timestamp": "2025-10-17",
            "event_type": "test",
            "user_id": 123,
            "details": {"key": "value"}
        }
        
        result = logger._log_to_db(audit_entry)
        
        assert result is True
        assert mock_cursor.execute.called
        assert mock_cursor.close.called
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    def test_log_to_db_error_fail_open(self, mock_log_error, mock_psycopg2):
        """Test database error with FAIL_OPEN - covers lines 227-231."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("DB error")
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        result = logger._log_to_db({"test": "data"})
        
        assert result is False
        assert mock_log_error.called


class TestLogToFile:
    """Test _log_to_file_backup method - covers lines 233-239."""
    
    @patch('backend.shared.audit_logger.logging.getLogger')
    def test_log_to_file_backup_success(self, mock_get_logger):
        """Test successful file logging - covers lines 235-237."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_logger = Mock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger
        
        with patch('backend.shared.audit_logger.logging.FileHandler'):
            logger = AuditLogger(log_to_file=True)
            
            audit_entry = {"test": "data"}
            logger._log_to_file_backup(audit_entry)
            
            assert mock_logger.info.called
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_to_file_backup_disabled(self, mock_logging):
        """Test file logging when disabled - line 235 false."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        # Should not crash
        logger._log_to_file_backup({"test": "data"})
    
    @patch('backend.shared.audit_logger.logging.getLogger')
    @patch('backend.shared.audit_logger.logging.error')
    def test_log_to_file_backup_error(self, mock_log_error, mock_get_logger):
        """Test file logging error - covers lines 238-239."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_logger = Mock()
        mock_logger.handlers = []
        mock_logger.info.side_effect = Exception("File error")
        mock_get_logger.return_value = mock_logger
        
        with patch('backend.shared.audit_logger.logging.FileHandler'):
            logger = AuditLogger(log_to_file=True)
            
            logger._log_to_file_backup({"test": "data"})
            
            assert mock_log_error.called


class TestLogMethod:
    """Test main log() method - covers lines 241-310."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_basic(self, mock_logging):
        """Test basic log method."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log(
            event_type="test_event",
            severity="info"
        )


class TestLogAuthAttempt:
    """Test log_auth_attempt method - covers lines 312-330."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_auth_attempt_success(self, mock_logging):
        """Test logging successful authentication."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_auth_attempt(
            username="testuser",
            ip_address="192.168.1.1",
            success=True
        )
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_auth_attempt_failure(self, mock_logging):
        """Test logging failed authentication."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_auth_attempt(
            username="hacker",
            ip_address="1.2.3.4",
            success=False)


class TestLogLogout:
    """Test log_logout method - covers lines 332-346."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_logout(self, mock_logging):
        """Test logging logout event."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_logout(
            username="testuser",
            session_id="abc123"
        )


class TestLogDataAccess:
    """Test log_data_access method - covers lines 348-369."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_data_access(self, mock_logging):
        """Test logging data access."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_data_access(
            user_id=123,
            resource="api_keys",
            action="read",
            sensitive=True
        )


class TestLogConfigChange:
    """Test log_config_change method - covers lines 371-396."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_config_change(self, mock_logging):
        """Test logging configuration change."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_config_change(
            user_id=1,
            config_key="security.mfa_enabled",
            old_value=False,
            new_value=True
        )


class TestLogToolExecution:
    """Test log_tool_execution method - covers lines 398-419."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_tool_execution(self, mock_logging):
        """Test logging offensive tool execution."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_tool_execution(
            user_id=1,
            tool_name="nmap",
            target="192.168.1.0/24",
            success=True)


class TestLogSecurityEvent:
    """Test log_security_event method - covers lines 421-443."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_security_event(self, mock_logging):
        """Test logging security event."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_security_event(
            event_type="suspicious_activity",
            severity="high",
            details={"attempts": 10}
        )


class TestLogAPICall:
    """Test log_api_call method - covers lines 445-466."""
    
    @patch('backend.shared.audit_logger.logging')
    def test_log_api_call(self, mock_logging):
        """Test logging API call."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        logger.log_api_call(
            user_id=1,
            endpoint="/api/v1/scan",
            method="POST",
            status_code=200
        )


class TestClose:
    """Test close method - covers lines 468-473."""
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging')
    def test_close_with_connection(self, mock_logging, mock_psycopg2):
        """Test closing database connection."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_conn = Mock()
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        logger.close()
        
        assert mock_conn.close.called
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_close_without_connection(self, mock_logging):
        """Test close when no connection - line 469 false branch."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        # Should not crash
        logger.close()


class TestAuditContext:
    """Test audit_context context manager - covers lines 478-485."""
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_audit_context(self, mock_logging):
        """Test audit context manager."""
        from backend.shared.audit_logger import audit_context
        
        with audit_context() as audit:
            assert audit is not None
            # Can use logger
            audit.log_security_event(
                event_type="test",
                severity="low",
                details={}
            )


class TestGetAuditLogger:
    """Test get_audit_logger singleton - covers lines 495-500."""
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_get_audit_logger_singleton(self, mock_logging):
        """Test get_audit_logger returns singleton."""
        from backend.shared.audit_logger import get_audit_logger
        
        # Reset global
        import backend.shared.audit_logger as module
        module._global_audit_logger = None
        
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        
        assert logger1 is logger2


class TestEdgeCasesForFullCoverage:
    """Edge cases to reach 100% ABSOLUTE coverage."""
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    def test_init_exception_fail_open_false_REAL(self, mock_log_error, mock_psycopg2):
        """Test __init__ exception with FAIL_OPEN=False - covers line 162->exit branch."""
        from backend.shared.audit_logger import AuditLogger, AuditConfig
        
        # Save original
        original_fail_open = AuditConfig.FAIL_OPEN
        
        try:
            # Set FAIL_OPEN to False BEFORE creating logger
            AuditConfig.FAIL_OPEN = False
            
            mock_psycopg2.connect.side_effect = Exception("Connection failed")
            
            # This MUST raise (line 163)
            with pytest.raises(Exception, match="Connection failed"):
                logger = AuditLogger(log_to_file=False)
        finally:
            # Restore
            AuditConfig.FAIL_OPEN = original_fail_open

    
    def test_import_error_handling(self):
        """Test ImportError handling - covers lines 86-89."""
        # Lines 86-89 are covered when psycopg2 is not available
        # This is tested by the POSTGRES_AVAILABLE=False tests above
        from backend.shared.audit_logger import POSTGRES_AVAILABLE
        # If psycopg2 is not installed, POSTGRES_AVAILABLE would be False
        assert isinstance(POSTGRES_AVAILABLE, bool)
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    @patch('backend.shared.audit_logger.AuditConfig')
    def test_init_exception_fail_open_false(self, mock_config, mock_log_error, mock_psycopg2):
        """Test __init__ exception with FAIL_OPEN=False - covers lines 160-163."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_config.FAIL_OPEN = False
        mock_config.LOG_FILE = "/tmp/test.log"
        mock_psycopg2.connect.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            logger = AuditLogger(log_to_file=False)
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', False)
    @patch('backend.shared.audit_logger.logging')
    def test_connect_db_postgres_not_available(self, mock_logging):
        """Test _connect_db when POSTGRES not available - covers line 178."""
        from backend.shared.audit_logger import AuditLogger
        
        logger = AuditLogger(log_to_file=False)
        
        # Should return early (line 178)
        logger._connect_db()
        
        assert logger.db_connection is None
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    @patch('backend.shared.audit_logger.AuditConfig')
    def test_connect_db_fail_open_false(self, mock_config, mock_log_error, mock_psycopg2):
        """Test _connect_db failure with FAIL_OPEN=False - covers line 187."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_config.FAIL_OPEN = False
        mock_config.LOG_FILE = "/tmp/test.log"
        mock_psycopg2.connect.side_effect = Exception("DB error")
        
        # Should raise because FAIL_OPEN=False
        with pytest.raises(Exception, match="DB error"):
            logger = AuditLogger(log_to_file=False)
    
    @patch('backend.shared.audit_logger.POSTGRES_AVAILABLE', True)
    @patch('backend.shared.audit_logger.psycopg2')
    @patch('backend.shared.audit_logger.logging.error')
    @patch('backend.shared.audit_logger.AuditConfig')
    def test_log_to_db_fail_open_false(self, mock_config, mock_log_error, mock_psycopg2):
        """Test _log_to_db failure with FAIL_OPEN=False - covers line 230."""
        from backend.shared.audit_logger import AuditLogger
        
        mock_config.FAIL_OPEN = True  # Allow init
        mock_config.LOG_FILE = "/tmp/test.log"
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg2.connect.return_value = mock_conn
        
        logger = AuditLogger(log_to_file=False)
        
        # Now set FAIL_OPEN=False for the _log_to_db call
        mock_config.FAIL_OPEN = False
        mock_cursor.execute.side_effect = Exception("DB write error")
        
        with pytest.raises(Exception, match="DB write error"):
            logger._log_to_db({"test": "data"})


def test_psycopg2_not_installed():
    """Test when psycopg2 is not installed - covers lines 86-89."""
    import sys
    from unittest.mock import patch
    import builtins
    
    # Remove from cache
    modules_to_remove = [k for k in sys.modules.keys() if 'audit_logger' in k]
    for mod in modules_to_remove:
        del sys.modules[mod]
    
    real_import = builtins.__import__
    
    def mock_import(name, *args, **kwargs):
        if 'psycopg2' in name:
            raise ImportError("No module named 'psycopg2'")
        return real_import(name, *args, **kwargs)
    
    with patch('builtins.__import__', side_effect=mock_import):
        # Force reimport with psycopg2 unavailable
        import importlib
        import backend.shared.audit_logger as audit_module
        importlib.reload(audit_module)
        
        # Lines 86-89 executed
        assert audit_module.POSTGRES_AVAILABLE is False


class TestBranchCoverage100:
    """Final test to hit 100.00% with branch coverage - line 162->exit."""
    
    def test_init_fail_open_false_raises_REAL(self):
        """Test __init__ raises when FAIL_OPEN=False - covers branch 162->exit."""
        import backend.shared.audit_logger as audit_module
        from unittest.mock import Mock
        
        # Save originals
        original_fail_open = audit_module.AuditConfig.FAIL_OPEN
        original_postgres_avail = audit_module.POSTGRES_AVAILABLE
        original_psycopg2 = audit_module.psycopg2
        
        try:
            # Setup: make postgres available but connection fails
            audit_module.POSTGRES_AVAILABLE = True
            
            # Mock psycopg2 to fail
            mock_psycopg2 = Mock()
            mock_psycopg2.connect.side_effect = RuntimeError("Connection error")
            audit_module.psycopg2 = mock_psycopg2
            
            # CRITICAL: Set FAIL_OPEN=False to force raise
            audit_module.AuditConfig.FAIL_OPEN = False
            
            # Now create logger - must raise (line 163)
            with pytest.raises(RuntimeError, match="Connection error"):
                audit_module.AuditLogger(log_to_file=False)
                
        finally:
            # Restore everything
            audit_module.AuditConfig.FAIL_OPEN = original_fail_open
            audit_module.POSTGRES_AVAILABLE = original_postgres_avail
            audit_module.psycopg2 = original_psycopg2
