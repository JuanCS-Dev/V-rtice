"""
HITL (Human-in-the-Loop) Interface

⚠️ POC IMPLEMENTATION FOR GRPC BRIDGE VALIDATION
This is a minimal implementation for Week 9-10 Migration Bridge testing.
Production implementation will integrate with real session management and operator tracking.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from .governance_engine import DecisionStatus, GovernanceEngine


class HITLInterface:
    """
    Human-in-the-Loop interface for operator interaction with governance decisions.

    ⚠️ POC IMPLEMENTATION - For gRPC bridge validation only.
    Production version will integrate with authentication and audit systems.
    """

    def __init__(self, governance_engine: GovernanceEngine):
        """
        Initialize HITL interface.

        Args:
            governance_engine: The governance engine managing decisions
        """
        self.governance_engine = governance_engine
        self.sessions: Dict[str, Dict] = {}
        self.operator_stats: Dict[str, Dict] = {}

    def create_session(self, operator_id: str) -> str:
        """
        Create a new operator session.

        Args:
            operator_id: Unique identifier for the operator

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid4())

        self.sessions[session_id] = {
            "operator_id": operator_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "decisions_processed": 0,
            "decisions_approved": 0,
            "decisions_rejected": 0,
            "decisions_escalated": 0,
        }

        # Initialize operator stats if not exists
        if operator_id not in self.operator_stats:
            self.operator_stats[operator_id] = {
                "total_decisions": 0,
                "approved": 0,
                "rejected": 0,
                "escalated": 0,
                "total_response_time": 0.0,
                "session_start": datetime.utcnow(),
            }

        return session_id

    def close_session(self, session_id: str) -> bool:
        """
        Close an operator session.

        Args:
            session_id: Session to close

        Returns:
            success: True if session was closed
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def approve_decision(
        self,
        decision_id: str,
        operator_id: str,
        comment: str = "",
        reasoning: str = ""
    ) -> bool:
        """
        Approve a governance decision.

        Args:
            decision_id: Decision to approve
            operator_id: Operator making the decision
            comment: Optional comment
            reasoning: Reasoning for approval

        Returns:
            success: True if decision was approved
        """
        success = self.governance_engine.update_decision_status(
            decision_id=decision_id,
            status=DecisionStatus.APPROVED,
            operator_id=operator_id,
            comment=comment,
            reasoning=reasoning
        )

        if success:
            # Update operator stats
            if operator_id in self.operator_stats:
                stats = self.operator_stats[operator_id]
                stats["total_decisions"] += 1
                stats["approved"] += 1

                # Calculate response time
                decision = self.governance_engine.get_decision(decision_id)
                if decision and decision.resolved_at:
                    response_time = (decision.resolved_at - decision.created_at).total_seconds()
                    stats["total_response_time"] += response_time

        return success

    def reject_decision(
        self,
        decision_id: str,
        operator_id: str,
        comment: str = "",
        reasoning: str = ""
    ) -> bool:
        """
        Reject a governance decision.

        Args:
            decision_id: Decision to reject
            operator_id: Operator making the decision
            comment: Optional comment
            reasoning: Reasoning for rejection

        Returns:
            success: True if decision was rejected
        """
        success = self.governance_engine.update_decision_status(
            decision_id=decision_id,
            status=DecisionStatus.REJECTED,
            operator_id=operator_id,
            comment=comment,
            reasoning=reasoning
        )

        if success:
            # Update operator stats
            if operator_id in self.operator_stats:
                stats = self.operator_stats[operator_id]
                stats["total_decisions"] += 1
                stats["rejected"] += 1

                # Calculate response time
                decision = self.governance_engine.get_decision(decision_id)
                if decision and decision.resolved_at:
                    response_time = (decision.resolved_at - decision.created_at).total_seconds()
                    stats["total_response_time"] += response_time

        return success

    def escalate_decision(
        self,
        decision_id: str,
        operator_id: str,
        reason: str,
        escalation_target: str
    ) -> bool:
        """
        Escalate a decision to higher authority.

        Args:
            decision_id: Decision to escalate
            operator_id: Operator escalating
            reason: Reason for escalation
            escalation_target: Target authority (e.g., "ERB", "Senior Operator")

        Returns:
            success: True if decision was escalated
        """
        success = self.governance_engine.update_decision_status(
            decision_id=decision_id,
            status=DecisionStatus.ESCALATED,
            operator_id=operator_id,
            comment=f"Escalated to: {escalation_target}",
            reasoning=reason
        )

        if success:
            # Update operator stats
            if operator_id in self.operator_stats:
                stats = self.operator_stats[operator_id]
                stats["total_decisions"] += 1
                stats["escalated"] += 1

                # Calculate response time
                decision = self.governance_engine.get_decision(decision_id)
                if decision and decision.resolved_at:
                    response_time = (decision.resolved_at - decision.created_at).total_seconds()
                    stats["total_response_time"] += response_time

        return success

    def get_operator_stats(self, operator_id: str) -> Dict:
        """
        Get statistics for an operator.

        Args:
            operator_id: Operator to get stats for

        Returns:
            stats: Dictionary with operator statistics
        """
        if operator_id not in self.operator_stats:
            return {
                "total_decisions": 0,
                "approved": 0,
                "rejected": 0,
                "escalated": 0,
                "avg_response_time": 0.0,
                "session_start": None,
            }

        stats = self.operator_stats[operator_id]

        # Calculate average response time
        avg_response_time = 0.0
        if stats["total_decisions"] > 0:
            avg_response_time = stats["total_response_time"] / stats["total_decisions"]

        return {
            "total_decisions": stats["total_decisions"],
            "approved": stats["approved"],
            "rejected": stats["rejected"],
            "escalated": stats["escalated"],
            "avg_response_time": avg_response_time,
            "session_start": stats["session_start"],
        }

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a session.

        Args:
            session_id: Session to get info for

        Returns:
            session_info: Dictionary with session information, or None if not found
        """
        return self.sessions.get(session_id)
