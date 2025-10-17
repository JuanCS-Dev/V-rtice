from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if "bcc" not in sys.modules:
    sys.modules["bcc"] = SimpleNamespace(BPF=SimpleNamespace)

from backend.modules.tegumentar.orchestrator import TegumentarModule


class FakeLayer:
    def __init__(self) -> None:
        self.startup = AsyncMock()
        self.shutdown = AsyncMock()
        self.stateless_filter = SimpleNamespace()


class FakePermeability:
    async def shutdown(self) -> None:
        return None


class FakeWoundHealing:
    async def shutdown(self) -> None:
        return None


@pytest.mark.asyncio
async def test_orchestrator_startup_shutdown(monkeypatch) -> None:
    epiderme = FakeLayer()
    derme = FakeLayer()
    monkeypatch.setattr(
        "backend.modules.tegumentar.orchestrator.EpidermeLayer",
        lambda *_: epiderme,
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.orchestrator.DermeLayer",
        lambda *_: derme,
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.orchestrator.PermeabilityController",
        lambda *_: FakePermeability(),
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.orchestrator.WoundHealingOrchestrator",
        lambda *_: FakeWoundHealing(),
    )

    module = TegumentarModule()
    await module.startup("eth0")
    epiderme.startup.assert_awaited()
    derme.startup.assert_awaited()

    await module.shutdown()
    epiderme.shutdown.assert_awaited()
    derme.shutdown.assert_awaited()
