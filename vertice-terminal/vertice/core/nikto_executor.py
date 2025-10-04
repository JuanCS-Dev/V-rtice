"""
Nikto Tool Executor
===================

Orchestrates Nikto web vulnerability scanner execution.

Nikto is a comprehensive web server scanner that detects:
- Outdated server versions
- Dangerous files and CGIs
- Server misconfigurations
- SSL/TLS issues
- Injection vulnerabilities

Scan Types:
- quick: Fast scan with common checks only
- full: Comprehensive scan with all plugins
- ssl: SSL/TLS-focused scan
- headers: HTTP headers security analysis
- custom: Custom options

Example Usage:
    executor = NiktoExecutor()

    # Quick scan
    result = executor.execute(target="https://example.com", scan_type="quick")

    # Full scan with tuning
    result = executor.execute(
        target="https://example.com",
        scan_type="full",
        tuning="1234"  # Enable specific tests
    )

Output:
    Nikto outputs text by default. We use -Format txt for consistent parsing.
    Each finding includes: OSVDB ID, URI, description, HTTP method.
"""

from typing import List, Optional
from .base import ToolExecutor


class NiktoExecutor(ToolExecutor):
    """Nikto web vulnerability scanner executor."""

    tool_name = "nikto"
    version_command = ["nikto", "-Version"]
    default_timeout = 600  # 10 minutes for web scans

    # Nikto tuning options
    # 1 = Interesting File / Seen in logs
    # 2 = Misconfiguration / Default File
    # 3 = Information Disclosure
    # 4 = Injection (XSS/Script/HTML)
    # 5 = Remote File Retrieval - Inside Web Root
    # 6 = Denial of Service
    # 7 = Remote File Retrieval - Server Wide
    # 8 = Command Execution / Remote Shell
    # 9 = SQL Injection
    # a = Authentication Bypass
    # b = Software Identification
    # c = Remote Source Inclusion
    # x = Reverse Tuning Options (exclude)

    SCAN_PROFILES = {
        "quick": {
            "tuning": "123b",  # Files, misconfig, info disclosure, software ID
            "timeout": 300
        },
        "full": {
            "tuning": None,  # All tests
            "timeout": 900
        },
        "ssl": {
            "tuning": "3b",  # Info disclosure + software ID
            "ssl": True,
            "timeout": 300
        },
        "headers": {
            "tuning": "23",  # Misconfig + info disclosure
            "timeout": 180
        },
    }

    def build_command(
        self,
        target: str,
        scan_type: str = "quick",
        tuning: Optional[str] = None,
        plugins: Optional[str] = None,
        ssl: bool = False,
        timeout: Optional[int] = None,
        custom_args: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Build Nikto command.

        Args:
            target: Target URL (e.g., "https://example.com", "http://10.10.1.5:8080")
            scan_type: Scan profile (quick, full, ssl, headers, custom)
            tuning: Tuning options (e.g., "1234", "x6" to exclude DoS)
            plugins: Specific plugins to run (e.g., "@@ALL", "apache")
            ssl: Force SSL mode (ignores cert errors)
            timeout: Max scan time in seconds
            custom_args: Additional Nikto arguments
            **kwargs: Ignored (allows flexibility)

        Returns:
            Command array

        Notes:
            - Nikto outputs text to stdout by default
            - -Format txt ensures consistent parsing
            - -nointeractive disables prompts
            - -ask no = don't ask to submit to CIRT
        """
        cmd = ["nikto"]

        # Target (can be URL or host)
        cmd.extend(["-h", target])

        # Output format (text for parsing)
        cmd.extend(["-Format", "txt"])

        # No interactive prompts
        cmd.append("-nointeractive")

        # Don't ask to submit findings
        cmd.extend(["-ask", "no"])

        # Apply scan profile
        profile = self.SCAN_PROFILES.get(scan_type, {})

        # Tuning (override profile if provided)
        tuning_opt = tuning or profile.get("tuning")
        if tuning_opt:
            cmd.extend(["-Tuning", tuning_opt])

        # Plugins
        if plugins:
            cmd.extend(["-Plugins", plugins])

        # SSL mode
        if ssl or profile.get("ssl"):
            cmd.append("-ssl")

        # Timeout
        timeout_val = timeout or profile.get("timeout") or self.default_timeout
        cmd.extend(["-timeout", str(timeout_val)])

        # Custom arguments
        if custom_args:
            cmd.extend(custom_args)

        return cmd
