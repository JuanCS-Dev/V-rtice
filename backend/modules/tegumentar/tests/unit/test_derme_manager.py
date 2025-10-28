"""
Testes unitários para backend.modules.tegumentar.derme.manager

Testa o DermeLayer que coordena:
- StatefulInspector
- DeepPacketInspector
- LangerhansCell
- SensoryProcessor

Padrão Pagani: Mocks dos componentes internos, validação de integração.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.deep_inspector import InspectionResult
from backend.modules.tegumentar.derme.manager import DermeLayer
from backend.modules.tegumentar.derme.stateful_inspector import (
    ConnectionState,
    FlowObservation,
    InspectorAction,
    InspectorDecision,
)


@pytest.fixture
def settings():
    """Settings de teste."""
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
        kafka_bootstrap_servers="localhost:9092",
    )


@pytest.fixture
def mock_stateful():
    """Mock do StatefulInspector."""
    mock = MagicMock()
    mock.startup = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.process = AsyncMock()
    return mock


@pytest.fixture
def mock_dpi():
    """Mock do DeepPacketInspector."""
    mock = MagicMock()
    mock.inspect = MagicMock()
    return mock


@pytest.fixture
def mock_langerhans():
    """Mock da LangerhansCell."""
    mock = MagicMock()
    mock.startup = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.capture_antigen = AsyncMock()
    return mock


@pytest.fixture
def mock_sensory():
    """Mock do SensoryProcessor."""
    mock = MagicMock()
    mock.register_event = MagicMock()
    mock.render_snapshot = MagicMock()
    return mock


@pytest.fixture
def observation():
    """FlowObservation de teste."""
    return FlowObservation(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        protocol="TCP",
        src_port=54321,
        dst_port=443,
        flags="SYN",
        payload_size=1024,
    )


class TestDermeLayerInitialization:
    """Testa inicialização do DermeLayer."""

    def test_derme_layer_initializes_with_settings(self, settings):
        """Deve inicializar com settings fornecido."""
        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch("backend.modules.tegumentar.derme.manager.LangerhansCell"), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            assert layer._settings is settings

    def test_derme_layer_initializes_with_default_settings(self):
        """Deve usar get_settings() quando settings não fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.manager.get_settings"
        ) as mock_get, patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector"
        ), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            mock_settings = MagicMock()
            mock_get.return_value = mock_settings

            layer = DermeLayer()

            mock_get.assert_called_once()
            assert layer._settings is mock_settings

    def test_creates_stateful_inspector(self, settings, mock_stateful):
        """Deve criar StatefulInspector."""
        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ) as mock_class, patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)

            mock_class.assert_called_once_with(settings)
            assert layer._stateful is mock_stateful

    def test_creates_dpi(self, settings, mock_dpi):
        """Deve criar DeepPacketInspector."""
        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector",
            return_value=mock_dpi,
        ) as mock_class, patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)

            mock_class.assert_called_once_with(settings)
            assert layer._dpi is mock_dpi

    def test_creates_langerhans_cell(self, settings, mock_langerhans):
        """Deve criar LangerhansCell."""
        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ) as mock_class, patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)

            mock_class.assert_called_once_with(settings)
            assert layer._langerhans is mock_langerhans

    def test_creates_sensory_processor(self, settings, mock_sensory):
        """Deve criar SensoryProcessor."""
        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch("backend.modules.tegumentar.derme.manager.LangerhansCell"), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ) as mock_class:
            layer = DermeLayer(settings)

            mock_class.assert_called_once()
            assert layer._sensory is mock_sensory

    def test_creates_asyncio_lock(self, settings):
        """Deve criar asyncio.Lock."""
        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch("backend.modules.tegumentar.derme.manager.LangerhansCell"), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            assert layer._lock is not None


class TestStartupShutdown:
    """Testa lifecycle do DermeLayer."""

    @pytest.mark.asyncio
    async def test_startup_calls_stateful_startup(
        self, settings, mock_stateful, mock_langerhans
    ):
        """startup() deve inicializar StatefulInspector."""
        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.startup()

            mock_stateful.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_calls_langerhans_startup(
        self, settings, mock_stateful, mock_langerhans
    ):
        """startup() deve inicializar LangerhansCell."""
        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.startup()

            mock_langerhans.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_calls_langerhans_shutdown(
        self, settings, mock_stateful, mock_langerhans
    ):
        """shutdown() deve parar LangerhansCell."""
        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.shutdown()

            mock_langerhans.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_calls_stateful_shutdown(
        self, settings, mock_stateful, mock_langerhans
    ):
        """shutdown() deve parar StatefulInspector."""
        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.shutdown()

            mock_stateful.shutdown.assert_called_once()


class TestProcessPacketDrop:
    """Testa process_packet quando StatefulInspector decide DROP."""

    @pytest.mark.asyncio
    async def test_process_packet_returns_drop_when_stateful_drops(
        self, settings, mock_stateful, mock_sensory, observation
    ):
        """Deve retornar DROP quando StatefulInspector decide DROP."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.DROP,
            reason="Suspicious flow pattern",
            connection_state=ConnectionState(),
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            result = await layer.process_packet(observation, b"payload")

            assert result.action == InspectorAction.DROP
            assert result.confidence == 0.95
            assert "Suspicious flow pattern" in result.reason

    @pytest.mark.asyncio
    async def test_process_packet_registers_drop_event(
        self, settings, mock_stateful, mock_sensory, observation
    ):
        """Deve registrar evento DROP no SensoryProcessor."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.DROP,
            reason="Blocked",
            connection_state=ConnectionState(),
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            await layer.process_packet(observation, b"payload")

            mock_sensory.register_event.assert_called_once()
            call_args = mock_sensory.register_event.call_args[0]
            assert call_args[0] is observation
            assert call_args[1].action == InspectorAction.DROP


class TestProcessPacketPass:
    """Testa process_packet quando StatefulInspector decide PASS."""

    @pytest.mark.asyncio
    async def test_process_packet_returns_pass_when_stateful_passes(
        self, settings, mock_stateful, mock_sensory, observation
    ):
        """Deve retornar PASS quando StatefulInspector decide PASS."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.PASS,
            reason="Known good flow",
            connection_state=ConnectionState(),
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            result = await layer.process_packet(observation, b"payload")

            assert result.action == InspectorAction.PASS
            assert result.confidence == 0.5

    @pytest.mark.asyncio
    async def test_process_packet_registers_pass_event(
        self, settings, mock_stateful, mock_sensory, observation
    ):
        """Deve registrar evento PASS no SensoryProcessor."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.PASS,
            reason="Whitelisted",
            connection_state=ConnectionState(),
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch("backend.modules.tegumentar.derme.manager.DeepPacketInspector"), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            await layer.process_packet(observation, b"payload")

            mock_sensory.register_event.assert_called_once()
            call_args = mock_sensory.register_event.call_args[0]
            assert call_args[1].action == InspectorAction.PASS


class TestProcessPacketDeepInspection:
    """Testa process_packet quando precisa de deep inspection."""

    @pytest.mark.asyncio
    async def test_process_packet_calls_dpi_when_stateful_is_uncertain(
        self, settings, mock_stateful, mock_dpi, mock_sensory, observation
    ):
        """Deve chamar DPI quando StatefulInspector não tem certeza."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.INSPECT_DEEP,
            reason="Uncertain",
            connection_state=ConnectionState(),
        )
        mock_dpi.inspect.return_value = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.7,
            anomaly_score=0.3,
            reason="Looks OK",
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector",
            return_value=mock_dpi,
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            result = await layer.process_packet(observation, b"test payload")

            mock_dpi.inspect.assert_called_once_with(observation, b"test payload")
            assert result.action == InspectorAction.PASS

    @pytest.mark.asyncio
    async def test_deep_inspection_registers_sensory_event(
        self, settings, mock_stateful, mock_dpi, mock_sensory, observation
    ):
        """Deep inspection deve registrar evento no SensoryProcessor."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.INSPECT_DEEP,
            reason="Check payload",
            connection_state=ConnectionState(),
        )
        mock_dpi.inspect.return_value = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.6,
            reason="Low anomaly detected",
            anomaly_score=0.2,
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector",
            return_value=mock_dpi,
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell"
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            await layer.process_packet(observation, b"payload")

            mock_sensory.register_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_deep_inspection_captures_antigen_when_anomaly_high(
        self, settings, mock_stateful, mock_dpi, mock_langerhans, observation
    ):
        """Deve capturar antígeno quando anomaly_score > 0.8."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.INSPECT_DEEP,
            reason="Uncertain",
            connection_state=ConnectionState(),
        )
        mock_result = InspectionResult(
            action=InspectorAction.DROP,
            confidence=0.95,
            anomaly_score=0.92,  # > 0.8
            reason="Suspicious payload",
        )
        mock_dpi.inspect.return_value = mock_result

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector",
            return_value=mock_dpi,
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.process_packet(observation, b"malicious payload")

            mock_langerhans.capture_antigen.assert_called_once_with(
                observation, mock_result, b"malicious payload"
            )

    @pytest.mark.asyncio
    async def test_deep_inspection_does_not_capture_when_anomaly_low(
        self, settings, mock_stateful, mock_dpi, mock_langerhans, observation
    ):
        """Não deve capturar antígeno quando anomaly_score <= 0.8."""
        mock_stateful.process.return_value = InspectorDecision(
            action=InspectorAction.INSPECT_DEEP,
            reason="Uncertain",
            connection_state=ConnectionState(),
        )
        mock_dpi.inspect.return_value = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.7,
            reason="Normal traffic",
            anomaly_score=0.5,  # <= 0.8
        )

        with patch(
            "backend.modules.tegumentar.derme.manager.StatefulInspector",
            return_value=mock_stateful,
        ), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector",
            return_value=mock_dpi,
        ), patch(
            "backend.modules.tegumentar.derme.manager.LangerhansCell",
            return_value=mock_langerhans,
        ), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor"
        ):
            layer = DermeLayer(settings)
            await layer.process_packet(observation, b"normal payload")

            mock_langerhans.capture_antigen.assert_not_called()


class TestSnapshot:
    """Testa método snapshot()."""

    def test_snapshot_returns_sensory_data(self, settings, mock_sensory):
        """snapshot() deve retornar dados do SensoryProcessor."""
        mock_snap = MagicMock()
        mock_snap.timestamp = "2025-10-28T12:00:00Z"
        mock_snap.pressure = 0.7
        mock_snap.temperature = 0.5
        mock_snap.pain = 0.2
        mock_snap.description = "Normal operation"
        mock_sensory.render_snapshot.return_value = mock_snap

        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch("backend.modules.tegumentar.derme.manager.LangerhansCell"), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            snapshot = layer.snapshot()

            assert snapshot["timestamp"] == "2025-10-28T12:00:00Z"
            assert snapshot["pressure"] == 0.7
            assert snapshot["temperature"] == 0.5
            assert snapshot["pain"] == 0.2
            assert snapshot["description"] == "Normal operation"

    def test_snapshot_calls_render_snapshot(self, settings, mock_sensory):
        """snapshot() deve chamar render_snapshot() do SensoryProcessor."""
        mock_sensory.render_snapshot.return_value = MagicMock(
            timestamp="", pressure=0, temperature=0, pain=0, description=""
        )

        with patch("backend.modules.tegumentar.derme.manager.StatefulInspector"), patch(
            "backend.modules.tegumentar.derme.manager.DeepPacketInspector"
        ), patch("backend.modules.tegumentar.derme.manager.LangerhansCell"), patch(
            "backend.modules.tegumentar.derme.manager.SensoryProcessor",
            return_value=mock_sensory,
        ):
            layer = DermeLayer(settings)
            layer.snapshot()

            mock_sensory.render_snapshot.assert_called_once()
