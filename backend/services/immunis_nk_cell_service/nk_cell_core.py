"""Immunis System - Natural Killer (NK) Cell Core Logic.

This module simulates the function of Natural Killer (NK) cells, a component of
the innate immune system. NK cells are best known for "missing-self detection,"
where they identify and kill cells that fail to present a "self" marker
(the MHC-I molecule).

Biological Analogy:
-   **MHC-I (Self Marker)**: A legitimate digital signature, a known-good file
    hash, or a process originating from a trusted source.
-   **Missing Self**: An executable that is unsigned, has an unknown hash, or is
    running from a suspicious location.
-   **Activating Signals**: Indicators of compromise (e.g., suspicious parent process).
-   **Inhibitory Signals**: The presence of a valid "self" marker.
-   **Lethal Hit**: A recommendation to terminate the suspicious process.
"""

import logging
import psutil
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class KillDecision(str, Enum):
    """Enumeration for the kill/spare decision of an NK cell."""
    KILL = "kill"
    SPARE = "spare"
    INVESTIGATE = "investigate"


class ThreatIndicator(str, Enum):
    """Enumeration for indicators that suggest a process might be compromised."""
    UNKNOWN_HASH = "unknown_hash"
    SUSPICIOUS_PARENT = "suspicious_parent"
    HIDDEN_PROCESS = "hidden_process"


@dataclass
class ProcessInfo:
    """Represents the collected information about a running process."""
    pid: int
    name: str
    exe_path: Optional[str]
    parent_pid: Optional[int]


@dataclass
class MissSelfDetection:
    """Represents a detection event where a process is missing a "self" marker.

    Attributes:
        process_info (ProcessInfo): The details of the suspicious process.
        threat_indicators (List[ThreatIndicator]): The list of indicators that were found.
        confidence (float): The confidence score for this detection.
        recommendation (KillDecision): The recommended action (kill, spare, or investigate).
    """
    process_info: ProcessInfo
    threat_indicators: List[ThreatIndicator]
    confidence: float
    recommendation: KillDecision
    reasoning: str


class NKCellCore:
    """Simulates a Natural Killer (NK) cell for missing-self detection.

    This class scans running processes on a host, checks them against a whitelist
    of known-good applications (self markers), and identifies processes that are
    unknown or exhibit suspicious characteristics.
    """

    def __init__(self, sensitivity: float = 0.7):
        """Initializes the NKCellCore.

        Args:
            sensitivity (float): The sensitivity of the NK cell (0.0 to 1.0).
                Higher values make it more likely to recommend a kill action.
        """
        self.sensitivity = sensitivity
        self.self_markers: Dict[str, str] = {} # {exe_hash: process_name}
        self.stats = {"processes_scanned": 0, "missing_self_detected": 0}

    def patrol(self) -> List[MissSelfDetection]:
        """Performs a patrol, scanning all running processes for missing-self markers.

        Returns:
            List[MissSelfDetection]: A list of all suspicious processes found.
        """
        detections = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'ppid']):
            try:
                info = ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    exe_path=proc.exe(),
                    parent_pid=proc.ppid()
                )
                detection = self._check_self_markers(info)
                if detection:
                    detections.append(detection)
                self.stats["processes_scanned"] += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        self.stats["missing_self_detected"] += len(detections)
        return detections

    def _check_self_markers(self, proc_info: ProcessInfo) -> Optional[MissSelfDetection]:
        """Checks a single process for self markers and other threat indicators.

        Args:
            proc_info (ProcessInfo): The process to check.

        Returns:
            Optional[MissSelfDetection]: A detection object if the process is
                suspicious, otherwise None.
        """
        activating_signals = 0
        inhibitory_signals = 0
        indicators = []

        # Check hash against whitelist (inhibitory signal)
        exe_hash = self._compute_file_hash(proc_info.exe_path) if proc_info.exe_path else None
        if exe_hash and exe_hash in self.self_markers:
            inhibitory_signals += 2
        elif exe_hash:
            activating_signals += 1
            indicators.append(ThreatIndicator.UNKNOWN_HASH)

        # Check for suspicious parent (activating signal)
        if self._is_suspicious_parent(proc_info):
            activating_signals += 1
            indicators.append(ThreatIndicator.SUSPICIOUS_PARENT)

        if not indicators: return None # Process appears safe

        # Make decision based on balance of signals
        confidence = activating_signals / (activating_signals + inhibitory_signals + 1e-6)
        if confidence * self.sensitivity > 0.7:
            recommendation = KillDecision.KILL
        elif confidence * self.sensitivity > 0.4:
            recommendation = KillDecision.INVESTIGATE
        else:
            recommendation = KillDecision.SPARE

        return MissSelfDetection(proc_info, indicators, confidence, recommendation, "Balance of signals")

    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        """Computes the SHA256 hash of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (FileNotFoundError, PermissionError):
            return None

    def _is_suspicious_parent(self, proc_info: ProcessInfo) -> bool:
        """Checks if a process has a suspicious parent (e.g., Word spawning PowerShell)."""
        # Simplified logic for demonstration
        try:
            parent = psutil.Process(proc_info.parent_pid)
            if parent.name().lower() in ["winword.exe", "excel.exe"] and proc_info.name.lower() == "powershell.exe":
                return True
        except psutil.NoSuchProcess:
            pass
        return False

    def get_stats(self) -> Dict[str, int]:
        """Returns a dictionary of performance statistics."""
        return self.stats