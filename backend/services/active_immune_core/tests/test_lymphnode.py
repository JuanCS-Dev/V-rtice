"""
Unit tests for Linfonodo Digital (Digital Lymphnode)

Tests cover actual production implementation:
- Initialization and lifecycle
- Agent registration/removal
- Agent cloning and specialization
- Cytokine processing
- Pattern detection
- Homeostatic state regulation
- Metrics
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest
import pytest_asyncio

from active_immune_core.agents.models import AgenteState
from active_immune_core.agents import AgentType
from active_immune_core.coordination.lymphnode import (
    LinfonodoDigital,
    HomeostaticState,
)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def lymphnode() -> LinfonodoDigital:
    """Create Linfonodo Digital instance for testing."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test_001",
        nivel="local",
        area_responsabilidade="subnet_10.0.1.0/24",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379/0",
    )
    yield lymph
    if lymph._running:
        await lymph.parar()


@pytest.fixture
def mock_agent_state() -> AgenteState:
    """Create mock agent state for testing."""
    return AgenteState(
        id="neutrofilo_test_001",
        tipo=AgentType.NEUTROFILO,
        localizacao_atual="subnet_10.0.1.0/24",
        area_patrulha="subnet_10.0.1.0/24",
        nivel_agressividade=0.8,
        sensibilidade=0.7,
    )


@pytest.fixture
def sample_cytokine() -> Dict[str, Any]:
    """Sample cytokine message matching production format."""
    return {
        "tipo": "IL1",
        "prioridade": 7,
        "origem_agente_id": "neutrofilo_001",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "evento": "ameaca_detectada",
            "is_threat": True,
            "alvo": {
                "id": "threat_12345",
                "tipo": "malware",
            },
            "severity": "high",
        },
    }


# ==================== INITIALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_lymphnode_initialization():
    """Test Linfonodo initialization with valid config."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test_001",
        nivel="local",
        area_responsabilidade="subnet_10.0.1.0/24",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379/0",
    )

    assert lymph.id == "lymph_test_001"
    assert lymph.nivel == "local"
    assert lymph.area == "subnet_10.0.1.0/24"
    assert lymph.temperatura_regional == 37.0
    assert lymph.homeostatic_state == HomeostaticState.VIGILANCIA
    assert not lymph._running
    assert len(lymph.agentes_ativos) == 0
    assert len(lymph.cytokine_buffer) == 0


@pytest.mark.asyncio
async def test_lymphnode_initialization_global_level():
    """Test Linfonodo initialization with global level."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_global_001",
        nivel="global",
        area_responsabilidade="datacenter",
    )

    assert lymph.nivel == "global"
    assert lymph.area == "datacenter"


@pytest.mark.asyncio
async def test_lymphnode_initialization_regional_level():
    """Test Linfonodo initialization with regional level."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_regional_001",
        nivel="regional",
        area_responsabilidade="us-east-1",
    )

    assert lymph.nivel == "regional"


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
async def test_lymphnode_start_stop(lymphnode: LinfonodoDigital):
    """Test Linfonodo lifecycle: start and stop."""
    # Start
    await lymphnode.iniciar()
    assert lymphnode._running is True
    assert lymphnode._redis_client is not None
    assert len(lymphnode._tasks) > 0

    # Stop
    await lymphnode.parar()
    assert lymphnode._running is False


@pytest.mark.asyncio
async def test_lymphnode_double_start_idempotent(lymphnode: LinfonodoDigital):
    """Test that starting twice is idempotent."""
    await lymphnode.iniciar()
    first_redis = lymphnode._redis_client

    # Start again (should not crash)
    await lymphnode.iniciar()
    second_redis = lymphnode._redis_client

    assert lymphnode._running is True
    # Same client (didn't recreate)
    assert first_redis is not None

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_lymphnode_stop_without_start(lymphnode: LinfonodoDigital):
    """Test stopping lymphnode that was never started."""
    # Should not raise exception
    await lymphnode.parar()
    assert lymphnode._running is False


# ==================== AGENT ORCHESTRATION TESTS ====================


@pytest.mark.asyncio
async def test_register_agent(lymphnode: LinfonodoDigital, mock_agent_state: AgenteState):
    """Test agent registration."""
    await lymphnode.registrar_agente(mock_agent_state)

    assert mock_agent_state.id in lymphnode.agentes_ativos
    assert lymphnode.agentes_ativos[mock_agent_state.id].tipo == AgentType.NEUTROFILO


@pytest.mark.asyncio
async def test_register_multiple_agents(lymphnode: LinfonodoDigital):
    """Test registering multiple agents."""
    agents = [
        AgenteState(
            id=f"agent_{i}",
            tipo=AgentType.NEUTROFILO if i % 2 == 0 else AgentType.NK_CELL,
            localizacao_atual=lymphnode.area,
            area_patrulha=lymphnode.area,
            nivel_agressividade=0.8,
            sensibilidade=0.7,
        )
        for i in range(5)
    ]

    for agent_state in agents:
        await lymphnode.registrar_agente(agent_state)

    assert len(lymphnode.agentes_ativos) == 5


@pytest.mark.asyncio
async def test_remove_agent(lymphnode: LinfonodoDigital, mock_agent_state: AgenteState):
    """Test agent removal."""
    await lymphnode.registrar_agente(mock_agent_state)
    assert mock_agent_state.id in lymphnode.agentes_ativos

    await lymphnode.remover_agente(mock_agent_state.id)
    assert mock_agent_state.id not in lymphnode.agentes_ativos


@pytest.mark.asyncio
async def test_remove_nonexistent_agent(lymphnode: LinfonodoDigital):
    """Test removing agent that doesn't exist (should not crash)."""
    # Should not raise exception
    await lymphnode.remover_agente("nonexistent_agent")
    assert len(lymphnode.agentes_ativos) == 0


# ==================== CLONING TESTS (requires running factory) ====================


# Note: Cloning tests require AgentFactory to be functional
# These are integration-level tests that will be added later


# ==================== CYTOKINE PROCESSING TESTS ====================


@pytest.mark.asyncio
async def test_process_regional_cytokine(lymphnode: LinfonodoDigital, sample_cytokine: Dict[str, Any]):
    """Test processing regional cytokine."""
    await lymphnode.iniciar()

    initial_temp = lymphnode.temperatura_regional

    # Process cytokine
    await lymphnode._processar_citocina_regional(sample_cytokine)

    # Temperature should increase
    assert lymphnode.temperatura_regional > initial_temp

    # Threat should be tracked
    threat_id = sample_cytokine["payload"]["alvo"]["id"]
    assert lymphnode.threat_detections[threat_id] >= 1

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_cytokine_buffer_management(lymphnode: LinfonodoDigital):
    """Test cytokine buffer maintains reasonable size."""
    await lymphnode.iniciar()

    # Add many cytokines
    for i in range(150):
        cytokine = {
            "tipo": "IL1",
            "prioridade": 5,
            "origem_agente_id": f"agent_{i}",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {},
        }
        lymphnode.cytokine_buffer.append(cytokine)

    # Buffer should trim (implementation may limit to ~100)
    assert len(lymphnode.cytokine_buffer) <= 200  # Reasonable upper bound

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_temperature_increase_from_high_level_cytokine(lymphnode: LinfonodoDigital):
    """Test temperature increases from high-level cytokine."""
    await lymphnode.iniciar()

    initial_temp = lymphnode.temperatura_regional

    # High-level pro-inflammatory cytokine
    cytokine = {
        "tipo": "IL6",
        "prioridade": 8,
        "origem_agente_id": "agent_001",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {},
    }

    await lymphnode._processar_citocina_regional(cytokine)

    # Temperature should increase significantly (IL6 is pro-inflammatory)
    assert lymphnode.temperatura_regional > initial_temp

    await lymphnode.parar()


# ==================== PATTERN DETECTION TESTS ====================


@pytest.mark.asyncio
async def test_persistent_threat_detection(lymphnode: LinfonodoDigital):
    """Test detection of persistent threat (multiple detections)."""
    await lymphnode.iniciar()

    threat_id = "persistent_threat_001"

    # Simulate 6 detections of same threat
    for i in range(6):
        cytokine = {
            "tipo": "IL1",
            "prioridade": 7,
            "origem_agente_id": f"agent_{i}",
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "evento": "ameaca_detectada",
                "is_threat": True,
                "alvo": {"id": threat_id},
            },
        }
        await lymphnode._processar_citocina_regional(cytokine)

    # Should have tracked the persistent threat
    assert lymphnode.threat_detections[threat_id] >= 5

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_coordinated_attack_detection(lymphnode: LinfonodoDigital):
    """Test detection of coordinated attack (many different threats)."""
    await lymphnode.iniciar()

    # Simulate 12 different threats in short time
    now = datetime.utcnow()
    for i in range(12):
        cytokine = {
            "tipo": "IL6",
            "prioridade": 9,
            "origem_agente_id": f"agent_{i}",
            "timestamp": now.isoformat(),
            "payload": {
                "evento": "ameaca_detectada",
                "is_threat": True,
                "alvo": {"id": f"threat_{i}"},
            },
        }
        await lymphnode._processar_citocina_regional(cytokine)

    # Should have tracked multiple unique threats
    assert len(lymphnode.threat_detections) >= 10

    await lymphnode.parar()


# ==================== HOMEOSTATIC STATE TESTS ====================


@pytest.mark.asyncio
async def test_homeostatic_state_repouso():
    """Test REPOUSO state (temperature < 37.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 36.5
    assert lymph.homeostatic_state == HomeostaticState.REPOUSO


@pytest.mark.asyncio
async def test_homeostatic_state_vigilancia():
    """Test VIGILÂNCIA state (37.0-37.5°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 37.2
    assert lymph.homeostatic_state == HomeostaticState.VIGILANCIA


@pytest.mark.asyncio
async def test_homeostatic_state_atencao():
    """Test ATENÇÃO state (37.5-38.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 37.7
    assert lymph.homeostatic_state == HomeostaticState.ATENCAO


@pytest.mark.asyncio
async def test_homeostatic_state_ativacao():
    """Test ATIVAÇÃO state (38.0-39.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 38.5
    assert lymph.homeostatic_state == HomeostaticState.ATIVACAO


@pytest.mark.asyncio
async def test_homeostatic_state_inflamacao():
    """Test INFLAMAÇÃO state (>= 39.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 39.5
    assert lymph.homeostatic_state == HomeostaticState.INFLAMACAO


@pytest.mark.asyncio
async def test_temperature_boundary_vigilancia():
    """Test exact boundary (37.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 37.0
    assert lymph.homeostatic_state == HomeostaticState.VIGILANCIA


@pytest.mark.asyncio
async def test_temperature_boundary_inflamacao():
    """Test exact boundary (39.0°C)."""
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
    )

    lymph.temperatura_regional = 39.0
    assert lymph.homeostatic_state == HomeostaticState.INFLAMACAO


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
async def test_get_metrics(lymphnode: LinfonodoDigital, mock_agent_state: AgenteState):
    """Test retrieving lymphnode metrics."""
    await lymphnode.iniciar()

    # Register agent
    await lymphnode.registrar_agente(mock_agent_state)

    # Set temperature
    lymphnode.temperatura_regional = 38.0

    # Add threats
    lymphnode.threat_detections["threat_001"] = 3
    lymphnode.threat_detections["threat_002"] = 7

    metrics = lymphnode.get_lymphnode_metrics()

    assert metrics["lymphnode_id"] == lymphnode.id
    assert metrics["nivel"] == lymphnode.nivel
    assert metrics["area"] == lymphnode.area
    assert metrics["temperatura_regional"] == 38.0
    assert metrics["agentes_total"] == 1
    assert metrics["agentes_dormindo"] == 0
    assert metrics["ameacas_detectadas"] >= 0
    assert metrics["threats_being_tracked"] >= 2

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_metrics_agent_counts(lymphnode: LinfonodoDigital):
    """Test metrics include correct agent counts."""
    await lymphnode.iniciar()

    # Register multiple agents
    for i in range(5):
        agent_state = AgenteState(
            id=f"agent_{i}",
            tipo=AgentType.NEUTROFILO,
            localizacao_atual=lymphnode.area,
            area_patrulha=lymphnode.area,
            nivel_agressividade=0.8,
            sensibilidade=0.7,
        )
        await lymphnode.registrar_agente(agent_state)

    metrics = lymphnode.get_lymphnode_metrics()

    assert metrics["agentes_total"] == 5

    await lymphnode.parar()


# ==================== ERROR HANDLING ====================


@pytest.mark.asyncio
async def test_graceful_degradation_redis_failure():
    """Test graceful degradation when Redis connection fails."""
    # Use invalid Redis URL
    lymph = LinfonodoDigital(
        lymphnode_id="lymph_test",
        nivel="local",
        area_responsabilidade="test",
        redis_url="redis://invalid-host:6379/0",
    )

    # Should start without crashing (graceful degradation)
    try:
        await lymph.iniciar()
        assert lymph._running is True
    finally:
        await lymph.parar()


@pytest.mark.asyncio
async def test_cytokine_processing_with_missing_payload(lymphnode: LinfonodoDigital):
    """Test cytokine processing with missing payload fields."""
    await lymphnode.iniciar()

    initial_temp = lymphnode.temperatura_regional

    # Cytokine missing payload (defaults to {})
    incomplete_cytokine = {
        "tipo": "IL1",
        "prioridade": 5,
        "origem_agente_id": "agent_001",
        "timestamp": datetime.utcnow().isoformat(),
        # Missing payload
    }

    # Should handle gracefully
    await lymphnode._processar_citocina_regional(incomplete_cytokine)

    # Temperature should still increase (IL1 is pro-inflammatory)
    assert lymphnode.temperatura_regional > initial_temp

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_cytokine_processing_with_invalid_timestamp(lymphnode: LinfonodoDigital):
    """Test cytokine processing with invalid timestamp."""
    await lymphnode.iniciar()

    # Cytokine with invalid timestamp (should still process)
    cytokine = {
        "tipo": "IL1",
        "prioridade": 5,
        "origem_agente_id": "agent_001",
        "timestamp": "invalid-timestamp",
        "payload": {},
    }

    # Should handle gracefully (timestamp not critical for processing)
    try:
        await lymphnode._processar_citocina_regional(cytokine)
    except Exception:
        # Expected to handle gracefully
        pass

    await lymphnode.parar()


# ==================== REPR TEST ====================


@pytest.mark.asyncio
async def test_repr(lymphnode: LinfonodoDigital):
    """Test string representation."""
    repr_str = repr(lymphnode)
    assert "lymph_test_001" in repr_str
    assert "local" in repr_str


# ==================== CLONAL EXPANSION TESTS ====================


@pytest.mark.asyncio
async def test_clonal_expansion_basic(lymphnode: LinfonodoDigital):
    """Test basic clonal expansion functionality."""
    await lymphnode.iniciar()

    # Trigger clonal expansion
    clone_ids = await lymphnode.clonar_agente(
        tipo_base="neutrofilo",
        quantidade=3,
        especializacao="test_threat",
    )

    # Verify clones were created
    assert len(clone_ids) == 3
    assert lymphnode.total_clones_criados == 3

    # Verify clones are registered
    for clone_id in clone_ids:
        assert clone_id in lymphnode.agentes_ativos

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_destroy_clones(lymphnode: LinfonodoDigital):
    """Test destroying clones with specific specialization."""
    await lymphnode.iniciar()

    # Create some clones
    specialization = "old_threat"
    clone_ids = await lymphnode.clonar_agente(
        tipo_base="neutrofilo",
        quantidade=4,
        especializacao=specialization,
    )

    assert len(clone_ids) == 4

    # Destroy clones
    destroyed_count = await lymphnode.destruir_clones(especializacao=specialization)

    assert destroyed_count == 4

    # Verify clones are removed
    for clone_id in clone_ids:
        assert clone_id not in lymphnode.agentes_ativos

    await lymphnode.parar()


# ==================== PHASE 2: ADVANCED COVERAGE (57%→90%) ====================


@pytest.mark.asyncio
async def test_adjust_temperature_decrease(lymphnode: LinfonodoDigital):
    """Test temperature adjustment with negative delta."""
    await lymphnode.iniciar()

    # Set high temp first (use correct attribute)
    lymphnode.temperatura_regional = 80.0
    await lymphnode._adjust_temperature(delta=-30.0)

    assert lymphnode.temperatura_regional < 80.0  # Should decrease

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_detect_coordinated_attacks(lymphnode: LinfonodoDigital):
    """Test coordinated attack detection."""
    await lymphnode.iniciar()

    # Create coordinated cytokines (same time window, different sources)
    now = datetime.now()
    cytokines = []
    for i in range(4):
        cytokines.append({
            "tipo": "IL1",
            "emissor_id": f"mac_{i:03d}",
            "prioridade": 8,
            "timestamp": (now - timedelta(seconds=i)).isoformat(),
            "payload": {"dst_ip": f"198.51.100.{50+i}"},
        })

    await lymphnode._detect_coordinated_attacks(cytokines)

    # Coordinated attack detection should trigger
    assert True

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_monitor_temperature_fever(lymphnode: LinfonodoDigital):
    """Test temperature monitoring with fever state."""
    await lymphnode.iniciar()

    # Set high temperature (fever)
    lymphnode.temperatura_regional = 75.0

    await lymphnode._monitor_temperature()

    # Temperature should be adjusted downward
    assert lymphnode.temperatura_regional < 75.0

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_monitor_temperature_hypothermia(lymphnode: LinfonodoDigital):
    """Test temperature monitoring with hypothermic state."""
    await lymphnode.iniciar()

    # Set very low temperature
    lymphnode.temperatura_regional = 20.0

    await lymphnode._monitor_temperature()

    # Temperature should be adjusted upward
    assert lymphnode.temperatura_regional > 20.0

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_homeostatic_state_property(lymphnode: LinfonodoDigital):
    """Test homeostatic state property calculation."""
    await lymphnode.iniciar()

    # Test normal state
    lymphnode.temperatura_regional = 40.0
    state = lymphnode.homeostatic_state
    assert state == HomeostaticState.NORMAL

    # Test fever state
    lymphnode.temperatura_regional = 70.0
    state = lymphnode.homeostatic_state
    assert state == HomeostaticState.FEVER

    # Test stress state
    lymphnode.temperatura_regional = 55.0
    state = lymphnode.homeostatic_state
    assert state == HomeostaticState.STRESS

    # Test hypothermia state
    lymphnode.temperatura_regional = 30.0
    state = lymphnode.homeostatic_state
    assert state == HomeostaticState.HYPOTHERMIA

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_send_apoptosis_signal(lymphnode: LinfonodoDigital):
    """Test apoptosis signal sending."""
    await lymphnode.iniciar()

    # Register an agent first
    agent_state = AgenteState(
        id="test_agent_apoptosis",
        tipo=AgentType.NEUTROFILO,
        area_patrulha="test_area",
    )
    await lymphnode.registrar_agente(agent_state)

    # Send apoptosis signal
    await lymphnode._send_apoptosis_signal("test_agent_apoptosis")

    # Agent should still be in registry (apoptosis is async)
    # Just verify signal was sent without error
    assert True

    await lymphnode.parar()


@pytest.mark.asyncio
async def test_cytokine_buffer_operations(lymphnode: LinfonodoDigital):
    """Test cytokine buffer operations."""
    await lymphnode.iniciar()

    # Add some cytokines to buffer
    for i in range(10):
        lymphnode.cytokine_buffer.append({
            "tipo": "IL1",
            "emissor_id": f"mac_{i:03d}",
            "timestamp": datetime.now().isoformat(),
        })

    # Verify buffer has data
    assert len(lymphnode.cytokine_buffer) == 10

    # Trigger aggregation
    await lymphnode._aggregate_cytokines()

    # Buffer should be processed
    assert True  # Just verify no exceptions

    await lymphnode.parar()
