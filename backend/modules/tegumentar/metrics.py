"""Coleta de métricas Prometheus para o módulo Tegumentar."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

REFLEX_EVENTS_TOTAL = Counter(
    "tegumentar_reflex_events_total",
    "Eventos de arco reflexo disparados pela epiderme",
    labelnames=("signature_id",),
)

ANTIGENS_CAPTURED_TOTAL = Counter(
    "tegumentar_antigens_captured_total",
    "Antígenos capturados pela camada derme",
    labelnames=("protocol",),
)

LYMPHNODE_VALIDATIONS_TOTAL = Counter(
    "tegumentar_lymphnode_validations_total",
    "Interações de validação com o Linfonodo",
    labelnames=("result", "severity"),
)

LYMPHNODE_LATENCY_SECONDS = Histogram(
    "tegumentar_lymphnode_latency_seconds",
    "Latência das chamadas ao Linfonodo",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
)

LYMPHNODE_VACCINATIONS_TOTAL = Counter(
    "tegumentar_vaccinations_total",
    "Vacinações disparadas para o Linfonodo",
    labelnames=("result",),
)

def record_reflex_event(signature_id: str) -> None:
    REFLEX_EVENTS_TOTAL.labels(signature_id=signature_id).inc()


def record_antigen_capture(protocol: str) -> None:
    ANTIGENS_CAPTURED_TOTAL.labels(protocol=protocol.lower()).inc()


def record_lymphnode_validation(result: str, severity: str, latency: float) -> None:
    LYMPHNODE_VALIDATIONS_TOTAL.labels(result=result, severity=severity).inc()
    LYMPHNODE_LATENCY_SECONDS.observe(latency)


def record_vaccination(result: str) -> None:
    LYMPHNODE_VACCINATIONS_TOTAL.labels(result=result).inc()


__all__ = [
    "record_reflex_event",
    "record_antigen_capture",
    "record_lymphnode_validation",
    "record_vaccination",
    "REFLEX_EVENTS_TOTAL",
    "ANTIGENS_CAPTURED_TOTAL",
    "LYMPHNODE_VALIDATIONS_TOTAL",
    "LYMPHNODE_LATENCY_SECONDS",
    "LYMPHNODE_VACCINATIONS_TOTAL",
]
