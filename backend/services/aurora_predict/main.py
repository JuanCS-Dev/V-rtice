# /home/juan/vertice-dev/backend/services/aurora_predict/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AuroraPredict Service",
    description="Motor de IA do Vértice - Análises preditivas e processamento inteligente de dados criminais.",
    version="1.1.0",
)

# === MODELOS DE DADOS ===

class OccurrenceInput(BaseModel):
    """Modelo flexível para receber dados de ocorrências"""
    lat: Union[float, int]
    lng: Union[float, int]
    intensity: Optional[Union[float, int]] = 1.0  # Valor padrão se não fornecido
    timestamp: Optional[Union[datetime, str]] = None
    tipo: Optional[str] = "unknown"

class PredictionInput(BaseModel):
    """Input para análise preditiva"""
    occurrences: List[OccurrenceInput]

class HotspotOutput(BaseModel):
    """Output de hotspot preditivo"""
    lat: float
    lng: float
    center_lat: float  # Para compatibilidade com frontend
    center_lng: float  # Para compatibilidade com frontend
    num_points: int
    core_samples: int  # Novo campo
    risk_level: str
    radius_km: float

class PredictionOutput(BaseModel):
    """Output da análise preditiva"""
    hotspots: List[HotspotOutput]
    total_occurrences_analyzed: int
    clusters_found: int
    analysis_timestamp: datetime

# === ENDPOINTS ===

@app.get("/", tags=["Health"])
async def read_root():
    """Health check do serviço"""
    return {
        "status": "AuroraPredict Service Online",
        "version": "1.1.0",
        "capabilities": ["crime_hotspots", "cluster_analysis", "predictive_modeling"],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check detalhado"""
    return {
        "status": "healthy",
        "service": "aurora_predict",
        "version": "1.1.0",
        "dependencies": {
            "sklearn": "available",
            "pandas": "available", 
            "numpy": "available"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict/crime-hotspots", response_model=PredictionOutput, tags=["Prediction"])
async def predict_crime_hotspots(data: PredictionInput):
    """
    Análise preditiva de hotspots criminais usando DBSCAN.
    
    Recebe dados de ocorrências e identifica clusters geográficos
    com alto potencial de atividade criminal.
    """
    logger.info(f"Iniciando análise preditiva com {len(data.occurrences)} ocorrências")
    
    try:
        # Validação inicial
        if len(data.occurrences) < 5:
            logger.warning(f"Dados insuficientes: {len(data.occurrences)} ocorrências")
            return PredictionOutput(
                hotspots=[],
                total_occurrences_analyzed=len(data.occurrences),
                clusters_found=0,
                analysis_timestamp=datetime.now()
            )

        # Processamento dos dados
        processed_data = []
        for i, occ in enumerate(data.occurrences):
            try:
                # Converter para float e validar coordenadas
                lat = float(occ.lat)
                lng = float(occ.lng)
                intensity = float(occ.intensity) if occ.intensity else 1.0
                
                # Validar se as coordenadas estão dentro de limites razoáveis
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    processed_data.append({
                        'lat': lat,
                        'lng': lng, 
                        'intensity': intensity,
                        'tipo': occ.tipo or 'unknown'
                    })
                else:
                    logger.warning(f"Coordenadas inválidas ignoradas: lat={lat}, lng={lng}")
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Erro ao processar ocorrência {i}: {e}")
                continue

        if len(processed_data) < 5:
            logger.warning(f"Após processamento: apenas {len(processed_data)} ocorrências válidas")
            return PredictionOutput(
                hotspots=[],
                total_occurrences_analyzed=len(processed_data),
                clusters_found=0,
                analysis_timestamp=datetime.now()
            )

        # Converter para DataFrame
        df = pd.DataFrame(processed_data)
        logger.info(f"DataFrame criado com {len(df)} registros válidos")

        # Preparar coordenadas para clustering
        coords = df[['lat', 'lng']].values
        
        # Configurar DBSCAN - Parâmetros mais flexíveis
        # Raio de 2.5km para capturar clusters maiores
        kms_per_radian = 6371.0088
        epsilon = 2.5 / kms_per_radian  # ~2.5km de raio (era 1.5km)
        min_samples = 3  # Fixo em 3 (era adaptativo e alto)
        
        logger.info(f"Configuração DBSCAN: epsilon={epsilon:.6f}, min_samples={min_samples}")

        # Executar clustering
        coords_rad = np.radians(coords)
        db = DBSCAN(
            eps=epsilon, 
            min_samples=min_samples, 
            algorithm='ball_tree', 
            metric='haversine'
        ).fit(coords_rad)
        
        cluster_labels = db.labels_
        unique_clusters = set(cluster_labels)
        
        # Remover noise (-1)
        valid_clusters = [c for c in unique_clusters if c != -1]
        logger.info(f"Clusters encontrados: {len(valid_clusters)}")

        # Processar hotspots
        hotspots = []
        for cluster_id in valid_clusters:
            try:
                # Pontos do cluster
                cluster_mask = cluster_labels == cluster_id
                cluster_points = coords[cluster_mask]
                cluster_intensities = df.loc[cluster_mask, 'intensity'].values
                
                # Calcular centro ponderado pela intensidade
                weights = cluster_intensities / cluster_intensities.sum()
                center_lat = np.average(cluster_points[:, 0], weights=weights)
                center_lng = np.average(cluster_points[:, 1], weights=weights)
                
                # Calcular raio do cluster
                distances = np.sqrt(np.sum((cluster_points - [center_lat, center_lng])**2, axis=1))
                radius_km = np.max(distances) * 111.32  # Conversão graus para km aproximada
                
                # Métricas do cluster
                num_points = len(cluster_points)
                avg_intensity = np.mean(cluster_intensities)
                core_samples = len(db.core_sample_indices_[cluster_labels[db.core_sample_indices_] == cluster_id])
                
                # Determinar nível de risco
                risk_score = (num_points * 0.4) + (avg_intensity * 0.4) + (core_samples * 0.2)
                
                if risk_score >= 15:
                    risk_level = "Crítico"
                elif risk_score >= 10:
                    risk_level = "Alto"
                elif risk_score >= 5:
                    risk_level = "Médio"
                else:
                    risk_level = "Baixo"
                
                hotspot = HotspotOutput(
                    lat=center_lat,
                    lng=center_lng,
                    center_lat=center_lat,  # Compatibilidade
                    center_lng=center_lng,  # Compatibilidade
                    num_points=num_points,
                    core_samples=core_samples,
                    risk_level=risk_level,
                    radius_km=round(radius_km, 2)
                )
                
                hotspots.append(hotspot)
                logger.info(f"Hotspot criado: {risk_level} - {num_points} ocorrências - R:{radius_km:.1f}km")
                
            except Exception as e:
                logger.error(f"Erro ao processar cluster {cluster_id}: {e}")
                continue

        # Ordenar por nível de risco
        risk_order = {"Crítico": 4, "Alto": 3, "Médio": 2, "Baixo": 1}
        hotspots.sort(key=lambda h: risk_order.get(h.risk_level, 0), reverse=True)

        result = PredictionOutput(
            hotspots=hotspots,
            total_occurrences_analyzed=len(processed_data),
            clusters_found=len(hotspots),
            analysis_timestamp=datetime.now()
        )
        
        logger.info(f"Análise concluída: {len(hotspots)} hotspots identificados")
        return result

    except Exception as e:
        logger.error(f"Erro na análise preditiva: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno na análise preditiva: {str(e)}"
        )

@app.get("/stats", tags=["Analytics"])
async def get_service_stats():
    """Estatísticas do serviço"""
    return {
        "service": "aurora_predict",
        "algorithms": {
            "clustering": "DBSCAN",
            "distance_metric": "haversine",
            "optimization": "ball_tree"
        },
        "parameters": {
            "default_radius_km": 1.5,
            "min_samples_adaptive": True,
            "risk_calculation": "weighted"
        },
        "performance": {
            "typical_processing_time": "< 5 seconds",
            "max_supported_points": 10000,
            "memory_efficient": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
