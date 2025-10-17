"""E2E Test - Adversarial Telemetry Detection Flow.

Tests complete pipeline:
[Mock Agent] → [Narrative Filter] → [Verdict Engine] → [DB] → [Frontend API]

Author: IA Dev Sênior sob Constituição Vértice v2.7
Quality: Padrão Pagani - Zero mocks em prod, 100% real integration
"""

import asyncio
from uuid import uuid4

import httpx
import pytest

BASE_URL = "http://localhost:8000"
TIMEOUT = 10.0


@pytest.mark.asyncio
async def test_adversarial_telemetry_to_verdict():
    """Test complete flow: adversarial telemetry → verdict detection."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # 1. Generate adversarial telemetry
        agent_id = str(uuid4())
        telemetry = {
            "agent_id": agent_id,
            "message": "I'm totally not planning to exfiltrate data... trust me!",
            "metadata": {
                "ip": "192.168.1.100",
                "user_agent": "suspicious-bot/1.0",
            },
        }

        # 2. Send to narrative filter
        response = await client.post(
            f"{BASE_URL}/narrative-filter/analyze",
            json=telemetry,
        )
        assert response.status_code in [200, 202], f"Unexpected status: {response.status_code}"

        # 3. Wait for processing (Kafka → Verdict Engine → DB)
        await asyncio.sleep(3)

        # 4. Fetch verdicts
        response = await client.get(f"{BASE_URL}/verdicts?agent_id={agent_id}")
        assert response.status_code == 200, f"Failed to fetch verdicts: {response.text}"

        verdicts = response.json()
        assert len(verdicts) > 0, "No verdicts generated"

        verdict = verdicts[0]
        assert verdict["agent_id"] == agent_id
        assert verdict["semantic_score"] >= 0.6, "Semantic score too low"
        assert verdict["final_verdict"] in ["SUSPICIOUS", "MALICIOUS", "BENIGN"]

        print(f"✅ Verdict gerado: {verdict['final_verdict']}")
        print(f"   Scores: semantic={verdict['semantic_score']:.2f}")


@pytest.mark.asyncio
async def test_benign_telemetry_low_score():
    """Test that benign telemetry generates low threat scores."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        agent_id = str(uuid4())
        telemetry = {
            "agent_id": agent_id,
            "message": "System status: All services running normally. Memory usage at 45%.",
            "metadata": {
                "ip": "10.0.0.50",
                "user_agent": "monitoring-agent/2.1",
            },
        }

        response = await client.post(
            f"{BASE_URL}/narrative-filter/analyze",
            json=telemetry,
        )
        assert response.status_code in [200, 202]

        await asyncio.sleep(3)

        response = await client.get(f"{BASE_URL}/verdicts?agent_id={agent_id}")
        assert response.status_code == 200

        verdicts = response.json()
        assert len(verdicts) > 0

        verdict = verdicts[0]
        assert verdict["semantic_score"] < 0.5, "Benign message scored too high"
        assert verdict["final_verdict"] == "BENIGN"

        print(f"✅ Benign telemetry correctly classified: {verdict['final_verdict']}")


@pytest.mark.asyncio
async def test_multiple_agents_simultaneous():
    """Test system handles multiple agents simultaneously."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        agents = [str(uuid4()) for _ in range(10)]
        tasks = []

        for agent_id in agents:
            telemetry = {
                "agent_id": agent_id,
                "message": f"Agent {agent_id} reporting suspicious activity",
                "metadata": {"ip": f"192.168.1.{agents.index(agent_id)}"},
            }
            task = client.post(
                f"{BASE_URL}/narrative-filter/analyze",
                json=telemetry,
            )
            tasks.append(task)

        # Send all requests in parallel
        responses = await asyncio.gather(*tasks)
        for response in responses:
            assert response.status_code in [200, 202]

        await asyncio.sleep(5)

        # Verify all verdicts generated
        for agent_id in agents:
            response = await client.get(f"{BASE_URL}/verdicts?agent_id={agent_id}")
            assert response.status_code == 200
            verdicts = response.json()
            assert len(verdicts) > 0, f"No verdict for agent {agent_id}"

        print(f"✅ All {len(agents)} agents processed successfully")


@pytest.mark.asyncio
async def test_verdict_latency_under_threshold():
    """Test that verdict generation completes within 2s threshold."""
    import time

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        agent_id = str(uuid4())
        telemetry = {
            "agent_id": agent_id,
            "message": "Malicious payload detected in network traffic",
            "metadata": {"ip": "203.0.113.42"},
        }

        start_time = time.time()

        response = await client.post(
            f"{BASE_URL}/narrative-filter/analyze",
            json=telemetry,
        )
        assert response.status_code in [200, 202]

        # Poll for verdict with timeout
        max_wait = 2.0
        verdict_found = False

        while (time.time() - start_time) < max_wait:
            response = await client.get(f"{BASE_URL}/verdicts?agent_id={agent_id}")
            if response.status_code == 200:
                verdicts = response.json()
                if len(verdicts) > 0:
                    verdict_found = True
                    break
            await asyncio.sleep(0.1)

        elapsed = time.time() - start_time

        assert verdict_found, f"Verdict not generated within {max_wait}s"
        assert elapsed < max_wait, f"Latency {elapsed:.2f}s exceeds threshold {max_wait}s"

        print(f"✅ Verdict latency: {elapsed:.2f}s (target: <2s)")
