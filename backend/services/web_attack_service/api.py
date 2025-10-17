"""Maximus Web Attack Service - API Endpoints.

This module defines the FastAPI application and its endpoints for the Web Attack
Service. It exposes functionalities for initiating web vulnerability scans,
executing AI-generated attack payloads, and integrating with specialized tools
like Burp Suite and OWASP ZAP.

Key functionalities include:
- Orchestrating web vulnerability assessments.
- Providing an interface for AI-driven attack vector generation.
- Managing the lifecycle of web attack operations.

This API allows other Maximus AI services or human operators to leverage the
Web Attack Service's capabilities for automated penetration testing, red teaming,
and proactive cybersecurity defense, focusing on web-specific attack surfaces.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from services.web_attack_service.ai_copilot import AICoPilot
from services.web_attack_service.burp_wrapper import BurpSuiteWrapper
from services.web_attack_service.config import get_settings
from services.web_attack_service.models import *
from services.web_attack_service.zap_wrapper import ZAPWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Scanners
ai_copilot: Optional[AICoPilot] = None
burp_wrapper: Optional[BurpSuiteWrapper] = None
zap_wrapper: Optional[ZAPWrapper] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida do serviço, inicializando e desligando componentes.

    Args:
        app (FastAPI): A instância da aplicação FastAPI.

    Yields:
        None
    """
    global ai_copilot, burp_wrapper, zap_wrapper

    logger.info("Starting Web Application Attack Service")

    # Initialize AI Co-Pilot (Gemini/Anthropic hybrid)
    ai_copilot = AICoPilot(
        gemini_api_key=settings.GEMINI_API_KEY,
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        default_provider=AIProvider.AUTO,
        prefrontal_cortex_url=settings.PREFRONTAL_CORTEX_URL,
    )

    # Initialize Burp Suite
    if settings.BURP_API_URL:
        burp_wrapper = BurpSuiteWrapper(burp_api_url=settings.BURP_API_URL, burp_api_key=settings.BURP_API_KEY)

    # Initialize ZAP
    if settings.ZAP_API_URL:
        zap_wrapper = ZAPWrapper(zap_api_url=settings.ZAP_API_URL, zap_api_key=settings.ZAP_API_KEY)

    yield

    logger.info("Shutting down Web Application Attack Service")


app = FastAPI(
    title="Web Application Attack Service",
    description="AI-Powered Web Security Testing: Burp Suite + OWASP ZAP + AI Co-Pilot",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Realiza uma verificação de saúde do serviço Web Application Attack.

    Retorna:
        Dict: Um dicionário indicando o status de saúde do serviço e seus componentes.
    """
    return {
        "status": "healthy",
        "service": "web_application_attack",
        "ai_copilot": ai_copilot is not None,
        "burp_suite": burp_wrapper is not None,
        "zap": zap_wrapper is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v1/scan/burp", response_model=BurpScanResult)
async def burp_scan(request: BurpScanRequest):
    """Executa uma varredura do Burp Suite em um alvo especificado.

    Args:
        request (BurpScanRequest): Os detalhes da requisição de varredura do Burp Suite.

    Returns:
        BurpScanResult: Os resultados da varredura do Burp Suite.

    Raises:
        HTTPException: Se o Burp Suite não estiver configurado.
    """
    if not burp_wrapper:
        raise HTTPException(500, "Burp Suite not configured")

    result = await burp_wrapper.scan(request, ai_copilot)
    return result


@app.post("/api/v1/scan/zap", response_model=ZAPScanResult)
async def zap_scan(request: ZAPScanRequest):
    """Executa uma varredura do OWASP ZAP em um alvo especificado.

    Args:
        request (ZAPScanRequest): Os detalhes da requisição de varredura do ZAP.

    Returns:
        ZAPScanResult: Os resultados da varredura do ZAP.

    Raises:
        HTTPException: Se o ZAP não estiver configurado.
    """
    if not zap_wrapper:
        raise HTTPException(500, "ZAP not configured")

    result = await zap_wrapper.scan(request)
    return result


@app.post("/api/v1/ai/generate-payloads", response_model=AICoPilotResponse)
async def generate_attack_payloads(request: AICoPilotRequest):
    """Gera payloads de ataque usando o AI Co-Pilot.

    Args:
        request (AICoPilotRequest): A requisição contendo o contexto para a geração de payloads.

    Returns:
        AICoPilotResponse: A resposta do AI Co-Pilot com os payloads gerados e a análise.

    Raises:
        HTTPException: Se o AI Co-Pilot não estiver disponível.
    """
    if not ai_copilot:
        raise HTTPException(500, "AI Co-Pilot not available")

    response = await ai_copilot.generate_attack_vectors(request)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8034)
