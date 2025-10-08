"""Helper T Cell Tests - Comprehensive test suite

Tests cover actual production implementation of Helper T Cell:
- Initialization & lifecycle
- Antigen recognition via MHC-II
- Differentiation (Th1, Th2, Th17)
- B cell activation (IL4, IL5)
- Cytotoxic T activation (IL2, IFN-gamma)
- Macrophage activation (IFN-gamma)
- Neutrophil activation (IL17)
- Multi-cytokine orchestration
- Metrics & repr
"""

import pytest
import pytest_asyncio

from active_immune_core.agents import LinfocitoTAuxiliar
from active_immune_core.agents.helper_t_cell import (
    AntigenPresentation,
    HelperTState,
)
from active_immune_core.agents.models import AgentStatus

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def helper_t() -> LinfocitoTAuxiliar:
    """Create Helper T Cell instance for testing"""
    cell = LinfocitoTAuxiliar(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        activation_threshold=0.75,
    )
    yield cell
    if cell._running:
        await cell.parar()


@pytest.fixture
def sample_antigen_virus() -> AntigenPresentation:
    """Sample viral antigen presentation (Th1)"""
    return AntigenPresentation(
        presentation_id="ag_virus_001",
        antigen_type="virus",
        mhc_ii_complex={
            "peptide": "MALWARE_SIGNATURE_ABC",
            "hla_dr": "DR1",
        },
        dendritic_cell_id="dc_001",
        confidence=0.85,
    )


@pytest.fixture
def sample_antigen_parasite() -> AntigenPresentation:
    """Sample parasite antigen presentation (Th2)"""
    return AntigenPresentation(
        presentation_id="ag_parasite_001",
        antigen_type="parasite",
        mhc_ii_complex={
            "peptide": "DDOS_PATTERN_XYZ",
            "hla_dr": "DR4",
        },
        dendritic_cell_id="dc_002",
        confidence=0.80,
    )


@pytest.fixture
def sample_antigen_bacterial() -> AntigenPresentation:
    """Sample bacterial antigen presentation (Th17)"""
    return AntigenPresentation(
        presentation_id="ag_bacterial_001",
        antigen_type="bacterial_intrusion",
        mhc_ii_complex={
            "peptide": "INTRUSION_PATTERN_123",
            "hla_dr": "DR3",
        },
        dendritic_cell_id="dc_003",
        confidence=0.90,
    )


# ==================== INITIALIZATION TESTS ====================


class TestHelperTInitialization:
    """Test Helper T Cell initialization"""

    def test_helper_t_creation(self, helper_t: LinfocitoTAuxiliar):
        """Test Helper T Cell is created correctly"""
        assert helper_t.state.tipo.value == "linfocito_t_auxiliar"
        assert helper_t.state.status == AgentStatus.DORMINDO
        assert helper_t.state.ativo is False
        assert helper_t.differentiation_state == HelperTState.NAIVE
        assert len(helper_t.recognized_antigens) == 0
        assert len(helper_t.activation_signals) == 0
        assert helper_t.activated_b_cells == 0
        assert helper_t.activated_cytotoxic_t == 0

    def test_helper_t_default_activation_threshold(self):
        """Test Helper T Cell default activation threshold"""
        cell = LinfocitoTAuxiliar(area_patrulha="test")
        assert cell.activation_threshold == 0.75

    def test_helper_t_custom_activation_threshold(self):
        """Test Helper T Cell custom activation threshold"""
        cell = LinfocitoTAuxiliar(area_patrulha="test", activation_threshold=0.9)
        assert cell.activation_threshold == 0.9


# ==================== LIFECYCLE TESTS ====================


class TestHelperTLifecycle:
    """Test Helper T Cell lifecycle"""

    @pytest.mark.asyncio
    async def test_helper_t_start_stop(self, helper_t: LinfocitoTAuxiliar):
        """Test Helper T Cell start and stop"""
        # Start
        await helper_t.iniciar()
        assert helper_t._running is True
        assert helper_t.state.ativo is True
        assert helper_t.state.status == AgentStatus.PATRULHANDO

        # Stop
        await helper_t.parar()
        assert helper_t._running is False
        assert helper_t.state.ativo is False

    @pytest.mark.asyncio
    async def test_helper_t_patrol_executes(self, helper_t: LinfocitoTAuxiliar):
        """Test Helper T Cell patrol executes without crashing"""
        await helper_t.iniciar()

        # Patrol should not crash (graceful degradation)
        await helper_t.patrulhar()

        # Should still be running
        assert helper_t._running is True

        await helper_t.parar()


# ==================== ANTIGEN RECOGNITION TESTS ====================


class TestAntigenRecognition:
    """Test antigen recognition and handling"""

    @pytest.mark.asyncio
    async def test_handle_antigen_presentation(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test handling antigen presentation"""
        await helper_t._handle_antigen_presentation(
            {
                "presentation_id": sample_antigen_virus.presentation_id,
                "antigen_type": sample_antigen_virus.antigen_type,
                "mhc_ii_complex": sample_antigen_virus.mhc_ii_complex,
                "dendritic_cell_id": sample_antigen_virus.dendritic_cell_id,
                "confidence": sample_antigen_virus.confidence,
            }
        )

        assert len(helper_t.recognized_antigens) == 1
        assert helper_t.recognized_antigens[0].antigen_type == "virus"

    @pytest.mark.asyncio
    async def test_activation_threshold_met(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test activation when confidence meets threshold"""
        await helper_t._handle_antigen_presentation(
            {
                "presentation_id": sample_antigen_virus.presentation_id,
                "antigen_type": sample_antigen_virus.antigen_type,
                "mhc_ii_complex": sample_antigen_virus.mhc_ii_complex,
                "dendritic_cell_id": sample_antigen_virus.dendritic_cell_id,
                "confidence": 0.85,  # Above threshold (0.75)
            }
        )

        # Should activate
        assert helper_t.differentiation_state != HelperTState.NAIVE

    @pytest.mark.asyncio
    async def test_activation_threshold_not_met(self, helper_t: LinfocitoTAuxiliar):
        """Test no activation when confidence below threshold"""
        await helper_t._handle_antigen_presentation(
            {
                "presentation_id": "ag_weak_001",
                "antigen_type": "weak_threat",
                "mhc_ii_complex": {},
                "dendritic_cell_id": "dc_001",
                "confidence": 0.5,  # Below threshold (0.75)
            }
        )

        # Should not activate
        assert helper_t.differentiation_state == HelperTState.NAIVE
        assert len(helper_t.recognized_antigens) == 1  # Stored but not activated

    @pytest.mark.asyncio
    async def test_multiple_antigen_presentations(
        self,
        helper_t: LinfocitoTAuxiliar,
        sample_antigen_virus: AntigenPresentation,
        sample_antigen_parasite: AntigenPresentation,
    ):
        """Test handling multiple antigen presentations"""
        await helper_t._handle_antigen_presentation(sample_antigen_virus.model_dump())
        await helper_t._handle_antigen_presentation(sample_antigen_parasite.model_dump())

        assert len(helper_t.recognized_antigens) == 2


# ==================== DIFFERENTIATION TESTS ====================


class TestDifferentiation:
    """Test Helper T Cell differentiation"""

    @pytest.mark.asyncio
    async def test_initial_state_is_naive(self):
        """Test Helper T Cell starts in naive state"""
        cell = LinfocitoTAuxiliar(area_patrulha="test")
        assert cell.differentiation_state == HelperTState.NAIVE

    @pytest.mark.asyncio
    async def test_differentiate_to_th1(self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation):
        """Test differentiation to Th1 (virus/intracellular)"""
        await helper_t._determine_differentiation(sample_antigen_virus)

        assert helper_t.differentiation_state == HelperTState.TH1

    @pytest.mark.asyncio
    async def test_differentiate_to_th2(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation
    ):
        """Test differentiation to Th2 (parasite/extracellular)"""
        await helper_t._determine_differentiation(sample_antigen_parasite)

        assert helper_t.differentiation_state == HelperTState.TH2

    @pytest.mark.asyncio
    async def test_differentiate_to_th17(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_bacterial: AntigenPresentation
    ):
        """Test differentiation to Th17 (bacterial/fungal)"""
        await helper_t._determine_differentiation(sample_antigen_bacterial)

        assert helper_t.differentiation_state == HelperTState.TH17


# ==================== B CELL ACTIVATION TESTS ====================


class TestBCellActivation:
    """Test B cell activation"""

    @pytest.mark.asyncio
    async def test_activate_b_cells_without_messenger(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation
    ):
        """Test B cell activation without messenger doesn't crash"""
        # No messenger started
        await helper_t._activate_b_cells(sample_antigen_parasite)

        # Should not crash (graceful degradation)
        assert helper_t.activated_b_cells == 0

    @pytest.mark.asyncio
    async def test_activate_b_cells_increments_counter(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation
    ):
        """Test B cell activation increments counters"""
        await helper_t.iniciar()

        await helper_t._activate_b_cells(sample_antigen_parasite)

        # Counters incremented (degraded mode - no actual cytokines)
        assert helper_t.activated_b_cells == 1
        assert helper_t.il4_secretions == 1
        assert helper_t.il5_secretions == 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_th2_activates_b_cells(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation
    ):
        """Test Th2 differentiation triggers B cell activation"""
        await helper_t.iniciar()

        # Set to Th2 state
        helper_t.differentiation_state = HelperTState.TH2

        await helper_t._coordinate_response(sample_antigen_parasite)

        assert helper_t.activated_b_cells >= 1

        await helper_t.parar()


# ==================== CYTOTOXIC T ACTIVATION TESTS ====================


class TestCytotoxicTActivation:
    """Test Cytotoxic T cell activation"""

    @pytest.mark.asyncio
    async def test_activate_cytotoxic_t_without_messenger(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test Cytotoxic T activation without messenger doesn't crash"""
        await helper_t._activate_cytotoxic_t_cells(sample_antigen_virus)

        # Should not crash (graceful degradation)
        assert helper_t.activated_cytotoxic_t == 0

    @pytest.mark.asyncio
    async def test_activate_cytotoxic_t_increments_counter(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test Cytotoxic T activation increments counters"""
        await helper_t.iniciar()

        await helper_t._activate_cytotoxic_t_cells(sample_antigen_virus)

        # Counters incremented (degraded mode)
        assert helper_t.activated_cytotoxic_t == 1
        assert helper_t.il2_secretions == 1
        assert helper_t.ifn_gamma_secretions >= 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_th1_activates_cytotoxic_t(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test Th1 differentiation triggers Cytotoxic T activation"""
        await helper_t.iniciar()

        # Set to Th1 state
        helper_t.differentiation_state = HelperTState.TH1

        await helper_t._coordinate_response(sample_antigen_virus)

        assert helper_t.activated_cytotoxic_t >= 1

        await helper_t.parar()


# ==================== MACROPHAGE ACTIVATION TESTS ====================


class TestMacrophageActivation:
    """Test Macrophage activation"""

    @pytest.mark.asyncio
    async def test_activate_macrophages_increments_counter(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test Macrophage activation increments counter"""
        await helper_t.iniciar()

        await helper_t._activate_macrophages(sample_antigen_virus)

        # Counter incremented (degraded mode)
        assert helper_t.activated_macrophages == 1
        assert helper_t.ifn_gamma_secretions >= 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_th1_activates_macrophages(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test Th1 differentiation triggers Macrophage activation"""
        await helper_t.iniciar()

        # Set to Th1 state
        helper_t.differentiation_state = HelperTState.TH1

        await helper_t._coordinate_response(sample_antigen_virus)

        assert helper_t.activated_macrophages >= 1

        await helper_t.parar()


# ==================== NEUTROPHIL ACTIVATION TESTS ====================


class TestNeutrophilActivation:
    """Test Neutrophil activation"""

    @pytest.mark.asyncio
    async def test_activate_neutrophils_no_crash(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_bacterial: AntigenPresentation
    ):
        """Test Neutrophil activation doesn't crash"""
        await helper_t.iniciar()

        await helper_t._activate_neutrophils(sample_antigen_bacterial)

        # Should execute without crash
        assert helper_t._running is True

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_th17_activates_neutrophils(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_bacterial: AntigenPresentation
    ):
        """Test Th17 differentiation triggers Neutrophil activation"""
        await helper_t.iniciar()

        # Set to Th17 state
        helper_t.differentiation_state = HelperTState.TH17

        await helper_t._coordinate_response(sample_antigen_bacterial)

        # Should have called neutrophil activation (no counter, but logged)
        assert helper_t._running is True

        await helper_t.parar()


# ==================== CYTOKINE SECRETION TESTS ====================


class TestCytokineSecretion:
    """Test multi-cytokine secretion"""

    @pytest.mark.asyncio
    async def test_il2_secretion(self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation):
        """Test IL2 secretion for Cytotoxic T activation"""
        await helper_t.iniciar()

        await helper_t._activate_cytotoxic_t_cells(sample_antigen_virus)

        assert helper_t.il2_secretions >= 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_il4_secretion(self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation):
        """Test IL4 secretion for B cell activation"""
        await helper_t.iniciar()

        await helper_t._activate_b_cells(sample_antigen_parasite)

        assert helper_t.il4_secretions >= 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_il5_secretion(self, helper_t: LinfocitoTAuxiliar, sample_antigen_parasite: AntigenPresentation):
        """Test IL5 secretion for B cell proliferation"""
        await helper_t.iniciar()

        await helper_t._activate_b_cells(sample_antigen_parasite)

        assert helper_t.il5_secretions >= 1

        await helper_t.parar()

    @pytest.mark.asyncio
    async def test_ifn_gamma_secretion(self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation):
        """Test IFN-gamma secretion for enhanced killing"""
        await helper_t.iniciar()

        await helper_t._activate_cytotoxic_t_cells(sample_antigen_virus)

        assert helper_t.ifn_gamma_secretions >= 1

        await helper_t.parar()


# ==================== INVESTIGATION/NEUTRALIZATION TESTS ====================


class TestInvestigationNeutralization:
    """Test Helper T Cell investigation and neutralization"""

    @pytest.mark.asyncio
    async def test_investigation_returns_coordination_only(self, helper_t: LinfocitoTAuxiliar):
        """Test Helper T doesn't investigate, only coordinates"""
        result = await helper_t.executar_investigacao({"ip": "192.0.2.100"})

        assert result["is_threat"] is False
        assert result["confidence"] == 0.0
        assert "coordination" in result["metodo"]

    @pytest.mark.asyncio
    async def test_neutralization_creates_activation_signal(self, helper_t: LinfocitoTAuxiliar):
        """Test neutralization creates activation signal for effectors"""
        result = await helper_t.executar_neutralizacao({"target_cell_type": "cytotoxic_t"}, metodo="delegate")

        assert result is True
        assert len(helper_t.activation_signals) == 1
        assert helper_t.activation_signals[0].target_cell_type == "cytotoxic_t"


# ==================== METRICS TESTS ====================


class TestHelperTMetrics:
    """Test Helper T Cell metrics"""

    @pytest.mark.asyncio
    async def test_get_helper_t_metrics(self, helper_t: LinfocitoTAuxiliar):
        """Test getting Helper T Cell metrics"""
        metrics = helper_t.get_helper_t_metrics()

        assert "differentiation_state" in metrics
        assert "recognized_antigens" in metrics
        assert "activation_signals" in metrics
        assert "activated_b_cells" in metrics
        assert "activated_cytotoxic_t" in metrics
        assert "activated_macrophages" in metrics
        assert "il2_secretions" in metrics
        assert "il4_secretions" in metrics
        assert "il5_secretions" in metrics
        assert "ifn_gamma_secretions" in metrics
        assert "total_cytokines" in metrics

    @pytest.mark.asyncio
    async def test_metrics_with_activations(
        self,
        helper_t: LinfocitoTAuxiliar,
        sample_antigen_virus: AntigenPresentation,
        sample_antigen_parasite: AntigenPresentation,
    ):
        """Test metrics with activations"""
        await helper_t.iniciar()

        await helper_t._activate_cytotoxic_t_cells(sample_antigen_virus)
        await helper_t._activate_b_cells(sample_antigen_parasite)

        metrics = helper_t.get_helper_t_metrics()

        assert metrics["activated_cytotoxic_t"] >= 1
        assert metrics["activated_b_cells"] >= 1
        assert metrics["total_cytokines"] >= 3  # IL2 + IL4 + IL5

        await helper_t.parar()

    def test_repr(self, helper_t: LinfocitoTAuxiliar):
        """Test string representation"""
        repr_str = repr(helper_t)

        assert "LinfocitoTAuxiliar" in repr_str
        assert helper_t.state.id[:8] in repr_str
        assert str(helper_t.state.status) in repr_str or helper_t.state.status.value in repr_str
        assert "state=" in repr_str


# ==================== EDGE CASES ====================


class TestHelperTEdgeCases:
    """Test Helper T Cell edge cases"""

    @pytest.mark.asyncio
    async def test_activation_with_invalid_antigen_data(self, helper_t: LinfocitoTAuxiliar):
        """Test handling invalid antigen data"""
        # Should not crash with missing fields
        await helper_t._handle_antigen_presentation({})

        assert len(helper_t.recognized_antigens) == 1  # Stored with defaults

    @pytest.mark.asyncio
    async def test_differentiation_with_unknown_antigen_type(self, helper_t: LinfocitoTAuxiliar):
        """Test differentiation with unknown antigen type"""
        unknown_antigen = AntigenPresentation(
            presentation_id="ag_unknown_001",
            antigen_type="unknown_threat",
            mhc_ii_complex={},
            dendritic_cell_id="dc_999",
            confidence=0.8,
        )

        await helper_t._determine_differentiation(unknown_antigen)

        # Should remain in current state (activated but not differentiated)
        assert helper_t.differentiation_state == HelperTState.NAIVE

    @pytest.mark.asyncio
    async def test_coordinate_response_in_naive_state(
        self, helper_t: LinfocitoTAuxiliar, sample_antigen_virus: AntigenPresentation
    ):
        """Test coordination in naive state (should not activate)"""
        await helper_t.iniciar()

        # Naive state
        assert helper_t.differentiation_state == HelperTState.NAIVE

        await helper_t._coordinate_response(sample_antigen_virus)

        # Should not activate anything in naive state
        assert helper_t.activated_b_cells == 0
        assert helper_t.activated_cytotoxic_t == 0

        await helper_t.parar()
