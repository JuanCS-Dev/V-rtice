"""Test non-critical action coverage."""

import pytest
from hotl.decision_system import HOTLDecisionSystem, ActionType, ApprovalStatus
from enum import Enum


# Create a custom non-critical action type for testing
class CustomActionType(Enum):
    """Custom action type not in CRITICAL_ACTIONS."""
    ANALYZE_LOG = "analyze_log"
    REPORT_STATUS = "report_status"


@pytest.mark.asyncio
async def test_non_critical_action_auto_approval() -> None:
    """Test auto-approval of non-critical actions."""
    hotl = HOTLDecisionSystem(auto_approve_test=False)
    
    # Temporarily add custom action to test non-critical path
    # Since ActionType enum is defined, we use a mock approach
    original_is_critical = hotl.is_critical_action
    
    def mock_is_critical(action: ActionType) -> bool:
        # Make one specific action non-critical for testing
        if action == ActionType.EXECUTE_EXPLOIT:
            return False  # Temporarily treat as non-critical
        return original_is_critical(action)
    
    hotl.is_critical_action = mock_is_critical  # type: ignore
    
    # Request approval for "non-critical" action
    request = await hotl.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": "non_critical"},
        risk_level="low"
    )
    
    # Should be auto-approved
    assert request.status == ApprovalStatus.APPROVED
    assert request.approval is not None
    assert request.approval.operator == "system"
    assert request.approval.reason == "Non-critical action"
    
    # Should NOT be in pending requests
    assert request.id not in hotl.pending_requests
    
    # Should be in audit log
    audit = hotl.get_audit_log()
    assert len(audit) > 0
    
    # Restore original method
    hotl.is_critical_action = original_is_critical  # type: ignore
