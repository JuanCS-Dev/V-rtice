"""
WorkspaceManager - State Management and Action Handler

Central manager for Governance Workspace state, SSE stream integration,
and backend API calls. Coordinates between UI components and backend.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import httpx
import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime

from .sse_client import GovernanceStreamClient

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """
    Manager for Governance Workspace operations.

    Responsibilities:
    - SSE stream lifecycle management
    - Backend API calls (approve/reject/escalate)
    - State synchronization between UI and backend
    - Event routing to UI components
    - Error handling and recovery

    Attributes:
        backend_url: MAXIMUS backend base URL
        operator_id: Operator identifier
        session_id: Active session ID
        sse_client: SSE stream client instance
        http_client: HTTP client for API calls
    """

    def __init__(
        self,
        backend_url: str,
        operator_id: str,
        session_id: str,
        on_event: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Initialize WorkspaceManager.

        Args:
            backend_url: MAXIMUS backend URL
            operator_id: Operator identifier
            session_id: Active session ID
            on_event: Callback for SSE events
            on_error: Callback for errors
        """
        self.backend_url = backend_url.rstrip("/")
        self.operator_id = operator_id
        self.session_id = session_id

        # Callbacks
        self._on_event = on_event
        self._on_error = on_error

        # Clients
        self.sse_client = GovernanceStreamClient(
            backend_url=backend_url,
            operator_id=operator_id,
            session_id=session_id,
        )
        self.http_client = httpx.AsyncClient(
            base_url=backend_url,
            timeout=30.0,
        )

        # State
        self._stream_task: Optional[asyncio.Task] = None
        self._metrics = {
            "events_received": 0,
            "decisions_approved": 0,
            "decisions_rejected": 0,
            "decisions_escalated": 0,
        }

    # ========================================================================
    # SSE Stream Management
    # ========================================================================

    async def start_stream(self) -> None:
        """Start SSE event stream in background."""
        if self._stream_task and not self._stream_task.done():
            logger.warning("Stream already running")
            return

        logger.info("Starting SSE stream")
        self._stream_task = asyncio.create_task(self._stream_events())

    async def stop_stream(self) -> None:
        """Stop SSE event stream."""
        if self._stream_task and not self._stream_task.done():
            logger.info("Stopping SSE stream")
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass

        await self.sse_client.close()

    async def _stream_events(self) -> None:
        """Background task to consume SSE events."""
        try:
            async for event in self.sse_client.connect():
                self._metrics["events_received"] += 1

                # Route event to handler
                event_type = event.get("event_type")
                logger.info(f"Received event: {event_type}")

                # Call user callback
                if self._on_event:
                    try:
                        self._on_event(event)
                    except Exception as e:
                        logger.error(f"Event callback error: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            if self._on_error:
                self._on_error(e)

    # ========================================================================
    # Decision Actions
    # ========================================================================

    async def approve_decision(
        self, decision_id: str, comment: str = ""
    ) -> Dict:
        """
        Approve a pending decision.

        Args:
            decision_id: Decision ID to approve
            comment: Optional approval comment

        Returns:
            Response dict from backend

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"/api/v1/governance/decision/{decision_id}/approve"
        payload = {
            "session_id": self.session_id,
            "comment": comment,
        }

        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            self._metrics["decisions_approved"] += 1
            logger.info(f"Approved decision {decision_id}")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Approve failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Approve error: {e}", exc_info=True)
            raise

    async def reject_decision(
        self, decision_id: str, reason: str, comment: str = ""
    ) -> Dict:
        """
        Reject a pending decision.

        Args:
            decision_id: Decision ID to reject
            reason: Rejection reason (required)
            comment: Optional additional comment

        Returns:
            Response dict from backend

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"/api/v1/governance/decision/{decision_id}/reject"
        payload = {
            "session_id": self.session_id,
            "reason": reason,
            "comment": comment,
        }

        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            self._metrics["decisions_rejected"] += 1
            logger.info(f"Rejected decision {decision_id}")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Reject failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Reject error: {e}", exc_info=True)
            raise

    async def escalate_decision(
        self,
        decision_id: str,
        escalation_reason: str,
        escalation_target: Optional[str] = None,
        comment: str = "",
    ) -> Dict:
        """
        Escalate a pending decision to higher authority.

        Args:
            decision_id: Decision ID to escalate
            escalation_reason: Why escalation is needed (required)
            escalation_target: Target role/person (optional)
            comment: Optional additional comment

        Returns:
            Response dict from backend

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"/api/v1/governance/decision/{decision_id}/escalate"
        payload = {
            "session_id": self.session_id,
            "escalation_reason": escalation_reason,
            "escalation_target": escalation_target,
            "comment": comment,
        }

        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            self._metrics["decisions_escalated"] += 1
            logger.info(f"Escalated decision {decision_id}")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Escalate failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Escalate error: {e}", exc_info=True)
            raise

    # ========================================================================
    # Stats & Health
    # ========================================================================

    async def get_pending_stats(self) -> Dict:
        """
        Get statistics about pending decisions.

        Returns:
            Stats dict with total, by_risk_level, etc.

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = "/api/v1/governance/pending"

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Get stats error: {e}")
            raise

    async def get_operator_stats(self) -> Dict:
        """
        Get operator performance statistics.

        Returns:
            Operator stats dict

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = f"/api/v1/governance/session/{self.operator_id}/stats"

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Get operator stats error: {e}")
            raise

    async def get_health(self) -> Dict:
        """
        Get backend health status.

        Returns:
            Health dict with status, active_connections, etc.

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        url = "/api/v1/governance/health"

        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Health check error: {e}")
            raise

    # ========================================================================
    # Cleanup
    # ========================================================================

    async def close(self) -> None:
        """Close manager and cleanup resources."""
        logger.info("Closing WorkspaceManager")

        # Stop stream
        await self.stop_stream()

        # Close HTTP client
        await self.http_client.aclose()

        logger.info(f"WorkspaceManager closed. Metrics: {self._metrics}")

    @property
    def metrics(self) -> Dict:
        """Get current metrics."""
        return self._metrics.copy()
