
import httpx
from typing import List, Dict

from models import Vulnerability, Severity

async def test_web_vulnerabilities(target: str, scan_type: str, scan_id: str) -> List[Vulnerability]:
    """Tests for common web vulnerabilities and returns them as Vulnerability objects."""
    vulnerabilities = []
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            base_url = target if target.startswith("http") else f"https://{target}"
            
            # Test connection first
            try:
                await client.get(base_url)
            except httpx.ConnectError:
                base_url = f"http://{target}"
                await client.get(base_url)

            # SQL Injection
            if scan_type in ["full", "sqli"]:
                vulnerabilities.extend(await test_sqli(client, base_url, scan_id))
            
            # XSS
            if scan_type in ["full", "xss"]:
                vulnerabilities.extend(await test_xss(client, base_url, scan_id))

            # Security Headers
            if scan_type == "full":
                vulnerabilities.extend(await test_security_headers(client, base_url, scan_id))

    except httpx.RequestError as e:
        vulnerabilities.append(Vulnerability(
            scan_id=scan_id,
            host=target,
            port=443 if 'https' in str(e.request.url) else 80,
            service="http/https",
            severity=Severity.INFO,
            description=f"Could not connect to target: {str(e)}",
            recommendation="Verify target is accessible and running a web server."
        ))
    return vulnerabilities

async def test_sqli(client: httpx.AsyncClient, base_url: str, scan_id: str) -> List[Vulnerability]:
    """Tests for basic SQL Injection vulnerabilities."""
    results = []
    sqli_payloads = ["'", "' OR 1=1--", "\" OR 1=1--"]
    error_indicators = ["sql syntax", "mysql", "unclosed quotation mark", "oracle"]

    for payload in sqli_payloads:
        try:
            response = await client.get(f"{base_url}?id={payload}")
            if any(error in response.text.lower() for error in error_indicators):
                results.append(Vulnerability(
                    scan_id=scan_id, host=base_url, port=80, service="web", cve_id="CWE-89",
                    severity=Severity.HIGH, description=f"Potential SQL Injection with payload: {payload}",
                    recommendation="Use parameterized queries (prepared statements) for all database access."
                ))
                break # Found one, no need to continue
        except httpx.RequestError:
            continue
    return results

async def test_xss(client: httpx.AsyncClient, base_url: str, scan_id: str) -> List[Vulnerability]:
    """Tests for basic reflected XSS vulnerabilities."""
    results = []
    xss_payload = "<script>alert('VULN_TEST')</script>"
    try:
        response = await client.get(f"{base_url}?q={xss_payload}")
        if xss_payload in response.text:
            results.append(Vulnerability(
                scan_id=scan_id, host=base_url, port=80, service="web", cve_id="CWE-79",
                severity=Severity.MEDIUM, description="Reflected Cross-Site Scripting (XSS) detected.",
                recommendation="Implement context-aware output encoding and content security policy (CSP)."
            ))
    except httpx.RequestError:
        pass
    return results

async def test_security_headers(client: httpx.AsyncClient, base_url: str, scan_id: str) -> List[Vulnerability]:
    """Checks for the presence of important security headers."""
    results = []
    try:
        response = await client.get(base_url)
        expected_headers = {
            "Content-Security-Policy": Severity.MEDIUM,
            "Strict-Transport-Security": Severity.MEDIUM,
            "X-Content-Type-Options": Severity.LOW,
            "X-Frame-Options": Severity.LOW,
        }
        for header, severity in expected_headers.items():
            if header not in response.headers:
                results.append(Vulnerability(
                    scan_id=scan_id, host=base_url, port=443, service="web", cve_id="CWE-693",
                    severity=severity, description=f"Missing security header: {header}",
                    recommendation=f"Set the {header} HTTP header to enhance security."
                ))
    except httpx.RequestError:
        pass
    return results
