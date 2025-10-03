"""
ADR Core Service - INTEGRATED & COMPLETE
==========================================

"Pela Arte. Pela Sociedade."

Versão: 2.0.0-INTEGRATED
Data: 2025-10-02
Status: PRODUCTION READY
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import logging
import uuid

# Import our engines
from engines import DetectionEngine, ResponseEngine, MLEngine
from connectors import (
    IPIntelligenceConnector,
    ThreatIntelConnector,
    MalwareAnalysisConnector
)
from playbooks import PlaybookLoader
from models import (
    ThreatDetection,
    AnalysisRequest,
    AnalysisResult,
    ResponseAction,
    PlaybookExecution,
    ServiceMetrics,
    APIResponse,
    HealthStatus,
    SeverityLevel,
    ThreatType,
    ActionType
)
from utils import setup_logger, MetricsCollector, generate_id

# Setup logging
logger = setup_logger("adr_core", level="INFO")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="ADR Core Service - INTEGRATED",
    description="Autonomous Detection & Response with Full Integration",
    version="2.0.0-integrated",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# GLOBAL STATE & ENGINES
# ============================================================================

class ADRCore:
    """Centralized ADR Core State"""

    def __init__(self):
        # Engines
        self.detection_engine: Optional[DetectionEngine] = None
        self.response_engine: Optional[ResponseEngine] = None
        self.ml_engine: Optional[MLEngine] = None

        # Connectors
        self.ip_intel_connector: Optional[IPIntelligenceConnector] = None
        self.threat_intel_connector: Optional[ThreatIntelConnector] = None
        self.malware_connector: Optional[MalwareAnalysisConnector] = None

        # Playbooks
        self.playbook_loader: Optional[PlaybookLoader] = None

        # Metrics
        self.metrics = MetricsCollector()

        # Config
        self.config = {
            'enable_auto_response': False,
            'enable_enrichment': True,
            'auto_response_threshold': 70,
            'enable_ml': True,
        }

        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize all components"""
        logger.info("🚀 Initializing ADR Core Service...")

        # Initialize engines
        logger.info("⚙️ Initializing engines...")
        self.detection_engine = DetectionEngine(config={
            'enabled': True,
            'workers': 4,
            'log_level': 'INFO'
        })

        self.response_engine = ResponseEngine(config={
            'enabled': True,
            'enable_auto_response': self.config['enable_auto_response'],
            'log_level': 'INFO'
        })

        self.ml_engine = MLEngine(config={
            'enabled': self.config['enable_ml'],
            'log_level': 'INFO'
        })

        # Initialize connectors
        logger.info("🔌 Initializing connectors...")
        self.ip_intel_connector = IPIntelligenceConnector("http://localhost:8000")
        self.threat_intel_connector = ThreatIntelConnector("http://localhost:8013")
        self.malware_connector = MalwareAnalysisConnector("http://localhost:8006")

        # Connect connectors
        await self.ip_intel_connector.connect()
        await self.threat_intel_connector.connect()
        await self.malware_connector.connect()

        # Load playbooks
        logger.info("📋 Loading playbooks...")
        self.playbook_loader = PlaybookLoader()
        playbooks = self.playbook_loader.load_all_playbooks()

        # Register playbooks in response engine
        for playbook in playbooks:
            self.response_engine.load_playbook(playbook)

        logger.info(f"✅ Loaded {len(playbooks)} playbooks")

        logger.info("✅ ADR Core Service READY")

    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("🛑 Shutting down ADR Core Service...")

        if self.ip_intel_connector:
            await self.ip_intel_connector.close()
        if self.threat_intel_connector:
            await self.threat_intel_connector.close()
        if self.malware_connector:
            await self.malware_connector.disconnect()

        logger.info("✅ ADR Core Service stopped")

# Global ADR Core instance
adr_core = ADRCore()

# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Startup initialization"""
    await adr_core.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown cleanup"""
    await adr_core.shutdown()

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class FileAnalysisRequest(BaseModel):
    file_path: str
    enrich: bool = True

class NetworkAnalysisRequest(BaseModel):
    source_ip: str
    destination_ip: str
    port: int
    protocol: str = "TCP"
    enrich: bool = True

class ProcessAnalysisRequest(BaseModel):
    process_name: str
    command_line: str
    pid: Optional[int] = None
    enrich: bool = True

class ConfigUpdate(BaseModel):
    enable_auto_response: Optional[bool] = None
    enable_enrichment: Optional[bool] = None
    auto_response_threshold: Optional[int] = None

# ============================================================================
# ENRICHMENT FUNCTIONS
# ============================================================================

async def enrich_detection(
    detection: ThreatDetection,
    enable_enrichment: bool = True
) -> ThreatDetection:
    """
    Enrich detection with external intelligence

    Returns enriched detection with:
    - IP Intelligence context
    - Threat Intelligence data
    - Malware analysis (if applicable)
    - Adjusted threat score
    """
    if not enable_enrichment or not adr_core.config['enable_enrichment']:
        return detection

    enriched = detection
    enrichment_sources = []

    try:
        # Convert to dict for connector enrichment
        detection_dict = detection.dict()

        # IP Intelligence enrichment
        if adr_core.ip_intel_connector and adr_core.ip_intel_connector.connected:
            try:
                detection_dict = await adr_core.ip_intel_connector.enrich_threat_with_ip_context(
                    detection_dict
                )
                enrichment_sources.append('ip_intelligence')
            except Exception as e:
                logger.error(f"IP Intel enrichment failed: {e}")

        # Threat Intelligence enrichment
        if adr_core.threat_intel_connector and adr_core.threat_intel_connector.connected:
            try:
                detection_dict = await adr_core.threat_intel_connector.enrich_threat_with_intel(
                    detection_dict
                )
                enrichment_sources.append('threat_intelligence')
            except Exception as e:
                logger.error(f"Threat Intel enrichment failed: {e}")

        # Malware Analysis enrichment (if file-based)
        if detection.threat_type in [ThreatType.MALWARE, ThreatType.RANSOMWARE]:
            if adr_core.malware_connector and adr_core.malware_connector.connected:
                try:
                    detection_dict = await adr_core.malware_connector.enrich(detection_dict)
                    enrichment_sources.append('malware_analysis')
                except Exception as e:
                    logger.error(f"Malware enrichment failed: {e}")

        # Reconstruct enriched detection
        # Update score and severity from enriched data
        if 'threat_score' in detection_dict:
            enriched.score = detection_dict['threat_score']
        if 'severity' in detection_dict:
            enriched.severity = SeverityLevel(detection_dict['severity'])

        # Store enriched context in evidence
        if 'enriched_context' in detection_dict:
            enriched.evidence['enriched_context'] = detection_dict['enriched_context']
            enriched.evidence['enrichment_sources'] = enrichment_sources

        # Add recommendations if available
        if 'recommendations' in detection_dict:
            enriched.evidence['recommendations'] = detection_dict['recommendations']

        logger.info(
            f"✅ Detection enriched: {len(enrichment_sources)} sources | "
            f"Score: {detection.score} → {enriched.score}"
        )

    except Exception as e:
        logger.error(f"Enrichment error: {e}")

    return enriched

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    components = {
        'detection_engine': 'healthy' if adr_core.detection_engine else 'unhealthy',
        'response_engine': 'healthy' if adr_core.response_engine else 'unhealthy',
        'ml_engine': 'healthy' if adr_core.ml_engine and adr_core.ml_engine.enabled else 'disabled',
        'ip_intel_connector': 'connected' if adr_core.ip_intel_connector and adr_core.ip_intel_connector.connected else 'disconnected',
        'threat_intel_connector': 'connected' if adr_core.threat_intel_connector and adr_core.threat_intel_connector.connected else 'disconnected',
        'malware_connector': 'connected' if adr_core.malware_connector and adr_core.malware_connector.connected else 'disconnected',
    }

    all_healthy = all(
        status in ['healthy', 'connected', 'disabled']
        for status in components.values()
    )

    return HealthStatus(
        status='healthy' if all_healthy else 'degraded',
        version='2.0.0-integrated',
        uptime_seconds=int((datetime.utcnow() - adr_core.start_time).total_seconds()),
        components=components
    )

@app.post("/api/adr/analyze/file")
async def analyze_file(request: FileAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze file for malware

    With enrichment enabled:
    - Hash-based detection
    - ML classification
    - Malware analysis service integration
    - Auto-adjusted threat score
    """
    try:
        # Create analysis request
        analysis_req = AnalysisRequest(
            request_id=generate_id("req_"),
            analysis_type="file",
            target=request.file_path,
            options={"enrich": request.enrich}
        )

        # Analyze with detection engine
        result = await adr_core.detection_engine.analyze(analysis_req)

        if not result.detections:
            return APIResponse(
                status="success",
                message="No threats detected",
                data={'result': result.dict()}
            )

        # Get primary detection
        primary_detection = result.detections[0]

        # Enrich detection
        if request.enrich:
            primary_detection = await enrich_detection(primary_detection, request.enrich)

        # Check if auto-response should trigger
        will_auto_respond = (
            adr_core.config['enable_auto_response'] and
            primary_detection.score >= adr_core.config['auto_response_threshold']
        )

        # Trigger auto-response in background
        if will_auto_respond:
            background_tasks.add_task(
                adr_core.response_engine.respond_to_threat,
                primary_detection,
                auto_approve=True
            )

        return APIResponse(
            status="success",
            message=f"Threat detected: {primary_detection.threat_type.value}",
            data={
                'threat': primary_detection.dict(),
                'will_auto_respond': will_auto_respond,
                'enriched': request.enrich,
                'enrichment_sources': primary_detection.evidence.get('enrichment_sources', [])
            }
        )

    except Exception as e:
        logger.error(f"File analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/adr/analyze/network")
async def analyze_network(request: NetworkAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze network traffic

    With enrichment:
    - IP Intelligence (geo, ISP, reputation)
    - Threat Intelligence (malicious IPs, C2)
    - Auto-adjusted threat score
    """
    try:
        analysis_req = AnalysisRequest(
            request_id=generate_id("req_"),
            analysis_type="network",
            target=f"{request.source_ip}:{request.destination_ip}:{request.port}",
            options={
                "source_ip": request.source_ip,
                "destination_ip": request.destination_ip,
                "port": request.port,
                "protocol": request.protocol,
                "enrich": request.enrich
            }
        )

        result = await adr_core.detection_engine.analyze(analysis_req)

        if not result.detections:
            return APIResponse(
                status="success",
                message="No threats detected",
                data={'result': result.dict()}
            )

        primary_detection = result.detections[0]

        if request.enrich:
            primary_detection = await enrich_detection(primary_detection, request.enrich)

        will_auto_respond = (
            adr_core.config['enable_auto_response'] and
            primary_detection.score >= adr_core.config['auto_response_threshold']
        )

        if will_auto_respond:
            background_tasks.add_task(
                adr_core.response_engine.respond_to_threat,
                primary_detection,
                auto_approve=True
            )

        return APIResponse(
            status="success",
            message=f"Threat detected: {primary_detection.threat_type.value}",
            data={
                'threat': primary_detection.dict(),
                'will_auto_respond': will_auto_respond,
                'enriched': request.enrich,
                'enrichment_sources': primary_detection.evidence.get('enrichment_sources', [])
            }
        )

    except Exception as e:
        logger.error(f"Network analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/adr/analyze/process")
async def analyze_process(request: ProcessAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze process behavior (LOTL detection)

    With enrichment:
    - Threat Intelligence correlation
    - MITRE ATT&CK mapping
    - Malware family identification
    """
    try:
        analysis_req = AnalysisRequest(
            request_id=generate_id("req_"),
            analysis_type="process",
            target=request.process_name,
            options={
                "process_name": request.process_name,
                "command_line": request.command_line,
                "pid": request.pid,
                "enrich": request.enrich
            }
        )

        result = await adr_core.detection_engine.analyze(analysis_req)

        if not result.detections:
            return APIResponse(
                status="success",
                message="No threats detected",
                data={'result': result.dict()}
            )

        primary_detection = result.detections[0]

        if request.enrich:
            primary_detection = await enrich_detection(primary_detection, request.enrich)

        will_auto_respond = (
            adr_core.config['enable_auto_response'] and
            primary_detection.score >= adr_core.config['auto_response_threshold']
        )

        if will_auto_respond:
            background_tasks.add_task(
                adr_core.response_engine.respond_to_threat,
                primary_detection,
                auto_approve=True
            )

        return APIResponse(
            status="success",
            message=f"Threat detected: {primary_detection.threat_type.value}",
            data={
                'threat': primary_detection.dict(),
                'will_auto_respond': will_auto_respond,
                'enriched': request.enrich,
                'enrichment_sources': primary_detection.evidence.get('enrichment_sources', [])
            }
        )

    except Exception as e:
        logger.error(f"Process analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/adr/metrics")
async def get_metrics():
    """Get ADR metrics"""
    detection_stats = adr_core.detection_engine.get_stats() if adr_core.detection_engine else {}
    response_stats = adr_core.response_engine.get_stats() if adr_core.response_engine else {}

    return APIResponse(
        status="success",
        data={
            'detection': detection_stats,
            'response': response_stats,
            'system': adr_core.metrics.get_summary()
        }
    )

@app.get("/api/adr/playbooks")
async def list_playbooks():
    """List loaded playbooks"""
    if not adr_core.playbook_loader:
        raise HTTPException(status_code=503, detail="Playbook loader not initialized")

    playbooks = adr_core.playbook_loader.list_playbooks()

    return APIResponse(
        status="success",
        data={'playbooks': playbooks, 'count': len(playbooks)}
    )

@app.post("/api/adr/playbooks/reload")
async def reload_playbooks():
    """Reload playbooks from disk"""
    if not adr_core.playbook_loader:
        raise HTTPException(status_code=503, detail="Playbook loader not initialized")

    count = adr_core.playbook_loader.reload_playbooks()

    # Re-register in response engine
    for playbook in adr_core.playbook_loader.loaded_playbooks.values():
        adr_core.response_engine.load_playbook(playbook)

    return APIResponse(
        status="success",
        message=f"Reloaded {count} playbooks"
    )

@app.post("/api/adr/config")
async def update_config(config: ConfigUpdate):
    """Update ADR configuration"""
    if config.enable_auto_response is not None:
        adr_core.config['enable_auto_response'] = config.enable_auto_response

    if config.enable_enrichment is not None:
        adr_core.config['enable_enrichment'] = config.enable_enrichment

    if config.auto_response_threshold is not None:
        adr_core.config['auto_response_threshold'] = config.auto_response_threshold

    return APIResponse(
        status="success",
        message="Configuration updated",
        data={'config': adr_core.config}
    )

@app.get("/api/adr/config")
async def get_config():
    """Get current ADR configuration"""
    return APIResponse(
        status="success",
        data={'config': adr_core.config}
    )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8050)
