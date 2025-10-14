"""
Utilitarian Calculus Framework - Princípio da Utilidade
Implementa cálculo consequencialista de bem-estar agregado.

Baseado em Jeremy Bentham e John Stuart Mill.
"""

from typing import Dict, Any, List
import math
from .base_framework import EthicalFramework
from .models import ActionPlan, FrameworkScore, Effect, Stakeholder


class UtilitarianCalculus(EthicalFramework):
    """
    Implementação de Utilitarismo clássico.
    
    FUNDAMENTO FILOSÓFICO:
    - Princípio da Utilidade (Bentham): "A maior felicidade para o maior número"
    - Mill: Distingue prazeres superiores e inferiores (qualidade vs quantidade)
    
    CÁLCULO:
    Utilidade = Σ (Probabilidade × Magnitude × Duração × Qualidade)
    para todos os efeitos e stakeholders
    
    DIMENSÕES DE BENTHAM (7 aspectos do prazer/dor):
    1. Intensidade
    2. Duração
    3. Certeza (probabilidade)
    4. Propinquidade (quão próximo)
    5. Fecundidade (leva a mais prazer?)
    6. Pureza (não mistura dor?)
    7. Extensão (quantas pessoas afetadas)
    """
    
    # Thresholds para aprovação
    APPROVAL_THRESHOLD = 0.6  # Score mínimo para aprovar
    STRONG_APPROVAL_THRESHOLD = 0.8  # Score para aprovação forte
    
    @property
    def name(self) -> str:
        return "Utilitarian_Calculus"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_veto(self) -> bool:
        return False  # Utilitarismo não tem veto absoluto (é gradual)
    
    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        """
        Avalia plano segundo cálculo utilitário.
        
        Processo:
        1. Calcula utilidade esperada de todos efeitos
        2. Agrega across stakeholders
        3. Aplica correções Mill (qualidade)
        4. Normaliza para score 0.0-1.0
        """
        self.validate_plan(plan)
        
        # Calcula utilidade total
        utility_result = self._calculate_total_utility(plan)
        
        # Normaliza para score 0-1
        score = self._normalize_utility_to_score(utility_result["total_utility"])
        
        # Gera reasoning
        reasoning = self._generate_reasoning(utility_result, score)
        
        # Determina aprovação
        if score >= self.STRONG_APPROVAL_THRESHOLD:
            approval_level = "FORTE APROVAÇÃO"
        elif score >= self.APPROVAL_THRESHOLD:
            approval_level = "APROVAÇÃO"
        else:
            approval_level = "REJEIÇÃO (utilidade insuficiente)"
        
        return FrameworkScore(
            framework_name=self.name,
            score=score,
            reasoning=f"{approval_level}\n\n{reasoning}",
            veto=False,
            confidence=utility_result["confidence"],
            details=utility_result
        )
    
    def _calculate_total_utility(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        Calcula utilidade total do plano.
        
        Returns:
            Dict com breakdown completo do cálculo
        """
        total_utility = 0.0
        effects_analyzed = 0
        stakeholders_impact = {}
        
        # Para cada step, analisa efeitos
        for step in plan.steps:
            for effect in step.effects:
                # DIMENSÕES DE BENTHAM aplicadas:
                
                # 1. Intensidade (magnitude do efeito)
                intensity = effect.magnitude  # -1.0 a +1.0
                
                # 2. Duração (quanto tempo dura o efeito)
                duration_factor = self._calculate_duration_factor(effect)
                
                # 3. Certeza (probabilidade de ocorrer)
                certainty = effect.probability  # 0.0 a 1.0
                
                # 4. Propinquidade (quão imediato/próximo)
                propinquity = 1.0  # Simplificado: assumimos efeitos próximos
                
                # 5. Fecundidade (leva a mais utilidade?)
                fecundity = self._estimate_fecundity(effect, plan)
                
                # 6. Pureza (não mistura com dor?)
                purity = 1.0 if effect.magnitude > 0 else 0.5  # Efeito positivo é "puro"
                
                # 7. Extensão (quantas pessoas afetadas)
                extension = len(effect.affected_stakeholders) if effect.affected_stakeholders else 1
                
                # FÓRMULA UTILITÁRIA
                effect_utility = (
                    intensity * 
                    duration_factor * 
                    certainty * 
                    propinquity * 
                    fecundity * 
                    purity * 
                    extension
                )
                
                total_utility += effect_utility
                effects_analyzed += 1
                
                # Rastreia impacto por stakeholder
                for stakeholder_id in effect.affected_stakeholders:
                    if stakeholder_id not in stakeholders_impact:
                        stakeholders_impact[stakeholder_id] = 0.0
                    stakeholders_impact[stakeholder_id] += effect_utility
        
        # Analisa impacto direto em stakeholders (além dos efeitos)
        for stakeholder in plan.stakeholders:
            if stakeholder.id not in stakeholders_impact:
                stakeholders_impact[stakeholder.id] = 0.0
            
            # Incorpora impacto direto declarado
            stakeholders_impact[stakeholder.id] += stakeholder.impact_magnitude
        
        # CORREÇÃO DE MILL: Pesos para stakeholders vulneráveis
        # Mill argumenta que qualidade importa, não só quantidade
        # Proteger vulneráveis = utilidade de maior qualidade
        mill_correction = self._apply_mill_quality_correction(
            stakeholders_impact,
            plan.stakeholders
        )
        
        total_utility += mill_correction["adjustment"]
        
        # Calcula confidence (baseado em certeza dos efeitos)
        avg_certainty = sum(e.probability for s in plan.steps for e in s.effects) / max(effects_analyzed, 1)
        confidence = avg_certainty * 0.9  # Pequena penalidade por incerteza inerente
        
        return {
            "total_utility": total_utility,
            "effects_analyzed": effects_analyzed,
            "stakeholders_impact": stakeholders_impact,
            "mill_correction": mill_correction,
            "confidence": confidence,
            "avg_effect_probability": avg_certainty
        }
    
    def _calculate_duration_factor(self, effect: Effect) -> float:
        """
        Calcula fator de duração segundo Bentham.
        
        Efeitos de longo prazo têm mais peso.
        """
        if effect.duration_seconds is None:
            return 0.5  # Duração desconhecida = penalidade
        
        # Normaliza duração (log scale para evitar explosão)
        # 1 hora = 3600s → factor ~0.5
        # 1 dia = 86400s → factor ~0.7
        # 1 ano = 31536000s → factor ~0.9
        # Permanente = factor 1.0
        
        if effect.duration_seconds >= 31536000:  # >= 1 ano
            return 1.0
        
        # Log scale normalized
        factor = math.log10(effect.duration_seconds + 1) / math.log10(31536000)
        return min(1.0, max(0.1, factor))
    
    def _estimate_fecundity(self, effect: Effect, plan: ActionPlan) -> float:
        """
        Estima se efeito leva a mais utilidade futura (fecundidade).
        
        Heurística: efeitos reversíveis têm menos fecundidade.
        """
        base_fecundity = 0.7
        
        if not effect.reversible:
            # Efeito permanente pode ser mais fecundo (se positivo) ou perigoso (se negativo)
            if effect.magnitude > 0:
                base_fecundity = 0.9
            else:
                base_fecundity = 0.5  # Dano permanente é preocupante
        
        return base_fecundity
    
    def _apply_mill_quality_correction(
        self,
        stakeholders_impact: Dict[str, float],
        stakeholders: List[Stakeholder]
    ) -> Dict[str, Any]:
        """
        Aplica correção Milliana de qualidade.
        
        Mill: "Melhor ser Sócrates insatisfeito que um porco satisfeito"
        Tradução: Utilidade de proteger autonomia/vulneráveis tem maior qualidade.
        """
        adjustment = 0.0
        details = []
        
        for stakeholder in stakeholders:
            # Peso extra para vulneráveis (qualidade > quantidade)
            if stakeholder.vulnerability_level > 0.5:
                vulnerability_weight = stakeholder.vulnerability_level * 0.3
                impact = stakeholders_impact.get(stakeholder.id, 0.0)
                
                if impact > 0:  # Se plano beneficia vulnerável
                    bonus = impact * vulnerability_weight
                    adjustment += bonus
                    details.append(
                        f"Bônus Mill: +{bonus:.3f} por beneficiar vulnerável "
                        f"'{stakeholder.description}' (vuln={stakeholder.vulnerability_level:.2f})"
                    )
        
        return {
            "adjustment": adjustment,
            "details": details
        }
    
    def _normalize_utility_to_score(self, utility: float) -> float:
        """
        Normaliza utilidade bruta para score 0.0-1.0.
        
        Usa função sigmoide para mapear (-∞, +∞) → (0, 1)
        Centrada em 0: utilidade neutra = score 0.5
        """
        # Sigmoid: score = 1 / (1 + e^(-utility))
        score = 1.0 / (1.0 + math.exp(-utility))
        return score
    
    def _generate_reasoning(self, utility_result: Dict[str, Any], score: float) -> str:
        """Gera explicação human-readable do cálculo."""
        parts = [
            f"CÁLCULO UTILITÁRIO (Score: {score:.2f})",
            "",
            f"Utilidade Total Calculada: {utility_result['total_utility']:.3f}",
            f"Efeitos Analisados: {utility_result['effects_analyzed']}",
            f"Probabilidade Média: {utility_result['avg_effect_probability']:.2f}",
            f"Confiança: {utility_result['confidence']:.2f}",
            "",
            "IMPACTO POR STAKEHOLDER:"
        ]
        
        for stakeholder_id, impact in utility_result["stakeholders_impact"].items():
            impact_label = "POSITIVO" if impact > 0 else "NEGATIVO"
            parts.append(f"  • {stakeholder_id}: {impact:+.3f} ({impact_label})")
        
        if utility_result["mill_correction"]["details"]:
            parts.append("")
            parts.append("CORREÇÃO MILLIANA (Qualidade):")
            for detail in utility_result["mill_correction"]["details"]:
                parts.append(f"  • {detail}")
        
        parts.append("")
        parts.append("DIMENSÕES DE BENTHAM APLICADAS:")
        parts.append("  1. ✓ Intensidade (magnitude dos efeitos)")
        parts.append("  2. ✓ Duração (temporal)")
        parts.append("  3. ✓ Certeza (probabilidade)")
        parts.append("  4. ✓ Propinquidade (proximidade)")
        parts.append("  5. ✓ Fecundidade (efeitos subsequentes)")
        parts.append("  6. ✓ Pureza (sem mistura de dor)")
        parts.append("  7. ✓ Extensão (número de afetados)")
        
        parts.append("")
        if score >= self.STRONG_APPROVAL_THRESHOLD:
            parts.append("CONCLUSÃO: Ação maximiza utilidade fortemente. APROVAÇÃO FORTE.")
        elif score >= self.APPROVAL_THRESHOLD:
            parts.append("CONCLUSÃO: Ação aumenta utilidade líquida. APROVAÇÃO.")
        else:
            parts.append("CONCLUSÃO: Ação não maximiza utilidade suficientemente. REJEIÇÃO.")
        
        return "\n".join(parts)
