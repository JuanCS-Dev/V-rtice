# Path: backend/services/sinesp_service/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import random
from datetime import datetime, timedelta

app = FastAPI(
    title="SINESP Service (Simulator)",
    description="Microsserviço que simula a consulta de placas e fornece dados para o heatmap.",
    version="2.6.0", # Version bump para resposta de dados enriquecida
)

# --- NOVO: Modelo Pydantic para Ocorrências ---
# Define a estrutura de dados de forma explícita
class Ocorrencia(BaseModel):
    lat: float
    lng: float
    intensity: float
    timestamp: datetime
    tipo: str

# --- Dados Simulados ---
mock_database = { # ... (sem alterações) ...
    "ABC1234": { "placa": "ABC1234", "modelo": "GOL 1.6", "marca": "VOLKSWAGEN", "cor": "BRANCO", "ano": "2018", "anoModelo": "2019", "chassi": "ABC123***********123", "situacao": "ROUBO/FURTO", "municipio": "GOIÂNIA", "uf": "GO", },
    "XYZ9876": { "placa": "XYZ9876", "modelo": "ONIX 1.0T", "marca": "CHEVROLET", "cor": "PRATA", "ano": "2021", "anoModelo": "2021", "chassi": "XYZ987***********987", "situacao": "CIRCULAÇÃO", "municipio": "APARECIDA DE GOIÂNIA", "uf": "GO", }
}

def generate_ocorrencias(placa, situacao): # ... (sem alterações) ...
    ocorrencias = []
    if situacao == "ROUBO/FURTO":
        ocorrencias.append({ "id": f"BO-{random.randint(1000, 9999)}", "data": (datetime.utcnow() - timedelta(days=random.randint(5, 30))).isoformat(), "tipo": "Roubo de Veículo", "local": "Av. Brasil, Setor Central, Goiânia - GO", "status": "Em Investigação", "resumo": f"Veículo de placa {placa} foi subtraído mediante grave ameaça com arma de fogo."})
    ocorrencias.append({ "id": f"AI-{random.randint(1000, 9999)}", "data": (datetime.utcnow() - timedelta(days=random.randint(60, 120))).isoformat(), "tipo": "Averiguação de Atitude Suspeita", "local": "Rua 10, Setor Sul, Anápolis - GO", "status": "Concluído", "resumo": f"Veículo foi avistado em área conhecida por desmanche. Nenhuma irregularidade constatada na abordagem."})
    return ocorrencias
def generate_history(base_lat, base_lng): # ... (sem alterações) ...
    history = []
    now = datetime.utcnow()
    for i in range(1, 5):
        history.append({ "lat": base_lat + (random.uniform(-0.05, 0.05) * i), "lng": base_lng + (random.uniform(-0.05, 0.05) * i), "timestamp": (now - timedelta(hours=i*2)).isoformat() + "Z", "description": f"Avistamento em área {random.choice(['comercial', 'residencial', 'industrial'])}"})
    return history

TIPOS_OCORRENCIA = ["roubo", "furto", "recuperacao", "atitude_suspeita", "trafico"]

def _generate_mock_ocorrencias_database(total_points=500) -> List[Ocorrencia]:
    """Gera uma lista de ocorrências com timestamps e tipos para simular um banco de dados."""
    db = []
    now = datetime.utcnow()
    for _ in range(total_points):
        db.append(
            Ocorrencia(
                lat = -16.328 + random.uniform(-0.2, 0.2),
                lng = -48.953 + random.uniform(-0.2, 0.2),
                intensity = random.uniform(0.2, 1.0),
                timestamp = now - timedelta(days=random.randint(0, 90)),
                tipo = random.choice(TIPOS_OCORRENCIA)
            )
        )
    return db

MOCK_OCORRENCIAS_DB = _generate_mock_ocorrencias_database()

# --- MODIFICADO: Endpoint agora retorna a lista de objetos Ocorrencia completos ---
@app.get("/ocorrencias/heatmap", response_model=List[Ocorrencia], tags=["Heatmap"])
async def get_heatmap_data(
    periodo: Optional[str] = None, 
    tipo: Optional[str] = None
):
    """
    Retorna uma lista de objetos de ocorrência completos, permitindo a filtragem
    por 'periodo' e 'tipo'.
    """
    now = datetime.utcnow()
    
    # 1. Filtro temporal
    if not periodo or periodo == 'all':
        temporally_filtered_points = MOCK_OCORRENCIAS_DB
    else:
        period_map = { "24h": timedelta(days=1), "7d": timedelta(days=7), "30d": timedelta(days=30), }
        delta = period_map.get(periodo)
        if not delta:
            raise HTTPException(status_code=400, detail=f"Valor de 'periodo' inválido.")
            
        cutoff_date = now - delta
        # A comparação agora é entre objetos datetime, o que é mais seguro
        temporally_filtered_points = [ occ for occ in MOCK_OCORRENCIAS_DB if occ.timestamp >= cutoff_date ]

    # 2. Filtro de tipo
    if not tipo or tipo == 'todos':
        final_points_to_return = temporally_filtered_points
    else:
        if tipo not in TIPOS_OCORRENCIA:
             raise HTTPException(status_code=400, detail=f"Valor de 'tipo' inválido.")
        final_points_to_return = [ occ for occ in temporally_filtered_points if occ.tipo == tipo ]

    # Retorna a lista completa de objetos filtrados. O FastAPI irá serializá-los para JSON.
    return final_points_to_return

@app.get("/ocorrencias/tipos", tags=["Ocorrências"])
async def get_ocorrencia_tipos() -> List[str]: # ... (sem alterações) ...
    return TIPOS_OCORRENCIA

@app.get("/veiculos/{placa}", tags=["Consultas"])
async def consultar_placa_simulado(placa: str): # ... (sem alterações) ...
    placa_upper = placa.upper()
    if placa_upper == 'ERR-001': raise HTTPException(status_code=503, detail="Falha forçada de comunicação com a base de dados.")
    if placa_upper == 'NOT-FND': raise HTTPException(status_code=404, detail="Placa não encontrada na base de dados.")
    data = mock_database.get(placa_upper)
    if not data: data = { "placa": placa_upper, "modelo": "STRADA RANCH", "marca": "FIAT", "cor": "CINZA", "ano": "2023", "anoModelo": "2023", "chassi": "RND123***********456", "situacao": "CIRCULAÇÃO", "municipio": "ANÁPOLIS", "uf": "GO" }
    data["riskLevel"] = "HIGH" if data["situacao"] == "ROUBO/FURTO" else ("MEDIUM" if random.random() > 0.6 else "LOW")
    base_location = {"lat": -16.328, "lng": -48.953}
    data["lastKnownLocation"] = base_location
    data["locationHistory"] = generate_history(base_location["lat"], base_location["lng"])
    data["ocorrencias"] = generate_ocorrencias(placa_upper, data["situacao"])
    return data
