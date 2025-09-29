# /home/juan/vertice-dev/backend/services/aurora_predict/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AuroraPredict Service",
    description="Motor de IA do Vértice - Análises preditivas com lógica de risco híbrida.",
    version="2.0.0", # Version bump para lógica de risco com Severidade e Decaimento Temporal
)

# === LÓGICA DE RISCO (VALIDADA NO SANDBOX) ===

# Tabela de Severidade - Ajustada para Anápolis, Set/2025
SEVERITY_WEIGHTS = {
    "homicidio": 100, "latrocinio": 100, "tentativa_homicidio": 85,
    "trafico_drogas": 90,
    "roubo_carga": 60, "roubo_residencia": 55, "roubo_transeunte": 50,
    "roubo_veiculo": 40,
    "furto_residencia": 25, "furto_veiculo": 15,
    "desordem": 10, "unknown": 5,
}

def calculate_decay_weight(timestamp_str: Optional[str], half_life_days: int = 7) -> float:
    """
    Calcula um peso de decaimento exponencial com base na idade de um evento.
    """
    if not timestamp_str:
        return 0.1 # Retorna um peso baixo para dados sem data

    try:
        # Garante que o timestamp seja timezone-aware (UTC) para comparações corretas
        event_time = datetime.fromisoformat(str(timestamp_str)).replace(tzinfo=timezone.utc if pd.isna(getattr(timestamp_str, 'tzinfo', None)) else None)
        now = datetime.now(timezone.utc)
        
        age_in_days = (now - event_time).total_seconds() / (24 * 3600)
        
        if age_in_days < 0: return 1.0 # Evento no futuro, peso máximo
        
        decay_factor = 0.5 ** (age_in_days / half_life_days)
        return decay_factor
    except (ValueError, TypeError):
        logger.warning(f"Timestamp inválido encontrado: {timestamp_str}. Usando peso de decaimento baixo.")
        return 0.1


# === MODELOS DE DADOS ===

class OccurrenceInput(BaseModel):
    lat: float
    lng: float
    timestamp: Optional[datetime] = None
    tipo: Optional[str] = "unknown"

class PredictionInput(BaseModel):
    occurrences: List[OccurrenceInput]
    eps_km: Optional[float] = Field(2.5, gt=0, description="Raio de busca do cluster em quilómetros.")
    min_samples: Optional[int] = Field(3, gt=0, description="Número mínimo de pontos para formar um cluster.")

class HotspotOutput(BaseModel):
    center_lat: float
    center_lng: float
    num_points: int
    risk_level: str
    risk_score: float = Field(..., description="Score de risco final do hotspot, com decaimento temporal.")
    crime_types: List[str]

class PredictionOutput(BaseModel):
    hotspots: List[HotspotOutput]
    total_occurrences_analyzed: int
    clusters_found: int
    analysis_timestamp: datetime
    parameters_used: dict

# === ENDPOINTS ===

@app.get("/", tags=["Health"])
async def read_root():
    return {
        "status": "AuroraPredict Service Online",
        "version": "2.0.0",
        "capabilities": ["crime_hotspots", "severity_weighted_risk", "temporal_decay_risk"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/predict/crime-hotspots", response_model=PredictionOutput, tags=["Prediction"])
async def predict_crime_hotspots(data: PredictionInput):
    """
    Análise preditiva de hotspots criminais com lógica de risco baseada em
    severidade de crime e decaimento temporal.
    """
    start_time = datetime.now(timezone.utc)
    logger.info(f"Iniciando análise com {len(data.occurrences)} ocorrências.")

    if len(data.occurrences) < data.min_samples:
        return PredictionOutput(hotspots=[], total_occurrences_analyzed=len(data.occurrences), clusters_found=0, analysis_timestamp=start_time, parameters_used={})

    try:
        df = pd.DataFrame([occ.dict() for occ in data.occurrences])
        coords = df[['lat', 'lng']].values

        kms_per_radian = 6371.0088
        epsilon = data.eps_km / kms_per_radian
        parameters_used = {"eps_km": data.eps_km, "min_samples": data.min_samples}

        logger.info(f"Executando DBSCAN com parâmetros: {parameters_used}")
        coords_rad = np.radians(coords)
        db = DBSCAN(eps=epsilon, min_samples=data.min_samples, algorithm='ball_tree', metric='haversine').fit(coords_rad)
        
        cluster_labels = db.labels_
        valid_clusters = [c for c in set(cluster_labels) if c != -1]
        logger.info(f"Clusters encontrados: {len(valid_clusters)}")

        hotspots = []
        for cluster_id in valid_clusters:
            cluster_mask = cluster_labels == cluster_id
            cluster_df = df[cluster_mask]
            
            num_points = len(cluster_df)
            center_lat, center_lng = cluster_df[['lat', 'lng']].mean().values

            # --- CÁLCULO DE RISCO HÍBRIDO (SEVERIDADE + TEMPO) ---
            total_risk_score = 0
            for _, occ in cluster_df.iterrows():
                base_weight = SEVERITY_WEIGHTS.get(occ.get('tipo', 'unknown'), 5)
                decay_weight = calculate_decay_weight(occ.get('timestamp'))
                total_risk_score += base_weight * decay_weight

            if total_risk_score >= 250: risk_level = "Crítico"
            elif total_risk_score >= 120: risk_level = "Alto"
            elif total_risk_score >= 40: risk_level = "Médio"
            else: risk_level = "Baixo"

            hotspots.append(HotspotOutput(
                center_lat=center_lat,
                center_lng=center_lng,
                num_points=num_points,
                risk_level=risk_level,
                risk_score=round(total_risk_score, 2),
                crime_types=list(cluster_df['tipo'].unique())
            ))
        
        # Ordenar hotspots pelo score de risco, do maior para o menor
        hotspots.sort(key=lambda h: h.risk_score, reverse=True)

        result = PredictionOutput(
            hotspots=hotspots,
            total_occurrences_analyzed=len(df),
            clusters_found=len(hotspots),
            analysis_timestamp=datetime.now(timezone.utc),
            parameters_used=parameters_used
        )
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.info(f"Análise concluída em {duration:.2f}s: {len(hotspots)} hotspots identificados.")
        return result

    except Exception as e:
        logger.error(f"Erro fatal na análise preditiva: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro interno no serviço de IA: {str(e)}")
