"""
Structured Logger - JSON-formatted logging for observability
=============================================================

Provides structured logging with consistent format across all MAXIMUS components.

Features:
- JSON-formatted log entries
- Automatic timestamp and service identification
- Context enrichment (user_id, request_id, etc.)
- Compatible with log aggregation systems (ELK, Splunk, Loki)

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Article IV (Operational Excellence)
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any

logger = logging.getLogger(__name__)


class StructuredLogger:
    """
    Structured logging with JSON formatting.

    Wraps Python's standard logging with structured JSON output
    for better observability and log aggregation.

    Usage:
        logger = StructuredLogger("prefrontal_cortex")

        # Simple log
        logger.log("processing_signal", user_id="agent_001")

        # With context
        logger.log(
            "action_generated",
            user_id="agent_001",
            action="provide_guidance",
            confidence=0.85
        )

        # Error logging
        logger.error("tom_inference_failed", error=str(e), user_id="agent_001")
    """

    def __init__(self, service: str, level: int = logging.INFO):
        """Initialize Structured Logger.

        Args:
            service: Service name (e.g., "prefrontal_cortex", "tom_engine")
            level: Logging level (default: INFO)
        """
        self.service = service
        self.logger = logging.getLogger(service)
        self.logger.setLevel(level)

        # Ensure handler exists for output
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            self.logger.addHandler(handler)

    def log(self, event: str, **context: Any) -> None:
        """Log event with structured context.

        Args:
            event: Event name (e.g., "processing_signal", "action_approved")
            **context: Additional context fields
        """
        entry = self._build_entry(event, level="INFO", **context)
        self.logger.info(json.dumps(entry))

    def debug(self, event: str, **context: Any) -> None:
        """Log debug event."""
        entry = self._build_entry(event, level="DEBUG", **context)
        self.logger.debug(json.dumps(entry))

    def info(self, event: str, **context: Any) -> None:
        """Log info event."""
        entry = self._build_entry(event, level="INFO", **context)
        self.logger.info(json.dumps(entry))

    def warning(self, event: str, **context: Any) -> None:
        """Log warning event."""
        entry = self._build_entry(event, level="WARNING", **context)
        self.logger.warning(json.dumps(entry))

    def error(self, event: str, **context: Any) -> None:
        """Log error event."""
        entry = self._build_entry(event, level="ERROR", **context)
        self.logger.error(json.dumps(entry))

    def critical(self, event: str, **context: Any) -> None:
        """Log critical event."""
        entry = self._build_entry(event, level="CRITICAL", **context)
        self.logger.critical(json.dumps(entry))

    def _build_entry(self, event: str, level: str, **context: Any) -> Dict[str, Any]:
        """Build structured log entry.

        Args:
            event: Event name
            level: Log level string
            **context: Additional context fields

        Returns:
            Structured log entry dictionary
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service,
            "level": level,
            "event": event,
        }

        # Add context fields
        if context:
            entry.update(context)

        return entry

    def __repr__(self) -> str:
        return f"StructuredLogger(service={self.service})"
