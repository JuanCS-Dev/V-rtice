"""Utilities to load and attach the eBPF reflex arc using libbpf."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Callable

from ..config import TegumentarSettings

logger = logging.getLogger(__name__)


class ReflexArcLoaderError(RuntimeError):
    """Raised when the reflex arc cannot be loaded or attached."""


class ReflexArcSession:
    """Runtime handle to the reflex arc program."""

    def __init__(self, interface: str):
        self._interface = interface

    def poll_events(self, callback: Callable[[dict], None]) -> None:
        """Blocking poll on the perf buffer to emit reflex events."""
        # Note: Perf buffer polling requires libbpf C API through ctypes
        # This is a placeholder - full implementation pending
        logger.warning("Perf buffer polling not implemented - events will not be collected")
        while True:
            pass  # Placeholder

    def close(self) -> None:
        """Detach XDP program from interface."""
        try:
            subprocess.run(
                ["ip", "link", "set", "dev", self._interface, "xdpgeneric", "off"],
                check=True,
                capture_output=True,
            )
            logger.info("Detached reflex arc from %s", self._interface)
        except subprocess.CalledProcessError as exc:
            logger.warning("Failed to detach XDP: %s", exc.stderr.decode())


class ReflexArcLoader:
    """Loads and attaches the pre-compiled XDP reflex arc using ip link + xdp."""

    def __init__(self, settings: TegumentarSettings):
        self._settings = settings

    def attach(self, source_path: Path, interface: str, flags: int = 0) -> ReflexArcSession:
        """Load pre-compiled BPF object (CO-RE) and attach to interface via XDP."""

        object_path = source_path.with_suffix('.o')

        if not object_path.exists():
            raise ReflexArcLoaderError(
                f"Pre-compiled BPF object not found: {object_path}. "
                "Ensure the Docker build stage compiled reflex_arc.c to reflex_arc.o"
            )

        try:
            logger.info("Loading pre-compiled BPF object (CO-RE): %s", object_path)

            # Attach XDP program using ip link command
            # xdpgeneric mode works in most environments including containers
            result = subprocess.run(
                ["ip", "link", "set", "dev", interface, "xdpgeneric", "obj", str(object_path), "sec", "xdp"],
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info("Reflex arc (CO-RE) successfully attached to %s", interface)
            return ReflexArcSession(interface=interface)

        except subprocess.CalledProcessError as exc:
            error_msg = exc.stderr if exc.stderr else str(exc)
            raise ReflexArcLoaderError(f"Failed to attach XDP program: {error_msg}") from exc
        except Exception as exc:  # noqa: BLE001
            raise ReflexArcLoaderError(f"Failed to attach reflex arc: {exc}") from exc


__all__ = ["ReflexArcLoader", "ReflexArcLoaderError", "ReflexArcSession"]
