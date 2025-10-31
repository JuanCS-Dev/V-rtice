"""Constitutional Structured Logging for Vértice Constitution v3.0.

Implements structured JSON logging with trace correlation and biblical
principle tracking for Loki aggregation.

Biblical Foundation:
- Aletheia (Truth): Honest, transparent logging
- Stewardship: Responsible log management
- Wisdom: Contextual information for decision tracking
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

import structlog
from opentelemetry import trace
from pythonjsonlogger import jsonlogger


class ConstitutionalLogProcessor:
    """Structlog processor that adds constitutional context."""

    def __call__(self, logger: Any, method_name: str, event_dict: Dict) -> Dict:
        """Add constitutional context to log entries."""
        # Add service metadata
        event_dict["service"] = os.getenv("SERVICE_NAME", "unknown")
        event_dict["version"] = os.getenv("SERVICE_VERSION", "1.0.0")
        event_dict["constitution_version"] = "3.0"

        # Add trace context if available
        current_span = trace.get_current_span()
        if current_span.is_recording():
            span_context = current_span.get_span_context()
            event_dict["trace_id"] = format(span_context.trace_id, "032x")
            event_dict["span_id"] = format(span_context.span_id, "016x")
            event_dict["trace_flags"] = span_context.trace_flags

        return event_dict


class BiblicalArticleProcessor:
    """Processor for biblical article compliance logging."""

    def __call__(self, logger: Any, method_name: str, event_dict: Dict) -> Dict:
        """Add biblical article context if present."""
        # Check for biblical article tags
        article_tags = {
            "sophia": "wisdom",
            "praotes": "gentleness",
            "tapeinophrosyne": "humility",
            "stewardship": "stewardship",
            "agape": "love",
            "sabbath": "rest",
            "aletheia": "truth",
        }

        for article, principle in article_tags.items():
            if article in event_dict:
                event_dict["biblical_article"] = article
                event_dict["biblical_principle"] = principle
                break

        return event_dict


def configure_constitutional_logging(
    service_name: str,
    log_level: str = "INFO",
    json_logs: bool = True,
) -> None:
    """
    Configure structured logging with constitutional compliance.

    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output JSON format (for Loki)
    """
    # Set service name for all logs
    os.environ.setdefault("SERVICE_NAME", service_name)

    if json_logs:
        # JSON formatter for Loki
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(service)s "
            "%(version)s %(constitution_version)s %(trace_id)s %(span_id)s",
            rename_fields={
                "levelname": "level",
                "asctime": "timestamp",
                "name": "logger",
            },
        )

        # Configure handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.handlers = [handler]
        root_logger.setLevel(getattr(logging, log_level.upper()))

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            ConstitutionalLogProcessor(),
            BiblicalArticleProcessor(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_constitutional_logger(name: str) -> structlog.BoundLogger:
    """
    Get a constitutional logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Convenience functions for biblical article logging
def log_sophia_decision(
    logger: structlog.BoundLogger,
    decision: str,
    confidence: float,
    **kwargs
) -> None:
    """Log a Sophia (Wisdom) decision."""
    logger.info(
        "wisdom_decision",
        sophia=True,
        decision=decision,
        confidence=confidence,
        **kwargs
    )


def log_praotes_check(
    logger: structlog.BoundLogger,
    operation: str,
    code_lines: int,
    reversibility: float,
    compliant: bool,
    **kwargs
) -> None:
    """Log a Praótes (Gentleness) check."""
    logger.info(
        "gentleness_check",
        praotes=True,
        operation=operation,
        code_lines=code_lines,
        reversibility_score=reversibility,
        compliant=compliant,
        **kwargs
    )


def log_tapeinophrosyne_check(
    logger: structlog.BoundLogger,
    operation: str,
    confidence: float,
    escalated: bool,
    **kwargs
) -> None:
    """Log a Tapeinophrosynē (Humility) check."""
    logger.info(
        "humility_check",
        tapeinophrosyne=True,
        operation=operation,
        confidence=confidence,
        escalated=escalated,
        compliant=confidence >= 0.85,
        **kwargs
    )


def log_sabbath_check(
    logger: structlog.BoundLogger,
    is_sabbath: bool,
    operation: str,
    is_p0: bool,
    allowed: bool,
    **kwargs
) -> None:
    """Log a Sabbath observance check."""
    level = "warning" if (is_sabbath and not is_p0) else "info"
    getattr(logger, level)(
        "sabbath_check",
        sabbath=True,
        is_sabbath=is_sabbath,
        operation=operation,
        is_p0=is_p0,
        allowed=allowed,
        **kwargs
    )


def log_aletheia_check(
    logger: structlog.BoundLogger,
    operation: str,
    uncertainty_declared: bool = False,
    hallucination_detected: bool = False,
    **kwargs
) -> None:
    """Log an Aletheia (Truth) check."""
    level = "critical" if hallucination_detected else "info"
    getattr(logger, level)(
        "truth_check",
        aletheia=True,
        operation=operation,
        uncertainty_declared=uncertainty_declared,
        hallucination_detected=hallucination_detected,
        **kwargs
    )


def log_constitutional_violation(
    logger: structlog.BoundLogger,
    article: str,
    violation_type: str,
    details: Dict[str, Any],
    **kwargs
) -> None:
    """Log a constitutional violation (CRITICAL)."""
    logger.critical(
        "constitutional_violation",
        constitutional_violation=True,
        article=article,
        violation_type=violation_type,
        details=details,
        **kwargs
    )


# 🤖 Generated with [Claude Code](https://claude.com/claude-code)
#
# Co-Authored-By: Claude <noreply@anthropic.com>
