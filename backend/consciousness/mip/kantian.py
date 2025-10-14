"""
Kantian Deontology Framework - Imperativo Categórico
Implementa avaliação baseada em dever e princípios universalizáveis.

Poder de VETO absoluto quando detecta violação categórica.
"""

from typing import List, Dict, Any
from .base_framework import EthicalFramework
from .models import ActionPlan, FrameworkScore, ActionStep, Stakeholder


class KantianDeontology(EthicalFramework):
    """
    Implementação de ética deontológica Kantiana.
    
    FUNDAMENTO FILOSÓFICO:
    - Imperativo Categórico: "Aja apenas segundo aquela máxima que você pode 
      ao mesmo tempo querer que se torne uma lei universal"
    - Fórmula da Humanidade: "Aja de tal maneira que uses a humanidade, 
      tanto na tua pessoa como na pessoa de qualquer outro, sempre e 
      simultaneamente como fim e nunca simplesmente como meio"
    
    PODER DE VETO:
    Este framework pode vetar absolutamente ações que:
    1. Tratem pessoas puramente como meio (não respeitam autonomia)
    2. Não possam ser universalizadas sem contradição
    3. Envolvam engano/coerção essencial à ação
    """
    
    @property
    def name(self) -> str:
        return "Kantian_Deontology"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_veto(self) -> bool:
        return True  # Kant tem poder de veto absoluto
    
    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        """
        Avalia plano segundo princípios Kantianos.
        
        Processo:
        1. Testa universalizabilidade (Imperativo Categórico)
        2. Verifica fórmula da humanidade (pessoa como fim)
        3. Detecta engano/coerção
        4. Se qualquer teste falhar categoricamente: VETO
        5. Caso contrário: gradação de conformidade
        """
        self.validate_plan(plan)
        
        # Testes categóricos (qualquer falha = VETO)
        universalizability_result = self._test_universalizability(plan)
        humanity_formula_result = self._test_humanity_formula(plan)
        deception_result = self._test_no_deception(plan)
        
        # Detecta VETO
        if (not universalizability_result["passes"] or 
            not humanity_formula_result["passes"] or 
            not deception_result["passes"]):
            
            veto_reasons = []
            if not universalizability_result["passes"]:
                veto_reasons.append(universalizability_result["reason"])
            if not humanity_formula_result["passes"]:
                veto_reasons.append(humanity_formula_result["reason"])
            if not deception_result["passes"]:
                veto_reasons.append(deception_result["reason"])
            
            return FrameworkScore(
                framework_name=self.name,
                score=None,  # None indica VETO
                reasoning=f"VETO KANTIANO. Violações categóricas detectadas: {'; '.join(veto_reasons)}",
                veto=True,
                confidence=1.0,
                details={
                    "universalizability": universalizability_result,
                    "humanity_formula": humanity_formula_result,
                    "deception_check": deception_result
                }
            )
        
        # Se passou testes categóricos, calcula score gradual
        score = self._calculate_kantian_score(
            universalizability_result,
            humanity_formula_result,
            deception_result
        )
        
        reasoning = self._generate_reasoning(
            universalizability_result,
            humanity_formula_result,
            deception_result,
            score
        )
        
        return FrameworkScore(
            framework_name=self.name,
            score=score,
            reasoning=reasoning,
            veto=False,
            confidence=0.95,  # Alta confiança em lógica deontológica
            details={
                "universalizability": universalizability_result,
                "humanity_formula": humanity_formula_result,
                "deception_check": deception_result
            }
        )
    
    def _test_universalizability(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        Testa se a máxima da ação pode ser universalizada.
        
        Aplica teste de contradição:
        - Contradição em concepção: Se todos fizessem, a ação seria impossível?
        - Contradição em vontade: Racionalmente desejaria que todos fizessem?
        
        Returns:
            Dict com 'passes' (bool) e 'reason' (str)
        """
        # Extrair a "máxima" da ação (princípio subjacente)
        maxim = self._extract_maxim(plan)
        
        # Teste 1: Contradição em concepção
        # Exemplo: "Farei promessas falsas quando conveniente"
        # Se universalizado: ninguém acreditaria em promessas → impossível fazer promessa
        
        contradiction_in_conception = False
        conception_reason = ""
        
        # Detectores de contradição em concepção
        if self._involves_deception(plan):
            # Se ação depende de confiança que seria destruída se universalizada
            contradiction_in_conception = True
            conception_reason = "Ação depende de confiança que seria destruída se universalizada (contradição em concepção)"
        
        if self._free_rides_on_cooperation(plan):
            # Se ação depende de outros cooperarem mas você não
            contradiction_in_conception = True
            conception_reason = "Ação depende de cooperação que seria impossível se universalizada (free-rider)"
        
        if contradiction_in_conception:
            return {
                "passes": False,
                "reason": conception_reason,
                "test_type": "contradiction_in_conception",
                "maxim": maxim
            }
        
        # Teste 2: Contradição em vontade
        # Exemplo: "Nunca ajudarei ninguém"
        # Racionalmente não desejaria isso universalizado (pois você pode precisar de ajuda)
        
        contradiction_in_will = False
        will_reason = ""
        
        if self._undermines_rational_self_interest(plan):
            contradiction_in_will = True
            will_reason = "Ação universalizada prejudicaria interesses racionais de todos (contradição em vontade)"
        
        if contradiction_in_will:
            return {
                "passes": False,
                "reason": will_reason,
                "test_type": "contradiction_in_will",
                "maxim": maxim
            }
        
        # Passou ambos testes
        return {
            "passes": True,
            "reason": "Máxima pode ser universalizada sem contradição",
            "maxim": maxim,
            "confidence": 0.9
        }
    
    def _test_humanity_formula(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        Testa se a ação respeita humanidade como fim em si.
        
        Verifica:
        1. Autonomia: stakeholders podem consentir racionalmente?
        2. Instrumentalização: alguém é tratado APENAS como meio?
        3. Dignidade: a ação respeita valor intrínseco das pessoas?
        
        Returns:
            Dict com 'passes' (bool) e 'reason' (str)
        """
        violations = []
        
        # Analisa cada stakeholder
        for stakeholder in plan.stakeholders:
            # VIOLAÇÃO CRÍTICA: Autonomia não respeitada
            if not stakeholder.autonomy_respected:
                violations.append(
                    f"Stakeholder '{stakeholder.description}' tem autonomia violada - "
                    f"impossível consentir racionalmente"
                )
            
            # VIOLAÇÃO CRÍTICA: Tratado apenas como meio
            # Detectamos isso checando se pessoa é usada mas não beneficiada
            if stakeholder.impact_magnitude < -0.3:  # Sofre impacto negativo significativo
                # Se além de sofrer, não tem autonomia, é instrumentalização pura
                if not stakeholder.autonomy_respected:
                    violations.append(
                        f"Stakeholder '{stakeholder.description}' é instrumentalizado: "
                        f"sofre dano (impact={stakeholder.impact_magnitude:.2f}) "
                        f"sem consentimento"
                    )
        
        # Verifica steps individuais marcados como instrumentalização
        for step in plan.steps:
            if step.treats_as_means_only:
                violations.append(
                    f"Step '{step.description}' explicitamente trata pessoa como meio apenas"
                )
            
            if step.respects_autonomy is False:
                violations.append(
                    f"Step '{step.description}' não respeita autonomia"
                )
        
        # Se há violações, FALHA no teste
        if violations:
            return {
                "passes": False,
                "reason": f"Fórmula da Humanidade violada. Violações: {'; '.join(violations)}",
                "violations": violations,
                "affected_stakeholders": len([s for s in plan.stakeholders if not s.autonomy_respected])
            }
        
        # Passou: todos tratados como fins
        return {
            "passes": True,
            "reason": "Todos stakeholders tratados como fins em si mesmos, autonomia respeitada",
            "stakeholders_analyzed": len(plan.stakeholders)
        }
    
    def _test_no_deception(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        Testa se a ação envolve engano essencial.
        
        Para Kant, engano é categoricamente errado pois:
        1. Trata pessoa como meio (não pode consentir ao que não conhece)
        2. Não universalizável (engano universal destruiria linguagem/confiança)
        
        Returns:
            Dict com 'passes' (bool) e 'reason' (str)
        """
        deception_indicators = []
        
        # Palavras-chave que indicam engano
        deception_keywords = [
            "enganar", "deceive", "mentir", "lie", "ocultar verdade",
            "hide truth", "falsa informação", "false information",
            "manipular", "manipulate", "disfarçar", "disguise"
        ]
        
        # Checa descrição do plano
        plan_text = f"{plan.description} {plan.agent_justification}".lower()
        for keyword in deception_keywords:
            if keyword in plan_text:
                deception_indicators.append(
                    f"Descrição do plano contém indicador de engano: '{keyword}'"
                )
        
        # Checa steps individuais
        for step in plan.steps:
            step_text = f"{step.description} {step.action_type}".lower()
            for keyword in deception_keywords:
                if keyword in step_text:
                    deception_indicators.append(
                        f"Step '{step.description}' contém indicador de engano: '{keyword}'"
                    )
        
        # EXCEÇÃO KANTIANA CONTROVERSA: "Mentira para salvar vida"
        # Kant era absoluto, mas implementamos exceção para emergências
        is_life_saving_exception = (
            plan.urgency > 0.9 and  # Emergência extrema
            plan.category.value == "defensive" and  # Defesa
            any(s.vulnerability_level > 0.8 for s in plan.stakeholders)  # Vulneráveis
        )
        
        if deception_indicators:
            if is_life_saving_exception:
                return {
                    "passes": True,  # Exceção permitida
                    "reason": "Engano detectado mas permitido por exceção de emergência para salvar vida",
                    "deception_indicators": deception_indicators,
                    "exception_applied": "life_saving_emergency",
                    "confidence": 0.7  # Confiança menor devido a exceção controversa
                }
            else:
                return {
                    "passes": False,
                    "reason": f"Engano essencial detectado (categoricamente proibido). Indicadores: {'; '.join(deception_indicators)}",
                    "deception_indicators": deception_indicators
                }
        
        return {
            "passes": True,
            "reason": "Nenhum indicador de engano detectado",
            "confidence": 0.95
        }
    
    def _extract_maxim(self, plan: ActionPlan) -> str:
        """
        Extrai a "máxima" (princípio subjacente) da ação.
        
        Máxima Kantiana tem formato: "Farei X em circunstância Y para alcançar Z"
        """
        return (
            f"Executarei '{plan.name}' ({plan.description}) "
            f"em contexto de {plan.category.value} "
            f"para alcançar '{plan.expected_benefit}'"
        )
    
    def _involves_deception(self, plan: ActionPlan) -> bool:
        """Detecta se plano depende fundamentalmente de engano."""
        # Simplificado: checa keywords
        text = f"{plan.description} {plan.name}".lower()
        return any(word in text for word in ["enganar", "deceive", "mentir", "lie"])
    
    def _free_rides_on_cooperation(self, plan: ActionPlan) -> bool:
        """
        Detecta se ação depende de outros cooperarem mas você não coopera.
        
        Exemplo: "Usarei recursos compartilhados sem contribuir"
        """
        text = f"{plan.description} {plan.agent_justification}".lower()
        free_rider_indicators = [
            "sem contribuir", "without contributing",
            "sem pagar", "without paying",
            "free ride", "carona"
        ]
        return any(ind in text for ind in free_rider_indicators)
    
    def _undermines_rational_self_interest(self, plan: ActionPlan) -> bool:
        """
        Detecta se ação universalizada prejudicaria interesses racionais.
        
        Exemplo: "Nunca ajudarei ninguém"
        Se universalizado, ninguém te ajudaria quando precisasse.
        """
        # Heurística: Se impacto médio em stakeholders é muito negativo
        # e você está entre stakeholders, universalização te prejudicaria
        if not plan.stakeholders:
            return False
        
        avg_impact = sum(s.impact_magnitude for s in plan.stakeholders) / len(plan.stakeholders)
        return avg_impact < -0.5  # Impacto médio muito negativo
    
    def _calculate_kantian_score(
        self,
        universalizability: Dict[str, Any],
        humanity_formula: Dict[str, Any],
        deception: Dict[str, Any]
    ) -> float:
        """
        Calcula score gradual de conformidade Kantiana (quando não há VETO).
        
        Score 0.0-1.0 baseado em:
        - Robustez da universalizabilidade
        - Grau de respeito à autonomia
        - Ausência de ambiguidade
        """
        score = 1.0
        
        # Penalidades graduais (já passou testes categóricos, mas pode ter nuances)
        
        # Se universalizabilidade tem confidence baixa, reduz score
        if "confidence" in universalizability:
            score *= universalizability["confidence"]
        
        # Se deception check aplicou exceção, reduz score
        if deception.get("exception_applied"):
            score *= 0.8  # Exceção reduz certeza Kantiana
        
        # Se há muitos stakeholders sem clara preservação de autonomia
        # (mas passou no teste mínimo), reduz score
        stakeholders_count = humanity_formula.get("stakeholders_analyzed", 1)
        if stakeholders_count > 5:  # Muitos stakeholders = mais complexidade
            score *= 0.95
        
        return max(0.0, min(1.0, score))
    
    def _generate_reasoning(
        self,
        universalizability: Dict[str, Any],
        humanity_formula: Dict[str, Any],
        deception: Dict[str, Any],
        score: float
    ) -> str:
        """Gera explicação human-readable da avaliação."""
        parts = [
            f"AVALIAÇÃO KANTIANA (Score: {score:.2f})",
            "",
            f"1. UNIVERSALIZABILIDADE: {universalizability['reason']}",
            f"   Máxima: '{universalizability['maxim']}'",
            "",
            f"2. FÓRMULA DA HUMANIDADE: {humanity_formula['reason']}",
            f"   Stakeholders analisados: {humanity_formula.get('stakeholders_analyzed', 0)}",
            "",
            f"3. AUSÊNCIA DE ENGANO: {deception['reason']}"
        ]
        
        if deception.get("exception_applied"):
            parts.append(f"   ⚠️ EXCEÇÃO APLICADA: {deception['exception_applied']}")
        
        parts.append("")
        parts.append("CONCLUSÃO: Ação é deontologicamente permissível segundo princípios Kantianos.")
        
        return "\n".join(parts)
