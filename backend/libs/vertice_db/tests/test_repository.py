"""Tests for vertice_db.repository module."""

import pytest
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from vertice_db import Base, BaseRepository


class User(Base):
    """Test User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100))


@pytest.mark.asyncio()
async def test_repository_create(db_session):
    """Test create operation."""
    repo = BaseRepository(User, db_session)
    user = await repo.create(name="John", email="john@test.com")

    assert user.id is not None
    assert user.name == "John"
    assert user.email == "john@test.com"


@pytest.mark.asyncio()
async def test_repository_get(db_session):
    """Test get operation."""
    repo = BaseRepository(User, db_session)
    user = await repo.create(name="Jane", email="jane@test.com")

    fetched = await repo.get(user.id)
    assert fetched is not None
    assert fetched.name == "Jane"


@pytest.mark.asyncio()
async def test_repository_get_nonexistent(db_session):
    """Test get returns None for nonexistent ID."""
    repo = BaseRepository(User, db_session)
    result = await repo.get(9999)
    assert result is None


@pytest.mark.asyncio()
async def test_repository_list(db_session):
    """Test list operation."""
    repo = BaseRepository(User, db_session)
    await repo.create(name="User1", email="user1@test.com")
    await repo.create(name="User2", email="user2@test.com")

    users = await repo.list()
    assert len(users) == 2


@pytest.mark.asyncio()
async def test_repository_update(db_session):
    """Test update operation."""
    repo = BaseRepository(User, db_session)
    user = await repo.create(name="Old Name", email="old@test.com")

    updated = await repo.update(user.id, name="New Name")
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.email == "old@test.com"


@pytest.mark.asyncio()
async def test_repository_update_nonexistent(db_session):
    """Test update returns None for nonexistent ID."""
    repo = BaseRepository(User, db_session)
    result = await repo.update(9999, name="Test")
    assert result is None


@pytest.mark.asyncio()
async def test_repository_delete(db_session):
    """Test delete operation."""
    repo = BaseRepository(User, db_session)
    user = await repo.create(name="Delete Me", email="delete@test.com")

    deleted = await repo.delete(user.id)
    assert deleted is True

    fetched = await repo.get(user.id)
    assert fetched is None


@pytest.mark.asyncio()
async def test_repository_delete_nonexistent(db_session):
    """Test delete returns False for nonexistent ID."""
    repo = BaseRepository(User, db_session)
    result = await repo.delete(9999)
    assert result is False
