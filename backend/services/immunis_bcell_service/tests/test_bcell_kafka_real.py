"""
Testes REAIS para cobertura de código Kafka em bcell_core.py

Objetivo: Cobrir linhas 41, 299-306, 403-430 (código Kafka)
Abordagem: Mock MÍNIMO apenas para simular Kafka disponível
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_bcell_service")


class TestKafkaIntegration:
    """Testes de integração com Kafka (mocked)."""

    @pytest.mark.asyncio
    async def test_bcell_core_with_kafka_available(self):
        """Testa BCellCore quando Kafka está disponível e funcional."""

        # Mock do KafkaProducer
        mock_kafka_producer_class = MagicMock()
        mock_producer_instance = MagicMock()
        mock_kafka_producer_class.return_value = mock_producer_instance

        # Mock do future retornado por send()
        mock_future = MagicMock()
        mock_result = MagicMock()
        mock_result.partition = 0
        mock_result.offset = 42
        mock_future.get.return_value = mock_result
        mock_producer_instance.send.return_value = mock_future

        # Patch ANTES de importar bcell_core
        with patch.dict("sys.modules", {"kafka": MagicMock(KafkaProducer=mock_kafka_producer_class)}):
            # Force reimport para que o try/except execute com Kafka "disponível"
            import importlib
            if "bcell_core" in sys.modules:
                del sys.modules["bcell_core"]

            # Agora importa bcell_core com Kafka mockado
            import bcell_core

            # Verifica que KAFKA_AVAILABLE = True (linha 41)
            assert bcell_core.KAFKA_AVAILABLE is True

            # Cria BCellCore (deve inicializar kafka_producer, linhas 299-306)
            core = bcell_core.BCellCore(kafka_bootstrap_servers="localhost:9092")

            # Verifica que kafka_producer foi criado
            assert core.kafka_producer is not None

            # Ativa com antigen (deve publicar no Kafka, linhas 403-430)
            antigen = {
                "antigen_id": "ag_kafka_test",
                "malware_family": "KafkaTest",
                "iocs": {
                    "strings": ["kafka_pattern"],
                    "file_hashes": [],
                    "mutexes": [],
                    "registry_keys": [],
                },
                "correlated_events": [],
            }

            result = await core.activate(antigen)

            # Deve ter gerado signature
            assert result["signature_generated"] is True

            # Verifica que publish_signature foi chamado
            # (internamente chama kafka_producer.send)
            assert mock_producer_instance.send.called

            # Verifica payload enviado ao Kafka
            call_args = mock_producer_instance.send.call_args
            assert call_args[0][0] == "signature.updates"  # Topic
            payload = call_args[1]["value"]
            assert payload["malware_family"] == "KafkaTest"
            assert payload["source"] == "bcell_service"
            assert "signature_id" in payload
            assert "yara_signature" in payload

    @pytest.mark.asyncio
    async def test_bcell_core_kafka_initialization_failure(self):
        """Testa BCellCore quando Kafka está disponível mas init falha."""

        # Mock que lança exceção ao criar KafkaProducer
        mock_kafka_producer_class = MagicMock()
        mock_kafka_producer_class.side_effect = Exception("Kafka connection refused")

        with patch.dict("sys.modules", {"kafka": MagicMock(KafkaProducer=mock_kafka_producer_class)}):
            # Force reimport
            import importlib
            if "bcell_core" in sys.modules:
                del sys.modules["bcell_core"]

            import bcell_core

            # KAFKA_AVAILABLE = True, mas init falha (linha 306)
            core = bcell_core.BCellCore(kafka_bootstrap_servers="invalid:9999")

            # kafka_producer deve ser None (init falhou)
            assert core.kafka_producer is None

            # Ativa antigen (deve funcionar mesmo sem Kafka)
            antigen = {
                "antigen_id": "ag_no_kafka",
                "malware_family": "NoKafka",
                "iocs": {
                    "strings": ["no_kafka_pattern"],
                    "file_hashes": [],
                    "mutexes": [],
                    "registry_keys": [],
                },
                "correlated_events": [],
            }

            result = await core.activate(antigen)

            # Deve funcionar normalmente (graceful degradation)
            assert result["signature_generated"] is True

    @pytest.mark.asyncio
    async def test_publish_signature_kafka_send_failure(self):
        """Testa publish_signature quando Kafka.send() falha."""

        # Mock do KafkaProducer que falha ao enviar
        mock_kafka_producer_class = MagicMock()
        mock_producer_instance = MagicMock()
        mock_kafka_producer_class.return_value = mock_producer_instance

        # send() lança exceção
        mock_producer_instance.send.side_effect = Exception("Kafka broker unavailable")

        with patch.dict("sys.modules", {"kafka": MagicMock(KafkaProducer=mock_kafka_producer_class)}):
            import importlib
            if "bcell_core" in sys.modules:
                del sys.modules["bcell_core"]

            import bcell_core

            core = bcell_core.BCellCore(kafka_bootstrap_servers="localhost:9092")

            # Ativa antigen
            antigen = {
                "antigen_id": "ag_send_fail",
                "malware_family": "SendFail",
                "iocs": {
                    "strings": ["fail_pattern"],
                    "file_hashes": [],
                    "mutexes": [],
                    "registry_keys": [],
                },
                "correlated_events": [],
            }

            result = await core.activate(antigen)

            # Signature gerada, mas publicação falhou (linhas 428-430)
            assert result["signature_generated"] is True
            # Kafka send foi tentado mas falhou
            assert mock_producer_instance.send.called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
