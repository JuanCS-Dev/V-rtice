"""PENELOPE API routes tests.

Testes para validar endpoints da API do serviço PENELOPE.

Coverage target: ≥90% per Constitutional requirement (Artigo II, Seção 2).

Author: Vértice Platform Team
License: Proprietary
"""

from fastapi import status


class TestFruitsStatusEndpoint:
    """Test suite for 9 Frutos do Espírito status endpoint."""

    def test_get_fruits_status_success(self, client):
        """Test GET /fruits/status returns all 9 fruits."""
        response = client.get("/api/v1/penelope/fruits/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validar estrutura
        assert "fruits" in data
        assert "overall_score" in data
        assert "healthy_fruits" in data
        assert "total_fruits" in data
        assert "biblical_reference" in data

        # Validar 9 frutos
        assert data["total_fruits"] == 9
        assert len(data["fruits"]) == 9

        # Validar frutos específicos
        expected_fruits = [
            "amor_agape",
            "alegria_chara",
            "paz_eirene",
            "paciencia_makrothymia",
            "bondade_chrestotes",
            "fidelidade_pistis",
            "mansidao_praotes",
            "dominio_proprio_enkrateia",
            "gentileza_agathosyne",
        ]

        for fruit_key in expected_fruits:
            assert fruit_key in data["fruits"]
            fruit = data["fruits"][fruit_key]
            assert "name" in fruit
            assert "score" in fruit
            assert "description" in fruit
            assert "metric" in fruit
            assert "status" in fruit
            assert 0.0 <= fruit["score"] <= 1.0

    def test_fruits_status_includes_biblical_reference(self, client):
        """Test that fruits status includes Galatians 5:22-23 reference."""
        response = client.get("/api/v1/penelope/fruits/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["biblical_reference"] == "Gálatas 5:22-23"

    def test_fruits_overall_score_calculation(self, client):
        """Test that overall score is correctly calculated."""
        response = client.get("/api/v1/penelope/fruits/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Calcular média manualmente
        fruits = data["fruits"]
        expected_avg = sum(f["score"] for f in fruits.values()) / len(fruits)

        assert abs(data["overall_score"] - expected_avg) < 0.01


class TestVirtuesMetricsEndpoint:
    """Test suite for 3 Virtudes Teológicas metrics endpoint."""

    def test_get_virtues_metrics_success(self, client):
        """Test GET /virtues/metrics returns 3 theological virtues."""
        response = client.get("/api/v1/penelope/virtues/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validar estrutura
        assert "virtues" in data
        assert "overall_score" in data
        assert "theological_reference" in data
        assert "governance_framework" in data

        # Validar 3 virtudes
        virtues = data["virtues"]
        assert len(virtues) == 3

        # Validar virtudes específicas
        assert "sophia" in virtues
        assert "praotes" in virtues
        assert "tapeinophrosyne" in virtues

        # Validar estrutura de cada virtude
        for virtue_key, virtue_data in virtues.items():
            assert "name" in virtue_data
            assert "score" in virtue_data
            assert "metrics" in virtue_data
            assert "biblical_reference" in virtue_data
            assert "status" in virtue_data
            assert 0.0 <= virtue_data["score"] <= 1.0

    def test_virtues_sophia_metrics(self, client):
        """Test Sophia (Sabedoria) virtue has expected metrics."""
        response = client.get("/api/v1/penelope/virtues/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        sophia = data["virtues"]["sophia"]
        metrics = sophia["metrics"]

        # Validar métricas esperadas
        assert "interventions_approved" in metrics
        assert "interventions_deferred" in metrics
        assert "false_positives_avoided" in metrics
        assert "wisdom_queries" in metrics
        assert "precedents_found" in metrics

    def test_virtues_praotes_metrics(self, client):
        """Test Praotes (Mansidão) virtue has expected metrics."""
        response = client.get("/api/v1/penelope/virtues/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        praotes = data["virtues"]["praotes"]
        metrics = praotes["metrics"]

        # Validar métricas esperadas
        assert "patches_under_25_lines" in metrics
        assert "patches_over_25_lines" in metrics
        assert "average_patch_size" in metrics
        assert "reversibility_score_avg" in metrics
        assert "breaking_changes_prevented" in metrics

    def test_virtues_tapeinophrosyne_metrics(self, client):
        """Test Tapeinophrosyne (Humildade) virtue has expected metrics."""
        response = client.get("/api/v1/penelope/virtues/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        tapeinophrosyne = data["virtues"]["tapeinophrosyne"]
        metrics = tapeinophrosyne["metrics"]

        # Validar métricas esperadas
        assert "autonomous_actions" in metrics
        assert "escalated_to_human" in metrics
        assert "correct_escalations" in metrics
        assert "false_confidence_cases" in metrics
        assert "lessons_learned" in metrics


class TestHealingHistoryEndpoint:
    """Test suite for healing history endpoint."""

    def test_get_healing_history_default_params(self, client):
        """Test GET /healing/history with default parameters."""
        response = client.get("/api/v1/penelope/healing/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validar estrutura
        assert "events" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        # Validar eventos
        assert isinstance(data["events"], list)

        # Se houver eventos, validar estrutura
        if data["events"]:
            event = data["events"][0]
            assert "event_id" in event
            assert "timestamp" in event
            assert "anomaly_type" in event
            assert "affected_service" in event
            assert "severity" in event
            assert "action_taken" in event
            assert "outcome" in event

    def test_healing_history_with_limit(self, client):
        """Test healing history respects limit parameter."""
        response = client.get("/api/v1/penelope/healing/history?limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["limit"] == 2
        assert len(data["events"]) <= 2

    def test_healing_history_with_offset(self, client):
        """Test healing history supports offset for pagination."""
        response = client.get("/api/v1/penelope/healing/history?offset=1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["offset"] == 1

    def test_healing_history_severity_filter(self, client):
        """Test healing history filters by severity."""
        response = client.get("/api/v1/penelope/healing/history?severity=P0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Todos os eventos devem ter severity P0
        for event in data["events"]:
            assert event["severity"] == "P0"

    def test_healing_history_invalid_limit(self, client):
        """Test healing history rejects invalid limit (>500)."""
        response = client.get("/api/v1/penelope/healing/history?limit=1000")

        # FastAPI deve retornar 422 para limite > 500
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDiagnoseEndpoint:
    """Test suite for anomaly diagnosis endpoint."""

    def test_diagnose_anomaly_success(self, client):
        """Test POST /diagnose with valid anomaly data."""
        request_data = {
            "anomaly_id": "test-anomaly-001",
            "anomaly_type": "latency_spike",
            "affected_service": "api-gateway",
            "metrics": {"p95_latency_ms": 850, "p99_latency_ms": 1200},
            "context": {"recent_deploy": "v2.3.1", "traffic_increase": False},
        }

        response = client.post("/api/v1/penelope/diagnose", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Validar estrutura de resposta
        assert "diagnosis_id" in data
        assert "anomaly_id" in data
        assert "root_cause" in data
        assert "confidence" in data
        assert "severity" in data
        assert "causal_chain" in data
        assert "sophia_recommendation" in data
        assert "intervention_level" in data
        assert "precedents" in data

        # Validar valores
        assert data["anomaly_id"] == "test-anomaly-001"
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["severity"] in ["P0", "P1", "P2", "P3"]
        assert data["sophia_recommendation"] in ["observe", "intervene", "escalate"]

    def test_diagnose_includes_causal_chain(self, client):
        """Test diagnosis includes causal chain analysis."""
        request_data = {
            "anomaly_id": "test-anomaly-002",
            "anomaly_type": "error_rate_increase",
            "affected_service": "worker-service",
            "metrics": {},
            "context": {},
        }

        response = client.post("/api/v1/penelope/diagnose", json=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Validar causal chain
        assert isinstance(data["causal_chain"], list)
        assert len(data["causal_chain"]) > 0

        for step in data["causal_chain"]:
            assert "step" in step
            assert "description" in step
            assert "confidence" in step

    def test_diagnose_missing_required_fields(self, client):
        """Test diagnosis endpoint rejects missing required fields."""
        request_data = {
            "anomaly_id": "test-anomaly-003"
            # Missing anomaly_type and affected_service
        }

        response = client.post("/api/v1/penelope/diagnose", json=request_data)

        # FastAPI deve retornar 422 para campos faltando
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestPatchesEndpoint:
    """Test suite for patches listing endpoint."""

    def test_get_patches_default(self, client):
        """Test GET /patches returns list of patches."""
        response = client.get("/api/v1/penelope/patches")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validar estrutura
        assert "patches" in data
        assert "total" in data
        assert "limit" in data

        # Validar estrutura de patches
        if data["patches"]:
            patch = data["patches"][0]
            assert "patch_id" in patch
            assert "diagnosis_id" in patch
            assert "status" in patch
            assert "patch_size_lines" in patch
            assert "mansidao_score" in patch
            assert "confidence" in patch
            assert "affected_files" in patch

    def test_get_patches_with_status_filter(self, client):
        """Test patches endpoint filters by status."""
        response = client.get("/api/v1/penelope/patches?status_filter=deployed")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Todos os patches devem ter status=deployed
        for patch in data["patches"]:
            assert patch["status"] == "deployed"

    def test_get_patches_with_limit(self, client):
        """Test patches endpoint respects limit."""
        response = client.get("/api/v1/penelope/patches?limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["limit"] == 5
        assert len(data["patches"]) <= 5


class TestWisdomBaseEndpoint:
    """Test suite for Wisdom Base query endpoint."""

    def test_query_wisdom_base_success(self, client):
        """Test GET /wisdom returns precedents."""
        response = client.get(
            "/api/v1/penelope/wisdom?anomaly_type=latency_spike&similarity_threshold=0.8"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Validar estrutura
        assert "precedents" in data
        assert "total_found" in data
        assert "query" in data

        # Validar query echo
        assert data["query"]["anomaly_type"] == "latency_spike"
        assert data["query"]["similarity_threshold"] == 0.8

        # Validar estrutura de precedentes
        if data["precedents"]:
            precedent = data["precedents"][0]
            assert "case_id" in precedent
            assert "anomaly_type" in precedent
            assert "patch_applied" in precedent
            assert "outcome" in precedent
            assert "lessons_learned" in precedent
            assert "similarity" in precedent
            assert 0.0 <= precedent["similarity"] <= 1.0

    def test_wisdom_base_with_service_filter(self, client):
        """Test wisdom base query with service filter."""
        response = client.get(
            "/api/v1/penelope/wisdom?anomaly_type=memory_leak&service=worker-service"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["query"]["service"] == "worker-service"

    def test_wisdom_base_missing_anomaly_type(self, client):
        """Test wisdom base query requires anomaly_type."""
        response = client.get("/api/v1/penelope/wisdom")

        # FastAPI deve retornar 422 para campo obrigatório faltando
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAudioSynthesisEndpoint:
    """Test suite for audio synthesis endpoint (placeholder)."""

    def test_audio_synthesis_not_implemented(self, client):
        """Test POST /audio/synthesize returns 501 Not Implemented."""
        response = client.post("/api/v1/penelope/audio/synthesize?text=Hello%20world")

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        data = response.json()

        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"] == "Audio synthesis not yet implemented"


# === Edge Cases and Validation Tests ===


class TestAPIValidation:
    """Test suite for API input validation and edge cases."""

    def test_healing_history_negative_offset(self, client):
        """Test healing history rejects negative offset."""
        response = client.get("/api/v1/penelope/healing/history?offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_patches_invalid_limit_too_high(self, client):
        """Test patches endpoint rejects limit > 100."""
        response = client.get("/api/v1/penelope/patches?limit=200")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_wisdom_similarity_threshold_bounds(self, client):
        """Test wisdom base validates similarity threshold bounds (0.0-1.0)."""
        # Threshold > 1.0 deve falhar
        response = client.get(
            "/api/v1/penelope/wisdom?anomaly_type=test&similarity_threshold=1.5"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Threshold < 0.0 deve falhar
        response = client.get(
            "/api/v1/penelope/wisdom?anomaly_type=test&similarity_threshold=-0.1"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Threshold = 0.5 deve funcionar
        response = client.get(
            "/api/v1/penelope/wisdom?anomaly_type=test&similarity_threshold=0.5"
        )
        assert response.status_code == status.HTTP_200_OK
