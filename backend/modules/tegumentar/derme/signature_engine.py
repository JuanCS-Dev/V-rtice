"""Signature engine for known threat patterns."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import yaml

from ..config import TegumentarSettings, get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Signature:
    name: str
    pattern: re.Pattern[str]
    severity: str
    action: str


class SignatureEngine:
    """Loads YAML signatures and matches payloads."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._signatures: Dict[str, Signature] = {}

    def load(self) -> None:
        directory = Path(self._settings.signature_directory)
        if not directory.exists():
            raise FileNotFoundError(f"Signature directory {directory} not found")

        for path in directory.glob("*.yaml"):
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
            for sig in data.get("signatures", []):
                compiled = Signature(
                    name=sig["name"],
                    pattern=re.compile(sig["pattern"], re.IGNORECASE),
                    severity=sig.get("severity", "medium"),
                    action=sig.get("action", "block"),
                )
                self._signatures[compiled.name] = compiled
                logger.debug("Loaded signature %s from %s", compiled.name, path)

        logger.info("Loaded %d signatures from %s", len(self._signatures), directory)

    def match(self, payload: bytes) -> Optional[Signature]:
        if not self._signatures:
            self.load()

        try:
            decoded = payload.decode("utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to decode payload: %s", exc)
            return None

        for signature in self._signatures.values():
            if signature.pattern.search(decoded):
                return signature
        return None


__all__ = ["Signature", "SignatureEngine"]
