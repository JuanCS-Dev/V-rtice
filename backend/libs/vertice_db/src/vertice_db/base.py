"""SQLAlchemy declarative base for all Vértice models.

This module provides the base class that all database models must inherit from.
It's separated from mixins to maintain clean architecture and avoid circular imports.

Example:
-------
    Basic model::

        from vertice_db.base import Base
        from sqlalchemy.orm import Mapped, mapped_column

        class User(Base):
            __tablename__ = "users"

            id: Mapped[int] = mapped_column(primary_key=True)
            username: Mapped[str] = mapped_column(unique=True)
            email: Mapped[str]

    With mixins::

        from vertice_db.base import Base
        from vertice_db.models import TimestampMixin

        class Article(Base, TimestampMixin):
            __tablename__ = "articles"

            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]
            content: Mapped[str]
            # created_at and updated_at from TimestampMixin

Note:
----
    - All models MUST inherit from Base
    - Base uses SQLAlchemy 2.0 declarative style
    - Use Mapped[] type hints for columns

"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all SQLAlchemy models.

    All database models in the Vértice ecosystem must inherit from this class.
    It provides the foundation for SQLAlchemy's ORM functionality.

    Attributes:
    ----------
        __tablename__: Must be defined in child classes.
        __table_args__: Optional table configuration (indexes, constraints).

    Example:
    -------
        >>> from vertice_db.base import Base
        >>> from sqlalchemy.orm import Mapped, mapped_column
        >>>
        >>> class Product(Base):
        >>>     __tablename__ = "products"
        >>>     __table_args__ = {"schema": "public"}
        >>>
        >>>     id: Mapped[int] = mapped_column(primary_key=True)
        >>>     name: Mapped[str] = mapped_column(index=True)
        >>>     price: Mapped[float]

    Note:
    ----
        - Uses SQLAlchemy 2.0 declarative syntax
        - Type-safe with Mapped[] annotations
        - Supports all SQLAlchemy features (relationships, indexes, constraints)
    """

