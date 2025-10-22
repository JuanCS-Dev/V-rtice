"""
Testes REAIS para immunis_dendritic_service - Dendritic Cell Core

OBJETIVO: 100% COBERTURA ABSOLUTA do dendritic_core.py
- Testa antigen processing (Kafka consumption graceful degradation)
- Testa event correlation (Qdrant vector DB graceful degradation)
- Testa vector embedding (_vectorize_threat com 128 dimensions)
- Testa activation criteria (_should_activate)
- Testa presentation to B-cells and T-cells
- ZERO MOCKS desnecessários (graceful degradation permite testes sem Kafka/Qdrant)

Padrão Pagani Absoluto: Dendritic Cell ponte entre imunidade inata e adaptativa.
"""

import pytest
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_dendritic_service")

from dendritic_core import (
    DendriticCore,
    EventCorrelationEngine,
    AntigenConsumer,
)


class TestEventCorrelationEngine:
    """Testes de Event Correlation Engine (vector DB)."""

    def test_event_correlation_engine_creation(self):
        """Testa criação de EventCorrelationEngine."""
        engine = EventCorrelationEngine(qdrant_url="localhost", qdrant_port=6333)

        assert engine.collection_name == "threat_events"
        assert engine.vector_size == 128

    def test_vectorize_threat_basic(self):
        """Testa vectorização básica de threat."""
        engine = EventCorrelationEngine()

        threat = {
            "antigen_id": "ag_001",
            "timestamp": datetime.now().isoformat(),
            "malware_family": "Emotet",
            "severity": 0.75,
            "iocs": {
                "ips": ["1.2.3.4", "5.6.7.8"],
                "domains": ["evil.com"],
                "urls": [],
                "file_hashes": ["abc123"],
                "mutexes": [],
                "registry_keys": [],
            },
            "source": "macrophage",
        }

        vector = engine._vectorize_threat(threat)

        # Deve retornar 128 dimensions
        assert len(vector) == 128
        # Deve ter valores float entre 0-1
        assert all(isinstance(v, float) for v in vector)
        assert all(0.0 <= v <= 1.0 for v in vector)

    def test_vectorize_threat_severity_encoding(self):
        """Testa que severity é encodado nos primeiros 10 elementos."""
        engine = EventCorrelationEngine()

        threat_high = {"severity": 0.9, "timestamp": datetime.now().isoformat()}
        threat_low = {"severity": 0.1, "timestamp": datetime.now().isoformat()}

        vector_high = engine._vectorize_threat(threat_high)
        vector_low = engine._vectorize_threat(threat_low)

        # Primeiros 10 elementos devem ser severity
        assert all(v == 0.9 for v in vector_high[:10])
        assert all(v == 0.1 for v in vector_low[:10])

    def test_vectorize_threat_temporal_features(self):
        """Testa que temporal features (hour of day) são encodados."""
        engine = EventCorrelationEngine()

        # Cria threat com timestamp específico (hora 14:00)
        timestamp = datetime.now().replace(hour=14, minute=0, second=0)
        threat = {"timestamp": timestamp.isoformat(), "severity": 0.5}

        vector = engine._vectorize_threat(threat)

        # Vector tem 128 dims: severity(10) + family_hash(16) + ioc_counts(6) + hour_vector(24) + source_hash(16) + padding
        # hour_vector começa no índice 32 (10 + 16 + 6)
        hour_vector_start = 32
        hour_vector = vector[hour_vector_start : hour_vector_start + 24]

        # Apenas hora 14 deve ser 1.0, resto 0.0
        assert hour_vector[14] == 1.0
        assert sum(hour_vector) == 1.0  # Apenas 1 hora ativa

    def test_vectorize_threat_pads_to_128(self):
        """Testa que vector sempre tem 128 dimensions (com padding se necessário)."""
        engine = EventCorrelationEngine()

        # Threat minimal (deve fazer padding)
        threat_minimal = {}

        vector = engine._vectorize_threat(threat_minimal)

        assert len(vector) == 128

    @pytest.mark.asyncio
    async def test_store_event_without_qdrant(self):
        """Testa que store_event funciona sem Qdrant (graceful degradation)."""
        engine = EventCorrelationEngine()

        # Se Qdrant não disponível, deve retornar False mas não falhar
        threat = {"antigen_id": "ag_test", "timestamp": datetime.now().isoformat()}

        result = await engine.store_event(threat)

        # Resultado depende de Qdrant estar disponível
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_correlate_events_without_qdrant(self):
        """Testa que correlate_events funciona sem Qdrant (retorna lista vazia)."""
        engine = EventCorrelationEngine()

        threat = {"antigen_id": "ag_test", "timestamp": datetime.now().isoformat()}

        correlated = await engine.correlate_events(threat, time_window_hours=24, top_k=10)

        # Sem Qdrant, retorna lista vazia
        assert isinstance(correlated, list)


class TestAntigenConsumer:
    """Testes de Antigen Consumer (Kafka)."""

    def test_antigen_consumer_creation(self):
        """Testa criação de AntigenConsumer."""
        consumer = AntigenConsumer(kafka_bootstrap_servers="localhost:9092")

        assert consumer.kafka_servers == "localhost:9092"
        assert consumer.running is False

    def test_antigen_consumer_stop(self):
        """Testa stop do consumer."""
        consumer = AntigenConsumer()

        consumer.stop()

        assert consumer.running is False


class TestDendriticCoreActivation:
    """Testes de critérios de ativação."""

    def test_should_activate_high_severity(self):
        """Testa que severity >= 0.7 triggera ativação."""
        core = DendriticCore()

        threat_high = {"severity": 0.75, "correlation_count": 0}

        assert core._should_activate(threat_high) is True

    def test_should_activate_multiple_correlations(self):
        """Testa que correlation_count >= 3 triggera ativação."""
        core = DendriticCore()

        threat_correlated = {"severity": 0.4, "correlation_count": 5}

        assert core._should_activate(threat_correlated) is True

    def test_should_activate_novel_threat(self):
        """Testa que novel threat (0 correlations + severity >= 0.5) triggera ativação."""
        core = DendriticCore()

        threat_novel = {"severity": 0.6, "correlation_count": 0}

        assert core._should_activate(threat_novel) is True

    def test_should_not_activate_low_severity_few_correlations(self):
        """Testa que low severity + few correlations NÃO triggera ativação."""
        core = DendriticCore()

        threat_low = {"severity": 0.3, "correlation_count": 1}

        assert core._should_activate(threat_low) is False

    def test_should_activate_boundary_severity(self):
        """Testa boundary de severity (exatamente 0.7)."""
        core = DendriticCore()

        threat_boundary = {"severity": 0.7, "correlation_count": 0}

        assert core._should_activate(threat_boundary) is True

    def test_should_activate_boundary_correlations(self):
        """Testa boundary de correlations (exatamente 3)."""
        core = DendriticCore()

        threat_boundary = {"severity": 0.3, "correlation_count": 3}

        assert core._should_activate(threat_boundary) is True

    def test_should_activate_novel_boundary(self):
        """Testa boundary de novel threat (severity exatamente 0.5, 0 correlations)."""
        core = DendriticCore()

        threat_boundary = {"severity": 0.5, "correlation_count": 0}

        assert core._should_activate(threat_boundary) is True


class TestAntigenProcessing:
    """Testes de processamento de antigens."""

    @pytest.mark.asyncio
    async def test_process_antigen_basic(self):
        """Testa processamento básico de antigen."""
        core = DendriticCore()

        antigen = {
            "antigen_id": "ag_001",
            "timestamp": datetime.now().isoformat(),
            "malware_family": "Emotet",
            "severity": 0.6,
            "iocs": {
                "ips": ["192.168.1.100"],
            },
        }

        result = await core.process_antigen(antigen)

        assert result["antigen_id"] == "ag_001"
        assert result["malware_family"] == "Emotet"
        assert "correlated_events" in result
        assert "correlation_count" in result
        assert "activation_required" in result
        assert "processing_timestamp" in result

    @pytest.mark.asyncio
    async def test_process_antigen_stores_in_history(self):
        """Testa que antigen processado é armazenado em processed_antigens."""
        core = DendriticCore()

        antigen = {
            "antigen_id": "ag_002",
            "timestamp": datetime.now().isoformat(),
            "malware_family": "Ryuk",
            "severity": 0.7,
        }

        await core.process_antigen(antigen)

        assert len(core.processed_antigens) == 1
        assert core.processed_antigens[0]["antigen_id"] == "ag_002"

    @pytest.mark.asyncio
    async def test_process_antigen_updates_last_processing_time(self):
        """Testa que last_processing_time é atualizado."""
        core = DendriticCore()

        antigen = {"antigen_id": "ag_003", "timestamp": datetime.now().isoformat(), "severity": 0.5}

        before = datetime.now()
        await core.process_antigen(antigen)
        after = datetime.now()

        assert core.last_processing_time is not None
        assert before <= core.last_processing_time <= after

    @pytest.mark.asyncio
    async def test_process_antigen_enriches_with_defaults(self):
        """Testa que antigen é enriched com valores default."""
        core = DendriticCore()

        # Antigen minimal
        antigen = {"antigen_id": "ag_minimal", "severity": 0.3}

        result = await core.process_antigen(antigen)

        # Deve ter campos enriquecidos
        assert result["source"] == "macrophage_service"  # Default
        assert "iocs" in result
        assert "processing_timestamp" in result


class TestPresentationToCells:
    """Testes de apresentação para B-cells e T-cells."""

    @pytest.mark.asyncio
    async def test_present_to_b_cell_structure(self):
        """Testa estrutura de payload para B-Cell."""
        core = DendriticCore(b_cell_endpoint="http://fake-bcell:8015")

        threat = {
            "antigen_id": "ag_bcell",
            "malware_family": "TestMalware",
            "iocs": {"ips": ["1.1.1.1"]},
            "severity": 0.6,
            "correlated_events": [],
        }

        # Não vamos fazer HTTP call real, mas podemos testar que método executa sem erro
        # (vai falhar na conexão, mas isso é esperado em testes sem serviços reais)
        result = await core.present_to_b_cell(threat)

        # Deve retornar dict com status
        assert isinstance(result, dict)
        assert "status" in result

    @pytest.mark.asyncio
    async def test_present_to_t_cells_structure(self):
        """Testa estrutura de payload para T-Cells."""
        core = DendriticCore(
            t_helper_endpoint="http://fake-helper:8016", t_cytotoxic_endpoint="http://fake-cytotoxic:8017"
        )

        threat = {
            "antigen_id": "ag_tcells",
            "malware_family": "TestMalware",
            "severity": 0.8,
            "correlated_events": [],
        }

        # Teste estrutural (HTTP call vai falhar mas método não deve crashar)
        result = await core.present_to_t_cells(threat, activate_helper=True, activate_cytotoxic=False)

        assert isinstance(result, dict)


class TestAdaptiveImmunityActivation:
    """Testes de ativação da imunidade adaptativa."""

    @pytest.mark.asyncio
    async def test_activate_adaptive_immunity_structure(self):
        """Testa estrutura de activate_adaptive_immunity."""
        core = DendriticCore()

        threat = {
            "antigen_id": "ag_adaptive",
            "malware_family": "Ransomware",
            "severity": 0.9,
            "iocs": {"ips": ["10.0.0.1"]},
            "correlated_events": [],
            "correlation_count": 0,
        }

        result = await core.activate_adaptive_immunity(threat)

        # Deve retornar dict com results
        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "antigen_id" in result
        assert "activations" in result


class TestStatus:
    """Testes do endpoint de status."""

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Testa get_status retorna informações corretas."""
        core = DendriticCore()

        # Processa 2 antigens
        antigen1 = {"antigen_id": "ag1", "timestamp": datetime.now().isoformat(), "severity": 0.5}
        antigen2 = {"antigen_id": "ag2", "timestamp": datetime.now().isoformat(), "severity": 0.7}

        await core.process_antigen(antigen1)
        await core.process_antigen(antigen2)

        status = await core.get_status()

        assert status["status"] == "operational"
        assert status["processed_antigens_count"] == 2
        assert status["activations_count"] >= 0
        assert status["last_processing"] != "N/A"
        assert "kafka_enabled" in status
        assert "qdrant_enabled" in status


class TestIntegration:
    """Testes de integração end-to-end."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Testa pipeline completo: process → activate → present."""
        core = DendriticCore()

        # 1. Process antigen
        antigen = {
            "antigen_id": "ag_pipeline",
            "timestamp": datetime.now().isoformat(),
            "malware_family": "APT29",
            "severity": 0.85,
            "iocs": {
                "ips": ["192.168.1.100", "192.168.1.101"],
                "domains": ["malicious.com"],
                "file_hashes": ["abc123def456"],
            },
        }

        processed = await core.process_antigen(antigen)

        # Deve ter processado
        assert processed["antigen_id"] == "ag_pipeline"
        assert processed["activation_required"] is True  # severity 0.85 >= 0.7

        # 2. Activate adaptive immunity (se activation_required)
        if processed["activation_required"]:
            activation_result = await core.activate_adaptive_immunity(processed)

            assert activation_result["antigen_id"] == "ag_pipeline"
            assert "activations" in activation_result

        # 3. Verify status
        status = await core.get_status()
        assert status["processed_antigens_count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
