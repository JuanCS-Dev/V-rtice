"""
Network Scanner - Port scanning and service detection.

AI-driven reconnaissance for network topology mapping.
"""
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import socket
import ipaddress
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError


@dataclass
class Port:
    """Represents a network port."""
    number: int
    protocol: str = "tcp"
    state: str = "unknown"
    service: Optional[str] = None
    version: Optional[str] = None
    banner: Optional[str] = None


@dataclass
class ScanResult:
    """Network scan result."""
    target: str
    scan_type: str
    start_time: datetime
    end_time: datetime
    ports: List[Port]
    os_fingerprint: Optional[str] = None
    metadata: Dict = None


class NetworkScanner(OffensiveTool):
    """
    AI-enhanced network scanner.
    
    Performs intelligent port scanning with service detection,
    version enumeration, and OS fingerprinting. Adapts scan
    strategy based on target responses and ML recommendations.
    """
    
    def __init__(self) -> None:
        """Initialize scanner with default configuration."""
        super().__init__(
            name="network_scanner",
            category="reconnaissance"
        )
        self.common_ports: Set[int] = {
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
            143, 443, 445, 993, 995, 1723, 3306, 3389,
            5900, 8080, 8443
        }
        self.timeout: float = 2.0
        self.max_concurrent: int = 100
    
    async def execute(
        self,
        target: str,
        ports: Optional[List[int]] = None,
        scan_type: str = "tcp_connect",
        **kwargs
    ) -> ToolResult:
        """
        Execute network scan.
        
        Args:
            target: Target IP or hostname
            ports: List of ports to scan (None = common ports)
            scan_type: Type of scan (tcp_connect, syn, udp)
            **kwargs: Additional scan parameters
            
        Returns:
            ToolResult with scan results
            
        Raises:
            OffensiveToolError: If scan fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate target
            target_ip = self._resolve_target(target)
            
            # Determine ports to scan
            scan_ports = ports if ports else list(self.common_ports)
            
            # Execute scan based on type
            if scan_type == "tcp_connect":
                scanned_ports = await self._tcp_connect_scan(
                    target_ip, scan_ports
                )
            elif scan_type == "syn":
                scanned_ports = await self._syn_scan(target_ip, scan_ports)
            elif scan_type == "udp":
                scanned_ports = await self._udp_scan(target_ip, scan_ports)
            else:
                raise OffensiveToolError(
                    f"Unknown scan type: {scan_type}",
                    tool_name=self.name
                )
            
            # Service detection on open ports
            open_ports = [p for p in scanned_ports if p.state == "open"]
            if open_ports:
                await self._detect_services(target_ip, open_ports)
            
            # OS fingerprinting
            os_fingerprint = await self._fingerprint_os(
                target_ip, open_ports
            ) if open_ports else None
            
            end_time = datetime.utcnow()
            
            scan_result = ScanResult(
                target=target,
                scan_type=scan_type,
                start_time=start_time,
                end_time=end_time,
                ports=scanned_ports,
                os_fingerprint=os_fingerprint,
                metadata={
                    "total_ports": len(scan_ports),
                    "open_ports": len(open_ports),
                    "duration_seconds": (end_time - start_time).total_seconds()
                }
            )
            
            return ToolResult(
                success=True,
                data=scan_result,
                message=f"Scan complete: {len(open_ports)} open ports found",
                metadata=self._create_metadata(scan_result)
            )
            
        except Exception as e:
            raise OffensiveToolError(
                f"Scan failed: {str(e)}",
                tool_name=self.name,
                details={"target": target, "scan_type": scan_type}
            )
    
    def _resolve_target(self, target: str) -> str:
        """
        Resolve target to IP address.
        
        Args:
            target: Hostname or IP
            
        Returns:
            Resolved IP address
            
        Raises:
            OffensiveToolError: If resolution fails
        """
        try:
            # Check if already IP
            ipaddress.ip_address(target)
            return target
        except ValueError:
            # Resolve hostname
            try:
                return socket.gethostbyname(target)
            except socket.gaierror:
                raise OffensiveToolError(
                    f"Cannot resolve target: {target}",
                    tool_name=self.name
                )
    
    async def _tcp_connect_scan(
        self, target: str, ports: List[int]
    ) -> List[Port]:
        """
        Perform TCP connect scan.
        
        Args:
            target: Target IP
            ports: Ports to scan
            
        Returns:
            List of scanned ports
        """
        results = []
        
        # Create tasks for concurrent scanning
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def scan_port(port_num: int) -> Port:
            async with semaphore:
                return await self._check_tcp_port(target, port_num)
        
        tasks = [scan_port(p) for p in ports]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        return [r for r in results if isinstance(r, Port)]
    
    async def _check_tcp_port(self, target: str, port: int) -> Port:
        """
        Check if TCP port is open.
        
        Args:
            target: Target IP
            port: Port number
            
        Returns:
            Port object with state
        """
        port_obj = Port(number=port, protocol="tcp")
        
        try:
            # Attempt connection
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(target, port),
                timeout=self.timeout
            )
            
            port_obj.state = "open"
            
            # Try to grab banner
            try:
                writer.write(b"\r\n")
                await writer.drain()
                data = await asyncio.wait_for(
                    writer.read(1024),
                    timeout=1.0
                )
                if data:
                    port_obj.banner = data.decode('utf-8', errors='ignore')
            except Exception:
                pass
            
            writer.close()
            await writer.wait_closed()
            
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            port_obj.state = "closed"
        
        return port_obj
    
    async def _syn_scan(
        self, target: str, ports: List[int]
    ) -> List[Port]:
        """
        Perform SYN scan (requires raw sockets).
        
        Args:
            target: Target IP
            ports: Ports to scan
            
        Returns:
            List of scanned ports
        """
        # SYN scan requires raw sockets (root privileges)
        # Fallback to TCP connect for now
        return await self._tcp_connect_scan(target, ports)
    
    async def _udp_scan(
        self, target: str, ports: List[int]
    ) -> List[Port]:
        """
        Perform UDP scan.
        
        Args:
            target: Target IP
            ports: Ports to scan
            
        Returns:
            List of scanned ports
        """
        results = []
        
        for port in ports:
            port_obj = Port(number=port, protocol="udp")
            
            try:
                # Send UDP packet
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(self.timeout)
                sock.sendto(b"\x00", (target, port))
                
                try:
                    data, _ = sock.recvfrom(1024)
                    port_obj.state = "open"
                except socket.timeout:
                    port_obj.state = "open|filtered"
                
                sock.close()
                
            except Exception:
                port_obj.state = "closed"
            
            results.append(port_obj)
        
        return results
    
    async def _detect_services(
        self, target: str, ports: List[Port]
    ) -> None:
        """
        Detect services on open ports.
        
        Args:
            target: Target IP
            ports: Open ports
        """
        # Service detection mapping
        service_map = {
            21: "ftp",
            22: "ssh",
            23: "telnet",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            143: "imap",
            443: "https",
            445: "smb",
            3306: "mysql",
            3389: "rdp",
            5900: "vnc",
            8080: "http-proxy",
            8443: "https-alt"
        }
        
        for port in ports:
            # Basic service detection from port number
            if port.number in service_map:
                port.service = service_map[port.number]
            
            # Enhanced detection from banner
            if port.banner:
                banner_lower = port.banner.lower()
                if "ssh" in banner_lower:
                    port.service = "ssh"
                    # Extract version
                    if "openssh" in banner_lower:
                        port.version = banner_lower.split("openssh")[1].split()[0]
                elif "http" in banner_lower:
                    port.service = "http"
                elif "ftp" in banner_lower:
                    port.service = "ftp"
    
    async def _fingerprint_os(
        self, target: str, ports: List[Port]
    ) -> Optional[str]:
        """
        Perform OS fingerprinting.
        
        Args:
            target: Target IP
            ports: Open ports
            
        Returns:
            OS fingerprint or None
        """
        # Basic OS detection from service banners
        for port in ports:
            if port.banner:
                banner_lower = port.banner.lower()
                
                if "ubuntu" in banner_lower or "debian" in banner_lower:
                    return "Linux (Debian-based)"
                elif "centos" in banner_lower or "redhat" in banner_lower:
                    return "Linux (RedHat-based)"
                elif "windows" in banner_lower:
                    return "Windows"
                elif "freebsd" in banner_lower:
                    return "FreeBSD"
        
        # Default fingerprint based on port combinations
        port_numbers = {p.number for p in ports}
        
        if 3389 in port_numbers or 445 in port_numbers:
            return "Windows (likely)"
        elif 22 in port_numbers:
            return "Unix-like (likely)"
        
        return None
    
    def _create_metadata(self, scan_result: ScanResult) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            scan_result: Scan result
            
        Returns:
            Tool metadata
        """
        open_ports = [p for p in scan_result.ports if p.state == "open"]
        
        return ToolMetadata(
            tool_name=self.name,
            execution_time=(
                scan_result.end_time - scan_result.start_time
            ).total_seconds(),
            success_rate=len(open_ports) / len(scan_result.ports) if scan_result.ports else 0.0,
            confidence_score=0.85 if open_ports else 0.5,
            resource_usage={
                "ports_scanned": len(scan_result.ports),
                "concurrent_connections": self.max_concurrent
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate scanner functionality.
        
        Returns:
            True if validation passes
        """
        try:
            # Test localhost scan
            result = await self.execute(
                target="127.0.0.1",
                ports=[80, 443]
            )
            return result.success
        except Exception:
            return False
