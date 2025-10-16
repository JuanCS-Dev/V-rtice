"""
Domain Layer - Custom Exceptions

Domain-specific exceptions.
"""


class DomainException(Exception):
    """Base exception for domain layer."""

    pass


class EntityNotFoundError(DomainException):
    """Entity not found in repository."""

    def __init__(self, entity_id: str, entity_type: str = "Entity") -> None:
        self.entity_id = entity_id
        self.entity_type = entity_type
        super().__init__(f"{entity_type} not found: {entity_id}")


class EntityAlreadyExistsError(DomainException):
    """Entity already exists."""

    def __init__(self, identifier: str, entity_type: str = "Entity") -> None:
        self.identifier = identifier
        self.entity_type = entity_type
        super().__init__(f"{entity_type} already exists: {identifier}")


class InvalidEntityStateError(DomainException):
    """Entity is in invalid state for operation."""

    def __init__(self, entity_id: str, operation: str, current_state: str) -> None:
        self.entity_id = entity_id
        self.operation = operation
        self.current_state = current_state
        super().__init__(
            f"Cannot {operation} entity {entity_id}: current state is {current_state}"
        )


class ValidationError(DomainException):
    """Domain validation failed."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error on {field}: {message}")
