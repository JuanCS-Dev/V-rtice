
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict

# This would be replaced by the database model in the final version
from models import CommonExploit, Vulnerability, Severity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def run_nmap_scan(target: str, scan_type: str, scan_id: str, db: AsyncSession):
    """Executes an Nmap scan and stores the results in the database."""
    cmd = await build_nmap_command(target, scan_type)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise Exception(f"Nmap scan failed: {stderr.decode()}")

    new_vulnerabilities = await parse_nmap_vulns(stdout.decode(), scan_id, db)
    return new_vulnerabilities

async def build_nmap_command(target: str, scan_type: str) -> List[str]:
    """Builds the Nmap command based on the selected scan type."""
    cmd = ["nmap"]
    if scan_type == "quick":
        cmd.extend(["-T4", "-F", "--script", "vuln"])
    elif scan_type == "stealth":
        cmd.extend(["-T2", "-sS", "-f", "--script", "vuln"])
    elif scan_type == "aggressive":
        cmd.extend(["-T5", "-A", "--script", "vuln,exploit"])
    else:  # comprehensive
        cmd.extend(["-T4", "-p-", "--script", "vuln,exploit,malware"])
    
    cmd.extend(["-oX", "-", target])
    return cmd

async def parse_nmap_vulns(xml_output: str, scan_id: str, db: AsyncSession) -> List[Vulnerability]:
    """Parses Nmap XML output and returns a list of Vulnerability objects."""
    vulnerabilities = []
    try:
        root = ET.fromstring(xml_output)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse Nmap XML: {e}")

    for host in root.findall(".//host"):
        host_ip = host.find(".//address[@addrtype='ipv4']").get("addr")

        for script in host.findall(".//script"):
            if "vuln" in script.get("id", "") or "cve" in script.get("id", "").lower():
                cve_matches = extract_cves(script.get("output", ""))
                
                for cve in cve_matches:
                    severity = await determine_severity(cve, script.get("output", ""), db)
                    exploit_info = (await db.execute(select(CommonExploit).filter_by(cve_id=cve))).scalar_one_or_none()

                    vuln = Vulnerability(
                        scan_id=scan_id,
                        host=host_ip,
                        port=get_port_from_script(host, script),
                        service=get_service_from_script(host, script),
                        cve_id=cve,
                        severity=severity,
                        description=script.get("output", "")[:1024],
                        recommendation="Patch immediately.",
                        exploit_available=exploit_info.metasploit_module if exploit_info else None
                    )
                    vulnerabilities.append(vuln)
    return vulnerabilities

def extract_cves(text: str) -> List[str]:
    """Extracts CVE identifiers from text."""
    import re
    cve_pattern = r'CVE-\d{4}-\d{4,7}'
    return re.findall(cve_pattern, text.upper())

def get_port_from_script(host, script) -> int:
    """Gets the port number associated with a script from the Nmap XML."""
    for port in host.findall(".//port"):
        if script in port.findall(".//script"):
            return int(port.get("portid"))
    return 0

def get_service_from_script(host, script) -> str:
    """Gets the service name associated with a script from the Nmap XML."""
    for port in host.findall(".//port"):
        if script in port.findall(".//script"):
            service = port.find(".//service")
            return service.get("name") if service is not None else "unknown"
    return "unknown"

async def determine_severity(cve: str, output: str, db: AsyncSession) -> Severity:
    """Determines the severity of a vulnerability."""
    exploit_info = (await db.execute(select(CommonExploit).filter_by(cve_id=cve))).scalar_one_or_none()
    if exploit_info:
        return exploit_info.severity

    if any(word in output.lower() for word in ["rce", "remote code execution", "critical"]):
        return Severity.CRITICAL
    if any(word in output.lower() for word in ["high", "privilege escalation"]):
        return Severity.HIGH
    if any(word in output.lower() for word in ["medium", "information disclosure"]):
        return Severity.MEDIUM
    return Severity.LOW
