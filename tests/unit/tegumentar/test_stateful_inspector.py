from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.stateful_inspector import (
    FlowObservation,
    InspectorAction,
    StatefulInspector,
)


def make_settings() -> TegumentarSettings:
    return TegumentarSettings()


def make_observation(flags: str = "S", payload_size: int = 128) -> FlowObservation:
    return FlowObservation(
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=1000,
        dst_port=80,
        protocol="TCP",
        flags=flags,
        payload_size=payload_size,
    )


@pytest.mark.asyncio
async def test_stateful_inspector_syn_drop() -> None:
    inspector = StatefulInspector(make_settings())
    inspector._persist_state = AsyncMock()
    inspector._evict_idle_connections = AsyncMock()

    observation = make_observation()
    decision = None
    for _ in range(12):
        decision = await inspector.process(observation)

    assert decision is not None
    assert decision.action is InspectorAction.DROP


@pytest.mark.asyncio
async def test_stateful_inspector_high_throughput() -> None:
    inspector = StatefulInspector(make_settings())
    inspector._persist_state = AsyncMock()
    inspector._evict_idle_connections = AsyncMock()

    observation = make_observation(flags="PA", payload_size=11_000_000)
    decision = await inspector.process(observation)

    assert decision.action is InspectorAction.INSPECT_DEEP


class FakeConn:
    async def execute(self, *args, **kwargs) -> None:
        self.executed = True


class FakeAcquire:
    async def __aenter__(self) -> FakeConn:
        self.conn = FakeConn()
        return self.conn

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakePool:
    def __init__(self) -> None:
        self.acquire = MagicMock(return_value=FakeAcquire())

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_stateful_inspector_startup_and_persist(monkeypatch) -> None:
    fake_pool = FakePool()

    async def create_pool(*args, **kwargs):  # noqa: ANN001
        return fake_pool

    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.stateful_inspector.asyncpg.create_pool",
        create_pool,
    )

    inspector = StatefulInspector(make_settings())
    await inspector.startup()

    observation = make_observation(flags="PA", payload_size=1024)
    inspector._evict_idle_connections = AsyncMock()
    decision = await inspector.process(observation)

    assert decision.action is InspectorAction.PASS
    fake_pool.acquire.assert_called()
