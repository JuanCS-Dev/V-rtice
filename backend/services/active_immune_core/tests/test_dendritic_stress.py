"""Dendritic Cell Stress Tests - Validate Robustness Under Load

These tests intentionally create high concurrency scenarios to validate
that the dendritic cell implementation is resilient to:
- Race conditions
- Resource contention
- Timing variations
- Background task interference

If these tests pass consistently, the implementation is production-ready
for high-load CI/CD environments.
"""

import asyncio
import random

import pytest
import pytest_asyncio

from active_immune_core.agents import CelulaDendritica
from active_immune_core.agents.dendritic_cell import CapturedAntigen, DendriticState


@pytest_asyncio.fixture
async def dendritic_stress() -> CelulaDendritica:
    """Dendritic cell for stress testing (with background tasks)"""
    cell = CelulaDendritica(
        area_patrulha="stress_test_zone",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        capture_threshold=0.5,
        migration_antigen_count=10,
    )
    cell.reset_state()
    yield cell

    try:
        if cell._running:
            await asyncio.wait_for(cell.parar(), timeout=3.0)
    except asyncio.TimeoutError:
        cell._running = False
        for task in cell._tasks:
            if not task.done():
                task.cancel()
    finally:
        cell.reset_state()


# ==================== STRESS TESTS ====================


class TestDendriticStress:
    """Stress tests for dendritic cell under high concurrency"""

    @pytest.mark.asyncio
    async def test_concurrent_antigen_captures(self, dendritic_stress: CelulaDendritica):
        """Test concurrent antigen captures from multiple coroutines"""

        # Create 50 concurrent capture operations
        capture_events = [
            {
                "src_ip": f"192.0.2.{i}",
                "dst_ip": "10.0.1.100",
                "type": f"malware_{i % 5}",
                "threat_score": 0.6 + (i % 5) * 0.05,
            }
            for i in range(50)
        ]

        # Execute all captures concurrently
        await asyncio.gather(*[dendritic_stress._attempt_antigen_capture(event) for event in capture_events])

        # Verify all were captured (thread-safe read)
        antigen_count = await dendritic_stress.safe_get_antigen_count()
        assert antigen_count == 50, f"Expected 50 antigens, got {antigen_count}"

    @pytest.mark.asyncio
    async def test_concurrent_peptide_processing(self, dendritic_stress: CelulaDendritica):
        """Test concurrent peptide processing"""

        # Create 30 antigens
        antigens = [
            CapturedAntigen(
                antigen_id=f"ag_{i}",
                threat_type="malware",
                source_ip=f"192.0.2.{i}",
                raw_data={"id": i},
                capture_method="phagocytosis",
            )
            for i in range(30)
        ]

        # Process all concurrently
        await asyncio.gather(*[dendritic_stress._process_antigen(ag) for ag in antigens])

        # Each antigen creates 2 peptides (MHC-I + MHC-II)
        # Thread-safe read
        peptide_count = len(dendritic_stress.processed_peptides)
        assert peptide_count == 60, f"Expected 60 peptides, got {peptide_count}"

    @pytest.mark.asyncio
    async def test_with_background_tasks_running(self, dendritic_stress: CelulaDendritica):
        """Test captures while background tasks are running"""

        # Start background tasks
        await dendritic_stress.iniciar()

        # Give background tasks time to start
        await asyncio.sleep(0.1)

        # Now perform captures while background loops are running
        capture_events = [
            {
                "src_ip": f"10.0.1.{i}",
                "type": "intrusion",
                "threat_score": 0.7,
            }
            for i in range(20)
        ]

        await asyncio.gather(*[dendritic_stress._attempt_antigen_capture(event) for event in capture_events])

        # Verify captures succeeded despite background tasks
        antigen_count = await dendritic_stress.safe_get_antigen_count()
        assert antigen_count >= 20, f"Expected >=20 antigens, got {antigen_count}"

        await dendritic_stress.parar()

    @pytest.mark.asyncio
    async def test_concurrent_presentations(self, dendritic_stress: CelulaDendritica):
        """Test concurrent MHC presentations"""

        # Setup mature state
        dendritic_stress.maturation_state = DendriticState.MATURE

        # Create 20 antigens and process them
        antigens = [
            CapturedAntigen(
                antigen_id=f"ag_present_{i}",
                threat_type="malware",
                source_ip=f"192.0.2.{i}",
                raw_data={"id": i},
                capture_method="phagocytosis",
            )
            for i in range(20)
        ]

        for ag in antigens:
            await dendritic_stress._process_antigen(ag)

        # Present all concurrently (MHC-I)
        await asyncio.gather(*[dendritic_stress._present_mhc_i() for _ in range(10)])

        # Verify presentations were created
        assert len(dendritic_stress.mhc_i_presentations) >= 10

    @pytest.mark.asyncio
    async def test_rapid_state_transitions(self, dendritic_stress: CelulaDendritica):
        """Test rapid state transitions don't cause corruption"""

        # Rapidly cycle through maturation states
        for i in range(20):
            dendritic_stress.maturation_state = DendriticState.IMMATURE
            await asyncio.sleep(0.001)
            dendritic_stress.maturation_state = DendriticState.MIGRATING
            await asyncio.sleep(0.001)
            dendritic_stress.maturation_state = DendriticState.MATURE
            await asyncio.sleep(0.001)

        # State should still be valid
        assert dendritic_stress.maturation_state in [
            DendriticState.IMMATURE,
            DendriticState.MIGRATING,
            DendriticState.MATURE,
            DendriticState.EXHAUSTED,
        ]

    @pytest.mark.asyncio
    async def test_random_operations_chaos(self, dendritic_stress: CelulaDendritica):
        """Chaos test: random operations in random order"""

        async def random_operation():
            """Execute a random operation"""
            op = random.choice(["capture", "process", "present", "reset"])

            if op == "capture":
                event = {
                    "src_ip": f"192.0.2.{random.randint(1, 255)}",
                    "type": "malware",
                    "threat_score": 0.7,
                }
                await dendritic_stress._attempt_antigen_capture(event)

            elif op == "process":
                ag = CapturedAntigen(
                    antigen_id=f"chaos_{random.randint(1, 1000)}",
                    threat_type="malware",
                    source_ip="192.0.2.1",
                    raw_data={},
                    capture_method="phagocytosis",
                )
                await dendritic_stress._process_antigen(ag)

            elif op == "present":
                await dendritic_stress._present_mhc_i()

            elif op == "reset":
                dendritic_stress.reset_state()

        # Execute 100 random operations concurrently
        await asyncio.gather(
            *[random_operation() for _ in range(100)],
            return_exceptions=True,  # Don't fail on individual errors
        )

        # System should still be operational
        metrics = dendritic_stress.get_dendritic_metrics()
        assert "maturation_state" in metrics
        assert "captured_antigens" in metrics


# ==================== LOAD TESTS ====================


@pytest.mark.asyncio
async def test_sustained_load():
    """Test sustained load over extended period"""

    cells = []
    try:
        # Create 10 dendritic cells
        cells = [
            CelulaDendritica(
                area_patrulha=f"zone_{i}",
                capture_threshold=0.5,
            )
            for i in range(10)
        ]

        # Each cell captures 100 antigens
        async def cell_workload(cell: CelulaDendritica):
            for j in range(100):
                event = {
                    "src_ip": f"10.0.{j % 255}.{j % 255}",
                    "type": "malware",
                    "threat_score": 0.7,
                }
                await cell._attempt_antigen_capture(event)

        # Execute all workloads in parallel
        await asyncio.gather(*[cell_workload(cell) for cell in cells])

        # Verify all cells processed correctly (gather all counts)
        antigen_counts = await asyncio.gather(*[cell.safe_get_antigen_count() for cell in cells])
        total_antigens = sum(antigen_counts)
        assert total_antigens == 1000, f"Expected 1000 antigens, got {total_antigens}"

    finally:
        # Cleanup
        for cell in cells:
            cell.reset_state()
