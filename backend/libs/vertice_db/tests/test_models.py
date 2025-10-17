"""Tests for vertice_db.models module."""

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from vertice_db import Base, SoftDeleteMixin, TimestampMixin


class UserModel(Base, TimestampMixin):
    """Test model."""

    __tablename__ = "user_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class SoftDeleteUserModel(Base, TimestampMixin, SoftDeleteMixin):
    """Test model with soft delete."""

    __tablename__ = "soft_delete_user_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


def test_base_model_exists():
    """Test Base model exists."""
    assert Base is not None


def test_timestamp_mixin_has_fields():
    """Test TimestampMixin has created_at and updated_at."""
    model = UserModel(id=1, name="test")
    assert hasattr(model, "created_at")
    assert hasattr(model, "updated_at")


def test_to_dict_converts_model():
    """Test to_dict method."""
    model = UserModel(id=1, name="test")
    model.created_at = datetime(2024, 1, 1, 12, 0, 0)
    model.updated_at = datetime(2024, 1, 1, 12, 0, 0)

    result = model.to_dict()
    assert result["id"] == 1
    assert result["name"] == "test"
    assert isinstance(result["created_at"], str)
    assert isinstance(result["updated_at"], str)


def test_soft_delete_mixin_has_deleted_at():
    """Test SoftDeleteMixin has deleted_at field."""
    model = SoftDeleteUserModel(id=1, name="test")
    assert hasattr(model, "deleted_at")
    assert model.deleted_at is None


def test_soft_delete_marks_as_deleted():
    """Test soft_delete marks record as deleted."""
    model = SoftDeleteUserModel(id=1, name="test")
    assert not model.is_deleted()

    model.soft_delete()
    assert model.is_deleted()
    assert isinstance(model.deleted_at, datetime)


def test_restore_unmarks_deletion():
    """Test restore removes deletion mark."""
    model = SoftDeleteUserModel(id=1, name="test")
    model.soft_delete()
    assert model.is_deleted()

    model.restore()
    assert not model.is_deleted()
    assert model.deleted_at is None


def test_is_deleted_returns_correct_status():
    """Test is_deleted returns correct boolean status."""
    model = SoftDeleteUserModel(id=1, name="test")

    # Not deleted initially
    assert model.is_deleted() is False

    # Deleted after soft_delete
    model.soft_delete()
    assert model.is_deleted() is True

    # Not deleted after restore
    model.restore()
    assert model.is_deleted() is False
