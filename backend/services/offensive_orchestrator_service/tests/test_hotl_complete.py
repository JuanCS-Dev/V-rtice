"""Complete tests for HOTL decision system - 100% coverage."""

import pytest
from datetime import datetime, timedelta
from hotl.decision_system import (
    HOTLDecisionSystem,
    ActionType,
    ApprovalStatus,
    Approval,
    ApprovalRequest
)


@pytest.fixture
def hotl_auto() -> HOTLDecisionSystem:
    """HOTL system with auto-approval."""
    return HOTLDecisionSystem(auto_approve_test=True)


@pytest.fixture
def hotl_manual() -> HOTLDecisionSystem:
    """HOTL system without auto-approval."""
    return HOTLDecisionSystem(auto_approve_test=False)


@pytest.mark.asyncio
async def test_request_approval_critical_auto(hotl_auto: HOTLDecisionSystem) -> None:
    """Test critical action with auto-approval."""
    request = await hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"target": "192.168.1.100"},
        risk_level="high"
    )
    
    assert request.status == ApprovalStatus.APPROVED
    assert request.approval is not None
    assert request.approval.approved is True


@pytest.mark.asyncio
async def test_request_approval_critical_manual(hotl_manual: HOTLDecisionSystem) -> None:
    """Test critical action without auto-approval."""
    request = await hotl_manual.request_approval(
        action=ActionType.LATERAL_MOVEMENT,
        context={"source": "host1", "target": "host2"},
        risk_level="critical"
    )
    
    assert request.status == ApprovalStatus.PENDING
    assert request.approval is None
    assert request.id in hotl_manual.pending_requests


@pytest.mark.asyncio
async def test_request_approval_all_critical_actions(hotl_manual: HOTLDecisionSystem) -> None:
    """Test all critical action types."""
    for action_type in ActionType:
        request = await hotl_manual.request_approval(
            action=action_type,
            context={"test": action_type.value},
            risk_level="medium"
        )
        
        assert request.action == action_type
        if hotl_manual.is_critical_action(action_type):
            assert request.status == ApprovalStatus.PENDING


@pytest.mark.asyncio
async def test_process_approval_approve(hotl_manual: HOTLDecisionSystem) -> None:
    """Test approval processing (approved)."""
    request = await hotl_manual.request_approval(
        action=ActionType.DATA_EXFILTRATION,
        context={"data": "sensitive.db"},
        risk_level="critical"
    )
    
    approval = await hotl_manual.process_approval(
        request_id=request.id,
        approved=True,
        operator="operator1",
        reason="Authorized"
    )
    
    assert approval.approved is True
    assert approval.operator == "operator1"
    assert approval.reason == "Authorized"
    assert approval.status == ApprovalStatus.APPROVED
    assert request.id not in hotl_manual.pending_requests


@pytest.mark.asyncio
async def test_process_approval_reject(hotl_manual: HOTLDecisionSystem) -> None:
    """Test approval processing (rejected)."""
    request = await hotl_manual.request_approval(
        action=ActionType.PERSISTENCE,
        context={"mechanism": "scheduled_task"},
        risk_level="high"
    )
    
    approval = await hotl_manual.process_approval(
        request_id=request.id,
        approved=False,
        operator="operator2",
        reason="Too risky"
    )
    
    assert approval.approved is False
    assert approval.status == ApprovalStatus.REJECTED
    assert request.status == ApprovalStatus.REJECTED
    assert request.approval == approval


@pytest.mark.asyncio
async def test_process_approval_no_reason(hotl_manual: HOTLDecisionSystem) -> None:
    """Test approval without reason."""
    request = await hotl_manual.request_approval(
        action=ActionType.PRIVILEGE_ESCALATION,
        context={"method": "sudo"},
        risk_level="high"
    )
    
    approval = await hotl_manual.process_approval(
        request_id=request.id,
        approved=True,
        operator="operator3"
    )
    
    assert approval.approved is True
    assert approval.reason is None


@pytest.mark.asyncio
async def test_process_approval_invalid_request(hotl_manual: HOTLDecisionSystem) -> None:
    """Test processing with invalid request ID."""
    with pytest.raises(ValueError, match="Request .* not found"):
        await hotl_manual.process_approval(
            request_id="invalid_id_xyz",
            approved=True,
            operator="operator1"
        )


def test_is_critical_action_all_types(hotl_auto: HOTLDecisionSystem) -> None:
    """Test critical action detection for all types."""
    assert hotl_auto.is_critical_action(ActionType.EXECUTE_EXPLOIT) is True
    assert hotl_auto.is_critical_action(ActionType.LATERAL_MOVEMENT) is True
    assert hotl_auto.is_critical_action(ActionType.DATA_EXFILTRATION) is True
    assert hotl_auto.is_critical_action(ActionType.PERSISTENCE) is True
    assert hotl_auto.is_critical_action(ActionType.PRIVILEGE_ESCALATION) is True
    assert hotl_auto.is_critical_action(ActionType.CREDENTIAL_DUMPING) is True


def test_get_audit_log_empty(hotl_manual: HOTLDecisionSystem) -> None:
    """Test audit log retrieval when empty."""
    log = hotl_manual.get_audit_log()
    assert isinstance(log, list)


def test_get_audit_log_with_entries(hotl_auto: HOTLDecisionSystem) -> None:
    """Test audit log with entries."""
    import asyncio
    
    initial_count = len(hotl_auto.get_audit_log())
    
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": 1}
    ))
    
    log = hotl_auto.get_audit_log()
    assert len(log) > initial_count


def test_get_audit_log_filter_action(hotl_auto: HOTLDecisionSystem) -> None:
    """Test audit log filtering by action type."""
    import asyncio
    
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": 1}
    ))
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.LATERAL_MOVEMENT,
        context={"test": 2}
    ))
    
    exploit_log = hotl_auto.get_audit_log(action_type=ActionType.EXECUTE_EXPLOIT)
    lateral_log = hotl_auto.get_audit_log(action_type=ActionType.LATERAL_MOVEMENT)
    
    assert len(exploit_log) > 0
    assert len(lateral_log) > 0
    assert all(e["action"] == ActionType.EXECUTE_EXPLOIT.value for e in exploit_log)


def test_get_audit_log_filter_time_recent(hotl_auto: HOTLDecisionSystem) -> None:
    """Test audit log time filtering (recent)."""
    import asyncio
    
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": True}
    ))
    
    since = datetime.now() - timedelta(hours=1)
    log = hotl_auto.get_audit_log(since=since)
    
    assert len(log) > 0


def test_get_audit_log_filter_time_future(hotl_auto: HOTLDecisionSystem) -> None:
    """Test audit log time filtering (future)."""
    import asyncio
    
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": True}
    ))
    
    future = datetime.now() + timedelta(hours=1)
    log = hotl_auto.get_audit_log(since=future)
    
    assert len(log) == 0


def test_get_audit_log_combined_filters(hotl_auto: HOTLDecisionSystem) -> None:
    """Test audit log with combined filters."""
    import asyncio
    
    asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": True}
    ))
    
    since = datetime.now() - timedelta(minutes=5)
    log = hotl_auto.get_audit_log(
        action_type=ActionType.EXECUTE_EXPLOIT,
        since=since
    )
    
    assert all(e["action"] == ActionType.EXECUTE_EXPLOIT.value for e in log)


def test_get_pending_requests_empty(hotl_manual: HOTLDecisionSystem) -> None:
    """Test pending requests when empty."""
    pending = hotl_manual.get_pending_requests()
    assert isinstance(pending, list)
    assert len(pending) == 0


@pytest.mark.asyncio
async def test_get_pending_requests_multiple_async(hotl_manual: HOTLDecisionSystem) -> None:
    """Test pending requests with multiple entries (async)."""
    req1 = await hotl_manual.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": 1}
    )
    req2 = await hotl_manual.request_approval(
        action=ActionType.LATERAL_MOVEMENT,
        context={"test": 2}
    )
    
    pending = hotl_manual.get_pending_requests()
    
    assert len(pending) == 2
    assert all(req.status == ApprovalStatus.PENDING for req in pending)
    
    # Verify both requests are in pending
    pending_ids = {req.id for req in pending}
    assert req1.id in pending_ids
    assert req2.id in pending_ids


@pytest.mark.asyncio
async def test_get_pending_requests_after_approval_async(hotl_manual: HOTLDecisionSystem) -> None:
    """Test pending requests after processing (async)."""
    request = await hotl_manual.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": 1}
    )
    
    assert len(hotl_manual.get_pending_requests()) == 1
    
    await hotl_manual.process_approval(
        request_id=request.id,
        approved=True,
        operator="test"
    )
    
    assert len(hotl_manual.get_pending_requests()) == 0


def test_approval_dataclass_creation() -> None:
    """Test Approval dataclass."""
    approval = Approval(
        approved=True,
        status=ApprovalStatus.APPROVED,
        operator="test_op",
        reason="Test"
    )
    
    assert approval.approved is True
    assert approval.operator == "test_op"
    assert approval.reason == "Test"
    assert isinstance(approval.timestamp, datetime)


def test_approval_request_dataclass() -> None:
    """Test ApprovalRequest dataclass."""
    request = ApprovalRequest(
        id="test_001",
        action=ActionType.EXECUTE_EXPLOIT,
        context={"target": "test"},
        risk_level="high"
    )
    
    assert request.id == "test_001"
    assert request.action == ActionType.EXECUTE_EXPLOIT
    assert request.status == ApprovalStatus.PENDING
    assert request.approval is None
    assert isinstance(request.created_at, datetime)


def test_action_type_enum_values() -> None:
    """Test ActionType enum values."""
    assert ActionType.EXECUTE_EXPLOIT.value == "execute_exploit"
    assert ActionType.LATERAL_MOVEMENT.value == "lateral_movement"
    assert ActionType.DATA_EXFILTRATION.value == "data_exfiltration"
    assert ActionType.PERSISTENCE.value == "persistence"
    assert ActionType.PRIVILEGE_ESCALATION.value == "privilege_escalation"
    assert ActionType.CREDENTIAL_DUMPING.value == "credential_dumping"


def test_approval_status_enum_values() -> None:
    """Test ApprovalStatus enum values."""
    assert ApprovalStatus.PENDING.value == "pending"
    assert ApprovalStatus.APPROVED.value == "approved"
    assert ApprovalStatus.REJECTED.value == "rejected"
    assert ApprovalStatus.TIMEOUT.value == "timeout"


def test_hotl_initialization_auto() -> None:
    """Test HOTL system initialization with auto-approve."""
    hotl = HOTLDecisionSystem(auto_approve_test=True)
    
    assert hotl.auto_approve_test is True
    assert isinstance(hotl.audit_log, list)
    assert isinstance(hotl.pending_requests, dict)


def test_hotl_initialization_manual() -> None:
    """Test HOTL system initialization without auto-approve."""
    hotl = HOTLDecisionSystem(auto_approve_test=False)
    
    assert hotl.auto_approve_test is False
    assert len(hotl.audit_log) == 0
    assert len(hotl.pending_requests) == 0


def test_log_decision_internal(hotl_auto: HOTLDecisionSystem) -> None:
    """Test internal log decision method."""
    import asyncio
    
    initial_count = len(hotl_auto.audit_log)
    
    request = asyncio.run(hotl_auto.request_approval(
        action=ActionType.EXECUTE_EXPLOIT,
        context={"test": True}
    ))
    
    # Auto-approved, should have 2 log entries (request + decision)
    assert len(hotl_auto.audit_log) > initial_count
