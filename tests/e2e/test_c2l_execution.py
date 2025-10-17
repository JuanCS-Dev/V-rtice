"""E2E Test - C2L Command Execution Flow.

Tests complete kill switch pipeline:
[Frontend] → [Command Bus API] → [NATS] → [C2L Executor] → [Kill Switch] → [Audit]

Author: IA Dev Sênior sob Constituição Vértice v2.7
Quality: Padrão Pagani
"""

import asyncio
from uuid import uuid4

import httpx
import pytest

BASE_URL = "http://localhost:8000"
COMMAND_BUS_URL = "http://localhost:8092"
TIMEOUT = 10.0


@pytest.mark.asyncio
async def test_c2l_mute_command():
    """Test C2L MUTE command execution (Layer 1 only)."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        command_id = str(uuid4())
        agent_id = str(uuid4())

        # 1. Create MUTE command
        command = {
            "command_id": command_id,
            "command_type": "MUTE",
            "target_agent_id": agent_id,
            "issuer": "test-suite-e2e",
        }

        response = await client.post(
            f"{COMMAND_BUS_URL}/commands",
            json=command,
        )
        assert response.status_code in [200, 202], f"Command failed: {response.text}"

        # 2. Wait for execution
        await asyncio.sleep(3)

        # 3. Check audit logs (should have 1 entry: GRACEFUL)
        response = await client.get(
            f"{COMMAND_BUS_URL}/audits?command_id={command_id}"
        )
        assert response.status_code == 200

        audits = response.json()
        assert len(audits) == 1, f"Expected 1 audit entry, got {len(audits)}"

        audit = audits[0]
        assert audit["layer"] == "GRACEFUL"
        assert audit["success"] is True

        print(f"✅ MUTE command executed: {audit['layer']}")


@pytest.mark.asyncio
async def test_c2l_isolate_command():
    """Test C2L ISOLATE command execution (Layers 1 + 3)."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        command_id = str(uuid4())
        agent_id = str(uuid4())

        command = {
            "command_id": command_id,
            "command_type": "ISOLATE",
            "target_agent_id": agent_id,
            "issuer": "test-suite-e2e",
        }

        response = await client.post(
            f"{COMMAND_BUS_URL}/commands",
            json=command,
        )
        assert response.status_code in [200, 202]

        await asyncio.sleep(3)

        response = await client.get(
            f"{COMMAND_BUS_URL}/audits?command_id={command_id}"
        )
        assert response.status_code == 200

        audits = response.json()
        assert len(audits) == 2, f"Expected 2 audit entries, got {len(audits)}"

        layers = [audit["layer"] for audit in audits]
        assert "GRACEFUL" in layers
        assert "NETWORK" in layers

        print(f"✅ ISOLATE command executed: {layers}")


@pytest.mark.asyncio
async def test_c2l_terminate_command():
    """Test C2L TERMINATE command execution (All 3 layers)."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        command_id = str(uuid4())
        agent_id = str(uuid4())

        command = {
            "command_id": command_id,
            "command_type": "TERMINATE",
            "target_agent_id": agent_id,
            "issuer": "test-suite-e2e",
        }

        response = await client.post(
            f"{COMMAND_BUS_URL}/commands",
            json=command,
        )
        assert response.status_code in [200, 202]

        await asyncio.sleep(5)

        response = await client.get(
            f"{COMMAND_BUS_URL}/audits?command_id={command_id}"
        )
        assert response.status_code == 200

        audits = response.json()
        assert len(audits) == 3, f"Expected 3 audit entries, got {len(audits)}"

        layers = [audit["layer"] for audit in audits]
        assert "GRACEFUL" in layers
        assert "FORCE" in layers
        assert "NETWORK" in layers

        # All should succeed
        for audit in audits:
            assert audit["success"] is True, f"Layer {audit['layer']} failed"

        print(f"✅ TERMINATE command executed: {layers}")


@pytest.mark.asyncio
async def test_c2l_command_latency():
    """Test that C2L command execution completes within 5s."""
    import time

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        command_id = str(uuid4())
        agent_id = str(uuid4())

        command = {
            "command_id": command_id,
            "command_type": "TERMINATE",
            "target_agent_id": agent_id,
            "issuer": "test-suite-latency",
        }

        start_time = time.time()

        response = await client.post(
            f"{COMMAND_BUS_URL}/commands",
            json=command,
        )
        assert response.status_code in [200, 202]

        # Poll for completion
        max_wait = 5.0
        completed = False

        while (time.time() - start_time) < max_wait:
            response = await client.get(
                f"{COMMAND_BUS_URL}/audits?command_id={command_id}"
            )
            if response.status_code == 200:
                audits = response.json()
                if len(audits) == 3:  # All layers completed
                    completed = True
                    break
            await asyncio.sleep(0.2)

        elapsed = time.time() - start_time

        assert completed, f"Command not completed within {max_wait}s"
        assert elapsed < max_wait, f"Latency {elapsed:.2f}s exceeds {max_wait}s"

        print(f"✅ Command latency: {elapsed:.2f}s (target: <5s)")


@pytest.mark.asyncio
async def test_c2l_cascade_terminate():
    """Test cascade termination (parent → sub-agents)."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        parent_id = str(uuid4())
        # Note: sub_agent_1, sub_agent_2 would be registered in DB
        # (In real system, this would be pre-populated via relationship graph)

        command_id = str(uuid4())
        command = {
            "command_id": command_id,
            "command_type": "TERMINATE",
            "target_agent_id": parent_id,
            "issuer": "test-suite-cascade",
        }

        response = await client.post(
            f"{COMMAND_BUS_URL}/commands",
            json=command,
        )
        assert response.status_code in [200, 202]

        await asyncio.sleep(7)

        # Verify parent terminated
        response = await client.get(
            f"{COMMAND_BUS_URL}/audits?command_id={command_id}"
        )
        assert response.status_code == 200
        audits = response.json()
        assert len(audits) >= 3

        print(f"✅ Cascade terminate executed (parent + {len(audits) - 3} sub-agents)")


@pytest.mark.asyncio
async def test_c2l_multiple_commands_simultaneous():
    """Test system handles multiple C2L commands concurrently."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        commands = []
        for i in range(5):
            command_id = str(uuid4())
            agent_id = str(uuid4())
            commands.append(
                {
                    "command_id": command_id,
                    "command_type": "MUTE",
                    "target_agent_id": agent_id,
                    "issuer": f"test-concurrent-{i}",
                }
            )

        # Submit all commands in parallel
        tasks = [
            client.post(f"{COMMAND_BUS_URL}/commands", json=cmd) for cmd in commands
        ]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            assert response.status_code in [200, 202]

        await asyncio.sleep(5)

        # Verify all executed
        for command in commands:
            response = await client.get(
                f"{COMMAND_BUS_URL}/audits?command_id={command['command_id']}"
            )
            assert response.status_code == 200
            audits = response.json()
            assert len(audits) >= 1, f"Command {command['command_id']} not executed"

        print(f"✅ {len(commands)} concurrent commands executed")
