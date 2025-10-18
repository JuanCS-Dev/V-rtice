"""Maximus OSINT Service - Structured JSON Logger.

This module implements structured JSON logging for OSINT tools, replacing
print() statements with proper logging infrastructure.

Structured logging enables:
- Log aggregation (ELK, Loki, CloudWatch)
- Filtering and querying (by tool, level, event type)
- Correlation (via request_id)
- Debugging (full context in each log)

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, no print() statements
    - Article V (Prior Legislation): Observability before deployment

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional


class StructuredLogger:
    """Structured JSON logger for OSINT tools.

    Outputs logs as JSON objects with standardized fields:
    - timestamp: ISO 8601 UTC timestamp
    - tool: Tool name (e.g., "ShodanTool")
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - event: Event type (e.g., "request_started", "cache_hit")
    - **kwargs: Additional context fields

    Usage Example:
        logger = StructuredLogger(tool_name="ShodanTool")

        logger.info("request_started", url="https://api.shodan.io/shodan/host/8.8.8.8")
        # Output: {"timestamp": "2025-10-14T12:00:00Z", "tool": "ShodanTool",
        #          "level": "INFO", "event": "request_started",
        #          "url": "https://api.shodan.io/shodan/host/8.8.8.8"}

        logger.error("request_failed", url="...", error="Timeout", status=504)
    """

    def __init__(
        self,
        tool_name: str,
        log_level: str = "INFO",
        output_stream=sys.stdout,
    ):
        """Initialize StructuredLogger.

        Args:
            tool_name: Name of the OSINT tool
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_stream: Output stream (default: stdout)
        """
        self.tool_name = tool_name
        self.logger = logging.getLogger(f"osint.{tool_name}")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Remove existing handlers
        self.logger.handlers = []

        # Add JSON formatter handler
        handler = logging.StreamHandler(output_stream)
        handler.setFormatter(self._JSONFormatter())
        self.logger.addHandler(handler)

        # Prevent propagation to root logger (avoid duplicate logs)
        self.logger.propagate = False

    def _log(
        self,
        level: str,
        event: str,
        request_id: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Internal log method with JSON serialization.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            event: Event type/name
            request_id: Optional request correlation ID
            **kwargs: Additional context fields
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": self.tool_name,
            "level": level.upper(),
            "event": event,
        }

        if request_id:
            log_entry["request_id"] = request_id

        # Add all additional context
        log_entry.update(kwargs)

        # Log as structured data
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, "", extra={"structured": log_entry})

    def debug(self, event: str, **kwargs) -> None:
        """Log DEBUG level event.

        Args:
            event: Event name
            **kwargs: Context fields
        """
        self._log("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs) -> None:
        """Log INFO level event.

        Args:
            event: Event name
            **kwargs: Context fields
        """
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs) -> None:
        """Log WARNING level event.

        Args:
            event: Event name
            **kwargs: Context fields
        """
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs) -> None:
        """Log ERROR level event.

        Args:
            event: Event name
            **kwargs: Context fields
        """
        self._log("ERROR", event, **kwargs)

    def critical(self, event: str, **kwargs) -> None:
        """Log CRITICAL level event.

        Args:
            event: Event name
            **kwargs: Context fields
        """
        self._log("CRITICAL", event, **kwargs)

    class _JSONFormatter(logging.Formatter):
        """Custom JSON formatter for structured logs."""

        def format(self, record: logging.LogRecord) -> str:
            """Format log record as JSON string.

            Args:
                record: Log record to format

            Returns:
                JSON-formatted log string
            """
            if hasattr(record, "structured"):
                return json.dumps(record.structured, default=str)
            else:
                # Fallback for non-structured logs
                return json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                }, default=str)


# Global logger for service-level logs
service_logger = StructuredLogger(tool_name="OSINTService", log_level="INFO")
