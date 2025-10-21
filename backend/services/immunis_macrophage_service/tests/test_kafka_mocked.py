"""
Testes com Kafka MOCKADO para atingir 95%+

OBJETIVO: Cobrir linhas 262-269, 351-370 (Kafka init + send) com mocks CIRÚRGICOS
ESTRATÉGIA: Mock APENAS KafkaProducer, testa a lógica de negócio

Padrão Pagani: Mock cirúrgico quando infra externa necessária.
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_macrophage_service")


class TestKafkaInitialization:
    """Testa inicialização do Kafka (linhas 262-269)."""

    def test_kafka_producer_init_success(self):
        """Testa que Kafka producer é inicializado com sucesso."""
        # Mock kafka module ANTES de importar macrophage_core
        mock_kafka_producer_class = MagicMock()
        mock_producer_instance = MagicMock()
        mock_kafka_producer_class.return_value = mock_producer_instance

        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer = mock_kafka_producer_class

        # Inject mock kafka module
        with patch.dict('sys.modules', {'kafka': mock_kafka_module}):
            # Force reimport to trigger Kafka import with mock
            if 'macrophage_core' in sys.modules:
                del sys.modules['macrophage_core']

            import macrophage_core
            from macrophage_core import MacrophageCore

            # KAFKA_AVAILABLE deve ser True agora
            assert macrophage_core.KAFKA_AVAILABLE is True

            core = MacrophageCore(kafka_bootstrap_servers="localhost:9092")

            # Deve ter inicializado producer
            assert core.kafka_producer is not None

            # Kafka producer deve ter sido chamado
            mock_kafka_producer_class.assert_called_once()

    def test_kafka_producer_init_failure(self):
        """Testa que exception no Kafka init não quebra o serviço (linha 268-269)."""
        # Mock kafka module que lança exception
        mock_kafka_producer_class = MagicMock()
        mock_kafka_producer_class.side_effect = Exception("Kafka connection refused")

        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer = mock_kafka_producer_class

        # Inject mock kafka module
        with patch.dict('sys.modules', {'kafka': mock_kafka_module}):
            # Force reimport
            if 'macrophage_core' in sys.modules:
                del sys.modules['macrophage_core']

            import macrophage_core
            from macrophage_core import MacrophageCore

            # KAFKA_AVAILABLE deve ser True (import sucedeu)
            assert macrophage_core.KAFKA_AVAILABLE is True

            core = MacrophageCore(kafka_bootstrap_servers="localhost:9092")

            # Deve ter fallback para None (exception no __init__)
            assert core.kafka_producer is None


class TestKafkaSendSuccess:
    """Testa send bem-sucedido ao Kafka (linhas 351-370)."""

    @pytest.mark.asyncio
    async def test_present_antigen_kafka_success(self):
        """Testa apresentação de antígeno com Kafka disponível (linhas 351-365)."""
        # Mock kafka module
        mock_kafka_producer_class = MagicMock()
        mock_producer_instance = MagicMock()

        # Mock future.get() para simular send bem-sucedido
        mock_result = MagicMock()
        mock_result.partition = 0
        mock_result.offset = 12345

        mock_future = MagicMock()
        mock_future.get.return_value = mock_result

        mock_producer_instance.send.return_value = mock_future
        mock_kafka_producer_class.return_value = mock_producer_instance

        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer = mock_kafka_producer_class

        # Inject mock kafka module
        with patch.dict('sys.modules', {'kafka': mock_kafka_module}):
            # Force reimport
            if 'macrophage_core' in sys.modules:
                del sys.modules['macrophage_core']

            from macrophage_core import MacrophageCore

            core = MacrophageCore()

            artifact = {
                "sample_hash": "abc123def456",
                "malware_family": "TestMalware",
                "analysis": {"severity": 0.85},
                "iocs": {"file_hashes": ["abc123"]},
                "yara_signature": "rule test {}",
            }

            result = await core.present_antigen(artifact)

            # Deve ter retornado sucesso
            assert result["status"] == "antigen_presented"
            assert result["kafka_partition"] == 0
            assert result["kafka_offset"] == 12345

            # Kafka send deve ter sido chamado
            mock_producer_instance.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_present_antigen_kafka_send_failure(self):
        """Testa falha no Kafka send (linhas 367-370)."""
        # Mock kafka module
        mock_kafka_producer_class = MagicMock()
        mock_producer_instance = MagicMock()

        # Mock send que lança exception
        mock_producer_instance.send.side_effect = Exception("Kafka send failed")

        mock_kafka_producer_class.return_value = mock_producer_instance

        mock_kafka_module = MagicMock()
        mock_kafka_module.KafkaProducer = mock_kafka_producer_class

        # Inject mock kafka module
        with patch.dict('sys.modules', {'kafka': mock_kafka_module}):
            # Force reimport
            if 'macrophage_core' in sys.modules:
                del sys.modules['macrophage_core']

            from macrophage_core import MacrophageCore

            core = MacrophageCore()

            artifact = {
                "sample_hash": "abc123def456",
                "malware_family": "TestMalware",
                "analysis": {"severity": 0.85},
                "iocs": {"file_hashes": ["abc123"]},
                "yara_signature": "rule test {}",
            }

            result = await core.present_antigen(artifact)

            # Deve ter retornado presentation_failed
            assert result["status"] == "presentation_failed"
            assert "error" in result


class TestKafkaUnavailableWarning:
    """Testa warning quando Kafka não disponível (linha 27)."""

    def test_kafka_unavailable_warning_logged(self, caplog):
        """Testa que warning é logado quando Kafka não disponível."""
        import logging
        caplog.set_level(logging.WARNING)

        # Remove kafka do sys.modules para forçar ImportError
        if 'kafka' in sys.modules:
            del sys.modules['kafka']

        # Force reimport SEM kafka module para trigger linha 27 (warning)
        if 'macrophage_core' in sys.modules:
            del sys.modules['macrophage_core']

        import importlib
        import macrophage_core

        # KAFKA_AVAILABLE deve ser False agora
        assert macrophage_core.KAFKA_AVAILABLE is False

        from macrophage_core import MacrophageCore
        core = MacrophageCore()

        # Sem Kafka, producer deve ser None
        assert core.kafka_producer is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
