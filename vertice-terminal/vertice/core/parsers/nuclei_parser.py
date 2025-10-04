"""
Nuclei JSON Parser
==================

Parses Nuclei JSON output into structured data compatible with Workspace.

Input: Nuclei JSON output (one JSON object per line - JSONL format)
Output: Structured dict with vulnerabilities

Nuclei Output Format:
    Each line is a separate JSON object:
    {
      "template-id": "CVE-2021-44228",
      "info": {
        "name": "Apache Log4j RCE",
        "severity": "critical",
        "description": "Apache Log4j2 <=2.14.1 JNDI features...",
        "reference": ["https://nvd.nist.gov/vuln/detail/CVE-2021-44228"],
        "tags": ["cve", "rce", "log4j", "oast"]
      },
      "type": "http",
      "host": "http://10.10.1.5:8080",
      "matched-at": "http://10.10.1.5:8080/admin",
      "timestamp": "2024-01-10T15:30:00.000Z",
      "curl-command": "curl -X GET ...",
      "matcher-name": "log4j-rce"
    }

Example Output:
    {
        "scan_info": {
            "target": "http://example.com",
            "total_findings": 5,
            "critical": 2,
            "high": 1,
            "medium": 2
        },
        "vulnerabilities": [
            {
                "template_id": "CVE-2021-44228",
                "name": "Apache Log4j RCE",
                "severity": "critical",
                "description": "...",
                "matched_at": "http://example.com/admin",
                "host": "http://example.com",
                "type": "http",
                "tags": ["cve", "rce"],
                "reference": ["..."],
                "timestamp": "2024-01-10T15:30:00.000Z"
            }
        ]
    }
"""

import json
from typing import Dict, List, Any, Optional
from ..base import ToolParser
import logging

logger = logging.getLogger(__name__)


class NucleiParser(ToolParser):
    """Parser for Nuclei JSON output."""

    def parse(self, output: str) -> Dict[str, Any]:
        """
        Parse Nuclei JSONL output.

        Args:
            output: Raw Nuclei output (JSONL - one JSON per line)

        Returns:
            Structured data with vulnerabilities

        Raises:
            ValueError: If output is invalid
        """
        vulnerabilities = []

        # Nuclei outputs JSONL (JSON Lines) - one JSON object per line
        lines = output.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                finding = json.loads(line)
                vuln_data = self._parse_finding(finding)
                if vuln_data:
                    vulnerabilities.append(vuln_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Nuclei output line: {e}")
                logger.debug(f"Invalid line: {line[:100]}")
                continue

        # Generate scan summary
        scan_info = self._generate_scan_info(vulnerabilities)

        return {
            "scan_info": scan_info,
            "vulnerabilities": vulnerabilities
        }

    def _parse_finding(self, finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse single Nuclei finding.

        Args:
            finding: Nuclei JSON finding object

        Returns:
            Structured vulnerability data
        """
        # Extract template info
        template_id = finding.get("template-id", "unknown")
        info = finding.get("info", {})

        # Required fields
        name = info.get("name")
        severity = info.get("severity", "info")

        if not name:
            logger.warning(f"Nuclei finding missing name: {template_id}")
            return None

        # Extract CVE if present
        cve_id = None
        if template_id.startswith("CVE-"):
            cve_id = template_id
        elif "cve-id" in info:
            # Some templates have explicit CVE field
            cve_ids = info.get("cve-id")
            if isinstance(cve_ids, list) and cve_ids:
                cve_id = cve_ids[0]
            elif isinstance(cve_ids, str):
                cve_id = cve_ids

        # Build vulnerability object
        vuln = {
            "template_id": template_id,
            "cve_id": cve_id,
            "name": name,
            "severity": severity.lower(),  # Normalize to lowercase
            "description": info.get("description", ""),
            "matched_at": finding.get("matched-at", finding.get("matched")),
            "host": finding.get("host", ""),
            "type": finding.get("type", ""),
            "tags": info.get("tags", []),
            "reference": info.get("reference", []),
            "timestamp": finding.get("timestamp"),
            "matcher_name": finding.get("matcher-name"),
            "curl_command": finding.get("curl-command")
        }

        # Extract port from host if possible
        host = vuln["host"]
        port = None
        if ":" in host:
            # Parse port from URL (e.g., "http://10.10.1.5:8080" -> 8080)
            try:
                parts = host.split(":")
                if len(parts) >= 3:  # http://host:port
                    port_str = parts[-1].split("/")[0]  # Remove path
                    port = int(port_str)
            except (ValueError, IndexError):
                pass

        vuln["port"] = port

        return vuln

    def _generate_scan_info(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate scan summary statistics.

        Args:
            vulnerabilities: List of parsed vulnerabilities

        Returns:
            Scan info dict with statistics
        """
        from urllib.parse import urlparse

        # Count by severity
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }

        # Extract unique hosts (IP/hostname only, not full URL)
        hosts = set()

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "info")
            if severity in severity_counts:
                severity_counts[severity] += 1

            host_url = vuln.get("host")
            if host_url:
                try:
                    parsed = urlparse(host_url)
                    # Extract just the hostname/IP (no port)
                    host_addr = parsed.hostname or parsed.netloc.split(":")[0]
                    hosts.add(host_addr)
                except Exception:
                    # Fallback: use raw host
                    hosts.add(host_url)

        return {
            "total_findings": len(vulnerabilities),
            "unique_hosts": len(hosts),
            **severity_counts
        }
