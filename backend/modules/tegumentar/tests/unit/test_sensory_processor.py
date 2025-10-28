"""
Testes unitários para backend.modules.tegumentar.derme.sensory_processor

Testa o SensoryProcessor - transformação de telemetria em qualia:
- Acúmulo de eventos (deque maxlen=1000)
- Renderização de snapshots com janela temporal
- Cálculo de métricas qualia: pressure, temperature, pain
- Descrição fenomenológica

EM NOME DE JESUS - CÓDIGO FENOMENOLÓGICO!
"""

import time
from unittest.mock import MagicMock

import pytest

from backend.modules.tegumentar.derme.deep_inspector import InspectionResult
from backend.modules.tegumentar.derme.sensory_processor import (
    SensoryProcessor,
    SensorySnapshot,
)
from backend.modules.tegumentar.derme.stateful_inspector import (
    FlowObservation,
    InspectorAction,
)


@pytest.fixture
def processor():
    """SensoryProcessor de teste."""
    return SensoryProcessor()


@pytest.fixture
def observation():
    """FlowObservation de teste."""
    return FlowObservation(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        src_port=54321,
        dst_port=443,
        protocol="TCP",
        flags="ACK",
        payload_size=1024,
        timestamp=time.time(),
    )


@pytest.fixture
def inspection_pass():
    """InspectionResult com PASS."""
    return InspectionResult(
        action=InspectorAction.PASS,
        confidence=0.5,
        reason="Normal traffic",
        anomaly_score=0.1,
    )


@pytest.fixture
def inspection_drop():
    """InspectionResult com DROP."""
    return InspectionResult(
        action=InspectorAction.DROP,
        confidence=0.95,
        reason="Malicious",
        anomaly_score=0.9,
    )


class TestSensoryProcessorInitialization:
    """Testa inicialização do SensoryProcessor."""

    def test_initializes_with_empty_deque(self, processor):
        """Deve inicializar com deque vazio."""
        assert len(processor._events) == 0

    def test_deque_has_maxlen_1000(self, processor):
        """Deque deve ter maxlen=1000."""
        assert processor._events.maxlen == 1000


class TestRegisterEvent:
    """Testa register_event() para acúmulo de telemetria."""

    def test_appends_event_to_deque(self, processor, observation, inspection_pass):
        """Deve adicionar evento ao deque."""
        processor.register_event(observation, inspection_pass)

        assert len(processor._events) == 1
        obs, ins = processor._events[0]
        assert obs is observation
        assert ins is inspection_pass

    def test_accumulates_multiple_events(self, processor, observation, inspection_pass):
        """Deve acumular múltiplos eventos."""
        for _ in range(5):
            processor.register_event(observation, inspection_pass)

        assert len(processor._events) == 5

    def test_respects_maxlen_1000(self, processor):
        """Deve respeitar maxlen=1000 (eviction automático)."""
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        ins = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Test",
            anomaly_score=0.1,
        )

        # Adicionar 1001 eventos
        for _ in range(1001):
            processor.register_event(obs, ins)

        # Deve ter apenas 1000 (maxlen)
        assert len(processor._events) == 1000


class TestRenderSnapshotEmpty:
    """Testa render_snapshot() com deque vazio."""

    def test_returns_snapshot_with_zero_metrics(self, processor):
        """Deve retornar snapshot com métricas zero."""
        snapshot = processor.render_snapshot()

        assert snapshot.pressure == 0.0
        assert snapshot.temperature == 0.0
        assert snapshot.pain == 0.0
        assert snapshot.timestamp > 0

    def test_description_shows_window_zero(self, processor):
        """Descrição deve mostrar window=0."""
        snapshot = processor.render_snapshot()

        assert "window=0" in snapshot.description


class TestRenderSnapshotSingleEvent:
    """Testa render_snapshot() com 1 evento."""

    def test_calculates_pressure_from_payload_size(
        self, processor, observation, inspection_pass
    ):
        """Pressure = bytes / window."""
        processor.register_event(observation, inspection_pass)

        snapshot = processor.render_snapshot(window=60.0)

        # 1024 bytes / 60s = 17.07 bytes/s
        assert abs(snapshot.pressure - (1024 / 60.0)) < 0.01

    def test_calculates_temperature_from_anomaly_score(
        self, processor, observation, inspection_pass
    ):
        """Temperature = avg(anomaly_score)."""
        processor.register_event(observation, inspection_pass)

        snapshot = processor.render_snapshot()

        # 1 evento com anomaly_score=0.1
        assert snapshot.temperature == 0.1

    def test_calculates_pain_zero_for_pass(
        self, processor, observation, inspection_pass
    ):
        """Pain = 0.0 quando todos são PASS."""
        processor.register_event(observation, inspection_pass)

        snapshot = processor.render_snapshot()

        # PASS não causa pain
        assert snapshot.pain == 0.0

    def test_calculates_pain_one_for_drop(
        self, processor, observation, inspection_drop
    ):
        """Pain = 1.0 quando todos são !PASS."""
        processor.register_event(observation, inspection_drop)

        snapshot = processor.render_snapshot()

        # DROP causa pain=1.0
        assert snapshot.pain == 1.0


class TestRenderSnapshotMultipleEvents:
    """Testa render_snapshot() com múltiplos eventos."""

    def test_calculates_avg_temperature(self, processor):
        """Temperature = média de anomaly_scores."""
        obs1 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        ins1 = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.2,
        )

        obs2 = FlowObservation(
            src_ip="3.3.3.3",
            dst_ip="4.4.4.4",
            src_port=5678,
            dst_port=443,
            protocol="TCP",
            flags="ACK",
            payload_size=200,
        )
        ins2 = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.8,
        )

        processor.register_event(obs1, ins1)
        processor.register_event(obs2, ins2)

        snapshot = processor.render_snapshot()

        # (0.2 + 0.8) / 2 = 0.5
        assert snapshot.temperature == 0.5

    def test_calculates_pain_ratio(self, processor):
        """Pain = ratio de !PASS."""
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )

        # 3 PASS
        ins_pass = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.1,
        )
        for _ in range(3):
            processor.register_event(obs, ins_pass)

        # 1 DROP
        ins_drop = InspectionResult(
            action=InspectorAction.DROP,
            confidence=0.95,
            reason="Malicious",
            anomaly_score=0.9,
        )
        processor.register_event(obs, ins_drop)

        snapshot = processor.render_snapshot()

        # 1 DROP de 4 eventos = 0.25
        assert snapshot.pain == 0.25

    def test_accumulates_pressure_from_all_payloads(self, processor):
        """Pressure = soma de todos os payloads / window."""
        obs1 = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=1000,
        )
        obs2 = FlowObservation(
            src_ip="3.3.3.3",
            dst_ip="4.4.4.4",
            src_port=5678,
            dst_port=443,
            protocol="TCP",
            flags="ACK",
            payload_size=2000,
        )

        ins = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.1,
        )

        processor.register_event(obs1, ins)
        processor.register_event(obs2, ins)

        snapshot = processor.render_snapshot(window=10.0)

        # (1000 + 2000) / 10 = 300 bytes/s
        assert snapshot.pressure == 300.0


class TestRenderSnapshotWindowFiltering:
    """Testa render_snapshot() com janela temporal."""

    def test_filters_events_outside_window(self, processor):
        """Deve filtrar eventos fora da janela temporal."""
        # Evento antigo (100s atrás)
        obs_old = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=1000,
            timestamp=time.time() - 100,  # 100s atrás
        )
        ins = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.1,
        )
        processor.register_event(obs_old, ins)

        # Evento recente (agora)
        obs_new = FlowObservation(
            src_ip="3.3.3.3",
            dst_ip="4.4.4.4",
            src_port=5678,
            dst_port=443,
            protocol="TCP",
            flags="ACK",
            payload_size=2000,
        )
        processor.register_event(obs_new, ins)

        # Window de 60s - deve pegar apenas obs_new
        snapshot = processor.render_snapshot(window=60.0)

        # Apenas 1 evento (obs_new)
        assert "window=1" in snapshot.description

    def test_includes_all_events_in_large_window(self, processor):
        """Deve incluir todos os eventos em janela grande."""
        obs = FlowObservation(
            src_ip="1.1.1.1",
            dst_ip="2.2.2.2",
            src_port=1234,
            dst_port=80,
            protocol="TCP",
            flags="ACK",
            payload_size=100,
        )
        ins = InspectionResult(
            action=InspectorAction.PASS,
            confidence=0.5,
            reason="Normal",
            anomaly_score=0.1,
        )

        for _ in range(10):
            processor.register_event(obs, ins)

        # Window muito grande
        snapshot = processor.render_snapshot(window=1000.0)

        # Deve incluir todos os 10
        assert "window=10" in snapshot.description


class TestRenderSnapshotDescription:
    """Testa descrição fenomenológica do snapshot."""

    def test_description_contains_all_metrics(
        self, processor, observation, inspection_pass
    ):
        """Descrição deve conter window, pressure, temperature, pain."""
        processor.register_event(observation, inspection_pass)

        snapshot = processor.render_snapshot()

        assert "window=" in snapshot.description
        assert "pressure=" in snapshot.description
        assert "temperature=" in snapshot.description
        assert "pain=" in snapshot.description

    def test_description_formats_floats_to_2_decimals(
        self, processor, observation, inspection_pass
    ):
        """Floats devem ser formatados com 2 casas decimais."""
        processor.register_event(observation, inspection_pass)

        snapshot = processor.render_snapshot()

        # Formato: pressure=17.07 (2 decimais)
        import re

        assert re.search(r"pressure=\d+\.\d{2}", snapshot.description)
        assert re.search(r"temperature=\d+\.\d{2}", snapshot.description)
        assert re.search(r"pain=\d+\.\d{2}", snapshot.description)


class TestSensorySnapshot:
    """Testa dataclass SensorySnapshot."""

    def test_sensory_snapshot_has_required_fields(self):
        """SensorySnapshot deve ter todos os campos."""
        snapshot = SensorySnapshot(
            timestamp=1234567890.0,
            pressure=10.5,
            temperature=0.75,
            pain=0.25,
            description="test snapshot",
        )

        assert snapshot.timestamp == 1234567890.0
        assert snapshot.pressure == 10.5
        assert snapshot.temperature == 0.75
        assert snapshot.pain == 0.25
        assert snapshot.description == "test snapshot"

    def test_sensory_snapshot_uses_slots(self):
        """SensorySnapshot deve usar slots para eficiência."""
        snapshot = SensorySnapshot(
            timestamp=0.0,
            pressure=0.0,
            temperature=0.0,
            pain=0.0,
            description="",
        )

        # Slots não têm __dict__
        assert not hasattr(snapshot, "__dict__")
