"""Tests for Kill Switch."""

import pytest
from kill_switch import KillSwitch


@pytest.mark.asyncio
async def test_graceful_shutdown():
    """Test graceful shutdown layer."""
    kill_switch = KillSwitch()

    result = await kill_switch.graceful_shutdown("agent-123")

    assert result["credentials_revoked"] is True
    assert result["sigterm_sent"] is True
    assert result["connections_drained"] is True


@pytest.mark.asyncio
async def test_force_kill():
    """Test force kill layer."""
    kill_switch = KillSwitch()

    result = await kill_switch.force_kill("agent-456")

    assert result["sigkill_sent"] is True
    assert result["container_deleted"] is True
    assert result["network_access_revoked"] is True
    assert result["marked_terminated"] is True


@pytest.mark.asyncio
async def test_network_quarantine():
    """Test network quarantine layer."""
    kill_switch = KillSwitch()

    result = await kill_switch.network_quarantine("agent-789")

    assert result["firewall_applied"] is True
    assert result["packets_dropped"] is True
    assert result["security_alerted"] is True


@pytest.mark.asyncio
async def test_all_layers_sequential():
    """Test executing all 3 layers sequentially."""
    kill_switch = KillSwitch()

    # Layer 1
    result1 = await kill_switch.graceful_shutdown("agent-999")
    assert len(result1) == 3

    # Layer 2
    result2 = await kill_switch.force_kill("agent-999")
    assert len(result2) == 4

    # Layer 3
    result3 = await kill_switch.network_quarantine("agent-999")
    assert len(result3) == 3
