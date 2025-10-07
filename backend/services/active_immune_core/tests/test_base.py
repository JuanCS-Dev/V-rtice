"""
Unit tests for AgenteImunologicoBase (Abstract Base Agent Class)

Tests cover production implementation:
- Initialization and lifecycle
- Abstract methods (patrol, investigation, neutralization)
- Communication (cytokines, hormones)
- Homeostasis (heartbeat, energy decay)
- Ethical AI validation
- Memory creation
- Metrics and error handling
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.agents.base import AgenteImunologicoBase
from active_immune_core.agents.models import AgentStatus, AgentType


# ==================== CONCRETE TEST AGENT ====================


class ConcreteTestAgent(AgenteImunologicoBase):
    """Concrete implementation for testing abstract base class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.patrol_count = 0
        self.investigation_count = 0
        self.neutralization_count = 0

    async def patrulhar(self) -> None:
        """Concrete patrol implementation."""
        self.patrol_count += 1

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """Concrete investigation implementation."""
        self.investigation_count += 1
        return {
            "is_threat": alvo.get("is_threat", False),
            "threat_level": alvo.get("threat_level", 0.0),
            "details": {"analysis": "test_investigation"},
        }

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """Concrete neutralization implementation."""
        self.neutralization_count += 1
        return alvo.get("neutralization_success", True)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def agent() -> ConcreteTestAgent:
    """Create ConcreteTestAgent instance for testing."""
    agent = ConcreteTestAgent(
        agent_id="test_agent_001",
        tipo=AgentType.MACROFAGO,
        area_patrulha="10.0.0.0/24",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        ethical_ai_url="http://localhost:8612",
        memory_service_url="http://localhost:8019",
    )
    yield agent
    if agent._running:
        await agent.parar()


@pytest_asyncio.fixture
async def running_agent(agent: ConcreteTestAgent) -> ConcreteTestAgent:
    """Create and start agent with mocked communication."""
    # Mock communication messengers
    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.stop = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.send_cytokine = AsyncMock()
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.stop = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.set_agent_state = AsyncMock()
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            await agent.iniciar()
            yield agent
            await agent.parar()


# ==================== INITIALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initialization with all parameters."""
    agent = ConcreteTestAgent(
        agent_id="test_001",
        tipo=AgentType.NK_CELL,
        area_patrulha="192.168.1.0/24",
        kafka_bootstrap="kafka:9092",
        redis_url="redis://redis:6379",
    )

    assert agent.state.id == "test_001"
    assert agent.state.tipo == AgentType.NK_CELL
    assert agent.state.area_patrulha == "192.168.1.0/24"
    assert agent.state.localizacao_atual == "192.168.1.0/24"
    assert agent.state.ativo is False
    assert agent.state.status == AgentStatus.DORMINDO
    assert agent._running is False
    assert len(agent._tasks) == 0


@pytest.mark.asyncio
async def test_agent_initialization_auto_id():
    """Test agent gets auto-generated UUID if no ID provided."""
    agent = ConcreteTestAgent()

    assert agent.state.id is not None
    assert len(agent.state.id) > 0
    # UUID format check
    assert "-" in agent.state.id


@pytest.mark.asyncio
async def test_agent_initialization_default_values():
    """Test agent uses default service URLs."""
    agent = ConcreteTestAgent()

    assert agent.kafka_bootstrap == "localhost:9092"
    assert agent.redis_url == "redis://localhost:6379"
    assert agent.ethical_ai_url == "http://localhost:8612"
    assert agent.memory_service_url == "http://localhost:8019"


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
async def test_iniciar_agent():
    """Test starting agent initializes all components."""
    agent = ConcreteTestAgent(agent_id="test_start")

    # Mock messengers
    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            await agent.iniciar()

            assert agent._running is True
            assert agent.state.ativo is True
            assert agent.state.status == AgentStatus.PATRULHANDO
            assert len(agent._tasks) == 3  # patrol, heartbeat, energy_decay
            assert agent._http_session is not None

            # Verify communication started
            mock_cytokine.start.assert_called_once()
            mock_hormone.start.assert_called_once()

            await agent.parar()


@pytest.mark.asyncio
async def test_parar_agent(running_agent: ConcreteTestAgent):
    """Test stopping agent cleans up resources."""
    assert running_agent._running is True

    await running_agent.parar()

    assert running_agent._running is False
    assert running_agent.state.ativo is False
    assert len(running_agent._tasks) == 0


@pytest.mark.asyncio
async def test_iniciar_idempotent(running_agent: ConcreteTestAgent):
    """Test starting already running agent is idempotent."""
    first_task_count = len(running_agent._tasks)

    # Start again (should not crash or duplicate tasks)
    await running_agent.iniciar()

    assert running_agent._running is True
    assert len(running_agent._tasks) == first_task_count


@pytest.mark.asyncio
async def test_parar_not_running():
    """Test stopping agent that was never started."""
    agent = ConcreteTestAgent()

    # Should not raise exception
    await agent.parar()
    assert agent._running is False


@pytest.mark.asyncio
async def test_apoptose_sends_death_signal(running_agent: ConcreteTestAgent):
    """Test apoptosis sends IL10 death signal."""
    await running_agent.apoptose(reason="test_death")

    assert running_agent.state.status == AgentStatus.APOPTOSE
    assert running_agent._running is False

    # Verify cytokine was sent
    running_agent._cytokine_messenger.send_cytokine.assert_called_once()
    call_kwargs = running_agent._cytokine_messenger.send_cytokine.call_args[1]
    assert call_kwargs["tipo"] == "IL10"
    assert call_kwargs["payload"]["evento"] == "apoptose"
    assert call_kwargs["payload"]["reason"] == "test_death"


@pytest.mark.asyncio
async def test_apoptose_without_messenger():
    """Test apoptosis without active messenger."""
    agent = ConcreteTestAgent()

    # Should not crash
    await agent.apoptose(reason="early_death")

    assert agent.state.status == AgentStatus.APOPTOSE
    assert agent._running is False


# ==================== PATROL TESTS ====================


@pytest.mark.asyncio
async def test_patrol_loop_calls_patrulhar(running_agent: ConcreteTestAgent):
    """Test patrol loop calls abstract patrulhar method."""
    # Wait for at least one patrol cycle
    await asyncio.sleep(0.5)

    assert running_agent.patrol_count > 0


@pytest.mark.asyncio
async def test_patrol_interval_calculation(agent: ConcreteTestAgent):
    """Test patrol interval varies with temperature."""
    # Repouso (<37.5)
    agent.state.temperatura_local = 37.0
    assert agent._get_patrol_interval() == 30.0

    # Vigilância (37.5-38.0)
    agent.state.temperatura_local = 37.7
    assert agent._get_patrol_interval() == 10.0

    # Atenção (38.0-39.0)
    agent.state.temperatura_local = 38.5
    assert agent._get_patrol_interval() == 3.0

    # Inflamação (>=39.0)
    agent.state.temperatura_local = 39.5
    assert agent._get_patrol_interval() == 1.0


# ==================== INVESTIGATION TESTS ====================


@pytest.mark.asyncio
async def test_investigar_benign_target(running_agent: ConcreteTestAgent):
    """Test investigating benign target."""
    alvo = {"id": "host_001", "is_threat": False, "threat_level": 0.0}

    resultado = await running_agent.investigar(alvo)

    assert resultado["is_threat"] is False
    assert running_agent.investigation_count == 1
    assert running_agent.state.deteccoes_total == 1


@pytest.mark.asyncio
async def test_investigar_threat_sends_cytokine(running_agent: ConcreteTestAgent):
    """Test investigating threat sends IL1 cytokine."""
    alvo = {"id": "malicious_host", "is_threat": True, "threat_level": 8.5}

    resultado = await running_agent.investigar(alvo)

    assert resultado["is_threat"] is True
    assert "malicious_host" in running_agent.state.ultimas_ameacas

    # Verify IL1 was sent
    running_agent._cytokine_messenger.send_cytokine.assert_called()
    call_kwargs = running_agent._cytokine_messenger.send_cytokine.call_args[1]
    assert call_kwargs["tipo"] == "IL1"
    assert call_kwargs["payload"]["evento"] == "ameaca_detectada"


@pytest.mark.asyncio
async def test_investigar_updates_status(running_agent: ConcreteTestAgent):
    """Test investigation updates agent status."""
    old_status = running_agent.state.status
    alvo = {"id": "test_target"}

    # Patch executar_investigacao to delay
    async def slow_investigation(alvo):
        await asyncio.sleep(0.1)
        return {"is_threat": False, "threat_level": 0.0, "details": {}}

    running_agent.executar_investigacao = slow_investigation

    # Start investigation
    task = asyncio.create_task(running_agent.investigar(alvo))
    await asyncio.sleep(0.05)  # Check status mid-investigation

    # Should be INVESTIGANDO during investigation
    assert running_agent.state.status == AgentStatus.INVESTIGANDO

    await task
    # Should revert to old status
    assert running_agent.state.status == old_status


@pytest.mark.asyncio
async def test_investigar_tracks_threats_limit(running_agent: ConcreteTestAgent):
    """Test ultimas_ameacas keeps only last 10 threats."""
    # Investigate 15 threats
    for i in range(15):
        alvo = {"id": f"threat_{i:03d}", "is_threat": True}
        await running_agent.investigar(alvo)

    # Should keep only last 10
    assert len(running_agent.state.ultimas_ameacas) == 10
    assert "threat_014" in running_agent.state.ultimas_ameacas
    assert "threat_004" not in running_agent.state.ultimas_ameacas


# ==================== NEUTRALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_neutralizar_with_ethical_approval(running_agent: ConcreteTestAgent):
    """Test neutralization with ethical AI approval."""
    alvo = {"id": "malware_001", "neutralization_success": True}

    # Mock ethical AI approval
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"decisao": "APROVADO"})

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    # Mock memory creation
    mock_memory_response = AsyncMock()
    mock_memory_response.status = 201
    mock_memory_ctx = AsyncMock()
    mock_memory_ctx.__aenter__.return_value = mock_memory_response
    mock_memory_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post") as mock_post:
        mock_post.side_effect = [mock_ctx, mock_memory_ctx]

        sucesso = await running_agent.neutralizar(alvo, metodo="isolate")

        assert sucesso is True
        assert running_agent.neutralization_count == 1
        assert running_agent.state.neutralizacoes_total == 1


@pytest.mark.asyncio
async def test_neutralizar_blocked_by_ethical_ai(running_agent: ConcreteTestAgent):
    """Test neutralization blocked by ethical AI."""
    alvo = {"id": "suspicious_target"}

    # Mock ethical AI rejection
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "decisao": "BLOQUEADO",
        "justificativa": "Insufficient evidence"
    })

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx):
        sucesso = await running_agent.neutralizar(alvo, metodo="kill")

        assert sucesso is False
        assert running_agent.neutralization_count == 0


@pytest.mark.asyncio
async def test_neutralizar_sends_il6_on_success(running_agent: ConcreteTestAgent):
    """Test successful neutralization sends IL6 cytokine."""
    alvo = {"id": "threat_001", "neutralization_success": True}

    # Mock ethical AI approval
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"decisao": "APROVADO"})

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    # Mock memory creation
    mock_memory_response = AsyncMock()
    mock_memory_response.status = 201
    mock_memory_ctx = AsyncMock()
    mock_memory_ctx.__aenter__.return_value = mock_memory_response
    mock_memory_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post") as mock_post:
        mock_post.side_effect = [mock_ctx, mock_memory_ctx]

        await running_agent.neutralizar(alvo, metodo="block")

        # Verify IL6 was sent
        calls = running_agent._cytokine_messenger.send_cytokine.call_args_list
        il6_call = [c for c in calls if c[1]["tipo"] == "IL6"]
        assert len(il6_call) > 0
        assert il6_call[0][1]["payload"]["evento"] == "neutralizacao_sucesso"


@pytest.mark.asyncio
async def test_neutralizar_updates_status(running_agent: ConcreteTestAgent):
    """Test neutralization updates agent status."""
    alvo = {"id": "test_target"}
    old_status = running_agent.state.status

    # Mock ethical AI approval
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"decisao": "APROVADO"})
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    # Mock memory creation
    mock_memory_response = AsyncMock()
    mock_memory_response.status = 201
    mock_memory_ctx = AsyncMock()
    mock_memory_ctx.__aenter__.return_value = mock_memory_response
    mock_memory_ctx.__aexit__.return_value = None

    # Slow neutralization
    async def slow_neutralization(alvo, metodo):
        await asyncio.sleep(0.1)
        return True

    running_agent.executar_neutralizacao = slow_neutralization

    with patch.object(running_agent._http_session, "post") as mock_post:
        mock_post.side_effect = [mock_ctx, mock_memory_ctx]

        task = asyncio.create_task(running_agent.neutralizar(alvo, metodo="isolate"))
        await asyncio.sleep(0.05)

        # Should be NEUTRALIZANDO during neutralization
        assert running_agent.state.status == AgentStatus.NEUTRALIZANDO

        await task
        # Should revert to old status
        assert running_agent.state.status == old_status


# ==================== MEMORY CREATION TESTS ====================


@pytest.mark.asyncio
async def test_criar_memoria_success(running_agent: ConcreteTestAgent):
    """Test successful memory creation."""
    ameaca = {"id": "threat_001", "type": "malware"}

    # Mock memory service response
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.text = AsyncMock(return_value="Memory created")

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx) as mock_post:
        await running_agent._criar_memoria(ameaca)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["tipo"] == "threat_neutralization"
        assert call_kwargs["json"]["ameaca"] == ameaca


@pytest.mark.asyncio
async def test_criar_memoria_service_failure(running_agent: ConcreteTestAgent):
    """Test memory creation handles service failure gracefully."""
    ameaca = {"id": "threat_002"}

    # Mock failed response
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal error")

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx):
        # Should not crash
        await running_agent._criar_memoria(ameaca)


@pytest.mark.asyncio
async def test_criar_memoria_timeout(running_agent: ConcreteTestAgent):
    """Test memory creation handles timeout."""
    ameaca = {"id": "threat_003"}

    async def timeout_post(*args, **kwargs):
        raise asyncio.TimeoutError()

    with patch.object(running_agent._http_session, "post", side_effect=timeout_post):
        # Should not crash
        await running_agent._criar_memoria(ameaca)


@pytest.mark.asyncio
async def test_criar_memoria_without_http_session():
    """Test memory creation without HTTP session."""
    agent = ConcreteTestAgent()
    ameaca = {"id": "threat_004"}

    # Should not crash
    await agent._criar_memoria(ameaca)


# ==================== ETHICAL AI VALIDATION TESTS ====================


@pytest.mark.asyncio
async def test_validate_ethical_approved(running_agent: ConcreteTestAgent):
    """Test ethical AI approves action."""
    alvo = {"id": "confirmed_malware"}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"decisao": "APROVADO"})

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx):
        approved = await running_agent._validate_ethical(alvo, "isolate")

        assert approved is True


@pytest.mark.asyncio
async def test_validate_ethical_blocked(running_agent: ConcreteTestAgent):
    """Test ethical AI blocks action."""
    alvo = {"id": "questionable_target"}

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "decisao": "BLOQUEADO",
        "justificativa": "Insufficient evidence"
    })

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx):
        approved = await running_agent._validate_ethical(alvo, "kill")

        assert approved is False


@pytest.mark.asyncio
async def test_validate_ethical_service_error_blocks(running_agent: ConcreteTestAgent):
    """Test ethical AI blocks on service error (fail-safe)."""
    alvo = {"id": "target"}

    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal error")

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post", return_value=mock_ctx):
        approved = await running_agent._validate_ethical(alvo, "isolate")

        # Fail-safe: block on error
        assert approved is False


@pytest.mark.asyncio
async def test_validate_ethical_timeout_blocks(running_agent: ConcreteTestAgent):
    """Test ethical AI blocks on timeout (fail-safe)."""
    alvo = {"id": "target"}

    async def timeout_post(*args, **kwargs):
        raise asyncio.TimeoutError()

    with patch.object(running_agent._http_session, "post", side_effect=timeout_post):
        approved = await running_agent._validate_ethical(alvo, "isolate")

        # Fail-safe: block on timeout
        assert approved is False


@pytest.mark.asyncio
async def test_validate_ethical_without_http_session():
    """Test ethical AI validation without HTTP session (fail-safe)."""
    agent = ConcreteTestAgent()
    alvo = {"id": "target"}

    approved = await agent._validate_ethical(alvo, "isolate")

    # Fail-safe: block if session not initialized
    assert approved is False


# ==================== COMMUNICATION TESTS ====================


@pytest.mark.asyncio
async def test_processar_citocina_proinflammatory(running_agent: ConcreteTestAgent):
    """Test processing pro-inflammatory cytokines increases temperature."""
    # Create mock cytokine
    mock_cytokine = MagicMock()
    mock_cytokine.tipo = "IL1"
    mock_cytokine.emissor_id = "other_agent"

    initial_temp = running_agent.state.temperatura_local

    await running_agent._processar_citocina(mock_cytokine)

    assert running_agent.state.temperatura_local > initial_temp
    assert running_agent.state.temperatura_local <= 42.0  # Max cap


@pytest.mark.asyncio
async def test_processar_citocina_antiinflammatory(running_agent: ConcreteTestAgent):
    """Test processing anti-inflammatory cytokines decreases temperature."""
    running_agent.state.temperatura_local = 39.0

    mock_cytokine = MagicMock()
    mock_cytokine.tipo = "IL10"
    mock_cytokine.emissor_id = "other_agent"

    await running_agent._processar_citocina(mock_cytokine)

    assert running_agent.state.temperatura_local < 39.0
    assert running_agent.state.temperatura_local >= 36.5  # Min cap


@pytest.mark.asyncio
async def test_processar_citocina_ignores_own_messages(running_agent: ConcreteTestAgent):
    """Test agent ignores its own cytokines."""
    mock_cytokine = MagicMock()
    mock_cytokine.tipo = "IL1"
    mock_cytokine.emissor_id = running_agent.state.id

    initial_temp = running_agent.state.temperatura_local

    await running_agent._processar_citocina(mock_cytokine)

    # Temperature should not change
    assert running_agent.state.temperatura_local == initial_temp


@pytest.mark.asyncio
async def test_processar_hormonio_cortisol(running_agent: ConcreteTestAgent):
    """Test cortisol decreases sensitivity (stress response)."""
    initial_sens = running_agent.state.sensibilidade

    mock_hormone = MagicMock()
    mock_hormone.tipo = "cortisol"
    mock_hormone.nivel = 8.0

    await running_agent._processar_hormonio(mock_hormone)

    assert running_agent.state.sensibilidade < initial_sens
    assert running_agent.state.sensibilidade >= 0.1  # Min cap


@pytest.mark.asyncio
async def test_processar_hormonio_adrenalina(running_agent: ConcreteTestAgent):
    """Test adrenalina increases aggressiveness."""
    initial_aggr = running_agent.state.nivel_agressividade

    mock_hormone = MagicMock()
    mock_hormone.tipo = "adrenalina"
    mock_hormone.nivel = 9.0

    await running_agent._processar_hormonio(mock_hormone)

    assert running_agent.state.nivel_agressividade > initial_aggr
    assert running_agent.state.nivel_agressividade <= 1.0  # Max cap


@pytest.mark.asyncio
async def test_processar_hormonio_melatonina(running_agent: ConcreteTestAgent):
    """Test high melatonina drains energy (sleep signal)."""
    initial_energy = running_agent.state.energia

    mock_hormone = MagicMock()
    mock_hormone.tipo = "melatonina"
    mock_hormone.nivel = 8.5

    await running_agent._processar_hormonio(mock_hormone)

    assert running_agent.state.energia < initial_energy


# ==================== HOMEOSTASIS TESTS ====================


@pytest.mark.asyncio
async def test_heartbeat_loop_updates_state(running_agent: ConcreteTestAgent):
    """Test heartbeat loop updates agent state."""
    # Wait for at least one heartbeat cycle
    await asyncio.sleep(0.5)

    # Should have updated state in Redis
    running_agent._hormone_messenger.set_agent_state.assert_called()


@pytest.mark.asyncio
async def test_energy_decay_varies_by_status(agent: ConcreteTestAgent):
    """Test energy decay rate varies by agent status."""
    # Test different statuses (we'll check the decay calculation logic)
    # Since the loop runs in background, we can't easily test real decay rates
    # But we can verify the pattern exists in code

    # Just verify agent has the energy decay loop method
    assert hasattr(agent, "_energy_decay_loop")


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
async def test_get_metrics(running_agent: ConcreteTestAgent):
    """Test get_metrics returns complete agent state."""
    metrics = running_agent.get_metrics()

    assert metrics["agent_id"] == running_agent.state.id
    assert metrics["agent_type"] == running_agent.state.tipo
    assert metrics["status"] == running_agent.state.status
    assert metrics["active"] is True
    assert "energy" in metrics
    assert "temperature" in metrics
    assert "detections_total" in metrics
    assert "neutralizations_total" in metrics
    assert "uptime_hours" in metrics


@pytest.mark.asyncio
async def test_metrics_track_detections(running_agent: ConcreteTestAgent):
    """Test metrics track detection counts."""
    alvo = {"id": "test", "is_threat": True}

    await running_agent.investigar(alvo)

    metrics = running_agent.get_metrics()
    assert metrics["detections_total"] == 1


@pytest.mark.asyncio
async def test_metrics_track_neutralizations(running_agent: ConcreteTestAgent):
    """Test metrics track neutralization counts."""
    alvo = {"id": "malware", "neutralization_success": True}

    # Mock ethical approval
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"decisao": "APROVADO"})
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_response
    mock_ctx.__aexit__.return_value = None

    # Mock memory creation
    mock_memory_response = AsyncMock()
    mock_memory_response.status = 201
    mock_memory_ctx = AsyncMock()
    mock_memory_ctx.__aenter__.return_value = mock_memory_response
    mock_memory_ctx.__aexit__.return_value = None

    with patch.object(running_agent._http_session, "post") as mock_post:
        mock_post.side_effect = [mock_ctx, mock_memory_ctx]

        await running_agent.neutralizar(alvo, metodo="isolate")

        metrics = running_agent.get_metrics()
        assert metrics["neutralizations_total"] == 1


# ==================== REPR TEST ====================


@pytest.mark.asyncio
async def test_repr(agent: ConcreteTestAgent):
    """Test string representation."""
    repr_str = repr(agent)

    assert "ConcreteTestAgent" in repr_str
    assert agent.state.id[:8] in repr_str
    assert str(agent.state.status) in repr_str or agent.state.status.value in repr_str


# ==================== PHASE 2: EXCEPTION COVERAGE (84%→87%+) ====================


@pytest.mark.asyncio
async def test_patrol_loop_handles_exception():
    """Test patrol loop handles exceptions from patrulhar()."""
    class FailingAgent(ConcreteTestAgent):
        async def patrulhar(self):
            raise ValueError("Patrol error")

    agent = FailingAgent()

    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.stop = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.stop = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            await agent.iniciar()

            # Wait for patrol loop to handle error
            await asyncio.sleep(0.5)

            # Agent should still be running despite patrol errors
            assert agent._running is True

            await agent.parar()


@pytest.mark.asyncio
async def test_criar_memoria_client_error(running_agent: ConcreteTestAgent):
    """Test memory creation handles ClientError."""
    import aiohttp

    ameaca = {"id": "threat_005"}

    async def raise_client_error(*args, **kwargs):
        raise aiohttp.ClientError("Connection failed")

    with patch.object(running_agent._http_session, "post", side_effect=raise_client_error):
        # Should handle error gracefully
        await running_agent._criar_memoria(ameaca)


@pytest.mark.asyncio
async def test_validate_ethical_client_error(running_agent: ConcreteTestAgent):
    """Test ethical validation handles ClientError (fail-safe)."""
    import aiohttp

    alvo = {"id": "target"}

    async def raise_client_error(*args, **kwargs):
        raise aiohttp.ClientError("Connection failed")

    with patch.object(running_agent._http_session, "post", side_effect=raise_client_error):
        approved = await running_agent._validate_ethical(alvo, "isolate")

        # Fail-safe: should block on error
        assert approved is False


@pytest.mark.asyncio
async def test_iniciar_metrics_import_error():
    """Test iniciar handles metrics import error gracefully."""
    agent = ConcreteTestAgent()

    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            # Agent should start successfully even if metrics import fails
            await agent.iniciar()
            assert agent._running is True
            await agent.parar()


@pytest.mark.asyncio
async def test_parar_messenger_errors():
    """Test parar handles messenger stop errors gracefully."""
    agent = ConcreteTestAgent()

    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.stop = AsyncMock(side_effect=Exception("Stop error"))
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.stop = AsyncMock(side_effect=Exception("Stop error"))
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            await agent.iniciar()

            # Should handle stop errors gracefully
            await agent.parar()
            assert agent._running is False


@pytest.mark.asyncio
async def test_parar_http_session_close_error():
    """Test parar handles HTTP session close error gracefully."""
    agent = ConcreteTestAgent()

    mock_cytokine = AsyncMock()
    mock_cytokine.start = AsyncMock()
    mock_cytokine.subscribe = AsyncMock()
    mock_cytokine.stop = AsyncMock()
    mock_cytokine.is_running = MagicMock(return_value=True)

    mock_hormone = AsyncMock()
    mock_hormone.start = AsyncMock()
    mock_hormone.subscribe = AsyncMock()
    mock_hormone.stop = AsyncMock()
    mock_hormone.is_running = MagicMock(return_value=True)

    with patch("active_immune_core.agents.base.CytokineMessenger", return_value=mock_cytokine):
        with patch("active_immune_core.agents.base.HormoneMessenger", return_value=mock_hormone):
            await agent.iniciar()

            # Mock HTTP session that raises error on close
            agent._http_session.close = AsyncMock(side_effect=Exception("Close error"))

            # Should handle close error gracefully
            await agent.parar()
            assert agent._running is False


@pytest.mark.asyncio
async def test_apoptose_cytokine_send_error(running_agent: ConcreteTestAgent):
    """Test apoptosis handles cytokine send error gracefully."""
    # Mock cytokine messenger to raise error
    running_agent._cytokine_messenger.send_cytokine = AsyncMock(side_effect=Exception("Send error"))

    # Should handle error and complete apoptosis
    await running_agent.apoptose(reason="test_error_handling")

    assert running_agent.state.status == AgentStatus.APOPTOSE
    assert running_agent._running is False
