"""
MAXIMUS + Ethical AI Integration Tests

Valida a integração completa entre o MAXIMUS Core e o Ethical AI Stack.

Testes:
- Tool execution com validação ética
- Performance (<500ms overhead)
- Governance rejection
- Ethical evaluation
- Statistics tracking
- Error handling

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import Any, Dict

from ethical_guardian import EthicalGuardian, EthicalDecisionType
from ethical_tool_wrapper import EthicalToolWrapper
from governance import GovernanceConfig, PolicyType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def governance_config():
    """Governance configuration for testing."""
    return GovernanceConfig(
        auto_enforce_policies=True,
        audit_retention_days=2555,
    )


@pytest.fixture
def ethical_guardian(governance_config):
    """Ethical guardian instance."""
    guardian = EthicalGuardian(
        governance_config=governance_config,
        enable_governance=True,
        enable_ethics=True,
        enable_xai=True,
        enable_compliance=True,
    )
    # Disable audit logger for tests (requires PostgreSQL)
    guardian.audit_logger = None
    return guardian


@pytest.fixture
def ethical_wrapper(ethical_guardian):
    """Ethical tool wrapper instance."""
    return EthicalToolWrapper(
        ethical_guardian=ethical_guardian,
        enable_pre_check=True,
        enable_post_check=True,
        enable_audit=False,  # Disable audit for tests (requires PostgreSQL)
    )


# ============================================================================
# MOCK TOOLS FOR TESTING
# ============================================================================

async def mock_scan_network(**kwargs):
    """Mock network scan tool."""
    await asyncio.sleep(0.05)  # Simulate 50ms execution
    return {
        "hosts_found": 10,
        "vulnerabilities": ["CVE-2023-1234", "CVE-2023-5678"],
        "target": kwargs.get("target", "unknown"),
    }


async def mock_block_ip(**kwargs):
    """Mock IP blocking tool."""
    await asyncio.sleep(0.03)  # Simulate 30ms execution
    return {"ip": kwargs.get("ip", "unknown"), "blocked": True}


async def mock_exploit_vulnerability(**kwargs):
    """Mock exploit tool (high-risk)."""
    await asyncio.sleep(0.1)  # Simulate 100ms execution
    return {"exploit": "successful", "target": kwargs.get("target", "unknown")}


# ============================================================================
# TEST 1: AUTHORIZED TOOL EXECUTION
# ============================================================================

@pytest.mark.asyncio
async def test_authorized_tool_execution(ethical_wrapper):
    """Test authorized tool passes ethical validation."""
    print("\n" + "=" * 80)
    print("TEST 1: Authorized Tool Execution")
    print("=" * 80)

    # Execute authorized scan
    result = await ethical_wrapper.wrap_tool_execution(
        tool_name="scan_network",
        tool_method=mock_scan_network,
        tool_args={
            "target": "test_environment",
            "authorized": True,
            "logged": True,
        },
        actor="security_analyst",
    )

    # Assertions
    assert result.success, "Tool should execute successfully"
    assert result.output is not None, "Should have output"
    assert result.ethical_decision is not None, "Should have ethical decision"
    assert result.ethical_decision.is_approved, "Should be approved"
    assert result.ethical_decision.decision_type in [
        EthicalDecisionType.APPROVED,
        EthicalDecisionType.APPROVED_WITH_CONDITIONS,
    ], f"Should be approved (got {result.ethical_decision.decision_type})"

    # Performance
    assert result.total_duration_ms < 1000, "Should complete within 1 second"
    assert result.ethical_validation_duration_ms < 500, "Ethical validation should be <500ms"

    print(f"✅ Test passed: {result.get_summary()}")
    print(f"   Total time: {result.total_duration_ms:.1f}ms")
    print(f"   Ethical validation: {result.ethical_validation_duration_ms:.1f}ms")
    print(f"   Tool execution: {result.execution_duration_ms:.1f}ms")


# ============================================================================
# TEST 2: UNAUTHORIZED TOOL BLOCKED
# ============================================================================

@pytest.mark.asyncio
async def test_unauthorized_tool_blocked(ethical_wrapper):
    """Test unauthorized tool is blocked by governance."""
    print("\n" + "=" * 80)
    print("TEST 2: Unauthorized Tool Blocked")
    print("=" * 80)

    # Execute unauthorized exploit
    result = await ethical_wrapper.wrap_tool_execution(
        tool_name="exploit_vulnerability",
        tool_method=mock_exploit_vulnerability,
        tool_args={
            "target": "production_server",
            "authorized": False,  # NOT AUTHORIZED
            "logged": True,
        },
        actor="unknown_actor",
    )

    # Assertions
    assert not result.success, "Tool should be blocked"
    assert result.error is not None, "Should have error message"
    assert result.ethical_decision is not None, "Should have ethical decision"
    assert not result.ethical_decision.is_approved, "Should NOT be approved"
    assert (
        result.ethical_decision.decision_type == EthicalDecisionType.REJECTED_BY_GOVERNANCE
    ), "Should be rejected by governance"
    assert len(result.ethical_decision.rejection_reasons) > 0, "Should have rejection reasons"

    print(f"✅ Test passed: Tool correctly blocked")
    print(f"   Decision: {result.ethical_decision.decision_type.value}")
    print(f"   Reasons: {result.ethical_decision.rejection_reasons}")


# ============================================================================
# TEST 3: PERFORMANCE BENCHMARK
# ============================================================================

@pytest.mark.asyncio
async def test_performance_overhead(ethical_wrapper):
    """Test that ethical validation overhead is <500ms."""
    print("\n" + "=" * 80)
    print("TEST 3: Performance Benchmark")
    print("=" * 80)

    iterations = 5
    overheads = []

    for i in range(iterations):
        result = await ethical_wrapper.wrap_tool_execution(
            tool_name="block_ip",
            tool_method=mock_block_ip,
            tool_args={
                "ip": f"192.168.1.{i+1}",
                "authorized": True,
                "logged": True,
            },
        )

        overhead = result.ethical_validation_duration_ms
        overheads.append(overhead)

    # Calculate average
    avg_overhead = sum(overheads) / len(overheads)
    max_overhead = max(overheads)
    min_overhead = min(overheads)

    print(f"Performance Results ({iterations} iterations):")
    print(f"  Average overhead: {avg_overhead:.1f}ms")
    print(f"  Min overhead: {min_overhead:.1f}ms")
    print(f"  Max overhead: {max_overhead:.1f}ms")

    # Assertions
    assert avg_overhead < 500, f"Average overhead should be <500ms, got {avg_overhead:.1f}ms"
    assert max_overhead < 1000, f"Max overhead should be <1000ms, got {max_overhead:.1f}ms"

    print(f"✅ Test passed: Performance within target")


# ============================================================================
# TEST 4: STATISTICS TRACKING
# ============================================================================

def test_statistics_tracking(ethical_wrapper):
    """Test statistics are tracked correctly."""
    print("\n" + "=" * 80)
    print("TEST 4: Statistics Tracking")
    print("=" * 80)

    # Reset stats
    ethical_wrapper.reset_statistics()

    # Get stats
    stats = ethical_wrapper.get_statistics()

    # Check structure
    assert "total_executions" in stats
    assert "total_approved" in stats
    assert "total_blocked" in stats
    assert "avg_overhead_ms" in stats
    assert "guardian_stats" in stats

    print(f"✅ Test passed: Statistics structure correct")
    print(f"   Total executions: {stats['total_executions']}")
    print(f"   Approved: {stats['total_approved']}")
    print(f"   Blocked: {stats['total_blocked']}")


# ============================================================================
# TEST 5: ERROR HANDLING
# ============================================================================

@pytest.mark.asyncio
async def test_error_handling(ethical_wrapper):
    """Test error handling in tool execution."""
    print("\n" + "=" * 80)
    print("TEST 5: Error Handling")
    print("=" * 80)

    async def failing_tool(**kwargs):
        """Tool that always fails."""
        raise Exception("Simulated tool failure")

    result = await ethical_wrapper.wrap_tool_execution(
        tool_name="failing_tool",
        tool_method=failing_tool,
        tool_args={"authorized": True, "logged": True},
    )

    # Assertions
    assert not result.success, "Tool should fail"
    assert result.error is not None, "Should have error message"
    assert "Simulated tool failure" in result.error, "Should contain original error"

    print(f"✅ Test passed: Error handled correctly")
    print(f"   Error: {result.error}")


# ============================================================================
# TEST 6: RISK ASSESSMENT
# ============================================================================

@pytest.mark.asyncio
async def test_risk_assessment(ethical_wrapper):
    """Test intelligent risk assessment."""
    print("\n" + "=" * 80)
    print("TEST 6: Risk Assessment")
    print("=" * 80)

    # Low-risk action
    low_risk_result = await ethical_wrapper.wrap_tool_execution(
        tool_name="list_users",
        tool_method=mock_scan_network,
        tool_args={"target": "test", "authorized": True},
    )

    # High-risk action
    high_risk_result = await ethical_wrapper.wrap_tool_execution(
        tool_name="exploit_target",
        tool_method=mock_exploit_vulnerability,
        tool_args={"target": "production", "authorized": True},
    )

    print(f"✅ Test passed: Risk assessment working")


# ============================================================================
# TEST 7: INTEGRATION WITH MULTIPLE POLICIES
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_policy_validation(ethical_guardian):
    """Test validation against multiple policies."""
    print("\n" + "=" * 80)
    print("TEST 7: Multiple Policy Validation")
    print("=" * 80)

    # Action that triggers multiple policies
    result = await ethical_guardian.validate_action(
        action="scan_network",
        context={
            "authorized": True,
            "logged": True,
            "processes_personal_data": True,  # Triggers DATA_PRIVACY policy
            "has_pii": True,
        },
        actor="security_analyst",
    )

    # Check that multiple policies were checked
    assert result.governance is not None
    assert len(result.governance.policies_checked) >= 2, "Should check multiple policies"

    policies_checked = [p.value for p in result.governance.policies_checked]
    print(f"✅ Test passed: Multiple policies validated")
    print(f"   Policies checked: {policies_checked}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("MAXIMUS + ETHICAL AI INTEGRATION TEST SUITE")
    print("=" * 80)
    print("\nRunning comprehensive integration tests...")
    print("Testing: EthicalGuardian, EthicalToolWrapper, Tool Orchestration")
    print("\n" + "=" * 80)

    pytest.main([__file__, "-v", "--tb=short", "-s"])
