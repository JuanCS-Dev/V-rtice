"""Structured JSON logging for all Vértice services."""

import logging
import sys

import structlog

_LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def get_logger(
    service_name: str,
    level: str = "INFO",
) -> structlog.stdlib.BoundLogger:
    """Get a configured structured logger for a service."""
    level_upper = level.upper()
    if level_upper not in _LOG_LEVELS:
        raise ValueError(
            f"Invalid log level: {level}. "
            f"Must be one of: {', '.join(_LOG_LEVELS.keys())}"
        )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=_LOG_LEVELS[level_upper],
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    return structlog.get_logger(service_name)  # type: ignore[no-any-return]
