"""
Testes unitários para backend.modules.tegumentar.lymphnode.api

Testa o LymphnodeAPI - cliente HTTP para Immunis (Sistema Imune Adaptativo):
- submit_threat(): Validação de ameaças com o Linfonodo
- broadcast_vaccination(): Disseminação de novas assinaturas (B-Cell)
- _classify_severity(): Classificação de severidade baseada em score
- Headers com Authorization Bearer token

Padrão Pagani: HTTP client 100%, httpx.AsyncClient mocked.

EM NOME DE JESUS - HTTP CLIENT PERFEITO!
"""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import httpx
import pytest

from backend.modules.tegumentar.config import TegumentarSettings
from backend.modules.tegumentar.lymphnode.api import LymphnodeAPI, ThreatValidation


@pytest.fixture
def settings():
    """Settings de teste."""
    return TegumentarSettings(
        postgres_dsn="postgresql://test:test@localhost:5432/test",
        lymphnode_endpoint="http://localhost:8080",
        lymphnode_api_key="test-api-key-12345",
    )


@pytest.fixture
def api(settings):
    """LymphnodeAPI de teste."""
    return LymphnodeAPI(settings)


@pytest.fixture
def threat_report():
    """Threat report de teste."""
    return {
        "threat_id": "teg-threat-abc123",
        "threat_type": "sql_injection",
        "severity": "critical",
        "anomaly_score": 0.95,
        "source": "tegumentar",
        "details": {"ip": "192.168.1.100", "pattern": "SELECT * FROM users"},
    }


def create_mock_http_client(response_json=None):
    """Helper para criar mock httpx.AsyncClient com context manager."""
    if response_json is None:
        response_json = {"status": "confirmed"}

    mock_response = MagicMock()
    mock_response.json.return_value = response_json
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mock_client, mock_response


class TestLymphnodeAPIInitialization:
    """Testa inicialização do LymphnodeAPI."""

    def test_initializes_with_settings(self, settings):
        """Deve armazenar settings fornecido."""
        api = LymphnodeAPI(settings)

        assert api._settings is settings

    def test_initializes_with_default_settings(self):
        """Deve usar get_settings() quando não fornecido."""
        with patch(
            "backend.modules.tegumentar.lymphnode.api.get_settings"
        ) as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            api = LymphnodeAPI()

            mock_get_settings.assert_called_once()
            assert api._settings is mock_settings

    def test_creates_httpx_timeout(self, api):
        """Deve criar httpx.Timeout com 10s total, 5s connect."""
        assert isinstance(api._timeout, httpx.Timeout)
        assert api._timeout.read == 10.0
        assert api._timeout.connect == 5.0


class TestHeaders:
    """Testa método _headers()."""

    def test_returns_content_type_json(self, api):
        """Deve sempre incluir Content-Type: application/json."""
        headers = api._headers()

        assert headers["Content-Type"] == "application/json"

    def test_includes_authorization_when_api_key_present(self, api):
        """Deve incluir Authorization Bearer quando API key configurado."""
        headers = api._headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-api-key-12345"

    def test_no_authorization_when_api_key_none(self, settings):
        """Não deve incluir Authorization quando API key é None."""
        settings.lymphnode_api_key = None
        api = LymphnodeAPI(settings)

        headers = api._headers()

        assert "Authorization" not in headers


class TestSubmitThreat:
    """Testa submit_threat() para validação de ameaças."""

    @pytest.mark.asyncio
    async def test_posts_to_threat_alert_endpoint(self, api, threat_report):
        """Deve fazer POST para /threat_alert."""
        mock_client, _ = create_mock_http_client(
            {"status": "confirmed", "immunis_response": "B-Cell activation"}
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.submit_threat(threat_report)

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/threat_alert"

    @pytest.mark.asyncio
    async def test_sends_correct_payload_structure(self, api, threat_report):
        """Deve enviar payload com threat_id, threat_type, severity, details, source."""
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.submit_threat(threat_report)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]

            assert payload["threat_id"] == "teg-threat-abc123"
            assert payload["threat_type"] == "sql_injection"
            assert payload["severity"] == "critical"
            assert payload["details"] == threat_report
            assert payload["source"] == "tegumentar"

    @pytest.mark.asyncio
    async def test_generates_threat_id_when_missing(self, api):
        """Deve gerar threat_id quando não fornecido."""
        threat_report = {"threat_type": "anomaly", "anomaly_score": 0.8}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client), patch.object(
            uuid, "uuid4"
        ) as mock_uuid:
            mock_uuid.return_value.hex = "abcdef123456"

            await api.submit_threat(threat_report)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]

            assert payload["threat_id"].startswith("teg-threat-")

    @pytest.mark.asyncio
    async def test_classifies_severity_when_missing(self, api):
        """Deve classificar severity usando _classify_severity() quando ausente."""
        threat_report = {"threat_type": "anomaly", "anomaly_score": 0.92}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.submit_threat(threat_report)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]

            # score 0.92 → "high" (>= 0.9)
            assert payload["severity"] == "high"

    @pytest.mark.asyncio
    async def test_uses_headers_with_authorization(self, api, threat_report):
        """Deve incluir headers com Authorization."""
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.submit_threat(threat_report)

            call_args = mock_client.post.call_args
            headers = call_args.kwargs["headers"]

            assert headers["Authorization"] == "Bearer test-api-key-12345"

    @pytest.mark.asyncio
    async def test_returns_threat_validation_with_confirmed_true(
        self, api, threat_report
    ):
        """Deve retornar ThreatValidation com confirmed=True."""
        mock_client, _ = create_mock_http_client(
            {"status": "confirmed", "immunis_response": "B-Cell activation"}
        )

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await api.submit_threat(threat_report)

            assert isinstance(result, ThreatValidation)
            assert result.confirmed is True
            assert result.threat_id == "teg-threat-abc123"
            assert result.severity == "critical"

    @pytest.mark.asyncio
    async def test_normalizes_confidence_to_0_1_range(self, api):
        """Deve normalizar confidence entre 0.0 e 1.0."""
        # Teste com score > 1.0
        threat_report = {"anomaly_score": 1.5}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await api.submit_threat(threat_report)

            # Deve ser capped em 1.0
            assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_includes_immunis_response_in_extra(self, api, threat_report):
        """Deve incluir immunis_response e raw body em extra."""
        response_body = {
            "status": "confirmed",
            "immunis_response": "B-Cell vaccination initiated",
        }
        mock_client, _ = create_mock_http_client(response_body)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await api.submit_threat(threat_report)

            assert result.extra["immunis_response"] == "B-Cell vaccination initiated"
            assert result.extra["raw"] == response_body
            assert "latency" in result.extra

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, api, threat_report):
        """Deve propagar HTTPStatusError quando response.raise_for_status() falha."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(),
        )

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client), pytest.raises(
            httpx.HTTPStatusError
        ):
            await api.submit_threat(threat_report)


class TestBroadcastVaccination:
    """Testa broadcast_vaccination() para disseminação de assinaturas."""

    @pytest.mark.asyncio
    async def test_posts_to_trigger_immune_response_endpoint(self, api):
        """Deve fazer POST para /trigger_immune_response."""
        rule = {"id": "sig-sql-001", "pattern": "SELECT.*FROM", "action": "block"}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.broadcast_vaccination(rule)

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/trigger_immune_response"

    @pytest.mark.asyncio
    async def test_sends_b_cell_vaccination_payload(self, api):
        """Deve enviar payload com response_type='b_cell_vaccination'."""
        rule = {"id": "sig-xss-002", "pattern": "<script>", "action": "block"}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.broadcast_vaccination(rule)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]

            assert payload["response_type"] == "b_cell_vaccination"
            assert payload["target_id"] == "sig-xss-002"
            assert payload["parameters"]["rule"] == rule

    @pytest.mark.asyncio
    async def test_generates_target_id_when_missing(self, api):
        """Deve gerar target_id quando rule não tem 'id'."""
        rule = {"pattern": "malware", "action": "block"}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client), patch.object(
            uuid, "uuid4"
        ) as mock_uuid:
            mock_uuid.return_value.hex = "xyz9876543"

            await api.broadcast_vaccination(rule)

            call_args = mock_client.post.call_args
            payload = call_args.kwargs["json"]

            assert payload["target_id"].startswith("rule-")

    @pytest.mark.asyncio
    async def test_uses_headers_with_authorization(self, api):
        """Deve incluir headers com Authorization."""
        rule = {"id": "test-rule"}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            await api.broadcast_vaccination(rule)

            call_args = mock_client.post.call_args
            headers = call_args.kwargs["headers"]

            assert headers["Authorization"] == "Bearer test-api-key-12345"

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self, api):
        """Deve retornar True quando vacinação bem-sucedida."""
        rule = {"id": "test-rule"}
        mock_client, _ = create_mock_http_client()

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await api.broadcast_vaccination(rule)

            assert result is True

    @pytest.mark.asyncio
    async def test_raises_on_http_error(self, api):
        """Deve propagar HTTPStatusError quando response.raise_for_status() falha."""
        rule = {"id": "test-rule"}

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=MagicMock(),
            response=MagicMock(),
        )

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client), pytest.raises(
            httpx.HTTPStatusError
        ):
            await api.broadcast_vaccination(rule)


class TestClassifySeverity:
    """Testa _classify_severity() para classificação de severidade."""

    def test_classifies_critical_for_score_gte_0_98(self):
        """Deve classificar como 'critical' quando score >= 0.98."""
        assert LymphnodeAPI._classify_severity(0.98) == "critical"
        assert LymphnodeAPI._classify_severity(0.99) == "critical"
        assert LymphnodeAPI._classify_severity(1.0) == "critical"

    def test_classifies_high_for_score_gte_0_9(self):
        """Deve classificar como 'high' quando 0.9 <= score < 0.98."""
        assert LymphnodeAPI._classify_severity(0.9) == "high"
        assert LymphnodeAPI._classify_severity(0.95) == "high"
        assert LymphnodeAPI._classify_severity(0.97) == "high"

    def test_classifies_medium_for_score_gte_0_75(self):
        """Deve classificar como 'medium' quando 0.75 <= score < 0.9."""
        assert LymphnodeAPI._classify_severity(0.75) == "medium"
        assert LymphnodeAPI._classify_severity(0.8) == "medium"
        assert LymphnodeAPI._classify_severity(0.89) == "medium"

    def test_classifies_low_for_score_below_0_75(self):
        """Deve classificar como 'low' quando score < 0.75."""
        assert LymphnodeAPI._classify_severity(0.74) == "low"
        assert LymphnodeAPI._classify_severity(0.5) == "low"
        assert LymphnodeAPI._classify_severity(0.0) == "low"


class TestThreatValidation:
    """Testa dataclass ThreatValidation."""

    def test_threat_validation_has_required_fields(self):
        """ThreatValidation deve ter confirmed, threat_id, severity, confidence, extra."""
        validation = ThreatValidation(
            confirmed=True,
            threat_id="threat-123",
            severity="high",
            confidence=0.92,
            extra={"key": "value"},
        )

        assert validation.confirmed is True
        assert validation.threat_id == "threat-123"
        assert validation.severity == "high"
        assert validation.confidence == 0.92
        assert validation.extra == {"key": "value"}

    def test_threat_validation_defaults(self):
        """ThreatValidation deve ter defaults para campos opcionais."""
        validation = ThreatValidation(confirmed=False)

        assert validation.threat_id is None
        assert validation.severity is None
        assert validation.confidence == 0.0
        assert validation.extra is None

    def test_threat_validation_uses_slots(self):
        """ThreatValidation deve usar slots para eficiência."""
        validation = ThreatValidation(confirmed=True)

        # Slots não têm __dict__
        assert not hasattr(validation, "__dict__")
