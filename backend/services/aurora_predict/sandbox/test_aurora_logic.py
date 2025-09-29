# test_aurora_logic.py - v3 com Lógica de Risco Temporal (Decay)

import json
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
from datetime import datetime, timezone

# Tabela de Severidade (sem alterações)
SEVERITY_WEIGHTS = {
    "homicidio": 100, "latrocinio": 100, "tentativa_homicidio": 85,
    "trafico_drogas": 90,
    "roubo_carga": 60, "roubo_residencia": 55, "roubo_transeunte": 50,
    "roubo_veiculo": 40,
    "furto_residencia": 25, "furto_veiculo": 15,
    "desordem": 10, "unknown": 5,
}

# --- NOVA FUNÇÃO DE DECAIMENTO TEMPORAL ---
def calculate_decay_weight(timestamp_str: str, half_life_days: int = 7) -> float:
    """
    Calcula um peso de decaimento exponencial com base na idade de um evento.
    A cada 'half_life_days', o peso do evento cai pela metade.
    """
    if not timestamp_str:
        return 0.1 # Retorna um peso baixo para dados sem data

    event_time = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    
    age_in_days = (now - event_time).total_seconds() / (24 * 3600)
    
    # Fórmula de decaimento exponencial baseada na meia-vida
    decay_factor = 0.5 ** (age_in_days / half_life_days)
    
    return decay_factor, age_in_days


def analyze_clusters(occurrences: list, eps_km: float, min_samples: int):
    print("="*80)
    print(f"INICIANDO ANÁLISE COM LÓGICA DE DECAIMENTO TEMPORAL")
    print(f"  - Raio (eps_km): {eps_km} km | Densidade Mínima: {min_samples} ocorrências")
    print(f"  - Meia-vida do Risco: 7 dias")
    print("="*80)

    df = pd.DataFrame(occurrences)
    coords = df[['lat', 'lng']].values
    
    kms_per_radian = 6371.0088
    epsilon = eps_km / kms_per_radian
    
    coords_rad = np.radians(coords)
    db = DBSCAN(eps=epsilon, min_samples=min_samples, algorithm='ball_tree', metric='haversine').fit(coords_rad)
    
    cluster_labels = db.labels_
    valid_clusters = [c for c in set(cluster_labels) if c != -1]
    
    print(f"[INFO] DBSCAN concluído. {len(valid_clusters)} clusters encontrados.")
    print("\n--- DETALHES DOS HOTSPOTS IDENTIFICADOS ---")

    for cluster_id in valid_clusters:
        cluster_mask = cluster_labels == cluster_id
        cluster_df = df[cluster_mask]
        
        num_points = len(cluster_df)
        center_lat, center_lng = cluster_df[['lat', 'lng']].mean().values

        # --- LÓGICA DE RISCO COM DECAIMENTO TEMPORAL ---
        total_risk_score = 0
        
        print(f"\n  [CLUSTER #{cluster_id}] - {num_points} Ocorrências")
        print(f"    {'Tipo':<20} | {'Idade (dias)':<12} | {'Peso Base':<10} | {'Decaimento':<12} | {'Peso Final':<10}")
        print(f"    {'-'*20} | {'-'*12} | {'-'*10} | {'-'*12} | {'-'*10}")

        for index, occ in cluster_df.iterrows():
            crime_type = occ.get('tipo', 'unknown')
            timestamp = occ.get('timestamp')
            
            base_weight = SEVERITY_WEIGHTS.get(crime_type, 5)
            decay_weight, age_days = calculate_decay_weight(timestamp, half_life_days=7)
            final_weight = base_weight * decay_weight
            
            total_risk_score += final_weight
            
            print(f"    {crime_type:<20} | {age_days:<12.1f} | {base_weight:<10} | {decay_weight:<12.4f} | {final_weight:<10.1f}")

        if total_risk_score >= 250: risk_level = "Crítico"
        elif total_risk_score >= 120: risk_level = "Alto"
        elif total_risk_score >= 40: risk_level = "Médio"
        else: risk_level = "Baixo"
        
        print(f"    ----------------------------------------------------------------------")
        print(f"    SCORE DE RISCO TOTAL (com decaimento): {total_risk_score:.2f}")
        print(f"    Nível de Risco Calculado: {risk_level}")
        print(f"    Centroide (Lat, Lng): {center_lat:.6f}, {center_lng:.6f}")

    if not valid_clusters:
        print("\nNenhum hotspot significativo foi formado com os parâmetros atuais.")
        
    print("\n--- FIM DA ANÁLISE ---")


if __name__ == "__main__":
    try:
        with open('occurrences.json', 'r') as f:
            sample_occurrences = json.load(f)
        print(f"Arquivo 'occurrences.json' carregado com sucesso. Contém {len(sample_occurrences)} registros.\n")
    except FileNotFoundError:
        print("\nERRO: O arquivo 'occurrences.json' não foi encontrado.")
        exit()

    analyze_clusters(
        occurrences=sample_occurrences, 
        eps_km=2.5,
        min_samples=3
    )
