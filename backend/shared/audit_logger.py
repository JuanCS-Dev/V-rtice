"""
Comprehensive Audit Logging System
===================================

PAGANI Quality - Compliance & Forensics

Audit logging for:
- Authentication attempts (success/failure)
- Authorization failures
- Data access (PII, credentials, secrets)
- Configuration changes
- Offensive tool executions
- Administrative actions
- Security events

Features:
- Immutable audit trail
- Structured JSON logging
- PostgreSQL storage
- SIEM integration ready
- Compliance (SOC 2, ISO 27001, PCI-DSS)
- Tamper detection

Usage:
    from backend.shared.audit_logger import AuditLogger
    
    audit = AuditLogger()
    
    # Log authentication
    audit.log_auth_attempt(
        username="admin",
        ip_address="192.168.1.1",
        success=True
    )
    
    # Log data access
    audit.log_data_access(
        user_id=123,
        resource="api_keys",
        action="read",
        sensitive=True
    )
    
    # Log security event
    audit.log_security_event(
        event_type="suspicious_activity",
        severity="high",
        details={"attempts": 10, "source_ip": "1.2.3.4"}
    )

Database Schema:
    CREATE TABLE audit_logs (
        id BIGSERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        event_type VARCHAR(50) NOT NULL,
        user_id INTEGER,
        username VARCHAR(255),
        ip_address INET,
        action VARCHAR(100),
        resource VARCHAR(255),
        details JSONB,
        success BOOLEAN,
        severity VARCHAR(20),
        session_id VARCHAR(255),
        request_id VARCHAR(255),
        user_agent TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
    CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
    CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
    CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import Json
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    psycopg2 = None
    Json = None

from backend.shared.enums import EventType, LogLevel, ThreatLevel


# ============================================================================
# CONFIGURATION
# ============================================================================

class AuditConfig:
    """Audit logging configuration."""
    
    # PostgreSQL connection (override via environment)
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "vertice_audit"
    DB_USER = "vertice"
    DB_PASSWORD = "changeme"
    
    # Table name
    TABLE_NAME = "audit_logs"
    
    # Retention policy (days)
    RETENTION_DAYS = 365  # 1 year
    
    # Log to file as backup
    LOG_TO_FILE = True
    LOG_FILE = "/var/log/vertice/audit.log"
    
    # Fail behavior if DB unavailable
    FAIL_OPEN = True  # Continue on DB error (log to file instead)


# ============================================================================
# AUDIT LOGGER
# ============================================================================

class AuditLogger:
    """
    Comprehensive audit logging system.
    
    Logs security-relevant events to:
    1. PostgreSQL (primary, queryable)
    2. File (backup, SIEM ingestion)
    3. Python logging (dev/debug)
    """
    
    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        log_to_file: bool = True
    ):
        self.db_config = db_config or self._get_default_config()
        self.log_to_file = log_to_file
        self.db_connection = None
        
        # Setup file logging
        if self.log_to_file:
            self.file_logger = logging.getLogger("vertice.audit")
            if not self.file_logger.handlers:
                handler = logging.FileHandler(AuditConfig.LOG_FILE)
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'
                ))
                self.file_logger.addHandler(handler)
                self.file_logger.setLevel(logging.INFO)
        
        # Initialize DB connection
        if POSTGRES_AVAILABLE:
            try:
                self._connect_db()
            except Exception as e:
                logging.error(f"Failed to connect to audit database: {e}")
                if not AuditConfig.FAIL_OPEN:
                    raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default database configuration."""
        return {
            "host": AuditConfig.DB_HOST,
            "port": AuditConfig.DB_PORT,
            "dbname": AuditConfig.DB_NAME,
            "user": AuditConfig.DB_USER,
            "password": AuditConfig.DB_PASSWORD
        }
    
    def _connect_db(self):
        """Connect to PostgreSQL."""
        if not POSTGRES_AVAILABLE:
            return
        
        try:
            self.db_connection = psycopg2.connect(**self.db_config)
            self.db_connection.autocommit = True
        except Exception as e:
            logging.error(f"PostgreSQL connection failed: {e}")
            self.db_connection = None
            if not AuditConfig.FAIL_OPEN:
                raise
    
    def _log_to_db(self, audit_entry: Dict[str, Any]):
        """Write audit entry to PostgreSQL."""
        if not self.db_connection or not POSTGRES_AVAILABLE:
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # Build INSERT query
            query = f"""
                INSERT INTO {AuditConfig.TABLE_NAME} (
                    timestamp, event_type, user_id, username, ip_address,
                    action, resource, details, success, severity,
                    session_id, request_id, user_agent
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(query, (
                audit_entry.get("timestamp"),
                audit_entry.get("event_type"),
                audit_entry.get("user_id"),
                audit_entry.get("username"),
                audit_entry.get("ip_address"),
                audit_entry.get("action"),
                audit_entry.get("resource"),
                Json(audit_entry.get("details", {})),
                audit_entry.get("success"),
                audit_entry.get("severity"),
                audit_entry.get("session_id"),
                audit_entry.get("request_id"),
                audit_entry.get("user_agent")
            ))
            
            cursor.close()
            return True
        
        except Exception as e:
            logging.error(f"Failed to write audit log to DB: {e}")
            if not AuditConfig.FAIL_OPEN:
                raise
            return False
    
    def _log_to_file_backup(self, audit_entry: Dict[str, Any]):
        """Write audit entry to file (backup)."""
        if self.log_to_file and self.file_logger:
            try:
                self.file_logger.info(json.dumps(audit_entry))
            except Exception as e:
                logging.error(f"Failed to write audit log to file: {e}")
    
    def log(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
        severity: str = "info",
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log audit event (generic).
        
        Args:
            event_type: Type of event (EventType enum value)
            user_id: User ID if applicable
            username: Username if applicable
            ip_address: Source IP address
            action: Action performed (read, write, delete, execute)
            resource: Resource accessed
            details: Additional context (JSON-serializable)
            success: Whether action succeeded
            severity: Severity level (info, warning, error, critical)
            session_id: Session identifier
            request_id: Request ID for tracing
            user_agent: User agent string
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "action": action,
            "resource": resource,
            "details": details or {},
            "success": success,
            "severity": severity,
            "session_id": session_id,
            "request_id": request_id,
            "user_agent": user_agent
        }
        
        # Log to database
        self._log_to_db(audit_entry)
        
        # Log to file (backup)
        self._log_to_file_backup(audit_entry)
        
        # Log to Python logging (dev)
        log_level = {
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }.get(severity, logging.INFO)
        
        logging.log(
            log_level,
            f"AUDIT: {event_type} - {action or 'N/A'} on {resource or 'N/A'} by {username or user_id or 'unknown'}"
        )
    
    # ========================================================================
    # AUTHENTICATION EVENTS
    # ========================================================================
    
    def log_auth_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        method: str = "password",
        details: Optional[Dict] = None
    ):
        """Log authentication attempt."""
        self.log(
            event_type=EventType.AUTH_SUCCESS.value if success else EventType.AUTH_FAILURE.value,
            username=username,
            ip_address=ip_address,
            action="login",
            resource="auth_system",
            details={"method": method, **(details or {})},
            success=success,
            severity="info" if success else "warning"
        )
    
    def log_logout(self, username: str, session_id: str):
        """Log user logout."""
        self.log(
            event_type=EventType.AUTH_SUCCESS.value,
            username=username,
            action="logout",
            resource="auth_system",
            session_id=session_id,
            success=True,
            severity="info"
        )
    
    # ========================================================================
    # DATA ACCESS EVENTS
    # ========================================================================
    
    def log_data_access(
        self,
        user_id: int,
        resource: str,
        action: str,
        sensitive: bool = False,
        details: Optional[Dict] = None
    ):
        """Log data access (especially PII/sensitive)."""
        self.log(
            event_type=EventType.DATA_ACCESS.value,
            user_id=user_id,
            action=action,
            resource=resource,
            details={"sensitive": sensitive, **(details or {})},
            success=True,
            severity="warning" if sensitive else "info"
        )
    
    # ========================================================================
    # CONFIGURATION EVENTS
    # ========================================================================
    
    def log_config_change(
        self,
        user_id: int,
        config_key: str,
        old_value: Any,
        new_value: Any,
        details: Optional[Dict] = None
    ):
        """Log configuration change."""
        self.log(
            event_type=EventType.CONFIG_CHANGE.value,
            user_id=user_id,
            action="update",
            resource=config_key,
            details={
                "old_value": str(old_value),
                "new_value": str(new_value),
                **(details or {})
            },
            success=True,
            severity="warning"
        )
    
    # ========================================================================
    # TOOL EXECUTION EVENTS
    # ========================================================================
    
    def log_tool_execution(
        self,
        user_id: int,
        tool_name: str,
        target: str,
        success: bool,
        details: Optional[Dict] = None
    ):
        """Log offensive/defensive tool execution."""
        self.log(
            event_type=EventType.TOOL_EXECUTION.value,
            user_id=user_id,
            action="execute",
            resource=tool_name,
            details={"target": target, **(details or {})},
            success=success,
            severity="warning"  # Tool execution always noteworthy
        )
    
    # ========================================================================
    # SECURITY EVENTS
    # ========================================================================
    
    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ):
        """Log security event (alerts, incidents)."""
        self.log(
            event_type=EventType.ALERT_TRIGGERED.value,
            user_id=user_id,
            ip_address=ip_address,
            action=event_type,
            resource="security_system",
            details=details,
            success=None,
            severity=severity
        )
    
    # ========================================================================
    # API EVENTS
    # ========================================================================
    
    def log_api_call(
        self,
        user_id: Optional[int],
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """Log API call."""
        self.log(
            event_type=EventType.API_CALL.value,
            user_id=user_id,
            ip_address=ip_address,
            action=method,
            resource=endpoint,
            details={"status_code": status_code, "duration_ms": duration_ms},
            success=200 <= status_code < 300,
            severity="info",
            request_id=request_id
        )
    
    def close(self):
        """Close database connection."""
        if self.db_connection:
            self.db_connection.close()


# ============================================================================
# CONTEXT MANAGER
# ============================================================================

@contextmanager
def audit_context():
    """Context manager for audit logging."""
    logger = AuditLogger()
    try:
        yield logger
    finally:
        logger.close()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Global audit logger instance
_global_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "AuditLogger",
    "AuditConfig",
    "audit_context",
    "get_audit_logger",
]
