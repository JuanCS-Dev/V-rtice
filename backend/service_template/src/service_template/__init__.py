"""Service Template - Clean Architecture for Vértice MAXIMUS services."""

from .application import (
    CreateEntityDTO,
    CreateEntityUseCase,
    DeleteEntityUseCase,
    EntityDTO,
    GetEntityUseCase,
    ListEntitiesUseCase,
    UpdateEntityDTO,
    UpdateEntityUseCase,
)
from .domain import (
    Email,
    Entity,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    ExampleEntity,
    ExampleRepository,
    Status,
)
from .infrastructure import Database, ExampleModel, Settings, get_settings
from .presentation import create_app

__version__ = "1.0.0"

__all__ = [
    # Application
    "CreateEntityDTO",
    "UpdateEntityDTO",
    "EntityDTO",
    "CreateEntityUseCase",
    "GetEntityUseCase",
    "UpdateEntityUseCase",
    "DeleteEntityUseCase",
    "ListEntitiesUseCase",
    # Domain
    "Entity",
    "ExampleEntity",
    "ExampleRepository",
    "Email",
    "Status",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    # Infrastructure
    "Settings",
    "get_settings",
    "Database",
    "ExampleModel",
    # Presentation
    "create_app",
    # Version
    "__version__",
]
