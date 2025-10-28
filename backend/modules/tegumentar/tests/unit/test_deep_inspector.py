"""
Testes unitários para backend.modules.tegumentar.derme.deep_inspector

Testa o DeepPacketInspector que combina:
- Signature matching (SignatureEngine)
- ML anomaly detection (AnomalyDetector + FeatureExtractor)

Padrão Pagani: Mocks dos componentes ML/signature, validação de lógica DPI.
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.deep_inspector import (
    DeepPacketInspector,
    InspectionResult,
)
from backend.modules.tegumentar.derme.signature_engine import Signature
from backend.modules.tegumentar.derme.stateful_inspector import (
    FlowObservation,
    InspectorAction,
)


@pytest.fixture
def settings():
    """Settings de teste."""
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
    )


@pytest.fixture
def observation():
    """FlowObservation de teste."""
    return FlowObservation(
        src_ip="192.168.1.100",
        dst_ip="10.0.0.1",
        src_port=54321,
        dst_port=443,
        protocol="TCP",
        flags="SYN",
        payload_size=1024,
    )


@pytest.fixture
def mock_signature_engine():
    """Mock do SignatureEngine."""
    mock = MagicMock()
    mock.load = MagicMock()
    mock.match = MagicMock(return_value=None)
    return mock


@pytest.fixture
def mock_feature_extractor():
    """Mock do FeatureExtractor."""
    mock = MagicMock()
    mock.transform = MagicMock(return_value=[0.1, 0.2, 0.3])
    return mock


@pytest.fixture
def mock_anomaly_detector():
    """Mock do AnomalyDetector."""
    mock = MagicMock()
    mock.load = MagicMock()
    mock.score = MagicMock(return_value=0.3)
    return mock


class TestDeepPacketInspectorInitialization:
    """Testa inicialização do DeepPacketInspector."""

    def test_initializes_with_settings(self, settings):
        """Deve inicializar com settings fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine"
        ) as mock_sig_class, patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor"
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector"
        ) as mock_anom_class:
            mock_sig = MagicMock()
            mock_sig.load = MagicMock()
            mock_sig_class.return_value = mock_sig

            mock_anom = MagicMock()
            mock_anom.load = MagicMock()
            mock_anom_class.return_value = mock_anom

            inspector = DeepPacketInspector(settings)

            assert inspector._settings is settings

    def test_initializes_with_default_settings(self):
        """Deve usar get_settings() quando settings não fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.get_settings"
        ) as mock_get_settings, patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine"
        ) as mock_sig_class, patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor"
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector"
        ) as mock_anom_class:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            mock_sig = MagicMock()
            mock_sig.load = MagicMock()
            mock_sig_class.return_value = mock_sig

            mock_anom = MagicMock()
            mock_anom.load = MagicMock()
            mock_anom_class.return_value = mock_anom

            inspector = DeepPacketInspector()

            mock_get_settings.assert_called_once()
            assert inspector._settings is mock_settings

    def test_creates_signature_engine(
        self, settings, mock_feature_extractor, mock_anomaly_detector
    ):
        """Deve criar SignatureEngine e chamar load()."""
        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine"
        ) as mock_class, patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            mock_sig = MagicMock()
            mock_sig.load = MagicMock()
            mock_class.return_value = mock_sig

            inspector = DeepPacketInspector(settings)

            mock_class.assert_called_once_with(settings)
            mock_sig.load.assert_called_once()
            assert inspector._signature_engine is mock_sig

    def test_creates_feature_extractor(
        self, settings, mock_signature_engine, mock_anomaly_detector
    ):
        """Deve criar FeatureExtractor."""
        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor"
        ) as mock_class, patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            mock_fe = MagicMock()
            mock_class.return_value = mock_fe

            inspector = DeepPacketInspector(settings)

            mock_class.assert_called_once()
            assert inspector._feature_extractor is mock_fe

    def test_creates_anomaly_detector(
        self, settings, mock_signature_engine, mock_feature_extractor
    ):
        """Deve criar AnomalyDetector e chamar load()."""
        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector"
        ) as mock_class:
            mock_ad = MagicMock()
            mock_ad.load = MagicMock()
            mock_class.return_value = mock_ad

            inspector = DeepPacketInspector(settings)

            mock_class.assert_called_once_with(settings)
            mock_ad.load.assert_called_once()
            assert inspector._anomaly_detector is mock_ad


class TestInspectSignatureMatch:
    """Testa inspect() quando há match de signature."""

    def test_inspect_returns_drop_when_signature_action_block(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve retornar DROP quando signature.action == 'block'."""
        signature = Signature(
            name="SQL_INJECTION",
            pattern=b"SELECT.*FROM",
            action="block",
            severity="critical",
        )
        mock_signature_engine.match.return_value = signature

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"SELECT * FROM users")

            assert result.action == InspectorAction.DROP
            assert result.confidence == 0.99
            assert "SQL_INJECTION" in result.reason
            assert result.signature is signature

    def test_inspect_returns_inspect_deep_when_signature_action_alert(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve retornar INSPECT_DEEP quando signature.action != 'block'."""
        signature = Signature(
            name="SUSPICIOUS_PATTERN",
            pattern=b"admin",
            action="alert",
            severity="low",
        )
        mock_signature_engine.match.return_value = signature

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"admin login")

            assert result.action == InspectorAction.INSPECT_DEEP
            assert result.confidence == 0.99
            assert "SUSPICIOUS_PATTERN" in result.reason
            assert result.signature is signature

    def test_inspect_calls_signature_engine_match(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve chamar signature_engine.match() com payload."""
        payload = b"test payload"

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            inspector.inspect(observation, payload)

            mock_signature_engine.match.assert_called_once_with(payload)


class TestInspectAnomalyDetection:
    """Testa inspect() quando não há signature match mas ML detecta anomalia."""

    def test_inspect_returns_inspect_deep_when_anomaly_score_high(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve retornar INSPECT_DEEP quando anomaly score > 0.7."""
        mock_signature_engine.match.return_value = None  # No signature match
        mock_anomaly_detector.score.return_value = 0.85

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"unusual payload")

            assert result.action == InspectorAction.INSPECT_DEEP
            assert result.confidence == 0.85
            assert "Anomaly detector" in result.reason
            assert result.anomaly_score == 0.85

    def test_inspect_caps_confidence_at_99_percent(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve limitar confidence a 0.99 mesmo com score > 0.99."""
        mock_signature_engine.match.return_value = None
        mock_anomaly_detector.score.return_value = 1.0  # Perfect score

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"payload")

            assert result.confidence == 0.99  # Capped

    def test_inspect_calls_feature_extraction_and_scoring(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve chamar feature extraction e anomaly scoring."""
        mock_signature_engine.match.return_value = None
        mock_features = [0.1, 0.2, 0.3]
        mock_feature_extractor.transform.return_value = mock_features
        payload = b"test payload"

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            inspector.inspect(observation, payload)

            mock_feature_extractor.transform.assert_called_once_with(
                observation, payload
            )
            mock_anomaly_detector.score.assert_called_once_with(mock_features)


class TestInspectNormalTraffic:
    """Testa inspect() quando não há signature nem anomalia."""

    def test_inspect_returns_pass_when_no_signature_and_low_anomaly(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Deve retornar PASS quando score <= 0.7 e sem signature."""
        mock_signature_engine.match.return_value = None
        mock_anomaly_detector.score.return_value = 0.3

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"normal payload")

            assert result.action == InspectorAction.PASS
            assert result.confidence == 0.5
            assert "No signature match" in result.reason
            assert result.anomaly_score == 0.3

    def test_inspect_threshold_boundary_at_0_7(
        self,
        settings,
        observation,
        mock_signature_engine,
        mock_feature_extractor,
        mock_anomaly_detector,
    ):
        """Score exatamente 0.7 deve retornar PASS (threshold não incluído)."""
        mock_signature_engine.match.return_value = None
        mock_anomaly_detector.score.return_value = 0.7

        with patch(
            "backend.modules.tegumentar.derme.deep_inspector.SignatureEngine",
            return_value=mock_signature_engine,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.FeatureExtractor",
            return_value=mock_feature_extractor,
        ), patch(
            "backend.modules.tegumentar.derme.deep_inspector.AnomalyDetector",
            return_value=mock_anomaly_detector,
        ):
            inspector = DeepPacketInspector(settings)
            result = inspector.inspect(observation, b"boundary case")

            assert result.action == InspectorAction.PASS  # <= 0.7 = PASS
