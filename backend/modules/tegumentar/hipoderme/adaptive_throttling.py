"""Adaptive throttling via tc/netem."""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)


class AdaptiveThrottlerError(RuntimeError):
    pass


class AdaptiveThrottler:
    """Applies rate limits to protect downstream services under stress."""

    def __init__(self, interface: str):
        self._interface = interface

    def apply(self, rate: str, burst: str = "32kbit") -> None:
        command = [
            "tc",
            "qdisc",
            "replace",
            "dev",
            self._interface,
            "root",
            "tbf",
            "rate",
            rate,
            "burst",
            burst,
            "latency",
            "400ms",
        ]
        self._run(command)
        logger.info(
            "Applied throttling on %s rate=%s burst=%s", self._interface, rate, burst
        )

    def clear(self) -> None:
        command = ["tc", "qdisc", "del", "dev", self._interface, "root"]
        try:
            self._run(command)
        except AdaptiveThrottlerError:
            logger.debug("No existing qdisc on %s", self._interface)

    def _run(self, command: list[str]) -> None:
        try:
            subprocess.run(
                command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode().strip()
            raise AdaptiveThrottlerError(
                f"Command {' '.join(command)} failed: {stderr}"
            ) from exc


__all__ = ["AdaptiveThrottler", "AdaptiveThrottlerError"]
