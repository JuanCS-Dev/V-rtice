"""
Governance Workspace - Ethical AI Decision Review

Real-time Human-in-the-Loop (HITL) workspace for reviewing and approving
AI ethical governance decisions from MAXIMUS.

Features:
- Real-time SSE streaming of pending decisions
- Three-panel reactive layout (Pending | Active | History)
- Approve/Reject/Escalate actions
- SLA monitoring and alerts
- Decision audit trail

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Quality: Production-ready, REGRA DE OURO compliant
"""

from .governance_workspace import GovernanceWorkspace

__all__ = ["GovernanceWorkspace"]
