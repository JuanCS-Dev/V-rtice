"""Common Observability Module - Structured Logging.

Reusable structured logging for all Vértice services.
Provides JSON-formatted logs with correlation IDs, contextual data.

Usage:
    from backend.common.observability.logging import setup_logging, get_logger
    
    # Setup once at startup
    setup_logging(service_name="bas_service", level="INFO")
    
    # Use in modules
    logger = get_logger(__name__)
    logger.info("Operation started", extra={"sim_id": "123", "user": "admin"})
"""

import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import json
    JSON_AVAILABLE = True
except ImportError:
    JSON_AVAILABLE = False


# Context variable for correlation ID (request tracing)
correlation_id_var: ContextVar[Optional[str]] = ContextVar(
    "correlation_id",
    default=None
)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.
    
    Produces logs like:
    {
        "timestamp": "2025-10-11T18:30:45.123Z",
        "level": "INFO",
        "service": "bas_service",
        "logger": "api",
        "message": "Simulation started",
        "correlation_id": "abc-123",
        "sim_id": "xyz-789",
        "user": "admin"
    }
    """
    
    def __init__(self, service_name: str = "vertice"):
        """Initialize JSON formatter.
        
        Args:
            service_name: Name of the service for log context
        """
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        if not JSON_AVAILABLE:
            # Fallback to standard format
            return super().format(record)
        
        # Base log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add extra fields from log call
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds contextual information.
    
    Automatically includes correlation ID and custom context.
    """
    
    def process(
        self,
        msg: str,
        kwargs: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """Process log message to add context.
        
        Args:
            msg: Log message
            kwargs: Log keyword arguments
            
        Returns:
            Tuple of (message, updated kwargs)
        """
        # Get extra fields from kwargs
        extra = kwargs.get("extra", {})
        
        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            extra["correlation_id"] = correlation_id
        
        # Add adapter context
        extra.update(self.extra)
        
        # Store extra fields for formatter
        kwargs["extra"] = {"extra_fields": extra}
        
        return msg, kwargs


def setup_logging(
    service_name: str = "vertice",
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
):
    """Setup structured logging for service.
    
    Args:
        service_name: Name of the service
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: "json" or "text"
        log_file: Optional file path for logging to file
    """
    # Determine formatter
    if format_type == "json" and JSON_AVAILABLE:
        formatter_class = JSONFormatter
        formatter_args = {"service_name": service_name}
    else:
        # Fallback to standard format
        formatter_class = logging.Formatter
        formatter_args = {
            "fmt": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    
    # Setup handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
            "level": level,
        }
    }
    
    if log_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "default",
            "level": level,
        }
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
                **formatter_args
            }
        },
        "handlers": handlers,
        "root": {
            "level": level,
            "handlers": list(handlers.keys())
        }
    }
    
    logging.config.dictConfig(config)
    
    # Log setup completion
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured for {service_name}",
        extra={
            "level": level,
            "format": format_type,
            "json_available": JSON_AVAILABLE
        }
    )


def get_logger(name: str, **context) -> ContextAdapter:
    """Get logger with contextual adapter.
    
    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all logs
        
    Returns:
        Logger adapter with context
        
    Example:
        logger = get_logger(__name__, service="bas", user="admin")
        logger.info("Operation started", extra={"sim_id": "123"})
    """
    base_logger = logging.getLogger(name)
    return ContextAdapter(base_logger, context)


def set_correlation_id(correlation_id: Optional[str] = None):
    """Set correlation ID for request tracing.
    
    Args:
        correlation_id: Correlation ID (auto-generated if None)
        
    Returns:
        The correlation ID set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID.
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


# FastAPI middleware for correlation ID
def correlation_id_middleware():
    """FastAPI middleware to set correlation ID per request.
    
    Usage:
        from fastapi import FastAPI, Request
        from backend.common.observability.logging import correlation_id_middleware
        
        app = FastAPI()
        
        @app.middleware("http")
        async def add_correlation_id(request: Request, call_next):
            return await correlation_id_middleware()(request, call_next)
    """
    from fastapi import Request, Response
    
    async def middleware(request: Request, call_next):
        # Get correlation ID from header or generate new
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Set in context
        set_correlation_id(correlation_id)
        
        # Add to response headers
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    
    return middleware


__all__ = [
    "setup_logging",
    "get_logger",
    "set_correlation_id",
    "get_correlation_id",
    "correlation_id_middleware",
    "JSONFormatter",
    "ContextAdapter",
]
