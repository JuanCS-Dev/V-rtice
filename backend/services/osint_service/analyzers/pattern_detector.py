"""
Pattern Detector - Detecção de padrões comportamentais
Análise temporal e correlação de dados OSINT
Projeto Vértice - SSP-GO
"""

import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, Counter
import asyncio
import logging
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class PatternDetector:
    """Detecta padrões comportamentais em dados OSINT"""
    
    def __init__(self):
        self.patterns_db = {}
        self.behavioral_models = {}
        self.anomaly_thresholds = {
            "activity_spike": 3.0,  # Desvios padrão
            "new_connections": 5,    # Novas conexões suspeitas
            "location_change": 100,  # km de distância
            "time_pattern_break": 0.7  # Correlação mínima
        }
        
    async def analyze_patterns(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Análise principal de padrões"""
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "patterns_found": [],
            "anomalies": [],
            "risk_indicators": [],
            "behavioral_profile": {},
            "predictions": {},
            "correlation_matrix": {}
        }
        
        # Análises paralelas
        tasks = [
            self._detect_temporal_patterns(data),
            self._detect_social_patterns(data),
            self._detect_location_patterns(data),
            self._detect_communication_patterns(data),
            self._detect_financial_patterns(data),
            self._detect_behavioral_anomalies(data)
        ]
        
        pattern_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for i, result in enumerate(pattern_results):
            if isinstance(result, dict):
                if i == 0:  # Temporal
                    results["patterns_found"].extend(result.get("patterns", []))
                    results["behavioral_profile"]["temporal"] = result
                elif i == 1:  # Social
                    results["behavioral_profile"]["social"] = result
                elif i == 2:  # Location
                    results["behavioral_profile"]["location"] = result
                elif i == 3:  # Communication
                    results["behavioral_profile"]["communication"] = result
                elif i == 4:  # Financial
                    results["risk_indicators"].extend(result.get("risks", []))
                elif i == 5:  # Anomalies
                    results["anomalies"] = result.get("anomalies", [])
        
        # Correlação entre padrões
        results["correlation_matrix"] = self._calculate_correlations(results)
        
        # Predições baseadas em padrões
        results["predictions"] = self._generate_predictions(results)
        
        # Score de risco final
        results["risk_score"] = self._calculate_risk_score(results)
        
        return results
    
    async def _detect_temporal_patterns(self, data: Dict) -> Dict:
        """Detecta padrões temporais de atividade"""
        
        patterns = {
            "patterns": [],
            "activity_hours": [],
            "peak_days": [],
            "frequency": "unknown",
            "regularity_score": 0
        }
        
        # Extrair timestamps de todas as atividades
        timestamps = []
        
        # De posts sociais
        if "social_posts" in data:
            for post in data.get("social_posts", []):
                if post.get("timestamp"):
                    timestamps.append(datetime.fromisoformat(post["timestamp"]))
        
        # De emails
        if "emails" in data:
            for email in data.get("emails", []):
                if email.get("sent_date"):
                    timestamps.append(datetime.fromisoformat(email["sent_date"]))
        
        if not timestamps:
            return patterns
        
        # Análise de horários
        hours = [ts.hour for ts in timestamps]
        hour_counts = Counter(hours)
        
        # Horários de pico (top 3)
        peak_hours = [h for h, _ in hour_counts.most_common(3)]
        patterns["activity_hours"] = peak_hours
        
        # Análise de dias da semana
        weekdays = [ts.weekday() for ts in timestamps]
        day_counts = Counter(weekdays)
        
        peak_days = [d for d, _ in day_counts.most_common(3)]
        patterns["peak_days"] = self._weekday_names(peak_days)
        
        # Detectar periodicidade
        if len(timestamps) > 10:
            intervals = []
            sorted_ts = sorted(timestamps)
            for i in range(1, len(sorted_ts)):
                interval = (sorted_ts[i] - sorted_ts[i-1]).total_seconds() / 3600
                intervals.append(interval)
            
            # Calcular regularidade
            if intervals:
                mean_interval = np.mean(intervals)
                std_interval = np.std(intervals)
                
                if std_interval < mean_interval * 0.3:
                    patterns["frequency"] = "highly_regular"
                    patterns["regularity_score"] = 0.9
                elif std_interval < mean_interval * 0.6:
                    patterns["frequency"] = "regular"
                    patterns["regularity_score"] = 0.6
                else:
                    patterns["frequency"] = "irregular"
                    patterns["regularity_score"] = 0.3
                
                # Detectar padrões específicos
                if mean_interval < 1:
                    patterns["patterns"].append({
                        "type": "high_frequency",
                        "description": "Atividade muito frequente",
                        "risk_level": "medium"
                    })
                elif mean_interval > 168:  # Mais de uma semana
                    patterns["patterns"].append({
                        "type": "low_frequency",
                        "description": "Atividade esporádica",
                        "risk_level": "low"
                    })
                    
                # Detectar atividade noturna
                night_hours = [h for h in hours if h < 6 or h > 22]
                if len(night_hours) > len(hours) * 0.3:
                    patterns["patterns"].append({
                        "type": "nocturnal",
                        "description": "Alta atividade noturna",
                        "risk_level": "medium"
                    })
        
        return patterns
    
    async def _detect_social_patterns(self, data: Dict) -> Dict:
        """Detecta padrões em redes sociais"""
        
        social_patterns = {
            "network_size": 0,
            "interaction_rate": 0,
            "influence_score": 0,
            "community_clusters": [],
            "key_connections": [],
            "behavioral_type": "unknown"
        }
        
        # Analisar conexões
        connections = set()
        interactions = []
        
        for platform in data.get("social_profiles", []):
            if platform.get("followers"):
                social_patterns["network_size"] += platform["followers"]
            
            if platform.get("connections"):
                for conn in platform["connections"]:
                    connections.add(conn.get("id", conn.get("username")))
                    
            if platform.get("interactions"):
                interactions.extend(platform["interactions"])
        
        # Calcular taxa de interação
        if social_patterns["network_size"] > 0 and interactions:
            social_patterns["interaction_rate"] = len(interactions) / social_patterns["network_size"]
        
        # Detectar clusters de comunidade usando DBSCAN
        if len(connections) > 10:
            # Simular features para clustering (em produção, usar dados reais)
            features = np.random.rand(len(connections), 2)
            
            clustering = DBSCAN(eps=0.3, min_samples=2)
            clusters = clustering.fit_predict(features)
            
            unique_clusters = set(clusters)
            social_patterns["community_clusters"] = [
                {"cluster_id": int(c), "size": int(np.sum(clusters == c))}
                for c in unique_clusters if c != -1
            ]
        
        # Classificar tipo comportamental
        if social_patterns["network_size"] > 10000:
            social_patterns["behavioral_type"] = "influencer"
            social_patterns["influence_score"] = min(100, social_patterns["network_size"] / 1000)
        elif social_patterns["network_size"] > 1000:
            social_patterns["behavioral_type"] = "active_user"
            social_patterns["influence_score"] = min(50, social_patterns["network_size"] / 100)
        elif social_patterns["interaction_rate"] > 0.1:
            social_patterns["behavioral_type"] = "engaged_user"
            social_patterns["influence_score"] = 25
        else:
            social_patterns["behavioral_type"] = "passive_observer"
            social_patterns["influence_score"] = 10
        
        return social_patterns
    
    async def _detect_location_patterns(self, data: Dict) -> Dict:
        """Detecta padrões de localização"""
        
        location_patterns = {
            "locations": [],
            "movement_pattern": "stationary",
            "travel_frequency": 0,
            "risk_locations": [],
            "geofence_violations": []
        }
        
        locations = []
        
        # Extrair localizações de diferentes fontes
        for source in ["images", "posts", "check_ins"]:
            if source in data:
                for item in data[source]:
                    if "location" in item or "gps" in item:
                        loc = item.get("location", item.get("gps"))
                        if loc:
                            locations.append({
                                "lat": loc.get("latitude", loc.get("lat")),
                                "lng": loc.get("longitude", loc.get("lng")),
                                "timestamp": item.get("timestamp"),
                                "source": source
                            })
        
        if not locations:
            return location_patterns
        
        location_patterns["locations"] = locations[:10]  # Primeiras 10
        
        # Calcular distâncias entre localizações
        if len(locations) > 1:
            distances = []
            for i in range(1, len(locations)):
                dist = self._calculate_distance(
                    locations[i-1]["lat"], locations[i-1]["lng"],
                    locations[i]["lat"], locations[i]["lng"]
                )
                distances.append(dist)
            
            avg_distance = np.mean(distances)
            
            # Classificar padrão de movimento
            if avg_distance < 1:
                location_patterns["movement_pattern"] = "stationary"
            elif avg_distance < 10:
                location_patterns["movement_pattern"] = "local"
            elif avg_distance < 50:
                location_patterns["movement_pattern"] = "regional"
            else:
                location_patterns["movement_pattern"] = "traveler"
                location_patterns["travel_frequency"] = len([d for d in distances if d > 50])
        
        # Detectar localizações de risco (exemplo simplificado)
        risk_zones = [
            {"lat": -16.6799, "lng": -49.255, "radius": 5, "name": "Zona de Risco A"},
            {"lat": -16.7000, "lng": -49.300, "radius": 3, "name": "Zona de Risco B"}
        ]
        
        for loc in locations:
            for zone in risk_zones:
                dist = self._calculate_distance(
                    loc["lat"], loc["lng"],
                    zone["lat"], zone["lng"]
                )
                if dist <= zone["radius"]:
                    location_patterns["risk_locations"].append({
                        "location": loc,
                        "zone": zone["name"],
                        "timestamp": loc.get("timestamp")
                    })
        
        return location_patterns
    
    async def _detect_communication_patterns(self, data: Dict) -> Dict:
        """Detecta padrões de comunicação"""
        
        comm_patterns = {
            "preferred_channels": [],
            "communication_style": "unknown",
            "response_time": "unknown",
            "language_patterns": [],
            "suspicious_keywords": []
        }
        
        # Analisar canais preferidos
        channels = defaultdict(int)
        
        if "emails" in data:
            channels["email"] = len(data["emails"])
        if "phone_calls" in data:
            channels["phone"] = len(data["phone_calls"])
        if "messages" in data:
            for msg in data["messages"]:
                channels[msg.get("platform", "unknown")] += 1
        
        # Top 3 canais
        comm_patterns["preferred_channels"] = [
            ch for ch, _ in sorted(channels.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        
        # Analisar estilo de comunicação
        all_text = []
        
        for source in ["emails", "messages", "posts"]:
            if source in data:
                for item in data[source]:
                    if "content" in item or "text" in item:
                        all_text.append(item.get("content", item.get("text", "")))
        
        if all_text:
            combined_text = " ".join(all_text).lower()
            
            # Detectar padrões linguísticos
            patterns = {
                "formal": len(re.findall(r'\b(senhor|senhora|atenciosamente|cordialmente)\b', combined_text)),
                "informal": len(re.findall(r'\b(oi|olá|vlw|blz|tmj)\b', combined_text)),
                "technical": len(re.findall(r'\b(sistema|código|database|api|bug)\b', combined_text)),
                "emotional": len(re.findall(r'[!?]{2,}|[😀-🙏]', combined_text))
            }
            
            # Determinar estilo dominante
            dominant_style = max(patterns.items(), key=lambda x: x[1])
            if dominant_style[1] > 0:
                comm_patterns["communication_style"] = dominant_style[0]
            
            # Detectar palavras-chave suspeitas
            suspicious = [
                "urgente", "segredo", "confidencial", "dinheiro", 
                "transferência", "bitcoin", "senha", "vazamento"
            ]
            
            for word in suspicious:
                if word in combined_text:
                    count = combined_text.count(word)
                    comm_patterns["suspicious_keywords"].append({
                        "keyword": word,
                        "frequency": count,
                        "risk_level": "high" if count > 3 else "medium"
                    })
        
        return comm_patterns
    
    async def _detect_financial_patterns(self, data: Dict) -> Dict:
        """Detecta padrões financeiros suspeitos"""
        
        financial_patterns = {
            "risks": [],
            "transaction_patterns": [],
            "crypto_activity": False,
            "money_mentions": 0
        }
        
        # Buscar menções financeiras
        financial_keywords = [
            r'\$\s*[\d,]+', r'R\$\s*[\d,]+', r'€\s*[\d,]+',
            r'\b(bitcoin|btc|ethereum|eth|crypto|blockchain)\b',
            r'\b(paypal|pix|transferência|depósito|saque)\b',
            r'\b(conta|banco|agência|swift)\b'
        ]
        
        text_sources = []
        for source in ["emails", "messages", "posts"]:
            if source in data:
                for item in data[source]:
                    text_sources.append(item.get("content", item.get("text", "")))
        
        combined_text = " ".join(text_sources).lower()
        
        for pattern in financial_keywords:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            if matches:
                financial_patterns["money_mentions"] += len(matches)
                
                if "bitcoin" in pattern or "crypto" in pattern:
                    financial_patterns["crypto_activity"] = True
                    financial_patterns["risks"].append({
                        "type": "crypto_activity",
                        "description": "Atividade com criptomoedas detectada",
                        "severity": "medium",
                        "evidence": matches[:3]  # Primeiras 3 evidências
                    })
        
        # Detectar padrões de transação suspeitos
        if financial_patterns["money_mentions"] > 10:
            financial_patterns["risks"].append({
                "type": "high_financial_activity",
                "description": "Alta frequência de menções financeiras",
                "severity": "high",
                "count": financial_patterns["money_mentions"]
            })
        
        return financial_patterns
    
    async def _detect_behavioral_anomalies(self, data: Dict) -> Dict:
        """Detecta anomalias comportamentais"""
        
        anomalies = {
            "anomalies": [],
            "risk_level": "low",
            "confidence": 0
        }
        
        # Verificar mudanças súbitas de padrão
        if "activity_history" in data:
            history = data["activity_history"]
            
            # Detectar spikes de atividade
            if len(history) > 7:
                recent = history[-7:]  # Última semana
                older = history[:-7]
                
                if older:
                    recent_avg = np.mean([h.get("count", 0) for h in recent])
                    older_avg = np.mean([h.get("count", 0) for h in older])
                    
                    if recent_avg > older_avg * 3:
                        anomalies["anomalies"].append({
                            "type": "activity_spike",
                            "description": "Aumento súbito de atividade",
                            "factor": recent_avg / max(older_avg, 1),
                            "severity": "high"
                        })
        
        # Verificar horários anormais
        if "timestamps" in data:
            night_activity = [
                ts for ts in data["timestamps"]
                if datetime.fromisoformat(ts).hour < 5 or datetime.fromisoformat(ts).hour > 23
            ]
            
            if len(night_activity) > len(data["timestamps"]) * 0.5:
                anomalies["anomalies"].append({
                    "type": "abnormal_hours",
                    "description": "Atividade predominantemente noturna",
                    "percentage": len(night_activity) / len(data["timestamps"]) * 100,
                    "severity": "medium"
                })
        
        # Calcular nível de risco geral
        if anomalies["anomalies"]:
            severities = [a["severity"] for a in anomalies["anomalies"]]
            if "high" in severities:
                anomalies["risk_level"] = "high"
                anomalies["confidence"] = 0.8
            elif "medium" in severities:
                anomalies["risk_level"] = "medium"
                anomalies["confidence"] = 0.6
            else:
                anomalies["risk_level"] = "low"
                anomalies["confidence"] = 0.4
        
        return anomalies
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcula distância entre coordenadas (km)"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Raio da Terra em km
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def _weekday_names(self, days: List[int]) -> List[str]:
        """Converte números de dias da semana para nomes"""
        names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        return [names[d] for d in days if 0 <= d < 7]
    
    def _calculate_correlations(self, results: Dict) -> Dict:
        """Calcula correlações entre diferentes padrões"""
        
        correlations = {}
        
        # Correlação temporal-social
        if "temporal" in results.get("behavioral_profile", {}) and \
           "social" in results.get("behavioral_profile", {}):
            
            temporal = results["behavioral_profile"]["temporal"]
            social = results["behavioral_profile"]["social"]
            
            # Se alta atividade noturna E muitas conexões
            if temporal.get("frequency") == "highly_regular" and \
               social.get("network_size", 0) > 1000:
                correlations["temporal_social"] = {
                    "correlation": "high",
                    "description": "Alta atividade regular com grande rede social",
                    "risk_implication": "Possível bot ou conta automatizada"
                }
        
        # Correlação localização-comunicação
        if "location" in results.get("behavioral_profile", {}) and \
           "communication" in results.get("behavioral_profile", {}):
            
            location = results["behavioral_profile"]["location"]
            comm = results["behavioral_profile"]["communication"]
            
            if location.get("movement_pattern") == "traveler" and \
               "crypto" in str(comm.get("suspicious_keywords", [])):
                correlations["location_communication"] = {
                    "correlation": "high",
                    "description": "Viajante frequente com atividade crypto",
                    "risk_implication": "Possível atividade financeira suspeita"
                }
        
        return correlations
    
    def _generate_predictions(self, results: Dict) -> Dict:
        """Gera predições baseadas nos padrões detectados"""
        
        predictions = {
            "next_activity": "unknown",
            "risk_evolution": "stable",
            "recommendations": []
        }
        
        # Predizer próxima atividade
        if "behavioral_profile" in results:
            temporal = results["behavioral_profile"].get("temporal", {})
            
            if temporal.get("activity_hours"):
                next_hour = temporal["activity_hours"][0]
                predictions["next_activity"] = f"Provável atividade às {next_hour}:00"
            
            if temporal.get("peak_days"):
                predictions["peak_days"] = temporal["peak_days"]
        
        # Predizer evolução de risco
        if len(results.get("anomalies", [])) > 2:
            predictions["risk_evolution"] = "increasing"
            predictions["recommendations"].append("Monitoramento contínuo recomendado")
        elif len(results.get("risk_indicators", [])) > 0:
            predictions["risk_evolution"] = "attention_required"
            predictions["recommendations"].append("Verificação adicional sugerida")
        
        return predictions
    
    def _calculate_risk_score(self, results: Dict) -> Dict:
        """Calcula score de risco final"""
        
        score = 0
        factors = []
        
        # Anomalias
        anomalies = results.get("anomalies", [])
        score += len(anomalies) * 15
        if anomalies:
            factors.append(f"{len(anomalies)} anomalias detectadas")
        
        # Indicadores de risco
        risk_indicators = results.get("risk_indicators", [])
        score += len(risk_indicators) * 10
        if risk_indicators:
            factors.append(f"{len(risk_indicators)} indicadores de risco")
        
        # Palavras suspeitas
        if "behavioral_profile" in results:
            comm = results["behavioral_profile"].get("communication", {})
            suspicious = comm.get("suspicious_keywords", [])
            if suspicious:
                score += len(suspicious) * 5
                factors.append(f"{len(suspicious)} palavras-chave suspeitas")
        
        # Normalizar score (0-100)
        score = min(100, score)
        
        # Classificar nível
        if score >= 70:
            level = "CRITICAL"
        elif score >= 50:
            level = "HIGH"
        elif score >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        return {
            "score": score,
            "level": level,
            "factors": factors,
            "recommendation": self._get_risk_recommendation(level)
        }
    
    def _get_risk_recommendation(self, level: str) -> str:
        """Retorna recomendação baseada no nível de risco"""
        
        recommendations = {
            "CRITICAL": "Ação imediata requerida. Escalar para equipe de segurança.",
            "HIGH": "Investigação prioritária necessária. Monitoramento contínuo.",
            "MEDIUM": "Acompanhamento regular recomendado. Verificar anomalias.",
            "LOW": "Situação normal. Manter monitoramento padrão."
        }
        
        return recommendations.get(level, "Continuar monitoramento padrão.")
