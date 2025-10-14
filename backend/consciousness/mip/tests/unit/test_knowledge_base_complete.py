"""
Unit Tests - Knowledge Base Complete Coverage

Testes para atingir 95%+ coverage no knowledge_base.py.
Foca em paths não cobertos: async operations, Neo4j integration, error handling.

Autor: Juan Carlos de Souza
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime

from mip.infrastructure.knowledge_base import (
    KnowledgeBaseRepository,
    PrincipleQueryService,
    AuditTrailService,
)
from mip.infrastructure.knowledge_models import (
    Principle,
    Decision,
    PrincipleLevel,
    DecisionStatus,
    ViolationSeverity,
)


class TestKnowledgeBaseRepositoryInit:
    """Testa inicialização do repository."""

    def test_init_with_defaults(self):
        """Deve inicializar com valores padrão."""
        repo = KnowledgeBaseRepository()

        assert repo.uri == "bolt://localhost:7687"
        assert repo.user == "neo4j"
        assert repo.password == "neo4j123"
        assert repo.database == "neo4j"
        assert repo.max_connection_pool_size == 50
        assert repo.driver is None
        assert repo._initialized is False

    def test_init_with_custom_params(self):
        """Deve aceitar parâmetros customizados."""
        repo = KnowledgeBaseRepository(
            uri="bolt://custom:7687",
            user="custom_user",
            password="custom_pass",
            database="custom_db",
            max_connection_pool_size=100,
        )

        assert repo.uri == "bolt://custom:7687"
        assert repo.user == "custom_user"
        assert repo.password == "custom_pass"
        assert repo.database == "custom_db"
        assert repo.max_connection_pool_size == 100


@pytest.mark.asyncio
class TestKnowledgeBaseRepositoryLifecycle:
    """Testa lifecycle (initialize/close) do repository."""

    async def test_initialize_success(self):
        """Deve inicializar driver Neo4j com sucesso."""
        repo = KnowledgeBaseRepository()

        # Mock AsyncGraphDatabase.driver
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"test": 1})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)

        with patch("mip.infrastructure.knowledge_base.AsyncGraphDatabase.driver", return_value=mock_driver):
            await repo.initialize()

        assert repo._initialized is True
        assert repo.driver is mock_driver

    async def test_initialize_already_initialized(self):
        """Deve retornar early se já inicializado."""
        repo = KnowledgeBaseRepository()
        repo._initialized = True
        repo.driver = Mock()

        # Should not call AsyncGraphDatabase.driver again
        with patch("mip.infrastructure.knowledge_base.AsyncGraphDatabase.driver") as mock_driver_constructor:
            await repo.initialize()
            mock_driver_constructor.assert_not_called()

    async def test_initialize_connection_failure(self):
        """Deve propagar exceção se falha ao conectar."""
        repo = KnowledgeBaseRepository()

        with patch("mip.infrastructure.knowledge_base.AsyncGraphDatabase.driver", side_effect=Exception("Connection failed")):
            with pytest.raises(Exception, match="Connection failed"):
                await repo.initialize()

        assert repo._initialized is False

    async def test_close_when_driver_exists(self):
        """Deve fechar driver se existir."""
        repo = KnowledgeBaseRepository()
        mock_driver = AsyncMock()
        repo.driver = mock_driver
        repo._initialized = True

        await repo.close()

        mock_driver.close.assert_called_once()
        assert repo._initialized is False

    async def test_close_when_no_driver(self):
        """Deve ser no-op se driver é None."""
        repo = KnowledgeBaseRepository()
        repo.driver = None

        # Should not raise
        await repo.close()


@pytest.mark.asyncio
class TestCreateIndexes:
    """Testa criação de indexes."""

    async def test_create_indexes_success(self):
        """Deve criar todos os indexes com sucesso."""
        repo = KnowledgeBaseRepository()

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_session.run = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        await repo._create_indexes()

        # Should call run 6 times (6 indexes)
        assert mock_session.run.call_count == 6

    async def test_create_indexes_no_driver(self):
        """Deve retornar early se driver é None."""
        repo = KnowledgeBaseRepository()
        repo.driver = None

        # Should not raise
        await repo._create_indexes()

    async def test_create_indexes_neo4j_error(self):
        """Deve logar warning mas não falhar se erro ao criar index."""
        from neo4j.exceptions import Neo4jError

        repo = KnowledgeBaseRepository()

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_session.run = AsyncMock(side_effect=Neo4jError("Index already exists"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        # Should not raise
        await repo._create_indexes()


@pytest.mark.asyncio
class TestPrincipleOperations:
    """Testa operações CRUD de Principles."""

    async def test_create_principle_success(self):
        """Deve criar principle com sucesso."""
        repo = KnowledgeBaseRepository()

        principle = Principle(
            id=uuid4(),
            name="Test Principle",
            level=PrincipleLevel.FUNDAMENTAL,
            description="Test description",
            severity=9,
        )

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": str(principle.id)})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.create_principle(principle)

        assert result == principle.id
        mock_session.run.assert_called_once()

    async def test_create_principle_no_driver(self):
        """Deve falhar se driver não inicializado."""
        repo = KnowledgeBaseRepository()
        repo.driver = None

        principle = Principle(
            id=uuid4(),
            name="Test",
            level=PrincipleLevel.FUNDAMENTAL,
            description="Test",
            severity=9,
        )

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.create_principle(principle)

    async def test_create_principle_with_parent(self):
        """Deve criar relação DERIVES_FROM se tem parent."""
        repo = KnowledgeBaseRepository()

        parent_id = uuid4()
        principle = Principle(
            id=uuid4(),
            name="Child Principle",
            level=PrincipleLevel.DERIVED,
            description="Test",
            severity=9,
            parent_principle_id=parent_id,
        )

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": str(principle.id)})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.create_principle(principle)

        assert result == principle.id
        # Should call run twice: once for create, once for hierarchy
        assert mock_session.run.call_count == 2

    async def test_get_principle_found(self):
        """Deve retornar principle se encontrado."""
        repo = KnowledgeBaseRepository()

        principle_id = uuid4()
        mock_data = {
            "id": str(principle_id),
            "name": "Test Principle",
            "level": "fundamental",
            "description": "Test",
            "severity": 9,
            "parent_principle_id": None,
            "applies_to_action_types": [],
            "philosophical_foundation": "",
            "references": [],
            "created_at": datetime.utcnow().isoformat(),
            "immutable": True,
        }

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"p": mock_data})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.get_principle(principle_id)

        assert result is not None
        assert result.id == principle_id
        assert result.name == "Test Principle"

    async def test_get_principle_not_found(self):
        """Deve retornar None se não encontrado."""
        repo = KnowledgeBaseRepository()

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value=None)

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.get_principle(uuid4())

        assert result is None

    async def test_get_principle_by_name_found(self):
        """Deve buscar principle por nome."""
        repo = KnowledgeBaseRepository()

        principle_id = uuid4()
        mock_data = {
            "id": str(principle_id),
            "name": "Lei Zero",
            "level": "zero",
            "description": "Test",
            "severity": 10,
            "parent_principle_id": None,
            "applies_to_action_types": [],
            "philosophical_foundation": "",
            "references": [],
            "created_at": datetime.utcnow().isoformat(),
            "immutable": True,
        }

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"p": mock_data})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.get_principle_by_name("Lei Zero")

        assert result is not None
        assert result.name == "Lei Zero"

    async def test_list_principles_all(self):
        """Deve listar todos os principles."""
        repo = KnowledgeBaseRepository()

        mock_data = [
            {"p": {
                "id": str(uuid4()),
                "name": "P1",
                "level": "fundamental",
                "description": "Test",
                "severity": 9,
                "parent_principle_id": None,
                "applies_to_action_types": [],
                "philosophical_foundation": "",
                "references": [],
                "created_at": datetime.utcnow().isoformat(),
                "immutable": True,
            }},
            {"p": {
                "id": str(uuid4()),
                "name": "P2",
                "level": "derived",
                "description": "Test",
                "severity": 7,
                "parent_principle_id": None,
                "applies_to_action_types": [],
                "philosophical_foundation": "",
                "references": [],
                "created_at": datetime.utcnow().isoformat(),
                "immutable": True,
            }},
        ]

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=mock_data)

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.list_principles()

        assert len(result) == 2
        assert result[0].name == "P1"
        assert result[1].name == "P2"

    async def test_list_principles_filtered_by_level(self):
        """Deve filtrar principles por nível."""
        repo = KnowledgeBaseRepository()

        mock_data = [
            {"p": {
                "id": str(uuid4()),
                "name": "P1",
                "level": "fundamental",
                "description": "Test",
                "severity": 9,
                "parent_principle_id": None,
                "applies_to_action_types": [],
                "philosophical_foundation": "",
                "references": [],
                "created_at": datetime.utcnow().isoformat(),
                "immutable": True,
            }},
        ]

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=mock_data)

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.list_principles(level=PrincipleLevel.FUNDAMENTAL)

        assert len(result) == 1
        assert result[0].level == PrincipleLevel.FUNDAMENTAL


@pytest.mark.asyncio
class TestDecisionOperations:
    """Testa operações CRUD de Decisions."""

    async def test_create_decision_success(self):
        """Deve criar decision com sucesso."""
        repo = KnowledgeBaseRepository()

        decision = Decision(
            id=uuid4(),
            action_plan_id=uuid4(),
            action_plan_name="Test Plan",
            status=DecisionStatus.APPROVED,
            aggregate_score=0.85,
            confidence=0.9,
            timestamp=datetime.utcnow(),
        )

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": str(decision.id)})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.create_decision(decision)

        assert result == decision.id

    async def test_create_decision_with_violations(self):
        """Deve criar relações VIOLATES se tem violated_principles."""
        repo = KnowledgeBaseRepository()

        principle_id = uuid4()
        decision = Decision(
            id=uuid4(),
            action_plan_id=uuid4(),
            action_plan_name="Violating Plan",
            status=DecisionStatus.REJECTED,
            aggregate_score=0.3,
            confidence=0.9,
            violated_principles=[principle_id],
            violation_severity=ViolationSeverity.CRITICAL,
            timestamp=datetime.utcnow(),
        )

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"id": str(decision.id)})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.create_decision(decision)

        assert result == decision.id
        # Should call run at least twice: once for create, once for violation link
        assert mock_session.run.call_count >= 2

    async def test_get_decision_found(self):
        """Deve retornar decision se encontrada."""
        repo = KnowledgeBaseRepository()

        decision_id = uuid4()
        plan_id = uuid4()
        mock_data = {
            "id": str(decision_id),
            "action_plan_id": str(plan_id),
            "action_plan_name": "Test Plan",
            "status": "approved",
            "aggregate_score": 0.85,
            "confidence": 0.9,
            "kantian_score": 0.9,
            "utilitarian_score": 0.8,
            "virtue_score": 0.85,
            "principialism_score": 0.9,
            "summary": "Approved",
            "detailed_reasoning": "All good",
            "violated_principles": [],
            "violation_severity": "none",
            "conflicts_detected": [],
            "resolution_method": "",
            "requires_human_review": False,
            "escalation_reason": "",
            "urgency": 0.5,
            "risk_level": 0.3,
            "novel_situation": False,
            "evaluation_duration_ms": 100.0,
            "timestamp": datetime.utcnow().isoformat(),
            "evaluator_version": "1.0.0",
        }

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value={"d": mock_data})

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.get_decision(decision_id)

        assert result is not None
        assert result.id == decision_id
        assert result.status == DecisionStatus.APPROVED

    async def test_get_decisions_by_plan(self):
        """Deve retornar histórico de decisões de um plano."""
        repo = KnowledgeBaseRepository()

        plan_id = uuid4()
        mock_data = [
            {"d": {
                "id": str(uuid4()),
                "action_plan_id": str(plan_id),
                "action_plan_name": "Test Plan",
                "status": "approved",
                "aggregate_score": 0.85,
                "confidence": 0.9,
                "kantian_score": None,
                "utilitarian_score": None,
                "virtue_score": None,
                "principialism_score": None,
                "summary": "",
                "detailed_reasoning": "",
                "violated_principles": [],
                "violation_severity": "none",
                "conflicts_detected": [],
                "resolution_method": "",
                "requires_human_review": False,
                "escalation_reason": "",
                "urgency": 0.5,
                "risk_level": 0.3,
                "novel_situation": False,
                "evaluation_duration_ms": 100.0,
                "timestamp": datetime.utcnow().isoformat(),
                "evaluator_version": "1.0.0",
            }},
        ]

        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data = AsyncMock(return_value=mock_data)

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_driver.session = Mock(return_value=mock_session)
        repo.driver = mock_driver

        result = await repo.get_decisions_by_plan(plan_id)

        assert len(result) == 1
        assert result[0].action_plan_id == plan_id


@pytest.mark.asyncio
class TestPrincipleQueryService:
    """Testa PrincipleQueryService."""

    async def test_get_principle_hierarchy(self):
        """Deve retornar hierarquia completa de princípios."""
        repo = Mock()

        # Mock list_principles to return principles of different levels
        principles = [
            Mock(level=PrincipleLevel.PRIMORDIAL, name="P1"),
            Mock(level=PrincipleLevel.ZERO, name="P2"),
            Mock(level=PrincipleLevel.FUNDAMENTAL, name="P3"),
            Mock(level=PrincipleLevel.DERIVED, name="P4"),
            Mock(level=PrincipleLevel.OPERATIONAL, name="P5"),
        ]

        repo.list_principles = AsyncMock(return_value=principles)

        service = PrincipleQueryService(repo)
        hierarchy = await service.get_principle_hierarchy()

        assert len(hierarchy[PrincipleLevel.PRIMORDIAL]) == 1
        assert len(hierarchy[PrincipleLevel.ZERO]) == 1
        assert len(hierarchy[PrincipleLevel.FUNDAMENTAL]) == 1
        assert len(hierarchy[PrincipleLevel.DERIVED]) == 1
        assert len(hierarchy[PrincipleLevel.OPERATIONAL]) == 1

    async def test_get_fundamental_laws(self):
        """Deve retornar leis fundamentais (Primordial + Zero + Fundamental)."""
        repo = Mock()

        primordial = [Mock(name="Primordial")]
        zero = [Mock(name="Zero")]
        fundamental = [Mock(name="Lei I"), Mock(name="Lei II")]

        repo.list_principles = AsyncMock(side_effect=[primordial, zero, fundamental])

        service = PrincipleQueryService(repo)
        laws = await service.get_fundamental_laws()

        assert len(laws) == 4  # 1 primordial + 1 zero + 2 fundamental
        assert repo.list_principles.call_count == 3


@pytest.mark.asyncio
class TestAuditTrailService:
    """Testa AuditTrailService."""

    async def test_log_decision(self):
        """Deve registrar decisão no audit trail."""
        repo = Mock()
        repo.create_decision = AsyncMock(return_value=uuid4())

        service = AuditTrailService(repo)

        decision = Mock()
        decision.id = uuid4()

        result = await service.log_decision(decision)

        assert isinstance(result, UUID)
        repo.create_decision.assert_called_once_with(decision)

    async def test_get_decision_history(self):
        """Deve retornar histórico de decisões."""
        repo = Mock()
        decisions = [Mock(id=uuid4()), Mock(id=uuid4())]
        repo.get_decisions_by_plan = AsyncMock(return_value=decisions)

        service = AuditTrailService(repo)

        plan_id = uuid4()
        history = await service.get_decision_history(plan_id)

        assert len(history) == 2
        repo.get_decisions_by_plan.assert_called_once_with(plan_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
