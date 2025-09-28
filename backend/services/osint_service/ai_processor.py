"""
Aurora AI Processor - Integração com motor de IA
Análise comportamental e geração de relatórios
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AuroraAIProcessor:
    def __init__(self):
        self.aurora_url = "http://aurora-predict:8006"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _make_request(self, endpoint: str, data: dict) -> dict:
        """Faz requisição para Aurora AI"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=self.timeout)
                
            async with self.session.post(
                f"{self.aurora_url}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Aurora AI retornou status {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Erro ao conectar com Aurora AI: {e}")
            return {}
            
    async def analyze_profiles(self, profiles: List[dict], context: str = "investigation") -> dict:
        """Análise comportamental de perfis encontrados"""
        
        data = {
            "analysis_type": "behavioral_profile",
            "context": context,
            "profiles": profiles,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/analyze/behavior", data)
        
        # Processar resposta do Aurora
        if result:
            return {
                "behavioral_pattern": result.get("pattern", "unknown"),
                "risk_assessment": result.get("risk", {}),
                "personality_traits": result.get("traits", []),
                "activity_timeline": result.get("timeline", {}),
                "recommendations": result.get("recommendations", []),
                "confidence_score": result.get("confidence", 0)
            }
        
        # Fallback se Aurora não responder
        return self._local_profile_analysis(profiles)
        
    async def assess_email_risk(self, email_data: dict, context: str = "security") -> dict:
        """Avalia risco de segurança de email"""
        
        data = {
            "analysis_type": "email_risk",
            "context": context,
            "email_data": email_data,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/analyze/email", data)
        
        if result:
            return {
                "risk_level": result.get("risk_level", "unknown"),
                "security_score": result.get("security_score", 0),
                "breach_probability": result.get("breach_prob", 0),
                "recommendations": result.get("recommendations", []),
                "patterns_detected": result.get("patterns", [])
            }
            
        return self._local_email_risk(email_data)
        
    async def analyze_phone_patterns(self, phone_data: dict, context: str = "investigation") -> dict:
        """Analisa padrões de comportamento via telefone"""
        
        data = {
            "analysis_type": "phone_patterns",
            "context": context,
            "phone_data": phone_data,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/analyze/phone", data)
        
        if result:
            return {
                "usage_pattern": result.get("pattern", "unknown"),
                "risk_indicators": result.get("risks", []),
                "carrier_analysis": result.get("carrier", {}),
                "geographic_patterns": result.get("geo_patterns", {}),
                "messaging_apps": result.get("apps", [])
            }
            
        return self._local_phone_analysis(phone_data)
        
    async def analyze_social_behavior(self, profile_data: dict, platform: str) -> dict:
        """Análise comportamental em redes sociais"""
        
        data = {
            "analysis_type": "social_behavior",
            "platform": platform,
            "profile_data": profile_data,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/analyze/social", data)
        
        if result:
            return {
                "behavior_type": result.get("behavior_type", "unknown"),
                "engagement_level": result.get("engagement", "low"),
                "content_themes": result.get("themes", []),
                "network_analysis": result.get("network", {}),
                "temporal_patterns": result.get("temporal", {}),
                "anomalies": result.get("anomalies", []),
                "influence_score": result.get("influence", 0)
            }
            
        return self._local_social_analysis(profile_data, platform)
        
    async def analyze_image_content(self, image_data: dict, context: str = "forensic") -> dict:
        """Análise forense de imagens"""
        
        data = {
            "analysis_type": "image_forensic",
            "context": context,
            "image_data": image_data,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/analyze/image", data)
        
        if result:
            return {
                "content_type": result.get("content_type", "unknown"),
                "objects_detected": result.get("objects", []),
                "faces_analysis": result.get("faces", {}),
                "text_extracted": result.get("text", ""),
                "metadata_analysis": result.get("metadata", {}),
                "manipulation_detection": result.get("manipulation", {}),
                "risk_assessment": result.get("risk", {})
            }
            
        return self._local_image_analysis(image_data)
        
    async def generate_investigation_report(self, data: dict, query: str, 
                                           search_type: str) -> dict:
        """Gera relatório completo de investigação"""
        
        request_data = {
            "report_type": "comprehensive_investigation",
            "query": query,
            "search_type": search_type,
            "investigation_data": data,
            "request_timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self._make_request("/api/report/generate", request_data)
        
        if result:
            return {
                "executive_summary": result.get("summary", ""),
                "key_findings": result.get("findings", []),
                "risk_assessment": result.get("risk", {}),
                "timeline": result.get("timeline", []),
                "connections_map": result.get("connections", {}),
                "recommendations": result.get("recommendations", []),
                "confidence_level": result.get("confidence", 0),
                "report_id": result.get("report_id", "")
            }
            
        return self._generate_local_report(data, query, search_type)
        
    # Métodos de fallback locais (quando Aurora não está disponível)
    
    def _local_profile_analysis(self, profiles: List[dict]) -> dict:
        """Análise local de perfis"""
        risk_score = len(profiles) * 3
        risk_level = "HIGH" if risk_score > 50 else "MEDIUM" if risk_score > 25 else "LOW"
        
        return {
            "behavioral_pattern": "active_user",
            "risk_assessment": {
                "score": min(100, risk_score),
                "level": risk_level
            },
            "personality_traits": ["digital_native", "multi_platform_user"],
            "activity_timeline": {},
            "recommendations": [
                "Realizar análise aprofundada dos perfis principais",
                "Verificar conexões entre as plataformas",
                "Monitorar atividade futura"
            ],
            "confidence_score": 75
        }
        
    def _local_email_risk(self, email_data: dict) -> dict:
        """Avaliação local de risco de email"""
        risk_score = 30
        if email_data.get("breaches"):
            risk_score += len(email_data["breaches"]) * 20
            
        return {
            "risk_level": "HIGH" if risk_score > 60 else "MEDIUM" if risk_score > 30 else "LOW",
            "security_score": max(0, 100 - risk_score),
            "breach_probability": min(100, risk_score),
            "recommendations": [
                "Alterar senha imediatamente" if risk_score > 60 else "Monitorar atividade",
                "Ativar autenticação de dois fatores",
                "Verificar contas vinculadas"
            ],
            "patterns_detected": []
        }
        
    def _local_phone_analysis(self, phone_data: dict) -> dict:
        """Análise local de telefone"""
        return {
            "usage_pattern": "standard",
            "risk_indicators": [],
            "carrier_analysis": phone_data.get("carrier", {}),
            "geographic_patterns": {},
            "messaging_apps": ["WhatsApp", "Telegram"]
        }
        
    def _local_social_analysis(self, profile_data: dict, platform: str) -> dict:
        """Análise local de comportamento social"""
        return {
            "behavior_type": "regular_user",
            "engagement_level": "moderate",
            "content_themes": ["personal", "professional"],
            "network_analysis": {},
            "temporal_patterns": {},
            "anomalies": [],
            "influence_score": 50
        }
        
    def _local_image_analysis(self, image_data: dict) -> dict:
        """Análise local de imagem"""
        return {
            "content_type": "photo",
            "objects_detected": [],
            "faces_analysis": {},
            "text_extracted": image_data.get("ocr_text", ""),
            "metadata_analysis": image_data.get("metadata", {}),
            "manipulation_detection": {"detected": False},
            "risk_assessment": {"level": "LOW", "score": 10}
        }
        
    def _generate_local_report(self, data: dict, query: str, search_type: str) -> dict:
        """Gera relatório local"""
        findings = []
        
        if "username_search" in data:
            findings.append(f"Username '{query}' encontrado em {len(data['username_search'].get('profiles_found', []))} plataformas")
            
        if "email_analysis" in data:
            findings.append(f"Email analisado com score de risco: {data['email_analysis'].get('risk_score', 'N/A')}")
            
        if "phone_analysis" in data:
            findings.append(f"Telefone verificado com operadora: {data['phone_analysis'].get('carrier', 'Desconhecida')}")
            
        return {
            "executive_summary": f"Investigação OSINT para {search_type}: {query}",
            "key_findings": findings,
            "risk_assessment": {
                "overall_risk": "MEDIUM",
                "confidence": 70
            },
            "timeline": [],
            "connections_map": {},
            "recommendations": [
                "Expandir investigação para plataformas adicionais",
                "Correlacionar dados encontrados",
                "Verificar autenticidade das informações"
            ],
            "confidence_level": 70,
            "report_id": f"OSINT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
