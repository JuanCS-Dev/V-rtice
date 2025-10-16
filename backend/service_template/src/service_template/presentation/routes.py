"""
Presentation Layer - FastAPI Routes

HTTP endpoints for the service.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..application.dtos import CreateEntityDTO, EntityDTO, PaginatedEntitiesDTO, UpdateEntityDTO
from ..application.use_cases import (
    CreateEntityUseCase,
    DeleteEntityUseCase,
    GetEntityUseCase,
    ListEntitiesUseCase,
    UpdateEntityUseCase,
)
from ..domain.exceptions import EntityAlreadyExistsError, EntityNotFoundError
from ..infrastructure.database import Database
from ..infrastructure.repositories import SQLAlchemyExampleRepository
from .dependencies import get_database

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])


async def get_repository(
    db: Annotated[Database, Depends(get_database)]
) -> SQLAlchemyExampleRepository:
    """Get repository dependency."""
    async with db.session() as session:
        yield SQLAlchemyExampleRepository(session)


@router.post(
    "/",
    response_model=EntityDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create entity",
)
async def create_entity(
    dto: CreateEntityDTO,
    repo: Annotated[SQLAlchemyExampleRepository, Depends(get_repository)],
) -> EntityDTO:
    """Create new entity."""
    try:
        use_case = CreateEntityUseCase(repo)
        entity = await use_case.execute(name=dto.name, description=dto.description)
        return EntityDTO.model_validate(entity)
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/{entity_id}",
    response_model=EntityDTO,
    summary="Get entity by ID",
)
async def get_entity(
    entity_id: UUID,
    repo: Annotated[SQLAlchemyExampleRepository, Depends(get_repository)],
) -> EntityDTO:
    """Get entity by ID."""
    try:
        use_case = GetEntityUseCase(repo)
        entity = await use_case.execute(entity_id)
        return EntityDTO.model_validate(entity)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/",
    response_model=PaginatedEntitiesDTO,
    summary="List entities",
)
async def list_entities(
    repo: Annotated[SQLAlchemyExampleRepository, Depends(get_repository)],
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> PaginatedEntitiesDTO:
    """List entities with pagination."""
    use_case = ListEntitiesUseCase(repo)
    entities = await use_case.execute(limit=limit, offset=offset)
    total = await repo.count()

    return PaginatedEntitiesDTO(
        items=[EntityDTO.model_validate(e) for e in entities],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/{entity_id}",
    response_model=EntityDTO,
    summary="Update entity",
)
async def update_entity(
    entity_id: UUID,
    dto: UpdateEntityDTO,
    repo: Annotated[SQLAlchemyExampleRepository, Depends(get_repository)],
) -> EntityDTO:
    """Update entity."""
    try:
        use_case = UpdateEntityUseCase(repo)
        entity = await use_case.execute(
            entity_id=entity_id,
            name=dto.name,
            description=dto.description,
        )
        return EntityDTO.model_validate(entity)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EntityAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete(
    "/{entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete entity",
)
async def delete_entity(
    entity_id: UUID,
    repo: Annotated[SQLAlchemyExampleRepository, Depends(get_repository)],
) -> None:
    """Delete entity."""
    try:
        use_case = DeleteEntityUseCase(repo)
        await use_case.execute(entity_id)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
