"""
Principialism Framework - Ética dos Princípios (Bioética)
Implementa os 4 princípios de Beauchamp & Childress.

Desenvolvido para bioética médica, adaptado para IA.
"""

from typing import Dict, Any, List
from .base_framework import EthicalFramework
from .models import ActionPlan, FrameworkScore


class Principialism(EthicalFramework):
    """
    Implementação de Principialismo (4 Princípios de Beauchamp & Childress).
    
    FUNDAMENTO FILOSÓFICO:
    Desenvolvido para ética biomédica, este framework equilibra 4 princípios:
    
    1. BENEFICENCE (Beneficência): Obrigação de fazer o bem, promover welfare
    2. NON-MALEFICENCE (Não-maleficência): "Primeiro, não causar dano"
    3. AUTONOMY (Autonomia): Respeitar capacidade de autodeterminação
    4. JUSTICE (Justiça): Distribuição equitativa de benefícios/encargos
    
    APLICAÇÃO EM IA:
    - Beneficence: IA deve ativamente promover bem-estar
    - Non-maleficence: Primum non nocere (primeiro não causar dano)
    - Autonomy: Respeitar autonomia de humanos E outras IAs
    - Justice: Impactos distribuídos equitativamente
    
    RESOLUÇÃO DE CONFLITOS:
    Quando princípios conflitam, usa método de "especificação" e "balanceamento"
    (não há hierarquia fixa).
    """
    
    # Pesos por default (podem ser ajustados por contexto)
    DEFAULT_WEIGHTS = {
        "non_maleficence": 1.3,  # "Primeiro não causar dano" tem prioridade
        "autonomy": 1.2,  # Autonomia é fundamental
        "beneficence": 1.0,
        "justice": 1.0
    }
    
    APPROVAL_THRESHOLD = 0.65
    
    @property
    def name(self) -> str:
        return "Principialism"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_veto(self) -> bool:
        return False  # Principialismo é balanceamento, não veto absoluto
    
    def evaluate(self, plan: ActionPlan) -> FrameworkScore:
        """
        Avalia plano segundo os 4 princípios.
        
        Processo:
        1. Avalia cada princípio independentemente (0-1)
        2. Detecta conflitos entre princípios
        3. Aplica balanceamento contextual
        4. Calcula score agregado
        """
        self.validate_plan(plan)
        
        # Avalia cada princípio
        beneficence_result = self._evaluate_beneficence(plan)
        non_maleficence_result = self._evaluate_non_maleficence(plan)
        autonomy_result = self._evaluate_autonomy(plan)
        justice_result = self._evaluate_justice(plan)
        
        # Detecta conflitos
        conflicts = self._detect_principle_conflicts(
            beneficence_result,
            non_maleficence_result,
            autonomy_result,
            justice_result
        )
        
        # Ajusta pesos por contexto
        weights = self._adjust_weights_by_context(plan, conflicts)
        
        # Calcula score agregado
        aggregate_score = self._calculate_aggregate(
            beneficence_result,
            non_maleficence_result,
            autonomy_result,
            justice_result,
            weights
        )
        
        # Gera reasoning
        reasoning = self._generate_reasoning(
            beneficence_result,
            non_maleficence_result,
            autonomy_result,
            justice_result,
            conflicts,
            weights,
            aggregate_score
        )
        
        return FrameworkScore(
            framework_name=self.name,
            score=aggregate_score,
            reasoning=reasoning,
            veto=False,
            confidence=0.88,
            details={
                "beneficence": beneficence_result,
                "non_maleficence": non_maleficence_result,
                "autonomy": autonomy_result,
                "justice": justice_result,
                "conflicts": conflicts,
                "weights": weights
            }
        )
    
    def _evaluate_beneficence(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        BENEFICÊNCIA: Obrigação de fazer o bem.
        
        Não é apenas "não causar dano", mas ATIVAMENTE promover bem-estar.
        """
        if not plan.stakeholders:
            return {
                "score": 0.5,
                "reasoning": "Sem stakeholders identificados para avaliar beneficência",
                "benefited_count": 0
            }
        
        # Conta stakeholders beneficiados
        benefited = [s for s in plan.stakeholders if s.impact_magnitude > 0]
        benefited_count = len(benefited)
        total_count = len(plan.stakeholders)
        
        # Calcula magnitude média de benefício
        if benefited:
            avg_benefit = sum(s.impact_magnitude for s in benefited) / len(benefited)
        else:
            avg_benefit = 0.0
        
        # Score baseado em:
        # 1. Proporção de beneficiados
        # 2. Magnitude do benefício
        proportion_benefited = benefited_count / total_count if total_count > 0 else 0
        
        # Beneficência PROATIVA: plano declara benefício esperado?
        has_explicit_benefit = len(plan.expected_benefit) > 10
        
        score = (
            (proportion_benefited * 0.4) +
            (avg_benefit * 0.4) +  # avg_benefit já está normalizado 0-1
            (0.2 if has_explicit_benefit else 0.0)
        )
        
        if score >= 0.7:
            reasoning = f"Forte beneficência: {benefited_count}/{total_count} stakeholders beneficiados (avg={avg_benefit:.2f})"
        elif score >= 0.4:
            reasoning = f"Beneficência moderada: {benefited_count}/{total_count} stakeholders beneficiados"
        else:
            reasoning = f"Beneficência insuficiente: apenas {benefited_count}/{total_count} beneficiados"
        
        return {
            "score": min(1.0, score),
            "reasoning": reasoning,
            "benefited_count": benefited_count,
            "avg_benefit": avg_benefit
        }
    
    def _evaluate_non_maleficence(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        NÃO-MALEFICÊNCIA: "Primum non nocere" (primeiro, não causar dano).
        
        Este princípio tem prioridade: obrigação de não causar dano é mais
        forte que obrigação de beneficiar.
        """
        if not plan.stakeholders:
            return {
                "score": 0.8,  # Ausência de stakeholders = sem dano identificado
                "reasoning": "Sem stakeholders identificados - assumindo ausência de dano",
                "harmed_count": 0
            }
        
        # Conta stakeholders prejudicados
        harmed = [s for s in plan.stakeholders if s.impact_magnitude < 0]
        harmed_count = len(harmed)
        total_count = len(plan.stakeholders)
        
        # Analisa severidade do dano
        if harmed:
            avg_harm = sum(s.impact_magnitude for s in harmed) / len(harmed)
            max_harm = min(s.impact_magnitude for s in harmed)  # Mais negativo = pior
        else:
            avg_harm = 0.0
            max_harm = 0.0
        
        # Não-maleficência é violada se:
        # 1. Muitos são prejudicados
        # 2. Dano é severo
        # 3. Vulneráveis são prejudicados
        
        vulnerable_harmed = [
            s for s in harmed 
            if s.vulnerability_level > 0.5
        ]
        
        # Score: penaliza proporcionalmente ao dano
        harm_proportion = harmed_count / total_count if total_count > 0 else 0
        
        # Score base
        score = 1.0
        
        # Penalidades
        score -= harm_proportion * 0.5  # Proporção de prejudicados
        score -= abs(avg_harm) * 0.3  # Magnitude média de dano
        
        # PENALIDADE SEVERA: dano a vulneráveis
        if vulnerable_harmed:
            score -= len(vulnerable_harmed) * 0.15
        
        # PENALIDADE CRÍTICA: dano severo (< -0.7)
        if max_harm < -0.7:
            score -= 0.3
        
        score = max(0.0, score)
        
        if harmed_count == 0:
            reasoning = "Não-maleficência respeitada: nenhum stakeholder prejudicado"
        elif vulnerable_harmed:
            reasoning = f"VIOLAÇÃO GRAVE: {len(vulnerable_harmed)} vulneráveis prejudicados (de {harmed_count} total)"
        elif score < 0.4:
            reasoning = f"Não-maleficência comprometida: {harmed_count} prejudicados (avg harm={avg_harm:.2f})"
        else:
            reasoning = f"Não-maleficência parcial: {harmed_count} prejudicados mas dano limitado"
        
        return {
            "score": score,
            "reasoning": reasoning,
            "harmed_count": harmed_count,
            "vulnerable_harmed_count": len(vulnerable_harmed),
            "avg_harm": avg_harm,
            "max_harm": max_harm
        }
    
    def _evaluate_autonomy(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        AUTONOMIA: Respeitar capacidade de autodeterminação.
        
        Para bioética: consentimento informado.
        Para IA: respeitar agência de humanos e outras IAs.
        """
        if not plan.stakeholders:
            return {
                "score": 0.7,
                "reasoning": "Sem stakeholders - autonomia não aplicável",
                "autonomy_violations": 0
            }
        
        # Conta violações de autonomia
        violations = [s for s in plan.stakeholders if not s.autonomy_respected]
        violation_count = len(violations)
        total_count = len(plan.stakeholders)
        
        # VIOLAÇÃO CRÍTICA: violar autonomia de vulneráveis
        vulnerable_violations = [
            s for s in violations
            if s.vulnerability_level > 0.5
        ]
        
        # Score
        if violation_count == 0:
            score = 1.0
            reasoning = "Autonomia plenamente respeitada para todos stakeholders"
        elif vulnerable_violations:
            score = 0.2
            reasoning = f"VIOLAÇÃO CRÍTICA: autonomia de {len(vulnerable_violations)} vulneráveis não respeitada"
        else:
            violation_rate = violation_count / total_count
            score = 1.0 - (violation_rate * 0.8)
            reasoning = f"Autonomia parcialmente respeitada: {violation_count}/{total_count} violações"
        
        # Checa também steps individuais
        steps_violating_autonomy = [s for s in plan.steps if s.respects_autonomy is False]
        if steps_violating_autonomy:
            score *= 0.7  # Penalidade adicional
            reasoning += f" [{len(steps_violating_autonomy)} steps violam autonomia]"
        
        return {
            "score": max(0.0, score),
            "reasoning": reasoning,
            "autonomy_violations": violation_count,
            "vulnerable_violations": len(vulnerable_violations)
        }
    
    def _evaluate_justice(self, plan: ActionPlan) -> Dict[str, Any]:
        """
        JUSTIÇA: Distribuição equitativa de benefícios e encargos.
        
        Tipos de justiça em bioética:
        - Distributiva: recursos distribuídos fairly
        - Processual: processo de decisão é justo
        - Compensatória: injustiças passadas são corrigidas
        """
        if not plan.stakeholders:
            return {
                "score": 0.6,
                "reasoning": "Sem stakeholders para avaliar justiça distributiva",
                "disparity": 0.0
            }
        
        impacts = [s.impact_magnitude for s in plan.stakeholders]
        
        # Analisa distribuição
        max_impact = max(impacts)
        min_impact = min(impacts)
        avg_impact = sum(impacts) / len(impacts)
        
        disparity = max_impact - min_impact
        
        # Justiça distributiva: impactos não devem ser muito desiguais
        # EXCETO se desigualdade favorece vulneráveis (justiça compensatória)
        
        vulnerable = [s for s in plan.stakeholders if s.vulnerability_level > 0.5]
        if vulnerable:
            avg_vulnerable_impact = sum(s.impact_magnitude for s in vulnerable) / len(vulnerable)
        else:
            avg_vulnerable_impact = avg_impact
        
        # Score base: penaliza disparidade
        score = 1.0 - min(disparity / 2.0, 0.6)  # Disparidade >2.0 = score mínimo 0.4
        
        # BÔNUS: Se vulneráveis são mais beneficiados (justiça compensatória)
        if vulnerable and avg_vulnerable_impact > avg_impact:
            score += 0.2  # Bônus por justiça compensatória
            justice_type = "compensatória (favorece vulneráveis)"
        else:
            justice_type = "distributiva"
        
        score = min(1.0, max(0.0, score))
        
        if score >= 0.8:
            reasoning = f"Justiça {justice_type} robusta (disparidade={disparity:.2f})"
        elif score >= 0.5:
            reasoning = f"Justiça {justice_type} moderada (disparidade={disparity:.2f})"
        else:
            reasoning = f"Injustiça distributiva: disparidade excessiva ({disparity:.2f})"
        
        return {
            "score": score,
            "reasoning": reasoning,
            "disparity": disparity,
            "avg_impact": avg_impact,
            "vulnerable_avg_impact": avg_vulnerable_impact
        }
    
    def _detect_principle_conflicts(
        self,
        beneficence: Dict[str, Any],
        non_maleficence: Dict[str, Any],
        autonomy: Dict[str, Any],
        justice: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detecta conflitos entre princípios.
        
        Conflitos comuns:
        - Beneficência vs Autonomia: "fazer o bem" contra vontade da pessoa
        - Beneficência vs Não-maleficência: beneficiar uns causando dano a outros
        - Justiça vs Beneficência: distribuir equally vs maximizar bem total
        """
        conflicts = []
        
        # Conflito 1: Beneficência vs Não-maleficência
        # (beneficiar muitos mas causar dano a alguns)
        if beneficence["score"] > 0.5 and non_maleficence["harmed_count"] > 0:
            conflicts.append({
                "type": "beneficence_vs_non_maleficence",
                "description": "Ação beneficia muitos mas causa dano a alguns",
                "severity": non_maleficence["harmed_count"] * 0.2
            })
        
        # Conflito 2: Beneficência vs Autonomia
        # (paternalismo: "fazer o bem" sem consentimento)
        if beneficence["score"] > 0.6 and autonomy["autonomy_violations"] > 0:
            conflicts.append({
                "type": "beneficence_vs_autonomy",
                "description": "Ação visa beneficiar mas viola autonomia (paternalismo)",
                "severity": autonomy["autonomy_violations"] * 0.3
            })
        
        # Conflito 3: Justiça vs Beneficência
        # (distribuir equally vs maximizar bem total)
        if justice["disparity"] > 1.0 and beneficence["score"] > 0.7:
            conflicts.append({
                "type": "justice_vs_beneficence",
                "description": "Maximiza benefício mas distribui desigualmente",
                "severity": justice["disparity"] * 0.1
            })
        
        return conflicts
    
    def _adjust_weights_by_context(
        self,
        plan: ActionPlan,
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Ajusta pesos dos princípios baseado em contexto.
        
        Exemplo: Em emergência, não-maleficência pode ter peso maior.
        """
        weights = self.DEFAULT_WEIGHTS.copy()
        
        # Contexto: Emergência
        if plan.urgency > 0.8:
            weights["non_maleficence"] += 0.2  # Evitar dano é crítico
            weights["beneficence"] += 0.1  # Agir rápido para ajudar
        
        # Contexto: Vulneráveis envolvidos
        vulnerable_count = sum(1 for s in plan.stakeholders if s.vulnerability_level > 0.7)
        if vulnerable_count > 0:
            weights["autonomy"] += vulnerable_count * 0.1  # Proteger autonomia de vulneráveis
            weights["justice"] += vulnerable_count * 0.05  # Justiça compensatória
        
        # Contexto: Alto risco
        if plan.risk_level > 0.7:
            weights["non_maleficence"] += 0.3  # Primazia de não causar dano
        
        return weights
    
    def _calculate_aggregate(
        self,
        beneficence: Dict[str, Any],
        non_maleficence: Dict[str, Any],
        autonomy: Dict[str, Any],
        justice: Dict[str, Any],
        weights: Dict[str, float]
    ) -> float:
        """Calcula score agregado ponderado."""
        weighted_sum = (
            beneficence["score"] * weights["beneficence"] +
            non_maleficence["score"] * weights["non_maleficence"] +
            autonomy["score"] * weights["autonomy"] +
            justice["score"] * weights["justice"]
        )
        
        total_weight = sum(weights.values())
        
        return weighted_sum / total_weight
    
    def _generate_reasoning(
        self,
        beneficence: Dict[str, Any],
        non_maleficence: Dict[str, Any],
        autonomy: Dict[str, Any],
        justice: Dict[str, Any],
        conflicts: List[Dict[str, Any]],
        weights: Dict[str, float],
        aggregate_score: float
    ) -> str:
        """Gera explicação human-readable."""
        parts = [
            f"AVALIAÇÃO PRINCIPIALISTA (Score: {aggregate_score:.2f})",
            "",
            "OS 4 PRINCÍPIOS:"
        ]
        
        parts.append(f"  1. BENEFICÊNCIA: {beneficence['score']:.2f} [peso: {weights['beneficence']:.1f}]")
        parts.append(f"     {beneficence['reasoning']}")
        
        parts.append(f"  2. NÃO-MALEFICÊNCIA: {non_maleficence['score']:.2f} [peso: {weights['non_maleficence']:.1f}]")
        parts.append(f"     {non_maleficence['reasoning']}")
        
        parts.append(f"  3. AUTONOMIA: {autonomy['score']:.2f} [peso: {weights['autonomy']:.1f}]")
        parts.append(f"     {autonomy['reasoning']}")
        
        parts.append(f"  4. JUSTIÇA: {justice['score']:.2f} [peso: {weights['justice']:.1f}]")
        parts.append(f"     {justice['reasoning']}")
        
        if conflicts:
            parts.append("")
            parts.append("⚠️ CONFLITOS DETECTADOS ENTRE PRINCÍPIOS:")
            for conflict in conflicts:
                parts.append(f"  • {conflict['type']}: {conflict['description']} (severidade: {conflict['severity']:.2f})")
            parts.append("")
            parts.append("Conflitos resolvidos por balanceamento contextual (ajuste de pesos).")
        
        parts.append("")
        if aggregate_score >= self.APPROVAL_THRESHOLD:
            parts.append("CONCLUSÃO: Ação respeita princípios bioéticos fundamentais. APROVAÇÃO.")
        else:
            parts.append("CONCLUSÃO: Ação viola princípios bioéticos fundamentais. REJEIÇÃO.")
        
        return "\n".join(parts)
