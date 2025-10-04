"""
Nikto Text Parser
=================

Parses Nikto text output into structured data compatible with Workspace.

Input: Nikto text output (-Format txt)
Output: Structured dict with web vulnerabilities

Nikto Output Format:
    - Nikto v2.5.0
    ---------------------------------------------------------------------------
    + Target IP:          10.10.1.5
    + Target Hostname:    example.com
    + Target Port:        80
    + Start Time:         2024-01-10 15:30:00 (GMT0)
    ---------------------------------------------------------------------------
    + Server: Apache/2.4.41 (Ubuntu)
    + The anti-clickjacking X-Frame-Options header is not present.
    + OSVDB-3268: /icons/: Directory indexing found.
    + /login.php: Admin login page/section found.
    + 8065 requests: 0 error(s) and 7 item(s) reported on remote host
    + End Time:           2024-01-10 15:35:00 (GMT0) (300 seconds)
    ---------------------------------------------------------------------------

Example Output:
    {
        "scan_info": {
            "target_ip": "10.10.1.5",
            "target_hostname": "example.com",
            "target_port": 80,
            "server": "Apache/2.4.41 (Ubuntu)",
            "total_requests": 8065,
            "total_findings": 7
        },
        "findings": [
            {
                "uri": "/icons/",
                "description": "Directory indexing found",
                "osvdb_id": "3268",
                "severity": "medium",
                "category": "information_disclosure"
            }
        ]
    }
"""

import re
from typing import Dict, List, Any, Optional
from ..base import ToolParser
import logging

logger = logging.getLogger(__name__)


class NiktoParser(ToolParser):
    """Parser for Nikto text output."""

    # Severity keywords for classification
    SEVERITY_KEYWORDS = {
        "critical": ["remote code execution", "rce", "shell", "command injection"],
        "high": ["sql injection", "authentication bypass", "password", "credential"],
        "medium": ["directory indexing", "outdated", "misconfiguration", "disclosure"],
        "low": ["banner", "version", "information leak"],
        "info": ["server:", "start time:", "end time:", "tested"]
    }

    def parse(self, output: str) -> Dict[str, Any]:
        """
        Parse Nikto text output.

        Args:
            output: Raw Nikto text output

        Returns:
            Structured data with findings

        Raises:
            ValueError: If output is invalid
        """
        if not output or not output.strip():
            return {
                "scan_info": {
                    "total_findings": 0,
                    "total_requests": 0
                },
                "findings": []
            }

        lines = output.strip().split('\n')

        # Extract metadata
        scan_info = self._parse_scan_info(lines)

        # Extract findings
        findings = self._parse_findings(lines)

        # Update scan info with findings count
        scan_info["total_findings"] = len(findings)

        return {
            "scan_info": scan_info,
            "findings": findings
        }

    def _parse_scan_info(self, lines: List[str]) -> Dict[str, Any]:
        """Extract scan metadata."""
        info = {
            "target_ip": None,
            "target_hostname": None,
            "target_port": None,
            "server": None,
            "total_requests": 0
        }

        for line in lines:
            line = line.strip()

            if "+ Target IP:" in line:
                info["target_ip"] = line.split(":")[-1].strip()
            elif "+ Target Hostname:" in line:
                info["target_hostname"] = line.split(":")[-1].strip()
            elif "+ Target Port:" in line:
                try:
                    info["target_port"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("+ Server:"):
                info["server"] = line.replace("+ Server:", "").strip()
            elif "requests:" in line and "item(s) reported" in line:
                # "8065 requests: 0 error(s) and 7 item(s) reported"
                match = re.search(r'(\d+)\s+requests?:', line)
                if match:
                    info["total_requests"] = int(match.group(1))

        return info

    def _parse_findings(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract vulnerability findings."""
        findings = []

        for line in lines:
            line = line.strip()

            # Skip non-finding lines
            if not line.startswith("+"):
                continue

            # Skip metadata lines
            if any(skip in line.lower() for skip in [
                "target ip:", "target hostname:", "target port:",
                "start time:", "end time:", "host(s) tested",
                "requests:", "nikto v"
            ]):
                continue

            # Skip separator lines
            if line.strip() == "+" or "----------" in line:
                continue

            # Parse finding
            finding = self._parse_finding_line(line)
            if finding:
                findings.append(finding)

        return findings

    def _parse_finding_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse single Nikto finding line.

        Examples:
            "+ OSVDB-3268: /icons/: Directory indexing found."
            "+ /login.php: Admin login page/section found."
            "+ The anti-clickjacking X-Frame-Options header is not present."
        """
        # Remove leading "+ "
        content = line.replace("+ ", "", 1)

        # Skip "Server:" line (metadata, not finding)
        if content.startswith("Server:"):
            return None

        # Extract OSVDB ID if present
        osvdb_id = None
        osvdb_match = re.match(r'OSVDB-(\d+):\s*(.*)', content)
        if osvdb_match:
            osvdb_id = osvdb_match.group(1)
            content = osvdb_match.group(2)

        # Extract URI (path starting with /)
        uri = None
        uri_match = re.match(r'(/[^:]*?):\s*(.*)', content)
        if uri_match:
            uri = uri_match.group(1).strip()
            description = uri_match.group(2).strip()
        else:
            description = content.strip()

        # Skip if no meaningful content
        if not description or len(description) < 10:
            return None

        # Determine severity and category
        severity = self._classify_severity(description.lower())
        category = self._classify_category(description.lower())

        return {
            "uri": uri,
            "description": description,
            "osvdb_id": osvdb_id,
            "severity": severity,
            "category": category
        }

    def _classify_severity(self, description: str) -> str:
        """Classify finding severity based on description keywords."""
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(keyword in description for keyword in keywords):
                return severity
        return "low"  # Default

    def _classify_category(self, description: str) -> str:
        """Classify finding category."""
        if any(word in description for word in ["injection", "xss", "script"]):
            return "injection"
        elif any(word in description for word in ["authentication", "login", "password"]):
            return "authentication"
        elif any(word in description for word in ["directory", "indexing", "listing"]):
            return "information_disclosure"
        elif any(word in description for word in ["outdated", "version", "eol"]):
            return "outdated_software"
        elif any(word in description for word in ["header", "x-frame", "x-content", "csp"]):
            return "security_headers"
        elif any(word in description for word in ["config", "backup", ".git", ".env"]):
            return "misconfiguration"
        else:
            return "general"
