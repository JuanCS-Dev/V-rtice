"""Domain Analysis Service - Vértice Cyber Security Module.

This microservice provides comprehensive analysis of domains, including OSINT,
DNS records, TLS certificate details, and reputation assessment. It serves as a
centralized tool for gathering intelligence on a given domain.
"""

import subprocess
import socket
import ssl
from html.parser import HTMLParser
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Domain Analysis Service",
    description="A microservice for comprehensive domain analysis (OSINT, DNS, TLS, reputation).",
    version="1.0.0",
)

# ============================================================================
# Pydantic Models
# ============================================================================

class DomainAnalysisRequest(BaseModel):
    """Request model for analyzing a domain."""
    domain: str

# ============================================================================
# HTML Parser for Title Extraction
# ============================================================================

class TitleParser(HTMLParser):
    """A simple HTML parser to extract the content of the <title> tag."""
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title": self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title": self.in_title = False

    def handle_data(self, data):
        if self.in_title: self.title += data

# ============================================================================
# Analysis Functions
# ============================================================================

async def query_dns_records(domain: str) -> Dict[str, List[str]]:
    """Queries various DNS records for a domain using the `dig` command.

    Args:
        domain (str): The domain to query.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are record types (A, MX, etc.)
            and values are lists of record values.
    """
    records = {}
    for record_type in ["A", "AAAA", "MX", "NS", "TXT", "SOA"]:
        try:
            proc = await asyncio.create_subprocess_exec("dig", "+short", domain, record_type, stdout=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            records[record_type] = [line.strip() for line in stdout.decode().splitlines() if line.strip()]
        except Exception:
            records[record_type] = []
    return records

async def analyze_http_service(url: str) -> Dict[str, Any]:
    """Analyzes an HTTP/HTTPS service to get status, headers, and title.

    Args:
        url (str): The URL to analyze (e.g., 'http://example.com').

    Returns:
        Dict[str, Any]: A dictionary containing the status code, headers, and page title.
    """
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Vértice-Cyber/1.0"})
        parser = TitleParser()
        parser.feed(response.text[:5000])
        return {
            "status_code": response.status_code,
            "title": parser.title.strip(),
            "headers": dict(response.headers),
        }
    except requests.RequestException as e:
        return {"error": str(e)}

async def get_tls_certificate_info(domain: str) -> Optional[Dict[str, Any]]:
    """Retrieves and parses the TLS certificate for a domain.

    Args:
        domain (str): The domain to check.

    Returns:
        Optional[Dict[str, Any]]: A dictionary with certificate details if successful,
            otherwise None.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return {
                    "subject": dict(x[0] for x in cert.get("subject", [])),
                    "issuer": dict(x[0] for x in cert.get("issuer", [])),
                    "expires": cert.get("notAfter"),
                }
    except Exception:
        return None

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def health_check():
    """Provides a basic health check of the service."""
    return {"service": "Domain Analysis Service", "status": "operational"}

@app.post("/analyze", tags=["Domain Analysis"])
async def analyze_domain(request: DomainAnalysisRequest):
    """Performs a comprehensive analysis of a given domain.

    This endpoint orchestrates calls to various analysis functions to gather
    DNS, HTTP, TLS, and reputation information for the specified domain.

    Args:
        request (DomainAnalysisRequest): The request containing the domain to analyze.

    Returns:
        Dict[str, Any]: A dictionary containing the aggregated analysis results.
    """
    domain = request.domain.strip().lower()
    results = {"domain": domain, "timestamp": datetime.now().isoformat(), "data": {}, "errors": []}
    try:
        # Concurrently run all analysis functions
        tasks = {
            "dns": query_dns_records(domain),
            "http": analyze_http_service(f"http://{domain}"),
            "https": analyze_http_service(f"https://{domain}"),
            "tls": get_tls_certificate_info(domain),
        }
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for task_name, res in zip(tasks.keys(), task_results):
            if isinstance(res, Exception):
                results["errors"].append(f"{task_name} analysis failed: {res}")
            else:
                results["data"][task_name] = res

    except Exception as e:
        results["errors"].append(f"An unexpected error occurred: {e}")

    results["success"] = not results["errors"]
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)