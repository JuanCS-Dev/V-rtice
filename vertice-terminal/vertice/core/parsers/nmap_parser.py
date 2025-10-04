"""
Nmap XML Parser
===============

Parses Nmap XML output into structured data compatible with Workspace.

Input: Nmap XML (-oX format)
Output: Structured dict with hosts, ports, services, OS info

Example Output:
    {
        "scan_info": {
            "command": "nmap -sV 10.10.1.5",
            "start_time": 1704670800,
            "end_time": 1704670850,
            "total_hosts": 1,
            "up_hosts": 1
        },
        "hosts": [
            {
                "ip": "10.10.1.5",
                "hostname": "target.local",
                "state": "up",
                "os_family": "Linux",
                "os_version": "Ubuntu 20.04",
                "ports": [
                    {
                        "port": 22,
                        "protocol": "tcp",
                        "state": "open",
                        "service": "ssh",
                        "version": "OpenSSH 8.2p1 Ubuntu",
                        "product": "OpenSSH",
                        "banner": "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
                    }
                ]
            }
        ]
    }
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..base import ToolParser
import logging

logger = logging.getLogger(__name__)


class NmapParser(ToolParser):
    """Parser for Nmap XML output."""

    def parse(self, output: str) -> Dict[str, Any]:
        """
        Parse Nmap XML output.

        Args:
            output: Raw Nmap XML output

        Returns:
            Structured data with hosts, ports, services

        Raises:
            ValueError: If XML is invalid
        """
        try:
            root = ET.fromstring(output)
        except ET.ParseError as e:
            raise ValueError(f"Invalid Nmap XML: {e}")

        # Extract scan metadata
        scan_info = self._parse_scan_info(root)

        # Extract hosts
        hosts = []
        for host_elem in root.findall("host"):
            host_data = self._parse_host(host_elem)
            if host_data:
                hosts.append(host_data)

        return {
            "scan_info": scan_info,
            "hosts": hosts
        }

    def _parse_scan_info(self, root: ET.Element) -> Dict[str, Any]:
        """Extract scan metadata."""
        runstats = root.find("runstats")
        finished = runstats.find("finished") if runstats is not None else None

        # Get command
        command = root.get("args", "")

        # Get timestamps
        start_time = int(root.get("start", 0))
        end_time = int(finished.get("time", 0)) if finished is not None else 0

        # Get host stats
        hosts_elem = runstats.find("hosts") if runstats is not None else None
        total_hosts = int(hosts_elem.get("total", 0)) if hosts_elem is not None else 0
        up_hosts = int(hosts_elem.get("up", 0)) if hosts_elem is not None else 0

        return {
            "command": command,
            "start_time": start_time,
            "end_time": end_time,
            "total_hosts": total_hosts,
            "up_hosts": up_hosts
        }

    def _parse_host(self, host_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse single host element."""
        # Host status
        status = host_elem.find("status")
        # Note: ElementTree elements are falsy if empty, so use "is None"
        if status is None or status.get("state") != "up":
            return None  # Skip down hosts

        # IP address - ElementTree doesn't support XPath predicates, so we filter manually
        address_elem = None
        for addr in host_elem.findall("address"):
            if addr.get("addrtype") in ("ipv4", "ipv6"):
                address_elem = addr
                break

        # ElementTree elements are falsy if empty, so use "is None"
        if address_elem is None:
            logger.warning("Host without IP address, skipping")
            return None

        ip = address_elem.get("addr")

        # Hostname
        hostname = None
        hostnames = host_elem.find("hostnames")
        if hostnames is not None:
            hostname_elem = hostnames.find("hostname")
            if hostname_elem is not None:
                hostname = hostname_elem.get("name")

        # OS detection
        os_family, os_version = self._parse_os(host_elem)

        # Ports
        ports = []
        ports_elem = host_elem.find("ports")
        if ports_elem:
            for port_elem in ports_elem.findall("port"):
                port_data = self._parse_port(port_elem)
                if port_data:
                    ports.append(port_data)

        return {
            "ip": ip,
            "hostname": hostname,
            "state": "up",
            "os_family": os_family,
            "os_version": os_version,
            "ports": ports
        }

    def _parse_os(self, host_elem: ET.Element) -> tuple[Optional[str], Optional[str]]:
        """Extract OS information."""
        os_elem = host_elem.find("os")
        if os_elem is None:
            return None, None

        # Try osmatch (OS detection results)
        osmatch = os_elem.find("osmatch")
        if osmatch is not None:
            os_name = osmatch.get("name", "")

            # Try to extract family and version
            # Examples: "Linux 4.15 - 5.8", "Microsoft Windows 10", "Ubuntu Linux"
            if "Linux" in os_name:
                os_family = "Linux"
                # Try to extract distribution
                if "Ubuntu" in os_name:
                    os_version = "Ubuntu"
                elif "Debian" in os_name:
                    os_version = "Debian"
                elif "CentOS" in os_name:
                    os_version = "CentOS"
                else:
                    os_version = os_name
            elif "Windows" in os_name:
                os_family = "Windows"
                os_version = os_name.replace("Microsoft ", "")
            else:
                os_family = os_name
                os_version = None

            return os_family, os_version

        return None, None

    def _parse_port(self, port_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse single port element."""
        # Port number and protocol
        port_num = int(port_elem.get("portid"))
        protocol = port_elem.get("protocol", "tcp")

        # Port state
        state_elem = port_elem.find("state")
        if state_elem is None:
            return None

        state = state_elem.get("state")

        # Service detection
        service_elem = port_elem.find("service")
        service = None
        product = None
        version = None
        banner = None

        if service_elem is not None:
            service = service_elem.get("name")
            product = service_elem.get("product")
            version_str = service_elem.get("version")
            extra_info = service_elem.get("extrainfo")

            # Build version string
            if product is not None:
                version = product
                if version_str:
                    version += f" {version_str}"
                if extra_info:
                    version += f" ({extra_info})"

            # Banner (if available)
            banner = service_elem.get("servicefp") or service_elem.get("tunnel")

        return {
            "port": port_num,
            "protocol": protocol,
            "state": state,
            "service": service,
            "version": version,
            "product": product,
            "banner": banner
        }
