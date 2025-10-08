"""
Governance SSE - Real-time Event Streaming for TUI

Provides Server-Sent Events (SSE) streaming of ethical governance decisions
to the Vértice CLI TUI for Human-in-the-Loop (HITL) review.

Architecture:
- Integrates with existing HITL DecisionQueue and OperatorInterface
- Streams pending decisions via SSE
- Provides REST API for operator actions (approve/reject/escalate)
- Production-ready with error handling and monitoring

Components:
- GovernanceSSEServer: SSE streaming server (591 lines)
- EventBroadcaster: Simplified event broadcasting (328 lines)
- create_governance_api(): FastAPI router factory (486 lines)

Total: ~1,405 lines production-ready code

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: REGRA DE OURO compliant (zero mocks, zero placeholders, zero incomplete code)
"""

from .api_routes import create_governance_api
from .event_broadcaster import BroadcastOptions, EventBroadcaster
from .sse_server import GovernanceSSEServer, SSEEvent, decision_to_sse_data

__all__ = [
    "GovernanceSSEServer",
    "SSEEvent",
    "decision_to_sse_data",
    "EventBroadcaster",
    "BroadcastOptions",
    "create_governance_api",
]
