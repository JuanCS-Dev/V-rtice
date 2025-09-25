from fastapi import FastAPI, HTTPException
import httpx
import json

app = FastAPI(
    title="VÉRTICE - Microsserviço SINESP",
    description="Serviço dedicado para consultas na API do SINESP Cidadão.",
    version="1.0.0",
)

SINESP_API_URL = "https://wdapi2.sinesp.gov.br/v2/consultar-placa"
SINESP_HEADERS = {
    "User-Agent": "SinespCidadao / 5.0.0",
    "Content-Type": "application/json; charset=utf-8",
    "Host": "wdapi2.sinesp.gov.br",
}

@app.get("/consultar/{placa}", tags=["Consulta"])
async def consultar_placa_sinesp(placa: str):
    """Consulta uma placa de veículo na base de dados do SINESP."""
    placa_formatada = placa.upper().replace("-", "")
    payload = {"latitude": -16.328, "longitude": -48.953, "placa": placa_formatada}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SINESP_API_URL, headers=SINESP_HEADERS, data=json.dumps(payload), timeout=15.0
            )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Erro na API do SINESP: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}")
