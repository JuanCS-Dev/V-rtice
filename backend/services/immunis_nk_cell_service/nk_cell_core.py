"""Immunis NK Cell Service - Production-Ready Missing-Self Detection

Bio-inspired Natural Killer Cell service that detects and eliminates
compromised entities lacking proper identification:

1. **Missing-Self Detection**: Processes without legitimate identity
   - No valid code signature
   - Not in whitelist
   - Suspicious parent-child relationships
   - Unusual execution paths

2. **DLL Hijacking Detection**: Detects malicious library loading
   - DLL load order hijacking
   - Path anomalies (non-system DLLs in system paths)
   - Unsigned DLLs loaded by signed processes

3. **Process Whitelist Management**: Known-good process validation
   - SHA256 hash verification
   - Code signature validation
   - Path whitelisting

Like biological NK cells: Kills targets missing MHC-I (self-markers).
NO MOCKS - Production-ready implementation.
"""

import json
import logging
import os
import platform
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Platform-specific imports
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


class ProcessWhitelist:
    """Manages whitelist of known-good processes."""

    def __init__(self, whitelist_path: Optional[str] = None):
        """Initialize process whitelist.

        Args:
            whitelist_path: Path to whitelist JSON file
        """
        self.whitelist_path = whitelist_path or "/app/whitelist/processes.json"
        self.whitelisted_hashes: Set[str] = set()
        self.whitelisted_paths: Set[str] = set()
        self.whitelisted_names: Set[str] = set()
        self.last_reload: Optional[datetime] = None

    def load_whitelist(self) -> Dict[str, Any]:
        """Load whitelist from file.

        Returns:
            Load statistics
        """
        try:
            if not os.path.exists(self.whitelist_path):
                logger.warning(f"Whitelist file not found: {self.whitelist_path}, using defaults")
                self._load_default_whitelist()
                return {
                    "status": "default_loaded",
                    "entries": len(self.whitelisted_names),
                }

            with open(self.whitelist_path, "r") as f:
                whitelist_data = json.load(f)

            self.whitelisted_hashes = set(whitelist_data.get("hashes", []))
            self.whitelisted_paths = set(whitelist_data.get("paths", []))
            self.whitelisted_names = set(whitelist_data.get("names", []))

            self.last_reload = datetime.now()

            logger.info(
                f"Whitelist loaded: {len(self.whitelisted_hashes)} hashes, "
                f"{len(self.whitelisted_paths)} paths, {len(self.whitelisted_names)} names"
            )

            return {
                "status": "loaded",
                "hashes_count": len(self.whitelisted_hashes),
                "paths_count": len(self.whitelisted_paths),
                "names_count": len(self.whitelisted_names),
                "timestamp": self.last_reload.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")
            self._load_default_whitelist()
            return {"status": "error", "error": str(e), "fallback": "default"}

    def _load_default_whitelist(self):
        """Load platform-specific default whitelist."""
        if IS_LINUX:
            self.whitelisted_paths = {
                "/usr/bin/",
                "/usr/sbin/",
                "/bin/",
                "/sbin/",
                "/usr/local/bin/",
                "/usr/local/sbin/",
            }
            self.whitelisted_names = {
                "systemd",
                "sshd",
                "dockerd",
                "containerd",
                "kubelet",
                "python3",
                "bash",
                "sh",
                "nginx",
                "apache2",
            }
        elif IS_WINDOWS:
            self.whitelisted_paths = {
                "C:\\Windows\\System32\\",
                "C:\\Windows\\SysWOW64\\",
                "C:\\Program Files\\",
                "C:\\Program Files (x86)\\",
            }
            self.whitelisted_names = {
                "svchost.exe",
                "lsass.exe",
                "services.exe",
                "explorer.exe",
                "System",
                "Registry",
                "smss.exe",
                "csrss.exe",
            }

    def is_whitelisted(
        self, process_name: str, process_path: str, process_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if process is whitelisted.

        Args:
            process_name: Process executable name
            process_path: Full process path
            process_hash: SHA256 hash of executable

        Returns:
            Whitelist check result
        """
        reasons = []

        # Check hash (highest confidence)
        if process_hash and process_hash in self.whitelisted_hashes:
            return {"whitelisted": True, "reason": "hash_match", "confidence": 0.99}

        # Check exact path
        if process_path in self.whitelisted_paths:
            reasons.append("exact_path_match")

        # Check path prefix
        for whitelisted_path in self.whitelisted_paths:
            if process_path.startswith(whitelisted_path):
                reasons.append("path_prefix_match")
                break

        # Check process name
        if process_name in self.whitelisted_names:
            reasons.append("name_match")

        if reasons:
            confidence = 0.70 if "name_match" in reasons else 0.85
            return {
                "whitelisted": True,
                "reason": ", ".join(reasons),
                "confidence": confidence,
            }

        return {"whitelisted": False, "reason": "not_in_whitelist", "confidence": 0.0}


class MissingSelfDetector:
    """Detects processes lacking proper self-identification markers."""

    def __init__(self, whitelist: ProcessWhitelist):
        """Initialize missing-self detector.

        Args:
            whitelist: Process whitelist instance
        """
        self.whitelist = whitelist

    async def detect_missing_self(self, process_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if process lacks proper self-identification.

        Args:
            process_info: Process information dictionary

        Returns:
            Detection result with missing-self indicators
        """
        missing_self_indicators = []
        severity_score = 0.0

        process_name = process_info.get("name", "unknown")
        process_path = process_info.get("path", "")
        process_hash = process_info.get("hash")
        parent_name = process_info.get("parent_name", "")
        cmdline = process_info.get("cmdline", "")

        # 1. Check whitelist
        whitelist_result = self.whitelist.is_whitelisted(process_name, process_path, process_hash)

        if not whitelist_result["whitelisted"]:
            missing_self_indicators.append("not_in_whitelist")
            severity_score += 0.3

        # 2. Check code signature (if available)
        if not process_info.get("signed", False):
            missing_self_indicators.append("unsigned_executable")
            severity_score += 0.4

        # 3. Check suspicious execution paths
        if self._is_suspicious_path(process_path):
            missing_self_indicators.append("suspicious_execution_path")
            severity_score += 0.5

        # 4. Check parent-child relationship anomalies
        if self._is_suspicious_parent_child(process_name, parent_name):
            missing_self_indicators.append("suspicious_parent_child_relationship")
            severity_score += 0.3

        # 5. Check for obfuscated/randomized names
        if self._is_obfuscated_name(process_name):
            missing_self_indicators.append("obfuscated_process_name")
            severity_score += 0.4

        # 6. Check for suspicious command-line arguments
        if self._has_suspicious_cmdline(cmdline):
            missing_self_indicators.append("suspicious_cmdline_args")
            severity_score += 0.3

        # Normalize severity score
        severity_score = min(severity_score, 1.0)

        missing_self = len(missing_self_indicators) > 0
        risk_level = self._calculate_risk_level(severity_score)

        return {
            "missing_self_detected": missing_self,
            "severity_score": severity_score,
            "risk_level": risk_level,
            "indicators": missing_self_indicators,
            "process_name": process_name,
            "process_path": process_path,
            "timestamp": datetime.now().isoformat(),
        }

    def _is_suspicious_path(self, path: str) -> bool:
        """Check if execution path is suspicious."""
        suspicious_paths = [
            "/tmp/",
            "/var/tmp/",
            "C:\\Temp\\",
            "C:\\Windows\\Temp\\",
            "/dev/shm/",
            "AppData\\Local\\Temp\\",
            "Downloads\\",
        ]

        for susp_path in suspicious_paths:
            if susp_path in path:
                return True
        return False

    def _is_suspicious_parent_child(self, process_name: str, parent_name: str) -> bool:
        """Check for suspicious parent-child relationships."""
        # Suspicious: svchost.exe child of cmd.exe
        suspicious_pairs = [
            ("svchost.exe", "cmd.exe"),
            ("svchost.exe", "powershell.exe"),
            ("lsass.exe", "cmd.exe"),
            ("services.exe", "explorer.exe"),
        ]

        for child, parent in suspicious_pairs:
            if process_name == child and parent_name == parent:
                return True

        return False

    def _is_obfuscated_name(self, name: str) -> bool:
        """Check if process name appears obfuscated."""
        # Random-looking names (e.g., "x7g2k.exe", "tmp_abc123.bin")
        if re.match(r"^[a-z0-9]{6,12}\.(exe|bin|dll)$", name, re.IGNORECASE):
            return True

        # All uppercase random chars
        if re.match(r"^[A-Z0-9]{8,}\.exe$", name):
            return True

        return False

    def _has_suspicious_cmdline(self, cmdline: str) -> bool:
        """Check for suspicious command-line patterns."""
        suspicious_patterns = [
            r"powershell.*-enc\s+",  # Encoded PowerShell
            r"cmd.*/c\s+echo.*\|",  # Command injection
            r"wget.*http.*\|\s*sh",  # Download and execute
            r"curl.*\|\s*bash",  # Download and execute
            r"base64\s+-d",  # Base64 decoding
            r"eval\(",  # Code evaluation
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, cmdline, re.IGNORECASE):
                return True

        return False

    def _calculate_risk_level(self, severity_score: float) -> str:
        """Calculate risk level from severity score."""
        if severity_score >= 0.8:
            return "CRITICAL"
        elif severity_score >= 0.6:
            return "HIGH"
        elif severity_score >= 0.4:
            return "MEDIUM"
        elif severity_score >= 0.2:
            return "LOW"
        else:
            return "INFO"


class DLLHijackDetector:
    """Detects DLL hijacking attempts."""

    def __init__(self):
        """Initialize DLL hijack detector."""
        self.system_dll_paths = self._get_system_dll_paths()

    def _get_system_dll_paths(self) -> Set[str]:
        """Get legitimate system DLL paths."""
        if IS_WINDOWS:
            return {
                "C:\\Windows\\System32\\",
                "C:\\Windows\\SysWOW64\\",
                "C:\\Windows\\WinSxS\\",
            }
        elif IS_LINUX:
            return {"/lib/", "/lib64/", "/usr/lib/", "/usr/lib64/", "/usr/local/lib/"}
        return set()

    async def detect_dll_hijacking(
        self, process_info: Dict[str, Any], loaded_libraries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect DLL hijacking in process.

        Args:
            process_info: Process information
            loaded_libraries: List of loaded DLLs/SOs

        Returns:
            Detection result
        """
        hijacking_indicators = []
        suspicious_dlls = []
        severity_score = 0.0

        process_signed = process_info.get("signed", False)

        for lib in loaded_libraries:
            lib_path = lib.get("path", "")
            lib_name = lib.get("name", "")
            lib_signed = lib.get("signed", False)

            # 1. Unsigned DLL loaded by signed process
            if process_signed and not lib_signed:
                hijacking_indicators.append("unsigned_dll_in_signed_process")
                suspicious_dlls.append({"name": lib_name, "reason": "unsigned"})
                severity_score += 0.4

            # 2. DLL not in system path
            if not any(lib_path.startswith(sys_path) for sys_path in self.system_dll_paths):
                # Check if it's in application directory (legitimate)
                app_dir = os.path.dirname(process_info.get("path", ""))
                if not lib_path.startswith(app_dir):
                    hijacking_indicators.append("dll_outside_expected_paths")
                    suspicious_dlls.append({"name": lib_name, "reason": "unexpected_path"})
                    severity_score += 0.3

            # 3. Known DLL hijacking targets
            if self._is_hijackable_dll(lib_name):
                hijacking_indicators.append("known_hijackable_dll")
                suspicious_dlls.append({"name": lib_name, "reason": "known_target"})
                severity_score += 0.5

            # 4. DLL in temp/suspicious directory
            if any(susp in lib_path for susp in ["/tmp/", "Temp\\", "AppData\\Local\\Temp\\"]):
                hijacking_indicators.append("dll_in_temp_directory")
                suspicious_dlls.append({"name": lib_name, "reason": "temp_path"})
                severity_score += 0.6

        severity_score = min(severity_score, 1.0)
        hijacking_detected = len(hijacking_indicators) > 0

        return {
            "hijacking_detected": hijacking_detected,
            "severity_score": severity_score,
            "indicators": list(set(hijacking_indicators)),
            "suspicious_dlls": suspicious_dlls,
            "process_name": process_info.get("name"),
            "timestamp": datetime.now().isoformat(),
        }

    def _is_hijackable_dll(self, dll_name: str) -> bool:
        """Check if DLL is commonly targeted for hijacking."""
        # Common DLL hijacking targets (Windows)
        hijackable_dlls = {
            "dwmapi.dll",
            "uxtheme.dll",
            "cryptbase.dll",
            "comctl32.dll",
            "version.dll",
            "wtsapi32.dll",
            "propsys.dll",
            "explorerframe.dll",
        }

        return dll_name.lower() in hijackable_dlls


class NKCellCore:
    """Production-ready NK Cell service for missing-self detection.

    Detects and eliminates entities lacking proper identification:
    - Missing-self detection (no valid identity markers)
    - DLL hijacking detection
    - Process whitelist enforcement
    """

    def __init__(self, whitelist_path: Optional[str] = None, dry_run: bool = True):
        """Initialize NK Cell Core.

        Args:
            whitelist_path: Path to process whitelist file
            dry_run: Enable dry-run mode (no actual elimination)
        """
        self.whitelist = ProcessWhitelist(whitelist_path)
        self.missing_self_detector = MissingSelfDetector(self.whitelist)
        self.dll_hijack_detector = DLLHijackDetector()

        self.dry_run = dry_run
        self.detections: List[Dict[str, Any]] = []
        self.eliminations: List[Dict[str, Any]] = []
        self.last_scan_time: Optional[datetime] = None

        # Load whitelist on initialization
        self.whitelist.load_whitelist()

        logger.info(f"NKCellCore initialized (dry_run={dry_run})")

    async def scan_process(
        self,
        process_info: Dict[str, Any],
        loaded_libraries: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Scan process for missing-self and DLL hijacking.

        Args:
            process_info: Process information dictionary
            loaded_libraries: List of loaded DLLs/SOs (optional)

        Returns:
            Scan result with detection findings
        """
        logger.info(f"Scanning process: {process_info.get('name')} (PID: {process_info.get('pid')})")

        scan_start = datetime.now()

        # 1. Missing-self detection
        missing_self_result = await self.missing_self_detector.detect_missing_self(process_info)

        # 2. DLL hijacking detection (if libraries provided)
        dll_hijack_result = None
        if loaded_libraries:
            dll_hijack_result = await self.dll_hijack_detector.detect_dll_hijacking(process_info, loaded_libraries)

        # 3. Aggregate threat assessment
        threat_detected = missing_self_result["missing_self_detected"] or (
            dll_hijack_result and dll_hijack_result["hijacking_detected"]
        )

        # Calculate combined severity
        combined_severity = missing_self_result["severity_score"]
        if dll_hijack_result:
            combined_severity = max(combined_severity, dll_hijack_result["severity_score"])

        scan_result = {
            "timestamp": datetime.now().isoformat(),
            "process_id": process_info.get("pid"),
            "process_name": process_info.get("name"),
            "threat_detected": threat_detected,
            "severity_score": combined_severity,
            "missing_self": missing_self_result,
            "dll_hijacking": dll_hijack_result,
            "requires_elimination": combined_severity >= 0.6,
            "scan_duration_ms": (datetime.now() - scan_start).total_seconds() * 1000,
        }

        self.detections.append(scan_result)
        self.last_scan_time = datetime.now()

        logger.info(
            f"Scan complete: threat_detected={threat_detected}, "
            f"severity={combined_severity:.2f}, duration={scan_result['scan_duration_ms']:.1f}ms"
        )

        return scan_result

    async def eliminate_entity(self, entity_id: str, entity_type: str, reason: str, severity: float) -> Dict[str, Any]:
        """Eliminate compromised entity.

        Args:
            entity_id: Entity identifier (PID, container ID, etc.)
            entity_type: Type of entity (process, container, etc.)
            reason: Elimination reason
            severity: Threat severity score

        Returns:
            Elimination result
        """
        logger.warning(f"Eliminating entity {entity_id} (type={entity_type}, severity={severity:.2f}): {reason}")

        if self.dry_run:
            elimination_result = {
                "timestamp": datetime.now().isoformat(),
                "entity_id": entity_id,
                "entity_type": entity_type,
                "action": "eliminate",
                "reason": reason,
                "severity": severity,
                "dry_run": True,
                "status": "simulated",
                "message": f"DRY-RUN: Would eliminate {entity_type} {entity_id}",
            }
            logger.info(f"DRY-RUN: Would eliminate {entity_type} {entity_id}")
        else:
            # Production elimination logic
            try:
                if entity_type == "process":
                    success = await self._kill_process(entity_id)
                elif entity_type == "container":
                    success = await self._stop_container(entity_id)
                else:
                    success = False
                    logger.error(f"Unknown entity type: {entity_type}")

                elimination_result = {
                    "timestamp": datetime.now().isoformat(),
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "action": "eliminate",
                    "reason": reason,
                    "severity": severity,
                    "dry_run": False,
                    "status": "success" if success else "failed",
                    "message": (f"Eliminated {entity_type} {entity_id}" if success else "Elimination failed"),
                }

            except Exception as e:
                logger.error(f"Elimination failed: {e}")
                elimination_result = {
                    "timestamp": datetime.now().isoformat(),
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "action": "eliminate",
                    "reason": reason,
                    "severity": severity,
                    "dry_run": False,
                    "status": "error",
                    "message": str(e),
                }

        self.eliminations.append(elimination_result)
        return elimination_result

    async def _kill_process(self, pid: str) -> bool:
        """Kill process by PID.

        Args:
            pid: Process ID

        Returns:
            True if successful
        """
        try:
            import signal

            os.kill(int(pid), signal.SIGKILL)
            logger.info(f"Process {pid} killed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            return False

    async def _stop_container(self, container_id: str) -> bool:
        """Stop Docker container.

        Args:
            container_id: Container ID

        Returns:
            True if successful
        """
        try:
            import subprocess

            result = subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=10)
            success = result.returncode == 0
            if success:
                logger.info(f"Container {container_id} stopped successfully")
            else:
                logger.error(f"Failed to stop container {container_id}: {result.stderr}")
            return success
        except Exception as e:
            logger.error(f"Failed to stop container {container_id}: {e}")
            return False

    async def reload_whitelist(self) -> Dict[str, Any]:
        """Reload process whitelist.

        Returns:
            Reload result
        """
        logger.info("Reloading process whitelist...")
        return self.whitelist.load_whitelist()

    async def get_status(self) -> Dict[str, Any]:
        """Get NK Cell service status.

        Returns:
            Service status dictionary
        """
        return {
            "status": "operational",
            "dry_run_mode": self.dry_run,
            "detections_count": len(self.detections),
            "eliminations_count": len(self.eliminations),
            "last_scan": (self.last_scan_time.isoformat() if self.last_scan_time else "N/A"),
            "whitelist_status": {
                "last_reload": (self.whitelist.last_reload.isoformat() if self.whitelist.last_reload else "N/A"),
                "hashes_count": len(self.whitelist.whitelisted_hashes),
                "paths_count": len(self.whitelist.whitelisted_paths),
                "names_count": len(self.whitelist.whitelisted_names),
            },
        }

    def enable_production_mode(self):
        """Enable production mode (DISABLES dry-run)."""
        logger.warning("⚠️  PRODUCTION MODE ENABLED - Real eliminations will occur!")
        self.dry_run = False
