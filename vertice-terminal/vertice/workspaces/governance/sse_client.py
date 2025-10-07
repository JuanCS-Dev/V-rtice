"""
GovernanceStreamClient - SSE Client for Real-time Events

Async client for consuming Server-Sent Events (SSE) from MAXIMUS
governance backend. Handles connection lifecycle, reconnection,
and event parsing.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import httpx
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GovernanceStreamClient:
    """
    SSE client for governance decision stream.

    Connects to MAXIMUS backend SSE endpoint and yields parsed events.
    Handles automatic reconnection with exponential backoff.

    Features:
    - Async event streaming via AsyncGenerator
    - Automatic reconnection on disconnect
    - Event parsing and validation
    - Heartbeat monitoring
    - Callback hooks for event types

    Attributes:
        backend_url: MAXIMUS backend base URL
        operator_id: Operator identifier
        session_id: Active session ID
        is_connected: Connection status flag
    """

    def __init__(
        self,
        backend_url: str,
        operator_id: str,
        session_id: str,
        timeout: float = 60.0,
        max_retries: int = 5,
    ):
        """
        Initialize SSE client.

        Args:
            backend_url: MAXIMUS backend URL (e.g. http://localhost:8000)
            operator_id: Operator identifier
            session_id: Active session ID from authentication
            timeout: Connection timeout in seconds (default 60s)
            max_retries: Maximum reconnection attempts (default 5)
        """
        self.backend_url = backend_url.rstrip("/")
        self.operator_id = operator_id
        self.session_id = session_id
        self.timeout = timeout
        self.max_retries = max_retries

        # Connection state
        self.is_connected = False
        self._client: Optional[httpx.AsyncClient] = None
        self._retry_count = 0
        self._last_event_id: Optional[str] = None

        # Event callbacks
        self._event_handlers: Dict[str, Callable] = {}

    async def connect(self) -> AsyncGenerator[Dict, None]:
        """
        Connect to SSE stream and yield events.

        Yields:
            Parsed event dictionaries with keys:
            - event_type: str
            - event_id: str
            - timestamp: str
            - data: Dict

        Raises:
            ConnectionError: If max retries exceeded
            httpx.HTTPError: On HTTP errors
        """
        stream_url = f"{self.backend_url}/api/v1/governance/stream/{self.operator_id}"
        params = {"session_id": self.session_id}

        while self._retry_count < self.max_retries:
            try:
                # Create client if not exists
                if self._client is None:
                    self._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(self.timeout, read=None),
                        follow_redirects=True,
                    )

                logger.info(f"Connecting to SSE stream: {stream_url}")

                # Connect to SSE endpoint
                async with self._client.stream(
                    "GET", stream_url, params=params
                ) as response:
                    response.raise_for_status()
                    self.is_connected = True
                    self._retry_count = 0  # Reset on successful connection

                    logger.info(f"SSE stream connected (operator={self.operator_id})")

                    # Parse SSE events
                    async for event in self._parse_sse_stream(response):
                        yield event

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error on SSE stream: {e.response.status_code}")
                self.is_connected = False

                if e.response.status_code in [401, 403]:
                    # Auth errors - don't retry
                    raise ConnectionError(f"Authentication failed: {e}")

                # Retry for other errors
                await self._handle_reconnect()

            except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
                logger.warning(f"Connection error: {e}")
                self.is_connected = False
                await self._handle_reconnect()

            except asyncio.CancelledError:
                logger.info("SSE stream cancelled")
                self.is_connected = False
                break

            except Exception as e:
                logger.error(f"Unexpected error in SSE stream: {e}", exc_info=True)
                self.is_connected = False
                await self._handle_reconnect()

        # Max retries exceeded
        raise ConnectionError(f"Failed to connect after {self.max_retries} attempts")

    async def _parse_sse_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[Dict, None]:
        """
        Parse SSE response stream into events.

        Args:
            response: httpx streaming response

        Yields:
            Parsed event dictionaries
        """
        event_id = None
        event_type = None
        data_lines = []

        async for line in response.aiter_lines():
            line = line.strip()

            if not line:
                # Empty line = event boundary
                if event_type and data_lines:
                    # Parse data as JSON
                    data_str = "\n".join(data_lines)
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data_str}")
                        data = {"raw": data_str}

                    # Build event dict
                    event = {
                        "event_type": event_type,
                        "event_id": event_id or "",
                        "timestamp": datetime.now().isoformat(),
                        "data": data,
                    }

                    # Update last event ID for resume
                    if event_id:
                        self._last_event_id = event_id

                    # Trigger callback if registered
                    if event_type in self._event_handlers:
                        try:
                            self._event_handlers[event_type](event)
                        except Exception as e:
                            logger.error(f"Event handler error: {e}", exc_info=True)

                    yield event

                # Reset for next event
                event_id = None
                event_type = None
                data_lines = []

            elif line.startswith("id:"):
                event_id = line[3:].strip()

            elif line.startswith("event:"):
                event_type = line[6:].strip()

            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

            elif line.startswith(":"):
                # Comment line - ignore
                pass

    async def _handle_reconnect(self) -> None:
        """Handle reconnection with exponential backoff."""
        self._retry_count += 1

        if self._retry_count >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) exceeded")
            return

        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
        delay = min(2 ** (self._retry_count - 1), 16)
        logger.info(f"Reconnecting in {delay}s (attempt {self._retry_count}/{self.max_retries})")
        await asyncio.sleep(delay)

    def on_event(self, event_type: str, handler: Callable[[Dict], None]) -> None:
        """
        Register event handler callback.

        Args:
            event_type: Event type to handle (e.g. "decision_pending")
            handler: Callback function receiving event dict
        """
        self._event_handlers[event_type] = handler

    async def close(self) -> None:
        """Close SSE client and cleanup."""
        self.is_connected = False
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("SSE client closed")
