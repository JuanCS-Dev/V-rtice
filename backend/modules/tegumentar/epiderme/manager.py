"""Coordinator for the epiderme layer."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import socket
import struct
from pathlib import Path
from typing import Optional

from aiokafka import AIOKafkaProducer

from ..config import TegumentarSettings, get_settings
from ..metrics import record_reflex_event
from .ip_reputation import IPReputationFeed, LocalReputationStore
from .rate_limiter import DistributedRateLimiter
from .reflex_loader import ReflexArcLoader, ReflexArcLoaderError, ReflexArcSession
from .stateless_filter import StatelessFilter

logger = logging.getLogger(__name__)


class EpidermeLayer:
    """Top-level orchestrator for the epiderme defensive layer."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._stateless_filter = StatelessFilter(self._settings)
        self._reputation_feed = IPReputationFeed(self._settings)
        self._reputation_store = LocalReputationStore(Path(self._settings.reputation_cache_path))
        self._rate_limiter = DistributedRateLimiter(self._settings)
        self._reflex_loader = ReflexArcLoader(self._settings)
        self._reflex_session: Optional[ReflexArcSession] = None
        self._producer: Optional[AIOKafkaProducer] = None
        self._tasks: list[asyncio.Task] = []
        self._interface: Optional[str] = None
        self._shutdown_event = asyncio.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def startup(self, interface: str) -> None:
        """Initialise all epiderme subsystems."""

        self._interface = interface
        self._loop = asyncio.get_running_loop()

        logger.info("Starting Epiderme layer on interface %s", interface)
        self._stateless_filter.ensure_table_structure()
        self._stateless_filter.attach_to_hook()

        await self._rate_limiter.startup()
        await self._producer_startup()

        await self._sync_reputation(initial=True)
        self._tasks.append(asyncio.create_task(self._periodic_reputation_sync()))

        reflex_source = Path(__file__).resolve().parent / "reflex_arc.c"
        try:
            self._reflex_session = self._reflex_loader.attach(
                source_path=reflex_source,
                interface=interface,
                flags=0,
            )
        except ReflexArcLoaderError as exc:
            logger.error("Failed to attach reflex arc: %s", exc)
            raise

        self._tasks.append(asyncio.create_task(self._poll_reflex_events()))

    async def shutdown(self) -> None:
        """Gracefully shutdown all subsystems."""

        logger.info("Shutting down Epiderme layer")
        self._shutdown_event.set()

        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

        if self._reflex_session:
            self._reflex_session.close()
            self._reflex_session = None

        await self._rate_limiter.shutdown()

        if self._producer:
            await self._producer.stop()
            self._producer = None

    async def _producer_startup(self) -> None:
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._settings.kafka_bootstrap_servers,
                value_serializer=lambda payload: json.dumps(payload).encode("utf-8"),
            )
            await self._producer.start()
            logger.info("Kafka producer connected to %s", self._settings.kafka_bootstrap_servers)

    async def _poll_reflex_events(self) -> None:
        if not self._reflex_session:
            return

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self._reflex_session.poll_events,
            self._handle_reflex_event,
        )

    async def _periodic_reputation_sync(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(self._settings.reputation_refresh_interval)
                await self._sync_reputation(initial=False)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Reputation sync failed: %s", exc)

    async def _sync_reputation(self, *, initial: bool) -> None:
        if initial:
            cached_ips = [ip async for ip in self._reputation_store.stream()]
            if cached_ips:
                logger.info("Restoring %d cached reputation entries", len(cached_ips))
                self._stateless_filter.sync_blocked_ips(cached_ips)

        ips = await self._reputation_feed.fetch_all()
        self._stateless_filter.sync_blocked_ips(ips)
        self._reputation_store.atomically_write(ips)

    def _handle_reflex_event(self, event: dict) -> None:
        if not self._producer:
            logger.warning("Kafka producer unavailable; dropping reflex event")
            return

        if not self._loop:
            logger.warning("Event loop not available; dropping reflex event")
            return

        ip_int = event["src_ip"]
        signature_id = event["signature_id"]
        ip_str = socket.inet_ntoa(struct.pack("!I", ip_int))
        payload = {
            "interface": self._interface,
            "src_ip": ip_str,
            "signature_id": signature_id,
        }
        record_reflex_event(str(signature_id))

        asyncio.run_coroutine_threadsafe(
            self._producer.send_and_wait(self._settings.reflex_topic, payload),
            self._loop,
        )
        logger.info("Reflex arc triggered signature %s for %s", signature_id, ip_str)

    @property
    def interface(self) -> Optional[str]:
        return self._interface

    @property
    def stateless_filter(self) -> StatelessFilter:
        return self._stateless_filter


__all__ = ["EpidermeLayer"]
