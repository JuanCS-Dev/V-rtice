"""
Immunis - Macrophage Service
============================
Digital phagocyte for malware analysis and antigen presentation.

Biological inspiration: Macrophages
- Engulf pathogens (phagocytosis)
- Digest and analyze (lysosome)
- Present antigens (MHC molecules)
- Secrete cytokines (alert other cells)
- Memory formation (trained immunity)

Computational implementation:
- Static analysis (YARA, strings, PE parsing)
- Dynamic analysis (sandbox execution)
- IOC extraction (hashes, IPs, domains, mutexes)
- Signature generation (YARA rules)
- Antigen presentation via Kafka
"""

import logging
import hashlib
import time
import re
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import json

import yara
import pefile
import magic

logger = logging.getLogger(__name__)


class MalwareFamily(str, Enum):
    """Known malware families"""
    RANSOMWARE = "ransomware"
    TROJAN = "trojan"
    WORM = "worm"
    ROOTKIT = "rootkit"
    BACKDOOR = "backdoor"
    SPYWARE = "spyware"
    ADWARE = "adware"
    CRYPTOMINER = "cryptominer"
    BOTNET = "botnet"
    UNKNOWN = "unknown"


class ThreatSeverity(str, Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BENIGN = "benign"


@dataclass
class IOC:
    """Indicator of Compromise"""
    ioc_type: str  # hash, ip, domain, url, mutex, registry, file_path
    value: str
    confidence: float  # 0-1
    context: str  # Where/how it was found
    metadata: Dict = field(default_factory=dict)


@dataclass
class Antigen:
    """
    Antigen for immune system presentation.

    Like biological MHC molecules, this carries processed malware features
    to other immune cells for recognition and response.
    """
    antigen_id: str  # Unique identifier
    sample_hash: str  # SHA256 of original sample
    malware_family: MalwareFamily
    severity: ThreatSeverity

    # Feature vectors for ML recognition
    static_features: Dict  # PE features, strings, entropy
    behavioral_features: Dict  # Syscalls, network, file ops
    iocs: List[IOC]

    # YARA signature (antibody)
    yara_rule: Optional[str] = None

    # Confidence and metadata
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


@dataclass
class PhagocytosisResult:
    """Result from engulfing and analyzing a sample"""
    success: bool
    sample_hash: str
    antigen: Optional[Antigen]
    analysis_time_ms: float
    error_message: Optional[str] = None


class MacrophageCore:
    """
    Macrophage - Digital phagocyte for malware analysis.

    Capabilities:
    1. Phagocytosis (ingest malware samples)
    2. Static analysis (PE parsing, strings, entropy)
    3. Dynamic analysis (sandbox execution)
    4. IOC extraction (hashes, IPs, domains, etc.)
    5. Signature generation (YARA rules)
    6. Antigen presentation (to adaptive immune system)
    """

    def __init__(
        self,
        yara_rules_path: Optional[Path] = None,
        enable_sandbox: bool = False,
        sandbox_timeout: int = 60
    ):
        self.yara_rules_path = yara_rules_path
        self.enable_sandbox = enable_sandbox
        self.sandbox_timeout = sandbox_timeout

        # Load YARA rules if provided
        self.yara_rules: Optional[yara.Rules] = None
        if yara_rules_path and yara_rules_path.exists():
            self.yara_rules = yara.compile(filepath=str(yara_rules_path))
            logger.info(f"Loaded YARA rules from {yara_rules_path}")

        # File type detector
        self.magic = magic.Magic(mime=True)

        # Statistics
        self.stats = {
            "samples_analyzed": 0,
            "malware_detected": 0,
            "benign_detected": 0,
            "yara_matches": 0,
            "iocs_extracted": 0,
            "antigens_presented": 0
        }

        logger.info(
            f"Macrophage initialized (sandbox={'enabled' if enable_sandbox else 'disabled'})"
        )

    async def phagocytose(
        self,
        sample_path: Path,
        source_metadata: Optional[Dict] = None
    ) -> PhagocytosisResult:
        """
        Phagocytose (engulf and analyze) a malware sample.

        Biological analogy:
        1. Recognition - Identify pathogen
        2. Engulfment - Ingest into phagosome
        3. Digestion - Lysosome processes pathogen
        4. Presentation - MHC molecules display antigens

        Computational implementation:
        1. File type detection
        2. Static analysis
        3. Dynamic analysis (optional)
        4. IOC extraction
        5. Antigen generation

        Args:
            sample_path: Path to malware sample
            source_metadata: Source information (IP, timestamp, etc.)

        Returns:
            PhagocytosisResult with extracted antigen
        """
        start_time = time.time()

        logger.info(f"Phagocytosing sample: {sample_path}")

        try:
            # Validate sample exists
            if not sample_path.exists():
                raise FileNotFoundError(f"Sample not found: {sample_path}")

            # Compute hash
            sample_hash = self._compute_hash(sample_path)
            logger.info(f"Sample SHA256: {sample_hash}")

            # Step 1: Static analysis
            static_features = await self._static_analysis(sample_path)

            # Step 2: YARA scanning
            yara_matches = await self._yara_scan(sample_path)
            if yara_matches:
                self.stats["yara_matches"] += len(yara_matches)

            # Step 3: IOC extraction
            iocs = await self._extract_iocs(sample_path, static_features)
            self.stats["iocs_extracted"] += len(iocs)

            # Step 4: Dynamic analysis (if enabled)
            behavioral_features = {}
            if self.enable_sandbox:
                behavioral_features = await self._sandbox_analysis(sample_path)

            # Step 5: Classification
            malware_family, severity, confidence = self._classify(
                static_features,
                behavioral_features,
                yara_matches,
                iocs
            )

            # Step 6: Generate YARA signature
            yara_rule = None
            if malware_family != MalwareFamily.UNKNOWN and confidence > 0.7:
                yara_rule = self._generate_yara_rule(
                    sample_hash,
                    malware_family,
                    static_features,
                    iocs
                )

            # Step 7: Create antigen
            antigen = Antigen(
                antigen_id=f"ag_{sample_hash[:16]}",
                sample_hash=sample_hash,
                malware_family=malware_family,
                severity=severity,
                static_features=static_features,
                behavioral_features=behavioral_features,
                iocs=iocs,
                yara_rule=yara_rule,
                confidence=confidence,
                metadata={
                    "source": source_metadata or {},
                    "yara_matches": yara_matches,
                    "analysis_type": "static+dynamic" if self.enable_sandbox else "static"
                }
            )

            # Update stats
            self.stats["samples_analyzed"] += 1
            if severity in [ThreatSeverity.CRITICAL, ThreatSeverity.HIGH, ThreatSeverity.MEDIUM]:
                self.stats["malware_detected"] += 1
            else:
                self.stats["benign_detected"] += 1

            analysis_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Phagocytosis complete: {malware_family} (severity={severity}, "
                f"confidence={confidence:.2f}, time={analysis_time_ms:.2f}ms)"
            )

            return PhagocytosisResult(
                success=True,
                sample_hash=sample_hash,
                antigen=antigen,
                analysis_time_ms=analysis_time_ms
            )

        except Exception as e:
            logger.error(f"Phagocytosis failed: {e}")
            analysis_time_ms = (time.time() - start_time) * 1000

            return PhagocytosisResult(
                success=False,
                sample_hash="",
                antigen=None,
                analysis_time_ms=analysis_time_ms,
                error_message=str(e)
            )

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _static_analysis(self, sample_path: Path) -> Dict:
        """
        Static analysis - examine without execution.

        Features extracted:
        - File metadata (size, type, magic)
        - PE structure (if Windows executable)
        - Strings (suspicious patterns)
        - Entropy (packing detection)
        - Imports/exports
        """
        features = {}

        # File basics
        features["file_size"] = sample_path.stat().st_size
        features["file_type"] = self.magic.from_file(str(sample_path))

        # Entropy (packing detection)
        features["entropy"] = self._calculate_entropy(sample_path)

        # PE analysis (if Windows executable)
        if features["file_type"] and "executable" in features["file_type"].lower():
            try:
                pe = pefile.PE(str(sample_path))
                features["pe"] = {
                    "entry_point": pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                    "num_sections": pe.FILE_HEADER.NumberOfSections,
                    "compile_timestamp": pe.FILE_HEADER.TimeDateStamp,
                    "sections": [
                        {
                            "name": section.Name.decode().strip('\x00'),
                            "virtual_size": section.Misc_VirtualSize,
                            "raw_size": section.SizeOfRawData,
                            "entropy": section.get_entropy()
                        }
                        for section in pe.sections
                    ],
                    "imports": [
                        entry.dll.decode()
                        for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', [])
                    ][:20],  # Limit to first 20
                }
                pe.close()
            except Exception as e:
                logger.warning(f"PE parsing failed: {e}")
                features["pe"] = None

        # Extract strings
        features["strings"] = self._extract_strings(sample_path, min_length=6, limit=50)

        return features

    def _calculate_entropy(self, file_path: Path) -> float:
        """Calculate Shannon entropy of file"""
        import math
        from collections import Counter

        with open(file_path, 'rb') as f:
            data = f.read()

        if not data:
            return 0.0

        # Count byte frequencies
        counter = Counter(data)
        length = len(data)

        # Calculate Shannon entropy
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        return entropy

    def _extract_strings(
        self,
        file_path: Path,
        min_length: int = 6,
        limit: int = 50
    ) -> List[str]:
        """Extract printable strings from file"""
        strings = []

        with open(file_path, 'rb') as f:
            data = f.read()

        # ASCII strings
        ascii_pattern = rb'[\x20-\x7E]{' + str(min_length).encode() + rb',}'
        matches = re.findall(ascii_pattern, data)
        strings.extend([m.decode('ascii') for m in matches[:limit]])

        return strings

    async def _yara_scan(self, sample_path: Path) -> List[str]:
        """Scan file with YARA rules"""
        if not self.yara_rules:
            return []

        matches = self.yara_rules.match(str(sample_path))
        return [match.rule for match in matches]

    async def _extract_iocs(
        self,
        sample_path: Path,
        static_features: Dict
    ) -> List[IOC]:
        """
        Extract Indicators of Compromise.

        IOC types:
        - File hashes (MD5, SHA1, SHA256)
        - IP addresses
        - Domain names
        - URLs
        - Registry keys
        - Mutexes
        - File paths
        """
        iocs = []

        # File hashes
        file_hash = self._compute_hash(sample_path)
        iocs.append(IOC(
            ioc_type="hash_sha256",
            value=file_hash,
            confidence=1.0,
            context="file_hash"
        ))

        # Extract from strings
        strings = static_features.get("strings", [])

        # IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        for string in strings:
            for ip in re.findall(ip_pattern, string):
                # Basic validation
                parts = ip.split('.')
                if all(0 <= int(p) <= 255 for p in parts):
                    iocs.append(IOC(
                        ioc_type="ip",
                        value=ip,
                        confidence=0.7,
                        context=f"string: {string[:50]}"
                    ))

        # Domain names
        domain_pattern = r'\b[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,6}\b'
        for string in strings:
            for domain in re.findall(domain_pattern, string.lower()):
                if not domain.endswith('.dll') and not domain.endswith('.exe'):
                    iocs.append(IOC(
                        ioc_type="domain",
                        value=domain,
                        confidence=0.6,
                        context=f"string: {string[:50]}"
                    ))

        # URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        for string in strings:
            for url in re.findall(url_pattern, string):
                iocs.append(IOC(
                    ioc_type="url",
                    value=url,
                    confidence=0.8,
                    context=f"string: {string[:50]}"
                ))

        return iocs

    async def _sandbox_analysis(self, sample_path: Path) -> Dict:
        """
        Dynamic analysis in Cuckoo Sandbox.

        Cuckoo Sandbox API integration for behavioral malware analysis.
        Executes sample in isolated VM and monitors:
        - Process creation/injection
        - File system modifications
        - Registry changes
        - Network activity
        - API calls
        """
        import httpx
        import asyncio

        cuckoo_url = os.getenv("CUCKOO_API_URL", "http://localhost:8090")
        cuckoo_api_key = os.getenv("CUCKOO_API_KEY")

        try:
            async with httpx.AsyncClient(timeout=self.sandbox_timeout) as client:
                # Prepare headers
                headers = {}
                if cuckoo_api_key:
                    headers["Authorization"] = f"Bearer {cuckoo_api_key}"

                # Submit file to Cuckoo
                logger.info(f"Submitting {sample_path.name} to Cuckoo Sandbox...")

                with open(sample_path, "rb") as f:
                    files = {"file": (sample_path.name, f, "application/octet-stream")}

                    submit_response = await client.post(
                        f"{cuckoo_url}/tasks/create/file",
                        files=files,
                        headers=headers
                    )

                if submit_response.status_code != 200:
                    logger.error(f"Cuckoo submission failed: HTTP {submit_response.status_code}")
                    return self._fallback_sandbox_analysis()

                submit_data = submit_response.json()
                task_id = submit_data.get("task_id")

                if not task_id:
                    logger.error("No task_id returned from Cuckoo")
                    return self._fallback_sandbox_analysis()

                logger.info(f"Cuckoo task created: {task_id}")

                # Poll for completion (with timeout)
                max_polls = self.sandbox_timeout // 5  # Poll every 5 seconds
                for attempt in range(max_polls):
                    await asyncio.sleep(5)

                    status_response = await client.get(
                        f"{cuckoo_url}/tasks/view/{task_id}",
                        headers=headers
                    )

                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        task_status = status_data.get("task", {}).get("status")

                        if task_status == "reported":
                            logger.info(f"Cuckoo analysis complete for task {task_id}")
                            break
                    else:
                        logger.warning(f"Status check failed: {status_response.status_code}")

                # Get report
                report_response = await client.get(
                    f"{cuckoo_url}/tasks/report/{task_id}",
                    headers=headers
                )

                if report_response.status_code != 200:
                    logger.error(f"Failed to retrieve Cuckoo report: {report_response.status_code}")
                    return self._fallback_sandbox_analysis()

                report = report_response.json()

                # Extract behavioral features from Cuckoo report
                behavior = report.get("behavior", {})
                network = report.get("network", {})

                # Process created
                processes = behavior.get("processes", [])
                process_created = [
                    {
                        "process_name": p.get("process_name"),
                        "pid": p.get("pid"),
                        "parent_pid": p.get("parent_id"),
                        "command_line": p.get("command_line")
                    }
                    for p in processes[:20]  # Limit to 20
                ]

                # Files created/deleted
                summary = behavior.get("summary", {})
                files_created = summary.get("files", [])[:50]
                files_deleted = summary.get("file_deleted", [])[:50]

                # Registry modifications
                registry_modified = [
                    {
                        "key": reg.get("key"),
                        "value": reg.get("value"),
                        "data": reg.get("data")
                    }
                    for reg in summary.get("keys", [])[:50]
                ]

                # Network connections
                connections = []
                for conn in network.get("tcp", [])[:30]:
                    connections.append({
                        "protocol": "tcp",
                        "src": conn.get("src"),
                        "dst": conn.get("dst"),
                        "sport": conn.get("sport"),
                        "dport": conn.get("dport")
                    })

                for conn in network.get("udp", [])[:30]:
                    connections.append({
                        "protocol": "udp",
                        "src": conn.get("src"),
                        "dst": conn.get("dst"),
                        "sport": conn.get("sport"),
                        "dport": conn.get("dport")
                    })

                # DNS queries
                dns_queries = [
                    {
                        "request": dns.get("request"),
                        "type": dns.get("type"),
                        "answers": dns.get("answers", [])
                    }
                    for dns in network.get("dns", [])[:50]
                ]

                # HTTP requests
                http_requests = [
                    {
                        "method": http.get("method"),
                        "host": http.get("host"),
                        "uri": http.get("uri"),
                        "user_agent": http.get("user_agent")
                    }
                    for http in network.get("http", [])[:50]
                ]

                logger.info(f"Cuckoo analysis extracted: {len(process_created)} processes, "
                           f"{len(connections)} network connections")

                return {
                    "task_id": task_id,
                    "cuckoo_score": report.get("info", {}).get("score", 0),
                    "process_created": process_created,
                    "files_created": files_created,
                    "files_deleted": files_deleted,
                    "registry_modified": registry_modified,
                    "network_connections": connections,
                    "dns_queries": dns_queries,
                    "http_requests": http_requests,
                    "signatures": [
                        {
                            "name": sig.get("name"),
                            "severity": sig.get("severity"),
                            "description": sig.get("description")
                        }
                        for sig in report.get("signatures", [])[:20]
                    ],
                    "analysis_duration": report.get("info", {}).get("duration")
                }

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Cuckoo Sandbox at {cuckoo_url}")
            return self._fallback_sandbox_analysis()
        except httpx.TimeoutException:
            logger.error(f"Cuckoo Sandbox timeout after {self.sandbox_timeout}s")
            return self._fallback_sandbox_analysis()
        except Exception as e:
            logger.error(f"Cuckoo Sandbox error: {e}")
            return self._fallback_sandbox_analysis()

    def _fallback_sandbox_analysis(self) -> Dict:
        """
        Fallback when Cuckoo is unavailable.
        Returns empty behavioral data with warning.
        """
        logger.warning("⚠️ Cuckoo Sandbox unavailable - using fallback (limited analysis)")

        return {
            "sandbox_available": False,
            "process_created": [],
            "files_created": [],
            "files_deleted": [],
            "registry_modified": [],
            "network_connections": [],
            "dns_queries": [],
            "http_requests": [],
            "warning": "Dynamic analysis unavailable - Cuckoo Sandbox not reachable"
        }

    def _classify(
        self,
        static_features: Dict,
        behavioral_features: Dict,
        yara_matches: List[str],
        iocs: List[IOC]
    ) -> Tuple[MalwareFamily, ThreatSeverity, float]:
        """
        Classify malware family and severity.

        Uses heuristics + YARA matches.
        """
        # Default
        family = MalwareFamily.UNKNOWN
        severity = ThreatSeverity.BENIGN
        confidence = 0.5

        # High entropy = likely packed
        entropy = static_features.get("entropy", 0)
        if entropy > 7.5:
            severity = ThreatSeverity.MEDIUM
            confidence = 0.6

        # YARA matches = high confidence
        if yara_matches:
            # Parse YARA rule names for family hints
            for rule in yara_matches:
                rule_lower = rule.lower()

                if "ransomware" in rule_lower:
                    family = MalwareFamily.RANSOMWARE
                    severity = ThreatSeverity.CRITICAL
                    confidence = 0.9
                elif "trojan" in rule_lower:
                    family = MalwareFamily.TROJAN
                    severity = ThreatSeverity.HIGH
                    confidence = 0.85
                elif "backdoor" in rule_lower:
                    family = MalwareFamily.BACKDOOR
                    severity = ThreatSeverity.HIGH
                    confidence = 0.85
                elif "miner" in rule_lower or "crypto" in rule_lower:
                    family = MalwareFamily.CRYPTOMINER
                    severity = ThreatSeverity.MEDIUM
                    confidence = 0.8

        # Many network IOCs = likely botnet/C2
        network_iocs = [ioc for ioc in iocs if ioc.ioc_type in ["ip", "domain", "url"]]
        if len(network_iocs) > 5:
            if family == MalwareFamily.UNKNOWN:
                family = MalwareFamily.BOTNET
            severity = max(severity, ThreatSeverity.HIGH, key=lambda s: ["benign", "low", "medium", "high", "critical"].index(s.value))
            confidence = max(confidence, 0.75)

        return family, severity, confidence

    def _generate_yara_rule(
        self,
        sample_hash: str,
        malware_family: MalwareFamily,
        static_features: Dict,
        iocs: List[IOC]
    ) -> str:
        """
        Generate YARA signature for this malware.

        Like antibody generation in the adaptive immune system.
        """
        rule_name = f"{malware_family.value}_{sample_hash[:8]}"

        # Extract distinctive strings
        strings = static_features.get("strings", [])[:10]

        # Build YARA rule
        yara_rule = f"""
rule {rule_name}
{{
    meta:
        description = "Auto-generated signature for {malware_family.value}"
        hash = "{sample_hash}"
        family = "{malware_family.value}"
        generated_by = "Macrophage Service"
        date = "{time.strftime('%Y-%m-%d')}"

    strings:
"""

        # Add strings
        for i, string in enumerate(strings):
            # Escape special characters
            escaped = string.replace('\\', '\\\\').replace('"', '\\"')
            yara_rule += f'        $s{i} = "{escaped}" ascii wide\n'

        # Add IOC patterns
        for i, ioc in enumerate([ioc for ioc in iocs if ioc.ioc_type in ["domain", "url"]][:5]):
            escaped = ioc.value.replace('.', '\\.')
            yara_rule += f'        $ioc{i} = /{escaped}/ ascii wide\n'

        yara_rule += """
    condition:
        any of them
}
"""

        return yara_rule.strip()

    def get_stats(self) -> Dict:
        """Get macrophage statistics"""
        return self.stats.copy()


# Test
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("MACROPHAGE SERVICE - DIGITAL PHAGOCYTE")
    print("="*80 + "\n")

    async def test_macrophage():
        # Initialize
        macrophage = MacrophageCore(enable_sandbox=False)

        # Create test sample
        test_file = Path("/tmp/test_malware.bin")
        test_file.write_bytes(b"MZ" + b"\x00" * 100 + b"This program cannot be run in DOS mode" + b"\x00" * 500)

        print(f"Created test sample: {test_file}\n")

        # Phagocytose
        result = await macrophage.phagocytose(test_file)

        print(f"Phagocytosis result:")
        print(f"  Success: {result.success}")
        print(f"  Sample hash: {result.sample_hash}")
        print(f"  Analysis time: {result.analysis_time_ms:.2f}ms")

        if result.antigen:
            print(f"\nAntigen generated:")
            print(f"  ID: {result.antigen.antigen_id}")
            print(f"  Family: {result.antigen.malware_family}")
            print(f"  Severity: {result.antigen.severity}")
            print(f"  Confidence: {result.antigen.confidence:.2f}")
            print(f"  IOCs extracted: {len(result.antigen.iocs)}")
            for ioc in result.antigen.iocs[:5]:
                print(f"    - {ioc.ioc_type}: {ioc.value}")

            if result.antigen.yara_rule:
                print(f"\nYARA rule generated:")
                print(result.antigen.yara_rule[:200] + "...")

        # Stats
        print(f"\n{'='*80}")
        print("STATISTICS")
        print("="*80)
        stats = macrophage.get_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")

        # Cleanup
        test_file.unlink()

        print("\n" + "="*80)
        print("MACROPHAGE TEST COMPLETE!")
        print("="*80 + "\n")

    asyncio.run(test_macrophage())
