"""SQLAlchemy model mixins for common patterns.

This module provides reusable mixins for database models, such as
timestamps, soft deletes, and utility methods.

Example:
-------
    Using TimestampMixin::

        from vertice_db.base import Base
        from vertice_db.models import TimestampMixin

        class Article(Base, TimestampMixin):
            __tablename__ = "articles"

            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]
            # created_at and updated_at automatically added

    Using SoftDeleteMixin::

        from vertice_db.models import SoftDeleteMixin

        class User(Base, TimestampMixin, SoftDeleteMixin):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str]
            # deleted_at automatically added

Note:
----
    - Mixins should be used via multiple inheritance
    - Order matters: Base should be first in inheritance chain
    - All mixins are production-ready with proper type hints

"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin for automatic created_at and updated_at timestamps.

    Adds two timestamp columns that are automatically managed:
    - created_at: Set once when row is created
    - updated_at: Updated automatically on every modification

    Example:
    -------
        >>> class User(Base, TimestampMixin):
        >>>     __tablename__ = "users"
        >>>
        >>>     id: Mapped[int] = mapped_column(primary_key=True)
        >>>     username: Mapped[str]
        >>>
        >>> # Usage
        >>> user = User(username="alice")
        >>> await session.add(user)
        >>> await session.commit()
        >>> # user.created_at and user.updated_at are set automatically

    Note:
    ----
        - Uses database-level functions (func.now()) for consistency
        - Timezone-aware timestamps (DateTime(timezone=True))
        - updated_at uses onupdate trigger
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when record was last updated",
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Automatically handles datetime serialization to ISO format.

        Returns:
        -------
            Dictionary with column names as keys.

        Example:
        -------
            >>> user = User(username="alice")
            >>> user_dict = user.to_dict()
            >>> # {"id": 1, "username": "alice", "created_at": "2025-10-16T...", ...}
        """
        result: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore[attr-defined]
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
        return result


class SoftDeleteMixin:
    """Mixin for soft delete functionality.

    Adds a deleted_at column for soft deletes. Records are never physically
    deleted, just marked with a deletion timestamp.

    Example:
    -------
        >>> class User(Base, TimestampMixin, SoftDeleteMixin):
        >>>     __tablename__ = "users"
        >>>
        >>>     id: Mapped[int] = mapped_column(primary_key=True)
        >>>     username: Mapped[str]
        >>>
        >>> # Soft delete
        >>> user.soft_delete()
        >>> await session.commit()
        >>>
        >>> # Check if deleted
        >>> if user.is_deleted():
        >>>     print("User was deleted")
        >>>
        >>> # Restore
        >>> user.restore()
        >>> await session.commit()

    Note:
    ----
        - Queries must filter deleted_at IS NULL to exclude deleted records
        - Use with repository pattern for automatic filtering
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        comment="Timestamp when record was soft-deleted (NULL = not deleted)",
    )

    def soft_delete(self) -> None:
        """Mark record as deleted.

        Sets deleted_at to current timestamp.
        """
        self.deleted_at = datetime.now()

    def restore(self) -> None:
        """Restore a soft-deleted record.

        Sets deleted_at back to None.
        """
        self.deleted_at = None

    def is_deleted(self) -> bool:
        """Check if record is soft-deleted.

        Returns
        -------
            True if deleted_at is set, False otherwise.
        """
        return self.deleted_at is not None
