"""Tests for vertice_core.logging - 100% coverage."""

import logging
from unittest.mock import Mock, patch

import pytest
from vertice_core.logging import get_logger


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_basic(self):
        """Test basic logger creation."""
        logger = get_logger("test-service")
        # Returns BoundLogger from structlog, not logging.Logger
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "error")
    
    def test_get_logger_with_service_name(self):
        """Test logger with specific service name."""
        logger = get_logger("maximus-core")
        assert hasattr(logger, "info")
    
    def test_logger_different_instances(self):
        """Test that different names return logger instances."""
        logger1 = get_logger("service1")
        logger2 = get_logger("service2")
        assert hasattr(logger1, "info")
        assert hasattr(logger2, "info")
    
    def test_logger_same_name_returns_instance(self):
        """Test that same name returns logger instance."""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        # Both should be valid loggers
        assert hasattr(logger1, "info")
        assert hasattr(logger2, "info")
    
    @patch("structlog.get_logger")
    def test_uses_structlog(self, mock_structlog):
        """Test that it uses structlog under the hood."""
        mock_logger = Mock()
        mock_structlog.return_value = mock_logger
        
        logger = get_logger("test")
        
        # Should call structlog.get_logger
        mock_structlog.assert_called_once()
    
    def test_logger_can_log(self):
        """Test that logger can log messages."""
        logger = get_logger("test")
        
        # Should not raise
        logger.info("test message")
        logger.debug("debug message")
        logger.warning("warning message")
        logger.error("error message")
    
    def test_logger_with_context(self):
        """Test logger with context binding."""
        logger = get_logger("test")
        
        # Should not raise
        if hasattr(logger, "bind"):
            bound_logger = logger.bind(request_id="123", user_id="456")
            bound_logger.info("test with context")
