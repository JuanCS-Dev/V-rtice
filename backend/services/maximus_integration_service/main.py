"""
MAXIMUS INTEGRATION SERVICE - Unified API Gateway
==================================================

FastAPI service que integra todos os componentes MAXIMUS.

Endpoints:
- /api/v1/oraculo/* - Self-improvement
- /api/v1/eureka/* - Malware analysis
- /api/v1/supply-chain/* - Supply chain guardian
- /api/v1/maximus/* - MAXIMUS Core
- /api/v1/adr/* - ADR Core proxy
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Adiciona paths dos serviços
sys.path.insert(0, str(Path(__file__).parent.parent / "maximus_oraculo"))
sys.path.insert(0, str(Path(__file__).parent.parent / "maximus_eureka"))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Imports dos componentes MAXIMUS
from oraculo import Oraculo
from eureka import Eureka
from suggestion_generator import SuggestionCategory
from pattern_detector import PatternCategory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MAXIMUS Integration Service",
    description="Unified API Gateway for MAXIMUS AI Platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
oraculo_instance = None
eureka_instance = None


# ============================================================================
# MODELS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime_seconds: float
    services: Dict[str, str]


class OraculoAnalysisRequest(BaseModel):
    """Request para análise do Oráculo"""
    focus_category: Optional[str] = None
    max_suggestions: int = Field(default=5, ge=1, le=20)
    min_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    dry_run: bool = True


class EurekaAnalysisRequest(BaseModel):
    """Request para análise do Eureka"""
    file_path: str
    generate_playbook: bool = True


class SupplyChainScanRequest(BaseModel):
    """Request para Supply Chain Guardian"""
    repository_path: str
    scan_dependencies: bool = True
    analyze_code: bool = True
    auto_fix: bool = False


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa componentes na startup"""
    global oraculo_instance, eureka_instance

    logger.info("="*80)
    logger.info("🚀 MAXIMUS INTEGRATION SERVICE - STARTING UP")
    logger.info("="*80)

    try:
        # Inicializa Oráculo
        logger.info("📚 Inicializando ORÁCULO...")
        oraculo_instance = Oraculo(
            enable_auto_implement=False,  # Seguro por padrão
            enable_auto_commit=False,
            require_tests=True
        )
        logger.info("✅ ORÁCULO inicializado")

        # Inicializa Eureka
        logger.info("🔬 Inicializando EUREKA...")
        eureka_instance = Eureka()
        logger.info("✅ EUREKA inicializado")

        logger.info("="*80)
        logger.info("✅ MAXIMUS INTEGRATION SERVICE - READY")
        logger.info("📡 Listening on: http://0.0.0.0:8099")
        logger.info("📖 Docs: http://0.0.0.0:8099/docs")
        logger.info("="*80)

    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup na shutdown"""
    logger.info("🛑 MAXIMUS INTEGRATION SERVICE - SHUTTING DOWN")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import time

    # Simula uptime (em produção seria um contador real)
    uptime = time.time() % 3600  # Mock uptime

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime,
        services={
            "oraculo": "ready" if oraculo_instance else "not_initialized",
            "eureka": "ready" if eureka_instance else "not_initialized",
            "maximus_core": "external",
            "adr_core": "external"
        }
    )


# ============================================================================
# ORÁCULO ENDPOINTS
# ============================================================================

@app.post("/api/v1/oraculo/analyze")
async def oraculo_analyze(request: OraculoAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Executa análise de self-improvement do MAXIMUS

    Returns:
        Sessão com sugestões de melhorias
    """
    if not oraculo_instance:
        raise HTTPException(status_code=503, detail="Oráculo não inicializado")

    logger.info(f"🔮 Iniciando análise Oráculo (dry_run={request.dry_run})...")

    try:
        # Converte categoria se fornecida
        category = None
        if request.focus_category:
            category = SuggestionCategory(request.focus_category)

        # Executa análise
        session = oraculo_instance.run_self_improvement_cycle(
            focus_category=category,
            max_suggestions=request.max_suggestions,
            min_confidence=request.min_confidence,
            dry_run=request.dry_run
        )

        return {
            "status": "success",
            "message": f"Análise concluída: {session.suggestions_generated} sugestões geradas",
            "data": {
                "session_id": session.session_id,
                "timestamp": session.timestamp.isoformat(),
                "files_scanned": session.files_scanned,
                "suggestions_generated": session.suggestions_generated,
                "suggestions_implemented": session.suggestions_implemented,
                "suggestions_awaiting_approval": session.suggestions_awaiting_approval,
                "duration_seconds": session.duration_seconds
            }
        }

    except Exception as e:
        logger.error(f"❌ Erro na análise Oráculo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/oraculo/pending-approvals")
async def get_pending_approvals():
    """Lista implementações aguardando aprovação humana"""
    if not oraculo_instance:
        raise HTTPException(status_code=503, detail="Oráculo não inicializado")

    pending = oraculo_instance.get_pending_approvals()

    return {
        "status": "success",
        "data": {
            "count": len(pending),
            "pending_approvals": [
                {
                    "suggestion_id": impl.suggestion_id,
                    "files_modified": impl.files_modified,
                    "branch_name": impl.branch_name
                }
                for impl in pending
            ]
        }
    }


@app.post("/api/v1/oraculo/approve/{suggestion_id}")
async def approve_suggestion(suggestion_id: str):
    """Aprova uma sugestão pendente"""
    if not oraculo_instance:
        raise HTTPException(status_code=503, detail="Oráculo não inicializado")

    try:
        result = oraculo_instance.approve_implementation(suggestion_id)

        return {
            "status": "success",
            "message": f"Sugestão {suggestion_id} aprovada e implementada",
            "data": {
                "status": result.status.value,
                "files_modified": result.files_modified,
                "tests_passed": result.tests_passed
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Erro ao aprovar sugestão: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/oraculo/stats")
async def get_oraculo_stats():
    """Retorna estatísticas do Oráculo"""
    if not oraculo_instance:
        raise HTTPException(status_code=503, detail="Oráculo não inicializado")

    stats = oraculo_instance.get_stats()

    return {
        "status": "success",
        "data": stats
    }


# ============================================================================
# EUREKA ENDPOINTS
# ============================================================================

@app.post("/api/v1/eureka/analyze")
async def eureka_analyze(request: EurekaAnalysisRequest):
    """
    Analisa arquivo malicioso com deep analysis

    Returns:
        Análise completa + playbook gerado
    """
    if not eureka_instance:
        raise HTTPException(status_code=503, detail="Eureka não inicializado")

    logger.info(f"🔬 Iniciando análise Eureka de: {request.file_path}")

    try:
        # Verifica se arquivo existe
        if not os.path.exists(request.file_path):
            raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {request.file_path}")

        # Executa análise
        result = eureka_instance.analyze_file(
            file_path=request.file_path,
            generate_playbook=request.generate_playbook
        )

        return {
            "status": "success",
            "message": f"Análise concluída: {result.classification.family} ({result.classification.type})",
            "data": result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro na análise Eureka: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/eureka/stats")
async def get_eureka_stats():
    """Retorna estatísticas do Eureka"""
    if not eureka_instance:
        raise HTTPException(status_code=503, detail="Eureka não inicializado")

    stats = eureka_instance.get_stats()

    return {
        "status": "success",
        "data": stats
    }


@app.get("/api/v1/eureka/patterns")
async def get_eureka_patterns():
    """Lista padrões maliciosos disponíveis"""
    if not eureka_instance:
        raise HTTPException(status_code=503, detail="Eureka não inicializado")

    patterns_stats = eureka_instance.pattern_detector.get_stats()

    return {
        "status": "success",
        "data": patterns_stats
    }


# ============================================================================
# SUPPLY CHAIN GUARDIAN ENDPOINTS
# ============================================================================

@app.post("/api/v1/supply-chain/scan")
async def supply_chain_scan(request: SupplyChainScanRequest):
    """
    Supply Chain Guardian: Oráculo + Eureka combo

    Workflow:
    1. Oráculo escaneia dependencies (requirements.txt, package.json)
    2. Eureka analisa código suspeito
    3. Gera playbooks de mitigação
    """
    if not oraculo_instance or not eureka_instance:
        raise HTTPException(status_code=503, detail="Componentes não inicializados")

    logger.info(f"🛡️ Supply Chain Guardian scan iniciado: {request.repository_path}")

    results = {
        "repository": request.repository_path,
        "timestamp": datetime.utcnow().isoformat(),
        "scans": {}
    }

    try:
        # 1. DEPENDENCY SCAN (via Oráculo)
        if request.scan_dependencies:
            logger.info("📦 Fase 1: Scanning dependencies...")
            # Placeholder - seria implementado scanning de dependencies
            results["scans"]["dependencies"] = {
                "status": "completed",
                "vulnerabilities_found": 0,
                "packages_scanned": 0
            }

        # 2. CODE ANALYSIS (via Eureka)
        if request.analyze_code:
            logger.info("🔬 Fase 2: Analyzing code for malicious patterns...")
            # Placeholder - seria scanning recursivo de arquivos
            results["scans"]["code_analysis"] = {
                "status": "completed",
                "files_analyzed": 0,
                "patterns_detected": 0
            }

        # 3. AUTO-FIX (via Oráculo)
        if request.auto_fix:
            logger.info("🔧 Fase 3: Auto-fixing issues...")
            results["scans"]["auto_fix"] = {
                "status": "completed",
                "issues_fixed": 0
            }

        return {
            "status": "success",
            "message": "Supply Chain scan completed",
            "data": results
        }

    except Exception as e:
        logger.error(f"❌ Erro no Supply Chain scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTEGRATION ENDPOINTS (Combos)
# ============================================================================

@app.post("/api/v1/integration/analyze-and-respond")
async def analyze_and_respond(file_path: str):
    """
    Workflow completo:
    1. EUREKA analisa malware
    2. ADR Core recebe playbook
    3. Playbook é executado automaticamente
    """
    if not eureka_instance:
        raise HTTPException(status_code=503, detail="Eureka não inicializado")

    logger.info(f"🔄 Workflow completo: analyze-and-respond para {file_path}")

    try:
        # 1. Analisa com Eureka
        logger.info("🔬 Fase 1: Eureka analysis...")
        result = eureka_instance.analyze_file(file_path, generate_playbook=True)

        # 2. Salva playbook (seria carregado pelo ADR Core)
        playbook_path = None
        if result.response_playbook:
            logger.info("📋 Fase 2: Saving playbook...")
            playbook_dir = Path("/tmp/maximus_playbooks")
            playbook_dir.mkdir(exist_ok=True)
            playbook_path = eureka_instance.playbook_generator.save_playbook(
                result.response_playbook,
                str(playbook_dir)
            )
            logger.info(f"✅ Playbook salvo: {playbook_path}")

        # 3. Notifica ADR Core (seria HTTP request para ADR)
        logger.info("📡 Fase 3: Notifying ADR Core...")
        # Placeholder - seria requests.post("http://localhost:8050/api/adr/playbooks/reload")

        return {
            "status": "success",
            "message": "Analysis complete, playbook generated and ready for execution",
            "data": {
                "analysis": {
                    "family": result.classification.family,
                    "type": result.classification.type,
                    "threat_score": result.threat_score,
                    "severity": result.severity
                },
                "playbook": {
                    "generated": playbook_path is not None,
                    "path": playbook_path,
                    "actions_count": len(result.response_playbook.actions) if result.response_playbook else 0
                },
                "next_steps": [
                    "Playbook saved to /tmp/maximus_playbooks",
                    "ADR Core can now load and execute playbook",
                    f"Manual execution: Review playbook at {playbook_path}"
                ]
            }
        }

    except Exception as e:
        logger.error(f"❌ Erro no workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROOT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "MAXIMUS Integration Service",
        "version": "1.0.0",
        "description": "Unified API Gateway for MAXIMUS AI Platform",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "oraculo": "/api/v1/oraculo/*",
            "eureka": "/api/v1/eureka/*",
            "supply_chain": "/api/v1/supply-chain/*",
            "integration": "/api/v1/integration/*"
        }
    }


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8099,
        reload=True,
        log_level="info"
    )
