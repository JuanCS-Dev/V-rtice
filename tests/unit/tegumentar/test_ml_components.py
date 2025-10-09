from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.ml.anomaly_detector import AnomalyDetector
from backend.modules.tegumentar.derme.signature_engine import SignatureEngine
from backend.modules.tegumentar.derme.ml.feature_extractor import FeatureExtractor
from backend.modules.tegumentar.derme.stateful_inspector import FlowObservation


def test_feature_extractor_produces_expected_vector() -> None:
    extractor = FeatureExtractor()
    observation = FlowObservation(
        src_ip="10.0.0.1",
        dst_ip="10.0.0.2",
        src_port=12345,
        dst_port=443,
        protocol="TCP",
        flags="PA",
        payload_size=512,
    )
    payload = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"
    vector = extractor.transform(observation, payload)
    assert vector.payload_length == len(payload)
    assert 0.0 <= vector.entropy <= 8.0
    assert 0.0 <= vector.printable_ratio <= 1.0
    assert vector.tcp_flag_score > 0.0


def test_anomaly_detector_trains_baseline(tmp_path: Path) -> None:
    resources = Path(__file__).resolve().parents[3] / "backend" / "modules" / "tegumentar" / "resources"
    model_dir = tmp_path / "ml"
    model_dir.mkdir(parents=True, exist_ok=True)
    dataset_src = resources / "ml" / "baseline_dataset.csv"
    dataset_dst = model_dir / "baseline_dataset.csv"
    shutil.copy(str(dataset_src), str(dataset_dst))

    settings = TegumentarSettings(
        anomaly_model_path=str(model_dir / "anomaly_detector.joblib"),
        signature_directory=str(resources / "signatures"),
        soar_playbooks_path=str(resources / "playbooks"),
        reputation_cache_path=str(resources / "cache" / "blocked_ips.txt"),
    )

    detector = AnomalyDetector(settings)
    detector.load()  # triggers training with copied dataset

    observation = FlowObservation(
        src_ip="192.168.0.10",
        dst_ip="192.168.0.20",
        src_port=5555,
        dst_port=443,
        protocol="TCP",
        flags="PA",
        payload_size=1024,
    )
    extractor = FeatureExtractor()
    vector = extractor.transform(observation, b"A" * 1024)
    score = detector.score(vector)
    assert 0.0 <= score <= 2.0


def test_signature_engine_matches_patterns() -> None:
    settings = TegumentarSettings()
    engine = SignatureEngine(settings)
    engine.load()
    signature = engine.match(b"GET /index.php?id=1 UNION SELECT password FROM users")
    assert signature is not None
    assert signature.name == "sql_injection_union_select"
