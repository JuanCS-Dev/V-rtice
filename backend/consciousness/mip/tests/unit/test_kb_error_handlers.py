"""
Testes para error handlers do Knowledge Base - MIP FASE 6
Objetivo: Cobrir as 10 linhas faltantes para atingir 95%+ coverage

Autor: Claude Code + Juan Carlos
Lei Governante: Constituição Vértice v2.7
Padrão: PADRÃO PAGANI ABSOLUTO (100%)
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime

from mip.infrastructure.knowledge_base import (
    KnowledgeBaseRepository,
)
from mip.infrastructure.knowledge_models import (
    Principle,
    Decision,
    PrincipleLevel,
    DecisionStatus,
    ViolationSeverity,
)


class TestKnowledgeBaseErrorHandlers:
    """Testa error handlers e defensive code paths."""

    @pytest.mark.asyncio
    async def test_get_principle_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()
        # Não chama initialize()

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.get_principle(uuid4())

    @pytest.mark.asyncio
    async def test_get_principle_by_name_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.get_principle_by_name("Lei Zero")

    @pytest.mark.asyncio
    async def test_get_principle_by_name_returns_none_when_not_found(self):
        """Deve retornar None se princípio não existe."""
        from unittest.mock import AsyncMock

        repo = KnowledgeBaseRepository()
        repo.driver = AsyncMock()
        repo._initialized = True

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value=None)  # Not found

        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        repo.driver.session = lambda database: mock_session

        result = await repo.get_principle_by_name("NonExistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_principles_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.list_principles()

    @pytest.mark.asyncio
    async def test_create_decision_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()

        decision = Decision(
            id=uuid4(),
            action_plan_id=uuid4(),
            action_plan_name="Test",
            status=DecisionStatus.APPROVED,
            aggregate_score=0.8,
            confidence=0.9,
            timestamp=datetime.utcnow(),
        )

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.create_decision(decision)

    @pytest.mark.asyncio
    async def test_get_decision_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.get_decision(uuid4())

    @pytest.mark.asyncio
    async def test_get_decision_returns_none_when_not_found(self):
        """Deve retornar None se decisão não existe."""
        from unittest.mock import AsyncMock

        repo = KnowledgeBaseRepository()
        repo.driver = AsyncMock()
        repo._initialized = True

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.single = AsyncMock(return_value=None)  # Not found

        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        repo.driver.session = lambda database: mock_session

        result = await repo.get_decision(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_decisions_by_plan_raises_when_not_initialized(self):
        """Deve lançar RuntimeError se driver não inicializado."""
        repo = KnowledgeBaseRepository()

        with pytest.raises(RuntimeError, match="not initialized"):
            await repo.get_decisions_by_plan(uuid4())

    @pytest.mark.asyncio
    async def test_create_principle_hierarchy_skips_when_no_driver(self):
        """Deve retornar early se driver é None."""
        repo = KnowledgeBaseRepository()
        # driver is None by default

        # Should not raise, just return early
        await repo._create_principle_hierarchy(uuid4(), uuid4())

        # No assertion needed - just ensuring no exception

    @pytest.mark.asyncio
    async def test_link_decision_violations_skips_when_no_driver(self):
        """Deve retornar early se driver é None."""
        repo = KnowledgeBaseRepository()

        decision = Decision(
            id=uuid4(),
            action_plan_id=uuid4(),
            action_plan_name="Test",
            status=DecisionStatus.REJECTED,
            aggregate_score=0.2,
            confidence=0.9,
            violated_principles=[uuid4()],
            violation_severity=ViolationSeverity.HIGH,
            timestamp=datetime.utcnow(),
        )

        # Should not raise, just return early
        await repo._link_decision_violations(decision)

        # No assertion needed - just ensuring no exception
