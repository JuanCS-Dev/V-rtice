"""
ESGT Subscriber - Event subscriber for ESGT ignition events

Subscribes to ESGT coordinator ignition events for immune system coordination.
"""

import asyncio
import logging
from typing import Awaitable, Callable, List

from consciousness.esgt.coordinator import ESGTEvent

logger = logging.getLogger(__name__)


class ESGTSubscriber:
    """
    Event subscriber for ESGT ignition events.

    Provides callback-based subscription for immune system to react to
    conscious access events.
    """

    def __init__(self):
        """Initialize ESGT subscriber."""
        self._handlers: List[Callable[[ESGTEvent], Awaitable[None]]] = []
        self._event_count = 0
        self._running = False

    def on_ignition(self, handler: Callable[[ESGTEvent], Awaitable[None]]):
        """
        Register callback for ESGT ignition events.

        Args:
            handler: Async function called on each ignition event
                     Signature: async def handler(event: ESGTEvent) -> None
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            logger.info(f"Registered ESGT ignition handler: {handler.__name__}")

    def remove_handler(self, handler: Callable):
        """Remove registered handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    async def notify(self, event: ESGTEvent):
        """
        Notify all handlers of ESGT ignition event.

        Called by ESGT coordinator when ignition succeeds.

        Args:
            event: ESGT ignition event
        """
        self._event_count += 1

        # Call all registered handlers
        if self._handlers:
            logger.debug(
                f"Notifying {len(self._handlers)} handlers of ESGT ignition "
                f"(salience={event.salience.compute_total():.2f})"
            )

            # Execute handlers concurrently
            tasks = [handler(event) for handler in self._handlers]
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_event_count(self) -> int:
        """Get total number of events processed."""
        return self._event_count

    def get_handler_count(self) -> int:
        """Get number of registered handlers."""
        return len(self._handlers)

    def clear_handlers(self):
        """Remove all handlers."""
        self._handlers.clear()


# Example handler for testing
async def example_immune_handler(event: ESGTEvent):
    """Example handler that logs ESGT ignition."""
    salience = event.salience.compute_total()
    logger.info(f"🧠 ESGT Ignition detected: salience={salience:.2f}, event_id={event.event_id}")

    if salience > 0.8:
        logger.warning("⚠️  High salience event - triggering immune activation!")
    elif salience > 0.6:
        logger.info("📊 Medium salience event - increasing vigilance")
