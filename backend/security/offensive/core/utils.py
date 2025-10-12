"""
Offensive Security Utilities
============================

Common utilities for offensive security operations.
"""

import asyncio
import socket
from typing import List, Optional
from ipaddress import ip_address, ip_network

from .exceptions import TargetUnreachableError


async def resolve_hostname(hostname: str) -> str:
    """
    Resolve hostname to IP address.
    
    Args:
        hostname: Hostname to resolve
        
    Returns:
        Resolved IP address
        
    Raises:
        TargetUnreachableError: If resolution fails
    """
    try:
        loop = asyncio.get_event_loop()
        addr_info = await loop.getaddrinfo(
            hostname, None, family=socket.AF_INET
        )
        return addr_info[0][4][0]
    except (socket.gaierror, IndexError) as e:
        raise TargetUnreachableError(
            f"Failed to resolve hostname '{hostname}': {e}"
        )


async def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Check if port is open on target.
    
    Args:
        host: Target host
        port: Target port
        timeout: Connection timeout in seconds
        
    Returns:
        True if port is open
    """
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


async def scan_ports(
    host: str,
    ports: List[int],
    timeout: float = 2.0
) -> List[int]:
    """
    Scan multiple ports on target.
    
    Args:
        host: Target host
        ports: List of ports to scan
        timeout: Connection timeout per port
        
    Returns:
        List of open ports
    """
    tasks = [check_port_open(host, port, timeout) for port in ports]
    results = await asyncio.gather(*tasks)
    return [port for port, is_open in zip(ports, results) if is_open]


def parse_cidr(cidr: str) -> List[str]:
    """
    Parse CIDR notation to list of IPs.
    
    Args:
        cidr: CIDR notation (e.g., "192.168.1.0/24")
        
    Returns:
        List of IP addresses in range
    """
    try:
        network = ip_network(cidr, strict=False)
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"Invalid CIDR notation '{cidr}': {e}")


def is_valid_ip(ip: str) -> bool:
    """
    Validate IP address.
    
    Args:
        ip: IP address string
        
    Returns:
        True if valid IPv4 address
    """
    try:
        ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """
    Check if IP is private.
    
    Args:
        ip: IP address string
        
    Returns:
        True if private IP address
    """
    try:
        addr = ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


async def fingerprint_service(host: str, port: int) -> Optional[str]:
    """
    Fingerprint service on port.
    
    Args:
        host: Target host
        port: Target port
        
    Returns:
        Service banner or None
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=3.0
        )
        
        # Read banner
        banner = await asyncio.wait_for(
            reader.read(1024),
            timeout=2.0
        )
        
        writer.close()
        await writer.wait_closed()
        
        return banner.decode('utf-8', errors='ignore').strip()
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return None


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input to prevent injection.
    
    Args:
        user_input: Raw user input
        
    Returns:
        Sanitized input
    """
    # Remove dangerous characters
    dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
    sanitized = user_input
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()


def format_findings(
    findings: List[dict],
    format_type: str = "text"
) -> str:
    """
    Format findings for output.
    
    Args:
        findings: List of finding dictionaries
        format_type: Output format ('text', 'json', 'xml')
        
    Returns:
        Formatted findings string
    """
    if format_type == "text":
        output = []
        for i, finding in enumerate(findings, 1):
            output.append(f"Finding {i}:")
            for key, value in finding.items():
                output.append(f"  {key}: {value}")
            output.append("")
        return "\n".join(output)
    elif format_type == "json":
        import json
        return json.dumps(findings, indent=2)
    else:
        return str(findings)
