"""
HITL Module - Human-in-the-Loop interface for APV review and decision-making.

Components:
- models: Pydantic models for review context, decisions, records
- decision_engine: Decision processing and GitHub PR actions
- api: FastAPI application with REST and WebSocket endpoints

Features:
- Complete review context (CVE, patch, scores, wargame results)
- Human decision submission (approve/reject/modify/escalate)
- GitHub PR actions (merge, close, request changes)
- Real-time WebSocket updates
- Decision audit trail
- Dashboard statistics
"""

from .models import (
    ReviewContext,
    DecisionRequest,
    DecisionRecord,
    ReviewStats,
    ReviewListItem,
    ReviewAction,
    WebSocketMessage,
)

from .decision_engine import DecisionEngine

from .api import app, broadcast_event

__all__ = [
    # Models
    "ReviewContext",
    "DecisionRequest",
    "DecisionRecord",
    "ReviewStats",
    "ReviewListItem",
    "ReviewAction",
    "WebSocketMessage",
    # Decision Engine
    "DecisionEngine",
    # API
    "app",
    "broadcast_event",
]
