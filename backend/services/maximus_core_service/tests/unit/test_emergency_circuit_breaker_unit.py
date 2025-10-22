"""
Emergency Circuit Breaker - Comprehensive Unit Test Suite
Coverage Target: 95%+

Tests the CRITICAL safety mechanism for constitutional violations:
- Emergency stop triggering
- Safe mode enforcement
- HITL escalation
- Audit trail logging
- Human authorization
- Status monitoring

Author: Claude Code + JuanCS-Dev (Artisanal, DOUTRINA VÉRTICE)
Date: 2025-10-21
"""

import pytest
import json
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from tempfile import TemporaryDirectory

from justice.emergency_circuit_breaker import EmergencyCircuitBreaker
from justice.constitutional_validator import (
    ViolationReport,
    ViolationLevel,
    ViolationType
)


# ===== FIXTURES =====

@pytest.fixture
def circuit_breaker():
    """Fresh circuit breaker instance for each test."""
    return EmergencyCircuitBreaker()


@pytest.fixture
def critical_violation():
    """Sample CRITICAL violation report."""
    return ViolationReport(
        is_blocking=True,
        level=ViolationLevel.CRITICAL,
        violated_law=ViolationType.LEI_ZERO,
        description="Attempted action that directly harms humans"
    )


@pytest.fixture
def warning_violation():
    """Sample WARNING violation (should NOT trigger circuit breaker)."""
    return ViolationReport(
        is_blocking=False,
        level=ViolationLevel.LOW,
        violated_law=ViolationType.MIP_VIOLATION,
        description="Minor process violation"
    )


@pytest.fixture
def valid_auth_token():
    """Generate valid authorization token."""
    timestamp = int(datetime.utcnow().timestamp())
    operator_id = "admin_001"
    return f"HUMAN_AUTH_{timestamp}_{operator_id}"


@pytest.fixture
def mock_file_operations():
    """Mock file operations to avoid permission errors."""
    with patch('builtins.open', new_callable=mock_open) as mock_file, \
         patch('justice.emergency_circuit_breaker.Path') as mock_path:
        # Setup Path mock
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = MagicMock()

        yield mock_file, mock_path


# ===== INITIALIZATION TESTS =====

class TestCircuitBreakerInitialization:
    """Tests for circuit breaker initialization."""

    @pytest.mark.unit
    def test_init_default_state(self, circuit_breaker):
        """
        SCENARIO: Initialize circuit breaker
        EXPECTED: Default state is inactive
        """
        # Assert
        assert circuit_breaker.triggered is False
        assert circuit_breaker.safe_mode is False
        assert circuit_breaker.trigger_count == 0
        assert len(circuit_breaker.incidents) == 0

    @pytest.mark.unit
    def test_init_empty_incident_list(self, circuit_breaker):
        """
        SCENARIO: New breaker has no incidents
        EXPECTED: Incidents list is empty
        """
        # Assert
        assert isinstance(circuit_breaker.incidents, list)
        assert len(circuit_breaker.incidents) == 0


# ===== TRIGGER TESTS =====

class TestCircuitBreakerTrigger:
    """Tests for emergency circuit breaker triggering."""

    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('justice.emergency_circuit_breaker.Path')
    def test_trigger_critical_violation(self, mock_path, mock_file, circuit_breaker, critical_violation):
        """
        SCENARIO: Trigger circuit breaker with CRITICAL violation
        EXPECTED: Breaker triggered, safe mode enabled
        """
        # Arrange - mock Path operations
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = MagicMock()

        # Act
        circuit_breaker.trigger(critical_violation)

        # Assert
        assert circuit_breaker.triggered is True
        assert circuit_breaker.safe_mode is True
        assert circuit_breaker.trigger_count == 1
        assert len(circuit_breaker.incidents) == 1
        assert circuit_breaker.incidents[0] == critical_violation

    @pytest.mark.unit
    @patch('builtins.open', new_callable=mock_open)
    @patch('justice.emergency_circuit_breaker.Path')
    def test_trigger_increments_count(self, mock_path, mock_file, circuit_breaker, critical_violation):
        """
        SCENARIO: Multiple triggers increment counter
        EXPECTED: trigger_count increases with each trigger
        """
        # Arrange
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = MagicMock()

        # Act
        circuit_breaker.trigger(critical_violation)
        circuit_breaker.trigger(critical_violation)
        circuit_breaker.trigger(critical_violation)

        # Assert
        assert circuit_breaker.trigger_count == 3
        assert len(circuit_breaker.incidents) == 3

    @pytest.mark.unit
    def test_trigger_stores_all_incidents(self, circuit_breaker, critical_violation, warning_violation, mock_file_operations):
        """
        SCENARIO: Store all triggered violations
        EXPECTED: All incidents stored in order
        """
        # Create second CRITICAL violation for testing
        critical_violation_2 = ViolationReport(
            is_blocking=True,
            level=ViolationLevel.CRITICAL,
            violated_law=ViolationType.LEI_I,
            description="Violated autonomy"
        )

        # Act
        circuit_breaker.trigger(critical_violation)
        circuit_breaker.trigger(critical_violation_2)

        # Assert
        assert len(circuit_breaker.incidents) == 2
        assert circuit_breaker.incidents[0].violated_law == ViolationType.LEI_ZERO
        assert circuit_breaker.incidents[1].violated_law == ViolationType.LEI_I

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.logger')
    def test_trigger_logs_critical_message(self, mock_logger, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Trigger logs CRITICAL level messages
        EXPECTED: Logger.critical called with violation details
        """
        # Act
        circuit_breaker.trigger(critical_violation)

        # Assert - logger.critical was called
        assert mock_logger.critical.called
        # Check that violation details were logged (LEI_ZERO enum or its value)
        call_args_list = [str(call) for call in mock_logger.critical.call_args_list]
        assert any("LEI_ZERO" in str(args) or "lei_zero" in str(args) for args in call_args_list)


# ===== SAFE MODE TESTS =====

class TestSafeMode:
    """Tests for safe mode functionality."""

    @pytest.mark.unit
    def test_enter_safe_mode(self, circuit_breaker):
        """
        SCENARIO: Enter safe mode
        EXPECTED: safe_mode flag set to True
        """
        # Arrange
        assert circuit_breaker.safe_mode is False

        # Act
        circuit_breaker.enter_safe_mode()

        # Assert
        assert circuit_breaker.safe_mode is True

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.logger')
    def test_enter_safe_mode_logs_warning(self, mock_logger, circuit_breaker):
        """
        SCENARIO: Safe mode logs warning message
        EXPECTED: Logger.warning called
        """
        # Act
        circuit_breaker.enter_safe_mode()

        # Assert
        assert mock_logger.warning.called
        call_args_list = [str(call) for call in mock_logger.warning.call_args_list]
        assert any("SAFE MODE" in str(args) for args in call_args_list)

    @pytest.mark.unit
    def test_exit_safe_mode_with_valid_auth(self, circuit_breaker, valid_auth_token):
        """
        SCENARIO: Exit safe mode with valid authorization
        EXPECTED: Safe mode disabled, breaker reset
        """
        # Arrange
        circuit_breaker.safe_mode = True
        circuit_breaker.triggered = True

        # Act
        circuit_breaker.exit_safe_mode(valid_auth_token)

        # Assert
        assert circuit_breaker.safe_mode is False
        assert circuit_breaker.triggered is False

    @pytest.mark.unit
    def test_exit_safe_mode_empty_auth_raises(self, circuit_breaker):
        """
        SCENARIO: Exit with empty authorization
        EXPECTED: ValueError raised
        """
        # Arrange
        circuit_breaker.safe_mode = True

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid authorization: empty"):
            circuit_breaker.exit_safe_mode("")

        with pytest.raises(ValueError, match="Invalid authorization: empty"):
            circuit_breaker.exit_safe_mode("   ")

    @pytest.mark.unit
    def test_exit_safe_mode_invalid_format_raises(self, circuit_breaker):
        """
        SCENARIO: Exit with invalid authorization format
        EXPECTED: ValueError raised with format error
        """
        # Arrange
        circuit_breaker.safe_mode = True

        # Act & Assert
        with pytest.raises(ValueError, match="must start with 'HUMAN_AUTH_'"):
            circuit_breaker.exit_safe_mode("INVALID_TOKEN_123")

    @pytest.mark.unit
    def test_exit_safe_mode_malformed_token_raises(self, circuit_breaker):
        """
        SCENARIO: Exit with malformed token (missing parts)
        EXPECTED: ValueError raised
        """
        # Arrange
        circuit_breaker.safe_mode = True

        # Act & Assert
        with pytest.raises(ValueError, match="expected 'HUMAN_AUTH_"):
            circuit_breaker.exit_safe_mode("HUMAN_AUTH_")

        with pytest.raises(ValueError, match="expected 'HUMAN_AUTH_"):
            circuit_breaker.exit_safe_mode("HUMAN_AUTH_123")

    @pytest.mark.unit
    def test_exit_safe_mode_invalid_timestamp_raises(self, circuit_breaker):
        """
        SCENARIO: Exit with non-numeric timestamp
        EXPECTED: ValueError raised
        """
        # Arrange
        circuit_breaker.safe_mode = True

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid authorization timestamp"):
            circuit_breaker.exit_safe_mode("HUMAN_AUTH_abc_operator")

    @pytest.mark.unit
    def test_exit_safe_mode_old_timestamp_raises(self, circuit_breaker):
        """
        SCENARIO: Exit with timestamp older than 1 hour
        EXPECTED: ValueError raised
        """
        # Arrange
        circuit_breaker.safe_mode = True
        old_timestamp = int(datetime.utcnow().timestamp()) - 7200  # 2 hours ago

        # Act & Assert
        with pytest.raises(ValueError, match="timestamp too old or in future"):
            circuit_breaker.exit_safe_mode(f"HUMAN_AUTH_{old_timestamp}_operator")


# ===== ESCALATION TESTS =====

class TestHITLEscalation:
    """Tests for HITL escalation functionality."""

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_escalate_writes_to_file(self, mock_file, mock_path, circuit_breaker, critical_violation):
        """
        SCENARIO: HITL escalation writes to file queue
        EXPECTED: Escalation JSON written to hitl_escalations.jsonl
        """
        # Arrange
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = MagicMock()

        # Act
        circuit_breaker._escalate_to_hitl(critical_violation)

        # Assert
        mock_file.assert_called_once()
        handle = mock_file()
        assert handle.write.called

        # Verify JSON structure
        written_data = handle.write.call_args[0][0]
        assert "constitutional_violation" in written_data
        assert "CRITICAL" in written_data
        # Check for enum value
        assert "lei_zero" in written_data.lower()

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.logger')
    @patch('justice.emergency_circuit_breaker.Path')
    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_escalate_handles_write_failure(self, mock_file, mock_path, mock_logger, circuit_breaker, critical_violation):
        """
        SCENARIO: HITL escalation file write fails
        EXPECTED: Error logged, no exception raised
        """
        # Act
        circuit_breaker._escalate_to_hitl(critical_violation)

        # Assert - error logged but didn't crash
        assert mock_logger.error.called
        error_calls = [str(call) for call in mock_logger.error.call_args_list]
        assert any("Failed to write HITL escalation" in str(call) for call in error_calls)


# ===== AUDIT LOG TESTS =====

class TestAuditLogging:
    """Tests for audit trail logging."""

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_log_incident_writes_audit(self, mock_file, mock_path, circuit_breaker, critical_violation):
        """
        SCENARIO: Log incident to audit trail
        EXPECTED: JSON written to circuit_breaker_audit.jsonl
        """
        # Arrange
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir = MagicMock()
        circuit_breaker.trigger_count = 1

        # Act
        circuit_breaker._log_incident(critical_violation)

        # Assert
        mock_file.assert_called_once()
        handle = mock_file()
        assert handle.write.called

        # Verify JSON structure
        written_data = handle.write.call_args[0][0]
        assert "CONST_VIOLATION_" in written_data
        # Check for enum value
        assert "lei_zero" in written_data.lower()

    @pytest.mark.unit
    @patch('justice.emergency_circuit_breaker.logger')
    @patch('justice.emergency_circuit_breaker.Path')
    @patch('builtins.open', side_effect=PermissionError("Access denied"))
    def test_log_incident_handles_permission_error(self, mock_file, mock_path, mock_logger, circuit_breaker, critical_violation):
        """
        SCENARIO: Audit log write fails with permission error
        EXPECTED: Error logged, no crash
        """
        # Arrange
        circuit_breaker.trigger_count = 1

        # Act
        circuit_breaker._log_incident(critical_violation)

        # Assert
        assert mock_logger.error.called


# ===== STATUS MONITORING TESTS =====

class TestStatusMonitoring:
    """Tests for status monitoring and history."""

    @pytest.mark.unit
    def test_get_status_default(self, circuit_breaker):
        """
        SCENARIO: Get status of fresh breaker
        EXPECTED: All flags False, counts zero
        """
        # Act
        status = circuit_breaker.get_status()

        # Assert
        assert status["triggered"] is False
        assert status["safe_mode"] is False
        assert status["trigger_count"] == 0
        assert status["incident_count"] == 0
        assert status["last_incident"] is None

    @pytest.mark.unit
    def test_get_status_after_trigger(self, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Get status after triggering
        EXPECTED: Status reflects triggered state
        """
        # Arrange
        circuit_breaker.trigger(critical_violation)

        # Act
        status = circuit_breaker.get_status()

        # Assert
        assert status["triggered"] is True
        assert status["safe_mode"] is True
        assert status["trigger_count"] == 1
        assert status["incident_count"] == 1
        assert status["last_incident"] is not None
        # violated_law is now a ViolationType enum, check the value or name
        assert "lei_zero" in str(status["last_incident"]["violated_law"]).lower()
        assert status["last_incident"]["level"] == "CRITICAL"

    @pytest.mark.unit
    def test_get_incident_history_empty(self, circuit_breaker):
        """
        SCENARIO: Get history with no incidents
        EXPECTED: Empty list
        """
        # Act
        history = circuit_breaker.get_incident_history()

        # Assert
        assert isinstance(history, list)
        assert len(history) == 0

    @pytest.mark.unit
    def test_get_incident_history_with_incidents(self, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Get incident history after triggers
        EXPECTED: List of incidents, most recent first
        """
        # Arrange - trigger 3 times
        for i in range(3):
            circuit_breaker.trigger(critical_violation)

        # Act
        history = circuit_breaker.get_incident_history(limit=10)

        # Assert
        assert len(history) == 3
        # All should be same violation (check if LEI_ZERO enum is in string representation)
        assert all("lei_zero" in str(inc["violated_law"]).lower() for inc in history)
        assert all(inc["level"] == "CRITICAL" for inc in history)

    @pytest.mark.unit
    def test_get_incident_history_respects_limit(self, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Get limited incident history
        EXPECTED: Returns only requested number
        """
        # Arrange - trigger 10 times
        for i in range(10):
            circuit_breaker.trigger(critical_violation)

        # Act
        history = circuit_breaker.get_incident_history(limit=3)

        # Assert
        assert len(history) == 3


# ===== RESET TESTS =====

class TestCircuitBreakerReset:
    """Tests for circuit breaker reset functionality."""

    @pytest.mark.unit
    def test_reset_with_authorization(self, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Reset circuit breaker with authorization
        EXPECTED: Flags cleared, history preserved
        """
        # Arrange
        circuit_breaker.trigger(critical_violation)
        assert circuit_breaker.triggered is True
        assert circuit_breaker.safe_mode is True

        # Act
        circuit_breaker.reset("ADMIN_OVERRIDE_001")

        # Assert
        assert circuit_breaker.triggered is False
        assert circuit_breaker.safe_mode is False
        # History preserved for audit
        assert circuit_breaker.trigger_count == 1
        assert len(circuit_breaker.incidents) == 1

    @pytest.mark.unit
    def test_reset_without_authorization_raises(self, circuit_breaker):
        """
        SCENARIO: Attempt reset without authorization
        EXPECTED: ValueError raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Authorization required"):
            circuit_breaker.reset("")

        with pytest.raises(ValueError, match="Authorization required"):
            circuit_breaker.reset("   ")

        with pytest.raises(ValueError, match="Authorization required"):
            circuit_breaker.reset(None)


# ===== INTEGRATION TESTS =====

class TestCircuitBreakerIntegration:
    """Integration tests for full workflow."""

    @pytest.mark.unit
    def test_full_trigger_and_recovery_workflow(self, circuit_breaker, critical_violation, valid_auth_token, mock_file_operations):
        """
        SCENARIO: Complete workflow - trigger, safe mode, recovery
        EXPECTED: All steps work together correctly
        """
        # Step 1: Initial state
        assert circuit_breaker.safe_mode is False

        # Step 2: Trigger circuit breaker
        circuit_breaker.trigger(critical_violation)
        assert circuit_breaker.triggered is True
        assert circuit_breaker.safe_mode is True

        # Step 3: Verify status
        status = circuit_breaker.get_status()
        assert status["safe_mode"] is True
        assert status["trigger_count"] == 1

        # Step 4: Exit safe mode
        circuit_breaker.exit_safe_mode(valid_auth_token)
        assert circuit_breaker.safe_mode is False

        # Step 5: History preserved
        assert len(circuit_breaker.incidents) == 1

    @pytest.mark.unit
    def test_multiple_violations_accumulate(self, circuit_breaker, critical_violation, mock_file_operations):
        """
        SCENARIO: Multiple violations during safe mode
        EXPECTED: All violations logged, count increases
        """
        # Arrange & Act - trigger 5 times
        for i in range(5):
            circuit_breaker.trigger(critical_violation)

        # Assert
        assert circuit_breaker.trigger_count == 5
        assert len(circuit_breaker.incidents) == 5
        assert circuit_breaker.safe_mode is True  # Still in safe mode

        # Check status
        status = circuit_breaker.get_status()
        assert status["trigger_count"] == 5
        assert status["incident_count"] == 5
