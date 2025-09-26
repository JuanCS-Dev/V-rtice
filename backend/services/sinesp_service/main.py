from fastapi import FastAPI, HTTPException
import random
from datetime import datetime, timedelta

app = FastAPI(
    title="SINESP Service (Simulator)",
    description="Microsserviço que simula a consulta de placas e fornece dados para o heatmap.",
    version="2.3.0",
)

# --- Dados Simulados (sem alterações) ---
mock_database = {
    "ABC1234": { "placa": "ABC1234", "modelo": "GOL 1.6", "marca": "VOLKSWAGEN", "cor": "BRANCO", "ano": "2018", "anoModelo": "2019", "chassi": "ABC123***********123", "situacao": "ROUBO/FURTO", "municipio": "GOIÂNIA", "uf": "GO", },
    "XYZ9876": { "placa": "XYZ9876", "modelo": "ONIX 1.0T", "marca": "CHEVROLET", "cor": "PRATA", "ano": "2021", "anoModelo": "2021", "chassi": "XYZ987***********987", "situacao": "CIRCULAÇÃO", "municipio": "APARECIDA DE GOIÂNIA", "uf": "GO", }
}
def generate_ocorrencias(placa, situacao):
    ocorrencias = []
    if situacao == "ROUBO/FURTO":
        ocorrencias.append({ "id": f"BO-{random.randint(1000, 9999)}", "data": (datetime.utcnow() - timedelta(days=random.randint(5, 30))).isoformat(), "tipo": "Roubo de Veículo", "local": "Av. Brasil, Setor Central, Goiânia - GO", "status": "Em Investigação", "resumo": f"Veículo de placa {placa} foi subtraído mediante grave ameaça com arma de fogo."})
    ocorrencias.append({ "id": f"AI-{random.randint(1000, 9999)}", "data": (datetime.utcnow() - timedelta(days=random.randint(60, 120))).isoformat(), "tipo": "Averiguação de Atitude Suspeita", "local": "Rua 10, Setor Sul, Anápolis - GO", "status": "Concluído", "resumo": f"Veículo foi avistado em área conhecida por desmanche. Nenhuma irregularidade constatada na abordagem."})
    return ocorrencias
def generate_history(base_lat, base_lng):
    history = []
    now = datetime.utcnow()
    for i in range(1, 5):
        history.append({ "lat": base_lat + (random.uniform(-0.05, 0.05) * i), "lng": base_lng + (random.uniform(-0.05, 0.05) * i), "timestamp": (now - timedelta(hours=i*2)).isoformat() + "Z", "description": f"Avistamento em área {random.choice(['comercial', 'residencial', 'industrial'])}"})
    return history

# --- NOVO ENDPOINT ---
@app.get("/ocorrencias/heatmap", tags=["Heatmap"])
async def get_heatmap_data():
    """
    Simula uma fonte de dados de ocorrências criminais para o mapa de calor.
    Retorna uma lista de pontos [latitude, longitude, intensidade].
    """
    heatmap_points = []
    # Cria uma "zona quente" principal em Anápolis
    for _ in range(150):
        lat = -16.328 + random.uniform(-0.05, 0.05)
        lng = -48.953 + random.uniform(-0.05, 0.05)
        intensity = random.uniform(0.5, 1.0)
        heatmap_points.append([lat, lng, intensity])
    # Cria alguns pontos mais dispersos
    for _ in range(50):
        lat = -16.328 + random.uniform(-0.2, 0.2)
        lng = -48.953 + random.uniform(-0.2, 0.2)
        intensity = random.uniform(0.2, 0.5)
        heatmap_points.append([lat, lng, intensity])
    return heatmap_points

# --- Endpoint de Veículos (sem alterações na lógica interna) ---
@app.get("/veiculos/{placa}", tags=["Consultas"])
async def consultar_placa_simulado(placa: str):
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
