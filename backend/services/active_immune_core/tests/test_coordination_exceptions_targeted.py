"""
Coordination Exceptions - Targeted Coverage Tests

Objetivo: Cobrir coordination/exceptions.py (79 lines, 0% → 100%)

Testa custom exceptions: hierarchy, raising, message handling

Author: Claude Code + JuanCS-Dev
Date: 2025-10-23
Lei Governante: Constituição Vértice v2.6
"""

import pytest
import sys
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import exceptions.py directly without triggering coordination/__init__.py
exceptions_path = Path(__file__).parent.parent / "coordination" / "exceptions.py"
spec = importlib.util.spec_from_file_location("coordination.exceptions", exceptions_path)
exceptions_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exceptions_module)

# Extract exception classes
LymphnodeException = exceptions_module.LymphnodeException
LymphnodeConfigurationError = exceptions_module.LymphnodeConfigurationError
LymphnodeConnectionError = exceptions_module.LymphnodeConnectionError
LymphnodeValidationError = exceptions_module.LymphnodeValidationError
LymphnodeRateLimitError = exceptions_module.LymphnodeRateLimitError
LymphnodeResourceExhaustedError = exceptions_module.LymphnodeResourceExhaustedError
CytokineProcessingError = exceptions_module.CytokineProcessingError
PatternDetectionError = exceptions_module.PatternDetectionError
AgentOrchestrationError = exceptions_module.AgentOrchestrationError
HormonePublishError = exceptions_module.HormonePublishError
ESGTIntegrationError = exceptions_module.ESGTIntegrationError
LymphnodeStateError = exceptions_module.LymphnodeStateError


# ===== BASE EXCEPTION TESTS =====


def test_lymphnode_exception_is_exception():
    """
    SCENARIO: LymphnodeException class
    EXPECTED: Is subclass of Exception
    """
    assert issubclass(LymphnodeException, Exception)


def test_lymphnode_exception_can_be_raised():
    """
    SCENARIO: Raise LymphnodeException
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeException):
        raise LymphnodeException("test error")


def test_lymphnode_exception_with_message():
    """
    SCENARIO: LymphnodeException raised with message
    EXPECTED: Message is preserved
    """
    msg = "Custom error message"
    with pytest.raises(LymphnodeException) as exc_info:
        raise LymphnodeException(msg)

    assert str(exc_info.value) == msg


# ===== CONFIGURATION ERROR TESTS =====


def test_configuration_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeConfigurationError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeConfigurationError, LymphnodeException)


def test_configuration_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeConfigurationError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeConfigurationError):
        raise LymphnodeConfigurationError("invalid config")


def test_configuration_error_catches_as_base():
    """
    SCENARIO: Raise LymphnodeConfigurationError
    EXPECTED: Can be caught as LymphnodeException
    """
    with pytest.raises(LymphnodeException):
        raise LymphnodeConfigurationError("config error")


# ===== CONNECTION ERROR TESTS =====


def test_connection_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeConnectionError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeConnectionError, LymphnodeException)


def test_connection_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeConnectionError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeConnectionError):
        raise LymphnodeConnectionError("Redis connection failed")


# ===== VALIDATION ERROR TESTS =====


def test_validation_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeValidationError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeValidationError, LymphnodeException)


def test_validation_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeValidationError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeValidationError):
        raise LymphnodeValidationError("validation failed")


# ===== RATE LIMIT ERROR TESTS =====


def test_rate_limit_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeRateLimitError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeRateLimitError, LymphnodeException)


def test_rate_limit_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeRateLimitError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeRateLimitError):
        raise LymphnodeRateLimitError("rate limit exceeded")


# ===== RESOURCE EXHAUSTED ERROR TESTS =====


def test_resource_exhausted_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeResourceExhaustedError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeResourceExhaustedError, LymphnodeException)


def test_resource_exhausted_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeResourceExhaustedError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeResourceExhaustedError):
        raise LymphnodeResourceExhaustedError("too many agents")


# ===== CYTOKINE PROCESSING ERROR TESTS =====


def test_cytokine_processing_error_is_lymphnode_exception():
    """
    SCENARIO: CytokineProcessingError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(CytokineProcessingError, LymphnodeException)


def test_cytokine_processing_error_can_be_raised():
    """
    SCENARIO: Raise CytokineProcessingError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(CytokineProcessingError):
        raise CytokineProcessingError("cytokine processing failed")


# ===== PATTERN DETECTION ERROR TESTS =====


def test_pattern_detection_error_is_lymphnode_exception():
    """
    SCENARIO: PatternDetectionError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(PatternDetectionError, LymphnodeException)


def test_pattern_detection_error_can_be_raised():
    """
    SCENARIO: Raise PatternDetectionError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(PatternDetectionError):
        raise PatternDetectionError("pattern detection failed")


# ===== AGENT ORCHESTRATION ERROR TESTS =====


def test_agent_orchestration_error_is_lymphnode_exception():
    """
    SCENARIO: AgentOrchestrationError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(AgentOrchestrationError, LymphnodeException)


def test_agent_orchestration_error_can_be_raised():
    """
    SCENARIO: Raise AgentOrchestrationError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(AgentOrchestrationError):
        raise AgentOrchestrationError("clone creation failed")


# ===== HORMONE PUBLISH ERROR TESTS =====


def test_hormone_publish_error_is_lymphnode_exception():
    """
    SCENARIO: HormonePublishError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(HormonePublishError, LymphnodeException)


def test_hormone_publish_error_can_be_raised():
    """
    SCENARIO: Raise HormonePublishError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(HormonePublishError):
        raise HormonePublishError("hormone publish failed")


# ===== ESGT INTEGRATION ERROR TESTS =====


def test_esgt_integration_error_is_lymphnode_exception():
    """
    SCENARIO: ESGTIntegrationError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(ESGTIntegrationError, LymphnodeException)


def test_esgt_integration_error_can_be_raised():
    """
    SCENARIO: Raise ESGTIntegrationError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(ESGTIntegrationError):
        raise ESGTIntegrationError("ESGT integration failed")


# ===== STATE ERROR TESTS =====


def test_state_error_is_lymphnode_exception():
    """
    SCENARIO: LymphnodeStateError class
    EXPECTED: Is subclass of LymphnodeException
    """
    assert issubclass(LymphnodeStateError, LymphnodeException)


def test_state_error_can_be_raised():
    """
    SCENARIO: Raise LymphnodeStateError
    EXPECTED: Can be raised and caught
    """
    with pytest.raises(LymphnodeStateError):
        raise LymphnodeStateError("invalid state for operation")


# ===== EXCEPTION HIERARCHY TESTS =====


def test_all_exceptions_inherit_from_base():
    """
    SCENARIO: All custom exceptions
    EXPECTED: All inherit from LymphnodeException
    """
    exceptions = [
        LymphnodeConfigurationError,
        LymphnodeConnectionError,
        LymphnodeValidationError,
        LymphnodeRateLimitError,
        LymphnodeResourceExhaustedError,
        CytokineProcessingError,
        PatternDetectionError,
        AgentOrchestrationError,
        HormonePublishError,
        ESGTIntegrationError,
        LymphnodeStateError,
    ]

    for exc_class in exceptions:
        assert issubclass(exc_class, LymphnodeException)


def test_all_exceptions_are_exceptions():
    """
    SCENARIO: All custom exceptions
    EXPECTED: All inherit from Exception
    """
    exceptions = [
        LymphnodeException,
        LymphnodeConfigurationError,
        LymphnodeConnectionError,
        LymphnodeValidationError,
        LymphnodeRateLimitError,
        LymphnodeResourceExhaustedError,
        CytokineProcessingError,
        PatternDetectionError,
        AgentOrchestrationError,
        HormonePublishError,
        ESGTIntegrationError,
        LymphnodeStateError,
    ]

    for exc_class in exceptions:
        assert issubclass(exc_class, Exception)


# ===== DOCSTRING TESTS =====


def test_base_exception_docstring():
    """
    SCENARIO: LymphnodeException.__doc__
    EXPECTED: Has docstring
    """
    assert LymphnodeException.__doc__ is not None
    assert "Base exception" in LymphnodeException.__doc__


def test_configuration_error_docstring():
    """
    SCENARIO: LymphnodeConfigurationError.__doc__
    EXPECTED: Mentions configuration
    """
    doc = LymphnodeConfigurationError.__doc__
    assert doc is not None
    assert "configuration" in doc.lower()


def test_connection_error_docstring():
    """
    SCENARIO: LymphnodeConnectionError.__doc__
    EXPECTED: Mentions connection
    """
    doc = LymphnodeConnectionError.__doc__
    assert doc is not None
    assert "connection" in doc.lower()


def test_module_docstring():
    """
    SCENARIO: coordination.exceptions module
    EXPECTED: Has module docstring describing purpose
    """
    doc = exceptions_module.__doc__
    assert doc is not None
    assert "Exception" in doc or "exception" in doc.lower()
