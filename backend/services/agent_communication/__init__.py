"""Agent Communication Protocol (ACP) implementation.

This module provides the foundational infrastructure for inter-agent
communication in the MAXIMUS offensive security toolkit. It implements
a message-passing architecture using RabbitMQ for reliable, asynchronous
communication between specialized agents.

Architectural Philosophy:
- Loose coupling between agents via message queues
- Async-first design for high throughput
- Type-safe message schemas via Pydantic
- Fault-tolerant with automatic retries

Components:
- MessageBroker: RabbitMQ wrapper for queue management
- ACPMessage: Type-safe message schemas
- MessageRouter: Routing logic for agent communication
"""
from .broker import MessageBroker
from .message import ACPMessage, MessageType
from .router import MessageRouter

__all__ = ["MessageBroker", "ACPMessage", "MessageType", "MessageRouter"]
__version__ = "1.0.0"
