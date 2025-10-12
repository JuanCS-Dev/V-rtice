"""Tests for MessageRouter routing logic."""
import pytest

from agent_communication.message import (
    ACPMessage,
    AgentType,
    MessageType,
    TaskPriority,
)
from agent_communication.router import MessageRouter, MessageTransformer


class TestMessageRouterValidation:
    """Test routing validation logic."""

    def test_router_strict_mode_default(self):
        """Test router defaults to strict mode."""
        router = MessageRouter()
        assert router.strict_mode is True

    def test_valid_orchestrator_to_agent_task_assign(self):
        """Test valid routing: Orchestrator assigns task to agents."""
        router = MessageRouter()

        # Test all valid agent targets for TASK_ASSIGN
        for agent in [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ]:
            is_valid = router.validate_route(
                AgentType.ORCHESTRATOR, MessageType.TASK_ASSIGN, agent
            )
            assert is_valid is True

    def test_valid_agent_to_orchestrator_result(self):
        """Test valid routing: Agents send results back to Orchestrator."""
        router = MessageRouter()

        for agent in [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ]:
            is_valid = router.validate_route(
                agent, MessageType.TASK_RESULT, AgentType.ORCHESTRATOR
            )
            assert is_valid is True

    def test_invalid_agent_to_agent_direct(self):
        """Test invalid routing: Agents cannot communicate directly."""
        router = MessageRouter()

        is_valid = router.validate_route(
            AgentType.RECONNAISSANCE,
            MessageType.TASK_ASSIGN,
            AgentType.EXPLOITATION,
        )
        assert is_valid is False

    def test_invalid_agent_sending_shutdown(self):
        """Test invalid routing: Only Orchestrator can send SHUTDOWN."""
        router = MessageRouter()

        is_valid = router.validate_route(
            AgentType.RECONNAISSANCE,
            MessageType.SHUTDOWN,
            AgentType.EXPLOITATION,
        )
        assert is_valid is False

    def test_valid_hotl_request_to_orchestrator(self):
        """Test valid HOTL request routing."""
        router = MessageRouter()

        for agent in [AgentType.EXPLOITATION, AgentType.POST_EXPLOITATION]:
            is_valid = router.validate_route(
                agent, MessageType.HOTL_REQUEST, AgentType.ORCHESTRATOR
            )
            assert is_valid is True

    def test_valid_hotl_response_from_orchestrator(self):
        """Test valid HOTL response routing."""
        router = MessageRouter()

        for agent in [AgentType.EXPLOITATION, AgentType.POST_EXPLOITATION]:
            is_valid = router.validate_route(
                AgentType.ORCHESTRATOR, MessageType.HOTL_RESPONSE, agent
            )
            assert is_valid is True

    def test_heartbeat_routing(self):
        """Test heartbeat messages can be sent to Orchestrator."""
        router = MessageRouter()

        for agent in [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ]:
            is_valid = router.validate_route(
                agent, MessageType.HEARTBEAT, AgentType.ORCHESTRATOR
            )
            assert is_valid is True


class TestMessageRouterStrictMode:
    """Test strict mode behavior."""

    def test_strict_mode_raises_on_invalid_route(self):
        """Test strict mode raises ValueError on invalid routes."""
        router = MessageRouter(strict_mode=True)

        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.RECONNAISSANCE,  # Invalid sender for TASK_ASSIGN
            recipient=AgentType.EXPLOITATION,
            payload={},
        )

        with pytest.raises(ValueError, match="Invalid route"):
            router.route_message(msg)

    def test_non_strict_mode_logs_warning(self):
        """Test non-strict mode returns None but doesn't raise."""
        router = MessageRouter(strict_mode=False)

        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.RECONNAISSANCE,
            recipient=AgentType.EXPLOITATION,
            payload={},
        )

        result = router.route_message(msg)
        assert result is None  # Invalid route returns None in non-strict


class TestMessageRouterRouting:
    """Test actual message routing logic."""

    def test_route_valid_message(self):
        """Test routing a valid message returns the message."""
        router = MessageRouter()

        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={"task": "scan"},
        )

        routed = router.route_message(msg)
        assert routed is not None
        assert routed.message_id == msg.message_id
        assert routed.payload == msg.payload

    def test_get_response_recipient(self):
        """Test determining response recipient."""
        original_msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={},
        )

        response_recipient = MessageRouter.get_response_recipient(original_msg)
        assert response_recipient == AgentType.ORCHESTRATOR


class TestMessageTransformer:
    """Test message transformation utilities."""

    def test_redact_password_field(self):
        """Test sensitive password field is redacted."""
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.EXPLOITATION,
            payload={"username": "admin", "password": "secret123"},
        )

        redacted = MessageTransformer.redact_sensitive_fields(msg)
        assert redacted.payload["username"] == "admin"  # Not sensitive
        assert redacted.payload["password"] == "***REDACTED***"

    def test_redact_multiple_sensitive_fields(self):
        """Test multiple sensitive fields are redacted."""
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={
                "api_key": "sk-1234567890",
                "token": "jwt-token-here",
                "normal_field": "safe_data",
            },
        )

        redacted = MessageTransformer.redact_sensitive_fields(msg)
        assert redacted.payload["api_key"] == "***REDACTED***"
        assert redacted.payload["token"] == "***REDACTED***"
        assert redacted.payload["normal_field"] == "safe_data"

    def test_redact_preserves_original_message(self):
        """Test redaction creates new message, doesn't modify original."""
        original_payload = {"password": "secret123"}
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.EXPLOITATION,
            payload=original_payload.copy(),
        )

        redacted = MessageTransformer.redact_sensitive_fields(msg)

        # Original should be unchanged
        assert msg.payload["password"] == "secret123"
        # Redacted should be modified
        assert redacted.payload["password"] == "***REDACTED***"


class TestRouterEdgeCases:
    """Test edge cases and error conditions."""

    def test_unknown_message_type_routing(self):
        """Test routing with message type not in routing table."""
        router = MessageRouter(strict_mode=False)

        # Manually create message with valid enum but no routing rule
        # Analysis agent cannot send SHUTDOWN messages
        is_valid = router.validate_route(
            AgentType.ANALYSIS, MessageType.SHUTDOWN, AgentType.ORCHESTRATOR
        )

        # Should return False (invalid route)
        assert is_valid is False

    def test_status_update_routing(self):
        """Test status update messages route correctly."""
        router = MessageRouter()

        for agent in [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ]:
            is_valid = router.validate_route(
                agent, MessageType.STATUS_UPDATE, AgentType.ORCHESTRATOR
            )
            assert is_valid is True

    def test_error_message_routing(self):
        """Test error messages route to Orchestrator."""
        router = MessageRouter()

        for agent in [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ]:
            is_valid = router.validate_route(
                agent, MessageType.ERROR, AgentType.ORCHESTRATOR
            )
            assert is_valid is True
