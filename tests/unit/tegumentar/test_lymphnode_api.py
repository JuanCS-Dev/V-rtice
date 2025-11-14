from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest
import respx

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.lymphnode import LymphnodeAPI


@pytest.mark.asyncio
@respx.mock
async def test_submit_threat_success() -> None:
    settings = TegumentarSettings(
        lymphnode_endpoint="http://linfonodo.local",
        lymphnode_api_key="token-123",
    )
    api = LymphnodeAPI(settings)

    route = respx.post("http://linfonodo.local/threat_alert").respond(
        200,
        json={"immunis_response": {"status": "queued"}}
    )

    validation = await api.submit_threat(
        {
            "threat_id": "antigen-1",
            "threat_type": "tcp",
            "anomaly_score": 0.95,
            "source": "tegumentar-test",
        }
    )

    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer token-123"
    assert validation.confirmed is True
    assert validation.severity == "high"
    assert validation.threat_id == "antigen-1"


@pytest.mark.asyncio
@respx.mock
async def test_submit_threat_failure_raises() -> None:
    settings = TegumentarSettings(lymphnode_endpoint="http://linfonodo.local")
    api = LymphnodeAPI(settings)

    respx.post("http://linfonodo.local/threat_alert").respond(500, json={"error": "fail"})

    with pytest.raises(httpx.HTTPStatusError):
        await api.submit_threat({"threat_id": "fail", "threat_type": "udp"})


@pytest.mark.asyncio
@respx.mock
async def test_broadcast_vaccination_success() -> None:
    settings = TegumentarSettings(lymphnode_endpoint="http://linfonodo.local")
    api = LymphnodeAPI(settings)

    route = respx.post("http://linfonodo.local/trigger_immune_response").respond(
        200,
        json={"status": "ok"}
    )

    result = await api.broadcast_vaccination({"id": "rule-123"})

    assert route.called
    assert result is True


@pytest.mark.asyncio
@respx.mock
async def test_broadcast_vaccination_failure_raises() -> None:
    settings = TegumentarSettings(lymphnode_endpoint="http://linfonodo.local")
    api = LymphnodeAPI(settings)

    respx.post("http://linfonodo.local/trigger_immune_response").respond(503, json={"error": "busy"})

    with pytest.raises(httpx.HTTPStatusError):
        await api.broadcast_vaccination({"id": "rule-err"})
