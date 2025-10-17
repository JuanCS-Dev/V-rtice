"""Tests for vertice_core.logging module."""

import json

import pytest
import structlog
from vertice_core.logging import get_logger


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_structlog_instance(self) -> None:
        """Test that get_logger returns a structlog BoundLogger."""
        logger = get_logger("test_service")
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")

    def test_accepts_custom_log_level(self) -> None:
        """Test that custom log level can be set."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger = get_logger("test_service", level=level)
            assert logger is not None

    def test_rejects_invalid_log_level(self) -> None:
        """Test that invalid log level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid log level.*Must be one of"):
            get_logger("test_service", level="INVALID")

    def test_invalid_level_error_message_format(self) -> None:
        """Test that error message contains expected format."""
        try:
            get_logger("test_service", level="BADLEVEL")
        except ValueError as e:
            assert "Invalid log level: BADLEVEL" in str(e)
            assert "Must be one of:" in str(e)
            assert "DEBUG" in str(e)
            assert "INFO" in str(e)

    def test_case_insensitive_log_level(self) -> None:
        """Test that log level is case-insensitive."""
        logger_upper = get_logger("test1", level="INFO")
        logger_lower = get_logger("test2", level="info")
        logger_mixed = get_logger("test3", level="InFo")

        assert logger_upper is not None
        assert logger_lower is not None
        assert logger_mixed is not None


class TestLogOutput:
    """Tests for log output format."""

    def test_outputs_valid_json(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that logger outputs valid JSON."""
        logger = get_logger("test_service", level="INFO")
        logger.info("test_event", user_id=123, action="login")

        captured = capsys.readouterr()
        log_line = captured.out.strip()

        log_entry = json.loads(log_line)
        assert isinstance(log_entry, dict)

    def test_includes_required_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that log entry includes all required fields."""
        logger = get_logger("test_service", level="INFO")
        logger.info("test_event", user_id=123)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        assert "event" in log_entry
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "logger" in log_entry

        assert log_entry["event"] == "test_event"
        assert log_entry["level"] == "info"
        assert log_entry["logger"] == "test_service"
        assert log_entry["user_id"] == 123

    def test_preserves_custom_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that custom fields are preserved."""
        logger = get_logger("test_service", level="INFO")

        custom_data = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }

        logger.info("test_event", **custom_data)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        for key, value in custom_data.items():
            assert log_entry[key] == value


class TestLogLevels:
    """Tests for log level filtering."""

    def test_respects_log_level_filtering(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that log level filtering works correctly."""
        logger = get_logger("test_service", level="WARNING")

        logger.debug("debug_message")
        logger.info("info_message")
        captured = capsys.readouterr()
        assert captured.out == ""

        logger.warning("warning_message")
        captured = capsys.readouterr()
        assert "warning_message" in captured.out

        logger.error("error_message")
        captured = capsys.readouterr()
        assert "error_message" in captured.out

    def test_debug_level_shows_all(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that DEBUG level shows all messages."""
        logger = get_logger("test_service", level="DEBUG")

        logger.debug("debug_msg")
        logger.info("info_msg")
        logger.warning("warning_msg")

        captured = capsys.readouterr()
        assert "debug_msg" in captured.out
        assert "info_msg" in captured.out
        assert "warning_msg" in captured.out


class TestExceptionLogging:
    """Tests for exception handling."""

    def test_formats_exceptions_correctly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that exceptions are properly captured and formatted."""
        logger = get_logger("test_service", level="ERROR")

        try:
            raise ValueError("Test error message")
        except ValueError:
            logger.exception("error_occurred", context="test_operation")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        log_entry = json.loads(lines[0])

        assert log_entry["event"] == "error_occurred"
        assert log_entry["context"] == "test_operation"
        assert "exception" in log_entry
        assert "ValueError" in log_entry["exception"]
        assert "Test error message" in log_entry["exception"]

    def test_captures_stack_trace(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that stack trace is included in exception logs."""
        logger = get_logger("test_service", level="ERROR")

        try:
            _ = 1 / 0
        except ZeroDivisionError:
            logger.exception("division_error")

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        log_entry = json.loads(lines[0])

        assert "exception" in log_entry
        assert "ZeroDivisionError" in log_entry["exception"]
        assert "division by zero" in log_entry["exception"]
        assert "Traceback" in log_entry["exception"]


class TestContextVariables:
    """Tests for context variables support."""

    def test_context_variables_included(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that context variables are automatically included."""
        logger = get_logger("test_service", level="INFO")

        structlog.contextvars.bind_contextvars(
            request_id="req-123",
            user_id=456,
        )

        logger.info("test_event", action="login")

        structlog.contextvars.clear_contextvars()

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        assert log_entry["request_id"] == "req-123"
        assert log_entry["user_id"] == 456
        assert log_entry["action"] == "login"

    def test_context_cleared_properly(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that clearing context removes variables."""
        logger = get_logger("test_service", level="INFO")

        structlog.contextvars.bind_contextvars(temp_var="temp_value")
        structlog.contextvars.clear_contextvars()

        logger.info("test_event")

        captured = capsys.readouterr()
        log_entry = json.loads(captured.out.strip())

        assert "temp_var" not in log_entry


class TestMultipleLoggers:
    """Tests for multiple logger instances."""

    def test_multiple_loggers_independent(self) -> None:
        """Test that multiple loggers can coexist."""
        logger1 = get_logger("service1")
        logger2 = get_logger("service2")

        assert logger1 is not None
        assert logger2 is not None

    def test_loggers_have_correct_names(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that each logger has its correct name."""
        logger1 = get_logger("service_alpha", level="INFO")
        logger2 = get_logger("service_beta", level="INFO")

        logger1.info("event_from_alpha")
        out1 = capsys.readouterr().out
        log1 = json.loads(out1.strip())

        logger2.info("event_from_beta")
        out2 = capsys.readouterr().out
        log2 = json.loads(out2.strip())

        assert log1["logger"] == "service_alpha"
        assert log2["logger"] == "service_beta"
