"""Real Nmap scanner integration using python-nmap library."""

import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    print("[WARNING] python-nmap not installed, using fallback mode")


class NmapScanner:
    """Real Nmap scanner wrapper."""
    
    def __init__(self):
        self.scanner = nmap.PortScanner() if NMAP_AVAILABLE else None
    
    def execute_scan(
        self,
        target: str,
        scan_type: str = "quick",
        options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute real Nmap scan.
        
        Args:
            target: IP, hostname, or CIDR
            scan_type: quick, full, port_scan, os_detection, vuln_scan
            options: Additional nmap args
            
        Returns:
            Scan results dictionary
        """
        if not NMAP_AVAILABLE or not self.scanner:
            return self._fallback_scan(target, scan_type)
        
        # Map scan types to nmap arguments
        scan_args_map = {
            "quick": "-F",  # Fast scan (100 most common ports)
            "full": "-p-",  # All ports
            "port_scan": "-sS",  # SYN scan
            "os_detection": "-O",  # OS detection
            "service_version": "-sV",  # Service version detection
            "vuln_scan": "--script vuln",  # Vulnerability scripts
        }
        
        args = scan_args_map.get(scan_type, "-F")
        
        # Add custom options
        if options:
            args += " " + " ".join(options)
        
        try:
            print(f"[Nmap] Scanning {target} with args: {args}")
            self.scanner.scan(target, arguments=args)
            
            results = {
                "target": target,
                "scan_type": scan_type,
                "timestamp": datetime.now().isoformat(),
                "hosts_up": len(self.scanner.all_hosts()),
                "hosts": {}
            }
            
            for host in self.scanner.all_hosts():
                host_data = {
                    "hostname": self.scanner[host].hostname(),
                    "state": self.scanner[host].state(),
                    "protocols": {},
                    "os_matches": []
                }
                
                # Port information
                for proto in self.scanner[host].all_protocols():
                    ports = self.scanner[host][proto].keys()
                    host_data["protocols"][proto] = {}
                    
                    for port in ports:
                        port_info = self.scanner[host][proto][port]
                        host_data["protocols"][proto][str(port)] = {
                            "state": port_info.get("state", "unknown"),
                            "name": port_info.get("name", ""),
                            "product": port_info.get("product", ""),
                            "version": port_info.get("version", ""),
                            "extrainfo": port_info.get("extrainfo", "")
                        }
                
                # OS detection (if available)
                if "osmatch" in self.scanner[host]:
                    host_data["os_matches"] = [
                        {
                            "name": match["name"],
                            "accuracy": match["accuracy"]
                        }
                        for match in self.scanner[host]["osmatch"]
                    ]
                
                results["hosts"][host] = host_data
            
            return results
            
        except Exception as e:
            print(f"[Nmap] Scan error: {e}")
            return {
                "target": target,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "fallback": True,
                **self._fallback_scan(target, scan_type)
            }
    
    def _fallback_scan(self, target: str, scan_type: str) -> Dict[str, Any]:
        """
        Fallback using subprocess when python-nmap unavailable.
        """
        try:
            # Try direct nmap command
            cmd = ["nmap"]
            
            if scan_type == "quick":
                cmd.extend(["-F", target])
            elif scan_type == "full":
                cmd.extend(["-p-", target])
            else:
                cmd.extend(["-F", target])
            
            print(f"[Nmap Fallback] Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5min timeout
            )
            
            if result.returncode == 0:
                output = result.stdout
                return {
                    "target": target,
                    "scan_type": scan_type,
                    "timestamp": datetime.now().isoformat(),
                    "raw_output": output,
                    "parsed": self._parse_nmap_output(output)
                }
            else:
                return self._simulation_fallback(target, scan_type, error=result.stderr)
                
        except FileNotFoundError:
            print("[Nmap] nmap command not found, using simulation")
            return self._simulation_fallback(target, scan_type, error="nmap not installed")
        except Exception as e:
            print(f"[Nmap Fallback] Error: {e}")
            return self._simulation_fallback(target, scan_type, error=str(e))
    
    def _parse_nmap_output(self, output: str) -> Dict[str, Any]:
        """Parse raw nmap text output."""
        lines = output.split("\n")
        parsed = {
            "open_ports": [],
            "host_status": "unknown"
        }
        
        for line in lines:
            if "Host is up" in line:
                parsed["host_status"] = "up"
            elif "/tcp" in line or "/udp" in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split("/")[0]
                    state = parts[1]
                    service = parts[2] if len(parts) > 2 else "unknown"
                    parsed["open_ports"].append({
                        "port": port,
                        "state": state,
                        "service": service
                    })
        
        return parsed
    
    def _simulation_fallback(self, target: str, scan_type: str, error: str = "") -> Dict[str, Any]:
        """Simulation fallback (absolute last resort)."""
        import random
        
        common_ports = [
            {"port": 22, "service": "ssh", "state": "open"},
            {"port": 80, "service": "http", "state": "open"},
            {"port": 443, "service": "https", "state": "open"},
            {"port": 3306, "service": "mysql", "state": "filtered"},
            {"port": 5432, "service": "postgresql", "state": "filtered"},
        ]
        
        # Randomly select some ports
        simulated_ports = random.sample(common_ports, k=random.randint(1, 4))
        
        return {
            "target": target,
            "scan_type": scan_type,
            "timestamp": datetime.now().isoformat(),
            "simulation": True,
            "simulation_reason": error or "Development mode",
            "hosts": {
                target: {
                    "state": "up",
                    "open_ports": simulated_ports
                }
            }
        }
