"""Message routing logic for Agent Communication Protocol.

Implements intelligent routing rules and message transformation between agents.
"""
import logging
from typing import Optional

from .message import ACPMessage, AgentType, MessageType

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes messages between agents based on protocol rules.

    The router implements the business logic of agent communication:
    - Determines valid sender-recipient combinations
    - Enforces message type constraints
    - Applies transformations/validations before routing
    - Logs audit trail of all routed messages

    This is the enforcer of the Agent Communication Protocol specification.
    """

    # Valid routing table: (sender, message_type) -> allowed recipients
    ROUTING_TABLE = {
        # Orchestrator can send to all agents
        (AgentType.ORCHESTRATOR, MessageType.TASK_ASSIGN): [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ],
        (AgentType.ORCHESTRATOR, MessageType.SHUTDOWN): [
            AgentType.RECONNAISSANCE,
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
            AgentType.ANALYSIS,
        ],
        # Agents can send results back to Orchestrator
        (AgentType.RECONNAISSANCE, MessageType.TASK_RESULT): [AgentType.ORCHESTRATOR],
        (AgentType.EXPLOITATION, MessageType.TASK_RESULT): [AgentType.ORCHESTRATOR],
        (AgentType.POST_EXPLOITATION, MessageType.TASK_RESULT): [
            AgentType.ORCHESTRATOR
        ],
        (AgentType.ANALYSIS, MessageType.TASK_RESULT): [AgentType.ORCHESTRATOR],
        # Status updates to Orchestrator
        (AgentType.RECONNAISSANCE, MessageType.STATUS_UPDATE): [
            AgentType.ORCHESTRATOR
        ],
        (AgentType.EXPLOITATION, MessageType.STATUS_UPDATE): [AgentType.ORCHESTRATOR],
        (AgentType.POST_EXPLOITATION, MessageType.STATUS_UPDATE): [
            AgentType.ORCHESTRATOR
        ],
        (AgentType.ANALYSIS, MessageType.STATUS_UPDATE): [AgentType.ORCHESTRATOR],
        # Error messages to Orchestrator
        (AgentType.RECONNAISSANCE, MessageType.ERROR): [AgentType.ORCHESTRATOR],
        (AgentType.EXPLOITATION, MessageType.ERROR): [AgentType.ORCHESTRATOR],
        (AgentType.POST_EXPLOITATION, MessageType.ERROR): [AgentType.ORCHESTRATOR],
        (AgentType.ANALYSIS, MessageType.ERROR): [AgentType.ORCHESTRATOR],
        # HOTL requests to Orchestrator (which forwards to human)
        (AgentType.EXPLOITATION, MessageType.HOTL_REQUEST): [AgentType.ORCHESTRATOR],
        (AgentType.POST_EXPLOITATION, MessageType.HOTL_REQUEST): [
            AgentType.ORCHESTRATOR
        ],
        # HOTL responses back to requesting agent
        (AgentType.ORCHESTRATOR, MessageType.HOTL_RESPONSE): [
            AgentType.EXPLOITATION,
            AgentType.POST_EXPLOITATION,
        ],
        # Heartbeats can go anywhere
        (AgentType.RECONNAISSANCE, MessageType.HEARTBEAT): [AgentType.ORCHESTRATOR],
        (AgentType.EXPLOITATION, MessageType.HEARTBEAT): [AgentType.ORCHESTRATOR],
        (AgentType.POST_EXPLOITATION, MessageType.HEARTBEAT): [
            AgentType.ORCHESTRATOR
        ],
        (AgentType.ANALYSIS, MessageType.HEARTBEAT): [AgentType.ORCHESTRATOR],
    }

    def __init__(self, strict_mode: bool = True):
        """Initialize router.

        Args:
            strict_mode: If True, reject invalid routes. If False, log warning only.
        """
        self.strict_mode = strict_mode

    def validate_route(
        self, sender: AgentType, message_type: MessageType, recipient: AgentType
    ) -> bool:
        """Check if a route is valid per protocol rules.

        Args:
            sender: Sending agent type
            message_type: Type of message
            recipient: Recipient agent type

        Returns:
            True if route is valid, False otherwise
        """
        allowed_recipients = self.ROUTING_TABLE.get((sender, message_type))
        if allowed_recipients is None:
            logger.warning(
                f"No routing rule for ({sender.value}, {message_type.value})"
            )
            return False  # Invalid if no routing rule exists

        return recipient in allowed_recipients

    def route_message(self, message: ACPMessage) -> Optional[ACPMessage]:
        """Validate and potentially transform message before routing.

        Args:
            message: Message to route

        Returns:
            Validated/transformed message, or None if invalid

        Raises:
            ValueError: If route is invalid in strict mode
        """
        is_valid = self.validate_route(
            message.sender, message.message_type, message.recipient
        )

        if not is_valid:
            error_msg = (
                f"Invalid route: {message.sender.value} cannot send "
                f"{message.message_type.value} to {message.recipient.value}"
            )
            if self.strict_mode:
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)
                return None

        # Log audit trail
        logger.info(
            f"Routing {message.message_type.value}: "
            f"{message.sender.value} → {message.recipient.value} "
            f"(msg_id={message.message_id})"
        )

        return message

    @staticmethod
    def get_response_recipient(
        original_message: ACPMessage,
    ) -> AgentType:
        """Determine recipient for a response to an original message.

        Args:
            original_message: The message being responded to

        Returns:
            Agent type that should receive the response
        """
        # Most responses go back to sender
        return original_message.sender


class MessageTransformer:
    """Transforms messages for protocol compatibility and optimization.

    Handles:
    - Message compression for large payloads
    - Sensitive data redaction for logging
    - Protocol version migration
    """

    @staticmethod
    def redact_sensitive_fields(message: ACPMessage) -> ACPMessage:
        """Remove sensitive data from message for logging/auditing.

        Args:
            message: Message to redact

        Returns:
            New message with sensitive fields redacted
        """
        redacted_payload = message.payload.copy()

        # Redact known sensitive keys
        sensitive_keys = [
            "password",
            "token",
            "api_key",
            "secret",
            "credential",
            "private_key",
        ]

        for key in sensitive_keys:
            if key in redacted_payload:
                redacted_payload[key] = "***REDACTED***"

        return message.model_copy(update={"payload": redacted_payload})
