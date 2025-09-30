
import subprocess
import socket
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncio
import xml.etree.ElementTree as ET
import logging

import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Refactored imports
import models
from database import engine, Base, get_db
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IP Intelligence Service",
    description="Microsserviço para análise completa de IPs com cache inteligente.",
    version="2.0.0",
)

@app.on_event("startup")
async def startup():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Pydantic Models ---
class IPAnalysisRequest(BaseModel):
    ip: str

# --- Regex ---
IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")

# --- Analysis Functions ---

async def query_whois(ip: str) -> Dict[str, Any]:
    try:
        proc = await asyncio.create_subprocess_exec(
            "whois", ip,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return {"raw": stdout.decode()}
        return {"error": f"WHOIS failed: {stderr.decode()}"}
    except Exception as e:
        return {"error": f"WHOIS error: {str(e)}"}

async def query_reverse_dns(ip: str) -> Optional[str]:
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, socket.gethostbyaddr, ip)
        return result[0] if result else None
    except (socket.herror, Exception):
        return None

async def query_geoip(ip: str, client: httpx.AsyncClient) -> Dict[str, Any]:
    try:
        resp = await client.get(settings.IP_API_URL.format(ip=ip), timeout=5)
        if resp.status_code == 200 and resp.json().get("status") == "success":
            return {"source": "ip-api.com", **resp.json()}
    except httpx.RequestError:
        pass
    try:
        resp = await client.get(settings.IPINFO_URL.format(ip=ip), timeout=5)
        if resp.status_code == 200:
            return {"source": "ipinfo.io", **resp.json()}
    except httpx.RequestError:
        pass
    return {"source": "none", "error": "All GeoIP providers failed"}

async def analyze_ip_reputation(ip: str) -> Dict[str, Any]:
    if ip.startswith(("192.168.", "10.")) or ip.startswith("172."):
        return {"score": 95, "threat_level": "low", "categories": ["private_range"]}
    return {"score": 80, "threat_level": "medium", "last_seen": datetime.now().strftime("%Y-%m-%d")}

async def detect_open_ports(ip: str) -> List[Dict[str, Any]]:
    try:
        cmd = ["nmap", "-T4", "-F", ip, "-oX", "-"]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return []
        open_ports = []
        root = ET.fromstring(stdout.decode())
        for port in root.findall(".//port[state[@state='open']]"):
            service = port.find("service")
            open_ports.append({
                "port": int(port.get("portid")),
                "service": service.get("name") if service is not None else "unknown",
            })
        return open_ports
    except Exception:
        return []

# --- API Endpoints ---

@app.post("/analyze", tags=["IP Intelligence"])
async def analyze_ip(request: IPAnalysisRequest, db: AsyncSession = Depends(get_db)):
    ip = request.ip.strip()
    if not IPV4_RE.match(ip):
        raise HTTPException(status_code=400, detail="Invalid IPv4 format")

    cached_result = (await db.execute(select(models.IPAnalysisCache).filter_by(ip=ip))).scalar_one_or_none()
    if cached_result and (datetime.utcnow() - cached_result.timestamp) < timedelta(seconds=settings.CACHE_TTL_SECONDS):
        return {"source": "cache", **cached_result.analysis_data}

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            query_reverse_dns(ip),
            query_whois(ip),
            query_geoip(ip, client),
            analyze_ip_reputation(ip),
            detect_open_ports(ip),
            return_exceptions=True
        )
    
    ptr_record, whois_data, geo_data, reputation_data, open_ports = results

    analysis_data = {
        "timestamp": datetime.utcnow().isoformat(), "ip": ip,
        "ptr_record": ptr_record if not isinstance(ptr_record, Exception) else str(ptr_record),
        "whois": whois_data if not isinstance(whois_data, Exception) else str(whois_data),
        "geolocation": geo_data if not isinstance(geo_data, Exception) else str(geo_data),
        "reputation": reputation_data if not isinstance(reputation_data, Exception) else str(reputation_data),
        "open_ports": open_ports if not isinstance(open_ports, Exception) else str(open_ports),
    }

    new_cache_entry = models.IPAnalysisCache(ip=ip, analysis_data=analysis_data)
    await db.merge(new_cache_entry)
    await db.commit()

    return {"source": "live", **analysis_data}

@app.get("/my-ip", tags=["IP Intelligence"])
async def get_my_ip():
    logger.info("Attempting to detect public IP.")
    sources = ["https://api.ipify.org?format=json", "https://httpbin.org/ip"]
    async with httpx.AsyncClient() as client:
        for source in sources:
            try:
                logger.info(f"Trying source: {source}")
                response = await client.get(source, timeout=5)
                response.raise_for_status()
                data = response.json()
                ip = data.get("ip") or data.get("origin")
                if ip and isinstance(ip, str):
                    detected_ip = ip.split(',')[0].strip()
                    if IPV4_RE.match(detected_ip):
                        logger.info(f"Successfully detected IP {detected_ip} from {source}")
                        return {"detected_ip": detected_ip, "source": source}
            except Exception as e:
                logger.error(f"Failed to get IP from {source}. Error: {str(e)}")
                continue
    
    logger.error("All IP detection sources failed.")
    raise HTTPException(status_code=503, detail="Could not detect public IP from any source.")

@app.post("/analyze-my-ip", tags=["IP Intelligence"])
async def analyze_my_ip(db: AsyncSession = Depends(get_db)):
    try:
        my_ip_data = await get_my_ip()
        ip_to_analyze = my_ip_data.get("detected_ip")
        if not ip_to_analyze:
             raise HTTPException(status_code=500, detail="Failed to get a valid IP to analyze.")
        
        analysis_request = IPAnalysisRequest(ip=ip_to_analyze)
        return await analyze_ip(analysis_request, db)
    except HTTPException as e:
        # Re-raise the exception from get_my_ip to ensure correct status code
        raise e

@app.get("/", tags=["Root"])
async def health_check():
    return {"service": "IP Intelligence Service", "status": "operational"}
