"""
Domain Layer - Value Objects

Immutable domain concepts without identity.
"""
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Email:
    """Email value object with validation."""

    value: str
    PATTERN: ClassVar[str] = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    def __post_init__(self) -> None:
        """Validate email format."""
        import re

        if not re.match(self.PATTERN, self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    def __str__(self) -> str:
        """String representation."""
        return self.value


@dataclass(frozen=True)
class Status:
    """Status value object with valid states."""

    value: str
    VALID_STATES: ClassVar[set[str]] = {"active", "inactive", "pending", "deleted"}

    def __post_init__(self) -> None:
        """Validate status value."""
        if self.value not in self.VALID_STATES:
            raise ValueError(
                f"Invalid status: {self.value}. Must be one of {self.VALID_STATES}"
            )

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def is_active(self) -> bool:
        """Check if status is active."""
        return self.value == "active"
