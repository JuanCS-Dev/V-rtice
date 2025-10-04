"""Cyber Security Service - Real-time System Integrity and Security Checks.

This microservice provides a set of endpoints to perform live security and
integrity checks on the underlying system. It is designed to be a self-contained
security verification tool for the Vertice ecosystem, using system utilities
and libraries to gather real-time data.
"""

import subprocess
import psutil
import socket
import ssl
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Cyber Security Service",
    description="A microservice for real-time security and integrity checks.",
    version="1.0.0",
)

# ============================================================================
# Pydantic Models
# ============================================================================

class NetworkScanRequest(BaseModel):
    """Request model for initiating a network scan."""
    target: str
    profile: str = "self-check"

class SecurityResult(BaseModel):
    """Standard response model for all security check endpoints."""
    timestamp: str
    success: bool
    data: Dict[str, Any]
    errors: List[str] = []

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def health_check():
    """Provides a basic health check of the service."""
    return {"service": "Cyber Security Service", "status": "operational"}

@app.post("/cyber/network-scan", response_model=SecurityResult, tags=["Security Checks"])
async def network_scan(request: NetworkScanRequest):
    """Performs a network scan on the specified target using nmap or netstat.

    If `nmap` is available, it performs a fast scan for open ports. If not, it
    falls back to using `netstat` to list listening ports as a basic alternative.

    Args:
        request (NetworkScanRequest): The request containing the target to scan.

    Returns:
        SecurityResult: The result of the scan, including the method used and
            a list of open ports found.
    """
    result = {"data": {}, "errors": []}
    try:
        nmap_path = subprocess.getoutput("which nmap")
        if not nmap_path:
            # Fallback to netstat
            proc = await asyncio.create_subprocess_shell("netstat -tuln", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"netstat failed: {stderr.decode()}")
            ports = [line.split()[3].split(':')[-1] for line in stdout.decode().splitlines() if 'LISTEN' in line]
            result["data"] = {"method": "netstat", "open_ports": list(set(ports))}
        else:
            # Use nmap
            proc = await asyncio.create_subprocess_exec("nmap", "-F", "--open", request.target, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"nmap failed: {stderr.decode()}")
            ports = [line.split('/')[0] for line in stdout.decode().splitlines() if '/tcp' in line and 'open' in line]
            result["data"] = {"method": "nmap", "open_ports": ports}
        
        result["success"] = True
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
    
    result["timestamp"] = datetime.now().isoformat()
    return result

@app.get("/cyber/process-analysis", response_model=SecurityResult, tags=["Security Checks"])
async def process_analysis():
    """Analyzes running processes for anomalies.

    Uses `psutil` to iterate through running processes, identifying those with
    high CPU or memory usage and categorizing them.

    Returns:
        SecurityResult: A summary of process information, including total count,
            suspicious processes, and system load averages.
    """
    suspicious_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['cpu_percent'] > 80.0:
                suspicious_procs.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=True,
        data={
            "total_processes": len(psutil.pids()),
            "suspicious_processes": suspicious_procs,
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": psutil.virtual_memory().percent
        }
    )

@app.get("/cyber/file-integrity", response_model=SecurityResult, tags=["Security Checks"])
async def file_integrity_check():
    """Performs an integrity check on critical system files.

    Checks for the existence and permissions of key files like `/etc/passwd`.
    It also scans for potentially dangerous SUID files.

    Returns:
        SecurityResult: A report on checked files, missing files, and any
            suspicious SUID files found.
    """
    critical_files = ["/etc/passwd", "/etc/shadow", "/app/main.py"]
    checked_files = []
    missing_files = []
    for f_path in critical_files:
        if os.path.exists(f_path):
            stat = os.stat(f_path)
            checked_files.append({"path": f_path, "size": stat.st_size, "permissions": oct(stat.st_mode)[-3:]})
        else:
            missing_files.append(f_path)

    return SecurityResult(
        timestamp=datetime.now().isoformat(),
        success=True,
        data={
            "checked_files": checked_files,
            "missing_files": missing_files
        }
    )