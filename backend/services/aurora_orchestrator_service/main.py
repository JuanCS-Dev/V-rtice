"""
Aurora Orchestrator Service - NSA Grade AI Brain
Orquestra investigações autônomas com IA decision-making
Coordena todos os microserviços de cyber security e OSINT
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import re

app = FastAPI(title="Aurora Orchestrator Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service Registry
SERVICES = {
    "ip_intelligence": {"url": "http://localhost:8002", "name": "IP Intelligence"},
    "threat_intel": {"url": "http://localhost:8013", "name": "Threat Intelligence"},
    "malware_analysis": {"url": "http://localhost:8014", "name": "Malware Analysis"},
    "ssl_monitor": {"url": "http://localhost:8015", "name": "SSL/TLS Monitor"},
    "nmap_scanner": {"url": "http://localhost:8010", "name": "Nmap Scanner"},
    "vuln_scanner": {"url": "http://localhost:8011", "name": "Vulnerability Scanner"},
    "social_eng": {"url": "http://localhost:8012", "name": "Social Engineering"},
    "domain_analyzer": {"url": "http://localhost:8003", "name": "Domain Analyzer"},
}

# Models
class InvestigationType(str, Enum):
    AUTO = "auto"
    DEFENSIVE = "defensive"
    OFFENSIVE = "offensive"
    FULL = "full"
    STEALTH = "stealth"

class TargetType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    HASH = "hash"
    EMAIL = "email"
    PHONE = "phone"
    USERNAME = "username"
    UNKNOWN = "unknown"

class InvestigationRequest(BaseModel):
    target: str
    investigation_type: InvestigationType = InvestigationType.AUTO
    priority: int = 5  # 1-10
    stealth_mode: bool = False
    deep_analysis: bool = False
    max_time: int = 300  # seconds
    callbacks: Optional[List[str]] = None

class StepResult(BaseModel):
    service: str
    action: str
    status: str  # running, completed, failed, skipped
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration: float
    timestamp: str

class InvestigationResponse(BaseModel):
    investigation_id: str
    target: str
    target_type: TargetType
    investigation_type: InvestigationType
    status: str  # running, completed, failed
    progress: int  # 0-100
    steps: List[StepResult]
    threat_assessment: Optional[Dict[str, Any]]
    recommendations: List[str]
    start_time: str
    end_time: Optional[str]
    duration: Optional[float]

# In-memory storage (em produção usar Redis/DB)
investigations_db = {}

# Aurora Decision Engine
class AuroraDecisionEngine:
    """
    O cérebro da Aurora - decide estratégias baseado em contexto
    """

    @staticmethod
    def detect_target_type(target: str) -> TargetType:
        """Detecta automaticamente o tipo de target"""
        # IP Address
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
            return TargetType.IP

        # Hash (MD5, SHA1, SHA256)
        if re.match(r'^[a-fA-F0-9]{32}$', target):
            return TargetType.HASH
        if re.match(r'^[a-fA-F0-9]{40}$', target):
            return TargetType.HASH
        if re.match(r'^[a-fA-F0-9]{64}$', target):
            return TargetType.HASH

        # Email
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target):
            return TargetType.EMAIL

        # Phone
        if re.match(r'^\+?[\d\s\-\(\)]{10,}$', target):
            return TargetType.PHONE

        # URL
        if target.startswith('http://') or target.startswith('https://'):
            return TargetType.URL

        # Domain
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?(\.[a-zA-Z]{2,})+$', target):
            return TargetType.DOMAIN

        return TargetType.UNKNOWN

    @staticmethod
    def plan_investigation(target: str, target_type: TargetType,
                          investigation_type: InvestigationType,
                          stealth_mode: bool, deep_analysis: bool) -> List[Dict[str, Any]]:
        """
        Aurora decide o workflow baseado em múltiplos fatores
        Retorna lista de steps a serem executados
        """
        workflow = []

        # FASE 1: RECONNAISSANCE (sempre executar)
        if target_type == TargetType.IP:
            workflow.append({
                "service": "threat_intel",
                "action": "check",
                "endpoint": "/api/threat-intel/check",
                "params": {"target": target, "target_type": "ip"},
                "priority": 10,
                "phase": "reconnaissance"
            })

            workflow.append({
                "service": "ip_intelligence",
                "action": "analyze",
                "endpoint": "/api/ip/analyze",
                "params": {"ip": target},
                "priority": 9,
                "phase": "reconnaissance"
            })

            if not stealth_mode:
                workflow.append({
                    "service": "nmap_scanner",
                    "action": "quick_scan",
                    "endpoint": "/api/nmap/scan",
                    "params": {"target": target, "scan_type": "quick"},
                    "priority": 7,
                    "phase": "enumeration"
                })

        elif target_type == TargetType.DOMAIN:
            workflow.append({
                "service": "threat_intel",
                "action": "check_domain",
                "endpoint": "/api/threat-intel/check",
                "params": {"target": target, "target_type": "domain"},
                "priority": 10,
                "phase": "reconnaissance"
            })

            workflow.append({
                "service": "ssl_monitor",
                "action": "check_certificate",
                "endpoint": "/api/ssl/check",
                "params": {"target": target, "port": 443},
                "priority": 8,
                "phase": "reconnaissance"
            })

            if not stealth_mode:
                workflow.append({
                    "service": "nmap_scanner",
                    "action": "service_scan",
                    "endpoint": "/api/nmap/scan",
                    "params": {"target": target, "scan_type": "service"},
                    "priority": 7,
                    "phase": "enumeration"
                })

        elif target_type == TargetType.HASH:
            workflow.append({
                "service": "malware_analysis",
                "action": "check_hash",
                "endpoint": "/api/malware/analyze-hash",
                "params": {"hash_value": target, "hash_type": "auto"},
                "priority": 10,
                "phase": "analysis"
            })

        elif target_type == TargetType.URL:
            workflow.append({
                "service": "malware_analysis",
                "action": "check_url",
                "endpoint": "/api/malware/analyze-url",
                "params": {"url": target},
                "priority": 10,
                "phase": "analysis"
            })

            # Extract domain from URL
            domain = re.findall(r'https?://([^/]+)', target)
            if domain:
                workflow.append({
                    "service": "ssl_monitor",
                    "action": "check_certificate",
                    "endpoint": "/api/ssl/check",
                    "params": {"target": domain[0], "port": 443},
                    "priority": 8,
                    "phase": "reconnaissance"
                })

        # FASE 2: OFFENSIVE (apenas se autorizado)
        if investigation_type in [InvestigationType.OFFENSIVE, InvestigationType.FULL]:
            if target_type in [TargetType.IP, TargetType.DOMAIN, TargetType.URL]:
                workflow.append({
                    "service": "vuln_scanner",
                    "action": "scan",
                    "endpoint": "/api/vuln-scanner/scan",
                    "params": {"target": target, "scan_type": "passive" if stealth_mode else "active"},
                    "priority": 6,
                    "phase": "exploitation",
                    "requires_auth": True
                })

        # FASE 3: DEEP ANALYSIS (se solicitado)
        if deep_analysis:
            if target_type == TargetType.IP:
                workflow.append({
                    "service": "nmap_scanner",
                    "action": "full_scan",
                    "endpoint": "/api/nmap/scan",
                    "params": {"target": target, "scan_type": "comprehensive"},
                    "priority": 5,
                    "phase": "deep_analysis"
                })

        # Ordenar por prioridade
        workflow.sort(key=lambda x: x['priority'], reverse=True)

        return workflow

    @staticmethod
    def assess_threat(results: List[StepResult]) -> Dict[str, Any]:
        """
        Aurora avalia todos os resultados e gera threat assessment
        """
        threat_scores = []
        malicious_indicators = []
        suspicious_indicators = []
        clean_indicators = []

        for result in results:
            if result.status == "completed" and result.data:
                data = result.data

                # Extract threat score
                if "threat_score" in data:
                    threat_scores.append(data["threat_score"])

                if "is_malicious" in data and data["is_malicious"]:
                    malicious_indicators.append(result.service)

                # SSL Analysis
                if result.service == "ssl_monitor":
                    if data.get("security_score", 0) < 70:
                        suspicious_indicators.append(f"SSL Score: {data.get('security_score')}")
                    if data.get("vulnerabilities"):
                        malicious_indicators.extend([
                            f"SSL: {v['title']}" for v in data["vulnerabilities"]
                            if v['severity'] in ['critical', 'high']
                        ])

                # Malware Analysis
                if result.service == "malware_analysis":
                    if data.get("is_malicious"):
                        malicious_indicators.append("Malware detected")

                # Threat Intel
                if result.service == "threat_intel":
                    if data.get("is_malicious"):
                        malicious_indicators.append(f"Threat Intel: {data.get('reputation')}")

        # Calculate aggregated threat score
        if threat_scores:
            avg_threat_score = sum(threat_scores) / len(threat_scores)
        else:
            avg_threat_score = 0

        # Determine threat level
        if avg_threat_score >= 80 or len(malicious_indicators) >= 2:
            threat_level = "CRITICAL"
            threat_color = "red"
        elif avg_threat_score >= 60 or len(malicious_indicators) >= 1:
            threat_level = "HIGH"
            threat_color = "orange"
        elif avg_threat_score >= 40 or len(suspicious_indicators) >= 2:
            threat_level = "MEDIUM"
            threat_color = "yellow"
        elif avg_threat_score >= 20:
            threat_level = "LOW"
            threat_color = "blue"
        else:
            threat_level = "CLEAN"
            threat_color = "green"

        return {
            "threat_level": threat_level,
            "threat_color": threat_color,
            "threat_score": int(avg_threat_score),
            "malicious_indicators": malicious_indicators[:10],
            "suspicious_indicators": suspicious_indicators[:10],
            "confidence": "high" if len(results) >= 3 else "medium" if len(results) >= 2 else "low"
        }

    @staticmethod
    def generate_recommendations(threat_assessment: Dict[str, Any],
                                results: List[StepResult]) -> List[str]:
        """
        Aurora gera recomendações baseadas em toda a investigação
        """
        recommendations = []

        threat_level = threat_assessment["threat_level"]

        if threat_level == "CRITICAL":
            recommendations.append("🚨 IMMEDIATE ACTION: Block target at firewall level")
            recommendations.append("🔥 ISOLATE: Quarantine affected systems immediately")
            recommendations.append("📞 ESCALATE: Notify security team and management")
            recommendations.append("📋 DOCUMENT: Create incident report")
            recommendations.append("🔍 INVESTIGATE: Check for lateral movement")

        elif threat_level == "HIGH":
            recommendations.append("⚠️ BLOCK: Add target to blocklist")
            recommendations.append("🔍 MONITOR: Enhanced logging and monitoring")
            recommendations.append("📊 ANALYZE: Review related traffic and connections")
            recommendations.append("🛡️ HARDEN: Review and update security policies")

        elif threat_level == "MEDIUM":
            recommendations.append("👁️ WATCH: Add to watch list")
            recommendations.append("📊 LOG: Increase logging verbosity")
            recommendations.append("🔍 PERIODIC: Schedule follow-up scans")

        elif threat_level == "LOW":
            recommendations.append("✅ MONITOR: Standard monitoring sufficient")
            recommendations.append("📊 BASELINE: Document for baseline comparison")

        else:  # CLEAN
            recommendations.append("✅ CLEAN: No immediate action required")
            recommendations.append("📊 BASELINE: Add to clean baselines")

        # Service-specific recommendations
        for result in results:
            if result.data and result.data.get("recommendations"):
                recommendations.extend(result.data["recommendations"][:2])

        return recommendations[:10]  # Top 10

# Service Executor
async def execute_service_call(step: Dict[str, Any]) -> StepResult:
    """
    Executa chamada para um microserviço
    """
    service_name = step["service"]
    service_info = SERVICES.get(service_name)

    if not service_info:
        return StepResult(
            service=service_name,
            action=step["action"],
            status="failed",
            data=None,
            error="Service not found",
            duration=0.0,
            timestamp=datetime.now().isoformat()
        )

    start_time = datetime.now()

    try:
        url = f"{service_info['url']}{step['endpoint']}"
        params = step["params"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=params)

            duration = (datetime.now() - start_time).total_seconds()

            if response.status_code == 200:
                return StepResult(
                    service=service_name,
                    action=step["action"],
                    status="completed",
                    data=response.json(),
                    error=None,
                    duration=duration,
                    timestamp=datetime.now().isoformat()
                )
            else:
                return StepResult(
                    service=service_name,
                    action=step["action"],
                    status="failed",
                    data=None,
                    error=f"HTTP {response.status_code}: {response.text}",
                    duration=duration,
                    timestamp=datetime.now().isoformat()
                )

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return StepResult(
            service=service_name,
            action=step["action"],
            status="failed",
            data=None,
            error=str(e),
            duration=duration,
            timestamp=datetime.now().isoformat()
        )

# Background Investigation Runner
async def run_investigation(investigation_id: str, target: str, target_type: TargetType,
                           investigation_type: InvestigationType, stealth_mode: bool,
                           deep_analysis: bool):
    """
    Executa investigação em background
    """
    investigation = investigations_db[investigation_id]

    # Aurora decide o workflow
    engine = AuroraDecisionEngine()
    workflow = engine.plan_investigation(
        target, target_type, investigation_type,
        stealth_mode, deep_analysis
    )

    investigation["status"] = "running"
    investigation["total_steps"] = len(workflow)

    # Execute workflow sequencialmente (em produção, pode ser paralelizado)
    for idx, step in enumerate(workflow):
        # Update progress
        progress = int((idx / len(workflow)) * 90)  # 0-90%, deixa 10% para análise final
        investigation["progress"] = progress

        # Execute step
        result = await execute_service_call(step)
        investigation["steps"].append(result)

        # Se falhou crítico, pode parar
        if result.status == "failed" and step.get("critical", False):
            break

    # Fase final: Aurora analisa tudo
    investigation["progress"] = 95

    threat_assessment = engine.assess_threat(investigation["steps"])
    investigation["threat_assessment"] = threat_assessment

    recommendations = engine.generate_recommendations(threat_assessment, investigation["steps"])
    investigation["recommendations"] = recommendations

    # Finalizar
    investigation["status"] = "completed"
    investigation["progress"] = 100
    investigation["end_time"] = datetime.now().isoformat()

    start = datetime.fromisoformat(investigation["start_time"])
    end = datetime.fromisoformat(investigation["end_time"])
    investigation["duration"] = (end - start).total_seconds()

@app.get("/")
async def root():
    return {
        "service": "Aurora Orchestrator",
        "status": "online",
        "version": "1.0.0",
        "classification": "TOP-SECRET // NSA-GRADE",
        "ai_engine": "Aurora Decision Engine v2.0",
        "registered_services": len(SERVICES),
        "capabilities": {
            "autonomous_investigation": True,
            "ai_decision_making": True,
            "multi_service_orchestration": True,
            "threat_assessment": True,
            "real_time_adaptation": True
        }
    }

@app.post("/api/aurora/investigate", response_model=InvestigationResponse)
async def start_investigation(request: InvestigationRequest, background_tasks: BackgroundTasks):
    """
    Inicia investigação orquestrada pela Aurora
    """
    # Detect target type
    engine = AuroraDecisionEngine()
    target_type = engine.detect_target_type(request.target)

    if target_type == TargetType.UNKNOWN:
        raise HTTPException(status_code=400, detail="Target type not recognized")

    # Create investigation
    investigation_id = f"AURORA-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    investigation = {
        "investigation_id": investigation_id,
        "target": request.target,
        "target_type": target_type,
        "investigation_type": request.investigation_type,
        "status": "initializing",
        "progress": 0,
        "steps": [],
        "threat_assessment": None,
        "recommendations": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "duration": None,
        "total_steps": 0
    }

    investigations_db[investigation_id] = investigation

    # Start background investigation
    background_tasks.add_task(
        run_investigation,
        investigation_id,
        request.target,
        target_type,
        request.investigation_type,
        request.stealth_mode,
        request.deep_analysis
    )

    return InvestigationResponse(**investigation)

@app.get("/api/aurora/investigation/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(investigation_id: str):
    """
    Obtém status de uma investigação
    """
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return InvestigationResponse(**investigations_db[investigation_id])

@app.get("/api/aurora/services")
async def list_services():
    """
    Lista todos os serviços disponíveis
    """
    services_status = {}

    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_id, service_info in SERVICES.items():
            try:
                response = await client.get(f"{service_info['url']}/")
                services_status[service_id] = {
                    "name": service_info["name"],
                    "url": service_info["url"],
                    "status": "online" if response.status_code == 200 else "error",
                    "response_time": response.elapsed.total_seconds()
                }
            except:
                services_status[service_id] = {
                    "name": service_info["name"],
                    "url": service_info["url"],
                    "status": "offline",
                    "response_time": None
                }

    return services_status

@app.get("/health")
async def health():
    return {"status": "healthy", "ai_engine": "operational"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8016)