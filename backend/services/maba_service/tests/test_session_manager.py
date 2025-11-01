"""Tests for Session Manager - Auto-timeout and cleanup."""

import asyncio
from datetime import datetime, timedelta

from core.session_manager import BrowserSession, SessionManager
import pytest


@pytest.fixture
async def manager():
    """Create session manager with short timeouts for testing."""
    mgr = SessionManager(
        idle_timeout_seconds=2,  # 2 seconds for fast tests
        cleanup_interval_seconds=1,  # 1 second cleanup
        max_session_age_seconds=5,  # 5 seconds max age
    )
    await mgr.start()
    yield mgr
    await mgr.stop()


class TestSessionCreation:
    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """GIVEN: SessionManager initialized.

        WHEN: create_session called
        THEN: Returns session ID and session is active.
        """
        session_id = await manager.create_session(
            browser_instance_id="browser-1", metadata={"user": "test"}
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID format

        session = await manager.get_session(session_id)
        assert session is not None
        assert session.session_id == session_id
        assert session.browser_instance_id == "browser-1"
        assert session.is_active is True
        assert session.metadata["user"] == "test"

    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self, manager):
        """GIVEN: SessionManager initialized.

        WHEN: Multiple sessions created
        THEN: All sessions are tracked independently.
        """
        session1 = await manager.create_session("browser-1")
        session2 = await manager.create_session("browser-2")

        assert session1 != session2

        sessions = await manager.list_sessions()
        assert len(sessions) == 2


class TestActivityTracking:
    @pytest.mark.asyncio
    async def test_update_activity(self, manager):
        """GIVEN: Active session.

        WHEN: update_activity called
        THEN: Last activity timestamp updated.
        """
        session_id = await manager.create_session("browser-1")

        # Get initial activity time
        session1 = await manager.get_session(session_id)
        assert session1 is not None
        initial_activity = session1.last_activity

        # Wait a bit
        await asyncio.sleep(0.1)

        # Update activity
        updated = await manager.update_activity(session_id)
        assert updated is True

        # Verify timestamp changed
        session2 = await manager.get_session(session_id)
        assert session2 is not None
        assert session2.last_activity > initial_activity

    @pytest.mark.asyncio
    async def test_update_nonexistent_session(self, manager):
        """GIVEN: No session exists.

        WHEN: update_activity called with invalid ID
        THEN: Returns False.
        """
        updated = await manager.update_activity("nonexistent")
        assert updated is False


class TestSessionClosure:
    @pytest.mark.asyncio
    async def test_close_session(self, manager):
        """GIVEN: Active session.

        WHEN: close_session called
        THEN: Session marked inactive.
        """
        session_id = await manager.create_session("browser-1")

        closed = await manager.close_session(session_id)
        assert closed is True

        # Session no longer retrievable
        session = await manager.get_session(session_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_close_already_closed(self, manager):
        """GIVEN: Already closed session.

        WHEN: close_session called again
        THEN: Returns False.
        """
        session_id = await manager.create_session("browser-1")
        await manager.close_session(session_id)

        # Try closing again
        closed = await manager.close_session(session_id)
        assert closed is False


class TestIdleTimeout:
    @pytest.mark.asyncio
    async def test_idle_timeout_cleanup(self, manager):
        """GIVEN: Session idle for longer than timeout.

        WHEN: Cleanup runs
        THEN: Session auto-closed.
        """
        session_id = await manager.create_session("browser-1")

        # Verify session active
        session = await manager.get_session(session_id)
        assert session is not None

        # Wait for idle timeout (2s) + cleanup interval (1s)
        await asyncio.sleep(3.5)

        # Session should be auto-closed
        session = await manager.get_session(session_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_activity_prevents_timeout(self, manager):
        """GIVEN: Session with regular activity.

        WHEN: Activity updated before timeout
        THEN: Session remains active.
        """
        session_id = await manager.create_session("browser-1")

        # Update activity every second for 4 seconds
        for _ in range(4):
            await asyncio.sleep(1)
            await manager.update_activity(session_id)

        # Session should still be active (idle timeout is 2s, but we updated it)
        session = await manager.get_session(session_id)
        assert session is not None


class TestMaxAge:
    @pytest.mark.asyncio
    async def test_max_age_timeout(self, manager):
        """GIVEN: Session older than max age.

        WHEN: Cleanup runs
        THEN: Session closed even with activity.
        """
        session_id = await manager.create_session("browser-1")

        # Keep updating activity to prevent idle timeout
        # But wait for max age (5s)
        for _ in range(6):
            await asyncio.sleep(1)
            await manager.update_activity(session_id)

        # Session should be closed due to max age
        session = await manager.get_session(session_id)
        assert session is None


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_active_sessions(self, manager):
        """GIVEN: Mix of active and inactive sessions.

        WHEN: list_sessions(active_only=True)
        THEN: Returns only active sessions.
        """
        # Create 3 sessions
        session1 = await manager.create_session("browser-1")
        session2 = await manager.create_session("browser-2")
        session3 = await manager.create_session("browser-3")

        # Close one
        await manager.close_session(session2)

        # List active
        active = await manager.list_sessions(active_only=True)
        assert len(active) == 2
        assert all(s.is_active for s in active)

    @pytest.mark.asyncio
    async def test_list_all_sessions(self, manager):
        """GIVEN: Mix of active and inactive sessions.

        WHEN: list_sessions(active_only=False)
        THEN: Returns all sessions.
        """
        # Create and close sessions
        session1 = await manager.create_session("browser-1")
        session2 = await manager.create_session("browser-2")
        await manager.close_session(session1)

        # List all
        all_sessions = await manager.list_sessions(active_only=False)
        assert len(all_sessions) == 2


class TestShutdown:
    @pytest.mark.asyncio
    async def test_close_all_sessions(self, manager):
        """GIVEN: Multiple active sessions.

        WHEN: close_all_sessions called
        THEN: All sessions closed.
        """
        # Create sessions
        await manager.create_session("browser-1")
        await manager.create_session("browser-2")
        await manager.create_session("browser-3")

        # Close all
        await manager.close_all_sessions()

        # Verify all inactive
        active = await manager.list_sessions(active_only=True)
        assert len(active) == 0


class TestStats:
    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """GIVEN: Active sessions.

        WHEN: get_stats called
        THEN: Returns statistics dict.
        """
        # Create sessions
        await manager.create_session("browser-1")
        await manager.create_session("browser-2")

        stats = await manager.get_stats()

        assert stats["total_sessions"] == 2
        assert stats["active_sessions"] == 2
        assert stats["inactive_sessions"] == 0
        assert "avg_idle_seconds" in stats
        assert "avg_age_seconds" in stats
        assert stats["idle_timeout_seconds"] == 2.0
        assert stats["max_age_seconds"] == 5.0
