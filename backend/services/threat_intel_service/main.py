"""
Threat Intelligence Aggregator Service - OFFLINE FIRST
Sistema primário: Análise offline com heurísticas e database local
Sistema secundário (opcional): APIs externas como VirusTotal

ZERO TRUST em APIs externas - tudo pode ser feito offline
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from datetime import datetime
from typing import Optional, List, Dict
import asyncio
from offline_engine import OfflineThreatIntel

app = FastAPI(title="Threat Intelligence Aggregator Service - Offline First")

# Initialize offline engine
offline_engine = OfflineThreatIntel()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys (OPCIONAL - sistema funciona 100% sem elas)
USE_EXTERNAL_APIS = os.getenv("USE_EXTERNAL_APIS", "false").lower() == "true"
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
OTX_API_KEY = os.getenv("OTX_API_KEY", "")
GREYNOISE_API_KEY = os.getenv("GREYNOISE_API_KEY", "")

# Models
class ThreatIntelRequest(BaseModel):
    target: str  # IP, domain, hash, etc
    target_type: str = "auto"  # auto, ip, domain, url, hash

class ThreatIntelResponse(BaseModel):
    target: str
    target_type: str
    threat_score: int  # 0-100
    is_malicious: bool
    confidence: str  # low, medium, high
    categories: List[str]
    sources: Dict[str, dict]
    first_seen: Optional[str]
    last_seen: Optional[str]
    reputation: str
    geolocation: Optional[dict]
    recommendations: List[str]
    timestamp: str

# Funções auxiliares
def detect_target_type(target: str) -> str:
    """Detecta automaticamente o tipo de target"""
    import re

    # IP
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
        return "ip"

    # Hash (MD5, SHA1, SHA256)
    if re.match(r'^[a-fA-F0-9]{32}$', target):
        return "md5"
    if re.match(r'^[a-fA-F0-9]{40}$', target):
        return "sha1"
    if re.match(r'^[a-fA-F0-9]{64}$', target):
        return "sha256"

    # URL
    if target.startswith('http://') or target.startswith('https://'):
        return "url"

    # Domain
    if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(\.[a-zA-Z]{2,})+$', target):
        return "domain"

    return "unknown"

async def check_abuseipdb(ip: str) -> dict:
    """Consulta AbuseIPDB"""
    if not ABUSEIPDB_API_KEY:
        return {"error": "API key not configured", "available": False}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.abuseipdb.com/api/v2/check",
                headers={
                    "Key": ABUSEIPDB_API_KEY,
                    "Accept": "application/json"
                },
                params={"ipAddress": ip, "maxAgeInDays": 90}
            )

            if response.status_code == 200:
                data = response.json()["data"]
                return {
                    "available": True,
                    "abuse_score": data.get("abuseConfidenceScore", 0),
                    "is_whitelisted": data.get("isWhitelisted", False),
                    "total_reports": data.get("totalReports", 0),
                    "country": data.get("countryCode", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "usage_type": data.get("usageType", "Unknown"),
                    "domain": data.get("domain", ""),
                    "last_reported": data.get("lastReportedAt", None)
                }
    except Exception as e:
        return {"error": str(e), "available": False}

    return {"available": False}

async def check_virustotal(target: str, target_type: str) -> dict:
    """Consulta VirusTotal"""
    if not VIRUSTOTAL_API_KEY:
        return {"error": "API key not configured", "available": False}

    try:
        async with httpx.AsyncClient() as client:
            if target_type == "ip":
                url = f"https://www.virustotal.com/api/v3/ip_addresses/{target}"
            elif target_type == "domain":
                url = f"https://www.virustotal.com/api/v3/domains/{target}"
            elif target_type in ["md5", "sha1", "sha256"]:
                url = f"https://www.virustotal.com/api/v3/files/{target}"
            else:
                return {"available": False}

            response = await client.get(
                url,
                headers={"x-apikey": VIRUSTOTAL_API_KEY}
            )

            if response.status_code == 200:
                data = response.json()["data"]
                attributes = data.get("attributes", {})
                stats = attributes.get("last_analysis_stats", {})

                return {
                    "available": True,
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0),
                    "reputation": attributes.get("reputation", 0),
                    "categories": attributes.get("categories", {}),
                    "last_analysis": attributes.get("last_analysis_date", None)
                }
    except Exception as e:
        return {"error": str(e), "available": False}

    return {"available": False}

async def check_greynoise(ip: str) -> dict:
    """Consulta GreyNoise"""
    if not GREYNOISE_API_KEY:
        return {"error": "API key not configured", "available": False}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.greynoise.io/v3/community/{ip}",
                headers={"key": GREYNOISE_API_KEY}
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "noise": data.get("noise", False),
                    "riot": data.get("riot", False),
                    "classification": data.get("classification", "unknown"),
                    "name": data.get("name", ""),
                    "link": data.get("link", ""),
                    "last_seen": data.get("last_seen", None)
                }
    except Exception as e:
        return {"error": str(e), "available": False}

    return {"available": False}

def calculate_threat_score(sources: dict) -> tuple:
    """Calcula threat score agregado de todas as fontes"""
    scores = []
    malicious_count = 0
    total_sources = 0

    # AbuseIPDB
    if sources.get("abuseipdb", {}).get("available"):
        abuse_data = sources["abuseipdb"]
        scores.append(abuse_data.get("abuse_score", 0))
        if abuse_data.get("total_reports", 0) > 0:
            malicious_count += 1
        total_sources += 1

    # VirusTotal
    if sources.get("virustotal", {}).get("available"):
        vt_data = sources["virustotal"]
        malicious = vt_data.get("malicious", 0)
        total = malicious + vt_data.get("harmless", 0) + vt_data.get("undetected", 0)
        if total > 0:
            vt_score = (malicious / total) * 100
            scores.append(vt_score)
            if malicious > 0:
                malicious_count += 1
        total_sources += 1

    # GreyNoise
    if sources.get("greynoise", {}).get("available"):
        gn_data = sources["greynoise"]
        if gn_data.get("classification") == "malicious":
            scores.append(80)
            malicious_count += 1
        elif gn_data.get("noise"):
            scores.append(40)
        total_sources += 1

    # Calcular score final
    if scores:
        final_score = sum(scores) // len(scores)
    else:
        final_score = 0

    # Determinar se é malicioso
    is_malicious = malicious_count >= 1 or final_score >= 60

    # Confidence
    if total_sources >= 3:
        confidence = "high"
    elif total_sources == 2:
        confidence = "medium"
    else:
        confidence = "low"

    return final_score, is_malicious, confidence

def generate_recommendations(threat_score: int, is_malicious: bool, sources: dict) -> List[str]:
    """Gera recomendações baseadas na análise"""
    recommendations = []

    if is_malicious:
        recommendations.append("🚨 BLOQUEAR: Target identificado como malicioso")
        recommendations.append("📋 Adicionar à blocklist do firewall")
        recommendations.append("🔍 Investigar conexões relacionadas")

        if threat_score >= 80:
            recommendations.append("⚠️ CRÍTICO: Ameaça de alto risco detectada")
            recommendations.append("📞 Notificar equipe de segurança imediatamente")
    elif threat_score >= 40:
        recommendations.append("⚠️ MONITORAR: Atividade suspeita detectada")
        recommendations.append("📊 Aumentar logging para este target")
        recommendations.append("🔍 Análise adicional recomendada")
    else:
        recommendations.append("✅ LIMPO: Nenhuma ameaça significativa detectada")
        recommendations.append("📊 Manter monitoramento padrão")

    # Recomendações específicas por fonte
    if sources.get("greynoise", {}).get("riot"):
        recommendations.append("ℹ️ IP identificado como serviço legítimo (RIOT)")

    return recommendations

@app.get("/")
async def root():
    return {
        "service": "Threat Intelligence Aggregator",
        "status": "online",
        "version": "1.0.0",
        "sources": {
            "abuseipdb": bool(ABUSEIPDB_API_KEY),
            "virustotal": bool(VIRUSTOTAL_API_KEY),
            "greynoise": bool(GREYNOISE_API_KEY),
            "otx": bool(OTX_API_KEY)
        }
    }

@app.post("/api/threat-intel/check", response_model=ThreatIntelResponse)
async def check_threat_intelligence(request: ThreatIntelRequest):
    """
    Análise de threat intelligence - OFFLINE FIRST
    1. Usa offline engine (heurísticas + database local)
    2. Opcionalmente complementa com APIs externas (se habilitado)
    """
    target = request.target
    target_type = request.target_type

    # Auto-detect target type
    if target_type == "auto":
        target_type = detect_target_type(target)

    if target_type == "unknown":
        raise HTTPException(status_code=400, detail="Tipo de target não reconhecido")

    # ============================
    # FASE 1: ANÁLISE OFFLINE (PRIMÁRIA)
    # ============================
    offline_result = None
    if target_type == "ip":
        offline_result = offline_engine.check_ip(target)
    elif target_type == "domain":
        offline_result = offline_engine.check_domain(target)

    # Coletar dados de todas as fontes
    sources = {
        "offline_engine": {
            "available": True,
            "threat_score": offline_result.get("threat_score", 0) if offline_result else 0,
            "is_malicious": offline_result.get("is_malicious", False) if offline_result else False,
            "indicators": offline_result.get("indicators", []) if offline_result else [],
            "confidence": offline_result.get("confidence", "low") if offline_result else "low",
            "details": offline_result.get("details", {}) if offline_result else {}
        }
    }

    # ============================
    # FASE 2: APIs EXTERNAS (OPCIONAL - apenas se habilitado)
    # ============================
    if USE_EXTERNAL_APIS:
        if target_type == "ip":
            results = await asyncio.gather(
                check_abuseipdb(target),
                check_virustotal(target, target_type),
                check_greynoise(target),
                return_exceptions=True
            )

            sources["abuseipdb"] = results[0] if not isinstance(results[0], Exception) else {"available": False}
            sources["virustotal"] = results[1] if not isinstance(results[1], Exception) else {"available": False}
            sources["greynoise"] = results[2] if not isinstance(results[2], Exception) else {"available": False}
        elif target_type in ["domain", "md5", "sha1", "sha256"]:
            vt_result = await check_virustotal(target, target_type)
            sources["virustotal"] = vt_result
    else:
        # APIs desabilitadas - apenas offline engine
        sources["external_apis"] = {"available": False, "reason": "APIs desabilitadas - modo offline"}

    # Calcular threat score agregado
    threat_score, is_malicious, confidence = calculate_threat_score(sources)

    # Determinar reputação
    if threat_score >= 80:
        reputation = "malicious"
    elif threat_score >= 60:
        reputation = "suspicious"
    elif threat_score >= 40:
        reputation = "questionable"
    else:
        reputation = "clean"

    # Extrair categorias
    categories = []
    if sources.get("virustotal", {}).get("available"):
        vt_categories = sources["virustotal"].get("categories", {})
        categories.extend(vt_categories.keys() if isinstance(vt_categories, dict) else [])

    # Gerar recomendações
    recommendations = generate_recommendations(threat_score, is_malicious, sources)

    # Geolocation (se disponível)
    geolocation = None
    if sources.get("abuseipdb", {}).get("available"):
        abuse_data = sources["abuseipdb"]
        geolocation = {
            "country": abuse_data.get("country", "Unknown"),
            "isp": abuse_data.get("isp", "Unknown")
        }

    # Timestamps
    last_seen = None
    first_seen = None

    if sources.get("abuseipdb", {}).get("last_reported"):
        last_seen = sources["abuseipdb"]["last_reported"]
    elif sources.get("greynoise", {}).get("last_seen"):
        last_seen = sources["greynoise"]["last_seen"]

    return ThreatIntelResponse(
        target=target,
        target_type=target_type,
        threat_score=threat_score,
        is_malicious=is_malicious,
        confidence=confidence,
        categories=categories[:5],  # Top 5 categories
        sources=sources,
        first_seen=first_seen,
        last_seen=last_seen,
        reputation=reputation,
        geolocation=geolocation,
        recommendations=recommendations,
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)