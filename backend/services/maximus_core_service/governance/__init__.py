"""
Governance Module for VÉRTICE Platform

Phase 0: Foundation & Governance

Provides comprehensive governance framework including:
- Ethics Review Board (ERB) management
- 5 core ethical policies
- Policy enforcement engine
- PostgreSQL audit infrastructure
- Whistleblower protection

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Platform Team"

# Base data structures
# Audit infrastructure
from .audit_infrastructure import AuditLogger
from .base import (
    # Audit structures
    AuditLog,
    # Enums
    AuditLogLevel,
    DecisionType,
    # ERB structures
    ERBDecision,
    ERBMeeting,
    ERBMember,
    ERBMemberRole,
    GovernanceAction,
    # Config
    GovernanceConfig,
    # Results
    GovernanceResult,
    # Policy structures
    Policy,
    PolicyEnforcementResult,
    PolicySeverity,
    PolicyType,
    PolicyViolation,
    WhistleblowerReport,
)

# ERB management
from .ethics_review_board import ERBManager

# Policies
from .policies import (
    PolicyRegistry,
    create_data_privacy_policy,
    create_ethical_use_policy,
    create_incident_response_policy,
    create_red_teaming_policy,
    create_whistleblower_policy,
)

# Policy enforcement
from .policy_engine import PolicyEngine

__all__ = [
    # Enums
    "AuditLogLevel",
    "DecisionType",
    "ERBMemberRole",
    "GovernanceAction",
    "PolicySeverity",
    "PolicyType",
    # Config
    "GovernanceConfig",
    # ERB
    "ERBDecision",
    "ERBManager",
    "ERBMeeting",
    "ERBMember",
    # Policies
    "Policy",
    "PolicyEnforcementResult",
    "PolicyEngine",
    "PolicyRegistry",
    "PolicyViolation",
    "create_data_privacy_policy",
    "create_ethical_use_policy",
    "create_incident_response_policy",
    "create_red_teaming_policy",
    "create_whistleblower_policy",
    # Audit
    "AuditLog",
    "AuditLogger",
    "WhistleblowerReport",
    # Results
    "GovernanceResult",
]
