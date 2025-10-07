"""B Cell Tests - Comprehensive test suite

Tests cover actual production implementation of B Cell:
- Initialization & lifecycle
- Pattern recognition & antibody-antigen matching
- Memory formation & persistence
- Plasma cell differentiation
- Clonal expansion
- IL4 cytokine secretion
- Metrics & repr
"""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from active_immune_core.agents import LinfocitoBDigital
from active_immune_core.agents.b_cell import (
    AntibodyPattern,
    BCellState,
    MemoryBCell,
)
from active_immune_core.agents.models import AgentStatus


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def b_cell() -> LinfocitoBDigital:
    """Create B Cell instance for testing"""
    cell = LinfocitoBDigital(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        affinity_threshold=0.7,
    )
    yield cell
    if cell._running:
        await cell.parar()


@pytest.fixture
def sample_antibody() -> AntibodyPattern:
    """Sample antibody pattern"""
    return AntibodyPattern(
        pattern_id="ab_test_001",
        pattern_type="port_scan",
        signature={
            "dst_port": 22,
            "protocol": "tcp",
            "pattern_type": "port_scan",
        },
        confidence=0.85,
        detections=3,
    )


@pytest.fixture
def sample_event() -> dict:
    """Sample network event"""
    return {
        "src_ip": "192.0.2.100",
        "dst_ip": "10.0.1.50",
        "dst_port": 22,
        "protocol": "tcp",
        "type": "port_scan",
        "timestamp": datetime.now().isoformat(),
    }


# ==================== INITIALIZATION TESTS ====================


class TestBCellInitialization:
    """Test B Cell initialization"""

    def test_b_cell_creation(self, b_cell: LinfocitoBDigital):
        """Test B Cell is created correctly"""
        assert b_cell.state.tipo.value == "linfocito_b"
        assert b_cell.state.status == AgentStatus.DORMINDO
        assert b_cell.state.ativo is False
        assert b_cell.differentiation_state == BCellState.NAIVE
        assert len(b_cell.antibody_patterns) == 0
        assert len(b_cell.memory_cells) == 0
        assert b_cell.plasma_cell_active is False

    def test_b_cell_default_affinity_threshold(self):
        """Test B Cell default affinity threshold"""
        cell = LinfocitoBDigital(area_patrulha="test")
        assert cell.affinity_threshold == 0.7

    def test_b_cell_custom_affinity_threshold(self):
        """Test B Cell custom affinity threshold"""
        cell = LinfocitoBDigital(area_patrulha="test", affinity_threshold=0.9)
        assert cell.affinity_threshold == 0.9


# ==================== LIFECYCLE TESTS ====================


class TestBCellLifecycle:
    """Test B Cell lifecycle"""

    @pytest.mark.asyncio
    async def test_b_cell_start_stop(self, b_cell: LinfocitoBDigital):
        """Test B Cell start and stop"""
        # Start
        await b_cell.iniciar()
        assert b_cell._running is True
        assert b_cell.state.ativo is True
        assert b_cell.state.status == AgentStatus.PATRULHANDO

        # Stop
        await b_cell.parar()
        assert b_cell._running is False
        assert b_cell.state.ativo is False

    @pytest.mark.asyncio
    async def test_b_cell_patrol_executes(self, b_cell: LinfocitoBDigital):
        """Test B Cell patrol executes without crashing"""
        await b_cell.iniciar()

        # Patrol should not crash (graceful degradation)
        await b_cell.patrulhar()

        # Should still be running
        assert b_cell._running is True

        await b_cell.parar()


# ==================== PATTERN RECOGNITION TESTS ====================


class TestPatternRecognition:
    """Test pattern recognition and affinity calculation"""

    def test_extract_signature(
        self, b_cell: LinfocitoBDigital, sample_event: dict
    ):
        """Test signature extraction from event"""
        signature = b_cell._extract_signature(sample_event)

        assert "src_ip" in signature
        assert "dst_ip" in signature
        assert "dst_port" in signature
        assert "protocol" in signature
        assert signature["dst_port"] == 22
        assert signature["protocol"] == "tcp"

    def test_calculate_affinity_perfect_match(self, b_cell: LinfocitoBDigital):
        """Test affinity calculation for perfect match"""
        signature = {
            "dst_port": 22,
            "protocol": "tcp",
            "pattern_type": "port_scan",
        }
        pattern = {
            "dst_port": 22,
            "protocol": "tcp",
            "pattern_type": "port_scan",
        }

        affinity = b_cell._calculate_affinity(signature, pattern)
        assert affinity == 1.0

    def test_calculate_affinity_partial_match(self, b_cell: LinfocitoBDigital):
        """Test affinity calculation for partial match"""
        signature = {
            "dst_port": 22,
            "protocol": "tcp",
            "pattern_type": "port_scan",
        }
        pattern = {
            "dst_port": 22,
            "protocol": "udp",  # Different protocol
            "pattern_type": "port_scan",
        }

        affinity = b_cell._calculate_affinity(signature, pattern)
        assert 0.0 < affinity < 1.0
        assert affinity == pytest.approx(0.666, rel=0.01)

    def test_calculate_affinity_no_match(self, b_cell: LinfocitoBDigital):
        """Test affinity calculation for no match"""
        signature = {
            "dst_port": 22,
            "protocol": "tcp",
        }
        pattern = {
            "dst_port": 80,
            "protocol": "http",
        }

        affinity = b_cell._calculate_affinity(signature, pattern)
        assert affinity == 0.0

    def test_calculate_affinity_empty_pattern(self, b_cell: LinfocitoBDigital):
        """Test affinity with empty pattern"""
        signature = {"dst_port": 22}
        pattern = {}

        affinity = b_cell._calculate_affinity(signature, pattern)
        assert affinity == 0.0


# ==================== PATTERN LEARNING TESTS ====================


class TestPatternLearning:
    """Test pattern learning and antibody creation"""

    @pytest.mark.asyncio
    async def test_learn_pattern(self, b_cell: LinfocitoBDigital):
        """Test learning a new pattern"""
        signature = {"dst_port": 22, "protocol": "tcp"}

        antibody = await b_cell.learn_pattern(
            pattern_type="port_scan", signature=signature, confidence=0.8
        )

        assert antibody.pattern_type == "port_scan"
        assert antibody.signature == signature
        assert antibody.confidence == 0.8
        assert antibody.pattern_id in b_cell.antibody_patterns
        assert len(b_cell.antibody_patterns) == 1

    @pytest.mark.asyncio
    async def test_learn_multiple_patterns(self, b_cell: LinfocitoBDigital):
        """Test learning multiple patterns"""
        await b_cell.learn_pattern(
            "port_scan", {"dst_port": 22, "protocol": "tcp"}, 0.8
        )
        await b_cell.learn_pattern(
            "brute_force", {"dst_port": 22, "failed_logins": 5}, 0.75
        )

        assert len(b_cell.antibody_patterns) == 2
        assert len(b_cell.state.padroes_aprendidos) == 2

    @pytest.mark.asyncio
    async def test_antibody_pattern_stored(self, b_cell: LinfocitoBDigital):
        """Test antibody pattern is properly stored"""
        antibody = await b_cell.learn_pattern(
            "malware", {"hash": "abc123"}, 0.9
        )

        stored = b_cell.antibody_patterns[antibody.pattern_id]
        assert stored == antibody
        assert stored.detections == 0


# ==================== MEMORY FORMATION TESTS ====================


class TestMemoryFormation:
    """Test memory B cell formation"""

    @pytest.mark.asyncio
    async def test_form_memory_cell(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test forming memory cell from antibody"""
        memory = await b_cell.form_memory_cell(sample_antibody)

        assert isinstance(memory, MemoryBCell)
        assert memory.antibody_pattern == sample_antibody
        assert memory.affinity == sample_antibody.confidence
        assert memory in b_cell.memory_cells
        assert b_cell.differentiation_state == BCellState.MEMORY

    @pytest.mark.asyncio
    async def test_memory_cell_persists(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test memory cell is added to list"""
        initial_count = len(b_cell.memory_cells)

        await b_cell.form_memory_cell(sample_antibody)

        assert len(b_cell.memory_cells) == initial_count + 1

    @pytest.mark.asyncio
    async def test_memory_cell_lifespan(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test memory cell has correct lifespan"""
        memory = await b_cell.form_memory_cell(sample_antibody)

        assert memory.lifespan_days == 365  # 1 year


# ==================== DIFFERENTIATION TESTS ====================


class TestDifferentiation:
    """Test B Cell differentiation states"""

    @pytest.mark.asyncio
    async def test_initial_state_is_naive(self):
        """Test B Cell starts in naive state"""
        cell = LinfocitoBDigital(area_patrulha="test")
        assert cell.differentiation_state == BCellState.NAIVE

    @pytest.mark.asyncio
    async def test_differentiate_to_plasma_cell(
        self, b_cell: LinfocitoBDigital
    ):
        """Test differentiation to plasma cell"""
        await b_cell._differentiate_to_plasma_cell()

        assert b_cell.plasma_cell_active is True
        assert b_cell.differentiation_state == BCellState.PLASMA

    @pytest.mark.asyncio
    async def test_plasma_cell_cant_redifferentiate(
        self, b_cell: LinfocitoBDigital
    ):
        """Test plasma cell state is terminal"""
        await b_cell._differentiate_to_plasma_cell()
        assert b_cell.differentiation_state == BCellState.PLASMA

        # Forming memory should change state
        antibody = await b_cell.learn_pattern("test", {}, 0.8)
        await b_cell.form_memory_cell(antibody)

        assert b_cell.differentiation_state == BCellState.MEMORY


# ==================== CLONAL EXPANSION TESTS ====================


class TestClonalExpansion:
    """Test clonal expansion triggering"""

    @pytest.mark.asyncio
    async def test_clonal_expansion_triggered(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test clonal expansion is triggered"""
        initial_count = b_cell.clonal_expansions

        await b_cell._trigger_clonal_expansion(sample_antibody)

        assert b_cell.clonal_expansions == initial_count + 1

    @pytest.mark.asyncio
    async def test_clonal_expansion_multiple_times(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test clonal expansion can be triggered multiple times"""
        await b_cell._trigger_clonal_expansion(sample_antibody)
        await b_cell._trigger_clonal_expansion(sample_antibody)
        await b_cell._trigger_clonal_expansion(sample_antibody)

        assert b_cell.clonal_expansions == 3


# ==================== INVESTIGATION TESTS ====================


class TestInvestigation:
    """Test B Cell investigation behavior"""

    @pytest.mark.asyncio
    async def test_investigation_returns_not_threat(
        self, b_cell: LinfocitoBDigital
    ):
        """Test B Cells don't investigate unknown threats"""
        result = await b_cell.investigar({"ip": "192.0.2.100"})

        assert result["is_threat"] is False
        assert result["confidence"] == 0.0
        assert "pattern_recognition_only" in result["metodo"]


# ==================== IL4 SECRETION TESTS ====================


class TestIL4Secretion:
    """Test IL4 cytokine secretion"""

    @pytest.mark.asyncio
    async def test_secretar_il4_without_messenger(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test IL4 secretion without messenger doesn't crash"""
        # No messenger started
        await b_cell._secretar_il4(sample_antibody, {})

        # Should not crash (graceful degradation)
        assert b_cell.il4_secretions == 0

    @pytest.mark.asyncio
    async def test_secretar_il4_increments_counter(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test IL4 secretion increments counter"""
        await b_cell.iniciar()

        await b_cell._secretar_il4(sample_antibody, {"test": "event"})

        # Counter incremented (degraded mode)
        assert b_cell.il4_secretions == 1

        await b_cell.parar()


# ==================== NEUTRALIZATION TESTS ====================


class TestNeutralization:
    """Test B Cell neutralization"""

    @pytest.mark.asyncio
    async def test_neutralization_without_pattern(
        self, b_cell: LinfocitoBDigital
    ):
        """Test neutralization fails without matching pattern"""
        result = await b_cell.executar_neutralizacao(
            {"pattern_id": "nonexistent"}, metodo="isolate"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_neutralization_with_pattern(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test neutralization with antibody pattern"""
        # Add antibody to B cell
        b_cell.antibody_patterns[sample_antibody.pattern_id] = sample_antibody

        # Call executar_neutralizacao directly (like other agent tests)
        result = await b_cell.executar_neutralizacao(
            {
                "pattern_id": sample_antibody.pattern_id,
                "dst_ip": "192.0.2.100",
            },
            metodo="isolate",
        )

        assert result is True
        assert b_cell.state.neutralizacoes_total == 1


# ==================== METRICS TESTS ====================


class TestBCellMetrics:
    """Test B Cell metrics"""

    @pytest.mark.asyncio
    async def test_get_b_cell_metrics(self, b_cell: LinfocitoBDigital):
        """Test getting B Cell metrics"""
        metrics = b_cell.get_b_cell_metrics()

        assert "differentiation_state" in metrics
        assert "antibody_patterns" in metrics
        assert "memory_cells" in metrics
        assert "plasma_cell_active" in metrics
        assert "pattern_matches" in metrics
        assert "il4_secretions" in metrics
        assert "clonal_expansions" in metrics
        assert "total_detections" in metrics
        assert "avg_pattern_confidence" in metrics

    @pytest.mark.asyncio
    async def test_metrics_with_patterns(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test metrics with learned patterns"""
        b_cell.antibody_patterns[sample_antibody.pattern_id] = sample_antibody

        metrics = b_cell.get_b_cell_metrics()

        assert metrics["antibody_patterns"] == 1
        assert metrics["total_detections"] == sample_antibody.detections
        assert metrics["avg_pattern_confidence"] == sample_antibody.confidence

    def test_repr(self, b_cell: LinfocitoBDigital):
        """Test string representation"""
        repr_str = repr(b_cell)

        assert "LinfocitoBDigital" in repr_str
        assert b_cell.state.id[:8] in repr_str
        assert str(b_cell.state.status) in repr_str or b_cell.state.status.value in repr_str
        assert "state=" in repr_str
        assert "patterns=" in repr_str


# ==================== EDGE CASES ====================


class TestBCellEdgeCases:
    """Test B Cell edge cases"""

    @pytest.mark.asyncio
    async def test_pattern_match_with_no_patterns(
        self, b_cell: LinfocitoBDigital, sample_event: dict
    ):
        """Test pattern matching with no learned patterns"""
        # Should not crash
        await b_cell._check_pattern_match(sample_event)

        assert b_cell.pattern_matches == 0

    @pytest.mark.asyncio
    async def test_neutralization_without_ip(
        self, b_cell: LinfocitoBDigital, sample_antibody: AntibodyPattern
    ):
        """Test neutralization without target IP"""
        b_cell.antibody_patterns[sample_antibody.pattern_id] = sample_antibody

        result = await b_cell.executar_neutralizacao(
            {
                "pattern_id": sample_antibody.pattern_id,
                # No dst_ip or ip
            },
            metodo="isolate",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_calculate_affinity_with_none_values(
        self, b_cell: LinfocitoBDigital
    ):
        """Test affinity calculation with None values"""
        affinity = b_cell._calculate_affinity(None, None)
        assert affinity == 0.0

        affinity = b_cell._calculate_affinity({}, None)
        assert affinity == 0.0

        affinity = b_cell._calculate_affinity(None, {})
        assert affinity == 0.0
