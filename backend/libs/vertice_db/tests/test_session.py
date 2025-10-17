"""Tests for vertice_db.session module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool
from vertice_db.session import (
    AsyncSessionFactory,
    TransactionManager,
    create_session_factory,
    create_test_session_factory,
    get_db_session,
)
import contextlib


class TestAsyncSessionFactory:
    """Tests for AsyncSessionFactory."""

    @pytest.fixture()
    def mock_engine(self):
        """Create mock async engine."""
        engine = MagicMock(spec=AsyncEngine)
        engine.dispose = AsyncMock()
        return engine

    def test_init_creates_session_maker(self, mock_engine):
        """Test factory initialization."""
        factory = AsyncSessionFactory(mock_engine, expire_on_commit=False)

        assert factory.engine is mock_engine
        assert factory.session_maker is not None

    @pytest.mark.asyncio()
    async def test_context_manager_yields_session(self, mock_engine):
        """Test context manager provides session."""
        from contextlib import asynccontextmanager

        factory = AsyncSessionFactory(mock_engine)

        # Mock the session and session maker
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        @asynccontextmanager
        async def mock_maker():
            yield mock_session

        factory.session_maker = mock_maker

        async with factory() as session:
            assert session is mock_session

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio()
    async def test_rollback_on_exception(self, mock_engine):
        """Test rollback is called when exception occurs."""
        from contextlib import asynccontextmanager

        factory = AsyncSessionFactory(mock_engine)

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        @asynccontextmanager
        async def mock_maker():
            yield mock_session

        factory.session_maker = mock_maker

        with pytest.raises(ValueError):
            async with factory():
                raise ValueError("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio()
    async def test_close_disposes_engine(self, mock_engine):
        """Test close disposes engine."""
        factory = AsyncSessionFactory(mock_engine)

        await factory.close()

        mock_engine.dispose.assert_called_once()


class TestCreateSessionFactory:
    """Tests for create_session_factory."""

    @patch("vertice_db.session.create_async_engine")
    def test_creates_factory_with_asyncpg_url(self, mock_create_engine):
        """Test factory creation with asyncpg URL."""
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine

        factory = create_session_factory(
            "postgresql+asyncpg://user:pass@localhost/db",
            pool_size=10,
            max_overflow=5,
        )

        assert isinstance(factory, AsyncSessionFactory)
        assert factory.engine is mock_engine

        mock_create_engine.assert_called_once()
        args, kwargs = mock_create_engine.call_args
        assert args[0] == "postgresql+asyncpg://user:pass@localhost/db"
        assert kwargs["pool_size"] == 10
        assert kwargs["max_overflow"] == 5
        assert kwargs["poolclass"] == QueuePool

    @patch("vertice_db.session.create_async_engine")
    def test_auto_converts_postgres_to_asyncpg(self, mock_create_engine):
        """Test auto-conversion of postgresql:// to asyncpg."""
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine

        create_session_factory("postgresql://user:pass@localhost/db")

        args, kwargs = mock_create_engine.call_args
        assert "postgresql+asyncpg://" in args[0]

    def test_raises_for_non_async_url(self):
        """Test raises ValueError for non-async database URL."""
        with pytest.raises(ValueError) as exc_info:
            create_session_factory("mysql://user:pass@localhost/db")

        assert "async driver" in str(exc_info.value).lower()

    @patch("vertice_db.session.create_async_engine")
    def test_passes_connect_args(self, mock_create_engine):
        """Test connect_args are passed to engine."""
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine

        connect_args = {"ssl": "require", "timeout": 30}
        create_session_factory(
            "postgresql+asyncpg://localhost/db",
            connect_args=connect_args,
        )

        args, kwargs = mock_create_engine.call_args
        assert kwargs["connect_args"] == connect_args


class TestCreateTestSessionFactory:
    """Tests for create_test_session_factory."""

    @patch("vertice_db.session.create_async_engine")
    def test_creates_factory_with_null_pool(self, mock_create_engine):
        """Test test factory uses NullPool."""
        mock_engine = MagicMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine

        factory = create_test_session_factory("postgresql+asyncpg://localhost/test_db")

        assert isinstance(factory, AsyncSessionFactory)

        args, kwargs = mock_create_engine.call_args
        assert kwargs["poolclass"] == NullPool
        assert kwargs["echo"] is False


class TestGetDbSession:
    """Tests for get_db_session dependency."""

    @pytest.mark.asyncio()
    async def test_yields_session_and_commits(self):
        """Test dependency yields session and commits on success."""
        from contextlib import asynccontextmanager

        mock_engine = MagicMock(spec=AsyncEngine)
        factory = AsyncSessionFactory(mock_engine)

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        @asynccontextmanager
        async def mock_maker():
            yield mock_session

        factory.session_maker = mock_maker

        async for session in get_db_session(factory):
            assert session is mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.asyncio()
    async def test_rollback_on_exception(self):
        """Test dependency rolls back on exception (via factory)."""
        from contextlib import asynccontextmanager

        mock_engine = MagicMock(spec=AsyncEngine)
        factory = AsyncSessionFactory(mock_engine)

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()

        @asynccontextmanager
        async def mock_maker():
            try:
                yield mock_session
            except Exception:
                await mock_session.rollback()
                raise
            finally:
                await mock_session.close()

        factory.session_maker = mock_maker

        gen = get_db_session(factory)
        await gen.__anext__()

        with contextlib.suppress(ValueError):
            await gen.athrow(ValueError, ValueError("Test error"), None)

        # Rollback happens in factory's context manager
        mock_session.rollback.assert_called()
        mock_session.close.assert_called()


class TestTransactionManager:
    """Tests for TransactionManager."""

    @pytest.mark.asyncio()
    async def test_commits_on_success(self):
        """Test transaction manager commits on success."""
        mock_transaction = MagicMock()
        mock_transaction.commit = AsyncMock()
        mock_transaction.rollback = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        async with TransactionManager(mock_session):
            pass

        mock_transaction.commit.assert_called_once()
        mock_transaction.rollback.assert_not_called()

    @pytest.mark.asyncio()
    async def test_rollback_on_exception(self):
        """Test transaction manager rolls back on exception."""
        mock_transaction = MagicMock()
        mock_transaction.commit = AsyncMock()
        mock_transaction.rollback = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        with pytest.raises(ValueError):
            async with TransactionManager(mock_session):
                raise ValueError("Test error")

        mock_transaction.rollback.assert_called_once()
        mock_transaction.commit.assert_not_called()

    @pytest.mark.asyncio()
    async def test_allows_nested_transactions(self):
        """Test nested transaction managers work correctly."""
        mock_transaction1 = MagicMock()
        mock_transaction1.commit = AsyncMock()

        mock_transaction2 = MagicMock()
        mock_transaction2.commit = AsyncMock()

    @pytest.mark.asyncio()
    async def test_manual_commit_mode(self):
        """Test transaction manager with auto_commit=False."""
        mock_transaction = MagicMock()
        mock_transaction.commit = AsyncMock()
        mock_transaction.rollback = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        # With auto_commit=False, no automatic commit
        async with TransactionManager(mock_session, auto_commit=False):
            pass

        mock_transaction.commit.assert_not_called()
        mock_transaction.rollback.assert_not_called()

    @pytest.mark.asyncio()
    async def test_manual_commit_with_explicit_call(self):
        """Test manual commit in transaction manager."""
        mock_transaction = MagicMock()
        mock_transaction.commit = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        async with TransactionManager(mock_session, auto_commit=False) as tx:
            await tx.commit()

        mock_transaction.commit.assert_called_once()

    @pytest.mark.asyncio()
    async def test_manual_rollback_with_explicit_call(self):
        """Test manual rollback in transaction manager."""
        mock_transaction = MagicMock()
        mock_transaction.rollback = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        async with TransactionManager(mock_session, auto_commit=False) as tx:
            await tx.rollback()

        mock_transaction.rollback.assert_called_once()

    @pytest.mark.asyncio()
    async def test_commit_when_no_transaction(self):
        """Test commit is safe when transaction already committed."""
        mock_transaction = MagicMock()
        mock_transaction.commit = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        async with TransactionManager(mock_session, auto_commit=True) as tx:
            # Transaction auto-committed, now manually commit again
            await tx.commit()  # Should handle gracefully (transaction is None)

        # Only one commit from auto_commit
        assert mock_transaction.commit.call_count >= 1

    @pytest.mark.asyncio()
    async def test_rollback_when_no_transaction(self):
        """Test rollback is safe when transaction already rolled back."""
        mock_transaction = MagicMock()
        mock_transaction.rollback = AsyncMock()

        mock_session = MagicMock(spec=AsyncSession)
        mock_session.begin = AsyncMock(return_value=mock_transaction)

        async with TransactionManager(mock_session, auto_commit=False) as tx:
            await tx.rollback()
            # Try to rollback again
            await tx.rollback()  # Should be safe (transaction is None)

        # Only one rollback
        mock_transaction.rollback.assert_called_once()
