"""
Testes unitários para backend.modules.tegumentar.orchestrator

Testa o orquestrador principal que coordena as 3 camadas:
- Epiderme (stateless)
- Derme (stateful) - DISABLED por falta de PostgreSQL
- Hipoderme (adaptive)

Padrão Pagani: Mocks dos layers, validação de integração.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.modules.tegumentar.orchestrator import TegumentarModule
from backend.modules.tegumentar.config import TegumentarSettings


@pytest.fixture
def settings():
    """Settings de teste para orchestrator."""
    return TegumentarSettings(
        redis_url="redis://localhost:6379/15",
        postgres_dsn="postgresql://test:test@localhost:5432/test"
    )


@pytest.fixture
def mock_epiderme():
    """Mock da camada Epiderme."""
    mock = MagicMock()
    mock.startup = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.stateless_filter = MagicMock()
    return mock


@pytest.fixture
def mock_derme():
    """Mock da camada Derme."""
    mock = MagicMock()
    mock.startup = AsyncMock()
    mock.shutdown = AsyncMock()
    mock.process_packet = AsyncMock()
    return mock


@pytest.fixture
def mock_permeability():
    """Mock do PermeabilityController."""
    mock = MagicMock()
    mock.shutdown = AsyncMock()
    return mock


@pytest.fixture
def mock_wound_healing():
    """Mock do WoundHealingOrchestrator."""
    mock = MagicMock()
    mock.shutdown = AsyncMock()
    return mock


class TestTegumentarModuleInitialization:
    """Testa inicialização do módulo."""

    def test_tegumentar_module_initializes_with_settings(self, settings):
        """Deve inicializar com settings fornecido."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)
            assert module._settings is settings

    def test_tegumentar_module_initializes_with_default_settings(self):
        """Deve usar get_settings() quando settings não fornecido."""
        with patch("backend.modules.tegumentar.orchestrator.get_settings") as mock_get_settings, \
             patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            module = TegumentarModule()

            mock_get_settings.assert_called_once()
            assert module._settings is mock_settings

    def test_creates_epiderme_layer(self, settings, mock_epiderme):
        """Deve criar instância de EpidermeLayer."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme) as mock_class, \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)

            mock_class.assert_called_once_with(settings)
            assert module.epiderme is mock_epiderme

    def test_creates_derme_layer(self, settings, mock_derme):
        """Deve criar instância de DermeLayer."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer", return_value=mock_derme) as mock_class, \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)

            mock_class.assert_called_once_with(settings)
            assert module.derme is mock_derme

    def test_creates_permeability_controller(self, settings, mock_epiderme, mock_permeability):
        """Deve criar PermeabilityController com stateless_filter."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController", return_value=mock_permeability) as mock_class, \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)

            mock_class.assert_called_once_with(mock_epiderme.stateless_filter, settings)
            assert module.permeability is mock_permeability

    def test_creates_wound_healing_orchestrator(self, settings, mock_wound_healing):
        """Deve criar WoundHealingOrchestrator."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator", return_value=mock_wound_healing) as mock_class:
            module = TegumentarModule(settings)

            mock_class.assert_called_once_with(settings)
            assert module.wound_healing is mock_wound_healing

    def test_throttler_starts_as_none(self, settings):
        """Throttler deve começar como None."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)
            assert module._throttler is None


class TestStartupShutdown:
    """Testa lifecycle do módulo."""

    @pytest.mark.asyncio
    async def test_startup_calls_epiderme_startup(self, settings, mock_epiderme):
        """startup() deve inicializar Epiderme com interface."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"), \
             patch("backend.modules.tegumentar.orchestrator.AdaptiveThrottler"):
            module = TegumentarModule(settings)
            await module.startup("eth0")

            mock_epiderme.startup.assert_called_once_with("eth0")

    @pytest.mark.asyncio
    async def test_startup_does_not_call_derme_startup(self, settings, mock_derme):
        """startup() NÃO deve inicializar Derme (disabled)."""
        mock_epiderme = MagicMock()
        mock_epiderme.startup = AsyncMock()

        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer", return_value=mock_derme), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"), \
             patch("backend.modules.tegumentar.orchestrator.AdaptiveThrottler"):
            module = TegumentarModule(settings)
            await module.startup("eth0")

            # Derme disabled
            mock_derme.startup.assert_not_called()

    @pytest.mark.asyncio
    async def test_startup_creates_adaptive_throttler(self, settings):
        """startup() deve criar AdaptiveThrottler."""
        mock_throttler = MagicMock()
        mock_epiderme = MagicMock()
        mock_epiderme.startup = AsyncMock()

        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"), \
             patch("backend.modules.tegumentar.orchestrator.AdaptiveThrottler", return_value=mock_throttler) as mock_class:
            module = TegumentarModule(settings)
            await module.startup("wlan0")

            mock_class.assert_called_once_with("wlan0")
            assert module._throttler is mock_throttler

    @pytest.mark.asyncio
    async def test_shutdown_calls_controller_shutdown(self, settings):
        """shutdown() deve chamar controller_shutdown()."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)
            module.controller_shutdown = AsyncMock()

            await module.shutdown()

            module.controller_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_controller_shutdown_stops_all_layers(self, settings, mock_epiderme, mock_permeability, mock_wound_healing):
        """controller_shutdown() deve parar todas as camadas."""
        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController", return_value=mock_permeability), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator", return_value=mock_wound_healing):
            module = TegumentarModule(settings)
            await module.controller_shutdown()

            mock_permeability.shutdown.assert_called_once()
            mock_wound_healing.shutdown.assert_called_once()
            mock_epiderme.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_controller_shutdown_does_not_stop_derme(self, settings, mock_derme):
        """controller_shutdown() NÃO deve parar Derme (disabled)."""
        mock_epiderme = MagicMock()
        mock_epiderme.shutdown = AsyncMock()
        mock_permeability = MagicMock()
        mock_permeability.shutdown = AsyncMock()
        mock_wound_healing = MagicMock()
        mock_wound_healing.shutdown = AsyncMock()

        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer", return_value=mock_derme), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController", return_value=mock_permeability), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator", return_value=mock_wound_healing):
            module = TegumentarModule(settings)
            await module.controller_shutdown()

            # Derme disabled
            mock_derme.shutdown.assert_not_called()


class TestProcessPacket:
    """Testa processamento de pacotes."""

    @pytest.mark.asyncio
    async def test_process_packet_delegates_to_derme(self, settings, mock_derme):
        """process_packet() deve delegar para Derme layer."""
        mock_observation = MagicMock()
        mock_payload = b"test payload"
        mock_result = MagicMock()
        mock_derme.process_packet.return_value = mock_result

        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer"), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer", return_value=mock_derme), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController"), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator"):
            module = TegumentarModule(settings)
            result = await module.process_packet(mock_observation, mock_payload)

            mock_derme.process_packet.assert_called_once_with(mock_observation, mock_payload)
            assert result is mock_result


class TestFastAPIApp:
    """Testa criação de app FastAPI."""

    def test_fastapi_app_creates_app(self, settings, mock_epiderme, mock_derme, mock_permeability, mock_wound_healing):
        """fastapi_app() deve criar app FastAPI."""
        mock_app = MagicMock()

        with patch("backend.modules.tegumentar.orchestrator.EpidermeLayer", return_value=mock_epiderme), \
             patch("backend.modules.tegumentar.orchestrator.DermeLayer", return_value=mock_derme), \
             patch("backend.modules.tegumentar.orchestrator.PermeabilityController", return_value=mock_permeability), \
             patch("backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator", return_value=mock_wound_healing), \
             patch("backend.modules.tegumentar.orchestrator.create_app", return_value=mock_app) as mock_create:
            module = TegumentarModule(settings)
            app = module.fastapi_app()

            mock_create.assert_called_once_with(
                mock_epiderme,
                mock_derme,
                mock_permeability,
                mock_wound_healing,
                settings
            )
            assert app is mock_app
