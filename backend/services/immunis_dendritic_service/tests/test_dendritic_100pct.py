"""
Testes ABSOLUTOS para immunis_dendritic_service - 100% Coverage

OBJETIVO: 100% COBERTURA ABSOLUTA baseado em fisiologia de Dendritic Cells
ESTRATÉGIA: Testes inspirados em função biológica real:

FISIOLOGIA DENDRITIC CELLS:
1. Antigen Presentation (APCs profissionais) - capturam, processam, apresentam
2. Pattern Recognition (PRRs detectam PAMPs)
3. Maturação e Migração - imaturas capturam → maturam → apresentam
4. Costimulation - sinais CD80/CD86 para ativar linfócitos
5. Event Correlation - agregam exposições múltiplas ao mesmo antígeno
6. Ponte Inata-Adaptativa - conectam Macrophages → B-cells/T-cells

Padrão Pagani Absoluto: Dendritic Cell = APC profissional DEVE ter 100%.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_dendritic_service")

from dendritic_core import (
    DendriticCore,
    EventCorrelationEngine,
    AntigenConsumer,
)


# =====================================================================
# TEST ACTIVATION CRITERIA (simula maturação de DC)
# =====================================================================


class TestActivationCriteria:
    """Testa _should_activate - simula maturação e activation thresholds."""

    def test_should_activate_high_severity(self):
        """Testa activation com high severity (≥0.7) - simula PAMP forte."""
        dc = DendriticCore()
        threat = {"severity": 0.8, "correlation_count": 0}

        assert dc._should_activate(threat) is True

    def test_should_activate_threshold_boundary(self):
        """Testa boundary exato em 0.7."""
        dc = DendriticCore()
        threat_exact = {"severity": 0.7, "correlation_count": 1}  # 1 correlation prevents novel logic
        threat_below = {"severity": 0.69, "correlation_count": 1}

        assert dc._should_activate(threat_exact) is True
        assert dc._should_activate(threat_below) is False

    def test_should_activate_multiple_correlations(self):
        """Testa activation com ≥3 correlations - simula exposure múltipla."""
        dc = DendriticCore()
        threat = {"severity": 0.5, "correlation_count": 3}

        assert dc._should_activate(threat) is True

    def test_should_activate_correlation_boundary(self):
        """Testa boundary em 3 correlations."""
        dc = DendriticCore()
        threat_yes = {"severity": 0.5, "correlation_count": 3}
        threat_no = {"severity": 0.5, "correlation_count": 2}

        assert dc._should_activate(threat_yes) is True
        assert dc._should_activate(threat_no) is False

    def test_should_activate_novel_threat(self):
        """Testa activation para novel threat (0 correlations, severity ≥0.5)."""
        dc = DendriticCore()
        threat_novel = {"severity": 0.6, "correlation_count": 0}
        threat_too_low = {"severity": 0.4, "correlation_count": 0}

        assert dc._should_activate(threat_novel) is True
        assert dc._should_activate(threat_too_low) is False

    def test_should_activate_novel_boundary(self):
        """Testa boundary de novel threat em 0.5."""
        dc = DendriticCore()
        threat_exact = {"severity": 0.5, "correlation_count": 0}
        threat_below = {"severity": 0.49, "correlation_count": 0}

        assert dc._should_activate(threat_exact) is True
        assert dc._should_activate(threat_below) is False

    def test_should_activate_insufficient_evidence(self):
        """Testa que low severity + few correlations NÃO ativa."""
        dc = DendriticCore()
        threat = {"severity": 0.3, "correlation_count": 1}

        assert dc._should_activate(threat) is False


# =====================================================================
# TEST EVENT CORRELATION (simula agregação de exposições)
# =====================================================================


class TestEventCorrelation:
    """Testa event correlation - simula detecção de pattern temporal."""

    @pytest.mark.asyncio
    async def test_correlate_events_qdrant_not_available(self):
        """Testa graceful degradation quando Qdrant não disponível."""
        engine = EventCorrelationEngine()
        engine.qdrant_client = None  # Force unavailable

        threat = {"antigen_id": "ag_001", "timestamp": datetime.now().isoformat()}
        result = await engine.correlate_events(threat)

        assert result == []  # Graceful degradation

    @pytest.mark.asyncio
    async def test_store_event_qdrant_not_available(self):
        """Testa graceful degradation no store."""
        engine = EventCorrelationEngine()
        engine.qdrant_client = None

        threat = {"antigen_id": "ag_002", "timestamp": datetime.now().isoformat()}
        result = await engine.store_event(threat)

        assert result is False  # Graceful failure

    @pytest.mark.asyncio
    async def test_correlate_events_empty_results(self):
        """Testa correlation sem matches."""
        engine = EventCorrelationEngine()

        # Mock Qdrant client
        mock_client = MagicMock()
        mock_client.search.return_value = []  # No results
        engine.qdrant_client = mock_client

        threat = {"antigen_id": "ag_003", "timestamp": datetime.now().isoformat()}
        result = await engine.correlate_events(threat)

        assert result == []

    @pytest.mark.asyncio
    async def test_correlate_events_time_window_filtering(self):
        """Testa time window filtering (24h) - simula temporal proximity."""
        engine = EventCorrelationEngine()

        # Mock Qdrant search result
        old_timestamp = (datetime.now() - timedelta(hours=48)).isoformat()  # Outside window
        recent_timestamp = (datetime.now() - timedelta(hours=12)).isoformat()  # Inside window

        mock_hit_old = MagicMock()
        mock_hit_old.payload = {
            "threat_id": "old",
            "timestamp": old_timestamp,
            "malware_family": "Emotet",
            "severity": 0.8,
            "source": "test",
        }
        mock_hit_old.score = 0.95

        mock_hit_recent = MagicMock()
        mock_hit_recent.payload = {
            "threat_id": "recent",
            "timestamp": recent_timestamp,
            "malware_family": "Emotet",
            "severity": 0.8,
            "source": "test",
        }
        mock_hit_recent.score = 0.92

        mock_client = MagicMock()
        mock_client.search.return_value = [mock_hit_old, mock_hit_recent]
        engine.qdrant_client = mock_client

        threat = {"antigen_id": "ag_004", "timestamp": datetime.now().isoformat()}
        result = await engine.correlate_events(threat, time_window_hours=24)

        # Only recent should be included
        assert len(result) == 1
        assert result[0]["threat_id"] == "recent"

    @pytest.mark.asyncio
    async def test_correlate_events_exception_handling(self):
        """Testa exception handling no correlate_events."""
        engine = EventCorrelationEngine()

        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("Qdrant error")
        engine.qdrant_client = mock_client

        threat = {"antigen_id": "ag_005", "timestamp": datetime.now().isoformat()}
        result = await engine.correlate_events(threat)

        assert result == []  # Graceful error handling


# =====================================================================
# TEST ANTIGEN PROCESSING (simula processamento completo)
# =====================================================================


class TestAntigenProcessing:
    """Testa process_antigen - simula processing pipeline completo."""

    @pytest.mark.asyncio
    async def test_process_antigen_full_pipeline(self):
        """Testa pipeline completo: enrich → store → correlate → activate decision."""
        dc = DendriticCore()

        antigen = {
            "antigen_id": "ag_full",
            "timestamp": datetime.now().isoformat(),
            "malware_family": "Emotet",
            "severity": 0.8,
            "iocs": {"ips": ["1.2.3.4"]},
            "yara_signature": "rule emotet { ... }",
            "source": "macrophage",
        }

        result = await dc.process_antigen(antigen)

        # Verify enrichment
        assert result["antigen_id"] == "ag_full"
        assert result["source"] == "macrophage"
        assert "processing_timestamp" in result
        assert "correlated_events" in result
        assert "correlation_count" in result
        assert "activation_required" in result

        # Verify stored in processed_antigens
        assert len(dc.processed_antigens) == 1
        assert dc.last_processing_time is not None

    @pytest.mark.asyncio
    async def test_process_antigen_missing_fields(self):
        """Testa process_antigen com campos missing - graceful handling."""
        dc = DendriticCore()

        antigen_minimal = {
            "antigen_id": "ag_minimal",
            "severity": 0.3,  # Provide severity to avoid None
            # Missing: timestamp, malware_family, etc
        }

        result = await dc.process_antigen(antigen_minimal)

        # Should not crash, uses defaults
        assert result["antigen_id"] == "ag_minimal"
        assert "processing_timestamp" in result
        assert result["source"] == "macrophage_service"  # Default

    @pytest.mark.asyncio
    async def test_process_antigen_high_severity_activates(self):
        """Testa que high severity (0.8) resulta em activation_required=True."""
        dc = DendriticCore()

        antigen = {
            "antigen_id": "ag_high_sev",
            "timestamp": datetime.now().isoformat(),
            "severity": 0.8,
        }

        result = await dc.process_antigen(antigen)

        assert result["activation_required"] is True  # High severity activates


# =====================================================================
# TEST PRESENTATION TO ADAPTIVE IMMUNITY
# =====================================================================


class TestPresentationToAdaptive:
    """Testa presentation to B-cells/T-cells - simula costimulation."""

    @pytest.mark.asyncio
    async def test_present_to_b_cell_success(self):
        """Testa B-Cell presentation success."""
        dc = DendriticCore()

        threat = {
            "antigen_id": "ag_bcell",
            "malware_family": "Emotet",
            "severity": 0.8,
            "iocs": {"ips": ["1.2.3.4"]},
            "yara_signature": "rule test {}",
            "correlated_events": [],
        }

        # Mock httpx
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"antibody_id": "ab_001"}
            mock_client.post.return_value = mock_response

            result = await dc.present_to_b_cell(threat)

            assert result["status"] == "presented"
            assert "b_cell_response" in result

    @pytest.mark.asyncio
    async def test_present_to_b_cell_http_error(self):
        """Testa B-Cell presentation com HTTP error."""
        dc = DendriticCore()

        threat = {"antigen_id": "ag_bcell_fail", "malware_family": "Test"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_client.post.return_value = mock_response

            result = await dc.present_to_b_cell(threat)

            assert result["status"] == "failed"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_present_to_b_cell_exception(self):
        """Testa B-Cell presentation com exception."""
        dc = DendriticCore()

        threat = {"antigen_id": "ag_bcell_exc"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.side_effect = Exception("Network error")

            result = await dc.present_to_b_cell(threat)

            assert result["status"] == "error"
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_present_to_t_cells_helper_only(self):
        """Testa T-Cell presentation com apenas Helper T."""
        dc = DendriticCore()

        threat = {
            "antigen_id": "ag_tcell",
            "malware_family": "Test",
            "severity": 0.5,
            "iocs": {},
            "correlation_count": 1,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"orchestration": "activated"}
            mock_client.post.return_value = mock_response

            result = await dc.present_to_t_cells(threat, activate_helper=True, activate_cytotoxic=False)

            assert "helper_t" in result
            assert result["helper_t"]["status"] == "activated"
            assert "cytotoxic_t" not in result

    @pytest.mark.asyncio
    async def test_present_to_t_cells_both_activated(self):
        """Testa T-Cell presentation com Helper + Cytotoxic."""
        dc = DendriticCore()

        threat = {
            "antigen_id": "ag_tcell_both",
            "malware_family": "High threat",
            "severity": 0.9,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"activated": True}
            mock_client.post.return_value = mock_response

            result = await dc.present_to_t_cells(threat, activate_helper=True, activate_cytotoxic=True)

            assert "helper_t" in result
            assert "cytotoxic_t" in result
            assert result["helper_t"]["status"] == "activated"
            assert result["cytotoxic_t"]["status"] == "activated"

    @pytest.mark.asyncio
    async def test_present_to_t_cells_helper_fails_cytotoxic_succeeds(self):
        """Testa failure parcial - helper falha, cytotoxic sucede."""
        dc = DendriticCore()

        threat = {"antigen_id": "ag_partial_fail"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Helper fails, cytotoxic succeeds
            def side_effect(*args, **kwargs):
                url = args[0]
                mock_resp = AsyncMock()
                if "helper-t" in url:
                    mock_resp.status_code = 500
                else:  # cytotoxic
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = {"ok": True}
                return mock_resp

            mock_client.post.side_effect = side_effect

            result = await dc.present_to_t_cells(threat, activate_helper=True, activate_cytotoxic=True)

            assert result["helper_t"]["status"] == "failed"
            assert result["cytotoxic_t"]["status"] == "activated"

    @pytest.mark.asyncio
    async def test_present_to_t_cells_exception(self):
        """Testa T-Cell presentation com exception geral."""
        dc = DendriticCore()

        threat = {"antigen_id": "ag_tcell_exc"}

        with patch("httpx.AsyncClient", side_effect=Exception("Import error")):
            result = await dc.present_to_t_cells(threat)

            assert result["status"] == "error"


# =====================================================================
# TEST ADAPTIVE IMMUNITY ACTIVATION
# =====================================================================


class TestAdaptiveImmunityActivation:
    """Testa activate_adaptive_immunity - simula activation completa."""

    @pytest.mark.asyncio
    async def test_activate_adaptive_immunity_low_severity(self):
        """Testa activation com low severity - apenas B-cell + Helper T."""
        dc = DendriticCore()

        threat = {
            "antigen_id": "ag_low",
            "severity": 0.5,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_client.post.return_value = mock_response

            result = await dc.activate_adaptive_immunity(threat)

            # Verify structure
            assert "activations" in result
            assert "b_cell" in result["activations"]
            assert "t_cells" in result["activations"]

            # Verify no cytotoxic activation (severity < 0.7)
            t_cells = result["activations"]["t_cells"]
            assert "cytotoxic_t" not in t_cells

            # Verify stored in activations
            assert len(dc.activations) == 1

    @pytest.mark.asyncio
    async def test_activate_adaptive_immunity_high_severity(self):
        """Testa activation com high severity (≥0.7) - inclui Cytotoxic T."""
        dc = DendriticCore()

        threat = {
            "antigen_id": "ag_high",
            "severity": 0.8,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_client.post.return_value = mock_response

            result = await dc.activate_adaptive_immunity(threat)

            # Verify Cytotoxic T activated
            t_cells = result["activations"]["t_cells"]
            assert "cytotoxic_t" in t_cells

    @pytest.mark.asyncio
    async def test_activate_adaptive_immunity_threshold_boundary(self):
        """Testa boundary de cytotoxic activation em 0.7."""
        dc = DendriticCore()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_client.post.return_value = mock_response

            # Exactly 0.7 - should activate cytotoxic
            threat_exact = {"antigen_id": "ag_exact", "severity": 0.7}
            result_exact = await dc.activate_adaptive_immunity(threat_exact)
            assert "cytotoxic_t" in result_exact["activations"]["t_cells"]

            # Below 0.7 - should NOT activate cytotoxic
            threat_below = {"antigen_id": "ag_below", "severity": 0.69}
            result_below = await dc.activate_adaptive_immunity(threat_below)
            assert "cytotoxic_t" not in result_below["activations"]["t_cells"]


# =====================================================================
# TEST STATUS & MONITORING
# =====================================================================


class TestStatusMonitoring:
    """Testa get_status - monitoring de DC."""

    @pytest.mark.asyncio
    async def test_get_status_initial_state(self):
        """Testa status inicial."""
        dc = DendriticCore()
        status = await dc.get_status()

        assert status["status"] == "operational"
        assert status["processed_antigens_count"] == 0
        assert status["activations_count"] == 0
        assert status["last_processing"] == "N/A"
        assert "kafka_enabled" in status
        assert "qdrant_enabled" in status
        assert status["antigen_consumer_running"] is False

    @pytest.mark.asyncio
    async def test_get_status_after_processing(self):
        """Testa status após processar antigens."""
        dc = DendriticCore()

        antigen = {"antigen_id": "ag_status", "severity": 0.5}
        await dc.process_antigen(antigen)

        status = await dc.get_status()

        assert status["processed_antigens_count"] == 1
        assert status["last_processing"] != "N/A"


# =====================================================================
# TEST ANTIGEN CONSUMER (Kafka integration)
# =====================================================================


class TestAntigenConsumer:
    """Testa AntigenConsumer - Kafka consumption."""

    def test_antigen_consumer_init_kafka_unavailable(self):
        """Testa init quando Kafka não disponível."""
        with patch("dendritic_core.KAFKA_AVAILABLE", False):
            consumer = AntigenConsumer()
            assert consumer.consumer is None
            assert consumer.running is False

    def test_antigen_consumer_stop(self):
        """Testa stop consumer."""
        consumer = AntigenConsumer()
        consumer.running = True
        consumer.stop()

        assert consumer.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
