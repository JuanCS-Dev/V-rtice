"""IP reputation synchronisation for the epiderme layer."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Iterable, List, Set

import httpx

from ..config import TegumentarSettings

logger = logging.getLogger(__name__)


class IPReputationFeed:
    """Fetches and parses IP blocklists (PAMP sources)."""

    def __init__(self, settings: TegumentarSettings):
        self._settings = settings
        self._http_timeout = httpx.Timeout(30.0, connect=10.0)

    async def fetch_all(self) -> Set[str]:
        """Fetch, parse and deduplicate all configured sources."""

        async with httpx.AsyncClient(timeout=self._http_timeout, verify=True) as client:
            tasks = [
                self._fetch_and_parse(client, str(url))
                for url in self._settings.ip_reputation_sources
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: Set[str] = set()
        for result in results:
            if isinstance(result, Exception):
                logger.error("Failed to fetch reputation feed: %s", result)
                continue
            merged.update(result)

        logger.info("Loaded %d unique IP/CIDR entries from feeds", len(merged))
        return merged

    async def _fetch_and_parse(self, client: httpx.AsyncClient, url: str) -> Set[str]:
        logger.debug("Fetching reputation feed %s", url)
        response = await client.get(url)
        response.raise_for_status()

        entries: Set[str] = set()
        for line in response.text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            entries.add(stripped)

        logger.debug("Parsed %d entries from %s", len(entries), url)
        return entries


class LocalReputationStore:
    """Maintains a local cache of reputation data for auditing and rollback."""

    def __init__(self, path: Path):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def atomically_write(self, ips: Iterable[str]) -> None:
        temp_path = self._path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as handle:
            for ip in sorted(set(ips)):
                handle.write(f"{ip}\n")
        temp_path.replace(self._path)
        logger.debug("Persisted %s IP entries to %s", len(set(ips)), self._path)

    async def stream(self) -> AsyncIterator[str]:
        if not self._path.exists():
            return
        loop = asyncio.get_running_loop()
        with self._path.open("r", encoding="utf-8") as handle:
            lines: List[str] = await loop.run_in_executor(None, handle.readlines)
        for line in lines:
            stripped = line.strip()
            if stripped:
                yield stripped


__all__ = ["IPReputationFeed", "LocalReputationStore"]
