"""
Nmap Tool Executor
==================

Orchestrates Nmap execution with preset scan profiles.

Scan Types:
- quick: Fast scan (-F - top 100 ports)
- full: Comprehensive scan (-p- all ports + version detection)
- vuln: Vulnerability scan (NSE vuln scripts)
- service: Service/version detection only (-sV)
- os: OS detection (-O)

Example Usage:
    executor = NmapExecutor()

    # Quick scan
    result = executor.execute(target="10.10.1.5", scan_type="quick")

    # Full scan with OS detection
    result = executor.execute(
        target="192.168.1.0/24",
        scan_type="full",
        os_detection=True
    )

    # Custom options
    result = executor.execute(
        target="example.com",
        scan_type="service",
        custom_args=["-T4", "--max-retries", "2"]
    )
"""

from typing import List, Optional
from .base import ToolExecutor


class NmapExecutor(ToolExecutor):
    """Nmap tool executor with preset scan profiles."""

    tool_name = "nmap"
    version_command = ["nmap", "--version"]
    default_timeout = 600  # 10 minutes for Nmap scans

    SCAN_PROFILES = {
        "quick": ["-F"],  # Fast scan, top 100 ports
        "full": ["-p-", "-sV", "-sC"],  # All ports + version + default scripts
        "vuln": ["-sV", "--script=vuln"],  # Vulnerability scan
        "service": ["-sV"],  # Service detection
        "os": ["-O"],  # OS detection
        "default": ["-sS"],  # SYN scan (requires root)
    }

    def build_command(
        self,
        target: str,
        scan_type: str = "quick",
        ports: Optional[str] = None,
        os_detection: bool = False,
        traceroute: bool = False,
        timing: Optional[str] = None,  # T0-T5
        custom_args: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Build Nmap command.

        Args:
            target: IP, hostname, or CIDR (e.g., "10.10.1.5", "192.168.1.0/24")
            scan_type: Scan profile (quick, full, vuln, service, os, default)
            ports: Port specification (e.g., "22,80,443" or "1-1000")
            os_detection: Enable OS detection (-O)
            traceroute: Enable traceroute (--traceroute)
            timing: Timing template (T0-T5, e.g., "T4")
            custom_args: Additional Nmap arguments
            **kwargs: Ignored (allows flexibility)

        Returns:
            Command array
        """
        cmd = ["nmap"]

        # Apply scan profile
        profile_args = self.SCAN_PROFILES.get(scan_type, self.SCAN_PROFILES["default"])
        cmd.extend(profile_args)

        # Port specification (overrides profile)
        if ports:
            cmd.extend(["-p", ports])

        # Optional features
        if os_detection:
            cmd.append("-O")

        if traceroute:
            cmd.append("--traceroute")

        if timing:
            cmd.append(f"-{timing}")

        # Custom arguments
        if custom_args:
            cmd.extend(custom_args)

        # Output format: XML to stdout
        cmd.extend(["-oX", "-"])

        # Target (must be last)
        cmd.append(target)

        return cmd
