"""
Testes unitários para backend.modules.tegumentar.derme.langerhans_cell

Testa as Células de Langerhans digitais:
- Captura de antígenos
- Armazenamento em PostgreSQL
- Publicação em Kafka
- Integração com Linfonodo
- Broadcast de vacinações
- Cálculo de severidade

EM NOME DE JESUS - MANIFESTAÇÃO FENOMENOLÓGICA MÁXIMA!
"""
import asyncio
import base64
from dataclasses import dataclass
import secrets
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.langerhans_cell import (
    AntigenRecord,
    LangerhansCell,
)


@dataclass
class MockFlowObservation:
    src_ip: str = "192.168.1.100"
    dst_ip: str = "10.0.0.1"
    protocol: str = "TCP"
    timestamp: float = 1698765432.0


@dataclass
class MockInspectionResult:
    anomaly_score: float = 0.95
    matched_signatures: list = None


@pytest.fixture
def settings():
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
        kafka_bootstrap_servers="localhost:9092",
        langerhans_topic="test.langerhans",
        lymphnode_endpoint="http://localhost:8021",
    )


@pytest.fixture
def langerhans_cell(settings):
    return LangerhansCell(settings)


@pytest.fixture
def mock_pool():
    """Mock PostgreSQL pool."""
    pool = MagicMock()
    conn = MagicMock()
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    pool.acquire = MagicMock(return_value=conn)
    pool.close = AsyncMock()
    return pool


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer."""
    producer = MagicMock()
    producer.start = AsyncMock()
    producer.stop = AsyncMock()
    producer.send_and_wait = AsyncMock()
    return producer


@pytest.fixture
def mock_lymphnode_api():
    """Mock Lymphnode API client."""
    api = MagicMock()

    # Mock validation response
    validation = MagicMock()
    validation.confirmed = True
    validation.threat_id = "threat-123"
    validation.confidence = 0.98
    validation.severity = "high"

    api.submit_threat = AsyncMock(return_value=validation)
    api.broadcast_vaccination = AsyncMock()

    return api


class TestLangerhansCellInitialization:
    """Testa inicialização."""

    def test_initialization_with_settings(self, settings):
        cell = LangerhansCell(settings)
        assert cell._settings is settings
        assert cell._pool is None
        assert cell._producer is None

    def test_initialization_without_settings(self):
        """Deve usar get_settings() se não fornecer settings."""
        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.get_settings"
        ) as mock_get:
            mock_settings = MagicMock()
            mock_get.return_value = mock_settings

            cell = LangerhansCell()
            assert cell._settings is mock_settings

    def test_has_feature_extractor(self, langerhans_cell):
        assert langerhans_cell._feature_extractor is not None

    def test_has_lymphnode_api(self, langerhans_cell):
        assert langerhans_cell._lymphnode_api is not None

    def test_has_asyncio_lock(self, langerhans_cell):
        assert langerhans_cell._lock is not None
        assert isinstance(langerhans_cell._lock, asyncio.Lock)


class TestStartupShutdown:
    """Testa lifecycle."""

    @pytest.mark.asyncio
    async def test_startup_creates_pool(self, langerhans_cell, mock_pool):
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
            with patch.object(langerhans_cell, "_initialise_schema", AsyncMock()):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.AIOKafkaProducer"
                ) as mock_producer_class:
                    mock_producer = MagicMock()
                    mock_producer.start = AsyncMock()
                    mock_producer_class.return_value = mock_producer

                    await langerhans_cell.startup()

                    assert langerhans_cell._pool is mock_pool

    @pytest.mark.asyncio
    async def test_startup_initializes_schema(self, langerhans_cell, mock_pool):
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
            with patch.object(
                langerhans_cell, "_initialise_schema", AsyncMock()
            ) as mock_init:
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.AIOKafkaProducer"
                ) as mock_producer_class:
                    mock_producer = MagicMock()
                    mock_producer.start = AsyncMock()
                    mock_producer_class.return_value = mock_producer

                    await langerhans_cell.startup()

                    mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_creates_kafka_producer(self, langerhans_cell, mock_pool):
        with patch("asyncpg.create_pool", AsyncMock(return_value=mock_pool)):
            with patch.object(langerhans_cell, "_initialise_schema", AsyncMock()):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.AIOKafkaProducer"
                ) as mock_producer_class:
                    mock_producer = MagicMock()
                    mock_producer.start = AsyncMock()
                    mock_producer_class.return_value = mock_producer

                    await langerhans_cell.startup()

                    assert langerhans_cell._producer is mock_producer
                    mock_producer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_is_idempotent(self, langerhans_cell, mock_pool):
        """Múltiplas chamadas a startup() não devem reconectar."""
        with patch(
            "asyncpg.create_pool", AsyncMock(return_value=mock_pool)
        ) as mock_create_pool:
            with patch.object(langerhans_cell, "_initialise_schema", AsyncMock()):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.AIOKafkaProducer"
                ) as mock_producer_class:
                    mock_producer = MagicMock()
                    mock_producer.start = AsyncMock()
                    mock_producer_class.return_value = mock_producer

                    await langerhans_cell.startup()
                    await langerhans_cell.startup()
                    await langerhans_cell.startup()

                    # create_pool só deve ser chamado uma vez
                    mock_create_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_closes_producer(self, langerhans_cell, mock_kafka_producer):
        langerhans_cell._producer = mock_kafka_producer

        await langerhans_cell.shutdown()

        mock_kafka_producer.stop.assert_called_once()
        assert langerhans_cell._producer is None

    @pytest.mark.asyncio
    async def test_shutdown_closes_pool(self, langerhans_cell, mock_pool):
        langerhans_cell._pool = mock_pool

        await langerhans_cell.shutdown()

        mock_pool.close.assert_called_once()
        assert langerhans_cell._pool is None

    @pytest.mark.asyncio
    async def test_shutdown_is_safe_when_not_initialized(self, langerhans_cell):
        await langerhans_cell.shutdown()  # Não deve lançar exceção


class TestCaptureAntigen:
    """Testa captura de antígenos."""

    @pytest.mark.asyncio
    async def test_requires_anomaly_score(self, langerhans_cell):
        observation = MockFlowObservation()
        inspection = MockInspectionResult(anomaly_score=None)
        payload = b"test payload"

        with pytest.raises(ValueError) as exc_info:
            await langerhans_cell.capture_antigen(observation, inspection, payload)

        assert "anomaly score" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_generates_unique_antigen_id(
        self, langerhans_cell, mock_pool, mock_kafka_producer, mock_lymphnode_api
    ):
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api = mock_lymphnode_api

        observation = MockFlowObservation()
        inspection = MockInspectionResult(anomaly_score=0.95)
        payload = b"test"

        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ):
                    record = await langerhans_cell.capture_antigen(
                        observation, inspection, payload
                    )

        assert record.antigen_id is not None
        assert len(record.antigen_id) == 16  # secrets.token_hex(8) = 16 chars

    @pytest.mark.asyncio
    async def test_creates_antigen_record_with_correct_data(
        self, langerhans_cell, mock_pool, mock_kafka_producer, mock_lymphnode_api
    ):
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api = mock_lymphnode_api

        observation = MockFlowObservation(
            src_ip="192.168.1.100", dst_ip="10.0.0.1", protocol="TCP"
        )
        inspection = MockInspectionResult(anomaly_score=0.87)
        payload = b"suspicious payload"

        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ):
                    record = await langerhans_cell.capture_antigen(
                        observation, inspection, payload
                    )

        assert record.src_ip == "192.168.1.100"
        assert record.dst_ip == "10.0.0.1"
        assert record.protocol == "TCP"
        assert record.anomaly_score == 0.87

    @pytest.mark.asyncio
    async def test_encodes_payload_preview_base64(
        self, langerhans_cell, mock_pool, mock_kafka_producer, mock_lymphnode_api
    ):
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api = mock_lymphnode_api

        observation = MockFlowObservation()
        inspection = MockInspectionResult(anomaly_score=0.95)
        payload = b"test payload data"

        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ):
                    record = await langerhans_cell.capture_antigen(
                        observation, inspection, payload
                    )

        # Verificar que é base64 válido
        decoded = base64.b64decode(record.payload_preview)
        assert decoded == payload[:512]

    @pytest.mark.asyncio
    async def test_limits_payload_preview_to_512_bytes(
        self, langerhans_cell, mock_pool, mock_kafka_producer, mock_lymphnode_api
    ):
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api = mock_lymphnode_api

        observation = MockFlowObservation()
        inspection = MockInspectionResult(anomaly_score=0.95)
        large_payload = b"X" * 10000  # 10KB

        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ):
                    record = await langerhans_cell.capture_antigen(
                        observation, inspection, large_payload
                    )

        decoded = base64.b64decode(record.payload_preview)
        assert len(decoded) == 512


class TestStore:
    """Testa armazenamento em PostgreSQL."""

    @pytest.mark.asyncio
    async def test_store_inserts_into_database(self, langerhans_cell, mock_pool):
        langerhans_cell._pool = mock_pool

        record = AntigenRecord(
            antigen_id="test123",
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol="TCP",
            anomaly_score=0.95,
            payload_preview="dGVzdA==",
        )

        await langerhans_cell._store(record)

        # Verificar que execute foi chamado com INSERT
        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute.assert_called_once()

        call_args = conn.execute.call_args[0]
        assert "INSERT INTO tegumentar_antigens" in call_args[0]
        assert call_args[1] == "test123"
        assert call_args[2] == "192.168.1.1"

    @pytest.mark.asyncio
    async def test_store_raises_if_not_initialized(self, langerhans_cell):
        record = AntigenRecord(
            antigen_id="test",
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            protocol="TCP",
            anomaly_score=0.9,
            payload_preview="test",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await langerhans_cell._store(record)

        assert "not initialised" in str(exc_info.value).lower()


class TestPublish:
    """Testa publicação em Kafka."""

    @pytest.mark.asyncio
    async def test_publish_sends_to_kafka(
        self, langerhans_cell, mock_kafka_producer, settings
    ):
        langerhans_cell._producer = mock_kafka_producer

        record = AntigenRecord(
            antigen_id="test456",
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol="UDP",
            anomaly_score=0.88,
            payload_preview="payload==",
        )

        await langerhans_cell._publish(record)

        mock_kafka_producer.send_and_wait.assert_called_once()
        call_args = mock_kafka_producer.send_and_wait.call_args[0]

        assert call_args[0] == settings.langerhans_topic
        assert call_args[1]["antigen_id"] == "test456"
        assert call_args[1]["src_ip"] == "192.168.1.1"
        assert call_args[1]["anomaly_score"] == 0.88

    @pytest.mark.asyncio
    async def test_publish_uses_lock(self, langerhans_cell, mock_kafka_producer):
        langerhans_cell._producer = mock_kafka_producer

        record = AntigenRecord(
            antigen_id="test",
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            protocol="TCP",
            anomaly_score=0.9,
            payload_preview="test",
        )

        # Verificar que lock existe
        assert langerhans_cell._lock is not None

        await langerhans_cell._publish(record)

        # Deve ter chamado Kafka
        mock_kafka_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_raises_if_producer_not_initialized(self, langerhans_cell):
        record = AntigenRecord(
            antigen_id="test",
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            protocol="TCP",
            anomaly_score=0.9,
            payload_preview="test",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await langerhans_cell._publish(record)

        assert "producer not initialised" in str(exc_info.value).lower()


class TestSeverityCalculation:
    """Testa cálculo de severidade."""

    def test_severity_critical_for_high_scores(self):
        assert LangerhansCell._severity_from_score(0.98) == "critical"
        assert LangerhansCell._severity_from_score(0.99) == "critical"
        assert LangerhansCell._severity_from_score(1.0) == "critical"

    def test_severity_high_for_medium_high_scores(self):
        assert LangerhansCell._severity_from_score(0.90) == "high"
        assert LangerhansCell._severity_from_score(0.95) == "high"
        assert LangerhansCell._severity_from_score(0.97) == "high"

    def test_severity_medium_for_moderate_scores(self):
        assert LangerhansCell._severity_from_score(0.75) == "medium"
        assert LangerhansCell._severity_from_score(0.80) == "medium"
        assert LangerhansCell._severity_from_score(0.89) == "medium"

    def test_severity_low_for_low_scores(self):
        assert LangerhansCell._severity_from_score(0.0) == "low"
        assert LangerhansCell._severity_from_score(0.5) == "low"
        assert LangerhansCell._severity_from_score(0.74) == "low"

    def test_severity_boundary_conditions(self):
        """Testa condições de fronteira."""
        assert LangerhansCell._severity_from_score(0.9799) == "high"
        assert LangerhansCell._severity_from_score(0.9800) == "critical"

        assert LangerhansCell._severity_from_score(0.8999) == "medium"
        assert LangerhansCell._severity_from_score(0.9000) == "high"

        assert LangerhansCell._severity_from_score(0.7499) == "low"
        assert LangerhansCell._severity_from_score(0.7500) == "medium"


class TestSchemaInitialization:
    """Testa criação de schema PostgreSQL."""

    @pytest.mark.asyncio
    async def test_creates_antigens_table(self, langerhans_cell, mock_pool):
        langerhans_cell._pool = mock_pool

        await langerhans_cell._initialise_schema()

        conn = mock_pool.acquire.return_value.__aenter__.return_value
        conn.execute.assert_called_once()

        sql = conn.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS tegumentar_antigens" in sql
        assert "antigen_id text PRIMARY KEY" in sql
        assert "src_ip inet" in sql
        assert "anomaly_score double precision" in sql

    @pytest.mark.asyncio
    async def test_schema_init_is_idempotent(self, langerhans_cell, mock_pool):
        """Deve usar CREATE IF NOT EXISTS."""
        langerhans_cell._pool = mock_pool

        await langerhans_cell._initialise_schema()

        sql = mock_pool.acquire.return_value.__aenter__.return_value.execute.call_args[
            0
        ][0]
        assert "IF NOT EXISTS" in sql


class TestMetrics:
    """Testa integração com métricas."""

    @pytest.mark.asyncio
    async def test_records_antigen_capture_metric(
        self, langerhans_cell, mock_pool, mock_kafka_producer, mock_lymphnode_api
    ):
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api = mock_lymphnode_api

        observation = MockFlowObservation(protocol="HTTP")
        inspection = MockInspectionResult(anomaly_score=0.9)

        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ) as mock_metric:
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ):
                    await langerhans_cell.capture_antigen(
                        observation, inspection, b"test"
                    )

        mock_metric.assert_called_once_with("HTTP")


class TestAntigenRecord:
    """Testa dataclass AntigenRecord."""

    def test_antigen_record_has_required_fields(self):
        record = AntigenRecord(
            antigen_id="test123",
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            protocol="TCP",
            anomaly_score=0.95,
            payload_preview="base64data",
        )

        assert record.antigen_id == "test123"
        assert record.src_ip == "1.1.1.1"
        assert record.dst_ip == "2.2.2.2"
        assert record.protocol == "TCP"
        assert record.anomaly_score == 0.95
        assert record.payload_preview == "base64data"

    def test_antigen_record_uses_slots(self):
        """Deve usar slots para eficiência de memória."""
        record = AntigenRecord(
            antigen_id="test",
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            protocol="TCP",
            anomaly_score=0.9,
            payload_preview="data",
        )

        # Slots não têm __dict__
        assert not hasattr(record, "__dict__")


class TestLangerhansErrorHandling:
    """Testa tratamento de erros HTTP e casos edge."""

    @pytest.mark.asyncio
    async def test_lymphnode_report_handles_http_error(
        self, langerhans_cell, mock_pool, mock_kafka_producer
    ):
        """Deve capturar e logar HTTPError ao enviar report ao Linfonodo."""
        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api.report_threat = AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )

        observation = MockFlowObservation()
        inspection = MockInspectionResult()

        # Não deve propagar exceção (HTTPError capturado linha 121-126)
        await langerhans_cell.capture_antigen(observation, inspection, b"payload")

    @pytest.mark.asyncio
    async def test_broadcast_vaccination_handles_http_error(
        self, langerhans_cell, mock_pool, mock_kafka_producer
    ):
        """Deve capturar e logar HTTPError ao fazer broadcast de vacinação."""
        from backend.modules.tegumentar.lymphnode.api import ThreatValidation

        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api.submit_threat = AsyncMock(
            return_value=ThreatValidation(
                confirmed=True,
                threat_id="threat-123",
                severity="critical",
                confidence=0.95,
            )
        )
        langerhans_cell._lymphnode_api.broadcast_vaccination = AsyncMock(
            side_effect=httpx.HTTPError("Broadcast failed")
        )

        observation = MockFlowObservation()
        inspection = MockInspectionResult()

        # Não deve propagar exceção (HTTPError capturado linha 145-148)
        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                with patch(
                    "backend.modules.tegumentar.derme.langerhans_cell.record_vaccination"
                ) as mock_record_vaccination:
                    await langerhans_cell.capture_antigen(
                        observation, inspection, b"payload"
                    )

                    # Deve ter chamado record_vaccination("failure") devido ao HTTPError
                    mock_record_vaccination.assert_called_with("failure")

    @pytest.mark.asyncio
    async def test_capture_antigen_when_lymphnode_rejects_threat(
        self, langerhans_cell, mock_pool, mock_kafka_producer
    ):
        """Deve logar warning quando Linfonodo não confirma ameaça."""
        from backend.modules.tegumentar.lymphnode.api import ThreatValidation

        langerhans_cell._pool = mock_pool
        langerhans_cell._producer = mock_kafka_producer
        langerhans_cell._lymphnode_api.submit_threat = AsyncMock(
            return_value=ThreatValidation(confirmed=False)  # Rejeitado
        )

        observation = MockFlowObservation()
        inspection = MockInspectionResult()

        # Sem exceção, warning logado (linha 150)
        with patch(
            "backend.modules.tegumentar.derme.langerhans_cell.record_antigen_capture"
        ):
            with patch(
                "backend.modules.tegumentar.derme.langerhans_cell.record_lymphnode_validation"
            ):
                await langerhans_cell.capture_antigen(
                    observation, inspection, b"payload"
                )

    @pytest.mark.asyncio
    async def test_initialise_schema_returns_early_when_no_pool(self):
        """_initialise_schema deve retornar imediatamente se pool é None."""
        cell = LangerhansCell(
            TegumentarSettings(
                postgres_dsn="postgresql://test@localhost/test",
                kafka_bootstrap_servers="localhost:9092",
            )
        )
        # Pool ainda não foi criado (startup não chamado)
        assert cell._pool is None

        # Não deve falhar
        await cell._initialise_schema()  # Early return na linha 201
