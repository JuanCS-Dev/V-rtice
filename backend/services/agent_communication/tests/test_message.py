"""Tests for Agent Communication Protocol message schemas."""
import json
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from agent_communication.message import (
    ACPMessage,
    AgentType,
    ErrorMessage,
    HOTLRequestMessage,
    HOTLResponseMessage,
    MessageType,
    StatusUpdateMessage,
    TaskAssignMessage,
    TaskPriority,
    TaskResultMessage,
)


class TestACPMessage:
    """Test suite for ACPMessage base class."""

    def test_message_creation(self):
        """Test basic message creation with required fields."""
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={"test": "data"},
        )

        assert msg.message_type == MessageType.TASK_ASSIGN
        assert msg.sender == AgentType.ORCHESTRATOR
        assert msg.recipient == AgentType.RECONNAISSANCE
        assert msg.payload == {"test": "data"}
        assert isinstance(msg.message_id, UUID)
        assert isinstance(msg.timestamp, datetime)
        assert msg.priority == TaskPriority.MEDIUM  # default

    def test_message_with_correlation_id(self):
        """Test message creation with correlation ID for request/response tracking."""
        correlation_id = uuid4()
        msg = ACPMessage(
            message_type=MessageType.TASK_RESULT,
            sender=AgentType.RECONNAISSANCE,
            recipient=AgentType.ORCHESTRATOR,
            correlation_id=correlation_id,
            payload={"result": "success"},
        )

        assert msg.correlation_id == correlation_id

    def test_message_priority_levels(self):
        """Test all priority levels can be set."""
        for priority in TaskPriority:
            msg = ACPMessage(
                message_type=MessageType.TASK_ASSIGN,
                sender=AgentType.ORCHESTRATOR,
                recipient=AgentType.EXPLOITATION,
                priority=priority,
                payload={},
            )
            assert msg.priority == priority

    def test_message_json_serialization(self):
        """Test message can be serialized to JSON and back."""
        original_msg = ACPMessage(
            message_type=MessageType.STATUS_UPDATE,
            sender=AgentType.EXPLOITATION,
            recipient=AgentType.ORCHESTRATOR,
            payload={"progress": 50},
        )

        # Serialize
        json_str = original_msg.to_json()
        assert isinstance(json_str, str)
        parsed_json = json.loads(json_str)
        assert "message_id" in parsed_json
        assert parsed_json["message_type"] == "status_update"

        # Deserialize
        restored_msg = ACPMessage.from_json(json_str)
        assert restored_msg.message_id == original_msg.message_id
        assert restored_msg.message_type == original_msg.message_type
        assert restored_msg.sender == original_msg.sender
        assert restored_msg.recipient == original_msg.recipient
        assert restored_msg.payload == original_msg.payload

    def test_message_with_metadata(self):
        """Test message optional metadata field."""
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={},
            metadata={"session_id": "test-123", "operator": "admin"},
        )

        assert msg.metadata is not None
        assert msg.metadata["session_id"] == "test-123"


class TestTaskAssignMessage:
    """Test suite for TaskAssignMessage payload schema."""

    def test_task_assign_creation(self):
        """Test task assignment message creation."""
        task = TaskAssignMessage(
            task_type="port_scan",
            target="10.0.0.1",
            parameters={"ports": [80, 443, 22]},
            timeout_seconds=600,
        )

        assert task.task_type == "port_scan"
        assert task.target == "10.0.0.1"
        assert task.parameters["ports"] == [80, 443, 22]
        assert task.timeout_seconds == 600
        assert isinstance(task.task_id, UUID)

    def test_task_with_hotl_requirement(self):
        """Test task that requires human approval."""
        task = TaskAssignMessage(
            task_type="exploit_launch",
            target="192.168.1.100",
            parameters={"exploit": "CVE-2024-1234"},
            requires_hotl=True,
        )

        assert task.requires_hotl is True


class TestTaskResultMessage:
    """Test suite for TaskResultMessage payload schema."""

    def test_successful_task_result(self):
        """Test successful task result message."""
        task_id = uuid4()
        result = TaskResultMessage(
            task_id=task_id,
            success=True,
            result_data={"open_ports": [80, 443]},
            execution_time_seconds=12.5,
            confidence_score=0.95,
        )

        assert result.task_id == task_id
        assert result.success is True
        assert result.result_data["open_ports"] == [80, 443]
        assert result.execution_time_seconds == 12.5
        assert result.confidence_score == 0.95
        assert result.error_message is None

    def test_failed_task_result(self):
        """Test failed task result message."""
        task_id = uuid4()
        result = TaskResultMessage(
            task_id=task_id,
            success=False,
            result_data={},
            execution_time_seconds=5.0,
            error_message="Target unreachable",
        )

        assert result.success is False
        assert result.error_message == "Target unreachable"


class TestStatusUpdateMessage:
    """Test suite for StatusUpdateMessage payload schema."""

    def test_status_update_creation(self):
        """Test status update message creation."""
        task_id = uuid4()
        status = StatusUpdateMessage(
            task_id=task_id,
            progress_percent=45.0,
            current_step="Scanning ports 1000-2000",
            estimated_completion_seconds=120,
        )

        assert status.task_id == task_id
        assert status.progress_percent == 45.0
        assert "Scanning" in status.current_step


class TestErrorMessage:
    """Test suite for ErrorMessage payload schema."""

    def test_error_message_creation(self):
        """Test error message creation."""
        error = ErrorMessage(
            error_code="CONN_TIMEOUT",
            error_message="Connection to target timed out",
            task_id=uuid4(),
            recoverable=True,
        )

        assert error.error_code == "CONN_TIMEOUT"
        assert "timed out" in error.error_message
        assert error.recoverable is True


class TestHOTLMessages:
    """Test suite for Human-on-the-Loop message schemas."""

    def test_hotl_request_creation(self):
        """Test HOTL request message creation."""
        request = HOTLRequestMessage(
            action_type="exploit_launch",
            target="192.168.1.50",
            risk_level="high",
            justification="CVE-2024-5678 detected, exploit available",
            proposed_command="python exploit.py --target 192.168.1.50",
        )

        assert request.action_type == "exploit_launch"
        assert request.risk_level == "high"
        assert "CVE-2024-5678" in request.justification

    def test_hotl_response_approved(self):
        """Test HOTL approval response."""
        request_id = uuid4()
        response = HOTLResponseMessage(
            request_id=request_id,
            approved=True,
            operator_notes="Approved by lead pentester",
        )

        assert response.approved is True
        assert response.request_id == request_id

    def test_hotl_response_rejected(self):
        """Test HOTL rejection response."""
        request_id = uuid4()
        response = HOTLResponseMessage(
            request_id=request_id,
            approved=False,
            operator_notes="Too risky during business hours",
        )

        assert response.approved is False
        assert "risky" in response.operator_notes


class TestMessageTypeEnum:
    """Test MessageType enumeration."""

    def test_all_message_types_defined(self):
        """Ensure all expected message types are defined."""
        expected_types = {
            "task_assign",
            "task_result",
            "status_update",
            "error",
            "heartbeat",
            "shutdown",
            "hotl_request",
            "hotl_response",
        }

        defined_types = {mt.value for mt in MessageType}
        assert expected_types == defined_types


class TestAgentTypeEnum:
    """Test AgentType enumeration."""

    def test_all_agent_types_defined(self):
        """Ensure all expected agent types are defined."""
        expected_agents = {
            "orchestrator",
            "reconnaissance",
            "exploitation",
            "post_exploitation",
            "analysis",
        }

        defined_agents = {at.value for at in AgentType}
        assert expected_agents == defined_agents
