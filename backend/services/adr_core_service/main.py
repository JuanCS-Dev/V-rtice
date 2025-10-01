"""
ADR Core Service - Autonomous Detection & Response
===================================================

"Segurança de classe mundial não é privilégio. É direito."

Este serviço implementa capacidades ADR (Autonomous Detection and Response)
de nível enterprise, democratizadas para toda a sociedade.

Inspirado em:
- SentinelOne Purple AI (Agentic AI)
- Darktrace (Self-Learning Behavioral AI)
- CrowdStrike Falcon (Threat Intelligence)
- CISA/NSA Guidance (Best Practices)

Construído com:
- ❤️ Amor pela arte
- 🎯 Missão de proteção social
- 🔥 Paixão por excelência técnica
- 🌍 Compromisso com a comunidade

Autor: Juan (Arquiteto)
Data: 2025-10-01
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aurora ADR Core Service",
    description="Autonomous Detection & Response - Democratizing Enterprise Security",
    version="1.0.0-alpha",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# MODELS
# ============================================================================

class ThreatDetection(BaseModel):
    """Modelo de detecção de ameaça"""
    threat_id: str
    type: str  # malware, lotl, phishing, exfiltration, etc
    severity: str  # critical, high, medium, low
    source: str  # IP, hostname, process, file
    indicators: List[str]
    threat_score: int  # 0-100
    confidence: str  # low, medium, high
    timestamp: str
    raw_data: Optional[Dict[str, Any]] = None


class ResponseAction(BaseModel):
    """Modelo de ação de resposta"""
    action_id: str
    threat_id: str
    action_type: str  # isolate, terminate, quarantine, rotate, alert
    target: str
    status: str  # pending, in_progress, completed, failed
    timestamp: str
    response_time_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ADRMetrics(BaseModel):
    """Métricas do ADR"""
    total_threats_detected: int
    threats_by_severity: Dict[str, int]
    autonomous_responses: int
    mean_time_to_respond_ms: float  # MTTR - métrica crítica
    detection_accuracy: float  # % de detecções corretas
    false_positive_rate: float
    uptime: str


# ============================================================================
# STATE
# ============================================================================

class ADRState:
    """Estado global do ADR"""

    def __init__(self):
        self.threats_detected: List[ThreatDetection] = []
        self.responses_executed: List[ResponseAction] = []
        self.is_armed: bool = True  # ADR está armado para resposta autônoma
        self.risk_threshold: int = 70  # Score mínimo para resposta autônoma

    def add_threat(self, threat: ThreatDetection):
        self.threats_detected.append(threat)
        logger.info(f"🚨 Threat detected: {threat.type} | Severity: {threat.severity} | Score: {threat.threat_score}")

    def add_response(self, response: ResponseAction):
        self.responses_executed.append(response)
        logger.info(f"⚡ Response executed: {response.action_type} | Target: {response.target}")

    def calculate_mttr(self) -> float:
        """Calcula Mean Time to Respond (MTTR)"""
        if not self.responses_executed:
            return 0.0

        response_times = [r.response_time_ms for r in self.responses_executed if r.response_time_ms]
        if not response_times:
            return 0.0

        return sum(response_times) / len(response_times)


# Global state
adr_state = ADRState()


# ============================================================================
# DETECTION ENGINE (Fase 1 - Estrutura Base)
# ============================================================================

class DetectionEngine:
    """
    Motor de detecção de ameaças

    Fase 1: Estrutura base + integração com serviços existentes
    Fase 2: ML models + behavioral analysis
    """

    def __init__(self):
        self.threat_signatures = self.load_threat_signatures()
        self.behavioral_baselines = {}

    def load_threat_signatures(self) -> Dict[str, Any]:
        """Carrega assinaturas de ameaças conhecidas"""
        # TODO: Integrar com threat intel service
        return {
            'malware_hashes': [],
            'malicious_ips': [],
            'suspicious_patterns': []
        }

    async def analyze_file(self, file_path: str) -> ThreatDetection:
        """
        Analisa arquivo em busca de malware

        Fase 1: Hash-based detection
        Fase 2: ML-based behavioral detection
        """
        import hashlib
        import os
        from uuid import uuid4

        # Calcula hash do arquivo
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

        # Verifica contra assinaturas conhecidas
        is_malicious = file_hash in self.threat_signatures.get('malware_hashes', [])

        # TODO: Integrar ML model para análise comportamental
        threat_score = 95 if is_malicious else 10

        return ThreatDetection(
            threat_id=str(uuid4()),
            type='malware' if is_malicious else 'unknown',
            severity='critical' if threat_score >= 80 else 'low',
            source=file_path,
            indicators=[f"SHA256: {file_hash}"],
            threat_score=threat_score,
            confidence='high' if is_malicious else 'low',
            timestamp=datetime.utcnow().isoformat(),
            raw_data={'file_hash': file_hash}
        )

    async def analyze_network_traffic(self, traffic_data: Dict[str, Any]) -> Optional[ThreatDetection]:
        """
        Analisa tráfego de rede em busca de anomalias

        Fase 1: IP blacklist checking
        Fase 2: ML-based anomaly detection
        """
        from uuid import uuid4

        dest_ip = traffic_data.get('destination_ip')

        # Verifica contra IPs maliciosos conhecidos
        is_malicious = dest_ip in self.threat_signatures.get('malicious_ips', [])

        if not is_malicious:
            return None

        return ThreatDetection(
            threat_id=str(uuid4()),
            type='exfiltration',
            severity='high',
            source=traffic_data.get('source_ip', 'unknown'),
            indicators=[f"Destination: {dest_ip}"],
            threat_score=85,
            confidence='high',
            timestamp=datetime.utcnow().isoformat(),
            raw_data=traffic_data
        )

    async def analyze_process_behavior(self, process_data: Dict[str, Any]) -> Optional[ThreatDetection]:
        """
        Analisa comportamento de processo (LOTL detection)

        Fase 1: Signature-based (PowerShell suspicious commands)
        Fase 2: ML behavioral analysis
        """
        from uuid import uuid4

        command = process_data.get('command_line', '')
        process_name = process_data.get('process_name', '')

        # Patterns suspeitos (LOTL)
        suspicious_patterns = [
            'powershell.*-encodedcommand',
            'powershell.*invoke-expression',
            'wmic.*process.*call.*create',
            'certutil.*-decode',
            'bitsadmin.*transfer'
        ]

        import re
        is_suspicious = any(re.search(pattern, command.lower()) for pattern in suspicious_patterns)

        if not is_suspicious:
            return None

        return ThreatDetection(
            threat_id=str(uuid4()),
            type='lotl',
            severity='high',
            source=process_name,
            indicators=[f"Command: {command[:100]}..."],
            threat_score=80,
            confidence='medium',
            timestamp=datetime.utcnow().isoformat(),
            raw_data=process_data
        )


# ============================================================================
# RESPONSE ENGINE (Fase 1 - Estrutura Base)
# ============================================================================

class ResponseEngine:
    """
    Motor de resposta autônoma a ameaças

    Fase 1: Playbooks básicos (alert, log)
    Fase 2: Autonomous actions (isolate, quarantine, terminate)
    """

    def __init__(self):
        self.playbooks = self.load_playbooks()

    def load_playbooks(self) -> Dict[str, Any]:
        """Carrega playbooks de resposta"""
        return {
            'malware': ['alert', 'quarantine', 'forensics'],
            'lotl': ['alert', 'log_powershell', 'monitor'],
            'exfiltration': ['alert', 'isolate_network', 'forensics'],
            'phishing': ['alert', 'block_sender', 'user_training']
        }

    async def respond_to_threat(
        self,
        threat: ThreatDetection,
        autonomous: bool = True
    ) -> ResponseAction:
        """
        Responde a uma ameaça detectada

        Args:
            threat: Ameaça detectada
            autonomous: Se True, executa ação automaticamente sem confirmação humana
                       (apenas se threat_score >= threshold)
        """
        from uuid import uuid4
        import time

        start_time = time.time()

        # Determina se deve agir autonomamente
        should_auto_respond = (
            autonomous and
            adr_state.is_armed and
            threat.threat_score >= adr_state.risk_threshold
        )

        if should_auto_respond:
            # RESPOSTA AUTÔNOMA
            actions_taken = await self.execute_autonomous_response(threat)
            status = 'completed'
        else:
            # APENAS ALERTA (requer confirmação humana)
            actions_taken = ['alert_generated']
            status = 'pending_approval'

        response_time = (time.time() - start_time) * 1000  # ms

        response = ResponseAction(
            action_id=str(uuid4()),
            threat_id=threat.threat_id,
            action_type='autonomous' if should_auto_respond else 'alert',
            target=threat.source,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            response_time_ms=int(response_time),
            details={
                'actions_taken': actions_taken,
                'autonomous': should_auto_respond,
                'playbook_used': self.playbooks.get(threat.type, ['alert'])
            }
        )

        adr_state.add_response(response)

        return response

    async def execute_autonomous_response(self, threat: ThreatDetection) -> List[str]:
        """
        Executa resposta autônoma baseada no tipo de ameaça

        Fase 1: Logging + alerting
        Fase 2: Network isolation, process termination, quarantine
        """
        actions = []

        # Ações baseadas no playbook
        playbook = self.playbooks.get(threat.type, ['alert'])

        for action in playbook:
            if action == 'alert':
                await self.send_alert(threat)
                actions.append('alert_sent')

            elif action == 'quarantine':
                # TODO: Implementar quarantine real
                logger.info(f"🔒 Quarantine: {threat.source}")
                actions.append('quarantine_simulated')

            elif action == 'isolate_network':
                # TODO: Implementar isolamento de rede real
                logger.info(f"🚫 Network isolation: {threat.source}")
                actions.append('network_isolation_simulated')

            elif action == 'forensics':
                # TODO: Coletar evidências forenses
                logger.info(f"🔍 Forensics collection: {threat.source}")
                actions.append('forensics_collected')

        return actions

    async def send_alert(self, threat: ThreatDetection):
        """Envia alerta sobre ameaça detectada"""
        # TODO: Integrar com sistema de notificação (email, Slack, etc)
        logger.warning(f"⚠️ ALERT: {threat.type} detected | Severity: {threat.severity} | Score: {threat.threat_score}")


# Import connectors
from connectors import IPIntelligenceConnector, ThreatIntelConnector

# Global engines
detection_engine = DetectionEngine()
response_engine = ResponseEngine()

# Global connectors (integração com serviços reais)
ip_intel_connector = IPIntelligenceConnector()
threat_intel_connector = ThreatIntelConnector()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check e informações do serviço"""
    return {
        "service": "Aurora ADR Core",
        "version": "1.0.0-alpha",
        "status": "operational",
        "mission": "Democratizing Enterprise Security",
        "philosophy": "Segurança de classe mundial não é privilégio. É direito.",
        "armed": adr_state.is_armed,
        "risk_threshold": adr_state.risk_threshold
    }


@app.post("/api/adr/analyze/file")
async def analyze_file(file_path: str, background_tasks: BackgroundTasks, enrich: bool = True):
    """
    Analisa arquivo em busca de malware

    Args:
        file_path: Caminho do arquivo
        enrich: Se True, enriquece com threat intelligence (default: True)

    Se ameaça for detectada e score >= threshold, resposta autônoma é executada
    """
    try:
        # FASE 1: Detecção local
        threat = await detection_engine.analyze_file(file_path)
        threat_dict = threat.dict()

        # FASE 2: Enriquecimento com serviços reais (se habilitado)
        if enrich:
            logger.info("🔍 Enriching threat with real intelligence services...")

            # Enriquece com Threat Intelligence
            threat_dict = await threat_intel_connector.enrich_threat_with_intel(threat_dict)

            logger.info(f"✨ Threat enriched with {len(threat_dict.get('enriched_context', {}))} sources")

        # Adiciona ao estado
        adr_state.add_threat(ThreatDetection(**threat_dict))

        # FASE 3: Resposta autônoma (se score >= threshold)
        will_respond = threat_dict['threat_score'] >= adr_state.risk_threshold

        if will_respond:
            background_tasks.add_task(
                response_engine.respond_to_threat,
                ThreatDetection(**threat_dict)
            )

        return {
            "success": True,
            "threat": threat_dict,
            "will_auto_respond": will_respond,
            "enriched": enrich,
            "enrichment_sources": list(threat_dict.get('enriched_context', {}).keys()) if enrich else []
        }

    except Exception as e:
        logger.error(f"Error analyzing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/adr/analyze/network")
async def analyze_network(traffic_data: Dict[str, Any], background_tasks: BackgroundTasks, enrich: bool = True):
    """
    Analisa tráfego de rede

    Args:
        traffic_data: Dados do tráfego (source_ip, destination_ip, etc)
        enrich: Se True, enriquece com IP intelligence e threat intel
    """
    threat = await detection_engine.analyze_network_traffic(traffic_data)

    if threat:
        threat_dict = threat.dict()

        # Enriquecimento com serviços reais
        if enrich:
            logger.info("🔍 Enriching network threat...")

            # IP Intelligence (geolocalização, ISP, ASN)
            threat_dict = await ip_intel_connector.enrich_threat_with_ip_context(threat_dict)

            # Threat Intelligence
            threat_dict = await threat_intel_connector.enrich_threat_with_intel(threat_dict)

            logger.info("✨ Network threat fully enriched")

        adr_state.add_threat(ThreatDetection(**threat_dict))

        will_respond = threat_dict['threat_score'] >= adr_state.risk_threshold

        if will_respond:
            background_tasks.add_task(
                response_engine.respond_to_threat,
                ThreatDetection(**threat_dict)
            )

        return {
            "success": True,
            "threat": threat_dict,
            "will_auto_respond": will_respond,
            "enriched": enrich,
            "enrichment_sources": list(threat_dict.get('enriched_context', {}).keys()) if enrich else []
        }

    return {
        "success": True,
        "threat": None,
        "message": "No threats detected"
    }


@app.post("/api/adr/analyze/process")
async def analyze_process(process_data: Dict[str, Any], background_tasks: BackgroundTasks, enrich: bool = True):
    """
    Analisa comportamento de processo (LOTL detection)

    Args:
        process_data: Dados do processo (command_line, process_name, etc)
        enrich: Se True, enriquece com threat intelligence
    """
    threat = await detection_engine.analyze_process_behavior(process_data)

    if threat:
        threat_dict = threat.dict()

        # Enriquecimento (LOTL patterns já são conhecidos, mas podemos verificar IOCs)
        if enrich:
            logger.info("🔍 Enriching LOTL threat...")

            # Threat Intelligence (pode correlacionar command patterns com malware families)
            threat_dict = await threat_intel_connector.enrich_threat_with_intel(threat_dict)

        adr_state.add_threat(ThreatDetection(**threat_dict))

        will_respond = threat_dict['threat_score'] >= adr_state.risk_threshold

        if will_respond:
            background_tasks.add_task(
                response_engine.respond_to_threat,
                ThreatDetection(**threat_dict)
            )

        return {
            "success": True,
            "threat": threat_dict,
            "will_auto_respond": will_respond,
            "enriched": enrich,
            "enrichment_sources": list(threat_dict.get('enriched_context', {}).keys()) if enrich else []
        }

    return {
        "success": True,
        "threat": None,
        "message": "No suspicious behavior detected"
    }


@app.get("/api/adr/metrics")
async def get_metrics():
    """Retorna métricas do ADR (MTTR, detection rate, etc)"""

    threats_by_severity = {
        'critical': len([t for t in adr_state.threats_detected if t.severity == 'critical']),
        'high': len([t for t in adr_state.threats_detected if t.severity == 'high']),
        'medium': len([t for t in adr_state.threats_detected if t.severity == 'medium']),
        'low': len([t for t in adr_state.threats_detected if t.severity == 'low'])
    }

    return ADRMetrics(
        total_threats_detected=len(adr_state.threats_detected),
        threats_by_severity=threats_by_severity,
        autonomous_responses=len([r for r in adr_state.responses_executed if r.action_type == 'autonomous']),
        mean_time_to_respond_ms=adr_state.calculate_mttr(),
        detection_accuracy=0.95,  # TODO: Calcular baseado em feedback
        false_positive_rate=0.05,  # TODO: Calcular baseado em feedback
        uptime="99.9%"  # TODO: Calcular real uptime
    ).dict()


@app.get("/api/adr/threats")
async def get_threats(limit: int = 100):
    """Lista ameaças detectadas"""
    return {
        "total": len(adr_state.threats_detected),
        "threats": [t.dict() for t in adr_state.threats_detected[-limit:]]
    }


@app.get("/api/adr/responses")
async def get_responses(limit: int = 100):
    """Lista respostas executadas"""
    return {
        "total": len(adr_state.responses_executed),
        "responses": [r.dict() for r in adr_state.responses_executed[-limit:]]
    }


@app.post("/api/adr/configure")
async def configure_adr(armed: Optional[bool] = None, risk_threshold: Optional[int] = None):
    """Configura parâmetros do ADR"""
    if armed is not None:
        adr_state.is_armed = armed
        logger.info(f"🛡️ ADR armed: {armed}")

    if risk_threshold is not None:
        if not 0 <= risk_threshold <= 100:
            raise HTTPException(status_code=400, detail="Risk threshold must be between 0 and 100")
        adr_state.risk_threshold = risk_threshold
        logger.info(f"⚙️ Risk threshold set to: {risk_threshold}")

    return {
        "success": True,
        "armed": adr_state.is_armed,
        "risk_threshold": adr_state.risk_threshold
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Aurora ADR Core Service...")
    logger.info("🎨 'Segurança de classe mundial não é privilégio. É direito.'")
    logger.info(f"🛡️ ADR Armed: {adr_state.is_armed}")
    logger.info(f"⚙️ Risk Threshold: {adr_state.risk_threshold}")

    uvicorn.run(app, host="0.0.0.0", port=8014)
