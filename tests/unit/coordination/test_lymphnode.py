import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CORE_ROOT = ROOT / "backend" / "services" / "active_immune_core"
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))

import pytest

from backend.services.active_immune_core.coordination.cytokine_aggregator import (
    ProcessingResult,
)
from backend.services.active_immune_core.coordination.lymphnode import LinfonodoDigital
from coordination.exceptions import LymphnodeConnectionError


class _DummyAgentFactory:
    async def create_agent(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("Agent creation should not be exercised in this test")


class _DummyAggregator:
    def __init__(self) -> None:
        self.next_validated: Optional[Dict[str, Any]] = None
        self.process_calls: list[Dict[str, Any]] = []
        self.should_process_for_area_calls: list[Dict[str, Any]] = []

    async def validate_and_parse(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.next_validated

    async def should_process_for_area(self, cytokine: Dict[str, Any]) -> bool:
        self.should_process_for_area_calls.append(cytokine)
        return cytokine.get("process", True)

    async def process_cytokine(self, cytokine: Dict[str, Any]) -> ProcessingResult:
        self.process_calls.append(cytokine)
        return ProcessingResult(metadata={"tipo": cytokine.get("tipo", "IL1")})


@pytest.fixture
def lymphnode() -> LinfonodoDigital:
    node = LinfonodoDigital(
        lymphnode_id="lymph-test",
        nivel="local",
        area_responsabilidade="zone-1",
        agent_factory=_DummyAgentFactory(),
        shared_secret="test-secret",
    )
    node._cytokine_aggregator = _DummyAggregator()  # type: ignore[assignment]
    return node


@pytest.mark.asyncio
async def test_handle_cytokine_message_processes_matching_area(lymphnode: LinfonodoDigital) -> None:
    aggregator: _DummyAggregator = lymphnode._cytokine_aggregator  # type: ignore[assignment]
    aggregator.next_validated = {
        "tipo": "IL6",
        "area_alvo": "zone-1",
        "payload": {},
    }

    processed = await lymphnode._handle_cytokine_message({"raw": "payload"})

    assert processed is True
    assert aggregator.process_calls  # ensures regional processing executed
    assert await lymphnode.cytokine_buffer.size() == 1


@pytest.mark.asyncio
async def test_handle_cytokine_message_skips_invalid_payload(lymphnode: LinfonodoDigital) -> None:
    aggregator: _DummyAggregator = lymphnode._cytokine_aggregator  # type: ignore[assignment]
    aggregator.next_validated = None

    processed = await lymphnode._handle_cytokine_message({"raw": "payload"})

    assert processed is False
    assert aggregator.should_process_for_area_calls == []
    assert await lymphnode.cytokine_buffer.size() == 0


def test_validate_token_success(lymphnode: LinfonodoDigital) -> None:
    lymphnode.validate_token("test-secret")
    assert lymphnode.is_quarantined() is False


def test_validate_token_failure_registers(lymphnode: LinfonodoDigital) -> None:
    with pytest.raises(LymphnodeConnectionError):
        lymphnode.validate_token(None)
    assert len(lymphnode._failure_timestamps) == 1


def test_validate_token_invalid_secret(lymphnode: LinfonodoDigital) -> None:
    with pytest.raises(LymphnodeConnectionError):
        lymphnode.validate_token("invalid")
    assert len(lymphnode._failure_timestamps) == 1
