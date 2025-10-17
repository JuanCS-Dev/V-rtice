from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.derme.manager import DermeLayer
from backend.modules.tegumentar.derme.deep_inspector import InspectionResult
from backend.modules.tegumentar.derme.stateful_inspector import (
    ConnectionState,
    FlowObservation,
    InspectorAction,
    InspectorDecision,
)
from backend.modules.tegumentar.derme.sensory_processor import SensoryProcessor


def make_observation(protocol: str = "TCP") -> FlowObservation:
    return FlowObservation(
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=1234,
        dst_port=80,
        protocol=protocol,
        flags="PA",
        payload_size=512,
    )


def test_sensory_processor_snapshot() -> None:
    processor = SensoryProcessor()
    observation = make_observation()
    result = InspectionResult(
        action=InspectorAction.PASS,
        confidence=0.5,
        reason="pass",
    )
    processor.register_event(observation, result)
    snapshot = processor.render_snapshot()
    assert snapshot.pressure > 0
    assert 0.0 <= snapshot.temperature <= 1.0
    assert 0.0 <= snapshot.pain <= 1.0


@pytest.mark.asyncio
async def test_derme_process_pass_path(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.DeepPacketInspector", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.StatefulInspector", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.LangerhansCell", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.SensoryProcessor", MagicMock()
    )
    layer = DermeLayer()
    layer._stateful = AsyncMock()
    layer._sensory = MagicMock()
    layer._langerhans = AsyncMock()

    observation = make_observation()
    decision = InspectorDecision(
        action=InspectorAction.PASS,
        reason="pass",
        connection_state=ConnectionState(),
    )
    layer._stateful.process.return_value = decision

    result = await layer.process_packet(observation, b"payload")

    assert result.action is InspectorAction.PASS
    layer._stateful.process.assert_awaited()
    layer._sensory.register_event.assert_called()
    layer._langerhans.capture_antigen.assert_not_called()


@pytest.mark.asyncio
async def test_derme_process_deep_inspection(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.DeepPacketInspector", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.StatefulInspector", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.LangerhansCell", MagicMock()
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.manager.SensoryProcessor", MagicMock()
    )
    layer = DermeLayer()
    layer._stateful = AsyncMock()
    layer._sensory = MagicMock()
    layer._langerhans = AsyncMock()
    layer._dpi = MagicMock()

    observation = make_observation()
    decision = InspectorDecision(
        action=InspectorAction.INSPECT_DEEP,
        reason="inspect",
        connection_state=ConnectionState(),
    )
    layer._stateful.process.return_value = decision
    dpi_result = InspectionResult(
        action=InspectorAction.INSPECT_DEEP,
        confidence=0.9,
        reason="anomaly",
        anomaly_score=0.92,
    )
    layer._dpi.inspect.return_value = dpi_result

    result = await layer.process_packet(observation, b"payload")

    assert result is dpi_result
    layer._langerhans.capture_antigen.assert_awaited_once()
