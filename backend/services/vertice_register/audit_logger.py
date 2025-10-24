"""
Audit Logger - TITANIUM Edition

Logs all registry operations for security auditing and compliance.

Log Format: Structured JSON
Fields: timestamp, who, what, where, result, details
Retention: 90 days (configurable for compliance)

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("audit")

# Configure audit logger with JSON formatter if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))  # Raw JSON
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class AuditLogger:
    """Audit logger for registry operations."""

    @staticmethod
    def log_operation(
        operation: str,
        who: str,
        where: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log an audit event.

        Args:
            operation: Operation performed (register, deregister, heartbeat, lookup)
            who: Who performed the operation (service_name or IP)
            where: Where (replica ID or hostname)
            result: Result (success, failure, rate_limited, validation_error)
            details: Additional details (optional)
        """
        audit_entry = {
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "operation": operation,
            "who": who,
            "where": where,
            "result": result,
            "details": details or {}
        }

        # Log as JSON
        logger.info(json.dumps(audit_entry))

    @staticmethod
    def log_register(
        service_name: str,
        endpoint: str,
        client_ip: str,
        result: str,
        error: Optional[str] = None
    ):
        """Log service registration."""
        AuditLogger.log_operation(
            operation="register",
            who=f"{service_name} ({client_ip})",
            where="registry",
            result=result,
            details={
                "service_name": service_name,
                "endpoint": endpoint,
                "client_ip": client_ip,
                "error": error
            }
        )

    @staticmethod
    def log_deregister(
        service_name: str,
        client_ip: str,
        result: str,
        error: Optional[str] = None
    ):
        """Log service deregistration."""
        AuditLogger.log_operation(
            operation="deregister",
            who=f"{service_name} ({client_ip})",
            where="registry",
            result=result,
            details={
                "service_name": service_name,
                "client_ip": client_ip,
                "error": error
            }
        )

    @staticmethod
    def log_heartbeat(
        service_name: str,
        client_ip: str,
        result: str,
        error: Optional[str] = None
    ):
        """Log service heartbeat."""
        AuditLogger.log_operation(
            operation="heartbeat",
            who=f"{service_name} ({client_ip})",
            where="registry",
            result=result,
            details={
                "service_name": service_name,
                "client_ip": client_ip,
                "error": error
            }
        )

    @staticmethod
    def log_lookup(
        service_name: str,
        client_ip: str,
        result: str,
        found: bool = False
    ):
        """Log service lookup."""
        AuditLogger.log_operation(
            operation="lookup",
            who=client_ip,
            where="registry",
            result=result,
            details={
                "service_name": service_name,
                "client_ip": client_ip,
                "found": found
            }
        )

    @staticmethod
    def log_rate_limit(
        operation: str,
        identifier: str,
        limit: float
    ):
        """Log rate limit violation."""
        AuditLogger.log_operation(
            operation=operation,
            who=identifier,
            where="registry",
            result="rate_limited",
            details={
                "identifier": identifier,
                "limit_per_second": limit
            }
        )

    @staticmethod
    def log_validation_error(
        operation: str,
        field: str,
        error: str,
        provided: str,
        client_ip: str
    ):
        """Log validation error."""
        AuditLogger.log_operation(
            operation=operation,
            who=client_ip,
            where="registry",
            result="validation_error",
            details={
                "field": field,
                "error": error,
                "provided": provided,
                "client_ip": client_ip
            }
        )
