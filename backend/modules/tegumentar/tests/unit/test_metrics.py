"""
Testes unitários para backend.modules.tegumentar.metrics

Testa funções de registro de métricas Prometheus:
- record_reflex_event()
- record_antigen_capture()
- record_lymphnode_validation()
- record_vaccination()

Padrão Pagani: Cobertura 100%, validação de labels e valores.
"""

from unittest.mock import MagicMock, patch

import pytest

from backend.modules.tegumentar.metrics import (
    ANTIGENS_CAPTURED_TOTAL,
    LYMPHNODE_LATENCY_SECONDS,
    LYMPHNODE_VACCINATIONS_TOTAL,
    LYMPHNODE_VALIDATIONS_TOTAL,
    record_antigen_capture,
    record_lymphnode_validation,
    record_reflex_event,
    record_vaccination,
    REFLEX_EVENTS_TOTAL,
)


class TestRecordReflexEvent:
    """Testa record_reflex_event()."""

    def test_increments_reflex_counter(self):
        """Deve incrementar contador com signature_id."""
        with patch.object(REFLEX_EVENTS_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_reflex_event("SQL_INJECTION")

            mock_labels.assert_called_once_with(signature_id="SQL_INJECTION")
            mock_counter.inc.assert_called_once()

    def test_accepts_different_signature_ids(self):
        """Deve aceitar diferentes signature_ids."""
        with patch.object(REFLEX_EVENTS_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_reflex_event("XSS_ATTACK")

            mock_labels.assert_called_once_with(signature_id="XSS_ATTACK")


class TestRecordAntigenCapture:
    """Testa record_antigen_capture()."""

    def test_increments_antigen_counter(self):
        """Deve incrementar contador com protocol."""
        with patch.object(ANTIGENS_CAPTURED_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_antigen_capture("TCP")

            mock_labels.assert_called_once_with(protocol="tcp")  # lowercase
            mock_counter.inc.assert_called_once()

    def test_converts_protocol_to_lowercase(self):
        """Deve converter protocol para lowercase."""
        with patch.object(ANTIGENS_CAPTURED_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_antigen_capture("HTTP")

            mock_labels.assert_called_once_with(protocol="http")


class TestRecordLymphnodeValidation:
    """Testa record_lymphnode_validation()."""

    def test_increments_validation_counter(self):
        """Deve incrementar contador com result e severity."""
        with patch.object(
            LYMPHNODE_VALIDATIONS_TOTAL, "labels"
        ) as mock_labels, patch.object(
            LYMPHNODE_LATENCY_SECONDS, "observe"
        ) as mock_observe:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_lymphnode_validation("success", "critical", 0.123)

            mock_labels.assert_called_once_with(result="success", severity="critical")
            mock_counter.inc.assert_called_once()

    def test_observes_latency(self):
        """Deve registrar latência no histogram."""
        with patch.object(
            LYMPHNODE_VALIDATIONS_TOTAL, "labels"
        ) as mock_labels, patch.object(
            LYMPHNODE_LATENCY_SECONDS, "observe"
        ) as mock_observe:
            mock_labels.return_value = MagicMock()

            record_lymphnode_validation("success", "low", 0.456)

            mock_observe.assert_called_once_with(0.456)

    def test_accepts_different_results(self):
        """Deve aceitar diferentes result values."""
        with patch.object(
            LYMPHNODE_VALIDATIONS_TOTAL, "labels"
        ) as mock_labels, patch.object(LYMPHNODE_LATENCY_SECONDS, "observe"):
            mock_labels.return_value = MagicMock()

            record_lymphnode_validation("error", "high", 1.234)

            mock_labels.assert_called_once_with(result="error", severity="high")


class TestRecordVaccination:
    """Testa record_vaccination()."""

    def test_increments_vaccination_counter(self):
        """Deve incrementar contador com result."""
        with patch.object(LYMPHNODE_VACCINATIONS_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_vaccination("success")

            mock_labels.assert_called_once_with(result="success")
            mock_counter.inc.assert_called_once()

    def test_accepts_failure_result(self):
        """Deve aceitar result='failure'."""
        with patch.object(LYMPHNODE_VACCINATIONS_TOTAL, "labels") as mock_labels:
            mock_counter = MagicMock()
            mock_labels.return_value = mock_counter

            record_vaccination("failure")

            mock_labels.assert_called_once_with(result="failure")
            mock_counter.inc.assert_called_once()


class TestPrometheusMetrics:
    """Testa definição das métricas Prometheus."""

    def test_reflex_events_total_has_correct_labels(self):
        """REFLEX_EVENTS_TOTAL deve ter labelnames correto."""
        assert REFLEX_EVENTS_TOTAL._labelnames == ("signature_id",)

    def test_antigens_captured_total_has_correct_labels(self):
        """ANTIGENS_CAPTURED_TOTAL deve ter labelnames correto."""
        assert ANTIGENS_CAPTURED_TOTAL._labelnames == ("protocol",)

    def test_lymphnode_validations_total_has_correct_labels(self):
        """LYMPHNODE_VALIDATIONS_TOTAL deve ter labelnames correto."""
        assert LYMPHNODE_VALIDATIONS_TOTAL._labelnames == ("result", "severity")

    def test_lymphnode_latency_has_buckets(self):
        """LYMPHNODE_LATENCY_SECONDS deve ter buckets configurados."""
        # Histogram tem atributo _buckets
        assert hasattr(LYMPHNODE_LATENCY_SECONDS, "_buckets")
        # Verifica que tem pelo menos alguns buckets
        assert len(LYMPHNODE_LATENCY_SECONDS._buckets) > 1

    def test_vaccinations_total_has_correct_labels(self):
        """LYMPHNODE_VACCINATIONS_TOTAL deve ter labelnames correto."""
        assert LYMPHNODE_VACCINATIONS_TOTAL._labelnames == ("result",)
