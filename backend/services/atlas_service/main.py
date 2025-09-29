# /home/juan/vertice-dev/backend/services/atlas_service/main.py

import httpx
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from datetime import datetime, timezone
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Atlas Service",
    description="Serviço de enriquecimento de dados geoespaciais (GIS) do Vértice. Fornece dados sobre pontos de interesse (POIs) a partir de fontes abertas.",
    version="1.0.0",
)

# URL da API Overpass
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

# === FUNÇÃO CLIENTE DA API OVERPASS ===

async def query_overpass_api(query: str) -> dict:
    """
    Executa uma query na API Overpass e retorna o resultado em JSON.
    """
    logger.info(f"Executando query na Overpass API...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OVERPASS_API_URL, data=query)
            
            # Levanta uma exceção para erros HTTP (e.g., 4xx, 5xx)
            response.raise_for_status()
            
            logger.info(f"Query executada com sucesso. Status: {response.status_code}")
            return response.json()
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP ao consultar a API Overpass: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Erro na API Overpass: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Erro de conexão com a API Overpass: {e}")
        raise HTTPException(status_code=503, detail=f"Não foi possível conectar à API Overpass: {e}")
    except Exception as e:
        logger.error(f"Erro inesperado ao processar a query Overpass: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar a query.")


# === ENDPOINTS ===

@app.get("/", tags=["Health"])
async def read_root():
    """Health check do serviço Atlas."""
    return {
        "status": "Atlas Service Online",
        "version": "1.0.0",
        "data_source": "OpenStreetMap via Overpass API",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/query/", tags=["Overpass"])
async def execute_raw_query(query: str = Body(..., media_type="text/plain")):
    """
    Endpoint de baixo nível para executar uma query Overpass QL crua.
    Útil para testes e desenvolvimento.
    """
    return await query_overpass_api(query=query)
