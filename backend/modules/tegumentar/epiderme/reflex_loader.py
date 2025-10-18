"""Utilities to build, attach and monitor the eBPF reflex arc."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from bcc import BPF  # type: ignore[import]

from ..config import TegumentarSettings

logger = logging.getLogger(__name__)


class ReflexArcLoaderError(RuntimeError):
    """Raised when the reflex arc cannot be compiled or attached."""


class ReflexArcSession:
    """Runtime handle to the reflex arc program and its perf buffer."""

    def __init__(self, bpf: BPF, interface: str):
        self._bpf = bpf
        self._interface = interface

    def poll_events(self, callback: Callable[[dict], None]) -> None:
        """Blocking poll on the perf buffer to emit reflex events."""

        def _handle_event(cpu: int, data: bytes, size: int) -> None:
            event = self._bpf["reflex_events"].event(data)
            callback(
                {
                    "cpu": cpu,
                    "src_ip": event.src_ip,
                    "signature_id": event.signature_id,
                }
            )

        self._bpf["reflex_events"].open_perf_buffer(_handle_event)  # type: ignore[attr-defined]
        logger.info("Started reflex perf buffer polling on %s", self._interface)
        while True:
            self._bpf.perf_buffer_poll()

    def close(self) -> None:
        self._bpf.detach_xdp(self._interface)
        logger.info("Detached reflex arc from %s", self._interface)


class ReflexArcLoader:
    """Compiles and attaches the reflex XDP program using BCC."""

    def __init__(self, settings: TegumentarSettings):
        self._settings = settings

    def attach(self, source_path: Path, interface: str, flags: int = 0) -> ReflexArcSession:
        """Compile (if needed) and attach the reflex arc to an interface."""

        if not source_path.exists():
            raise ReflexArcLoaderError(f"Source {source_path} does not exist")

        try:
            bpf = BPF(src_file=str(source_path))
            fx = bpf.load_func("xdp_reflex_firewall", BPF.XDP)  # type: ignore[attr-defined]
            bpf.attach_xdp(dev=interface, fn=fx, flags=flags)
            logger.info("Reflex arc attached to %s", interface)
            return ReflexArcSession(bpf=bpf, interface=interface)
        except Exception as exc:  # noqa: BLE001
            raise ReflexArcLoaderError(f"Failed to attach reflex arc: {exc}") from exc


__all__ = ["ReflexArcLoader", "ReflexArcLoaderError", "ReflexArcSession"]
