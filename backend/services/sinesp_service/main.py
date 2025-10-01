import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from config import settings
from intelligence_agent import IntelligenceAgent
from llm_client import LLMClientFactory
from models import SinespAnalysisReport, SinespQueryInput


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the application.
    """
    # Initialize Redis cache
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

    # Initialize the LLM Client Factory
    LLMClientFactory()
    yield
    # Clean up resources if needed

app = FastAPI(
    title="SINESP Intelligence Node",
    description="Autonomous intelligence node for vehicle analysis and correlation.",
    version="4.0.0",
    lifespan=lifespan
)

def mock_sinesp_api_call(plate: str) -> dict:
    """Simulates a call to the SINESP API."""
    return {
        "plate": plate.upper(),
        "status": "COM RESTRIÇÃO DE ROUBO/FURTO",
        "details": {
            "model": "FIAT TORO",
            "color": "PRETA",
            "year": 2022,
            "city": "São Paulo",
            "state": "SP"
        }
    }

@app.post("/analyze", response_model=SinespAnalysisReport)
@cache(expire=3600)
async def analyze_plate(query: SinespQueryInput) -> SinespAnalysisReport:
    """
    Analyzes a vehicle plate, correlates with criminal hotspots, and generates an intelligence report.
    Caches the result for 1 hour.
    """
    # 1. Collect factual data
    plate_details = mock_sinesp_api_call(query.plate)
    location_analysis = None

    if query.deep_analysis:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://aurora_predict_service:8009/api/predict/check-location",
                    json={"latitude": -23.550520, "longitude": -46.633308}, # Mock location
                    timeout=5.0
                )
                response.raise_for_status()
                location_analysis = response.json()
        except httpx.RequestError:
            # If the service is down, we can proceed without this data
            location_analysis = {"error": "Aurora Predict Service unavailable."}

    facts = {
        "plate_details": plate_details,
        "location_analysis": location_analysis
    }

    # 2. Select LLM model
    model_name = 'gemini-1.5-pro-latest' if query.deep_analysis else 'gemini-1.5-flash-latest'
    llm_client = LLMClientFactory().get_client(model_name)

    # 3. Instantiate and run the intelligence agent
    agent = IntelligenceAgent(llm_client)

    try:
        # 4. Get the AI-synthesized report
        report = await agent.analyze(facts)
        return report
    except Exception as e:
        # 5. Graceful Degradation
        # If the LLM fails after all retries, return a partial report with factual data.
        return SinespAnalysisReport(
            plate_details=plate_details,
            threat_score=0, # Default score
            risk_level="INDETERMINADO",
            summary="A análise de IA falhou. As informações apresentadas são apenas dados factuais.",
            reasoning_chain=[
                "Coleta de dados factuais bem-sucedida.",
                f"Falha na síntese de IA após múltiplas tentativas. Erro: {str(e)}",
                "Retornando relatório parcial como medida de degradação graciosa."
            ],
            correlated_events=[{"type": "SYSTEM_WARNING", "description": "AI synthesis failed."}],
            recommended_actions=["Revisar dados brutos e proceder com cautela.", "Reportar falha do sistema de IA."],
            confidence_score=0.4, # Low confidence due to failure
            timestamp=datetime.now()
        )
