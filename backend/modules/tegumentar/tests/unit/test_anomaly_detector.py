"""
Testes unitários para backend.modules.tegumentar.derme.ml.anomaly_detector

Testa o AnomalyDetector - Isolation Forest para detecção de zero-days:
- __init__: settings, _model None
- load(): joblib.load, auto-train quando missing, TypeError validation
- score(): lazy load, decision_function, conversão (1.0 - score)
- _train_default_model(): CSV parsing, IsolationForest fit, FileNotFoundError

Padrão Pagani: ML model loading/training 100%, scikit-learn mocking.

EM NOME DE JESUS - ML DETECTOR PERFEITO!
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from sklearn.ensemble import IsolationForest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.derme.ml.anomaly_detector import AnomalyDetector
from backend.modules.tegumentar.derme.ml.feature_extractor import FeatureVector


@pytest.fixture
def settings(tmp_path):
    """Settings de teste com diretório temporário."""
    model_path = tmp_path / "anomaly_model.pkl"
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
        anomaly_model_path=str(model_path),
    )


@pytest.fixture
def detector(settings):
    """AnomalyDetector de teste."""
    return AnomalyDetector(settings)


@pytest.fixture
def feature_vector():
    """FeatureVector de teste."""
    return FeatureVector(
        payload_length=100,
        entropy=4.5,
        printable_ratio=0.8,
        digit_ratio=0.2,
        average_byte_value=65.3,
        tcp_flag_score=1.0,
        inter_packet_interval=0.05,
    )


@pytest.fixture
def mock_isolation_forest():
    """Mock do IsolationForest."""
    mock = MagicMock(spec=IsolationForest)
    mock.decision_function = MagicMock(return_value=[0.5])
    mock.fit = MagicMock()
    return mock


class TestAnomalyDetectorInitialization:
    """Testa inicialização do AnomalyDetector."""

    def test_initializes_with_settings(self, settings):
        """Deve armazenar settings fornecido."""
        detector = AnomalyDetector(settings)

        assert detector._settings is settings

    def test_initializes_with_default_settings(self):
        """Deve usar get_settings() quando não fornecido."""
        with patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            detector = AnomalyDetector()

            mock_get_settings.assert_called_once()
            assert detector._settings is mock_settings

    def test_initializes_model_as_none(self, detector):
        """Deve inicializar _model como None."""
        assert detector._model is None


class TestLoad:
    """Testa método load() para carregar modelo."""

    def test_loads_model_from_path(self, detector, settings, mock_isolation_forest):
        """Deve carregar modelo usando joblib.load()."""
        # Criar arquivo fake
        model_path = Path(settings.anomaly_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        with patch("joblib.load", return_value=mock_isolation_forest):
            detector.load()

            assert detector._model is mock_isolation_forest

    def test_raises_type_error_when_model_not_isolation_forest(
        self, detector, settings
    ):
        """Deve levantar TypeError quando modelo não é IsolationForest."""
        # Criar arquivo fake
        model_path = Path(settings.anomaly_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        # Mock retornando tipo errado
        wrong_model = MagicMock(spec=object)

        with patch("joblib.load", return_value=wrong_model), pytest.raises(
            TypeError
        ) as exc_info:
            detector.load()

        assert "not an IsolationForest instance" in str(exc_info.value)

    def test_trains_default_model_when_missing(self, detector, settings):
        """Deve treinar modelo baseline quando arquivo não existe."""
        # Model path não existe
        model_path = Path(settings.anomaly_model_path)
        assert not model_path.exists()

        mock_model = MagicMock(spec=IsolationForest)

        with patch.object(detector, "_train_default_model") as mock_train, patch(
            "joblib.load", return_value=mock_model
        ):
            detector.load()

            # Deve ter chamado _train_default_model
            mock_train.assert_called_once_with(model_path)

    def test_sets_model_after_load(self, detector, settings, mock_isolation_forest):
        """Deve armazenar modelo em _model após load()."""
        model_path = Path(settings.anomaly_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        with patch("joblib.load", return_value=mock_isolation_forest):
            detector.load()

            assert detector._model is mock_isolation_forest


class TestScore:
    """Testa método score() para scoring de anomalias."""

    def test_lazy_loads_model_when_none(
        self, detector, settings, mock_isolation_forest
    ):
        """Deve chamar load() quando _model é None."""
        model_path = Path(settings.anomaly_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        feature = FeatureVector(
            payload_length=100,
            entropy=4.5,
            printable_ratio=0.8,
            digit_ratio=0.2,
            average_byte_value=65.3,
            tcp_flag_score=1.0,
            inter_packet_interval=0.05,
        )

        with patch("joblib.load", return_value=mock_isolation_forest):
            detector.score(feature)

            # Deve ter carregado
            assert detector._model is not None

    def test_calls_decision_function_with_feature_list(
        self, detector, feature_vector, mock_isolation_forest
    ):
        """Deve chamar decision_function() com feature.as_list()."""
        detector._model = mock_isolation_forest

        detector.score(feature_vector)

        # Deve ter chamado com lista de features
        mock_isolation_forest.decision_function.assert_called_once()
        call_args = mock_isolation_forest.decision_function.call_args[0][0]

        # Deve ser lista de listas [[features]]
        assert isinstance(call_args, list)
        assert len(call_args) == 1
        assert call_args[0] == feature_vector.as_list()

    def test_converts_score_to_anomaly_score(
        self, detector, feature_vector, mock_isolation_forest
    ):
        """Deve converter decision_function score para anomaly score (1.0 - score)."""
        # decision_function retorna [0.3] (normal)
        mock_isolation_forest.decision_function.return_value = [0.3]
        detector._model = mock_isolation_forest

        result = detector.score(feature_vector)

        # Anomaly score = 1.0 - 0.3 = 0.7
        assert result == 0.7

    def test_returns_high_anomaly_score_for_anomalous_data(
        self, detector, feature_vector, mock_isolation_forest
    ):
        """Score baixo (anômalo) deve retornar anomaly score alto."""
        # decision_function retorna [-0.5] (anômalo)
        mock_isolation_forest.decision_function.return_value = [-0.5]
        detector._model = mock_isolation_forest

        result = detector.score(feature_vector)

        # Anomaly score = 1.0 - (-0.5) = 1.5
        assert result == 1.5

    def test_returns_low_anomaly_score_for_normal_data(
        self, detector, feature_vector, mock_isolation_forest
    ):
        """Score alto (normal) deve retornar anomaly score baixo."""
        # decision_function retorna [0.8] (muito normal)
        mock_isolation_forest.decision_function.return_value = [0.8]
        detector._model = mock_isolation_forest

        result = detector.score(feature_vector)

        # Anomaly score = 1.0 - 0.8 = 0.2 (float precision)
        assert abs(result - 0.2) < 0.001


class TestTrainDefaultModel:
    """Testa método _train_default_model() para treinar baseline."""

    def test_raises_file_not_found_when_dataset_missing(self, detector, settings):
        """Deve levantar FileNotFoundError quando dataset não existe."""
        output_path = Path(settings.anomaly_model_path)

        # Mock dataset path não existe
        with patch("pathlib.Path.exists", return_value=False), pytest.raises(
            FileNotFoundError
        ) as exc_info:
            detector._train_default_model(output_path)

        assert "Baseline dataset not found" in str(exc_info.value)

    def test_raises_value_error_when_dataset_empty(self, detector, settings):
        """Deve levantar ValueError quando dataset está vazio."""
        output_path = Path(settings.anomaly_model_path)

        # Mock CSV vazio (apenas header)
        csv_content = "payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval\n"

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), pytest.raises(ValueError) as exc_info:
            detector._train_default_model(output_path)

        assert "Baseline dataset is empty" in str(exc_info.value)

    def test_trains_isolation_forest_with_correct_params(self, detector, settings):
        """Deve treinar IsolationForest com parâmetros corretos."""
        output_path = Path(settings.anomaly_model_path)

        csv_content = """payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval
100,4.5,0.8,0.2,65.3,1.0,0.05
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.IsolationForest"
        ) as mock_if_class, patch(
            "joblib.dump"
        ), patch(
            "pathlib.Path.mkdir"
        ):
            mock_model = MagicMock()
            mock_if_class.return_value = mock_model

            detector._train_default_model(output_path)

            # Verificar parâmetros
            mock_if_class.assert_called_once_with(
                n_estimators=200,
                contamination=0.02,
                max_features=1.0,
                random_state=42,
            )

    def test_calls_fit_on_model(self, detector, settings):
        """Deve chamar fit() no modelo."""
        output_path = Path(settings.anomaly_model_path)

        csv_content = """payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval
100,4.5,0.8,0.2,65.3,1.0,0.05
200,5.2,0.9,0.1,70.1,0.5,0.1
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.IsolationForest"
        ) as mock_if_class, patch(
            "joblib.dump"
        ), patch(
            "pathlib.Path.mkdir"
        ):
            mock_model = MagicMock()
            mock_if_class.return_value = mock_model

            detector._train_default_model(output_path)

            # Deve ter chamado fit() com 2 samples
            mock_model.fit.assert_called_once()
            call_args = mock_model.fit.call_args[0][0]
            assert len(call_args) == 2  # 2 samples

    def test_saves_model_with_joblib_dump(self, detector, settings):
        """Deve salvar modelo usando joblib.dump()."""
        output_path = Path(settings.anomaly_model_path)

        csv_content = """payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval
100,4.5,0.8,0.2,65.3,1.0,0.05
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.IsolationForest"
        ) as mock_if_class, patch(
            "joblib.dump"
        ) as mock_dump, patch(
            "pathlib.Path.mkdir"
        ):
            mock_model = MagicMock()
            mock_if_class.return_value = mock_model

            detector._train_default_model(output_path)

            # Deve ter chamado joblib.dump com modelo e path
            assert mock_dump.called
            call_args = mock_dump.call_args[0]
            assert call_args[1] == output_path

    def test_creates_output_directory(self, detector, settings):
        """Deve criar diretório de saída se não existir."""
        output_path = Path(settings.anomaly_model_path)

        csv_content = """payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval
100,4.5,0.8,0.2,65.3,1.0,0.05
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.IsolationForest"
        ), patch(
            "joblib.dump"
        ), patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            detector._train_default_model(output_path)

            # Deve ter chamado mkdir
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_parses_all_csv_columns(self, detector, settings):
        """Deve parsear todas as 7 colunas do CSV."""
        output_path = Path(settings.anomaly_model_path)

        csv_content = """payload_length,entropy,printable_ratio,digit_ratio,average_byte_value,tcp_flag_score,inter_packet_interval
123,4.56,0.78,0.12,67.89,1.5,0.23
"""

        with patch("pathlib.Path.exists", return_value=True), patch(
            "pathlib.Path.open", mock_open(read_data=csv_content)
        ), patch(
            "backend.modules.tegumentar.derme.ml.anomaly_detector.IsolationForest"
        ) as mock_if_class, patch(
            "joblib.dump"
        ), patch(
            "pathlib.Path.mkdir"
        ):
            mock_model = MagicMock()
            mock_if_class.return_value = mock_model

            detector._train_default_model(output_path)

            # Verificar features passadas para fit()
            call_args = mock_model.fit.call_args[0][0]
            assert len(call_args) == 1  # 1 sample
            assert len(call_args[0]) == 7  # 7 features
            assert call_args[0] == [123.0, 4.56, 0.78, 0.12, 67.89, 1.5, 0.23]


class TestIntegration:
    """Testes de integração do AnomalyDetector."""

    def test_full_workflow_load_and_score(self, detector, settings, feature_vector):
        """Deve carregar modelo e fazer scoring."""
        model_path = Path(settings.anomaly_model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.touch()

        mock_model = MagicMock(spec=IsolationForest)
        mock_model.decision_function.return_value = [0.6]

        with patch("joblib.load", return_value=mock_model):
            detector.load()
            result = detector.score(feature_vector)

            # 1.0 - 0.6 = 0.4
            assert result == 0.4
