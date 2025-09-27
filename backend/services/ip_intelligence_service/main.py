# backend/services/ip_intelligence_service/main.py

"""
IP Intelligence Service - Vértice Cyber Security Module
Migração do Batman do Cerrado ip_analyzer.py para arquitetura de microsserviços
"""

import subprocess
import socket
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="IP Intelligence Service",
    description="Microsserviço para análise completa de IPs - GeoIP, WHOIS, reputação, DNS reverso",
    version="1.0.0",
)

# Modelos de dados
class IPAnalysisRequest(BaseModel):
    ip: str

# Constantes e Regex
IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")
WHOIS_KV_RE = re.compile(r"^\s*([^:]+?)\s*:\s*(.+?)\s*$")

# --- Funções de Parsing WHOIS ---

def _parse_whois_kv(text: str) -> Dict[str, List[str]]:
    """Transforma saída WHOIS em dicionário chave-valor"""
    data: Dict[str, List[str]] = {}
    for line in text.splitlines():
        if not line or line.startswith(("%", "#")):
            continue
        match = WHOIS_KV_RE.match(line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_")
            value = match.group(2).strip()
            data.setdefault(key, []).append(value)
    return data

def _parse_ip_whois(text: str) -> Dict[str, Any]:
    """Extrai campos comuns de resposta WHOIS de IP"""
    kv = _parse_whois_kv(text)
    def get_first(keys: List[str]) -> Optional[str]:
        for key in keys:
            if key in kv:
                return kv[key][0]
        return None

    asn_str = get_first(["origin", "originas", "origin-as", "originating_as"])
    asn_num = None
    if asn_str:
        asn_match = re.search(r'\d+', asn_str)
        if asn_match:
            asn_num = int(asn_match.group(0))

    return {
        "isp": get_first(["orgname", "org-name", "organization", "owner", "descr"]),
        "asn_number": asn_num,
        "asn_name": get_first(["asn-name", "as-name"]),
        "raw": text,
    }

# --- Análise WHOIS ---

async def query_whois(ip: str) -> Dict[str, Any]:
    """Executa consulta WHOIS para um IP"""
    try:
        result = subprocess.run(
            ["whois", ip],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            whois_data = _parse_ip_whois(result.stdout)
            return whois_data
        else:
            return {"error": "WHOIS lookup failed"}
            
    except subprocess.TimeoutExpired:
        return {"error": "WHOIS timeout"}
    except Exception as e:
        return {"error": f"WHOIS error: {str(e)}"}

# --- DNS Reverso ---

async def query_reverse_dns(ip: str) -> Optional[str]:
    """Obtém registro PTR (DNS reverso) para um IP"""
    try:
        ptr_record = socket.gethostbyaddr(ip)[0]
        return ptr_record
    except socket.herror:
        return None
    except Exception:
        return None

# --- GeoIP Analysis ---

async def query_geoip(ip: str) -> Dict[str, Any]:
    """Consulta GeoIP usando múltiplos provedores com fallback"""
    session = requests.Session()
    session.headers.update({"User-Agent": "Vértice-Cyber-Security/2.0"})
    
    # Provedor 1: ip-api.com (gratuito, sem rate limit baixo)
    try:
        resp = session.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,regionName,city,lat,lon,timezone,isp,org,as,query",
            timeout=10
        )
        if resp.ok and resp.json().get("status") == "success":
            data = resp.json()
            return {
                "source": "ip-api.com",
                "country": data.get("country"),
                "country_code": data.get("countryCode"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "latitude": data.get("lat"),
                "longitude": data.get("lon"),
                "timezone": data.get("timezone"),
                "isp": data.get("isp"),
                "org": data.get("org"),
                "asn": data.get("as"),
                "raw_data": data
            }
    except requests.RequestException:
        pass

    # Provedor 2: ipinfo.io (fallback - requer token para uso intenso)
    try:
        resp = session.get(f"https://ipinfo.io/{ip}/json", timeout=10)
        if resp.ok:
            data = resp.json()
            lat, lon = None, None
            if loc := data.get("loc"):
                try:
                    lat, lon = map(float, loc.split(','))
                except (ValueError, IndexError):
                    pass
            
            return {
                "source": "ipinfo.io",
                "country": data.get("country"),
                "country_code": data.get("country"),
                "region": data.get("region"),
                "city": data.get("city"),
                "latitude": lat,
                "longitude": lon,
                "timezone": data.get("timezone"),
                "isp": data.get("org"),
                "org": data.get("org"),
                "raw_data": data
            }
    except requests.RequestException:
        pass
    
    return {"source": "none", "error": "All GeoIP providers failed"}

# --- Reputation Analysis ---

async def analyze_ip_reputation(ip: str) -> Dict[str, Any]:
    """Análise básica de reputação de IP"""
    reputation_data = {
        "score": None,
        "categories": [],
        "threat_level": "unknown",
        "last_seen": None,
        "sources": []
    }
    
    # Análise básica de padrões suspeitos
    threats = []
    
    # IPs privados são considerados seguros
    if ip.startswith(("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", 
                      "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                      "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.")):
        reputation_data["score"] = 95
        reputation_data["threat_level"] = "low"
        return reputation_data
    
    # Simula análise de reputação baseada em padrões
    # Em produção, integraria com APIs como AbuseIPDB, VirusTotal, etc.
    
    # Análise de faixas conhecidas problemáticas (exemplo)
    suspicious_ranges = ["185.220.", "198.251.", "146.70."]
    
    if any(ip.startswith(range_ip) for range_ip in suspicious_ranges):
        threats.append("Known suspicious IP range")
        reputation_data["score"] = 25
        reputation_data["threat_level"] = "high"
        reputation_data["categories"] = ["suspicious_range"]
    else:
        reputation_data["score"] = 80
        reputation_data["threat_level"] = "medium"
    
    # Adiciona timestamp simulado
    reputation_data["last_seen"] = datetime.now().strftime("%Y-%m-%d")
    reputation_data["threats_detected"] = threats
    
    return reputation_data

# --- Port Scanning Detection ---

async def detect_open_ports(ip: str) -> List[Dict[str, Any]]:
    """Detecção básica de portas abertas usando nmap se disponível"""
    try:
        # Verifica se nmap está disponível
        nmap_check = subprocess.run(["which", "nmap"], capture_output=True, text=True)
        if nmap_check.returncode != 0:
            return []
        
        # Scan rápido de portas comuns
        result = subprocess.run(
            ["nmap", "-T4", "--top-ports", "20", "-oX", "-", ip],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse básico do XML
            open_ports = []
            lines = result.stdout.split('\n')
            for line in lines:
                if 'portid=' in line and 'open' in line:
                    try:
                        port_start = line.find('portid="') + 8
                        port_end = line.find('"', port_start)
                        port = line[port_start:port_end]
                        
                        service = "unknown"
                        if 'name="' in line:
                            service_start = line.find('name="') + 6
                            service_end = line.find('"', service_start)
                            service = line[service_start:service_end]
                        
                        open_ports.append({
                            "port": int(port),
                            "service": service,
                            "state": "open"
                        })
                    except (ValueError, IndexError):
                        continue
            
            return open_ports
        
    except subprocess.TimeoutExpired:
        return [{"error": "Port scan timeout"}]
    except Exception:
        return []
    
    return []

# --- Main Analysis Endpoint ---

@app.post("/analyze", tags=["IP Intelligence"])
async def analyze_ip(request: IPAnalysisRequest):
    """Análise completa de IP - GeoIP, WHOIS, reputação, DNS reverso"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "ip": request.ip.strip(),
        "data": {},
        "errors": []
    }
    
    ip = request.ip.strip()
    
    # Validação básica do IP
    if not IPV4_RE.match(ip):
        result["errors"].append("Invalid IPv4 format")
        return result
    
    try:
        # DNS Reverso
        ptr_record = await query_reverse_dns(ip)
        result["data"]["ptr_record"] = ptr_record
        
        # WHOIS Analysis
        whois_data = await query_whois(ip)
        result["data"]["whois"] = whois_data
        
        # GeoIP Analysis
        geo_data = await query_geoip(ip)
        result["data"]["geolocation"] = geo_data
        
        # Reputation Analysis
        reputation_data = await analyze_ip_reputation(ip)
        result["data"]["reputation"] = reputation_data
        
        # Port Detection (optional, can be slow)
        open_ports = await detect_open_ports(ip)
        result["data"]["open_ports"] = open_ports
        
        # Dados consolidados para compatibilidade com frontend
        result["data"]["location"] = {
            "country": geo_data.get("country", "Unknown"),
            "region": geo_data.get("region", "Unknown"),
            "city": geo_data.get("city", "Unknown"),
            "latitude": geo_data.get("latitude"),
            "longitude": geo_data.get("longitude")
        }
        
        result["data"]["isp"] = whois_data.get("isp") or geo_data.get("isp", "Unknown")
        
        result["data"]["asn"] = {
            "number": whois_data.get("asn_number"),
            "name": whois_data.get("asn_name") or geo_data.get("asn", "Unknown")
        }
        
        result["data"]["threat_level"] = reputation_data.get("threat_level", "unknown")
        
        # Simula serviços detectados para compatibilidade
        services = []
        for port_info in open_ports:
            if isinstance(port_info, dict) and "port" in port_info:
                services.append({
                    "port": port_info["port"],
                    "service": port_info.get("service", "unknown"),
                    "version": "N/A"
                })
        result["data"]["services"] = services
        
        result["success"] = True
        
    except Exception as e:
        result["errors"].append(f"Analysis failed: {str(e)}")
    
    return result

@app.get("/", tags=["Root"])
async def health_check():
    """Health check endpoint"""
    return {
        "service": "IP Intelligence Service",
        "status": "operational", 
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze",
            "health": "GET /"
        }
    }
