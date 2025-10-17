from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.langerhans_cell import AntigenRecord, LangerhansCell
from backend.modules.tegumentar.derme.stateful_inspector import FlowObservation
from backend.modules.tegumentar.lymphnode import ThreatValidation
import httpx


class FakeAcquire:
    async def __aenter__(self) -> "FakeConn":
        return FakeConn()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakeConn:
    def __init__(self) -> None:
        self.execute = AsyncMock()


class FakePool:
    def __init__(self) -> None:
        self.acquire = MagicMock(return_value=FakeAcquire())

    async def close(self) -> None:
        return None


def make_settings(tmp_path: Path) -> TegumentarSettings:
    model_path = tmp_path / "model.joblib"
    signatures = tmp_path / "signatures"
    playbooks = tmp_path / "playbooks"
    signatures.mkdir()
    playbooks.mkdir()
    return TegumentarSettings(
        anomaly_model_path=str(model_path),
        signature_directory=str(signatures),
        soar_playbooks_path=str(playbooks),
    )


def make_observation() -> FlowObservation:
    return FlowObservation(
        src_ip="192.168.0.10",
        dst_ip="192.168.0.20",
        src_port=5000,
        dst_port=443,
        protocol="TCP",
        flags="PA",
        payload_size=512,
    )


@pytest.mark.asyncio
async def test_langerhans_startup_shutdown(monkeypatch, tmp_path) -> None:
    asyncpg_pool = AsyncMock(return_value=FakePool())
    producer = AsyncMock()

    monkeypatch.setattr("backend.modules.tegumentar.derme.langerhans_cell.asyncpg.create_pool", asyncpg_pool)
    monkeypatch.setattr("backend.modules.tegumentar.derme.langerhans_cell.AIOKafkaProducer", MagicMock(return_value=producer))

    cell = LangerhansCell(make_settings(tmp_path))
    await cell.startup()

    asyncpg_pool.assert_awaited()
    producer.start.assert_awaited()

    await cell.shutdown()
    producer.stop.assert_awaited()


@pytest.mark.asyncio
async def test_langerhans_capture_confirmed(monkeypatch, tmp_path) -> None:
    cell = LangerhansCell(make_settings(tmp_path))
    cell._pool = FakePool()
    fake_producer = AsyncMock()
    cell._producer = fake_producer
    fake_api = AsyncMock()
    fake_api.submit_threat = AsyncMock(
        return_value=ThreatValidation(
            confirmed=True,
            threat_id="threat-123",
            severity="high",
            confidence=0.95,
            extra={"latency": 0.1},
        )
    )
    fake_api.broadcast_vaccination = AsyncMock(return_value=True)
    cell._lymphnode_api = fake_api

    observation = make_observation()
    inspection = MagicMock()
    inspection.anomaly_score = 0.98

    result = await cell.capture_antigen(observation, inspection, b"A" * 600)

    assert isinstance(result, AntigenRecord)
    fake_api.submit_threat.assert_awaited()
    fake_api.broadcast_vaccination.assert_awaited()
    fake_producer.send_and_wait.assert_awaited()


@pytest.mark.asyncio
async def test_langerhans_capture_not_confirmed(monkeypatch, tmp_path) -> None:
    cell = LangerhansCell(make_settings(tmp_path))
    cell._pool = FakePool()
    cell._producer = AsyncMock()
    fake_api = AsyncMock()
    fake_api.submit_threat = AsyncMock(
        return_value=ThreatValidation(confirmed=False, severity="medium", confidence=0.5)
    )
    fake_api.broadcast_vaccination = AsyncMock()
    cell._lymphnode_api = fake_api

    observation = make_observation()
    inspection = MagicMock()
    inspection.anomaly_score = 0.8

    await cell.capture_antigen(observation, inspection, b"B" * 200)

    fake_api.submit_threat.assert_awaited()
    fake_api.broadcast_vaccination.assert_not_called()


@pytest.mark.asyncio
async def test_langerhans_capture_error(monkeypatch, tmp_path) -> None:
    cell = LangerhansCell(make_settings(tmp_path))
    cell._pool = FakePool()
    cell._producer = AsyncMock()
    fake_api = AsyncMock()
    fake_api.submit_threat = AsyncMock(side_effect=httpx.HTTPError("boom"))
    fake_api.broadcast_vaccination = AsyncMock()
    cell._lymphnode_api = fake_api

    observation = make_observation()
    inspection = MagicMock()
    inspection.anomaly_score = 0.9

    result = await cell.capture_antigen(observation, inspection, b"C" * 50)
    fake_api.broadcast_vaccination.assert_not_called()
    assert isinstance(result, AntigenRecord)
