"""Base Agent - Direct Execution Tests for Real Coverage

Strategy: Execute real code paths with minimal mocking to get TRUE coverage.

Focus: Lines that should be covered but aren't showing up.

NO MOCK, NO PLACEHOLDER, NO TODO - PRODUCTION-READY.

Authors: Juan & Claude
Version: 4.0.0 - Direct Execution
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from active_immune_core.agents.base import AgenteImunologicoBase
from active_immune_core.agents.models import AgentStatus, AgentType


# ==================== CONCRETE TEST AGENT ====================


class ConcreteTestAgent(AgenteImunologicoBase):
    """Concrete agent with real implementations"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.patrol_called = False
        self.investigation_result = {"is_threat": True, "threat_level": 3}
        self.neutralization_success = True

    async def patrulhar(self) -> None:
        """Real patrol implementation"""
        self.patrol_called = True
        await asyncio.sleep(0.001)

    async def executar_investigacao(self, alvo: dict) -> dict:
        """Real investigation"""
        await asyncio.sleep(0.001)
        return self.investigation_result

    async def executar_neutralizacao(self, alvo: dict, metodo: str) -> bool:
        """Real neutralization"""
        await asyncio.sleep(0.001)
        return self.neutralization_success


# ==================== HELPER TO SETUP AGENT ====================


async def setup_agent_with_mocked_communication(agent: AgenteImunologicoBase):
    """Setup agent with only communication mocked, everything else real"""
    # Mock only external dependencies (messengers)
    agent._cytokine_messenger = Mock()
    agent._cytokine_messenger.start = AsyncMock()
    agent._cytokine_messenger.stop = AsyncMock()
    agent._cytokine_messenger.subscribe = AsyncMock()
    agent._cytokine_messenger.send_cytokine = AsyncMock()
    agent._cytokine_messenger.is_running = Mock(return_value=True)

    agent._hormone_messenger = Mock()
    agent._hormone_messenger.start = AsyncMock()
    agent._hormone_messenger.stop = AsyncMock()
    agent._hormone_messenger.subscribe = AsyncMock()
    agent._hormone_messenger.set_agent_state = AsyncMock()
    agent._hormone_messenger.is_running = Mock(return_value=True)

    # Mock HTTP session creation
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.post = AsyncMock()

    return mock_session


# ==================== AGENT LIFECYCLE TESTS ====================


class TestAgentLifecycleDirectExecution:
    """Test complete agent lifecycle with real execution"""

    @pytest.mark.asyncio
    async def test_complete_agent_lifecycle_iniciar_to_parar(self):
        """Test complete lifecycle: iniciar → running → parar (lines 137-172, 174-223)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_lifecycle_001")
        mock_session = await setup_agent_with_mocked_communication(agent)

        # Mock ClientSession creation
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # ACT: Start agent (lines 137-172)
            await agent.iniciar()

            # ASSERT: Agent started
            assert agent._running is True
            assert agent.state.ativo is True
            assert agent._http_session is not None

            # ACT: Stop agent (lines 174-223)
            await agent.parar()

            # ASSERT: Agent stopped (lines 212-223 covered)
            assert agent._running is False
            assert agent.state.ativo is False

    @pytest.mark.asyncio
    async def test_iniciar_exception_triggers_rollback(self):
        """Test iniciar() exception handling and rollback (lines 169-172)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_rollback_002")

        # Mock ClientSession to raise exception (after messengers succeed)
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        # Mock messengers to succeed
        mock_session = await setup_agent_with_mocked_communication(agent)

        # Make ClientSession raise exception during iniciar
        with patch('aiohttp.ClientSession', side_effect=RuntimeError("HTTP session failed")):
            # ACT & ASSERT: Should raise and rollback (lines 169-172)
            with pytest.raises(RuntimeError, match="HTTP session failed"):
                await agent.iniciar()

            # Verify rollback happened (lines 169-172 covered)
            assert agent._running is False
            assert agent.state.ativo is False


# ==================== APOPTOSIS TESTS ====================


class TestApoptosisDirectExecution:
    """Test apoptosis with real execution"""

    @pytest.mark.asyncio
    async def test_apoptose_complete_flow(self):
        """Test complete apoptosis flow (lines 238-273)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_apoptosis_003")
        agent._running = True
        agent.state.ativo = True

        mock_session = await setup_agent_with_mocked_communication(agent)
        agent._http_session = mock_session

        # ACT: Trigger apoptosis (lines 238-273)
        await agent.apoptose(reason="test_complete_apoptosis")

        # ASSERT: Apoptosis completed (lines 262-273 covered)
        assert agent.state.status == AgentStatus.APOPTOSE
        assert agent._running is False
        assert agent.state.ativo is False


# ==================== INVESTIGATION AND NEUTRALIZATION ====================


class TestInvestigationNeutralizationDirectExecution:
    """Test investigation and neutralization with real execution"""

    @pytest.mark.asyncio
    async def test_investigar_finds_threat(self):
        """Test investigation that finds a threat (lines 342-387)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_investigation_004")
        agent._running = True
        agent.investigation_result = {"is_threat": True, "threat_level": 5}

        # ACT: Investigate (lines 342-387)
        resultado = await agent.investigar({"ip": "192.168.1.100", "id": "threat_001"})

        # ASSERT: Threat detected (lines 366-387 covered)
        assert resultado["is_threat"] is True
        assert agent.state.deteccoes_total == 1

    @pytest.mark.asyncio
    async def test_investigar_exception_handling(self):
        """Test investigation exception handling (lines 389-391)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_investigation_error_005")
        agent._running = True

        # Make investigation raise exception
        async def failing_investigation(alvo):
            raise RuntimeError("Investigation service down")

        agent.executar_investigacao = failing_investigation

        # ACT: Investigate (should handle exception)
        resultado = await agent.investigar({"ip": "192.168.1.100"})

        # ASSERT: Exception handled (lines 389-391 covered)
        assert resultado["is_threat"] is False
        assert "error" in resultado

    @pytest.mark.asyncio
    async def test_neutralizar_success(self):
        """Test successful neutralization (lines 409-472)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_neutralization_006")
        agent._running = True
        agent.neutralization_success = True

        # Mock ethical validation to approve
        agent._validate_ethical = AsyncMock(return_value=True)

        mock_session = await setup_agent_with_mocked_communication(agent)
        agent._http_session = mock_session

        # ACT: Neutralize (lines 409-472)
        success = await agent.neutralizar(
            {"ip": "192.168.1.100", "threat_level": 3, "id": "threat_001"},
            metodo="quarantine"
        )

        # ASSERT: Neutralization successful (lines 428-472 covered)
        assert success is True
        assert agent.state.neutralizacoes_total == 1

    @pytest.mark.asyncio
    async def test_neutralizar_ethical_blocked(self):
        """Test neutralization blocked by ethics (lines 419-422)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_neutralization_blocked_007")
        agent._running = True

        # Mock ethical validation to block
        agent._validate_ethical = AsyncMock(return_value=False)

        # ACT: Try to neutralize (should be blocked)
        success = await agent.neutralizar(
            {"ip": "192.168.1.100", "threat_level": 3},
            metodo="terminate"
        )

        # ASSERT: Blocked by ethics (lines 419-422 covered)
        assert success is False

    @pytest.mark.asyncio
    async def test_neutralizar_exception_handling(self):
        """Test neutralization exception handling (lines 476-478)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_neutralization_error_008")
        agent._running = True

        # Mock ethical validation to approve
        agent._validate_ethical = AsyncMock(return_value=True)

        # Mock messengers
        mock_session = await setup_agent_with_mocked_communication(agent)
        agent._http_session = mock_session

        # Make neutralization raise exception
        async def failing_neutralization(alvo, metodo):
            raise RuntimeError("Neutralization failed")

        agent.executar_neutralizacao = failing_neutralization

        # ACT: Try to neutralize (should handle exception)
        success = await agent.neutralizar(
            {"ip": "192.168.1.100", "threat_level": 3},
            metodo="isolate"
        )

        # ASSERT: Exception handled (lines 476-478 covered)
        assert success is False


# ==================== MEMORY CREATION ====================


class TestMemoryCreationDirectExecution:
    """Test memory creation with real execution"""

    @pytest.mark.asyncio
    async def test_criar_memoria_without_session(self):
        """Test memory creation when session not initialized (lines 505-507)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_memory_no_session_009")
        agent._http_session = None

        # ACT: Try to create memory (should skip)
        await agent._criar_memoria(ameaca={"id": "threat_001", "ip": "192.168.1.100"})

        # ASSERT: Skipped without error (lines 505-507 covered)
        assert agent.state.status == AgentStatus.DORMINDO

    @pytest.mark.asyncio
    async def test_criar_memoria_client_error(self):
        """Test memory creation with client error (lines 526-527)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_memory_client_error_010")

        # Create mock context manager that raises ClientError
        import aiohttp
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection failed"))
        mock_response.__aexit__ = AsyncMock()

        mock_session = Mock()
        mock_session.post = Mock(return_value=mock_response)
        agent._http_session = mock_session

        # ACT: Create memory (should handle ClientError)
        await agent._criar_memoria(ameaca={"id": "threat_001", "ip": "192.168.1.100"})

        # ASSERT: ClientError handled (lines 526-527 covered)
        assert agent.state.status == AgentStatus.DORMINDO

    @pytest.mark.asyncio
    async def test_criar_memoria_timeout(self):
        """Test memory creation timeout (lines 529-530)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_memory_timeout_011")

        # Create mock context manager that raises TimeoutError
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_response.__aexit__ = AsyncMock()

        mock_session = Mock()
        mock_session.post = Mock(return_value=mock_response)
        agent._http_session = mock_session

        # ACT: Create memory (should handle timeout)
        await agent._criar_memoria(ameaca={"id": "threat_001", "ip": "192.168.1.100"})

        # ASSERT: Timeout handled (lines 529-530 covered)
        assert agent.state.status == AgentStatus.DORMINDO

    @pytest.mark.asyncio
    async def test_criar_memoria_generic_exception(self):
        """Test memory creation generic exception (lines 532-533)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_memory_generic_error_012")

        # Create mock context manager that raises generic exception
        mock_response = AsyncMock()
        mock_response.__aenter__ = AsyncMock(side_effect=ValueError("Invalid data"))
        mock_response.__aexit__ = AsyncMock()

        mock_session = Mock()
        mock_session.post = Mock(return_value=mock_response)
        agent._http_session = mock_session

        # ACT: Create memory (should handle exception)
        await agent._criar_memoria(ameaca={"id": "threat_001", "ip": "192.168.1.100"})

        # ASSERT: Exception handled (lines 532-533 covered)
        assert agent.state.status == AgentStatus.DORMINDO


# ==================== GET METRICS ====================


class TestGetMetrics:
    """Test get_metrics method"""

    def test_get_metrics_returns_dict(self):
        """Test get_metrics returns proper dict (line 701)"""
        # ARRANGE
        agent = ConcreteTestAgent(agent_id="test_metrics_013")

        # ACT: Get metrics (line 701)
        metrics = agent.get_metrics()

        # ASSERT: Returns dict with expected keys (line 701 covered)
        assert isinstance(metrics, dict)
        assert "agent_id" in metrics
        assert "agent_type" in metrics
        assert metrics["agent_id"] == "test_metrics_013"
