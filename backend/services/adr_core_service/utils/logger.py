"""Logging utilities for the ADR Core Service.

This module provides standardized logger configuration for other parts of
the service, ensuring consistent log formatting and output.

Typical usage example:

  from .logger import setup_logger
  logger = setup_logger("my_module")
  logger.info("This is an informational message.")
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logger(
    name: str = "adr_core",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """Configures and retrieves a logger instance.

    Sets up a logger with a specified name and level, adding handlers for
    console output and optionally for a log file. It ensures a consistent
    format for all log messages. If the logger already has handlers, they
    are cleared to avoid duplication.

    Args:
        name (str, optional): The name of the logger. Defaults to "adr_core".
        level (str, optional): The minimum log level to capture (e.g., "INFO",
            "DEBUG"). Defaults to "INFO".
        log_file (Optional[str], optional): If provided, logs will also be
            written to this file path. Defaults to None.

    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Format
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retrieves a logger by name.

    This is a convenience function to get a logger instance that is expected
    to have been previously configured by `setup_logger`. It simply wraps
    `logging.getLogger`.

    Args:
        name (str): The name of the logger to retrieve.

    Returns:
        logging.Logger: The logger instance.
    """
    return logging.getLogger(name)