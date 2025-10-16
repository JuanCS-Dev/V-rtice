"""Domain Layer - Clean Architecture domain models and business logic."""

from .entities import Entity, ExampleEntity
from .events import DomainEvent, EntityCreated, EntityDeleted, EntityUpdated
from .exceptions import (
    DomainException,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidEntityStateError,
    ValidationError,
)
from .repositories import ExampleRepository
from .value_objects import Email, Status

__all__ = [
    # Entities
    "Entity",
    "ExampleEntity",
    # Value Objects
    "Email",
    "Status",
    # Repositories
    "ExampleRepository",
    # Events
    "DomainEvent",
    "EntityCreated",
    "EntityUpdated",
    "EntityDeleted",
    # Exceptions
    "DomainException",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "InvalidEntityStateError",
    "ValidationError",
]
