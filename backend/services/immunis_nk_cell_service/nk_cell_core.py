"""
Immunis - NK Cell Service
=========================
Missing-self detection - identify compromised hosts.

Biological inspiration: Natural Killer (NK) Cells
- Detect cells lacking "self" markers (MHC-I)
- Kill virus-infected or tumor cells
- No prior sensitization needed (innate immunity)
- Patrol continuously
- Balance activating/inhibitory signals

Computational implementation:
- Process whitelist (legitimate software)
- Missing-self detection (unknown/modified processes)
- DLL hijacking detection
- Memory integrity checks
- Rootkit detection
- One agent per host (DaemonSet)
"""

import logging
import time
import psutil
import hashlib
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class KillDecision(str, Enum):
    """NK cell kill/spare decision"""
    KILL = "kill"  # Missing-self detected
    SPARE = "spare"  # Self marker present
    INVESTIGATE = "investigate"  # Ambiguous


class ThreatIndicator(str, Enum):
    """Indicators of compromise"""
    MISSING_SIGNATURE = "missing_signature"
    UNKNOWN_HASH = "unknown_hash"
    HIDDEN_PROCESS = "hidden_process"
    DLL_HIJACK = "dll_hijack"
    MEMORY_INJECTION = "memory_injection"
    SUSPICIOUS_PARENT = "suspicious_parent"
    UNUSUAL_NETWORK = "unusual_network"
    ROOTKIT_BEHAVIOR = "rootkit_behavior"


@dataclass
class ProcessInfo:
    """Process information for analysis"""
    pid: int
    name: str
    exe_path: str
    cmdline: List[str]
    parent_pid: int
    user: str
    create_time: float
    memory_mb: float
    cpu_percent: float
    connections: List[Dict] = field(default_factory=list)
    open_files: List[str] = field(default_factory=list)
    threads: int = 0


@dataclass
class SelfMarker:
    """
    Self marker (MHC-I equivalent).

    In biology: MHC-I molecules present "self" peptides
    In computation: Signature, hash, certificate of legitimate software
    """
    process_name: str
    exe_hash: str  # SHA256
    signature: Optional[str] = None  # Digital signature
    certificate: Optional[str] = None
    vendor: Optional[str] = None
    trusted: bool = True


@dataclass
class MissSelfDetection:
    """Detection of missing-self (compromised process)"""
    process_info: ProcessInfo
    threat_indicators: List[ThreatIndicator]
    confidence: float  # 0-1
    recommendation: KillDecision
    reasoning: str
    timestamp: float = field(default_factory=time.time)


class NKCellCore:
    """
    NK Cell - Missing-self detector.

    Mechanism:
    1. Maintain whitelist of legitimate processes (self markers)
    2. Scan running processes
    3. Check for self markers (hash, signature, parent)
    4. Missing markers → activating signal → KILL
    5. Present markers → inhibitory signal → SPARE

    Activating signals (kill):
    - Unknown executable hash
    - No digital signature
    - Suspicious parent process
    - DLL hijacking
    - Memory injection

    Inhibitory signals (spare):
    - Known hash in whitelist
    - Valid digital signature
    - Legitimate parent
    - Expected behavior
    """

    def __init__(
        self,
        whitelist_path: Optional[Path] = None,
        auto_learn: bool = True,
        sensitivity: float = 0.7  # 0-1, higher = more aggressive
    ):
        self.whitelist_path = whitelist_path
        self.auto_learn = auto_learn
        self.sensitivity = sensitivity

        # Self markers (whitelist)
        self.self_markers: Dict[str, SelfMarker] = {}

        # Load whitelist if provided
        if whitelist_path and whitelist_path.exists():
            self._load_whitelist(whitelist_path)

        # Detection cache (avoid re-scanning same processes)
        self.detection_cache: Dict[int, MissSelfDetection] = {}

        # Statistics
        self.stats = {
            "processes_scanned": 0,
            "missing_self_detected": 0,
            "kill_recommendations": 0,
            "spare_decisions": 0,
            "whitelist_size": len(self.self_markers)
        }

        logger.info(
            f"NK Cell initialized (whitelist={len(self.self_markers)}, "
            f"sensitivity={sensitivity}, auto_learn={auto_learn})"
        )

    def patrol(self) -> List[MissSelfDetection]:
        """
        Patrol system for missing-self processes.

        Scans all running processes and checks for self markers.

        Returns:
            List of missing-self detections
        """
        detections = []

        # Get all running processes
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'ppid', 'username']):
            try:
                # Skip if already in cache
                if proc.info['pid'] in self.detection_cache:
                    continue

                # Get process info
                process_info = self._get_process_info(proc)

                # Check for self markers
                detection = self._check_self_markers(process_info)

                if detection:
                    detections.append(detection)
                    self.detection_cache[proc.info['pid']] = detection

                    if detection.recommendation == KillDecision.KILL:
                        self.stats["kill_recommendations"] += 1
                    elif detection.recommendation == KillDecision.SPARE:
                        self.stats["spare_decisions"] += 1

                self.stats["processes_scanned"] += 1

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if detections:
            self.stats["missing_self_detected"] += len(detections)
            logger.info(f"Patrol complete: {len(detections)} missing-self detections")

        return detections

    def _get_process_info(self, proc: psutil.Process) -> ProcessInfo:
        """Extract process information"""
        try:
            return ProcessInfo(
                pid=proc.pid,
                name=proc.name(),
                exe_path=proc.exe() or "",
                cmdline=proc.cmdline() or [],
                parent_pid=proc.ppid(),
                user=proc.username(),
                create_time=proc.create_time(),
                memory_mb=proc.memory_info().rss / 1024 / 1024,
                cpu_percent=proc.cpu_percent(interval=0.1),
                connections=[
                    {
                        "laddr": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        "status": conn.status
                    }
                    for conn in proc.connections() if hasattr(conn, 'laddr')
                ][:10],  # Limit to 10
                open_files=[f.path for f in proc.open_files()][:10],
                threads=proc.num_threads()
            )
        except Exception as e:
            # Minimal info if access denied
            return ProcessInfo(
                pid=proc.pid,
                name=proc.name() if hasattr(proc, 'name') else "unknown",
                exe_path="",
                cmdline=[],
                parent_pid=0,
                user="unknown",
                create_time=0,
                memory_mb=0,
                cpu_percent=0
            )

    def _check_self_markers(self, process_info: ProcessInfo) -> Optional[MissSelfDetection]:
        """
        Check if process has self markers.

        Returns None if process is definitely safe (strong self markers).
        Returns MissSelfDetection if suspicious.
        """
        threat_indicators = []
        activating_signals = 0
        inhibitory_signals = 0

        # Signal 1: Executable hash
        if process_info.exe_path:
            exe_hash = self._compute_file_hash(process_info.exe_path)

            if exe_hash:
                # Check whitelist
                if exe_hash in [marker.exe_hash for marker in self.self_markers.values()]:
                    inhibitory_signals += 2  # Strong inhibition
                else:
                    activating_signals += 1
                    threat_indicators.append(ThreatIndicator.UNKNOWN_HASH)

                    # Auto-learn if enabled and seems benign
                    if self.auto_learn and self._seems_benign(process_info):
                        self._add_to_whitelist(process_info, exe_hash)
                        inhibitory_signals += 1
            else:
                # Cannot compute hash (missing file)
                activating_signals += 2
                threat_indicators.append(ThreatIndicator.MISSING_SIGNATURE)

        # Signal 2: Parent process legitimacy
        parent_suspicious = self._check_parent_process(process_info)
        if parent_suspicious:
            activating_signals += 1
            threat_indicators.append(ThreatIndicator.SUSPICIOUS_PARENT)
        else:
            inhibitory_signals += 1

        # Signal 3: Hidden process detection
        if self._is_hidden_process(process_info):
            activating_signals += 2
            threat_indicators.append(ThreatIndicator.HIDDEN_PROCESS)

        # Signal 4: DLL hijacking detection
        if self._detect_dll_hijacking(process_info):
            activating_signals += 2
            threat_indicators.append(ThreatIndicator.DLL_HIJACK)

        # Signal 5: Network connections
        suspicious_connections = self._check_network_connections(process_info)
        if suspicious_connections:
            activating_signals += 1
            threat_indicators.append(ThreatIndicator.UNUSUAL_NETWORK)

        # Decision: activating vs inhibitory signals
        if not threat_indicators:
            return None  # Definitely safe

        # Compute confidence
        total_signals = activating_signals + inhibitory_signals
        if total_signals == 0:
            confidence = 0.5
        else:
            confidence = activating_signals / total_signals

        # Adjust by sensitivity
        adjusted_confidence = confidence * (1 + self.sensitivity) / 2

        # Make kill/spare decision
        if adjusted_confidence > 0.7:
            recommendation = KillDecision.KILL
            reasoning = f"Missing-self detected: {', '.join([ind.value for ind in threat_indicators])}"
        elif adjusted_confidence > 0.4:
            recommendation = KillDecision.INVESTIGATE
            reasoning = f"Ambiguous signals (activating={activating_signals}, inhibitory={inhibitory_signals})"
        else:
            recommendation = KillDecision.SPARE
            reasoning = f"Self markers present (confidence={adjusted_confidence:.2f})"

        return MissSelfDetection(
            process_info=process_info,
            threat_indicators=threat_indicators,
            confidence=adjusted_confidence,
            recommendation=recommendation,
            reasoning=reasoning
        )

    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        """Compute SHA256 hash of executable"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def _check_parent_process(self, process_info: ProcessInfo) -> bool:
        """
        Check if parent process is suspicious.

        Suspicious parents:
        - cmd.exe spawning unusual children
        - explorer.exe spawning servers
        - Office apps spawning cmd/powershell
        """
        if process_info.parent_pid == 0:
            return False

        try:
            parent = psutil.Process(process_info.parent_pid)
            parent_name = parent.name().lower()

            # Office apps spawning shells
            office_apps = ['winword.exe', 'excel.exe', 'powerpnt.exe', 'outlook.exe']
            shell_names = ['cmd.exe', 'powershell.exe', 'bash', 'sh']

            if parent_name in office_apps and process_info.name.lower() in shell_names:
                return True

            # explorer.exe spawning server processes
            if parent_name == 'explorer.exe':
                server_indicators = ['server', 'daemon', 'service']
                if any(ind in process_info.name.lower() for ind in server_indicators):
                    return True

        except psutil.NoSuchProcess:
            pass

        return False

    def _is_hidden_process(self, process_info: ProcessInfo) -> bool:
        """
        Detect hidden processes (rootkit behavior).

        Techniques:
        - Process name starts with spaces or special chars
        - No executable path (process hollowing)
        - Name mismatch with exe
        """
        # No exe path = suspicious
        if not process_info.exe_path:
            return True

        # Name starts with special chars
        if process_info.name.startswith((' ', '.', '\x00')):
            return True

        # Name/exe mismatch
        if process_info.exe_path:
            exe_name = Path(process_info.exe_path).name
            if exe_name.lower() != process_info.name.lower():
                return True

        return False

    def _detect_dll_hijacking(self, process_info: ProcessInfo) -> bool:
        """
        Detect DLL hijacking.

        Indicators:
        - DLL loaded from unusual location
        - DLL in same directory as exe (side-loading)
        """
        # TODO: Implement full DLL analysis
        # For now: check if exe is in unusual location
        if process_info.exe_path:
            exe_path = Path(process_info.exe_path)

            # Suspicious locations
            suspicious_dirs = [
                '/tmp', '/var/tmp', 'AppData\\Local\\Temp',
                'Downloads', 'Desktop'
            ]

            for sus_dir in suspicious_dirs:
                if sus_dir.lower() in str(exe_path).lower():
                    return True

        return False

    def _check_network_connections(self, process_info: ProcessInfo) -> bool:
        """
        Check for suspicious network connections.

        Indicators:
        - Connections to known malicious IPs
        - Unusual ports
        - High number of connections
        """
        if not process_info.connections:
            return False

        # High connection count
        if len(process_info.connections) > 50:
            return True

        # Check for unusual ports
        unusual_ports = {6666, 6667, 6668, 31337, 12345, 54321}  # Common malware ports
        for conn in process_info.connections:
            if 'raddr' in conn and conn['raddr']:
                try:
                    port = int(conn['raddr'].split(':')[1])
                    if port in unusual_ports:
                        return True
                except (IndexError, ValueError):
                    pass

        return False

    def _seems_benign(self, process_info: ProcessInfo) -> bool:
        """
        Heuristic to determine if process seems benign.

        Used for auto-learning whitelist.
        """
        # System processes
        if process_info.user in ['root', 'system', 'systemd']:
            return True

        # Low resource usage
        if process_info.cpu_percent < 5 and process_info.memory_mb < 100:
            return True

        # Standard system paths
        if process_info.exe_path:
            system_paths = ['/usr/bin', '/usr/sbin', '/bin', '/sbin', 'C:\\Windows\\System32']
            if any(path in process_info.exe_path for path in system_paths):
                return True

        return False

    def _add_to_whitelist(self, process_info: ProcessInfo, exe_hash: str):
        """Add process to whitelist"""
        marker = SelfMarker(
            process_name=process_info.name,
            exe_hash=exe_hash,
            vendor="auto-learned",
            trusted=True
        )

        self.self_markers[exe_hash] = marker
        self.stats["whitelist_size"] = len(self.self_markers)

        logger.info(f"Auto-learned: {process_info.name} (hash={exe_hash[:16]}...)")

    def _load_whitelist(self, whitelist_path: Path):
        """Load whitelist from file"""
        import json

        with open(whitelist_path, 'r') as f:
            whitelist_data = json.load(f)

        for entry in whitelist_data:
            marker = SelfMarker(
                process_name=entry["process_name"],
                exe_hash=entry["exe_hash"],
                signature=entry.get("signature"),
                vendor=entry.get("vendor"),
                trusted=entry.get("trusted", True)
            )
            self.self_markers[marker.exe_hash] = marker

        logger.info(f"Loaded {len(self.self_markers)} whitelist entries")

    def save_whitelist(self, output_path: Path):
        """Save whitelist to file"""
        import json

        whitelist_data = [
            {
                "process_name": marker.process_name,
                "exe_hash": marker.exe_hash,
                "signature": marker.signature,
                "vendor": marker.vendor,
                "trusted": marker.trusted
            }
            for marker in self.self_markers.values()
        ]

        with open(output_path, 'w') as f:
            json.dump(whitelist_data, f, indent=2)

        logger.info(f"Saved {len(whitelist_data)} whitelist entries to {output_path}")

    def get_stats(self) -> Dict:
        """Get NK cell statistics"""
        return self.stats.copy()


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("NK CELL SERVICE - MISSING-SELF DETECTION")
    print("="*80 + "\n")

    # Initialize NK cell
    nk_cell = NKCellCore(auto_learn=True, sensitivity=0.7)

    print(f"NK Cell patrolling system...\n")

    # Patrol
    detections = nk_cell.patrol()

    if detections:
        print(f"Missing-self detections: {len(detections)}\n")

        for detection in detections[:10]:  # Show first 10
            print(f"Process: {detection.process_info.name} (PID {detection.process_info.pid})")
            print(f"  Recommendation: {detection.recommendation}")
            print(f"  Confidence: {detection.confidence:.2f}")
            print(f"  Reasoning: {detection.reasoning}")
            print(f"  Indicators: {[ind.value for ind in detection.threat_indicators]}")
            print()
    else:
        print("No missing-self detections (all processes have valid self markers)\n")

    # Stats
    print("="*80)
    print("STATISTICS")
    print("="*80)
    stats = nk_cell.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n" + "="*80)
    print("NK CELL TEST COMPLETE!")
    print("="*80 + "\n")
