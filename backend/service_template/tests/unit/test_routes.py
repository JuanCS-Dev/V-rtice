"""
Unit tests for Presentation Layer - Routes
"""
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from service_template.application.dtos import CreateEntityDTO, UpdateEntityDTO
from service_template.domain.entities import ExampleEntity
from service_template.domain.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from service_template.infrastructure.database import Database
from service_template.presentation.routes import (
    create_entity,
    delete_entity,
    get_entity,
    get_repository,
    list_entities,
    update_entity,
)


@pytest.fixture
def sample_entity() -> ExampleEntity:
    """Create sample entity."""
    return ExampleEntity(
        id=uuid4(),
        name="Test Entity",
        description="Test Description",
        status="active",
    )


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get = AsyncMock()
    repo.list = AsyncMock()
    repo.count = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_database() -> Mock:
    """Create mock database."""
    db = Mock(spec=Database)
    session_mock = AsyncMock()
    db.session = Mock(return_value=session_mock)
    session_mock.__aenter__ = AsyncMock(return_value=session_mock)
    session_mock.__aexit__ = AsyncMock(return_value=None)
    return db


class TestGetRepository:
    """Tests for get_repository dependency."""

    async def test_get_repository_yields_repository(
        self, mock_database: Mock
    ) -> None:
        """Test get_repository yields repository instance."""
        gen = get_repository(mock_database)
        repo = await gen.__anext__()

        assert repo is not None
        mock_database.session.assert_called_once()


class TestCreateEntity:
    """Tests for create_entity endpoint."""

    async def test_create_entity_success(
        self, sample_entity: ExampleEntity, mock_repository: AsyncMock
    ) -> None:
        """Test successful entity creation."""
        dto = CreateEntityDTO(name="Test", description="Test Desc")

        with patch(
            "service_template.presentation.routes.CreateEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=sample_entity)
            mock_use_case_class.return_value = mock_use_case

            result = await create_entity(dto, mock_repository)

            assert result.name == sample_entity.name
            assert result.description == sample_entity.description
            mock_use_case.execute.assert_called_once_with(
                name=dto.name, description=dto.description
            )

    async def test_create_entity_already_exists(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test entity creation when entity already exists."""
        dto = CreateEntityDTO(name="Test", description="Test Desc")

        with patch(
            "service_template.presentation.routes.CreateEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(
                side_effect=EntityAlreadyExistsError("Test")
            )
            mock_use_case_class.return_value = mock_use_case

            with pytest.raises(HTTPException) as exc_info:
                await create_entity(dto, mock_repository)

            assert exc_info.value.status_code == 409


class TestGetEntity:
    """Tests for get_entity endpoint."""

    async def test_get_entity_success(
        self, sample_entity: ExampleEntity, mock_repository: AsyncMock
    ) -> None:
        """Test successful entity retrieval."""
        entity_id = sample_entity.id

        with patch(
            "service_template.presentation.routes.GetEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=sample_entity)
            mock_use_case_class.return_value = mock_use_case

            result = await get_entity(entity_id, mock_repository)

            assert result.id == entity_id
            assert result.name == sample_entity.name
            mock_use_case.execute.assert_called_once_with(entity_id)

    async def test_get_entity_not_found(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test entity retrieval when entity not found."""
        entity_id = uuid4()

        with patch(
            "service_template.presentation.routes.GetEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(
                side_effect=EntityNotFoundError(entity_id)
            )
            mock_use_case_class.return_value = mock_use_case

            with pytest.raises(HTTPException) as exc_info:
                await get_entity(entity_id, mock_repository)

            assert exc_info.value.status_code == 404


class TestListEntities:
    """Tests for list_entities endpoint."""

    async def test_list_entities_success(
        self, sample_entity: ExampleEntity, mock_repository: AsyncMock
    ) -> None:
        """Test successful entity listing."""
        entities = [sample_entity]
        mock_repository.count = AsyncMock(return_value=1)

        with patch(
            "service_template.presentation.routes.ListEntitiesUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=entities)
            mock_use_case_class.return_value = mock_use_case

            result = await list_entities(mock_repository, limit=100, offset=0)

            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].name == sample_entity.name
            assert result.limit == 100
            assert result.offset == 0
            mock_use_case.execute.assert_called_once_with(limit=100, offset=0)

    async def test_list_entities_empty(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test listing when no entities exist."""
        mock_repository.count = AsyncMock(return_value=0)

        with patch(
            "service_template.presentation.routes.ListEntitiesUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=[])
            mock_use_case_class.return_value = mock_use_case

            result = await list_entities(mock_repository, limit=100, offset=0)

            assert result.total == 0
            assert len(result.items) == 0


class TestUpdateEntity:
    """Tests for update_entity endpoint."""

    async def test_update_entity_success(
        self, sample_entity: ExampleEntity, mock_repository: AsyncMock
    ) -> None:
        """Test successful entity update."""
        entity_id = sample_entity.id
        dto = UpdateEntityDTO(name="Updated", description="Updated Desc")

        with patch(
            "service_template.presentation.routes.UpdateEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=sample_entity)
            mock_use_case_class.return_value = mock_use_case

            result = await update_entity(entity_id, dto, mock_repository)

            assert result.id == entity_id
            mock_use_case.execute.assert_called_once_with(
                entity_id=entity_id,
                name=dto.name,
                description=dto.description,
            )

    async def test_update_entity_not_found(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test entity update when entity not found."""
        entity_id = uuid4()
        dto = UpdateEntityDTO(name="Updated", description="Updated Desc")

        with patch(
            "service_template.presentation.routes.UpdateEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(
                side_effect=EntityNotFoundError(entity_id)
            )
            mock_use_case_class.return_value = mock_use_case

            with pytest.raises(HTTPException) as exc_info:
                await update_entity(entity_id, dto, mock_repository)

            assert exc_info.value.status_code == 404

    async def test_update_entity_name_conflict(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test entity update when new name conflicts."""
        entity_id = uuid4()
        dto = UpdateEntityDTO(name="Existing", description="Updated Desc")

        with patch(
            "service_template.presentation.routes.UpdateEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(
                side_effect=EntityAlreadyExistsError("Existing")
            )
            mock_use_case_class.return_value = mock_use_case

            with pytest.raises(HTTPException) as exc_info:
                await update_entity(entity_id, dto, mock_repository)

            assert exc_info.value.status_code == 409


class TestDeleteEntity:
    """Tests for delete_entity endpoint."""

    async def test_delete_entity_success(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test successful entity deletion."""
        entity_id = uuid4()

        with patch(
            "service_template.presentation.routes.DeleteEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(return_value=None)
            mock_use_case_class.return_value = mock_use_case

            result = await delete_entity(entity_id, mock_repository)

            assert result is None
            mock_use_case.execute.assert_called_once_with(entity_id)

    async def test_delete_entity_not_found(
        self, mock_repository: AsyncMock
    ) -> None:
        """Test entity deletion when entity not found."""
        entity_id = uuid4()

        with patch(
            "service_template.presentation.routes.DeleteEntityUseCase"
        ) as mock_use_case_class:
            mock_use_case = AsyncMock()
            mock_use_case.execute = AsyncMock(
                side_effect=EntityNotFoundError(entity_id)
            )
            mock_use_case_class.return_value = mock_use_case

            with pytest.raises(HTTPException) as exc_info:
                await delete_entity(entity_id, mock_repository)

            assert exc_info.value.status_code == 404
