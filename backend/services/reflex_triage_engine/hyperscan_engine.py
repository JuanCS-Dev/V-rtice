"""Hyperscan Pattern Matching Engine - Ultra-fast signature scanning <50ms

Uses Intel Hyperscan for parallel regex matching of threats.
Supports YARA rules, Snort signatures, custom patterns.

Performance: 10-50ms for 50k+ signatures (hardware-accelerated regex).
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import hyperscan - graceful fallback if not available
try:
    import hyperscan

    HYPERSCAN_AVAILABLE = True
except ImportError:
    HYPERSCAN_AVAILABLE = False
    logger.warning("Hyperscan not available - using fallback regex engine")
    import re


@dataclass
class SignatureMatch:
    """Match result from signature scanning."""

    signature_id: int
    signature_name: str
    pattern: str
    severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    category: str  # 'MALWARE', 'EXPLOIT', 'ANOMALY', 'IOC'
    matched_offset: int
    matched_data: str
    confidence: float = 1.0


class HyperscanEngine:
    """Ultra-fast pattern matching engine using Intel Hyperscan.

    Compiles 50k+ signatures into optimized database for parallel scanning.
    """

    def __init__(self, signatures_path: Optional[str] = None):
        """Initialize Hyperscan engine.

        Args:
            signatures_path: Path to signatures JSON file (optional)
        """
        self.signatures = []
        self.signature_map = {}  # ID -> signature metadata
        self.database = None
        self.scratch = None
        self.compiled = False

        # Fallback regex patterns
        self.fallback_patterns = []

        if signatures_path:
            self.load_signatures(signatures_path)

        logger.info(
            f"HyperscanEngine initialized (hyperscan={'available' if HYPERSCAN_AVAILABLE else 'FALLBACK'})"
        )

    def load_signatures(self, path: str):
        """Load signatures from JSON file.

        Expected format:
        [
            {
                "id": 1,
                "name": "Metasploit Meterpreter",
                "pattern": "metsrv\\.dll|meterpreter",
                "severity": "CRITICAL",
                "category": "MALWARE"
            },
            ...
        ]
        """
        try:
            with open(path, "r") as f:
                signatures_data = json.load(f)

            self.signatures = []
            self.signature_map = {}

            for sig in signatures_data:
                sig_id = sig["id"]
                self.signatures.append(
                    {
                        "id": sig_id,
                        "pattern": sig["pattern"],
                        "flags": (
                            hyperscan.HS_FLAG_CASELESS | hyperscan.HS_FLAG_DOTALL
                            if HYPERSCAN_AVAILABLE
                            else 0
                        ),
                    }
                )
                self.signature_map[sig_id] = {
                    "name": sig["name"],
                    "pattern": sig["pattern"],
                    "severity": sig.get("severity", "MEDIUM"),
                    "category": sig.get("category", "ANOMALY"),
                }

            logger.info(f"Loaded {len(self.signatures)} signatures from {path}")

        except Exception as e:
            logger.error(f"Failed to load signatures: {e}")
            raise

    def compile_database(self):
        """Compile signatures into Hyperscan database."""
        if not self.signatures:
            logger.warning("No signatures to compile")
            return

        compile_start = time.time()

        if HYPERSCAN_AVAILABLE:
            try:
                # Compile Hyperscan database
                patterns = [s["pattern"] for s in self.signatures]
                ids = [s["id"] for s in self.signatures]
                flags = [s["flags"] for s in self.signatures]

                self.database = hyperscan.Database()
                self.database.compile(
                    expressions=patterns,
                    ids=ids,
                    elements=len(patterns),
                    flags=flags,
                    mode=hyperscan.HS_MODE_BLOCK,
                )

                # Allocate scratch space
                self.scratch = hyperscan.Scratch(self.database)

                self.compiled = True

                compile_time = (time.time() - compile_start) * 1000
                logger.info(
                    f"Hyperscan database compiled: {len(patterns)} patterns in {compile_time:.1f}ms"
                )

            except Exception as e:
                logger.error(f"Hyperscan compilation failed: {e}")
                self._compile_fallback()
        else:
            self._compile_fallback()

    def _compile_fallback(self):
        """Compile fallback regex patterns (when Hyperscan unavailable)."""
        self.fallback_patterns = []

        for sig in self.signatures:
            try:
                compiled = re.compile(sig["pattern"], re.IGNORECASE | re.DOTALL)
                self.fallback_patterns.append({"id": sig["id"], "regex": compiled})
            except Exception as e:
                logger.warning(f"Failed to compile pattern {sig['id']}: {e}")

        self.compiled = True
        logger.info(f"Fallback regex compiled: {len(self.fallback_patterns)} patterns")

    def scan(self, data: bytes, max_matches: int = 100) -> List[SignatureMatch]:
        """Scan data for signature matches.

        Args:
            data: Binary data to scan
            max_matches: Maximum number of matches to return

        Returns:
            List of signature matches
        """
        if not self.compiled:
            logger.warning("Database not compiled - compiling now")
            self.compile_database()

        scan_start = time.time()
        matches = []

        if HYPERSCAN_AVAILABLE and self.database:
            # Hyperscan scan
            def on_match(id, from_offset, to_offset, flags, context):
                if len(matches) >= max_matches:
                    return 1  # Stop scanning

                sig_meta = self.signature_map.get(id, {})
                match_data = data[from_offset:to_offset].decode(
                    "utf-8", errors="ignore"
                )

                matches.append(
                    SignatureMatch(
                        signature_id=id,
                        signature_name=sig_meta.get("name", f"SIG_{id}"),
                        pattern=sig_meta.get("pattern", ""),
                        severity=sig_meta.get("severity", "MEDIUM"),
                        category=sig_meta.get("category", "ANOMALY"),
                        matched_offset=from_offset,
                        matched_data=match_data[:100],  # First 100 chars
                        confidence=1.0,
                    )
                )

                return 0  # Continue scanning

            try:
                self.database.scan(
                    data, match_event_handler=on_match, scratch=self.scratch
                )
            except Exception as e:
                logger.error(f"Hyperscan scan error: {e}")

        else:
            # Fallback regex scan
            data_str = data.decode("utf-8", errors="ignore")

            for pattern_info in self.fallback_patterns:
                if len(matches) >= max_matches:
                    break

                sig_id = pattern_info["id"]
                regex = pattern_info["regex"]

                for match in regex.finditer(data_str):
                    if len(matches) >= max_matches:
                        break

                    sig_meta = self.signature_map.get(sig_id, {})

                    matches.append(
                        SignatureMatch(
                            signature_id=sig_id,
                            signature_name=sig_meta.get("name", f"SIG_{sig_id}"),
                            pattern=sig_meta.get("pattern", ""),
                            severity=sig_meta.get("severity", "MEDIUM"),
                            category=sig_meta.get("category", "ANOMALY"),
                            matched_offset=match.start(),
                            matched_data=match.group()[:100],
                            confidence=0.9,  # Lower confidence for fallback
                        )
                    )

        scan_time = (time.time() - scan_start) * 1000

        if scan_time > 50:
            logger.warning(f"Scan exceeded 50ms target: {scan_time:.1f}ms")

        logger.debug(f"Scan complete: {len(matches)} matches in {scan_time:.1f}ms")

        return matches

    def scan_file(self, file_path: str) -> List[SignatureMatch]:
        """Scan a file for signatures.

        Args:
            file_path: Path to file to scan

        Returns:
            List of signature matches
        """
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return self.scan(data)
        except Exception as e:
            logger.error(f"File scan error: {e}")
            return []

    def scan_network_packet(self, packet: bytes) -> List[SignatureMatch]:
        """Scan network packet for signatures.

        Args:
            packet: Raw packet bytes

        Returns:
            List of signature matches
        """
        return self.scan(packet, max_matches=10)  # Limit for performance

    def get_statistics(self) -> Dict:
        """Get engine statistics."""
        return {
            "signatures_loaded": len(self.signatures),
            "database_compiled": self.compiled,
            "hyperscan_available": HYPERSCAN_AVAILABLE,
            "engine_type": "hyperscan" if HYPERSCAN_AVAILABLE else "fallback_regex",
        }

    def reload_signatures(self, path: str):
        """Hot-reload signatures from file.

        Args:
            path: Path to new signatures file
        """
        logger.info(f"Hot-reloading signatures from {path}")
        self.load_signatures(path)
        self.compile_database()
        logger.info("Signatures reloaded successfully")
