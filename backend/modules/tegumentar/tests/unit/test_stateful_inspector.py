"""
Testes unitários para backend.modules.tegumentar.derme.stateful_inspector

Testa o StatefulInspector - guardião de estado de conexões:
- Tracking de conexões TCP/UDP
- Detecção de SYN flood
- Detecção de evasão (TCP sem flags)
- Detecção de high throughput
- Persistência em PostgreSQL
- Eviction de conexões idle

EM NOME DE JESUS - CÓDIGO QUE ECOA PELAS ERAS!
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.stateful_inspector import (
    ConnectionState,
    FlowObservation,
    InspectorAction,
    InspectorDecision,
    StatefulInspector,
)


@pytest.fixture
def settings():
    """Settings de teste."""
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
    )


@pytest.fixture
def mock_pool():
    """Mock do asyncpg.Pool."""
    pool = MagicMock()
    pool.close = AsyncMock()

    # Mock acquire context manager
    conn = MagicMock()
    conn.execute = AsyncMock()

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)

    pool.acquire = MagicMock(return_value=acquire_cm)

    return pool


@pytest.fixture
def observation():
    """FlowObservation de teste."""
    return FlowObservation(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        src_port=54321,
        dst_port=443,
        protocol="TCP",
        flags="SYN",
        payload_size=1024,
        timestamp=time.time(),
    )


class TestStatefulInspectorInitialization:
    """Testa inicialização do StatefulInspector."""

    def test_initializes_with_settings(self, settings):
        """Deve inicializar com settings fornecido."""
        inspector = StatefulInspector(settings)
        assert inspector._settings is settings
        assert inspector._pool is None
        assert inspector._state == {}
        assert inspector._lock is not None

    def test_initializes_with_default_settings(self):
        """Deve usar get_settings() quando settings não fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.stateful_inspector.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            inspector = StatefulInspector()

            mock_get_settings.assert_called_once()
            assert inspector._settings is mock_settings

    def test_creates_empty_state_dict(self, settings):
        """Deve criar dict vazio para tracking de conexões."""
        inspector = StatefulInspector(settings)
        assert isinstance(inspector._state, dict)
        assert len(inspector._state) == 0

    def test_creates_asyncio_lock(self, settings):
        """Deve criar asyncio.Lock para thread safety."""
        inspector = StatefulInspector(settings)
        assert isinstance(inspector._lock, asyncio.Lock)


class TestStartupShutdown:
    """Testa lifecycle do StatefulInspector."""

    @pytest.mark.asyncio
    async def test_startup_creates_pool(self, settings):
        """startup() deve criar connection pool."""
        with patch(
            "backend.modules.tegumentar.derme.stateful_inspector.asyncpg"
        ) as mock_asyncpg:
            mock_pool = MagicMock()
            mock_pool.acquire = MagicMock()
            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

            inspector = StatefulInspector(settings)

            # Mock acquire for _initialise_schema
            conn = MagicMock()
            conn.execute = AsyncMock()
            acquire_cm = MagicMock()
            acquire_cm.__aenter__ = AsyncMock(return_value=conn)
            acquire_cm.__aexit__ = AsyncMock(return_value=None)
            mock_pool.acquire.return_value = acquire_cm

            await inspector.startup()

            mock_asyncpg.create_pool.assert_called_once_with(
                settings.postgres_dsn, min_size=2, max_size=10
            )
            assert inspector._pool is mock_pool

    @pytest.mark.asyncio
    async def test_startup_calls_initialise_schema(self, settings):
        """startup() deve chamar _initialise_schema()."""
        with patch(
            "backend.modules.tegumentar.derme.stateful_inspector.asyncpg"
        ) as mock_asyncpg:
            mock_pool = MagicMock()
            conn = MagicMock()
            conn.execute = AsyncMock()

            acquire_cm = MagicMock()
            acquire_cm.__aenter__ = AsyncMock(return_value=conn)
            acquire_cm.__aexit__ = AsyncMock(return_value=None)
            mock_pool.acquire.return_value = acquire_cm

            mock_asyncpg.create_pool = AsyncMock(return_value=mock_pool)

            inspector = StatefulInspector(settings)
            await inspector.startup()

            # Verifica que CREATE TABLE foi executado
            conn.execute.assert_called_once()
            call_args = conn.execute.call_args[0][0]
            assert "CREATE TABLE IF NOT EXISTS tegumentar_sessions" in call_args

    @pytest.mark.asyncio
    async def test_startup_does_not_recreate_pool(self, settings, mock_pool):
        """startup() não deve recriar pool se já existe."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        with patch(
            "backend.modules.tegumentar.derme.stateful_inspector.asyncpg"
        ) as mock_asyncpg:
            await inspector.startup()

            # create_pool não deve ser chamado
            mock_asyncpg.create_pool.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_closes_pool(self, settings, mock_pool):
        """shutdown() deve fechar connection pool."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        await inspector.shutdown()

        mock_pool.close.assert_called_once()
        assert inspector._pool is None

    @pytest.mark.asyncio
    async def test_shutdown_handles_no_pool(self, settings):
        """shutdown() não deve falhar se pool é None."""
        inspector = StatefulInspector(settings)
        assert inspector._pool is None

        # Não deve lançar exceção
        await inspector.shutdown()


class TestProcessNewConnection:
    """Testa process() para novas conexões."""

    @pytest.mark.asyncio
    async def test_creates_new_connection_state(self, settings, observation):
        """Deve criar ConnectionState para nova conexão."""
        inspector = StatefulInspector(settings)

        decision = await inspector.process(observation)

        key = ("192.168.1.100", "10.0.0.1", 54321, 443, "TCP")
        assert key in inspector._state
        state = inspector._state[key]
        assert state.packets == 1
        assert state.bytes == 1024
        assert state.syn_seen is True  # SYN flag presente

    @pytest.mark.asyncio
    async def test_increments_packet_count(self, settings, observation):
        """Deve incrementar contador de pacotes."""
        inspector = StatefulInspector(settings)

        await inspector.process(observation)
        await inspector.process(observation)

        key = ("192.168.1.100", "10.0.0.1", 54321, 443, "TCP")
        assert inspector._state[key].packets == 2

    @pytest.mark.asyncio
    async def test_increments_bytes_count(self, settings, observation):
        """Deve incrementar contador de bytes."""
        inspector = StatefulInspector(settings)

        await inspector.process(observation)
        await inspector.process(observation)

        key = ("192.168.1.100", "10.0.0.1", 54321, 443, "TCP")
        assert inspector._state[key].bytes == 2048  # 1024 * 2

    @pytest.mark.asyncio
    async def test_updates_last_seen(self, settings, observation):
        """Deve atualizar timestamp last_seen."""
        inspector = StatefulInspector(settings)

        first_time = time.time()
        observation.timestamp = first_time
        await inspector.process(observation)

        second_time = first_time + 10
        observation.timestamp = second_time
        await inspector.process(observation)

        key = ("192.168.1.100", "10.0.0.1", 54321, 443, "TCP")
        assert inspector._state[key].last_seen == second_time


class TestProcessTCPFlags:
    """Testa process() com flags TCP."""

    @pytest.mark.asyncio
    async def test_sets_syn_seen_on_syn_flag(self, settings):
        """Deve marcar syn_seen quando flag SYN presente."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=100,
        )

        await inspector.process(obs)

        key = ("1.1.1.1", "2.2.2.2", 1234, 80, "TCP")
        assert inspector._state[key].syn_seen is True

    @pytest.mark.asyncio
    async def test_sets_established_on_syn_ack(self, settings):
        """Deve marcar established quando SYN+ACK presente."""
        inspector = StatefulInspector(settings)

        # Primeiro pacote: SYN
        obs1 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=100,
        )
        await inspector.process(obs1)

        # Segundo pacote: ACK (após SYN)
        obs2 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        await inspector.process(obs2)

        key = ("1.1.1.1", "2.2.2.2", 1234, 80, "TCP")
        assert inspector._state[key].established is True

    @pytest.mark.asyncio
    async def test_does_not_set_established_without_syn(self, settings):
        """Não deve marcar established se SYN não foi visto."""
        inspector = StatefulInspector(settings)

        # Apenas ACK, sem SYN prévio
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        await inspector.process(obs)

        key = ("1.1.1.1", "2.2.2.2", 1234, 80, "TCP")
        assert inspector._state[key].established is False


class TestEvaluateTCPWithoutFlags:
    """Testa _evaluate() para TCP sem flags (evasão)."""

    @pytest.mark.asyncio
    async def test_detects_tcp_without_flags(self, settings):
        """Deve detectar TCP packet sem flags no primeiro pacote."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags=None,  # SEM FLAGS
            payload_size=100,
        )

        decision = await inspector.process(obs)

        assert decision.action == InspectorAction.INSPECT_DEEP
        assert "without flags" in decision.reason.lower()
        assert "evasion" in decision.reason.lower()


class TestEvaluateSYNFlood:
    """Testa _evaluate() para detecção de SYN flood."""

    @pytest.mark.asyncio
    async def test_detects_syn_flood(self, settings):
        """Deve detectar SYN flood (>10 SYNs sem estabelecer)."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=100,
        )

        # Enviar 11 SYNs sem ACK
        for _ in range(11):
            decision = await inspector.process(obs)

        # Último deve ser DROP
        assert decision.action == InspectorAction.DROP
        assert "SYN flood" in decision.reason

    @pytest.mark.asyncio
    async def test_does_not_flag_established_connection(self, settings):
        """Não deve flaggar SYN flood em conexão estabelecida."""
        inspector = StatefulInspector(settings)

        # SYN
        obs_syn = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=100,
        )
        await inspector.process(obs_syn)

        # ACK (estabelece)
        obs_ack = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        await inspector.process(obs_ack)

        # Mais 10 SYNs (já estabelecido)
        for _ in range(10):
            decision = await inspector.process(obs_syn)

        # Não deve ser DROP porque established=True
        assert decision.action != InspectorAction.DROP


class TestEvaluateHighThroughput:
    """Testa _evaluate() para detecção de high throughput."""

    @pytest.mark.asyncio
    async def test_detects_high_throughput(self, settings):
        """Deve detectar high throughput (>10MB em <5s)."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=11_000_000,  # 11MB em um pacote
        )

        decision = await inspector.process(obs)

        assert decision.action == InspectorAction.INSPECT_DEEP
        assert "throughput" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_flags_recent_high_throughput(self, settings):
        """Deve flaggar throughput alto se última atividade foi <5s atrás."""
        inspector = StatefulInspector(settings)

        # Primeiro pacote (5MB)
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=5_000_000,
        )
        await inspector.process(obs)

        # Segundo pacote (6MB) imediatamente depois
        obs2 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=6_000_000,
        )
        decision = await inspector.process(obs2)

        # Total 11MB em <5s → INSPECT_DEEP
        assert decision.action == InspectorAction.INSPECT_DEEP
        assert "throughput" in decision.reason.lower()


class TestEvaluatePass:
    """Testa _evaluate() para tráfego normal (PASS)."""

    @pytest.mark.asyncio
    async def test_returns_pass_for_normal_traffic(self, settings):
        """Deve retornar PASS para tráfego normal."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )

        decision = await inspector.process(obs)

        assert decision.action == InspectorAction.PASS
        assert "no anomaly" in decision.reason.lower()


class TestPersistState:
    """Testa _persist_state() para persistência em PostgreSQL."""

    @pytest.mark.asyncio
    async def test_persist_state_writes_to_db(self, settings, mock_pool):
        """Deve escrever estado no PostgreSQL."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=100,
        )

        # SYN flood para forçar persistência (action != PASS)
        for _ in range(11):
            await inspector.process(obs)

        # Verifica que INSERT foi chamado
        conn = await mock_pool.acquire().__aenter__()
        conn.execute.assert_called()

        call_args = conn.execute.call_args[0]
        assert "INSERT INTO tegumentar_sessions" in call_args[0]
        assert "ON CONFLICT" in call_args[0]

    @pytest.mark.asyncio
    async def test_persist_state_does_not_persist_pass(self, settings, mock_pool):
        """Não deve persistir quando action == PASS."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )

        await inspector.process(obs)  # Deve retornar PASS

        # execute não deve ter sido chamado
        conn = await mock_pool.acquire().__aenter__()
        conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_persist_state_returns_early_when_no_pool(self, settings):
        """Deve retornar early quando pool é None."""
        inspector = StatefulInspector(settings)
        assert inspector._pool is None

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags=None,  # Vai gerar INSPECT_DEEP
            payload_size=100,
        )

        # Não deve lançar exceção mesmo sem pool
        await inspector.process(obs)


class TestEvictIdleConnections:
    """Testa _evict_idle_connections() para limpeza de memória."""

    @pytest.mark.asyncio
    async def test_evicts_idle_connections(self, settings):
        """Deve remover conexões idle >300s."""
        inspector = StatefulInspector(settings)

        # Criar conexão antiga
        obs_old = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
            timestamp=time.time() - 400,  # 400s atrás
        )
        await inspector.process(obs_old)

        # Criar conexão recente
        obs_new = FlowObservation(
            src_ip="3.3.3.3",
            dst_ip="4.4.4.4",
            src_port=5678,
            dst_port=443,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        await inspector.process(obs_new)

        assert len(inspector._state) == 1  # Apenas a nova
        assert ("3.3.3.3", "4.4.4.4", 5678, 443, "TCP") in inspector._state
        assert ("1.1.1.1", "2.2.2.2", 1234, 80, "TCP") not in inspector._state

    @pytest.mark.asyncio
    async def test_keeps_active_connections(self, settings):
        """Deve manter conexões ativas (<300s)."""
        inspector = StatefulInspector(settings)

        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        await inspector.process(obs)
        await inspector.process(obs)

        assert len(inspector._state) == 1


class TestInitialiseSchema:
    """Testa _initialise_schema() para criação de tabela."""

    @pytest.mark.asyncio
    async def test_creates_table_schema(self, settings, mock_pool):
        """Deve criar tabela tegumentar_sessions."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        await inspector._initialise_schema()

        conn = await mock_pool.acquire().__aenter__()
        conn.execute.assert_called_once()

        call_args = conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS tegumentar_sessions" in call_args
        assert "src_ip inet NOT NULL" in call_args
        assert "PRIMARY KEY" in call_args

    @pytest.mark.asyncio
    async def test_returns_early_when_no_pool(self, settings):
        """Deve retornar early quando pool é None."""
        inspector = StatefulInspector(settings)
        assert inspector._pool is None

        # Não deve lançar exceção
        await inspector._initialise_schema()


class TestNonTCPProtocols:
    """Testa handling de protocolos não-TCP (UDP, ICMP)."""

    @pytest.mark.asyncio
    async def test_handles_udp_traffic(self, settings, mock_pool):
        """Deve processar tráfego UDP corretamente (branches 99->105, 152->172)."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        # UDP não tem flags, não deve entrar no bloco TCP
        observation = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=53,
            dst_port=53,
            protocol="UDP",
            flags=None,  # UDP não tem TCP flags
            payload_size=512,
        )

        decision = await inspector.process(observation)

        # UDP normal deve passar
        assert decision.action == InspectorAction.PASS
        assert decision.connection_state.packets == 1
        assert decision.connection_state.bytes == 512
        # TCP-specific state não deve ser setado
        assert decision.connection_state.syn_seen is False
        assert decision.connection_state.established is False

    @pytest.mark.asyncio
    async def test_handles_icmp_traffic(self, settings, mock_pool):
        """Deve processar tráfego ICMP corretamente."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        observation = FlowObservation(
            src_ip="10.0.0.1",
            dst_ip="10.0.0.2",
            src_port=0,
            dst_port=0,
            protocol="ICMP",
            flags=None,
            payload_size=64,
        )

        decision = await inspector.process(observation)

        # ICMP deve passar normalmente
        assert decision.action == InspectorAction.PASS

    @pytest.mark.asyncio
    async def test_tcp_with_ack_but_no_syn_seen(self, settings, mock_pool):
        """TCP com ACK mas sem SYN prévio não deve marcar established (branch 102->105)."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        # ACK sem SYN prévio (possível pacote out-of-order ou scan)
        observation = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            flags="A",  # ACK sem SYN prévio
            payload_size=100,
        )

        decision = await inspector.process(observation)

        # Deve processar mas não marcar established (branch 102 false)
        assert decision.connection_state.established is False
        assert decision.connection_state.syn_seen is False
        assert decision.connection_state.packets == 1

    @pytest.mark.asyncio
    async def test_udp_multiple_packets_existing_connection(self, settings, mock_pool):
        """UDP com múltiplos pacotes deve atualizar state sem entrar bloco TCP (branch 99->105)."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        # Primeiro pacote UDP (cria conexão)
        obs1 = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=53,
            dst_port=53,
            protocol="UDP",
            flags=None,
            payload_size=256,
        )
        await inspector.process(obs1)

        # Segundo pacote UDP (conexão existente, entra else linha 88, depois skip TCP linha 99->105)
        obs2 = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="8.8.8.8",
            src_port=53,
            dst_port=53,
            protocol="UDP",
            flags=None,
            payload_size=512,
        )
        decision2 = await inspector.process(obs2)

        # Deve ter 2 pacotes, 768 bytes total
        assert decision2.connection_state.packets == 2
        assert decision2.connection_state.bytes == 768
        # Não deve ter setado TCP state
        assert decision2.connection_state.syn_seen is False
        assert decision2.connection_state.established is False

    @pytest.mark.asyncio
    async def test_tcp_with_fin_but_no_ack(self, settings, mock_pool):
        """TCP com FIN mas sem ACK não deve marcar established (branch 102->105)."""
        inspector = StatefulInspector(settings)
        inspector._pool = mock_pool

        # Primeiro: SYN para marcar syn_seen
        obs1 = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            flags="S",
            payload_size=0,
        )
        await inspector.process(obs1)

        # Segundo: FIN sem ACK (linha 102: "A" not in flags, então skip linha 103)
        obs2 = FlowObservation(
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=80,
            protocol="TCP",
            flags="F",  # FIN sem ACK
            payload_size=100,
        )
        decision2 = await inspector.process(obs2)

        # syn_seen deve estar True (do primeiro pacote)
        assert decision2.connection_state.syn_seen is True
        # Mas established False (linha 102 falhou: "A" not in flags)
        assert decision2.connection_state.established is False
        assert decision2.connection_state.packets == 2


class TestDataclasses:
    """Testa dataclasses (FlowObservation, ConnectionState, InspectorDecision)."""

    def test_flow_observation_has_required_fields(self):
        """FlowObservation deve ter todos os campos obrigatórios."""
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="SYN",
            payload_size=1024,
        )

        assert obs.src_ip == "1.1.1.1"
        assert obs.dst_ip == "2.2.2.2"
        assert obs.src_port == 1234
        assert obs.dst_port == 80
        assert obs.protocol == "TCP"
        assert obs.flags == "SYN"
        assert obs.payload_size == 1024
        assert obs.timestamp > 0  # Auto-gerado

    def test_connection_state_has_defaults(self):
        """ConnectionState deve ter valores padrão."""
        state = ConnectionState()

        assert state.packets == 0
        assert state.bytes == 0
        assert state.last_seen > 0  # Auto-gerado
        assert state.syn_seen is False
        assert state.established is False

    def test_inspector_decision_has_required_fields(self):
        """InspectorDecision deve ter action, reason e connection_state."""
        state = ConnectionState(packets=10, bytes=1024)
        decision = InspectorDecision(
            action=InspectorAction.DROP,
            reason="Test reason",
            connection_state=state,
        )

        assert decision.action == InspectorAction.DROP
        assert decision.reason == "Test reason"
        assert decision.connection_state is state
