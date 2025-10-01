import logging
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from loguru import logger
from starlette.requests import Request
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter

from .config import settings
from .sinesp_client import SinespAPIClient, SinespAPIError
from .sinesp_service import SinespService, InvalidPlateError

# Configure basic logging with loguru
logger.add("file.log", rotation="500 MB")  # Example: log to file, rotate at 500MB
logger.info("Sinesp Service starting up...")

# Override default Python logging with loguru
logging.basicConfig(handlers=[logger.handlers[0]], level=logging.INFO)

app = FastAPI(
    title="VÉRTICE - Microsserviço SINESP",
    description="Serviço dedicado para consultas na API do SINESP Cidadão, integrado com a arquitetura AI-FIRST.",
    version="1.0.0",
)

# Rate Limiting Setup
storage = MemoryStorage()
limiter = MovingWindowRateLimiter(storage)
# Define a rate limit for the entire service or specific endpoints
# For AI-FIRST, rate limits should be carefully considered based on expected AI usage
rate_limit_string = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"


# Dependency for SinespAPIClient
def get_sinesp_api_client() -> SinespAPIClient:
    return SinespAPIClient()


# Dependency for SinespService
def get_sinesp_service(
    sinesp_api_client: SinespAPIClient = Depends(get_sinesp_api_client),
) -> SinespService:
    return SinespService(sinesp_api_client)


# Placeholder for Authentication Dependency
# In a real AI-FIRST system, this would likely come from a shared library
# or an authentication service, verifying JWT tokens from the API Gateway.
async def get_current_user():
    # This is a placeholder. Implement actual authentication logic here.
    # For now, it just allows access.
    # In production, you'd validate a token, fetch user info, etc.
    return {"user_id": "ai_agent", "roles": ["system", "ai_agent"]}


# Pydantic Models for API contract
class VehiclePlateRequest(BaseModel):
    plate: str = Field(
        ..., min_length=7, max_length=7, pattern="^[A-Z0-9]{7}$", example="ABC1234"
    )


class SinespResponse(BaseModel):
    status_code: int
    message: str
    data: dict  # Placeholder, should be a more specific Pydantic model


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Monitoring"])
async def health_check():
    """Health check endpoint to verify service status."""
    logger.info("Health check requested.")
    return {"status": "ok", "service": "sinesp_service"}


@app.get("/consultar/{placa}", tags=["Consulta"])
async def consultar_placa_get(
    placa: str,
    sinesp_service: SinespService = Depends(get_sinesp_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Consulta dados de um veículo via GET (compatibilidade com API Gateway).
    Endpoint legado mantido para retrocompatibilidade com frontend.
    """
    logger.info(f"GET request for plate: {placa} from user: {current_user.get('user_id')}")

    try:
        sinesp_data = await sinesp_service.get_vehicle_data(placa.upper())
        logger.info(f"Successfully fetched data for plate: {placa}")

        # Enriquecer dados com campos esperados pelo frontend
        enriched_data = {
            **sinesp_data,
            "placa": placa.upper(),
            "lastKnownLocation": sinesp_data.get("lastKnownLocation", {
                "lat": -16.328,
                "lng": -48.953
            }),
            "riskLevel": "LOW",  # Placeholder - pode ser calculado por IA
            "situacao": sinesp_data.get("situacao", "N/A"),
            "marca": sinesp_data.get("marca", "N/A"),
            "modelo": sinesp_data.get("modelo", "N/A"),
            "ano": sinesp_data.get("ano", "N/A"),
            "cor": sinesp_data.get("cor", "N/A"),
            "municipio": sinesp_data.get("municipio", "N/A"),
            "uf": sinesp_data.get("uf", "N/A"),
        }

        return enriched_data

    except InvalidPlateError as exc:
        logger.warning(f"Invalid plate format for {placa}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de placa inválido: {exc}",
        )
    except SinespAPIError as exc:
        logger.error(f"Sinesp API error for plate {placa}: {exc.status_code} - {exc.response_text}")
        raise HTTPException(
            status_code=exc.status_code if exc.status_code else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro na API do SINESP: {str(exc)}",
        )
    except Exception as exc:
        logger.error(f"Internal server error for plate {placa}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno inesperado: {str(exc)}",
        )


@app.post("/vehicle-data", response_model=SinespResponse, tags=["Consulta AI-FIRST"])
async def get_vehicle_data(
    request: VehiclePlateRequest,
    sinesp_service: SinespService = Depends(get_sinesp_service),
    current_user: dict = Depends(get_current_user),  # Apply authentication
    http_request: Request = Request,  # For rate limiting
):
    """
    Consulta dados de um veículo na base de dados do SINESP (AI-FIRST endpoint).
    Esta ferramenta é utilizada pelo Agente de IA para obter informações detalhadas de veículos.

    Novo endpoint AI-FIRST com validação Pydantic e rate limiting.
    """
    # Apply rate limiting
    if not limiter.hit(rate_limit_string, http_request.client.host):
        logger.warning(f"Rate limit exceeded for client: {http_request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {60 / settings.RATE_LIMIT_PER_MINUTE:.0f} seconds.",
        )

    logger.info(
        f"Received request for plate: {request.plate} from user: {current_user.get('user_id')}"
    )

    try:
        sinesp_data = await sinesp_service.get_vehicle_data(request.plate)
        logger.info(f"Successfully fetched data for plate: {request.plate}")
        return SinespResponse(
            status_code=status.HTTP_200_OK, message="Success", data=sinesp_data
        )
    except InvalidPlateError as exc:
        logger.warning(f"Invalid plate format for {request.plate}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato de placa inválido: {exc}",
        )
    except SinespAPIError as exc:
        logger.error(
            f"Sinesp API error for plate {request.plate}: {exc.status_code} - {exc.response_text}"
        )
        raise HTTPException(
            status_code=exc.status_code
            if exc.status_code
            else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro na API do SINESP: {exc.message}",
        )
    except Exception as exc:
        logger.error(f"Internal server error for plate {request.plate}: {str(exc)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno inesperado: {str(exc)}",
        )
