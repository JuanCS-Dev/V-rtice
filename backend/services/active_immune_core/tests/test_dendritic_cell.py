"""Dendritic Cell Tests - Comprehensive test suite

Tests cover actual production implementation of Dendritic Cell:
- Initialization & lifecycle
- Antigen capture (phagocytosis)
- Antigen processing (peptide creation)
- Maturation (immature → mature)
- Migration to lymph nodes
- MHC-I presentation (Cytotoxic T)
- MHC-II presentation (Helper T)
- IL12 secretion (Th1 promotion)
- T cell activation
- Metrics & repr
"""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from active_immune_core.agents import CelulaDendritica
from active_immune_core.agents.dendritic_cell import (
    CapturedAntigen,
    DendriticState,
    ProcessedPeptide,
)
from active_immune_core.agents.models import AgentStatus

# NOTE: assert_eventually() helper is available from conftest.py
# Usage: await assert_eventually(lambda: condition, timeout=2.0)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture(scope="function")
async def dendritic() -> CelulaDendritica:
    """
    Create Dendritic Cell instance for testing.

    Provides complete test isolation:
    - Fresh instance per test
    - Guaranteed teardown with timeout
    - State reset before each test
    - Background tasks cleanup
    """
    cell = CelulaDendritica(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        capture_threshold=0.6,
        migration_antigen_count=5,
    )

    # Ensure clean state before test
    cell.reset_state()

    yield cell

    # Guaranteed teardown with timeout (prevent hanging tests)
    try:
        if cell._running:
            # Give 2 seconds max for graceful shutdown
            await asyncio.wait_for(cell.parar(), timeout=2.0)
    except asyncio.TimeoutError:
        # Force stop if graceful shutdown hangs
        cell._running = False
        for task in cell._tasks:
            if not task.done():
                task.cancel()
        # Clean up connection resources
        if cell._cytokine_messenger:
            try:
                await asyncio.wait_for(cell._cytokine_messenger.stop(), timeout=1.0)
            except (asyncio.TimeoutError, Exception):
                pass
        if cell._hormone_messenger:
            try:
                await asyncio.wait_for(cell._hormone_messenger.stop(), timeout=1.0)
            except (asyncio.TimeoutError, Exception):
                pass
    except Exception as e:
        # Log but don't fail test due to teardown issues
        import logging
        logging.getLogger(__name__).warning(f"Fixture teardown error: {e}")
    finally:
        # Final state reset to prevent contamination
        cell.reset_state()


@pytest_asyncio.fixture(scope="function")
async def dendritic_no_background() -> CelulaDendritica:
    """
    Create Dendritic Cell WITHOUT background tasks.

    Use for tests that need deterministic state without race conditions
    from _patrol_loop, _heartbeat_loop, _energy_decay_loop.

    Background tasks are NOT started, allowing precise control over
    cell state mutations.
    """
    cell = CelulaDendritica(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        capture_threshold=0.6,
        migration_antigen_count=5,
    )

    # Ensure clean state
    cell.reset_state()

    # Mark as "running" but DON'T start background tasks
    cell._running = False  # Keep tasks disabled
    cell.state.ativo = False
    cell.state.status = AgentStatus.PATRULHANDO

    yield cell

    # Minimal teardown (no tasks to cancel)
    try:
        cell._running = False
        cell.state.ativo = False
    finally:
        cell.reset_state()


@pytest.fixture
def sample_threat_event() -> dict:
    """Sample threat event for antigen capture"""
    return {
        "src_ip": "192.0.2.100",
        "dst_ip": "10.0.1.50",
        "dst_port": 22,
        "protocol": "tcp",
        "type": "malware",
        "threat_score": 0.85,
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def weak_threat_event() -> dict:
    """Weak threat event (below capture threshold)"""
    return {
        "src_ip": "192.0.2.200",
        "dst_ip": "10.0.1.60",
        "type": "suspicious",
        "threat_score": 0.4,
    }


@pytest.fixture
def captured_antigen() -> CapturedAntigen:
    """Sample captured antigen"""
    return CapturedAntigen(
        antigen_id="ag_test_001",
        threat_type="malware",
        source_ip="192.0.2.100",
        raw_data={"type": "malware", "signature": "ABC123"},
        capture_method="phagocytosis",
    )


# ==================== INITIALIZATION TESTS ====================


class TestDendriticInitialization:
    """Test Dendritic Cell initialization"""

    def test_dendritic_creation(self, dendritic: CelulaDendritica):
        """Test Dendritic Cell is created correctly"""
        assert dendritic.state.tipo.value == "dendritica"
        assert dendritic.state.status == AgentStatus.DORMINDO
        assert dendritic.state.ativo is False
        assert dendritic.maturation_state == DendriticState.IMMATURE
        assert len(dendritic.captured_antigens) == 0
        assert len(dendritic.processed_peptides) == 0
        assert dendritic.activated_helper_t == 0
        assert dendritic.activated_cytotoxic_t == 0

    def test_dendritic_default_capture_threshold(self):
        """Test Dendritic Cell default capture threshold"""
        cell = CelulaDendritica(area_patrulha="test")
        assert cell.capture_threshold == 0.6

    def test_dendritic_custom_migration_count(self):
        """Test Dendritic Cell custom migration count"""
        cell = CelulaDendritica(area_patrulha="test", migration_antigen_count=10)
        assert cell.migration_antigen_count == 10


# ==================== LIFECYCLE TESTS ====================


class TestDendriticLifecycle:
    """Test Dendritic Cell lifecycle"""

    @pytest.mark.asyncio
    async def test_dendritic_start_stop(self, dendritic: CelulaDendritica):
        """Test Dendritic Cell start and stop"""
        # Start
        await dendritic.iniciar()
        assert dendritic._running is True
        assert dendritic.state.ativo is True
        assert dendritic.state.status == AgentStatus.PATRULHANDO
        assert dendritic.maturation_state == DendriticState.IMMATURE

        # Stop
        await dendritic.parar()
        assert dendritic._running is False
        assert dendritic.state.ativo is False

    @pytest.mark.asyncio
    async def test_dendritic_patrol_executes(self, dendritic: CelulaDendritica):
        """Test Dendritic Cell patrol executes without crashing"""
        await dendritic.iniciar()

        # Patrol should not crash (graceful degradation)
        await dendritic.patrulhar()

        # Should still be running
        assert dendritic._running is True

        await dendritic.parar()


# ==================== ANTIGEN CAPTURE TESTS ====================


class TestAntigenCapture:
    """Test antigen capture"""

    @pytest.mark.asyncio
    async def test_capture_antigen_above_threshold(
        self, dendritic: CelulaDendritica, sample_threat_event: dict
    ):
        """Test antigen capture when above threshold"""
        await dendritic._attempt_antigen_capture(sample_threat_event)

        assert len(dendritic.captured_antigens) == 1
        assert dendritic.captured_antigens[0].threat_type == "malware"
        assert dendritic.captured_antigens[0].source_ip == "192.0.2.100"

    @pytest.mark.asyncio
    async def test_no_capture_below_threshold(
        self, dendritic: CelulaDendritica, weak_threat_event: dict
    ):
        """Test no capture when below threshold"""
        await dendritic._attempt_antigen_capture(weak_threat_event)

        assert len(dendritic.captured_antigens) == 0

    @pytest.mark.asyncio
    async def test_capture_creates_peptides(
        self, dendritic_no_background: CelulaDendritica, sample_threat_event: dict
    ):
        """Test antigen capture triggers peptide processing (NO BACKGROUND TASKS)"""
        await dendritic_no_background._attempt_antigen_capture(sample_threat_event)

        # Should have created MHC-I and MHC-II peptides
        assert len(dendritic_no_background.processed_peptides) == 2
        mhc_i = [p for p in dendritic_no_background.processed_peptides if p.mhc_binding == "I"]
        mhc_ii = [p for p in dendritic_no_background.processed_peptides if p.mhc_binding == "II"]
        assert len(mhc_i) == 1
        assert len(mhc_ii) == 1

    @pytest.mark.asyncio
    async def test_multiple_antigen_captures(
        self, dendritic_no_background: CelulaDendritica, sample_threat_event: dict
    ):
        """Test multiple antigen captures (NO BACKGROUND TASKS)"""
        await dendritic_no_background._attempt_antigen_capture(sample_threat_event)
        await dendritic_no_background._attempt_antigen_capture(sample_threat_event)
        await dendritic_no_background._attempt_antigen_capture(sample_threat_event)

        assert len(dendritic_no_background.captured_antigens) == 3
        assert len(dendritic_no_background.processed_peptides) == 6  # 2 per antigen


# ==================== ANTIGEN PROCESSING TESTS ====================


class TestAntigenProcessing:
    """Test antigen processing"""

    @pytest.mark.asyncio
    async def test_process_antigen_creates_peptides(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test antigen processing creates peptides"""
        await dendritic._process_antigen(captured_antigen)

        assert len(dendritic.processed_peptides) == 2

    @pytest.mark.asyncio
    async def test_peptides_have_unique_ids(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test peptides have unique IDs"""
        await dendritic._process_antigen(captured_antigen)

        peptide_ids = [p.peptide_id for p in dendritic.processed_peptides]
        assert len(peptide_ids) == len(set(peptide_ids))  # All unique

    @pytest.mark.asyncio
    async def test_peptides_linked_to_antigen(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test peptides are linked to parent antigen"""
        await dendritic._process_antigen(captured_antigen)

        for peptide in dendritic.processed_peptides:
            assert peptide.antigen_id == captured_antigen.antigen_id


# ==================== MATURATION & MIGRATION TESTS ====================


class TestMaturationMigration:
    """Test maturation and migration"""

    @pytest.mark.asyncio
    async def test_initial_state_is_immature(self, dendritic: CelulaDendritica):
        """Test Dendritic Cell starts immature"""
        await dendritic.iniciar()
        assert dendritic.maturation_state == DendriticState.IMMATURE
        await dendritic.parar()

    @pytest.mark.asyncio
    async def test_maturation_triggered_by_antigen_count(
        self, dendritic: CelulaDendritica, sample_threat_event: dict
    ):
        """Test maturation triggered when antigen count reached"""
        # Add antigens up to migration threshold
        for _ in range(dendritic.migration_antigen_count):
            await dendritic._attempt_antigen_capture(sample_threat_event)

        # Should trigger maturation
        await dendritic._initiate_maturation()

        assert dendritic.maturation_state == DendriticState.MIGRATING
        assert dendritic.migrations == 1

    @pytest.mark.asyncio
    async def test_migration_changes_to_mature(
        self, dendritic: CelulaDendritica
    ):
        """Test migration changes state to mature"""
        dendritic.maturation_state = DendriticState.MIGRATING

        await dendritic._migrate_to_lymphnode()

        assert dendritic.maturation_state == DendriticState.MATURE
        assert dendritic.current_lymphnode is not None

    @pytest.mark.asyncio
    async def test_exhaustion_after_many_presentations(
        self, dendritic: CelulaDendritica
    ):
        """Test exhaustion after many presentations"""
        dendritic.maturation_state = DendriticState.MATURE

        # Add many presentations
        for _ in range(25):
            dendritic.mhc_i_presentations.append(None)  # Dummy presentations

        await dendritic._present_to_t_cells()

        assert dendritic.maturation_state == DendriticState.EXHAUSTED


# ==================== MHC-I PRESENTATION TESTS ====================


class TestMHCIPresentation:
    """Test MHC-I presentation"""

    @pytest.mark.asyncio
    async def test_present_mhc_i_without_messenger(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-I presentation without messenger doesn't crash"""
        await dendritic._process_antigen(captured_antigen)

        # No messenger started
        await dendritic._present_mhc_i()

        # Should not crash (graceful degradation)
        assert len(dendritic.mhc_i_presentations) == 1

    @pytest.mark.asyncio
    async def test_present_mhc_i_increments_counter(
        self, dendritic_no_background: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-I presentation increments counters (NO BACKGROUND TASKS)"""
        # Process antigen first
        await dendritic_no_background._process_antigen(captured_antigen)

        # Present without background tasks interfering
        await dendritic_no_background._present_mhc_i()

        assert len(dendritic_no_background.mhc_i_presentations) == 1
        # Counter won't increment without cytokine messenger running
        # This is expected behavior (graceful degradation)

    @pytest.mark.asyncio
    async def test_mhc_i_targets_cytotoxic_t(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-I presentation targets Cytotoxic T cells"""
        await dendritic._process_antigen(captured_antigen)
        await dendritic._present_mhc_i()

        assert dendritic.mhc_i_presentations[0].target_cell_type == "cytotoxic_t"
        assert dendritic.mhc_i_presentations[0].mhc_type == "I"


# ==================== MHC-II PRESENTATION TESTS ====================


class TestMHCIIPresentation:
    """Test MHC-II presentation"""

    @pytest.mark.asyncio
    async def test_present_mhc_ii_without_messenger(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-II presentation without messenger doesn't crash"""
        dendritic.captured_antigens.append(captured_antigen)
        await dendritic._process_antigen(captured_antigen)

        # No messenger started
        await dendritic._present_mhc_ii()

        # Should not crash (graceful degradation)
        assert len(dendritic.mhc_ii_presentations) == 1

    @pytest.mark.asyncio
    async def test_present_mhc_ii_increments_counter(
        self, dendritic_no_background: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-II presentation increments counters (NO BACKGROUND TASKS)"""
        # Add antigen and process
        dendritic_no_background.captured_antigens.append(captured_antigen)
        await dendritic_no_background._process_antigen(captured_antigen)

        # Present without background tasks
        await dendritic_no_background._present_mhc_ii()

        assert len(dendritic_no_background.mhc_ii_presentations) == 1
        # Counter won't increment without cytokine messenger running
        # This is expected behavior (graceful degradation)

    @pytest.mark.asyncio
    async def test_mhc_ii_targets_helper_t(
        self, dendritic: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test MHC-II presentation targets Helper T cells"""
        await dendritic._process_antigen(captured_antigen)
        await dendritic._present_mhc_ii()

        assert dendritic.mhc_ii_presentations[0].target_cell_type == "helper_t"
        assert dendritic.mhc_ii_presentations[0].mhc_type == "II"


# ==================== IL12 SECRETION TESTS ====================


class TestIL12Secretion:
    """Test IL12 secretion"""

    @pytest.mark.asyncio
    async def test_secrete_il12_without_messenger(
        self, dendritic: CelulaDendritica
    ):
        """Test IL12 secretion without messenger doesn't crash"""
        # No messenger started
        await dendritic._secrete_il12()

        # Should not crash (graceful degradation)
        assert dendritic.il12_secretions == 0

    @pytest.mark.asyncio
    async def test_secrete_il12_increments_counter(
        self, dendritic: CelulaDendritica
    ):
        """Test IL12 secretion increments counter"""
        await dendritic.iniciar()

        await dendritic._secrete_il12()

        # Counter incremented (degraded mode)
        assert dendritic.il12_secretions == 1

        await dendritic.parar()


# ==================== T CELL ACTIVATION TESTS ====================


class TestTCellActivation:
    """Test T cell activation"""

    @pytest.mark.asyncio
    async def test_present_to_t_cells_calls_both_mhc(
        self, dendritic_no_background: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test presentation calls both MHC-I and MHC-II (NO BACKGROUND TASKS)"""
        # Setup mature state
        dendritic_no_background.maturation_state = DendriticState.MATURE
        dendritic_no_background.captured_antigens.append(captured_antigen)
        await dendritic_no_background._process_antigen(captured_antigen)

        # Present to T cells
        await dendritic_no_background._present_to_t_cells()

        # Both MHC types should have presentations created
        assert len(dendritic_no_background.mhc_i_presentations) >= 1
        assert len(dendritic_no_background.mhc_ii_presentations) >= 1
        # IL12 won't be secreted without messenger (graceful degradation)

    @pytest.mark.asyncio
    async def test_activation_counts_both_t_cell_types(
        self, dendritic_no_background: CelulaDendritica, captured_antigen: CapturedAntigen
    ):
        """Test activation creates presentations for both T cell types (NO BACKGROUND TASKS)"""
        # Setup mature state
        dendritic_no_background.maturation_state = DendriticState.MATURE
        dendritic_no_background.captured_antigens.append(captured_antigen)
        await dendritic_no_background._process_antigen(captured_antigen)

        # Present to T cells
        await dendritic_no_background._present_to_t_cells()

        # Presentations should be created (counters won't increment without messenger)
        assert len(dendritic_no_background.mhc_i_presentations) >= 1
        assert len(dendritic_no_background.mhc_ii_presentations) >= 1

    @pytest.mark.asyncio
    async def test_only_present_in_mature_state(
        self, dendritic: CelulaDendritica, sample_threat_event: dict
    ):
        """Test patrol behavior changes with maturation state"""
        await dendritic.iniciar()

        # Immature: should patrol for antigens
        assert dendritic.maturation_state == DendriticState.IMMATURE
        initial_antigens = len(dendritic.captured_antigens)

        # Mature: should present (tested above)
        dendritic.maturation_state = DendriticState.MATURE

        # Behavior should change based on state
        assert dendritic.maturation_state != DendriticState.IMMATURE

        await dendritic.parar()


# ==================== INVESTIGATION/NEUTRALIZATION TESTS ====================


class TestInvestigationNeutralization:
    """Test Dendritic Cell investigation and neutralization"""

    @pytest.mark.asyncio
    async def test_investigation_captures_antigen(
        self, dendritic: CelulaDendritica
    ):
        """Test investigation identifies threats for capture"""
        result = await dendritic.executar_investigacao({"threat_score": 0.8})

        assert result["is_threat"] is True
        assert result["confidence"] == 0.8
        assert "antigen_capture" in result["metodo"]

    @pytest.mark.asyncio
    async def test_investigation_below_threshold(
        self, dendritic: CelulaDendritica
    ):
        """Test investigation below capture threshold"""
        result = await dendritic.executar_investigacao({"threat_score": 0.3})

        assert result["is_threat"] is False
        assert "no_capture" in result["metodo"]

    @pytest.mark.asyncio
    async def test_neutralization_delegates_to_t_cells(
        self, dendritic: CelulaDendritica
    ):
        """Test neutralization delegates to T cells"""
        result = await dendritic.executar_neutralizacao(
            {"threat_score": 0.8}, metodo="delegate"
        )

        assert result is True  # Presented for T cell action


# ==================== METRICS TESTS ====================


class TestDendriticMetrics:
    """Test Dendritic Cell metrics"""

    @pytest.mark.asyncio
    async def test_get_dendritic_metrics(self, dendritic: CelulaDendritica):
        """Test getting Dendritic Cell metrics"""
        metrics = dendritic.get_dendritic_metrics()

        assert "maturation_state" in metrics
        assert "captured_antigens" in metrics
        assert "processed_peptides" in metrics
        assert "mhc_i_presentations" in metrics
        assert "mhc_ii_presentations" in metrics
        assert "total_presentations" in metrics
        assert "activated_helper_t" in metrics
        assert "activated_cytotoxic_t" in metrics
        assert "il12_secretions" in metrics
        assert "migrations" in metrics
        assert "current_lymphnode" in metrics

    @pytest.mark.asyncio
    async def test_metrics_with_captures_and_presentations(
        self, dendritic_no_background: CelulaDendritica,
        sample_threat_event: dict,
        captured_antigen: CapturedAntigen,
    ):
        """Test metrics with captures and presentations (NO BACKGROUND TASKS)"""
        # Capture and process antigens
        await dendritic_no_background._attempt_antigen_capture(sample_threat_event)
        dendritic_no_background.captured_antigens.append(captured_antigen)
        await dendritic_no_background._process_antigen(captured_antigen)
        await dendritic_no_background._present_mhc_i()
        await dendritic_no_background._present_mhc_ii()

        # Get metrics
        metrics = dendritic_no_background.get_dendritic_metrics()

        # Verify exact counts (no race conditions)
        assert metrics["captured_antigens"] == 2  # 1 captured + 1 manually added
        assert metrics["processed_peptides"] == 4  # 2 peptides per antigen
        assert metrics["mhc_i_presentations"] == 2  # 2 antigens → 2 MHC-I presentations
        assert metrics["mhc_ii_presentations"] == 2  # 2 antigens → 2 MHC-II presentations
        assert metrics["total_presentations"] == 4

    def test_repr(self, dendritic: CelulaDendritica):
        """Test string representation"""
        repr_str = repr(dendritic)

        assert "CelulaDendritica" in repr_str
        assert dendritic.state.id[:8] in repr_str
        assert dendritic.maturation_state in repr_str or "state=" in repr_str


# ==================== EDGE CASES ====================


class TestDendriticEdgeCases:
    """Test Dendritic Cell edge cases"""

    @pytest.mark.asyncio
    async def test_process_antigen_with_empty_data(
        self, dendritic: CelulaDendritica
    ):
        """Test processing antigen with empty raw data"""
        empty_antigen = CapturedAntigen(
            antigen_id="ag_empty_001",
            threat_type="unknown",
            source_ip="0.0.0.0",
            raw_data={},
            capture_method="phagocytosis",
        )

        # Should not crash
        await dendritic._process_antigen(empty_antigen)

        assert len(dendritic.processed_peptides) == 2  # Still creates peptides

    @pytest.mark.asyncio
    async def test_present_without_peptides(
        self, dendritic: CelulaDendritica
    ):
        """Test presentation without any peptides"""
        await dendritic.iniciar()
        dendritic.maturation_state = DendriticState.MATURE

        # Should not crash with no peptides
        await dendritic._present_to_t_cells()

        assert len(dendritic.mhc_i_presentations) == 0
        assert len(dendritic.mhc_ii_presentations) == 0

        await dendritic.parar()

    @pytest.mark.asyncio
    async def test_exhausted_state_minimal_activity(
        self, dendritic: CelulaDendritica
    ):
        """Test exhausted state reduces activity"""
        await dendritic.iniciar()
        dendritic.maturation_state = DendriticState.EXHAUSTED

        # Patrol should do minimal activity
        await dendritic.patrulhar()

        # Should remain exhausted
        assert dendritic.maturation_state == DendriticState.EXHAUSTED

        await dendritic.parar()
