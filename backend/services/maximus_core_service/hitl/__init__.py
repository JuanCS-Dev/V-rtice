"""
HITL/HOTL Module - Human-in-the-Loop and Human-on-the-Loop Framework

This module provides a comprehensive framework for human-AI collaboration in
security operations, ensuring that critical decisions receive appropriate human
oversight while maintaining operational efficiency.

Key Features:
- Risk-based automation level determination (FULL, SUPERVISED, ADVISORY, MANUAL)
- Decision queue with SLA tracking
- Escalation management for timeouts and high-risk scenarios
- Operator interface for human review and approval
- Complete audit trail for compliance and forensics

Architecture:
    MAXIMUS AI Decision
            ↓
    Risk Assessor → Automation Level
            ↓
    HIGH (≥95%)? → EXECUTE (auto)
    MEDIUM (≥80%)? → SUPERVISED (approval required)
    LOW (≥60%)? → ADVISORY (AI suggests, human decides)
    VERY LOW (<60%)? → MANUAL (no AI execution)
            ↓
    Decision Queue (SLA: 5-30min)
            ↓
    Operator Interface
            ↓
    Execute + Audit Trail

Privacy & Security:
- All decisions logged with complete context
- Audit trail immutable and timestamped
- Role-based access control for operators
- PII redaction in logs (configurable)

Integration:
- Integrates with MAXIMUS AI reasoning engine
- Works with Immunis immune system for threat response
- Feeds ethical_audit_service for compliance tracking

Usage:
    from hitl import (
        HITLDecisionFramework,
        RiskAssessor,
        DecisionQueue,
        OperatorInterface,
        AuditTrail,
    )

    # Initialize framework
    framework = HITLDecisionFramework(config)

    # AI makes decision
    decision = framework.evaluate_action(
        action_type="isolate_host",
        context={"host_id": "srv-123", "threat_score": 0.92},
        confidence=0.88,
    )

    # Check automation level
    if decision.automation_level == AutomationLevel.FULL:
        # Execute immediately
        result = framework.execute_decision(decision)
    else:
        # Queue for human review
        framework.queue_for_review(decision)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

from .audit_trail import (
    AuditQuery,
    AuditTrail,
    ComplianceReport,
)
from .base import (
    ActionType,
    AuditEntry,
    # Enums
    AutomationLevel,
    DecisionContext,
    DecisionStatus,
    EscalationConfig,
    # Configuration
    HITLConfig,
    # Core data structures
    HITLDecision,
    OperatorAction,
    RiskLevel,
    SLAConfig,
)
from .decision_framework import (
    DecisionResult,
    HITLDecisionFramework,
)
from .decision_queue import (
    DecisionQueue,
    QueuedDecision,
    SLAMonitor,
)
from .escalation_manager import (
    EscalationEvent,
    EscalationManager,
    EscalationRule,
)
from .operator_interface import (
    OperatorInterface,
    OperatorMetrics,
    OperatorSession,
)
from .risk_assessor import (
    RiskAssessor,
    RiskFactors,
    RiskScore,
)

# Version information
__version__ = "1.0.0"
__author__ = "Claude Code + JuanCS-Dev"
__all__ = [
    # Base classes
    "HITLDecision",
    "DecisionContext",
    "OperatorAction",
    "AuditEntry",
    "AutomationLevel",
    "RiskLevel",
    "DecisionStatus",
    "ActionType",
    "HITLConfig",
    "SLAConfig",
    "EscalationConfig",
    # Risk assessment
    "RiskAssessor",
    "RiskScore",
    "RiskFactors",
    # Decision framework
    "HITLDecisionFramework",
    "DecisionResult",
    # Queue management
    "DecisionQueue",
    "QueuedDecision",
    "SLAMonitor",
    # Escalation
    "EscalationManager",
    "EscalationRule",
    "EscalationEvent",
    # Operator interface
    "OperatorInterface",
    "OperatorSession",
    "OperatorMetrics",
    # Audit
    "AuditTrail",
    "AuditQuery",
    "ComplianceReport",
]
