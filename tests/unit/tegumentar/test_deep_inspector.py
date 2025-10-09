from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.deep_inspector import DeepPacketInspector
from backend.modules.tegumentar.derme.ml.anomaly_detector import AnomalyDetector
from backend.modules.tegumentar.derme.ml.feature_extractor import FeatureExtractor
from backend.modules.tegumentar.derme.signature_engine import Signature, SignatureEngine
from backend.modules.tegumentar.derme.stateful_inspector import FlowObservation, InspectorAction


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


def make_observation(flags: str | None = "PA") -> FlowObservation:
    return FlowObservation(
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=1111,
        dst_port=80,
        protocol="TCP",
        flags=flags,
        payload_size=600,
    )


def test_signature_engine_match(tmp_path: Path) -> None:
    signatures = tmp_path / "sigs"
    signatures.mkdir()
    sample = signatures / "demo.yaml"
    sample.write_text(
        "signatures:\n  - name: demo\n    pattern: 'demo-pattern'\n    severity: medium\n    action: block\n"
    )
    engine = SignatureEngine(TegumentarSettings(signature_directory=str(signatures)))
    signature = engine.match(b"prefix demo-pattern suffix")
    assert isinstance(signature, Signature)
    assert signature.name == "demo"


def test_feature_extractor_variations() -> None:
    extractor = FeatureExtractor()
    observation = make_observation(flags=None)
    vector = extractor.transform(observation, b"123ABC")
    assert vector.entropy >= 0
    assert vector.tcp_flag_score == 0.0


@pytest.mark.asyncio
async def test_anomaly_detector_auto_training(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    detector = AnomalyDetector(settings)
    detector.load()
    vector = FeatureExtractor().transform(make_observation(), b"sample-payload")
    score = detector.score(vector)
    assert 0.0 <= score <= 2.0


def test_deep_inspector_signature_path(monkeypatch, tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    fake_signature = Signature(name="sig", pattern=MagicMock(), severity="high", action="block")

    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
        lambda *_: MagicMock(match=MagicMock(return_value=fake_signature)),
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
        lambda *_: MagicMock(score=MagicMock(return_value=0.2)),
    )

    inspector = DeepPacketInspector(settings)
    result = inspector.inspect(make_observation(), b"payload")
    assert result.action is InspectorAction.DROP


def test_deep_inspector_anomaly_path(monkeypatch, tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
        lambda *_: MagicMock(match=MagicMock(return_value=None)),
    )
    monkeypatch.setattr(
        "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
        lambda *_: MagicMock(score=MagicMock(return_value=0.85)),
    )

    inspector = DeepPacketInspector(settings)
    result = inspector.inspect(make_observation(), b"payload")
    assert result.action is InspectorAction.INSPECT_DEEP
