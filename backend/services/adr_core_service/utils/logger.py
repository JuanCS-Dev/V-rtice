"""Maximus ADR Core Service - Logging Utilities.

This module provides a standardized logging configuration for the Automated
Detection and Response (ADR) service. It ensures consistent log formatting,
output destinations, and log levels across all components of the ADR system.

By centralizing logging configuration, Maximus AI can effectively capture
operational events, debug information, warnings, and errors, which is crucial
for monitoring the system's health, troubleshooting issues, and auditing
security-related activities.
"""

import logging
import sys


def setup_logger(name: str) -> logging.Logger:
    """Sets up a standardized logger for ADR Core Service modules.

    Args:
        name (str): The name of the logger, typically __name__ of the module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Default logging level

    # Prevent adding multiple handlers if the logger is already configured
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional: File handler for persistent logs
        # file_handler = logging.FileHandler('adr_service.log')
        # file_handler.setLevel(logging.DEBUG)
        # file_handler.setFormatter(formatter)
        # logger.addHandler(file_handler)

    return logger
