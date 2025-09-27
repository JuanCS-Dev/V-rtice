# backend/services/domain_service/main.py

"""
Domain Analysis Service - Vértice Cyber Security Module
Migração do Batman do Cerrado para arquitetura de microsserviços
"""

import subprocess
import socket
import ssl
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from html.parser import HTMLParser

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Domain Analysis Service",
    description="Microsserviço para análise completa de domínios - OSINT, DNS, TLS, reputação",
    version="1.0.0",
)

# Modelos de dados
class DomainAnalysisRequest(BaseModel):
    domain: str

class TitleParser(HTMLParser):
    """Parser HTML para extrair título da página"""
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""
    
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True
    
    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False
    
    def handle_data(self, data):
        if self.in_title:
            self.title += data

# --- DNS Analysis Functions ---

async def query_dns_records(domain: str) -> Dict[str, List[str]]:
    """Consulta registros DNS usando dig"""
    records = {}
    record_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CAA"]
    
    for record_type in record_types:
        try:
            result = subprocess.run(
                ["dig", "+short", domain, record_type],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                records[record_type] = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            else:
                records[record_type] = []
        except Exception:
            records[record_type] = []
    
    # DMARC query
    try:
        result = subprocess.run(
            ["dig", "+short", f"_dmarc.{domain}", "TXT"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            records["DMARC"] = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        else:
            records["DMARC"] = []
    except Exception:
        records["DMARC"] = []
    
    return records

def parse_spf_record(txt_records: List[str]) -> Optional[Dict[str, Any]]:
    """Parse SPF record from TXT records"""
    for record in txt_records:
        clean_record = record.strip('"').lower()
        if clean_record.startswith("v=spf1"):
            mechanisms = [part for part in record.strip('"').split() if not part.startswith("exp=")]
            return {
                "raw": record.strip('"'),
                "mechanisms": mechanisms,
                "valid": True
            }
    return None

def parse_dmarc_record(dmarc_records: List[str]) -> Optional[Dict[str, Any]]:
    """Parse DMARC record"""
    if not dmarc_records:
        return None
    
    record = dmarc_records[0].strip('"')
    parsed = {"raw": record}
    
    for part in record.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            parsed[key.strip()] = value.strip()
    
    return parsed

async def test_axfr_vulnerability(domain: str, ns_records: List[str]) -> bool:
    """Test for AXFR zone transfer vulnerability"""
    if not ns_records:
        return False
    
    for ns in ns_records:
        try:
            result = subprocess.run(
                ["dig", f"@{ns.rstrip('.')}", domain, "AXFR"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0 and "Transfer failed." not in result.stdout and "XFR size" in result.stdout:
                return True
        except Exception:
            continue
    
    return False

# --- HTTP/HTTPS Analysis Functions ---

async def analyze_http_service(url: str) -> Dict[str, Any]:
    """Analyze HTTP/HTTPS service"""
    try:
        session = requests.Session()
        session.headers.update({"User-Agent": "Vértice-Cyber-Security/2.0"})
        
        response = session.get(url, timeout=10, allow_redirects=False)
        
        # Parse title
        title_parser = TitleParser()
        title_parser.feed(response.text[:4096])
        
        return {
            "status_code": response.status_code,
            "title": title_parser.title.strip(),
            "headers": dict(response.headers),
            "redirect_location": response.headers.get("Location")
        }
    
    except requests.RequestException as e:
        return {"error": f"Connection failed: {str(e)}"}

async def get_tls_certificate_info(domain: str) -> Optional[Dict[str, Any]]:
    """Get TLS certificate information"""
    try:
        context = ssl.create_default_context()
        
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                sans = [item[1] for item in cert.get("subjectAltName", [])]
                
                return {
                    "subject": subject.get("commonName"),
                    "issuer": issuer.get("commonName"),
                    "expires": cert.get("notAfter"),
                    "sans": sans,
                    "valid": True
                }
    
    except Exception:
        return None

# --- Reputation Analysis ---

async def analyze_domain_reputation(domain: str) -> tuple[Optional[int], List[str]]:
    """Analyze domain reputation and detect threats"""
    threats = []
    reputation_score = None
    
    # Basic threat detection (expandable)
    suspicious_keywords = ["phishing", "malware", "spam", "scam", "fraud"]
    
    try:
        # Check domain age and patterns
        if any(keyword in domain.lower() for keyword in suspicious_keywords):
            threats.append("Suspicious domain name pattern")
            reputation_score = 25
        else:
            reputation_score = 85
        
        # Check for common phishing patterns
        if len(domain.split('.')) > 3:
            threats.append("Excessive subdomain levels")
            reputation_score = max(20, (reputation_score or 50) - 30)
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            threats.append("Suspicious top-level domain")
            reputation_score = max(15, (reputation_score or 50) - 40)
    
    except Exception:
        pass
    
    return reputation_score, threats

# --- Main Analysis Endpoint ---

@app.post("/analyze", tags=["Domain Analysis"])
async def analyze_domain(request: DomainAnalysisRequest):
    """Análise completa de domínio - DNS, HTTP/HTTPS, TLS, reputação"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "domain": request.domain.lower().strip(),
        "data": {},
        "errors": []
    }
    
    domain = request.domain.lower().strip()
    
    try:
        # DNS Analysis
        dns_records = await query_dns_records(domain)
        result["data"]["dns"] = dns_records
        
        # HTTP Analysis
        http_info = await analyze_http_service(f"http://{domain}")
        result["data"]["http"] = http_info
        
        # HTTPS Analysis  
        https_info = await analyze_http_service(f"https://{domain}")
        result["data"]["https"] = https_info
        
        # TLS Certificate Analysis
        tls_info = await get_tls_certificate_info(domain)
        result["data"]["tls"] = tls_info
        
        # Email Security Analysis
        spf_record = parse_spf_record(dns_records.get("TXT", []))
        dmarc_record = parse_dmarc_record(dns_records.get("DMARC", []))
        result["data"]["spf"] = spf_record
        result["data"]["dmarc"] = dmarc_record
        
        # AXFR Vulnerability Test
        axfr_vulnerable = await test_axfr_vulnerability(domain, dns_records.get("NS", []))
        result["data"]["axfr_vulnerable"] = axfr_vulnerable
        
        # Reputation Analysis
        reputation_score, threats = await analyze_domain_reputation(domain)
        result["data"]["reputation_score"] = reputation_score
        result["data"]["threats_detected"] = threats
        
        result["success"] = True
        
    except Exception as e:
        result["errors"].append(f"Analysis failed: {str(e)}")
    
    return result

@app.get("/", tags=["Root"])
async def health_check():
    """Health check endpoint"""
    return {
        "service": "Domain Analysis Service",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /"
        }
    }
