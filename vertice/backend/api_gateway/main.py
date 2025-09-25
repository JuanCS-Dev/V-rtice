from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(
    title="Projeto VÉRTICE - API Gateway",
    version="0.1.0",
)

origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# O gateway agora aponta para o nome do serviço no Docker Compose
SINESP_SERVICE_URL = "http://sinesp_service:8000"

@app.get("/", tags=["Root"])
async def read_root():
    return {"status": "API Gateway is running!"}

@app.get("/veiculos/{placa}", tags=["SINESP"])
async def consultar_placa(placa: str):
    """Consulta uma placa de veículo através do microsserviço SINESP."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SINESP_SERVICE_URL}/consultar/{placa}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.json())
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
