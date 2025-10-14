"""
Tests for HOTL (Human-on-the-Loop) Decision System.

Covers:
- HOTLDecisionSystem initialization
- Audit log creation
- Request approval flow
- Auto-approval (HOTL disabled, low-risk)
- Timeout handling
- Provide approval (operator decision)
- Get pending requests
- Risk assessment
- Decision logging
- Cleanup stale requests
- Error handling
"""

import pytest
import asyncio
import json
import tempfile
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, mock_open

from hotl_system import HOTLDecisionSystem
from models import (
    HOTLRequest,
    HOTLResponse,
    ApprovalStatus,
    RiskLevel,
    ActionType,
)
from config import HOTLConfig


@pytest.mark.unit
class TestHOTLSystemInit:
    """Test HOTLDecisionSystem initialization."""

    def test_hotl_system_init_default_config(self):
        """Test creating HOTL system with default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                auto_approve_low_risk=True,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            assert system.config == config
            assert len(system._pending_requests) == 0
            assert system._audit_log_path.exists()

    def test_hotl_system_init_no_config(self):
        """Test creating HOTL system without explicit config (uses default)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('hotl_system.HOTLConfig') as mock_config_class:
                mock_config = Mock()
                mock_config.audit_log_path = f"{tmpdir}/hotl_audit.log"
                mock_config.enabled = True
                mock_config.approval_timeout_seconds = 300
                mock_config.auto_approve_low_risk = False
                mock_config_class.return_value = mock_config

                system = HOTLDecisionSystem()

                assert system.config == mock_config

    def test_ensure_audit_log_creates_directory(self):
        """Test audit log directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = f"{tmpdir}/subdir/hotl_audit.log"
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=audit_path,
            )

            system = HOTLDecisionSystem(config=config)

            assert Path(audit_path).parent.exists()
            assert Path(audit_path).exists()

    def test_ensure_audit_log_fallback_on_error(self):
        """Test audit log fallback to /tmp on error."""
        config = HOTLConfig(
            enabled=True,
            approval_timeout_seconds=300,
            audit_log_path="/invalid/readonly/path/hotl_audit.log",
        )

        with patch('hotl_system.Path.mkdir', side_effect=PermissionError("No permission")):
            system = HOTLDecisionSystem(config=config)

            # Should fallback to /tmp
            assert "/tmp/hotl_audit.log" in str(system._audit_log_path)


@pytest.mark.unit
class TestRequestApproval:
    """Test request approval flow."""

    @pytest.mark.asyncio
    async def test_request_approval_hotl_disabled(self, sample_hotl_request):
        """Test auto-approval when HOTL is disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=False,  # Disabled
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            response = await system.request_approval(sample_hotl_request)

            assert response.status == ApprovalStatus.APPROVED
            assert response.approved is True
            assert response.operator == "system"
            assert "disabled" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_request_approval_low_risk_auto_approve(self):
        """Test auto-approval for low-risk actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                auto_approve_low_risk=True,  # Auto-approve enabled
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            # Create low-risk request
            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.RECONNAISSANCE,
                description="Port scan",
                risk_level=RiskLevel.LOW,  # Low risk
                context={},
            )

            system = HOTLDecisionSystem(config=config)

            response = await system.request_approval(request)

            assert response.status == ApprovalStatus.APPROVED
            assert response.approved is True
            assert response.operator == "system"
            assert "low risk" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_request_approval_timeout(self):
        """Test request timeout when no approval is provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=1,  # Short timeout for test
                auto_approve_low_risk=False,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            # High-risk request that requires approval
            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Exploit vulnerability",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            system = HOTLDecisionSystem(config=config)

            # Should timeout since no approval is provided
            response = await system.request_approval(request)

            assert response.status == ApprovalStatus.TIMEOUT
            assert response.approved is False
            assert "timed out" in response.reasoning.lower()
            assert request.request_id not in system._pending_requests

    @pytest.mark.asyncio
    async def test_request_approval_queued(self):
        """Test request is queued for approval."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=2,
                auto_approve_low_risk=False,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Test action",
                risk_level=RiskLevel.MEDIUM,
                context={},
            )

            system = HOTLDecisionSystem(config=config)

            # Start approval request (will timeout after 2s)
            approval_task = asyncio.create_task(system.request_approval(request))

            # Wait a bit to let it queue
            await asyncio.sleep(0.1)

            # Should be in pending
            assert request.request_id in system._pending_requests
            assert system.get_pending_count() == 1

            # Cancel to avoid waiting for timeout
            approval_task.cancel()
            try:
                await approval_task
            except asyncio.CancelledError:
                pass


@pytest.mark.unit
class TestProvideApproval:
    """Test providing approval decisions."""

    @pytest.mark.asyncio
    async def test_provide_approval_approved(self):
        """Test approving a pending request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Test action",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            system = HOTLDecisionSystem(config=config)

            # Manually add to pending (simulating queued request)
            system._pending_requests[request.request_id] = request

            # Provide approval
            response = await system.provide_approval(
                request_id=request.request_id,
                approved=True,
                operator="operator1",
                reasoning="Action is safe to proceed",
            )

            assert response.status == ApprovalStatus.APPROVED
            assert response.approved is True
            assert response.operator == "operator1"
            assert response.reasoning == "Action is safe to proceed"
            assert request.request_id not in system._pending_requests

    @pytest.mark.asyncio
    async def test_provide_approval_rejected(self):
        """Test rejecting a pending request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Dangerous action",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            system = HOTLDecisionSystem(config=config)
            system._pending_requests[request.request_id] = request

            # Reject request
            response = await system.provide_approval(
                request_id=request.request_id,
                approved=False,
                operator="operator2",
                reasoning="Too risky to proceed",
            )

            assert response.status == ApprovalStatus.REJECTED
            assert response.approved is False
            assert response.operator == "operator2"
            assert request.request_id not in system._pending_requests

    @pytest.mark.asyncio
    async def test_provide_approval_request_not_found(self):
        """Test providing approval for non-existent request raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            with pytest.raises(ValueError) as exc_info:
                await system.provide_approval(
                    request_id=uuid4(),
                    approved=True,
                    operator="operator1",
                )

            assert "not found" in str(exc_info.value).lower()


@pytest.mark.unit
class TestGetPendingRequests:
    """Test retrieving pending requests."""

    def test_get_pending_requests_empty(self):
        """Test getting pending requests when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            pending = system.get_pending_requests()

            assert len(pending) == 0
            assert system.get_pending_count() == 0

    def test_get_pending_requests_multiple(self):
        """Test getting multiple pending requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            # Add multiple pending requests
            request1 = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Action 1",
                risk_level=RiskLevel.HIGH,
                context={},
            )
            request2 = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Action 2",
                risk_level=RiskLevel.MEDIUM,
                context={},
            )

            system._pending_requests[request1.request_id] = request1
            system._pending_requests[request2.request_id] = request2

            pending = system.get_pending_requests()

            assert len(pending) == 2
            assert system.get_pending_count() == 2
            assert request1 in pending
            assert request2 in pending


@pytest.mark.unit
class TestRiskAssessment:
    """Test risk assessment logic."""

    def test_assess_risk_high_exploitation(self):
        """Test high risk assessment for exploitation actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type="exploitation",
                description="Exploit SQL injection",
                risk_level=RiskLevel.MEDIUM,  # Will be reassessed
                context={},
            )

            assessed_risk = system.assess_risk(request)

            assert assessed_risk == RiskLevel.HIGH

    def test_assess_risk_high_post_exploitation(self):
        """Test high risk assessment for post-exploitation actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type="post_exploitation",
                description="Lateral movement",
                risk_level=RiskLevel.LOW,
                context={},
            )

            assessed_risk = system.assess_risk(request)

            assert assessed_risk == RiskLevel.HIGH

    def test_assess_risk_low_reconnaissance(self):
        """Test low risk assessment for reconnaissance actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type="reconnaissance",
                description="Port scan",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            assessed_risk = system.assess_risk(request)

            assert assessed_risk == RiskLevel.LOW

    def test_assess_risk_low_analysis(self):
        """Test low risk assessment for analysis actions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type="analysis",
                description="Analyze logs",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            assessed_risk = system.assess_risk(request)

            assert assessed_risk == RiskLevel.LOW

    def test_assess_risk_medium_default(self):
        """Test medium risk assessment for actions that don't match specific rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            # Use valid ActionType but one that doesn't match any specific rule
            # (not exploitation, post_exploitation, reconnaissance, or analysis)
            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,  # But we'll test with lowercase that doesn't match
                description="Custom action",
                risk_level=RiskLevel.LOW,
                context={},
            )

            # Manually override action_type to test the string matching logic
            # The assess_risk method uses .lower() so "EXPLOITATION" won't match "exploit"
            request.action_type = "weaponization"  # Valid ActionType value but no specific rule

            # Since "weaponization" doesn't match any specific keywords, should return MEDIUM
            assessed_risk = system.assess_risk(request)

            assert assessed_risk == RiskLevel.MEDIUM


@pytest.mark.unit
class TestDecisionLogging:
    """Test decision audit logging."""

    @pytest.mark.asyncio
    async def test_log_decision_success(self):
        """Test successful decision logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = f"{tmpdir}/hotl_audit.log"
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=audit_path,
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Test action",
                risk_level=RiskLevel.HIGH,
                context={"test": "data"},
            )

            response = HOTLResponse(
                request_id=request.request_id,
                status=ApprovalStatus.APPROVED,
                approved=True,
                operator="operator1",
                reasoning="Test reasoning",
            )

            await system._log_decision(request, response)

            # Read audit log
            with open(audit_path, "r") as f:
                log_lines = f.readlines()

            assert len(log_lines) == 1
            log_entry = json.loads(log_lines[0])

            assert log_entry["request_id"] == str(request.request_id)
            assert log_entry["campaign_id"] == str(request.campaign_id)
            assert log_entry["action_type"] == request.action_type
            assert log_entry["decision"]["approved"] is True
            assert log_entry["decision"]["operator"] == "operator1"

    @pytest.mark.asyncio
    async def test_log_decision_error_handling(self):
        """Test error handling when logging fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Test",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            response = HOTLResponse(
                request_id=request.request_id,
                status=ApprovalStatus.APPROVED,
                approved=True,
            )

            # Mock open to raise exception
            with patch('builtins.open', side_effect=IOError("Write failed")):
                # Should not raise, just log error
                await system._log_decision(request, response)


@pytest.mark.unit
class TestCleanupStaleRequests:
    """Test cleanup of stale requests."""

    @pytest.mark.asyncio
    async def test_cleanup_stale_requests_none_stale(self):
        """Test cleanup when no requests are stale."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            # Add recent request
            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Recent request",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            system._pending_requests[request.request_id] = request

            await system.cleanup_stale_requests(max_age_seconds=3600)

            # Should still be there
            assert request.request_id in system._pending_requests
            assert system.get_pending_count() == 1

    @pytest.mark.asyncio
    async def test_cleanup_stale_requests_removes_old(self):
        """Test cleanup removes stale requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            # Add old request (mock old timestamp)
            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Old request",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            # Make it appear old
            old_timestamp = datetime.utcnow() - timedelta(seconds=7200)  # 2 hours old
            request.timestamp = old_timestamp

            system._pending_requests[request.request_id] = request

            await system.cleanup_stale_requests(max_age_seconds=3600)  # 1 hour max

            # Should be removed
            assert request.request_id not in system._pending_requests
            assert system.get_pending_count() == 0


@pytest.mark.unit
class TestWaitForApproval:
    """Test _wait_for_approval internal method."""

    @pytest.mark.asyncio
    async def test_wait_for_approval_returns_response_when_resolved(self):
        """Test _wait_for_approval returns response when request is resolved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.EXPLOITATION,
                description="Test",
                risk_level=RiskLevel.HIGH,
                context={},
            )

            # Add to pending
            system._pending_requests[request.request_id] = request

            # Start wait_for_approval task
            wait_task = asyncio.create_task(system._wait_for_approval(request.request_id))

            # Wait a bit
            await asyncio.sleep(0.1)

            # Manually remove from pending (simulating provide_approval)
            system._pending_requests.pop(request.request_id, None)

            # Should return a response
            response = await wait_task

            assert isinstance(response, HOTLResponse)
            assert response.request_id == request.request_id
            assert response.approved is True
            assert "retrieved_from_provider" in response.operator


@pytest.mark.unit
class TestAutoApprove:
    """Test _auto_approve internal method."""

    @pytest.mark.asyncio
    async def test_auto_approve_creates_response(self):
        """Test _auto_approve creates proper response."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = HOTLConfig(
                enabled=True,
                approval_timeout_seconds=300,
                audit_log_path=f"{tmpdir}/hotl_audit.log",
            )

            system = HOTLDecisionSystem(config=config)

            request = HOTLRequest(
                request_id=uuid4(),
                campaign_id=uuid4(),
                action_type=ActionType.RECONNAISSANCE,
                description="Low risk scan",
                risk_level=RiskLevel.LOW,
                context={},
            )

            response = system._auto_approve(request, reason="Test auto-approval")

            assert response.status == ApprovalStatus.APPROVED
            assert response.approved is True
            assert response.operator == "system"
            assert response.reasoning == "Test auto-approval"

            # Give time for async task to complete
            await asyncio.sleep(0.1)
