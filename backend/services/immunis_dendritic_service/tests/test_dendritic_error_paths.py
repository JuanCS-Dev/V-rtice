"""
Testes de ERROR PATHS para Dendritic Service - 100% Coverage Final

OBJETIVO: Cobrir linhas de error handling e edge cases
FOCO: Kafka errors, Qdrant errors, exception paths

Linhas alvo (75% → 100%):
- 39, 47-49: Kafka consumer init exceptions
- 69-81, 93-117, 124: Kafka consumption loop
- 142-148, 152-169, 222, 239-269: Qdrant init/store exceptions
- 550, 613-617: Start/stop consumption

Padrão Pagani Absoluto: 100% = 100%
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_dendritic_service")

from dendritic_core import (
    AntigenConsumer,
    EventCorrelationEngine,
    DendriticCore,
)


# =====================================================================
# TEST KAFKA ERRORS
# =====================================================================


class TestKafkaErrors:
    """Testa error paths no Kafka consumer."""

    def test_antigen_consumer_kafka_init_exception(self):
        """Testa Kafka consumer init com exception (line 79-81)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", True):
            # Mock KafkaConsumer no sys.modules antes de importar
            mock_kafka = MagicMock()
            mock_kafka.KafkaConsumer.side_effect = Exception("Kafka down")

            with patch.dict("sys.modules", {"kafka": mock_kafka}):
                consumer = AntigenConsumer()
                assert consumer.consumer is None  # Graceful degradation

    def test_antigen_consumer_init_kafka_not_available(self):
        """Testa init quando Kafka não instalado (line 39)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", False):
            consumer = AntigenConsumer()
            assert consumer.consumer is None

    @pytest.mark.asyncio
    async def test_consume_antigens_no_consumer(self):
        """Testa consume_antigens quando consumer is None (line 89-91)."""
        consumer = AntigenConsumer()
        consumer.consumer = None

        callback_called = False

        async def test_callback(antigen):
            nonlocal callback_called
            callback_called = True

        await consumer.consume_antigens(test_callback)

        # Should return early, not call callback
        assert callback_called is False

    @pytest.mark.asyncio
    async def test_consume_antigens_poll_loop(self):
        """Testa consumption loop com messages (lines 97-112)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", True):
            consumer = AntigenConsumer()

            # Mock Kafka consumer
            mock_consumer = MagicMock()
            mock_record = MagicMock()
            mock_record.value = {"antigen_id": "test_001"}

            # Mock poll to return messages once, then empty
            call_count = [0]

            def mock_poll(timeout_ms):
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call: return message
                    return {MagicMock(): [mock_record]}
                else:
                    # Stop after first message
                    consumer.running = False
                    return {}

            mock_consumer.poll = mock_poll
            consumer.consumer = mock_consumer

            callback_results = []

            async def capture_callback(antigen):
                callback_results.append(antigen)

            # Start consumption (will stop after first message)
            await consumer.consume_antigens(capture_callback)

            assert len(callback_results) == 1
            assert callback_results[0]["antigen_id"] == "test_001"

    @pytest.mark.asyncio
    async def test_consume_antigens_callback_exception(self):
        """Testa callback exception handling (line 108-109)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", True):
            consumer = AntigenConsumer()

            mock_consumer = MagicMock()
            mock_record = MagicMock()
            mock_record.value = {"antigen_id": "test_fail"}

            call_count = [0]

            def mock_poll(timeout_ms):
                call_count[0] += 1
                if call_count[0] == 1:
                    return {MagicMock(): [mock_record]}
                else:
                    consumer.running = False
                    return {}

            mock_consumer.poll = mock_poll
            consumer.consumer = mock_consumer

            async def failing_callback(antigen):
                raise Exception("Callback error")

            # Should not crash, logs error
            await consumer.consume_antigens(failing_callback)

            # Verify loop continued
            assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_consume_antigens_general_exception(self):
        """Testa general exception no consumption loop (line 114-115)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", True):
            consumer = AntigenConsumer()

            mock_consumer = MagicMock()
            mock_consumer.poll.side_effect = Exception("Poll error")
            consumer.consumer = mock_consumer

            async def dummy_callback(antigen):
                pass

            # Should handle exception gracefully
            await consumer.consume_antigens(dummy_callback)

            assert consumer.running is False  # Stopped after exception

    def test_antigen_consumer_stop_with_consumer(self):
        """Testa stop com consumer ativo (line 124)."""
        with patch("dendritic_core.KAFKA_AVAILABLE", True):
            consumer = AntigenConsumer()

            mock_consumer = MagicMock()
            consumer.consumer = mock_consumer
            consumer.running = True

            consumer.stop()

            assert consumer.running is False
            mock_consumer.close.assert_called_once()

    def test_antigen_consumer_stop_no_consumer(self):
        """Testa stop sem consumer (graceful)."""
        consumer = AntigenConsumer()
        consumer.consumer = None
        consumer.running = True

        consumer.stop()

        assert consumer.running is False


# =====================================================================
# TEST QDRANT ERRORS
# =====================================================================


class TestQdrantErrors:
    """Testa error paths no Qdrant correlation engine."""

    def test_event_correlation_engine_qdrant_not_available(self):
        """Testa init quando Qdrant não instalado."""
        with patch("dendritic_core.QDRANT_AVAILABLE", False):
            engine = EventCorrelationEngine()
            assert engine.qdrant_client is None

    def test_event_correlation_engine_init_exception(self):
        """Testa Qdrant init exception (line 146-148)."""
        with patch("dendritic_core.QDRANT_AVAILABLE", True):
            # Mock Qdrant no sys.modules
            mock_qdrant = MagicMock()
            mock_qdrant.QdrantClient.side_effect = Exception("Qdrant down")

            with patch.dict("sys.modules", {"qdrant_client": mock_qdrant, "qdrant_client.models": MagicMock()}):
                engine = EventCorrelationEngine()
                assert engine.qdrant_client is None

    def test_initialize_collection_no_client(self):
        """Testa _initialize_collection sem client (line 152-153)."""
        engine = EventCorrelationEngine()
        engine.qdrant_client = None

        # Should return early without error
        engine._initialize_collection()

    def test_initialize_collection_exception_lines_166_169(self):
        """Testa exception no _initialize_collection (lines 168-169)."""
        engine = EventCorrelationEngine()

        # Mock client que causa exception no get_collections
        mock_client = MagicMock()
        mock_client.get_collections.side_effect = RuntimeError("Qdrant connection error")
        engine.qdrant_client = mock_client

        # Should not crash
        engine._initialize_collection()

        # Verifica que tentou get_collections
        mock_client.get_collections.assert_called_once()

    def test_initialize_collection_already_exists(self):
        """Testa _initialize_collection quando já existe."""
        engine = EventCorrelationEngine()

        mock_client = MagicMock()

        # Mock collection exists
        mock_collection = MagicMock()
        mock_collection.name = "threat_events"
        mock_collections_response = MagicMock()
        mock_collections_response.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections_response

        engine.qdrant_client = mock_client

        engine._initialize_collection()

        # Should NOT create collection
        mock_client.create_collection.assert_not_called()

    def test_initialize_collection_exception(self):
        """Testa _initialize_collection exception handling (line 168-169)."""
        engine = EventCorrelationEngine()

        mock_client = MagicMock()
        mock_client.get_collections.side_effect = Exception("Network error")
        engine.qdrant_client = mock_client

        # Should not crash
        engine._initialize_collection()

    def test_vectorize_threat_truncates_to_128(self):
        """Testa que vector é truncado se > 128 (line 222)."""
        engine = EventCorrelationEngine()

        # Create threat que gera vector gigante
        threat = {
            "severity": 1.0,
            "timestamp": datetime.now().isoformat(),
            "iocs": {
                "ips": ["1.2.3.4"] * 200,  # Muitos IOCs
                "domains": ["evil.com"] * 200,
            },
        }

        vector = engine._vectorize_threat(threat)

        # Deve ser exatamente 128
        assert len(vector) == 128

    @pytest.mark.asyncio
    async def test_store_event_exception(self):
        """Testa store_event exception handling (line 267-269)."""
        engine = EventCorrelationEngine()

        mock_client = MagicMock()
        mock_client.upsert.side_effect = Exception("Qdrant error")
        engine.qdrant_client = mock_client

        threat = {"antigen_id": "test", "timestamp": datetime.now().isoformat()}

        result = await engine.store_event(threat)

        assert result is False  # Graceful failure


# =====================================================================
# TEST DENDRITIC CORE INTEGRATION ERRORS
# =====================================================================


class TestDendriticCoreErrors:
    """Testa error paths no DendriticCore."""

    @pytest.mark.asyncio
    async def test_start_antigen_consumption(self):
        """Testa start_antigen_consumption loop (lines 607-619)."""
        dc = DendriticCore()

        # Mock consumer to return one antigen then stop
        call_count = [0]

        async def mock_consume(callback):
            call_count[0] += 1
            # Simulate one antigen
            await callback({"antigen_id": "test_start", "severity": 0.5})

        dc.antigen_consumer.consume_antigens = mock_consume

        # Mock present methods to avoid HTTP calls
        async def mock_present(threat, **kwargs):
            return {"status": "mocked"}

        dc.present_to_b_cell = mock_present
        dc.present_to_t_cells = mock_present

        await dc.start_antigen_consumption()

        assert call_count[0] == 1  # Callback was called

    def test_stop_antigen_consumption(self):
        """Testa stop_antigen_consumption (line 621-623)."""
        dc = DendriticCore()

        dc.antigen_consumer.running = True
        dc.stop_antigen_consumption()

        assert dc.antigen_consumer.running is False

    @pytest.mark.asyncio
    async def test_present_to_t_cells_cytotoxic_exception(self):
        """Testa cytotoxic T-cell exception (line 554-555)."""
        dc = DendriticCore()

        threat = {"antigen_id": "test_cyto_exc"}

        with patch("httpx.AsyncClient") as mock_client_class:
            from unittest.mock import AsyncMock

            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Helper succeeds
            mock_helper_response = AsyncMock()
            mock_helper_response.status_code = 200
            mock_helper_response.json.return_value = {"ok": True}

            # Cytotoxic raises exception
            def side_effect(*args, **kwargs):
                url = args[0]
                if "cytotoxic" in url:
                    raise Exception("Cytotoxic error")
                return mock_helper_response

            mock_client.post.side_effect = side_effect

            result = await dc.present_to_t_cells(threat, activate_helper=True, activate_cytotoxic=True)

            # Helper should succeed, cytotoxic should have error
            assert result["helper_t"]["status"] == "activated"
            assert result["cytotoxic_t"]["status"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
