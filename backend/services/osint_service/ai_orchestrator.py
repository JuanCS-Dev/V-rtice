"""
AI Orchestrator - Orquestração Inteligente OSINT
Coordena automaticamente todas as ferramentas baseado em AI
Projeto Vértice - SSP-GO
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from enum import Enum

# Importações locais
from scrapers.username_hunter import UsernameHunter
from scrapers.social_scraper import SocialScraper
from analyzers.email_analyzer import EmailAnalyzer
from analyzers.phone_analyzer import PhoneAnalyzer
from analyzers.image_analyzer import ImageAnalyzer
from pattern_detector import PatternDetector
from ai_processor import AuroraAIProcessor
from report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class InvestigationPhase(Enum):
    """Fases da investigação"""
    INITIAL = "initial_recon"
    DEEP_SCAN = "deep_scan"
    CORRELATION = "correlation"
    ANALYSIS = "analysis"
    REPORT = "report_generation"

class AIOrchestrator:
    """Orquestrador inteligente que coordena todas as ferramentas OSINT"""
    
    def __init__(self):
        # Inicializar todas as ferramentas
        self.username_hunter = UsernameHunter()
        self.social_scraper = SocialScraper()
        self.email_analyzer = EmailAnalyzer()
        self.phone_analyzer = PhoneAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self.pattern_detector = PatternDetector()
        self.aurora_ai = AuroraAIProcessor()
        self.report_generator = ReportGenerator()
        
        # Estado da investigação
        self.investigation_state = {
            "phase": InvestigationPhase.INITIAL,
            "data_collected": {},
            "tools_used": [],
            "decisions_made": [],
            "confidence_scores": {}
        }
        
    async def investigate(self, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Investigação completa automatizada usando AI
        
        Args:
            initial_data: Dados iniciais do alvo
                - username (opcional)
                - email (opcional) 
                - phone (opcional)
                - name (opcional)
                - image_url (opcional)
                - context (opcional): Contexto da investigação
        """
        
        logger.info(f"Iniciando investigação automatizada com Aurora AI")
        start_time = datetime.utcnow()
        
        # Resultado final
        final_report = {
            "investigation_id": self._generate_investigation_id(),
            "start_time": start_time.isoformat(),
            "initial_data": initial_data,
            "phases_completed": [],
            "data_collected": {},
            "patterns_found": [],
            "risk_assessment": {},
            "recommendations": [],
            "executive_summary": "",
            "detailed_report": {},
            "confidence_score": 0
        }
        
        try:
            # FASE 1: Reconhecimento Inicial
            logger.info("Fase 1: Reconhecimento inicial")
            self.investigation_state["phase"] = InvestigationPhase.INITIAL
            initial_results = await self._initial_reconnaissance(initial_data)
            final_report["data_collected"]["initial"] = initial_results
            final_report["phases_completed"].append("initial_recon")
            
            # Decisão da AI: Quais ferramentas usar baseado nos dados iniciais
            ai_decision = await self._ai_decide_next_tools(initial_results)
            self.investigation_state["decisions_made"].append(ai_decision)
            
            # FASE 2: Deep Scan baseado na decisão da AI
            logger.info("Fase 2: Deep scan inteligente")
            self.investigation_state["phase"] = InvestigationPhase.DEEP_SCAN
            
            if ai_decision.get("recommended_tools"):
                deep_results = await self._execute_deep_scan(
                    ai_decision["recommended_tools"],
                    initial_results
                )
                final_report["data_collected"]["deep_scan"] = deep_results
                final_report["phases_completed"].append("deep_scan")
            
            # FASE 3: Correlação de Dados
            logger.info("Fase 3: Correlação e enriquecimento")
            self.investigation_state["phase"] = InvestigationPhase.CORRELATION
            
            correlated_data = await self._correlate_data(
                final_report["data_collected"]
            )
            final_report["data_collected"]["correlations"] = correlated_data
            final_report["phases_completed"].append("correlation")
            
            # FASE 4: Análise de Padrões com Aurora
            logger.info("Fase 4: Análise de padrões comportamentais")
            self.investigation_state["phase"] = InvestigationPhase.ANALYSIS
            
            patterns = await self.pattern_detector.analyze_patterns(
                final_report["data_collected"]
            )
            final_report["patterns_found"] = patterns.get("patterns_found", [])
            final_report["phases_completed"].append("analysis")
            
            # FASE 5: Avaliação de Risco com AI
            logger.info("Fase 5: Avaliação de risco com Aurora AI")
            risk_assessment = await self._ai_risk_assessment(final_report)
            final_report["risk_assessment"] = risk_assessment
            
            # FASE 6: Geração de Relatório Final
            logger.info("Fase 6: Gerando relatório executivo")
            self.investigation_state["phase"] = InvestigationPhase.REPORT
            
            executive_summary = await self._generate_executive_summary(final_report)
            final_report["executive_summary"] = executive_summary
            final_report["phases_completed"].append("report")
            
            # Calcular confidence score final
            final_report["confidence_score"] = self._calculate_confidence(final_report)
            
            # Gerar recomendações baseadas em AI
            recommendations = await self._ai_recommendations(final_report)
            final_report["recommendations"] = recommendations
            
            # Tempo total de investigação
            final_report["investigation_time"] = (
                datetime.utcnow() - start_time
            ).total_seconds()
            
            logger.info(f"Investigação completa em {final_report['investigation_time']:.2f} segundos")
            
            return final_report
            
        except Exception as e:
            logger.error(f"Erro na investigação automatizada: {e}")
            final_report["error"] = str(e)
            final_report["phases_completed"].append("error")
            return final_report
    
    async def _initial_reconnaissance(self, initial_data: Dict) -> Dict:
        """Fase 1: Reconhecimento inicial básico"""
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_found": {}
        }
        
        tasks = []
        
        # Username search
        if initial_data.get("username"):
            logger.info(f"Buscando username: {initial_data['username']}")
            tasks.append(self.username_hunter.hunt(
                initial_data["username"],
                platforms="all",
                deep_search=False
            ))
            
        # Email analysis
        if initial_data.get("email"):
            logger.info(f"Analisando email: {initial_data['email']}")
            tasks.append(self.email_analyzer.analyze(
                initial_data["email"],
                check_breaches=True,
                check_social=True
            ))
            
        # Phone analysis
        if initial_data.get("phone"):
            logger.info(f"Analisando telefone: {initial_data['phone']}")
            tasks.append(self.phone_analyzer.analyze(
                initial_data["phone"],
                include_carrier=True,
                include_location=True
            ))
            
        # Executar tarefas em paralelo
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Processar resultados
            for i, result in enumerate(task_results):
                if not isinstance(result, Exception):
                    if i == 0 and initial_data.get("username"):
                        results["data_found"]["username_search"] = result
                    elif initial_data.get("email"):
                        results["data_found"]["email_analysis"] = result
                    elif initial_data.get("phone"):
                        results["data_found"]["phone_analysis"] = result
                        
        return results
    
    async def _ai_decide_next_tools(self, initial_results: Dict) -> Dict:
        """AI decide quais ferramentas usar baseado nos resultados iniciais"""
        
        decision = {
            "timestamp": datetime.utcnow().isoformat(),
            "recommended_tools": [],
            "reasoning": [],
            "priority": "medium"
        }
        
        # Analisar resultados iniciais
        data_quality = self._assess_data_quality(initial_results)
        
        # Decisões baseadas em lógica + Aurora AI
        if data_quality["has_social_profiles"]:
            decision["recommended_tools"].append({
                "tool": "social_scraper",
                "targets": data_quality["social_platforms"],
                "depth": "deep"
            })
            decision["reasoning"].append("Múltiplos perfis sociais encontrados")
            
        if data_quality["has_email_breaches"]:
            decision["recommended_tools"].append({
                "tool": "breach_analyzer",
                "focus": "security"
            })
            decision["reasoning"].append("Vazamentos detectados - análise de segurança necessária")
            decision["priority"] = "high"
            
        if data_quality["has_location_data"]:
            decision["recommended_tools"].append({
                "tool": "location_tracker",
                "analysis": "movement_patterns"
            })
            decision["reasoning"].append("Dados de localização disponíveis")
            
        # Consultar Aurora AI para decisões adicionais
        aurora_suggestion = await self.aurora_ai.analyze_profiles(
            initial_results.get("data_found", {}),
            context="investigation_planning"
        )
        
        if aurora_suggestion.get("recommendations"):
            decision["ai_suggestions"] = aurora_suggestion["recommendations"]
            
        return decision
    
    async def _execute_deep_scan(self, tools: List[Dict], context: Dict) -> Dict:
        """Fase 2: Executar deep scan com as ferramentas recomendadas"""
        
        deep_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tools_executed": [],
            "data": {}
        }
        
        for tool_config in tools:
            tool_name = tool_config["tool"]
            
            try:
                if tool_name == "social_scraper":
                    # Scraping profundo de redes sociais
                    for platform in tool_config.get("targets", []):
                        if platform.get("platform") and platform.get("username"):
                            result = await self.social_scraper.scrape_profile(
                                platform["platform"],
                                platform["username"],
                                depth=tool_config.get("depth", "medium"),
                                include_connections=True,
                                include_timeline=True
                            )
                            deep_results["data"][f"{platform['platform']}_profile"] = result
                            
                elif tool_name == "breach_analyzer":
                    # Análise profunda de breaches
                    # Implementar conforme necessidade
                    pass
                    
                elif tool_name == "location_tracker":
                    # Análise de padrões de movimento
                    # Implementar conforme necessidade
                    pass
                    
                deep_results["tools_executed"].append(tool_name)
                
            except Exception as e:
                logger.error(f"Erro ao executar {tool_name}: {e}")
                deep_results["data"][f"{tool_name}_error"] = str(e)
                
        return deep_results
    
    async def _correlate_data(self, all_data: Dict) -> Dict:
        """Fase 3: Correlacionar dados de diferentes fontes"""
        
        correlations = {
            "cross_references": [],
            "identity_matches": [],
            "timeline": [],
            "network_map": {},
            "anomalies": []
        }
        
        # Extrair todos os identificadores únicos
        identifiers = {
            "usernames": set(),
            "emails": set(),
            "phones": set(),
            "names": set(),
            "locations": []
        }
        
        # Coletar identificadores de todas as fontes
        for phase, data in all_data.items():
            if isinstance(data, dict):
                # Processar usernames
                if "username_search" in str(data):
                    # Extrair usernames encontrados
                    pass
                    
                # Processar emails
                if "email" in str(data).lower():
                    # Extrair emails
                    pass
                    
        # Encontrar conexões entre diferentes plataformas
        # Construir timeline de atividades
        # Identificar anomalias
        
        return correlations
    
    async def _ai_risk_assessment(self, report_data: Dict) -> Dict:
        """Avaliação de risco usando Aurora AI"""
        
        # Preparar dados para Aurora
        risk_data = {
            "profiles_found": len(report_data.get("data_collected", {}).get("initial", {}).get("data_found", {}).get("username_search", {}).get("profiles_found", [])),
            "breaches_detected": 0,
            "suspicious_patterns": len(report_data.get("patterns_found", [])),
            "data_points": self._count_data_points(report_data)
        }
        
        # Consultar Aurora para avaliação
        risk_assessment = await self.aurora_ai.assess_email_risk(
            risk_data,
            context="comprehensive_risk"
        )
        
        # Adicionar nossa própria lógica
        risk_score = 0
        risk_factors = []
        
        if risk_data["profiles_found"] > 20:
            risk_score += 30
            risk_factors.append("Alta exposição online")
            
        if risk_data["breaches_detected"] > 0:
            risk_score += 40
            risk_factors.append("Dados comprometidos em vazamentos")
            
        if risk_data["suspicious_patterns"] > 3:
            risk_score += 30
            risk_factors.append("Padrões suspeitos detectados")
            
        return {
            "risk_score": min(100, risk_score),
            "risk_level": self._classify_risk_level(risk_score),
            "risk_factors": risk_factors,
            "ai_assessment": risk_assessment,
            "mitigation_suggestions": self._generate_mitigation_suggestions(risk_factors)
        }
    
    async def _generate_executive_summary(self, report: Dict) -> str:
        """Gerar resumo executivo usando AI"""
        
        summary_data = {
            "investigation_id": report["investigation_id"],
            "target_identifiers": report["initial_data"],
            "phases_completed": report["phases_completed"],
            "key_findings": self._extract_key_findings(report),
            "risk_level": report["risk_assessment"].get("risk_level", "Unknown"),
            "data_points_collected": self._count_data_points(report),
            "investigation_time": report.get("investigation_time", 0)
        }
        
        # Template de resumo
        summary = f"""
# Relatório Executivo - Investigação OSINT
**ID da Investigação:** {summary_data['investigation_id']}
**Data:** {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC

## Alvo da Investigação
{self._format_target_info(summary_data['target_identifiers'])}

## Resumo da Análise
- **Fases Completadas:** {', '.join(summary_data['phases_completed'])}
- **Pontos de Dados Coletados:** {summary_data['data_points_collected']}
- **Tempo de Investigação:** {summary_data['investigation_time']:.1f} segundos
- **Nível de Risco:** {summary_data['risk_level']}

## Principais Descobertas
{self._format_key_findings(summary_data['key_findings'])}

## Avaliação de Risco
{self._format_risk_assessment(report['risk_assessment'])}

## Recomendações
{self._format_recommendations(report.get('recommendations', []))}

---
*Relatório gerado automaticamente pelo Sistema Vértice - Aurora AI*
        """
        
        return summary.strip()
    
    async def _ai_recommendations(self, report: Dict) -> List[Dict]:
        """Gerar recomendações usando AI"""
        
        recommendations = []
        risk_level = report.get("risk_assessment", {}).get("risk_level", "Unknown")
        
        # Recomendações baseadas no nível de risco
        if risk_level == "HIGH" or risk_level == "CRITICAL":
            recommendations.append({
                "priority": "urgent",
                "action": "Investigação aprofundada necessária",
                "description": "Os indicadores sugerem risco elevado. Recomenda-se ação imediata.",
                "suggested_tools": ["Monitoramento contínuo", "Análise forense digital"]
            })
            
        if report.get("patterns_found"):
            recommendations.append({
                "priority": "high",
                "action": "Analisar padrões comportamentais",
                "description": "Padrões suspeitos foram identificados que requerem análise humana.",
                "suggested_tools": ["Análise temporal", "Correlação de eventos"]
            })
            
        # Consultar Aurora para recomendações adicionais
        ai_recommendations = report.get("risk_assessment", {}).get("ai_assessment", {}).get("recommendations", [])
        for ai_rec in ai_recommendations:
            recommendations.append({
                "priority": "medium",
                "action": ai_rec,
                "description": "Recomendação gerada por IA",
                "source": "Aurora AI"
            })
            
        return recommendations
    
    # Métodos auxiliares
    
    def _generate_investigation_id(self) -> str:
        """Gerar ID único para a investigação"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"INV-{timestamp}"
    
    def _assess_data_quality(self, initial_results: Dict) -> Dict:
        """Avaliar qualidade e tipo dos dados iniciais"""
        assessment = {
            "has_social_profiles": False,
            "social_platforms": [],
            "has_email_breaches": False,
            "has_location_data": False,
            "data_completeness": 0
        }
        
        # Verificar perfis sociais
        if "username_search" in initial_results.get("data_found", {}):
            profiles = initial_results["data_found"]["username_search"].get("profiles_found", [])
            if profiles:
                assessment["has_social_profiles"] = True
                assessment["social_platforms"] = profiles[:10]  # Top 10
                
        # Verificar breaches
        if "email_analysis" in initial_results.get("data_found", {}):
            breaches = initial_results["data_found"]["email_analysis"].get("breaches", [])
            if breaches:
                assessment["has_email_breaches"] = True
                
        return assessment
    
    def _count_data_points(self, report: Dict) -> int:
        """Contar total de pontos de dados coletados"""
        count = 0
        
        def count_recursive(obj):
            nonlocal count
            if isinstance(obj, dict):
                count += len(obj)
                for value in obj.values():
                    count_recursive(value)
            elif isinstance(obj, list):
                count += len(obj)
                for item in obj:
                    count_recursive(item)
                    
        count_recursive(report.get("data_collected", {}))
        return count
    
    def _classify_risk_level(self, score: int) -> str:
        """Classificar nível de risco"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _generate_mitigation_suggestions(self, risk_factors: List[str]) -> List[str]:
        """Gerar sugestões de mitigação"""
        suggestions = []
        
        if "Alta exposição online" in risk_factors:
            suggestions.append("Reduzir pegada digital removendo perfis não utilizados")
            
        if "Dados comprometidos" in risk_factors:
            suggestions.append("Alterar senhas imediatamente e ativar 2FA")
            
        if "Padrões suspeitos" in risk_factors:
            suggestions.append("Monitorar atividade e investigar anomalias")
            
        return suggestions
    
    def _extract_key_findings(self, report: Dict) -> List[str]:
        """Extrair principais descobertas"""
        findings = []
        
        # Adicionar descobertas baseadas nos dados
        data = report.get("data_collected", {})
        
        if data.get("initial", {}).get("data_found", {}).get("username_search"):
            profiles_count = len(data["initial"]["data_found"]["username_search"].get("profiles_found", []))
            if profiles_count > 0:
                findings.append(f"{profiles_count} perfis online encontrados")
                
        if report.get("patterns_found"):
            findings.append(f"{len(report['patterns_found'])} padrões comportamentais identificados")
            
        return findings
    
    def _format_target_info(self, target_data: Dict) -> str:
        """Formatar informações do alvo"""
        info = []
        if target_data.get("username"):
            info.append(f"- **Username:** {target_data['username']}")
        if target_data.get("email"):
            info.append(f"- **Email:** {target_data['email']}")
        if target_data.get("phone"):
            info.append(f"- **Telefone:** {target_data['phone']}")
        return "\n".join(info) if info else "- Sem identificadores fornecidos"
    
    def _format_key_findings(self, findings: List[str]) -> str:
        """Formatar principais descobertas"""
        if not findings:
            return "- Nenhuma descoberta significativa"
        return "\n".join([f"- {finding}" for finding in findings])
    
    def _format_risk_assessment(self, risk_assessment: Dict) -> str:
        """Formatar avaliação de risco"""
        if not risk_assessment:
            return "Avaliação de risco não disponível"
            
        text = f"""
- **Score de Risco:** {risk_assessment.get('risk_score', 0)}/100
- **Nível:** {risk_assessment.get('risk_level', 'Unknown')}
- **Fatores de Risco:** {', '.join(risk_assessment.get('risk_factors', ['Nenhum']))}
        """
        return text.strip()
    
    def _format_recommendations(self, recommendations: List[Dict]) -> str:
        """Formatar recomendações"""
        if not recommendations:
            return "- Sem recomendações específicas"
            
        formatted = []
        for rec in recommendations[:5]:  # Top 5
            formatted.append(f"- **{rec.get('action', 'Ação')}:** {rec.get('description', '')}")
            
        return "\n".join(formatted)
    
    def _calculate_confidence(self, report: Dict) -> float:
        """Calcular score de confiança da investigação"""
        confidence = 0.0
        factors = 0
        
        # Fases completadas
        phases = len(report.get("phases_completed", []))
        if phases > 0:
            confidence += (phases / 6) * 30  # 6 fases totais
            factors += 1
            
        # Dados coletados
        data_points = self._count_data_points(report)
        if data_points > 0:
            confidence += min(30, data_points / 10)  # Max 30 pontos
            factors += 1
            
        # Ferramentas usadas
        if self.investigation_state.get("tools_used"):
            confidence += len(self.investigation_state["tools_used"]) * 5
            factors += 1
            
        # Normalizar para 0-100
        if factors > 0:
            confidence = min(100, confidence)
            
        return round(confidence, 2)
