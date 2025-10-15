"""
Human-on-the-Loop Decision System.

Critical actions require human approval before execution.
Implements audit logging and decision tracking.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions requiring HOTL approval."""
    EXECUTE_EXPLOIT = "execute_exploit"
    LATERAL_MOVEMENT = "lateral_movement"
    DATA_EXFILTRATION = "data_exfiltration"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CREDENTIAL_DUMPING = "credential_dumping"


class ApprovalStatus(Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class Approval:
    """Human approval decision."""
    
    approved: bool
    status: ApprovalStatus
    operator: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalRequest:
    """Request for human approval."""
    
    id: str
    action: ActionType
    context: Dict[str, Any]
    risk_level: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approval: Optional[Approval] = None


class HOTLDecisionSystem:
    """
    Human-on-the-Loop decision checkpoints.
    Critical actions require human approval.
    """
    
    CRITICAL_ACTIONS = [
        ActionType.EXECUTE_EXPLOIT,
        ActionType.LATERAL_MOVEMENT,
        ActionType.DATA_EXFILTRATION,
        ActionType.PERSISTENCE,
        ActionType.PRIVILEGE_ESCALATION,
        ActionType.CREDENTIAL_DUMPING
    ]
    
    def __init__(self, auto_approve_test: bool = False) -> None:
        """
        Initialize HOTL system.
        
        Args:
            auto_approve_test: Auto-approve in test mode (DANGEROUS in production)
        """
        self.logger = logging.getLogger(__name__)
        self.audit_log: List[Dict[str, Any]] = []
        self.auto_approve_test = auto_approve_test
        self.pending_requests: Dict[str, ApprovalRequest] = {}
    
    def is_critical_action(self, action: ActionType) -> bool:
        """
        Check if action requires approval.
        
        Args:
            action: Action type to check
            
        Returns:
            True if action is critical
        """
        return action in self.CRITICAL_ACTIONS
    
    async def request_approval(
        self,
        action: ActionType,
        context: Dict[str, Any],
        risk_level: str = "medium"
    ) -> ApprovalRequest:
        """
        Request human approval for critical action.
        
        Args:
            action: Action requiring approval
            context: Action context and details
            risk_level: Risk assessment (low/medium/high/critical)
            
        Returns:
            Approval request (may be pending)
        """
        if not self.is_critical_action(action):
            # Auto-approve non-critical actions
            approval = Approval(
                approved=True,
                status=ApprovalStatus.APPROVED,
                operator="system",
                reason="Non-critical action"
            )
            request = ApprovalRequest(
                id=f"req_{uuid.uuid4().hex[:12]}",
                action=action,
                context=context,
                risk_level=risk_level,
                status=ApprovalStatus.APPROVED,
                approval=approval
            )
            self._log_decision(request, approval)
            return request
        
        # Create approval request with unique ID
        request = ApprovalRequest(
            id=f"req_{uuid.uuid4().hex[:12]}",
            action=action,
            context=context,
            risk_level=risk_level
        )
        
        # Log approval request
        self.audit_log.append({
            "request_id": request.id,
            "action": action.value,
            "context": context,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        })
        
        self.logger.warning(
            f"HOTL approval required for: {action.value} "
            f"(risk: {risk_level})"
        )
        
        # Store pending request
        self.pending_requests[request.id] = request
        
        # Auto-approve in test mode (ONLY for testing)
        if self.auto_approve_test:
            approval = Approval(
                approved=True,
                status=ApprovalStatus.APPROVED,
                operator="test_operator",
                reason="Test mode auto-approval"
            )
            request.status = ApprovalStatus.APPROVED
            request.approval = approval
            self._log_decision(request, approval)
        
        return request
    
    async def process_approval(
        self,
        request_id: str,
        approved: bool,
        operator: str,
        reason: Optional[str] = None
    ) -> Approval:
        """
        Process human approval decision.
        
        Args:
            request_id: Request ID
            approved: Approval decision
            operator: Human operator identifier
            reason: Decision reason
            
        Returns:
            Approval decision
        """
        request = self.pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        approval = Approval(
            approved=approved,
            status=ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED,
            operator=operator,
            reason=reason
        )
        
        request.status = approval.status
        request.approval = approval
        
        self._log_decision(request, approval)
        
        # Remove from pending
        del self.pending_requests[request_id]
        
        return approval
    
    def _log_decision(
        self,
        request: ApprovalRequest,
        approval: Approval
    ) -> None:
        """
        Log approval decision to audit log.
        
        Args:
            request: Approval request
            approval: Approval decision
        """
        self.audit_log.append({
            "request_id": request.id,
            "action": request.action.value,
            "context": request.context,
            "risk_level": request.risk_level,
            "decision": approval.approved,
            "operator": approval.operator,
            "reason": approval.reason,
            "timestamp": approval.timestamp.isoformat()
        })
    
    def get_audit_log(
        self,
        action_type: Optional[ActionType] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit log entries.
        
        Args:
            action_type: Filter by action type
            since: Filter by timestamp
            
        Returns:
            Filtered audit log entries
        """
        log = self.audit_log
        
        if action_type:
            log = [
                entry for entry in log
                if entry.get("action") == action_type.value
            ]
        
        if since:
            log = [
                entry for entry in log
                if datetime.fromisoformat(entry["timestamp"]) >= since
            ]
        
        return log
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """
        Get all pending approval requests.
        
        Returns:
            List of pending requests
        """
        return list(self.pending_requests.values())
