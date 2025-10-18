"""
Reactive Fabric - Human-in-the-Loop (HITL) Models.

Data models for human authorization workflow and decision tracking.
Critical safety mechanism preventing automated response escalation.

Phase 1 Mandate: ALL actions beyond passive collection require human approval.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ActionLevel(str, Enum):
    """
    Action authorization level aligned with viability analysis risk matrix.
    
    Level 1 (PASSIVE): Observation only - NO human authorization required
    Level 2 (ADAPTIVE): Defensive tuning - RECOMMENDED human review
    Level 3 (DECEPTIVE): Active deception - MANDATORY human authorization
    Level 4 (OFFENSIVE): Counter-attack - PROHIBITED in Phase 1
    
    Phase 1 Constraint: Only Level 1 automated. Levels 2-3 HITL required.
    """
    LEVEL_1_PASSIVE = "level_1_passive"
    LEVEL_2_ADAPTIVE = "level_2_adaptive"
    LEVEL_3_DECEPTIVE = "level_3_deceptive"
    LEVEL_4_OFFENSIVE = "level_4_offensive"


class ActionType(str, Enum):
    """Specific action types requiring authorization."""
    # Level 1 - Passive (auto-approved)
    COLLECT_TELEMETRY = "collect_telemetry"
    LOG_EVENT = "log_event"
    GENERATE_ALERT = "generate_alert"
    
    # Level 2 - Adaptive (recommended HITL)
    UPDATE_FIREWALL_RULE = "update_firewall_rule"
    ADJUST_IDS_SIGNATURE = "adjust_ids_signature"
    MODIFY_ASSET_CONFIG = "modify_asset_config"
    
    # Level 3 - Deceptive (mandatory HITL)
    DEPLOY_DECEPTION_ASSET = "deploy_deception_asset"
    MODIFY_HONEYPOT_RESPONSE = "modify_honeypot_response"
    INJECT_FALSE_DATA = "inject_false_data"
    
    # Level 4 - Offensive (PROHIBITED Phase 1)
    COUNTER_EXPLOIT = "counter_exploit"
    REVERSE_SHELL = "reverse_shell"
    DATA_POISONING = "data_poisoning"


class DecisionStatus(str, Enum):
    """Authorization decision status."""
    PENDING = "pending"              # Awaiting human review
    APPROVED = "approved"            # Action authorized
    REJECTED = "rejected"            # Action denied
    ESCALATED = "escalated"          # Escalated to higher authority
    EXPIRED = "expired"              # Authorization window expired
    AUTO_APPROVED = "auto_approved"  # Level 1 actions only


class DecisionRationale(BaseModel):
    """
    Structured rationale for authorization decision.
    
    Critical for audit trail and learning from human decisions.
    Future ML models may learn from these patterns.
    """
    reasoning: str = Field(..., min_length=1, description="Human decision reasoning")
    risk_assessment: str = Field(..., description="Assessed risk level and factors")
    alternative_considered: Optional[str] = Field(None, description="Alternative actions considered")
    lessons_learned: Optional[str] = Field(None, description="Insights for future decisions")


class AuthorizationRequest(BaseModel):
    """
    Request for human authorization of proposed action.
    
    Core HITL mechanism preventing automation runaway.
    Every Level 2+ action flows through this approval gate.
    
    Design Philosophy:
    - Clear context for decision-maker
    - Explicit risk communication
    - Time-bounded decision window
    - Full audit trail
    
    Safety Property:
    No destructive action executes without human approval.
    Timeout results in conservative default (rejection).
    """
    
    # Core identification
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Action details
    action_level: ActionLevel = Field(...)
    action_type: ActionType = Field(...)
    action_description: str = Field(..., min_length=1, description="What will be done")
    action_target: str = Field(..., description="What system/asset will be affected")
    
    # Context for decision
    triggering_event_id: Optional[UUID] = Field(None, description="ThreatEvent that triggered this")
    threat_context: str = Field(..., description="Why this action is being proposed")
    expected_outcome: str = Field(..., description="What we hope to achieve")
    
    # Risk assessment
    risk_level: str = Field(..., description="HIGH/MEDIUM/LOW risk classification")
    potential_impact: List[str] = Field(..., description="Potential consequences")
    containment_measures: List[str] = Field(..., description="Safety measures in place")
    rollback_plan: str = Field(..., description="How to undo if things go wrong")
    
    # Authorization workflow
    requested_by: str = Field(..., description="System/user requesting authorization")
    assigned_to: str = Field(..., description="Human approver assigned")
    decision_deadline: datetime = Field(..., description="When decision must be made")
    decision_status: DecisionStatus = Field(default=DecisionStatus.PENDING)
    
    # Decision outcome
    decided_at: Optional[datetime] = Field(None)
    decided_by: Optional[str] = Field(None)
    decision_rationale: Optional[DecisionRationale] = Field(None)
    
    # Execution tracking
    executed_at: Optional[datetime] = Field(None)
    execution_result: Optional[str] = Field(None)
    
    # Extensibility
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('action_type')
    def validate_action_level_consistency(cls, v: ActionType, values: Dict[str, Any]) -> ActionType:
        """
        Validate action type matches declared action level.
        
        Prevents mislabeling high-risk actions as low-risk.
        """
        if 'action_level' not in values:
            return v
        
        level = values['action_level']
        
        # Level 4 actions PROHIBITED in Phase 1
        level_4_actions = {
            ActionType.COUNTER_EXPLOIT,
            ActionType.REVERSE_SHELL,
            ActionType.DATA_POISONING
        }
        if v in level_4_actions:
            raise ValueError(
                f"Level 4 offensive actions prohibited in Phase 1: {v}. "
                "Risk: Escalation to cyber warfare and legal liability."
            )
        
        # Validate level consistency
        level_1_actions = {ActionType.COLLECT_TELEMETRY, ActionType.LOG_EVENT, ActionType.GENERATE_ALERT}
        level_2_actions = {ActionType.UPDATE_FIREWALL_RULE, ActionType.ADJUST_IDS_SIGNATURE, ActionType.MODIFY_ASSET_CONFIG}
        level_3_actions = {ActionType.DEPLOY_DECEPTION_ASSET, ActionType.MODIFY_HONEYPOT_RESPONSE, ActionType.INJECT_FALSE_DATA}
        
        if level == ActionLevel.LEVEL_1_PASSIVE and v not in level_1_actions:
            raise ValueError(f"Action {v} cannot be Level 1 - requires higher authorization")
        if level == ActionLevel.LEVEL_2_ADAPTIVE and v not in level_2_actions:
            raise ValueError(f"Action {v} mislabeled as Level 2")
        if level == ActionLevel.LEVEL_3_DECEPTIVE and v not in level_3_actions:
            raise ValueError(f"Action {v} mislabeled as Level 3")
        
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class AuthorizationRequestCreate(BaseModel):
    """DTO for creating authorization requests."""
    action_level: ActionLevel
    action_type: ActionType
    action_description: str = Field(..., min_length=1)
    action_target: str
    triggering_event_id: Optional[UUID] = None
    threat_context: str
    expected_outcome: str
    risk_level: str
    potential_impact: List[str]
    containment_measures: List[str]
    rollback_plan: str
    requested_by: str
    assigned_to: str
    decision_deadline: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuthorizationDecision(BaseModel):
    """
    DTO for human authorization decision.
    
    Captures decision and rationale for audit trail.
    """
    request_id: UUID
    decision_status: DecisionStatus
    decided_by: str
    decision_rationale: DecisionRationale
    
    @validator('decision_status')
    def validate_decision_is_final(cls, v: DecisionStatus) -> DecisionStatus:
        """Ensure only final decisions are submitted."""
        if v == DecisionStatus.PENDING:
            raise ValueError("Cannot submit PENDING as decision")
        return v


class HITLMetrics(BaseModel):
    """
    Human-in-the-loop workflow metrics.
    
    Tracks authorization efficiency and decision patterns.
    Critical for identifying automation bottlenecks vs. necessary controls.
    """
    
    # Request volume
    total_requests: int = Field(default=0, ge=0)
    level_1_auto_approved: int = Field(default=0, ge=0)
    level_2_requests: int = Field(default=0, ge=0)
    level_3_requests: int = Field(default=0, ge=0)
    
    # Decision outcomes
    approved_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    escalated_count: int = Field(default=0, ge=0)
    expired_count: int = Field(default=0, ge=0)
    
    # Approval rates
    approval_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    rejection_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Response time
    average_decision_time_minutes: float = Field(default=0.0, ge=0.0)
    median_decision_time_minutes: float = Field(default=0.0, ge=0.0)
    expired_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Decision makers
    active_approvers: List[str] = Field(default_factory=list)
    approver_utilization: Dict[str, int] = Field(default_factory=dict)
    
    # Risk patterns
    high_risk_approved: int = Field(default=0, ge=0)
    high_risk_rejected: int = Field(default=0, ge=0)
    
    # Measurement period
    period_start: datetime = Field(default_factory=datetime.utcnow)
    period_end: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ApproverProfile(BaseModel):
    """
    Human approver profile and authorization scope.
    
    Addresses viability analysis requirement:
    "Who are these humans, what training, what protocol?"
    """
    
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    email: str = Field(...)
    
    # Authorization scope
    authorized_levels: List[ActionLevel] = Field(..., min_length=1)
    authorized_action_types: List[ActionType] = Field(..., min_length=1)
    max_risk_level: str = Field(..., description="Maximum risk level they can approve")
    
    # Training and certification
    security_clearance: Optional[str] = Field(None)
    training_completed: List[str] = Field(default_factory=list)
    certification_date: Optional[datetime] = Field(None)
    recertification_due: Optional[datetime] = Field(None)
    
    # Activity tracking
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_decision: Optional[datetime] = Field(None)
    total_decisions: int = Field(default=0, ge=0)
    
    # Escalation chain
    escalation_contact: Optional[str] = Field(None, description="Who to escalate to")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


# ============================================================================
# ALIASES FOR ROUTER COMPATIBILITY
# ============================================================================

# Type aliases to match router expectations
HITLDecision = AuthorizationRequest
HITLDecisionCreate = AuthorizationRequestCreate
HITLDecisionUpdate = BaseModel  # Placeholder - create if needed
HITLDecisionType = ActionType
HITLDecisionStatus = DecisionStatus
HITLDecisionOutcome = DecisionStatus
HITLApprovalLevel = ActionLevel
HITLAuditLog = BaseModel  # Placeholder - implement when needed


__all__ = [
    "ActionLevel",
    "ActionType",
    "DecisionStatus",
    "DecisionRationale",
    "AuthorizationRequest",
    "AuthorizationRequestCreate",
    "AuthorizationDecision",
    "HITLMetrics",
    "ApproverProfile",
    # Aliases
    "HITLDecision",
    "HITLDecisionCreate",
    "HITLDecisionUpdate",
    "HITLDecisionType",
    "HITLDecisionStatus",
    "HITLDecisionOutcome",
    "HITLApprovalLevel",
    "HITLAuditLog",
]
