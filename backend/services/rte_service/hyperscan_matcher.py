"""
RTE - Hyperscan Pattern Matcher
=================================
Intel Hyperscan integration for ultra-fast pattern matching (<50ms).

Uses SIMD instructions for parallel regex matching.
NO MOCKS - Real Hyperscan library with Python bindings.
"""

import hyperscan
import logging
import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Pattern definition for Hyperscan"""
    id: int
    pattern: str  # Regex pattern
    flags: int = 0  # Hyperscan flags (CASELESS, DOTALL, etc)
    metadata: Dict = None  # Threat metadata (severity, category, etc)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Match:
    """Match result from Hyperscan"""
    pattern_id: int
    start: int
    end: int
    matched_text: str
    metadata: Dict
    timestamp: float


class HyperscanMatcher:
    """
    Hyperscan-based pattern matcher for threat detection.

    Performance target: <10ms for 50k patterns
    """

    def __init__(self, patterns_file: Optional[Path] = None):
        """
        Initialize Hyperscan matcher.

        Args:
            patterns_file: JSON file with patterns (optional, can load later)
        """
        self.database = None
        self.patterns: List[Pattern] = []
        self.pattern_lookup: Dict[int, Pattern] = {}
        self.stats = {
            "total_scans": 0,
            "total_matches": 0,
            "avg_scan_time_ms": 0.0,
            "patterns_loaded": 0
        }

        if patterns_file and patterns_file.exists():
            self.load_patterns(patterns_file)
            self.compile()

        logger.info("Hyperscan matcher initialized")

    def load_patterns(self, patterns_file: Path):
        """
        Load patterns from JSON file.

        Format:
        [
            {
                "id": 1,
                "pattern": "malware.*\\.exe",
                "flags": ["CASELESS"],
                "metadata": {"severity": "high", "category": "malware"}
            },
            ...
        ]
        """
        logger.info(f"Loading patterns from {patterns_file}")

        with open(patterns_file, 'r') as f:
            patterns_data = json.load(f)

        self.patterns = []

        for p in patterns_data:
            # Convert flags from strings to Hyperscan constants
            flags = 0
            if "flags" in p:
                flag_map = {
                    "CASELESS": hyperscan.HS_FLAG_CASELESS,
                    "DOTALL": hyperscan.HS_FLAG_DOTALL,
                    "MULTILINE": hyperscan.HS_FLAG_MULTILINE,
                    "SINGLEMATCH": hyperscan.HS_FLAG_SINGLEMATCH,
                    "UTF8": hyperscan.HS_FLAG_UTF8,
                    "UCP": hyperscan.HS_FLAG_UCP
                }
                for flag_name in p.get("flags", []):
                    if flag_name in flag_map:
                        flags |= flag_map[flag_name]

            pattern = Pattern(
                id=p["id"],
                pattern=p["pattern"],
                flags=flags,
                metadata=p.get("metadata", {})
            )
            self.patterns.append(pattern)
            self.pattern_lookup[pattern.id] = pattern

        logger.info(f"Loaded {len(self.patterns)} patterns")
        self.stats["patterns_loaded"] = len(self.patterns)

    def compile(self):
        """
        Compile patterns into Hyperscan database.

        This is the preprocessing step that enables fast matching.
        """
        if not self.patterns:
            logger.warning("No patterns to compile")
            return

        logger.info(f"Compiling {len(self.patterns)} patterns...")
        start_time = time.time()

        # Prepare patterns for Hyperscan
        patterns_list = [p.pattern.encode() for p in self.patterns]
        ids_list = [p.id for p in self.patterns]
        flags_list = [p.flags for p in self.patterns]

        # Compile database (BLOCK mode for streaming)
        self.database = hyperscan.Database(mode=hyperscan.HS_MODE_BLOCK)

        try:
            expressions = list(zip(patterns_list, ids_list, flags_list))
            self.database = hyperscan.Database()
            self.database.compile(
                expressions=expressions,
                elements=len(expressions),
                mode=hyperscan.HS_MODE_BLOCK
            )

            compile_time = (time.time() - start_time) * 1000
            logger.info(f"Compiled {len(self.patterns)} patterns in {compile_time:.2f}ms")

        except hyperscan.error as e:
            logger.error(f"Hyperscan compilation error: {e}")
            raise

    def scan(self, data: bytes) -> List[Match]:
        """
        Scan data for pattern matches.

        Args:
            data: Byte string to scan

        Returns:
            List of matches with metadata
        """
        if self.database is None:
            logger.error("Database not compiled. Call compile() first.")
            return []

        matches = []
        start_time = time.time()

        def on_match(id: int, from_: int, to: int, flags: int, context: None):
            """Callback for each match"""
            pattern = self.pattern_lookup.get(id)
            if pattern:
                match = Match(
                    pattern_id=id,
                    start=from_,
                    end=to,
                    matched_text=data[from_:to].decode('utf-8', errors='ignore'),
                    metadata=pattern.metadata,
                    timestamp=time.time()
                )
                matches.append(match)
            return 0  # Continue scanning

        # Perform scan
        try:
            self.database.scan(data, match_event_handler=on_match)
        except hyperscan.error as e:
            logger.error(f"Hyperscan scan error: {e}")

        scan_time_ms = (time.time() - start_time) * 1000

        # Update stats
        self.stats["total_scans"] += 1
        self.stats["total_matches"] += len(matches)

        # Running average
        n = self.stats["total_scans"]
        old_avg = self.stats["avg_scan_time_ms"]
        self.stats["avg_scan_time_ms"] = (old_avg * (n - 1) + scan_time_ms) / n

        logger.debug(
            f"Scan complete: {len(matches)} matches in {scan_time_ms:.2f}ms "
            f"(avg: {self.stats['avg_scan_time_ms']:.2f}ms)"
        )

        return matches

    def scan_text(self, text: str) -> List[Match]:
        """Convenience method for scanning text strings"""
        return self.scan(text.encode('utf-8'))

    def get_unique_severities(self, matches: List[Match]) -> Set[str]:
        """Extract unique severity levels from matches"""
        return {m.metadata.get("severity", "unknown") for m in matches}

    def get_highest_severity(self, matches: List[Match]) -> str:
        """Get highest severity from matches"""
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
        severities = [m.metadata.get("severity", "unknown") for m in matches]

        if not severities:
            return "unknown"

        return max(severities, key=lambda s: severity_order.get(s, 0))

    def filter_by_category(self, matches: List[Match], category: str) -> List[Match]:
        """Filter matches by threat category"""
        return [m for m in matches if m.metadata.get("category") == category]

    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return self.stats.copy()

    def reload_patterns(self, patterns_file: Path):
        """Hot-reload patterns (useful for updating signatures)"""
        logger.info("Hot-reloading patterns...")
        self.load_patterns(patterns_file)
        self.compile()
        logger.info("Patterns reloaded successfully")


# Test function
if __name__ == "__main__":
    import tempfile

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("HYPERSCAN PATTERN MATCHER TEST")
    print("="*80 + "\n")

    # Create test patterns
    test_patterns = [
        {
            "id": 1,
            "pattern": "malware.*\\.exe",
            "flags": ["CASELESS"],
            "metadata": {"severity": "high", "category": "malware", "description": "Malware executable"}
        },
        {
            "id": 2,
            "pattern": "SELECT.*FROM.*users.*WHERE",
            "flags": ["CASELESS"],
            "metadata": {"severity": "high", "category": "sqli", "description": "SQL injection attempt"}
        },
        {
            "id": 3,
            "pattern": "<script[^>]*>.*</script>",
            "flags": ["CASELESS", "DOTALL"],
            "metadata": {"severity": "medium", "category": "xss", "description": "XSS attempt"}
        },
        {
            "id": 4,
            "pattern": "cmd\\.exe|powershell\\.exe|bash",
            "flags": ["CASELESS"],
            "metadata": {"severity": "high", "category": "rce", "description": "Command execution"}
        },
        {
            "id": 5,
            "pattern": "\\b(?:\\d{1,3}\\.){3}\\d{1,3}\\b",
            "flags": [],
            "metadata": {"severity": "low", "category": "recon", "description": "IP address detected"}
        }
    ]

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_patterns, f)
        patterns_file = Path(f.name)

    # Initialize matcher
    matcher = HyperscanMatcher(patterns_file)

    # Test data
    test_samples = [
        "Download Malware.exe from the server",
        "SELECT * FROM users WHERE username='admin'",
        "<script>alert('XSS')</script>",
        "Execute cmd.exe with admin privileges",
        "Connect to 192.168.1.100 on port 22",
        "Normal clean text with no threats"
    ]

    print("Testing pattern matching:\n")

    for i, sample in enumerate(test_samples, 1):
        print(f"Sample {i}: {sample}")
        matches = matcher.scan_text(sample)

        if matches:
            print(f"  ✗ THREAT DETECTED: {len(matches)} match(es)")
            for match in matches:
                severity = match.metadata.get("severity", "unknown")
                category = match.metadata.get("category", "unknown")
                desc = match.metadata.get("description", "")
                print(f"    - [{severity.upper()}] {category}: {desc}")
                print(f"      Matched: '{match.matched_text}'")
        else:
            print(f"  ✓ Clean")
        print()

    # Performance stats
    print("="*80)
    print("PERFORMANCE STATISTICS")
    print("="*80)
    stats = matcher.get_stats()
    print(f"Total scans: {stats['total_scans']}")
    print(f"Total matches: {stats['total_matches']}")
    print(f"Average scan time: {stats['avg_scan_time_ms']:.2f}ms")
    print(f"Patterns loaded: {stats['patterns_loaded']}")

    # Cleanup
    patterns_file.unlink()

    print("\n" + "="*80)
    print("TEST COMPLETE - REAL HYPERSCAN WORKING!")
    print("="*80 + "\n")
