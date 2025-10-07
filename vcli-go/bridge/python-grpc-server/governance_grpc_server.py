#!/usr/bin/env python3
"""
gRPC Server Bridge for Governance Service

This server wraps the existing Python Governance HTTP service
and exposes it via gRPC for Go clients.

Follows REGRA DE OURO: No mocks, production-ready code only.
"""

import asyncio
import logging
from concurrent import futures
from datetime import datetime
from typing import Dict, List, Optional

import grpc
from google.protobuf.timestamp_pb2 import Timestamp

# Import generated gRPC code
import governance_pb2
import governance_pb2_grpc

# Import existing Python Governance service
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../backend/services/maximus_core_service"))

from governance.governance_engine import GovernanceEngine, Decision, DecisionStatus
from governance.hitl_interface import HITLInterface


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GovernanceServicer:
    """
    gRPC Servicer that wraps the existing Python Governance service.

    This provides a gRPC interface to the HITL (Human-in-the-Loop)
    governance system, allowing Go clients to interact with it.
    """

    def __init__(self, governance_engine: GovernanceEngine, hitl_interface: HITLInterface):
        """
        Initialize the gRPC servicer.

        Args:
            governance_engine: Existing Python governance engine
            hitl_interface: Existing HITL interface
        """
        self.governance_engine = governance_engine
        self.hitl_interface = hitl_interface
        self.sessions: Dict[str, Dict] = {}
        logger.info("GovernanceServicer initialized")

    def HealthCheck(self, request, context):
        """Health check endpoint."""
        response = governance_pb2.HealthCheckResponse(
            healthy=True,
            status="operational",
            uptime_seconds=int(self.governance_engine.get_uptime())
        )
        logger.debug("Health check: OK")
        return response

    def CreateSession(self, request, context):
        """Create a new operator session."""
        session_id = self.hitl_interface.create_session(request.operator_id)

        timestamp = Timestamp()
        timestamp.GetCurrentTime()

        response = governance_pb2.CreateSessionResponse(
            session_id=session_id,
            created_at=timestamp
        )

        self.sessions[session_id] = {
            "operator_id": request.operator_id,
            "created_at": datetime.utcnow(),
            "decisions_processed": 0
        }

        logger.info(f"Session created: {session_id} for operator {request.operator_id}")
        return response

    def CloseSession(self, request, context):
        """Close an operator session."""
        session_id = request.session_id

        if session_id in self.sessions:
            del self.sessions[session_id]
            success = True
            logger.info(f"Session closed: {session_id}")
        else:
            success = False
            logger.warning(f"Session not found: {session_id}")

        response = governance_pb2.CloseSessionResponse(success=success)
        return response

    def ListPendingDecisions(self, request, context):
        """List pending decisions requiring HITL review."""
        # Get pending decisions from governance engine
        decisions = self.governance_engine.get_pending_decisions(
            limit=request.limit if request.limit > 0 else 50,
            status=request.status if request.status else "PENDING",
            priority=request.priority if request.priority else None
        )

        # Convert to protobuf
        pb_decisions = [self._decision_to_proto(d) for d in decisions]

        response = governance_pb2.ListPendingDecisionsResponse(
            decisions=pb_decisions,
            total_count=len(decisions)
        )

        logger.debug(f"Listed {len(decisions)} pending decisions")
        return response

    def GetDecision(self, request, context):
        """Get a specific decision by ID."""
        decision = self.governance_engine.get_decision(request.decision_id)

        if decision is None:
            context.abort(grpc.StatusCode.NOT_FOUND, f"Decision not found: {request.decision_id}")

        response = governance_pb2.GetDecisionResponse(
            decision=self._decision_to_proto(decision)
        )
        return response

    def ApproveDecision(self, request, context):
        """Approve a decision."""
        session_id = request.session_id
        decision_id = request.decision_id

        if session_id not in self.sessions:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")

        operator_id = self.sessions[session_id]["operator_id"]

        # Process approval through HITL interface
        success = self.hitl_interface.approve_decision(
            decision_id=decision_id,
            operator_id=operator_id,
            comment=request.comment,
            reasoning=request.reasoning
        )

        timestamp = Timestamp()
        timestamp.GetCurrentTime()

        response = governance_pb2.ApproveDecisionResponse(
            success=success,
            message="Decision approved" if success else "Approval failed",
            processed_at=timestamp
        )

        if success:
            self.sessions[session_id]["decisions_processed"] += 1
            logger.info(f"Decision approved: {decision_id} by {operator_id}")

        return response

    def RejectDecision(self, request, context):
        """Reject a decision."""
        session_id = request.session_id
        decision_id = request.decision_id

        if session_id not in self.sessions:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")

        operator_id = self.sessions[session_id]["operator_id"]

        # Process rejection through HITL interface
        success = self.hitl_interface.reject_decision(
            decision_id=decision_id,
            operator_id=operator_id,
            comment=request.comment,
            reasoning=request.reasoning
        )

        timestamp = Timestamp()
        timestamp.GetCurrentTime()

        response = governance_pb2.RejectDecisionResponse(
            success=success,
            message="Decision rejected" if success else "Rejection failed",
            processed_at=timestamp
        )

        if success:
            self.sessions[session_id]["decisions_processed"] += 1
            logger.info(f"Decision rejected: {decision_id} by {operator_id}")

        return response

    def EscalateDecision(self, request, context):
        """Escalate a decision to higher authority."""
        session_id = request.session_id
        decision_id = request.decision_id

        if session_id not in self.sessions:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")

        operator_id = self.sessions[session_id]["operator_id"]

        # Process escalation through HITL interface
        success = self.hitl_interface.escalate_decision(
            decision_id=decision_id,
            operator_id=operator_id,
            reason=request.reason,
            escalation_target=request.escalation_target
        )

        timestamp = Timestamp()
        timestamp.GetCurrentTime()

        response = governance_pb2.EscalateDecisionResponse(
            success=success,
            message="Decision escalated" if success else "Escalation failed",
            processed_at=timestamp
        )

        if success:
            self.sessions[session_id]["decisions_processed"] += 1
            logger.info(f"Decision escalated: {decision_id} by {operator_id}")

        return response

    def GetMetrics(self, request, context):
        """Get overall metrics."""
        metrics = self.governance_engine.get_metrics()

        response = governance_pb2.GetMetricsResponse(
            metrics=self._metrics_to_proto(metrics)
        )
        return response

    def GetSessionStats(self, request, context):
        """Get session-specific statistics."""
        operator_id = request.operator_id
        stats = self.hitl_interface.get_operator_stats(operator_id)

        session_start = Timestamp()
        if stats.get("session_start"):
            session_start.FromDatetime(stats["session_start"])

        response = governance_pb2.GetSessionStatsResponse(
            total_decisions=stats.get("total_decisions", 0),
            approved=stats.get("approved", 0),
            rejected=stats.get("rejected", 0),
            escalated=stats.get("escalated", 0),
            avg_response_time_seconds=stats.get("avg_response_time", 0.0),
            session_start=session_start
        )
        return response

    def StreamDecisions(self, request, context):
        """Stream decision events in real-time (Server-side streaming)."""
        session_id = request.session_id

        if session_id not in self.sessions:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")

        logger.info(f"Starting decision stream for session {session_id}")

        # Subscribe to decision events from governance engine
        for decision_event in self.governance_engine.subscribe_decision_events():
            timestamp = Timestamp()
            timestamp.GetCurrentTime()

            event = governance_pb2.DecisionEvent(
                type=self._map_event_type(decision_event["type"]),
                decision=self._decision_to_proto(decision_event["decision"]),
                timestamp=timestamp
            )

            yield event

    def StreamEvents(self, request, context):
        """Stream governance events in real-time (Server-side streaming)."""
        session_id = request.session_id

        if session_id not in self.sessions:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid session")

        logger.info(f"Starting event stream for session {session_id}")

        # Subscribe to governance events
        for gov_event in self.governance_engine.subscribe_events():
            timestamp = Timestamp()
            timestamp.GetCurrentTime()

            event = governance_pb2.GovernanceEvent(
                type=self._map_governance_event_type(gov_event["type"]),
                message=gov_event.get("message", ""),
                timestamp=timestamp
            )

            if gov_event.get("metrics"):
                event.metrics.CopyFrom(self._metrics_to_proto(gov_event["metrics"]))

            yield event

    # Helper methods

    def _decision_to_proto(self, decision: Decision):
        """Convert Python Decision to protobuf Decision."""
        pb_decision = governance_pb2.Decision()
        pb_decision.decision_id = decision.decision_id
        pb_decision.operation_type = decision.operation_type

        # Context
        for key, value in decision.context.items():
            pb_decision.context[key] = str(value)

        # Risk assessment
        pb_decision.risk_assessment.score = decision.risk.score
        pb_decision.risk_assessment.level = decision.risk.level
        pb_decision.risk_assessment.factors.extend(decision.risk.factors)

        # Status and priority
        pb_decision.status = decision.status.value
        pb_decision.priority = decision.priority

        # Timestamps
        created_at = Timestamp()
        created_at.FromDatetime(decision.created_at)
        pb_decision.created_at.CopyFrom(created_at)

        if decision.expires_at:
            expires_at = Timestamp()
            expires_at.FromDatetime(decision.expires_at)
            pb_decision.expires_at.CopyFrom(expires_at)

        pb_decision.sla_seconds = decision.sla_seconds

        return pb_decision

    def _metrics_to_proto(self, metrics: Dict):
        """Convert metrics dict to protobuf DecisionMetrics."""
        pb_metrics = governance_pb2.DecisionMetrics()
        pb_metrics.pending_count = metrics.get("pending_count", 0)
        pb_metrics.total_decisions = metrics.get("total_decisions", 0)
        pb_metrics.approved_count = metrics.get("approved_count", 0)
        pb_metrics.rejected_count = metrics.get("rejected_count", 0)
        pb_metrics.escalated_count = metrics.get("escalated_count", 0)
        pb_metrics.critical_count = metrics.get("critical_count", 0)
        pb_metrics.high_priority_count = metrics.get("high_priority_count", 0)
        pb_metrics.avg_response_time_seconds = metrics.get("avg_response_time", 0.0)
        pb_metrics.approval_rate = metrics.get("approval_rate", 0.0)
        pb_metrics.sla_violations = metrics.get("sla_violations", 0)
        return pb_metrics

    def _map_event_type(self, event_type: str):
        """Map Python event type to protobuf EventType."""
        mapping = {
            "new_decision": governance_pb2.DecisionEvent.NEW_DECISION,
            "decision_updated": governance_pb2.DecisionEvent.DECISION_UPDATED,
            "decision_resolved": governance_pb2.DecisionEvent.DECISION_RESOLVED,
        }
        return mapping.get(event_type, governance_pb2.DecisionEvent.NEW_DECISION)

    def _map_governance_event_type(self, event_type: str):
        """Map Python governance event type to protobuf EventType."""
        mapping = {
            "connection_established": governance_pb2.GovernanceEvent.CONNECTION_ESTABLISHED,
            "connection_lost": governance_pb2.GovernanceEvent.CONNECTION_LOST,
            "metrics_updated": governance_pb2.GovernanceEvent.METRICS_UPDATED,
            "error": governance_pb2.GovernanceEvent.ERROR,
        }
        return mapping.get(event_type, governance_pb2.GovernanceEvent.ERROR)


async def serve(host: str = "0.0.0.0", port: int = 50051):
    """
    Start the gRPC server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    # Initialize existing Python services
    governance_engine = GovernanceEngine()
    hitl_interface = HITLInterface(governance_engine)

    # Create gRPC server
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
        ]
    )

    # Add servicer
    servicer = GovernanceServicer(governance_engine, hitl_interface)
    governance_pb2_grpc.add_GovernanceServiceServicer_to_server(servicer, server)

    # Bind and start
    server.add_insecure_port(f'{host}:{port}')
    await server.start()

    logger.info(f"🚀 gRPC server started on {host}:{port}")
    logger.info("✅ Governance service bridge active")
    logger.info("🔗 Go clients can now connect via gRPC")

    await server.wait_for_termination()


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
