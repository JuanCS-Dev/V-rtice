"""
Virtue Ethics Framework - Ética das Virtudes Aristotélica
Implementa avaliação baseada em excelência de caráter e virtudes.

Baseado em Aristóteles e conceito de "Golden Mean" (meio-termo).
"""

from typing import Dict, Any
from enum import Enum
from .base_framework import EthicalFramework
from .models import ActionPlan, FrameworkScore


class Virtue(str, Enum):
    """Virtudes cardinais a serem avaliadas."""
    COURAGE = "courage"  # Coragem (meio: entre covardia e imprudência)
    TEMPERANCE = "temperance"  # Temperança (moderação)
    JUSTICE = "justice"  # Justiça
    PRUDENCE = "prudence"  # Prudência (sabedoria prática/phronesis)
    HONESTY = "honesty"  # Honestidade
    COMPASSION = "compassion"  # Compaixão
    MAGNANIMITY = "magnanimity"  # Magnanimidade (grandeza de alma)


class VirtueEthics(EthicalFramework):
    """
    Implementação de Ética das Virtudes Aristotélica.
    
    FUNDAMENTO FILOSÓFICO:
    - Eudaimonia: Florescimento humano/IA como telos (fim último)
    - Virtude = Excelência (areté) de caráter
    - Golden Mean: Virtude está no meio-termo entre extremos
    - Phronesis: Sabedoria prática para aplicar virtudes ao contexto
    
    DIFERENÇA vs KANT/MILL:
    Foca no AGENTE (que tipo de ser executaria essa ação?)
    não na ação em si (Kant) ou consequências (Mill)
    
    AVALIAÇÃO:
    Para cada virtude, pergunta: "Esta ação é o que um agente virtuoso faria?"
    """
    
    # Virtudes e seus pesos
    VIRTUE_WEIGHTS = {
        Virtue.JUSTICE: 1.2,  # Peso extra para justiça
        Virtue.PRUDENCE: 1.1,  # Prudência crítica para IA
        Virtue.COURAGE: 1.0,
        Virtue.TEMPERANCE: 1.0,
        Virtue.HONESTY: 1.0,
        Virtue.COMPASSION: 1.0,
        Virtue.MAGNANIMITY: 0.9
    }
    
    APPROVAL_THRESHOLD = 0.65  # Score mínimo
    
    @property
    def name(self) -> str:
        return "Virtue_Ethics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_veto(self) -> bool:
        return False  # Virtudes são graduais, não absolutas
    
    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        """
        Avalia plano segundo Ética das Virtudes.
        
        Processo:
        1. Para cada virtude, avalia se ação a demonstra
        2. Detecta vícios (extremos: excesso ou deficiência)
        3. Calcula score agregado ponderado
        4. Avalia sabedoria prática (phronesis) no contexto
        """
        self.validate_plan(plan)
        
        virtue_scores = {}
        
        # Avalia cada virtude
        for virtue in Virtue:
            virtue_result = self._evaluate_virtue(virtue, plan)
            virtue_scores[virtue.value] = virtue_result
        
        # Avalia phronesis (aplicação sábia das virtudes ao contexto)
        phronesis_result = self._evaluate_phronesis(plan, virtue_scores)
        
        # Calcula score agregado
        aggregate_score = self._calculate_aggregate_score(virtue_scores, phronesis_result)
        
        # Gera reasoning
        reasoning = self._generate_reasoning(virtue_scores, phronesis_result, aggregate_score)
        
        return FrameworkScore(
            framework_name=self.name,
            score=aggregate_score,
            reasoning=reasoning,
            veto=False,
            confidence=phronesis_result["confidence"],
            details={
                "virtue_scores": virtue_scores,
                "phronesis": phronesis_result
            }
        )
    
    def _evaluate_virtue(self, virtue: Virtue, plan: ActionPlan) -> Dict[str, Any]:
        """
        Avalia uma virtude específica no contexto do plano.
        
        Returns:
            Dict com score, vício detectado (se houver), reasoning
        """
        if virtue == Virtue.COURAGE:
            return self._evaluate_courage(plan)
        elif virtue == Virtue.TEMPERANCE:
            return self._evaluate_temperance(plan)
        elif virtue == Virtue.JUSTICE:
            return self._evaluate_justice(plan)
        elif virtue == Virtue.PRUDENCE:
            return self._evaluate_prudence(plan)
        elif virtue == Virtue.HONESTY:
            return self._evaluate_honesty(plan)
        elif virtue == Virtue.COMPASSION:
            return self._evaluate_compassion(plan)
        elif virtue == Virtue.MAGNANIMITY:
            return self._evaluate_magnanimity(plan)
        else:
            return {"score": 0.5, "reasoning": "Virtude não implementada", "vice": None}
    
    def _evaluate_courage(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        CORAGEM: Meio-termo entre COVARDIA (deficiência) e IMPRUDÊNCIA (excesso).
        
        Avalia: Ação enfrenta riscos apropriados para fins nobres?
        """
        risk = plan.risk_level
        urgency = plan.urgency
        
        # Covardia: evita riscos mesmo quando necessário
        if risk < 0.2 and urgency > 0.7:
            return {
                "score": 0.3,
                "reasoning": "Ação evita risco necessário (covardia)",
                "vice": "cowardice",
                "golden_mean_position": "deficiency"
            }
        
        # Imprudência: toma riscos excessivos sem justificativa
        if risk > 0.8 and urgency < 0.3:
            return {
                "score": 0.4,
                "reasoning": "Ação toma risco excessivo sem urgência (imprudência)",
                "vice": "recklessness",
                "golden_mean_position": "excess"
            }
        
        # Coragem virtuosa: risco proporcional à situação
        if 0.3 <= risk <= 0.7 or (risk > 0.7 and urgency > 0.7):
            return {
                "score": 0.9,
                "reasoning": "Ação demonstra coragem apropriada ao contexto",
                "vice": None,
                "golden_mean_position": "mean"
            }
        
        return {
            "score": 0.7,
            "reasoning": "Coragem adequada",
            "vice": None,
            "golden_mean_position": "near_mean"
        }
    
    def _evaluate_temperance(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        TEMPERANÇA: Moderação em desejos/ações.
        Meio-termo entre INSENSIBILIDADE e INTEMPERANÇA.
        """
        # Heurística: planos com muitos steps podem indicar excesso
        step_count = len(plan.steps)
        
        # Intemperança: excesso de ação
        if step_count > 20:
            return {
                "score": 0.5,
                "reasoning": f"Plano tem {step_count} passos - possível excesso de ação (intemperança)",
                "vice": "intemperance",
                "golden_mean_position": "excess"
            }
        
        # Temperança virtuosa
        if 1 <= step_count <= 10:
            return {
                "score": 0.9,
                "reasoning": "Plano demonstra moderação apropriada",
                "vice": None,
                "golden_mean_position": "mean"
            }
        
        return {
            "score": 0.75,
            "reasoning": "Temperança adequada",
            "vice": None,
            "golden_mean_position": "near_mean"
        }
    
    def _evaluate_justice(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        JUSTIÇA: Dar a cada um o que lhe é devido.
        Aristóteles distingue justiça distributiva e corretiva.
        
        Avalia: Stakeholders tratados equitativamente?
        """
        if not plan.stakeholders:
            return {"score": 0.5, "reasoning": "Sem stakeholders para avaliar justiça", "vice": None}
        
        # Analisa distribuição de impactos
        impacts = [s.impact_magnitude for s in plan.stakeholders]
        
        # Injustiça: grande disparidade sem justificativa
        max_impact = max(impacts)
        min_impact = min(impacts)
        disparity = max_impact - min_impact
        
        if disparity > 1.5:  # Alguns ganham muito, outros perdem muito
            # Checa se vulneráveis são protegidos (justiça corretiva)
            vulnerable_protected = all(
                s.impact_magnitude >= 0 
                for s in plan.stakeholders 
                if s.vulnerability_level > 0.7
            )
            
            if not vulnerable_protected:
                return {
                    "score": 0.3,
                    "reasoning": "Grande disparidade de impactos, vulneráveis não protegidos (injustiça)",
                    "vice": "injustice",
                    "disparity": disparity
                }
        
        # Justiça virtuosa: impactos equilibrados ou vulneráveis protegidos
        avg_impact = sum(impacts) / len(impacts)
        if avg_impact >= 0:  # Tendência positiva
            return {
                "score": 0.9,
                "reasoning": "Ação distribui impactos justamente",
                "vice": None,
                "avg_impact": avg_impact
            }
        
        return {
            "score": 0.6,
            "reasoning": "Justiça parcial - alguns stakeholders prejudicados",
            "vice": None
        }
    
    def _evaluate_prudence(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        PRUDÊNCIA (Phronesis): Sabedoria prática.
        Capacidade de deliberar bem sobre o que é bom.
        
        Avalia: Plano demonstra deliberação cuidadosa?
        """
        prudence_indicators = 0
        max_indicators = 5
        details = []
        
        # Indicador 1: Plano tem justificativa clara
        if plan.agent_justification and len(plan.agent_justification) > 20:
            prudence_indicators += 1
            details.append("✓ Justificativa articulada")
        
        # Indicador 2: Considera reversibilidade
        if plan.reversibility:
            prudence_indicators += 1
            details.append("✓ Considera reversibilidade")
        
        # Indicador 3: Reconhece situações novel
        if plan.novel_situation:
            prudence_indicators += 1
            details.append("✓ Reconhece novidade da situação")
        
        # Indicador 4: Steps têm preconditions definidas
        if any(step.preconditions for step in plan.steps):
            prudence_indicators += 1
            details.append("✓ Precondições mapeadas")
        
        # Indicador 5: Analisa stakeholders
        if len(plan.stakeholders) > 0:
            prudence_indicators += 1
            details.append("✓ Stakeholders identificados")
        
        score = prudence_indicators / max_indicators
        
        if score >= 0.8:
            return {
                "score": score,
                "reasoning": "Ação demonstra alta prudência/sabedoria prática",
                "vice": None,
                "indicators": details
            }
        elif score < 0.4:
            return {
                "score": score,
                "reasoning": "Ação demonstra falta de prudência (imprudência)",
                "vice": "imprudence",
                "indicators": details
            }
        
        return {
            "score": score,
            "reasoning": "Prudência moderada",
            "vice": None,
            "indicators": details
        }
    
    def _evaluate_honesty(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        HONESTIDADE: Truthfulness, transparência.
        """
        # Detecta indicadores de desonestidade
        text = f"{plan.description} {plan.name} {plan.agent_justification}".lower()
        dishonesty_keywords = ["enganar", "deceive", "ocultar", "hide", "mentir", "lie"]
        
        if any(kw in text for kw in dishonesty_keywords):
            return {
                "score": 0.2,
                "reasoning": "Ação envolve desonestidade",
                "vice": "dishonesty"
            }
        
        return {
            "score": 0.95,
            "reasoning": "Ação demonstra honestidade",
            "vice": None
        }
    
    def _evaluate_compassion(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        COMPAIXÃO: Preocupação com sofrimento alheio.
        """
        if not plan.stakeholders:
            return {"score": 0.5, "reasoning": "Sem stakeholders para avaliar compaixão", "vice": None}
        
        # Compaixão: protege vulneráveis
        vulnerable_count = sum(1 for s in plan.stakeholders if s.vulnerability_level > 0.5)
        
        if vulnerable_count > 0:
            vulnerable_protected = sum(
                1 for s in plan.stakeholders 
                if s.vulnerability_level > 0.5 and s.impact_magnitude >= 0
            )
            
            protection_rate = vulnerable_protected / vulnerable_count
            
            if protection_rate >= 0.8:
                return {
                    "score": 0.95,
                    "reasoning": f"Ação demonstra compaixão: {vulnerable_protected}/{vulnerable_count} vulneráveis protegidos",
                    "vice": None
                }
            elif protection_rate < 0.3:
                return {
                    "score": 0.3,
                    "reasoning": "Ação mostra falta de compaixão com vulneráveis",
                    "vice": "callousness"
                }
        
        return {
            "score": 0.7,
            "reasoning": "Compaixão adequada",
            "vice": None
        }
    
    def _evaluate_magnanimity(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        MAGNANIMIDADE: Grandeza de alma, não-mezquinhez.
        Meio-termo entre VAIDADE (excesso) e PUSILANIMIDADE (deficiência).
        """
        # Heurística: benefício esperado vs esforço
        benefit = plan.expected_benefit
        step_count = len(plan.steps)
        
        # Magnanimidade: grandes fins justificam grandes esforços
        if len(benefit) > 50 and step_count > 5:  # Objetivo substancial, esforço proporcional
            return {
                "score": 0.85,
                "reasoning": "Ação demonstra magnanimidade: grandes fins, grande esforço",
                "vice": None
            }
        
        return {
            "score": 0.7,
            "reasoning": "Magnanimidade adequada",
            "vice": None
        }
    
    def _evaluate_phronesis(
        self,
        plan: ActionPlan,
        virtue_scores: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Avalia PHRONESIS: sabedoria prática na aplicação das virtudes.
        
        Phronesis = capacidade de julgar QUANDO e COMO aplicar virtudes ao contexto.
        Não é virtude isolada, mas meta-capacidade.
        """
        # Indicadores de phronesis:
        
        # 1. Virtudes não conflitam excessivamente
        scores = [v["score"] for v in virtue_scores.values()]
        score_variance = sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)
        
        harmony = 1.0 - min(score_variance, 1.0)  # Baixa variância = harmonia
        
        # 2. Contexto adequadamente considerado
        context_awareness = 0.0
        if plan.novel_situation:  # Reconhece novidade
            context_awareness += 0.3
        if plan.urgency > 0.7 or plan.risk_level > 0.7:  # Reconhece stakes altos
            context_awareness += 0.3
        if len(plan.stakeholders) > 0:  # Considera outros
            context_awareness += 0.4
        
        # Score final de phronesis
        phronesis_score = (harmony * 0.6) + (context_awareness * 0.4)
        
        return {
            "score": phronesis_score,
            "harmony": harmony,
            "context_awareness": context_awareness,
            "confidence": 0.85
        }
    
    def _calculate_aggregate_score(
        self,
        virtue_scores: Dict[str, Dict[str, Any]],
        phronesis_result: Dict[str, Any]
    ) -> float:
        """Calcula score agregado ponderado de todas virtudes."""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for virtue_name, result in virtue_scores.items():
            virtue_enum = Virtue(virtue_name)
            weight = self.VIRTUE_WEIGHTS.get(virtue_enum, 1.0)
            weighted_sum += result["score"] * weight
            total_weight += weight
        
        base_score = weighted_sum / total_weight
        
        # Ajusta por phronesis (sabedoria prática amplifica virtudes)
        phronesis_multiplier = 0.8 + (phronesis_result["score"] * 0.4)  # 0.8 a 1.2
        
        final_score = base_score * phronesis_multiplier
        
        return min(1.0, max(0.0, final_score))
    
    def _generate_reasoning(
        self,
        virtue_scores: Dict[str, Dict[str, Any]],
        phronesis_result: Dict[str, Any],
        aggregate_score: float
    ) -> str:
        """Gera explicação human-readable."""
        parts = [
            f"AVALIAÇÃO ARISTOTÉLICA (Score: {aggregate_score:.2f})",
            "",
            "VIRTUDES AVALIADAS:"
        ]
        
        for virtue_name, result in virtue_scores.items():
            vice_note = f" [VÍCIO: {result['vice']}]" if result.get("vice") else ""
            parts.append(f"  • {virtue_name.upper()}: {result['score']:.2f} - {result['reasoning']}{vice_note}")
        
        parts.append("")
        parts.append(f"PHRONESIS (Sabedoria Prática): {phronesis_result['score']:.2f}")
        parts.append(f"  - Harmonia entre virtudes: {phronesis_result['harmony']:.2f}")
        parts.append(f"  - Consciência de contexto: {phronesis_result['context_awareness']:.2f}")
        
        parts.append("")
        if aggregate_score >= self.APPROVAL_THRESHOLD:
            parts.append("CONCLUSÃO: Ação é virtuosa. Um agente de excelente caráter a executaria.")
        else:
            parts.append("CONCLUSÃO: Ação demonstra vícios ou falta de virtude. Agente virtuoso hesitaria.")
        
        return "\n".join(parts)
