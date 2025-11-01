"""Session Manager - Auto-timeout and graceful cleanup for browser sessions.

Prevents memory leaks by automatically cleaning up idle sessions
and ensuring graceful shutdown.

Biblical Foundation:
- Ecclesiastes 3:1: "For everything there is a season,
  and a time for every matter under heaven"

Features:
- Auto-timeout idle sessions (30 min default)
- Periodic cleanup task
- Memory leak prevention
- Graceful shutdown of all sessions
- Session lifecycle tracking

Author: Vértice Platform Team
Created: 2025-11-01
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import uuid4

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


@dataclass
class BrowserSession:
    """Represents an active browser session."""

    session_id: str
    browser_instance_id: str
    created_at: datetime
    last_activity: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    @property
    def idle_time(self) -> timedelta:
        """Get idle time since last activity."""
        return datetime.utcnow() - self.last_activity

    @property
    def age(self) -> timedelta:
        """Get total session age."""
        return datetime.utcnow() - self.created_at


# Prometheus metrics
session_created = Counter(
    "maba_sessions_created_total", "Total browser sessions created"
)

session_timeout = Counter(
    "maba_sessions_timeout_total", "Sessions terminated due to timeout"
)

session_closed = Counter("maba_sessions_closed_total", "Sessions explicitly closed")

active_sessions = Gauge("maba_sessions_active", "Current number of active sessions")

session_lifetime = Histogram(
    "maba_session_lifetime_seconds", "Session lifetime in seconds"
)


class SessionManager:
    """Auto-timeout and graceful cleanup for browser sessions.

    Manages session lifecycle, auto-timeout idle sessions, prevents memory leaks.

    Biblical Principle: Ecclesiastes 3:1 - "For everything there is a season"
    """

    def __init__(
        self,
        idle_timeout_seconds: int = 1800,  # 30 minutes
        cleanup_interval_seconds: int = 60,  # 1 minute
        max_session_age_seconds: int = 7200,  # 2 hours
    ):
        """Initialize session manager.

        Args:
            idle_timeout_seconds: Seconds before idle session times out (default 30 min)
            cleanup_interval_seconds: Seconds between cleanup runs (default 1 min)
            max_session_age_seconds: Maximum session age regardless of activity (default 2 hours)

        """
        self.idle_timeout = timedelta(seconds=idle_timeout_seconds)
        self.cleanup_interval = cleanup_interval_seconds
        self.max_session_age = timedelta(seconds=max_session_age_seconds)

        self.sessions: dict[str, BrowserSession] = {}
        self._cleanup_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        logger.info(
            f"SessionManager initialized (idle_timeout={idle_timeout_seconds}s, "
            f"max_age={max_session_age_seconds}s)"
        )

    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running")
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session cleanup task started")

    async def stop(self):
        """Stop background cleanup task and close all sessions."""
        logger.info("Stopping session manager...")

        # Signal shutdown
        self._shutdown_event.set()

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all active sessions
        await self.close_all_sessions()

        logger.info("✅ Session manager stopped")

    async def create_session(
        self, browser_instance_id: str, metadata: dict[str, Any] | None = None
    ) -> str:
        """Create new browser session.

        Args:
            browser_instance_id: ID of browser instance for this session
            metadata: Optional session metadata

        Returns:
            session_id: Unique session identifier

        """
        session_id = str(uuid4())
        now = datetime.utcnow()

        session = BrowserSession(
            session_id=session_id,
            browser_instance_id=browser_instance_id,
            created_at=now,
            last_activity=now,
            metadata=metadata or {},
            is_active=True,
        )

        self.sessions[session_id] = session

        # Update metrics
        session_created.inc()
        active_sessions.set(len([s for s in self.sessions.values() if s.is_active]))

        logger.info(f"Created session {session_id} on browser {browser_instance_id}")
        return session_id

    async def update_activity(self, session_id: str) -> bool:
        """Update session activity timestamp.

        Args:
            session_id: Session to update

        Returns:
            True if updated, False if session not found

        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False

        if not session.is_active:
            logger.warning(f"Session inactive: {session_id}")
            return False

        session.update_activity()
        logger.debug(f"Updated activity for session {session_id}")
        return True

    async def close_session(self, session_id: str) -> bool:
        """Explicitly close a session.

        Args:
            session_id: Session to close

        Returns:
            True if closed, False if session not found

        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False

        if not session.is_active:
            logger.warning(f"Session already inactive: {session_id}")
            return False

        # Mark inactive
        session.is_active = False

        # Record lifetime
        lifetime = session.age.total_seconds()
        session_lifetime.observe(lifetime)

        # Update metrics
        session_closed.inc()
        active_sessions.set(len([s for s in self.sessions.values() if s.is_active]))

        logger.info(
            f"Closed session {session_id} (lifetime={lifetime:.1f}s, "
            f"idle={session.idle_time.total_seconds():.1f}s)"
        )

        return True

    async def get_session(self, session_id: str) -> BrowserSession | None:
        """Get session by ID.

        Args:
            session_id: Session to retrieve

        Returns:
            BrowserSession if found and active, None otherwise

        """
        session = self.sessions.get(session_id)
        if not session or not session.is_active:
            return None

        return session

    async def list_sessions(self, active_only: bool = True) -> list[BrowserSession]:
        """List sessions.

        Args:
            active_only: If True, return only active sessions

        Returns:
            List of BrowserSession objects

        """
        if active_only:
            return [s for s in self.sessions.values() if s.is_active]
        return list(self.sessions.values())

    async def _cleanup_loop(self):
        """Background task to cleanup idle/expired sessions."""
        logger.info("Session cleanup loop started")

        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_sessions()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

        logger.info("Session cleanup loop stopped")

    async def _cleanup_sessions(self):
        """Cleanup idle and expired sessions."""
        now = datetime.utcnow()
        closed_count = 0

        for session_id, session in list(self.sessions.items()):
            if not session.is_active:
                continue

            # Check idle timeout
            if session.idle_time > self.idle_timeout:
                logger.info(
                    f"Session {session_id} timed out (idle={session.idle_time.total_seconds():.1f}s)"
                )
                session.is_active = False
                session_timeout.inc()
                closed_count += 1
                continue

            # Check max age
            if session.age > self.max_session_age:
                logger.info(
                    f"Session {session_id} expired (age={session.age.total_seconds():.1f}s)"
                )
                session.is_active = False
                session_timeout.inc()
                closed_count += 1
                continue

        if closed_count > 0:
            # Update metrics
            active_sessions.set(len([s for s in self.sessions.values() if s.is_active]))
            logger.info(f"Cleaned up {closed_count} sessions")

    async def close_all_sessions(self):
        """Close all active sessions (for shutdown)."""
        active = [s for s in self.sessions.values() if s.is_active]
        count = len(active)

        for session in active:
            await self.close_session(session.session_id)

        logger.info(f"Closed {count} active sessions")

    async def get_stats(self) -> dict[str, Any]:
        """Get session manager statistics.

        Returns:
            Dictionary with stats

        """
        active = [s for s in self.sessions.values() if s.is_active]
        inactive = [s for s in self.sessions.values() if not s.is_active]

        # Calculate average idle time for active sessions
        avg_idle = 0.0
        if active:
            avg_idle = sum(s.idle_time.total_seconds() for s in active) / len(active)

        # Calculate average age for active sessions
        avg_age = 0.0
        if active:
            avg_age = sum(s.age.total_seconds() for s in active) / len(active)

        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len(active),
            "inactive_sessions": len(inactive),
            "avg_idle_seconds": avg_idle,
            "avg_age_seconds": avg_age,
            "idle_timeout_seconds": self.idle_timeout.total_seconds(),
            "max_age_seconds": self.max_session_age.total_seconds(),
        }
