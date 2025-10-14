"""
Unit Tests - MIP FastAPI Application

Testes para endpoints REST do Motor de Integridade Processual.
Target: 95%+ coverage de api.py.

Autor: Juan Carlos de Souza
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from uuid import uuid4

# Import app and models
from mip.api import app
from mip.models import (
    ActionPlan,
    ActionStep,
    Stakeholder,
    StakeholderType,
    ActionCategory,
    Effect,
    EthicalVerdict,
    VerdictStatus,
    FrameworkScore,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_engine():
    """Mock ProcessIntegrityEngine."""
    engine = Mock()
    engine.evaluate = Mock()
    engine.get_audit_trail = Mock(return_value=[])
    return engine


@pytest.fixture
def mock_kb_repo():
    """Mock KnowledgeBaseRepository."""
    repo = AsyncMock()
    repo.initialize = AsyncMock()
    repo.close = AsyncMock()
    repo.list_principles = AsyncMock(return_value=[])
    repo.get_principle = AsyncMock(return_value=None)
    repo.get_decision = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def test_client_with_mocks(mock_engine, mock_kb_repo):
    """
    TestClient com mocks injetados no app state.

    Bypassa o lifespan async para testes síncronos.
    """
    # Override lifespan para testes
    app.state.engine = mock_engine
    app.state.kb_repo = mock_kb_repo
    app.state.kb_connected = True
    app.state.principle_service = Mock()
    app.state.audit_service = AsyncMock()

    client = TestClient(app)
    yield client

    # Cleanup
    del app.state.engine
    del app.state.kb_repo
    del app.state.kb_connected


@pytest.fixture
def valid_action_plan():
    """ActionPlan válido para testes."""
    return ActionPlan(
        name="Test Plan",
        description="Test description",
        category=ActionCategory.DEFENSIVE,
        steps=[
            ActionStep(
                sequence_number=1,
                description="Test step",
                action_type="test",
            )
        ],
        stakeholders=[
            Stakeholder(
                id="user1",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test user",
                impact_magnitude=0.5,
                autonomy_respected=True,
                vulnerability_level=0.3,
            )
        ],
        urgency=0.5,
        risk_level=0.3,
    )


@pytest.fixture
def approved_verdict():
    """EthicalVerdict aprovado para testes."""
    return EthicalVerdict(
        plan_id=str(uuid4()),
        status=VerdictStatus.APPROVED,
        aggregate_score=0.85,
        confidence=0.90,
        summary="Plan approved by all frameworks",
        detailed_reasoning="All ethical frameworks agree",
        kantian_score=FrameworkScore("Kantian", 0.9, "Respects autonomy"),
        utilitarian_score=FrameworkScore("Utilitarian", 0.85, "Maximizes utility"),
        virtue_score=FrameworkScore("Virtue", 0.82, "Virtuous action"),
        principialism_score=FrameworkScore("Principialism", 0.88, "Principles respected"),
        conflicts_detected=[],
        requires_human_review=False,
    )


# ============================================================================
# Tests: Root Endpoint
# ============================================================================

class TestRootEndpoint:
    """Testes para GET /."""

    def test_root_returns_service_info(self, test_client_with_mocks):
        """Root deve retornar informações do serviço."""
        response = test_client_with_mocks.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert data["status"] == "operational"
        assert data["docs"] == "/docs"


# ============================================================================
# Tests: Health Check
# ============================================================================

class TestHealthEndpoint:
    """Testes para GET /health."""

    def test_health_check_success(self, test_client_with_mocks):
        """Health check deve retornar status healthy."""
        response = test_client_with_mocks.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
        assert "neo4j_connected" in data
        assert "engine_initialized" in data

    def test_health_check_shows_kb_connected(self, test_client_with_mocks):
        """Health check deve refletir status do Knowledge Base."""
        response = test_client_with_mocks.get("/health")
        data = response.json()

        assert data["neo4j_connected"] is True
        assert data["engine_initialized"] is True

    def test_health_check_when_kb_disconnected(self, test_client_with_mocks):
        """Health check com KB desconectado."""
        app.state.kb_connected = False

        response = test_client_with_mocks.get("/health")
        data = response.json()

        assert response.status_code == 200
        assert data["neo4j_connected"] is False


# ============================================================================
# Tests: Evaluate Endpoint
# ============================================================================

class TestEvaluateEndpoint:
    """Testes para POST /evaluate."""

    def test_evaluate_valid_plan(self, test_client_with_mocks, valid_action_plan, approved_verdict):
        """Deve avaliar plano válido e retornar verdict."""
        # Mock engine response
        app.state.engine.evaluate.return_value = approved_verdict

        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": valid_action_plan.model_dump(mode="json")}
        )

        assert response.status_code == 200
        data = response.json()

        assert "verdict" in data
        assert "evaluation_time_ms" in data

        verdict = data["verdict"]
        assert verdict["status"] == "approved"
        assert verdict["aggregate_score"] == 0.85
        assert verdict["confidence"] == 0.90

    def test_evaluate_invalid_plan_returns_400(self, test_client_with_mocks):
        """Plano inválido deve retornar 400."""
        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": {"invalid": "data"}}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_evaluate_engine_error_returns_500(self, test_client_with_mocks, valid_action_plan):
        """Erro no engine deve retornar 500."""
        # Mock engine para lançar exceção
        app.state.engine.evaluate.side_effect = Exception("Engine failure")

        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": valid_action_plan.model_dump(mode="json")}
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_evaluate_persists_decision_when_kb_available(
        self, test_client_with_mocks, valid_action_plan, approved_verdict
    ):
        """Deve persistir decisão quando KB disponível."""
        app.state.engine.evaluate.return_value = approved_verdict

        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": valid_action_plan.model_dump(mode="json")}
        )

        assert response.status_code == 200

        # Verify audit service foi chamado
        app.state.audit_service.log_decision.assert_called_once()

    def test_evaluate_handles_persistence_failure_gracefully(
        self, test_client_with_mocks, valid_action_plan, approved_verdict
    ):
        """Deve continuar mesmo se persistence falhar."""
        app.state.engine.evaluate.return_value = approved_verdict

        # Mock audit service para falhar
        app.state.audit_service.log_decision.side_effect = Exception("Persistence error")

        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": valid_action_plan.model_dump(mode="json")}
        )

        # Should still succeed (graceful degradation)
        assert response.status_code == 200

    def test_evaluate_skips_persistence_when_kb_unavailable(
        self, test_client_with_mocks, valid_action_plan, approved_verdict
    ):
        """Não deve tentar persistir quando KB indisponível."""
        app.state.kb_connected = False
        app.state.engine.evaluate.return_value = approved_verdict

        response = test_client_with_mocks.post(
            "/evaluate",
            json={"plan": valid_action_plan.model_dump(mode="json")}
        )

        assert response.status_code == 200

        # Audit service NÃO deve ser chamado
        app.state.audit_service.log_decision.assert_not_called()


# ============================================================================
# Tests: Principles Endpoints
# ============================================================================

class TestPrinciplesEndpoints:
    """Testes para endpoints de princípios."""

    def test_list_principles_requires_kb(self, test_client_with_mocks):
        """Listar princípios requer KB disponível."""
        app.state.kb_connected = False

        response = test_client_with_mocks.get("/principles")

        assert response.status_code == 503
        data = response.json()
        assert "Knowledge Base unavailable" in data["error"]

    def test_list_principles_success(self, test_client_with_mocks):
        """Deve listar princípios quando KB disponível."""
        from mip.infrastructure.knowledge_models import Principle, PrincipleLevel

        mock_principle = Principle(
            name="Test Principle",
            level=PrincipleLevel.LAW,
            description="Test description",
            severity=5,
            philosophical_foundation="Test foundation",
        )

        app.state.kb_repo.list_principles.return_value = [mock_principle]

        response = test_client_with_mocks.get("/principles")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test Principle"

    def test_list_principles_with_level_filter(self, test_client_with_mocks):
        """Deve permitir filtrar princípios por level."""
        app.state.kb_repo.list_principles.return_value = []

        response = test_client_with_mocks.get("/principles?level=law")

        assert response.status_code == 200

    def test_list_principles_handles_errors(self, test_client_with_mocks):
        """Deve lidar com erros ao listar princípios."""
        app.state.kb_repo.list_principles.side_effect = Exception("DB error")

        response = test_client_with_mocks.get("/principles")

        assert response.status_code == 500

    def test_get_principle_by_id_requires_kb(self, test_client_with_mocks):
        """GET principle by ID requer KB."""
        app.state.kb_connected = False
        test_id = uuid4()

        response = test_client_with_mocks.get(f"/principles/{test_id}")

        assert response.status_code == 503

    def test_get_principle_by_id_not_found(self, test_client_with_mocks):
        """Deve retornar 404 se princípio não existe."""
        app.state.kb_repo.get_principle.return_value = None
        test_id = uuid4()

        response = test_client_with_mocks.get(f"/principles/{test_id}")

        assert response.status_code == 404

    def test_get_principle_by_id_success(self, test_client_with_mocks):
        """Deve retornar princípio quando existe."""
        from mip.infrastructure.knowledge_models import Principle, PrincipleLevel

        test_id = uuid4()
        mock_principle = Principle(
            id=test_id,
            name="Test Principle",
            level=PrincipleLevel.LAW,
            description="Test",
            severity=5,
            philosophical_foundation="Test",
        )

        app.state.kb_repo.get_principle.return_value = mock_principle

        response = test_client_with_mocks.get(f"/principles/{test_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_id)
        assert data["name"] == "Test Principle"


# ============================================================================
# Tests: Decisions/Audit Trail Endpoints
# ============================================================================

class TestDecisionsEndpoints:
    """Testes para endpoints de decisões e audit trail."""

    def test_get_decision_by_id_requires_kb(self, test_client_with_mocks):
        """GET decision by ID requer KB."""
        app.state.kb_connected = False
        test_id = uuid4()

        response = test_client_with_mocks.get(f"/decisions/{test_id}")

        assert response.status_code == 503

    def test_get_decision_by_id_not_found(self, test_client_with_mocks):
        """Deve retornar 404 se decisão não existe."""
        app.state.kb_repo.get_decision.return_value = None
        test_id = uuid4()

        response = test_client_with_mocks.get(f"/decisions/{test_id}")

        assert response.status_code == 404

    def test_get_decision_by_id_success(self, test_client_with_mocks):
        """Deve retornar decisão quando existe."""
        from mip.infrastructure.knowledge_models import Decision, DecisionStatus
        from datetime import datetime

        test_id = uuid4()
        mock_decision = Decision(
            id=test_id,
            action_plan_id=str(uuid4()),
            action_plan_name="Test Plan",
            status=DecisionStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.90,
            summary="Test summary",
            timestamp=datetime.utcnow(),
        )

        app.state.kb_repo.get_decision.return_value = mock_decision

        response = test_client_with_mocks.get(f"/decisions/{test_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_id)
        assert data["action_plan_name"] == "Test Plan"
        assert data["status"] == "approved"

    def test_get_audit_trail_with_kb_disconnected(self, test_client_with_mocks):
        """Deve usar fallback in-memory quando KB desconectado."""
        from mip.models import AuditTrailEntry
        from datetime import datetime

        app.state.kb_connected = False

        # Mock in-memory audit trail
        mock_entry = Mock()
        mock_entry.verdict = Mock()
        mock_entry.verdict.plan_id = str(uuid4())
        mock_entry.verdict.status = VerdictStatus.APPROVED
        mock_entry.verdict.aggregate_score = 0.85
        mock_entry.verdict.confidence = 0.90
        mock_entry.verdict.summary = "Test"
        mock_entry.timestamp = datetime.utcnow()

        app.state.engine.get_audit_trail.return_value = [mock_entry]

        response = test_client_with_mocks.get("/audit-trail")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_audit_trail_pagination(self, test_client_with_mocks):
        """Deve suportar paginação."""
        app.state.kb_connected = False
        app.state.engine.get_audit_trail.return_value = []

        response = test_client_with_mocks.get("/audit-trail?limit=10&offset=0")

        assert response.status_code == 200

    def test_get_audit_trail_with_kb_connected(self, test_client_with_mocks):
        """Com KB conectado retorna lista vazia (TODO implementado)."""
        app.state.kb_connected = True

        response = test_client_with_mocks.get("/audit-trail")

        assert response.status_code == 200
        data = response.json()
        assert data == []  # TODO: Not yet implemented in api.py


# ============================================================================
# Tests: Error Handlers
# ============================================================================

class TestErrorHandlers:
    """Testes para exception handlers."""

    def test_404_not_found(self, test_client_with_mocks):
        """Endpoint inexistente deve retornar 404."""
        response = test_client_with_mocks.get("/nonexistent")

        assert response.status_code == 404

    def test_http_exception_handler(self, test_client_with_mocks):
        """HTTPException deve ser tratada."""
        # Trigger 503 (já testado acima)
        app.state.kb_connected = False
        response = test_client_with_mocks.get("/principles")

        assert response.status_code == 503
        data = response.json()
        assert "error" in data
        assert "status_code" in data


# ============================================================================
# Tests: Pydantic Models (Request/Response)
# ============================================================================

class TestPydanticModels:
    """Testes para request/response models da API."""

    def test_evaluate_request_model(self):
        """EvaluateRequest deve validar plan."""
        from mip.api import EvaluateRequest

        plan = ActionPlan(
            name="Test",
            description="Test",
            category=ActionCategory.DEFENSIVE,
            steps=[ActionStep(sequence_number=1, description="Test", action_type="test")],
            urgency=0.5,
            risk_level=0.3,
        )

        request = EvaluateRequest(plan=plan)
        assert request.plan == plan

    def test_evaluate_response_model(self):
        """EvaluateResponse deve incluir verdict e timing."""
        from mip.api import EvaluateResponse

        verdict = EthicalVerdict(
            plan_id=str(uuid4()),
            status=VerdictStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.90,
            summary="Test",
            detailed_reasoning="Test",
        )

        response = EvaluateResponse(verdict=verdict, evaluation_time_ms=1.5)

        assert response.verdict == verdict
        assert response.evaluation_time_ms == 1.5

    def test_health_response_model(self):
        """HealthResponse deve ter campos corretos."""
        from mip.api import HealthResponse

        health = HealthResponse(
            service="mip",
            version="1.0.0",
            neo4j_connected=True,
            engine_initialized=True,
        )

        assert health.status == "healthy"
        assert health.service == "mip"

    def test_principle_response_model(self):
        """PrincipleResponse deve mapear Principle."""
        from mip.api import PrincipleResponse

        principle = PrincipleResponse(
            id=str(uuid4()),
            name="Test",
            level="law",
            description="Test",
            severity=5,
            philosophical_foundation="Test",
        )

        assert principle.name == "Test"
        assert principle.level == "law"

    def test_decision_response_model(self):
        """DecisionResponse deve mapear Decision."""
        from mip.api import DecisionResponse

        decision = DecisionResponse(
            id=str(uuid4()),
            action_plan_name="Test",
            status="approved",
            aggregate_score=0.85,
            confidence=0.90,
            summary="Test",
            timestamp="2025-10-14T12:00:00",
        )

        assert decision.status == "approved"

    def test_error_response_model(self):
        """ErrorResponse deve ter campos de erro."""
        from mip.api import ErrorResponse

        error = ErrorResponse(
            error="Test error",
            detail="Test detail",
            status_code=500,
        )

        assert error.error == "Test error"
        assert error.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
