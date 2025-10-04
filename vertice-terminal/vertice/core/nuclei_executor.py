"""
Nuclei Tool Executor
====================

Orchestrates Nuclei vulnerability scanner execution.

Nuclei is a fast, template-based vulnerability scanner that uses YAML templates
to detect security issues across web apps, networks, DNS, etc.

Scan Types:
- quick: Fast scan with critical/high severity templates only
- full: Comprehensive scan with all templates
- web: Web application vulnerabilities (OWASP Top 10, etc.)
- network: Network-level vulnerabilities
- cve: Known CVE checks only
- custom: Custom template path

Example Usage:
    executor = NucleiExecutor()

    # Quick scan
    result = executor.execute(target="https://example.com", scan_type="quick")

    # Full scan with all templates
    result = executor.execute(target="https://example.com", scan_type="full")

    # Custom templates
    result = executor.execute(
        target="https://example.com",
        scan_type="custom",
        templates="/path/to/templates/"
    )

Output:
    Nuclei outputs JSON by default, making parsing straightforward.
    Each finding includes: template-id, severity, matched-at, etc.
"""

from typing import List, Optional
from .base import ToolExecutor


class NucleiExecutor(ToolExecutor):
    """Nuclei vulnerability scanner executor."""

    tool_name = "nuclei"
    version_command = ["nuclei", "-version"]
    default_timeout = 900  # 15 minutes for Nuclei scans

    # Nuclei template directories (relative to nuclei-templates repo)
    TEMPLATE_CATEGORIES = {
        "cve": "cves/",
        "web": "vulnerabilities/",
        "network": "network/",
        "dns": "dns/",
        "default": "default-logins/",
    }

    def build_command(
        self,
        target: str,
        scan_type: str = "quick",
        templates: Optional[str] = None,
        severity: Optional[List[str]] = None,
        rate_limit: int = 150,  # requests per second
        concurrency: int = 25,
        custom_args: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Build Nuclei command.

        Args:
            target: Target URL or host (e.g., "https://example.com", "10.10.1.5")
            scan_type: Scan profile (quick, full, web, network, cve, custom)
            templates: Custom template path (for scan_type="custom")
            severity: List of severities to include (critical, high, medium, low, info)
            rate_limit: Max requests per second (default: 150)
            concurrency: Concurrent templates to run (default: 25)
            custom_args: Additional Nuclei arguments
            **kwargs: Ignored (allows flexibility)

        Returns:
            Command array

        Notes:
            - Nuclei outputs JSON to stdout by default with -json flag
            - Rate limiting prevents overwhelming targets
            - Concurrency controls parallel template execution
        """
        cmd = ["nuclei"]

        # Target
        cmd.extend(["-u", target])

        # JSON output (parseable)
        cmd.append("-json")

        # Silent mode (no progress bars in JSON output)
        cmd.append("-silent")

        # Scan type profiles
        if scan_type == "quick":
            # Only critical and high severity
            cmd.extend(["-s", "critical,high"])
        elif scan_type == "full":
            # All templates (default behavior)
            pass
        elif scan_type == "web":
            # Web vulnerabilities + OWASP
            cmd.extend(["-t", "vulnerabilities/", "-t", "exposures/"])
        elif scan_type == "network":
            # Network-level checks
            cmd.extend(["-t", "network/"])
        elif scan_type == "cve":
            # CVE checks only
            cmd.extend(["-t", "cves/"])
        elif scan_type == "custom":
            # Custom template path
            if templates:
                cmd.extend(["-t", templates])
            else:
                raise ValueError("scan_type='custom' requires 'templates' parameter")

        # Severity filter (overrides scan_type if provided)
        if severity:
            severity_str = ",".join(severity)
            cmd.extend(["-s", severity_str])

        # Rate limiting
        cmd.extend(["-rl", str(rate_limit)])

        # Concurrency
        cmd.extend(["-c", str(concurrency)])

        # Disable automatic template updates during scan
        cmd.append("-duc")

        # Custom arguments
        if custom_args:
            cmd.extend(custom_args)

        return cmd
