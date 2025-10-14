"""
Conflict Resolver - Sistema de resolução de conflitos entre frameworks éticos
Core decision engine do MIP
"""

from typing import List, Dict, Any, Optional
from .models import FrameworkScore, VerdictStatus, ActionPlan


class ConflictResolver:
    """
    Resolve conflitos quando frameworks éticos discordam.
    
    FILOSOFIA:
    Não há "resposta correta" única em ética. Este resolver implementa
    meta-regras para harmonizar diferentes perspectivas éticas.
    
    HIERARQUIA DE PRECEDÊNCIA:
    1. VETO Kantiano tem precedência absoluta (deontologia)
    2. Se sem veto, agrega scores com pesos contextuais
    3. Thresholds determinam approve/reject/escalate
    4. Novel situations ou ambiguidade alta → escala para humano
    """
    
    # Thresholds de decisão
    STRONG_APPROVAL_THRESHOLD = 0.80  # Aprovação automática forte
    APPROVAL_THRESHOLD = 0.65  # Aprovação com confiança moderada
    REJECTION_THRESHOLD = 0.40  # Abaixo disso = rejeição
    # Entre 0.40 e 0.65 = zona de ambiguidade (escala)
    
    # Pesos default dos frameworks (podem ser ajustados por contexto)
    DEFAULT_WEIGHTS = {
        "kantian": 1.4,  # Maior peso: deontologia protege princípios fundamentais
        "utilitarian": 1.0,
        "virtue": 0.9,
        "principialism": 1.1
    }
    
    def resolve(
        self,
        plan: ActionPlan,
        kantian: FrameworkScore,
        utilitarian: FrameworkScore,
        virtue: FrameworkScore,
        principialism: FrameworkScore
    ) -> Dict[str, Any]:
        """
        Resolve conflitos e produz decisão final.
        
        Args:
            plan: Plano sendo avaliado
            kantian, utilitarian, virtue, principialism: Scores dos frameworks
            
        Returns:
            Dict com:
            - status: VerdictStatus final
            - aggregate_score: Score agregado (se aplicável)
            - confidence: Confiança na decisão
            - conflicts: Lista de conflitos detectados
            - reasoning: Explicação da resolução
        """
        # REGRA 1: VETO KANTIANO
        if kantian.veto:
            return {
                "status": VerdictStatus.REJECTED,
                "aggregate_score": None,
                "confidence": 1.0,
                "conflicts": ["Veto Kantiano acionado"],
                "reasoning": self._explain_kantian_veto(kantian),
                "escalation_reason": None
            }
        
        # REGRA 2: Detecta conflitos entre frameworks
        conflicts = self._detect_conflicts(kantian, utilitarian, virtue, principialism)
        
        # REGRA 3: Ajusta pesos por contexto
        weights = self._adjust_weights_by_context(plan, conflicts)
        
        # REGRA 4: Calcula score agregado
        aggregate_result = self._aggregate_scores(
            kantian, utilitarian, virtue, principialism, weights
        )
        
        # REGRA 5: Aplica lógica de decisão
        decision = self._make_decision(
            aggregate_result["score"],
            aggregate_result["confidence"],
            conflicts,
            plan
        )
        
        # REGRA 6: Gera explicação
        reasoning = self._generate_resolution_reasoning(
            kantian, utilitarian, virtue, principialism,
            weights, aggregate_result, conflicts, decision
        )
        
        return {
            "status": decision["status"],
            "aggregate_score": aggregate_result["score"],
            "confidence": aggregate_result["confidence"],
            "conflicts": conflicts,
            "reasoning": reasoning,
            "escalation_reason": decision.get("escalation_reason")
        }
    
    def _detect_conflicts(
        self,
        kantian: FrameworkScore,
        utilitarian: FrameworkScore,
        virtue: FrameworkScore,
        principialism: FrameworkScore
    ) -> List[str]:
        """
        Detecta quando frameworks discordam significativamente.
        
        Conflito = diferença de score > 0.3 entre qualquer par.
        """
        conflicts = []
        
        scores = {
            "Kant": kantian.score,
            "Mill": utilitarian.score,
            "Aristóteles": virtue.score,
            "Principialismo": principialism.score
        }
        
        # Remove None (veto já foi tratado antes)
        scores = {k: v for k, v in scores.items() if v is not None}
        
        # Compara todos os pares
        frameworks = list(scores.keys())
        for i in range(len(frameworks)):
            for j in range(i + 1, len(frameworks)):
                fw1, fw2 = frameworks[i], frameworks[j]
                diff = abs(scores[fw1] - scores[fw2])
                
                if diff > 0.3:
                    if scores[fw1] > scores[fw2]:
                        conflicts.append(
                            f"{fw1} aprova fortemente ({scores[fw1]:.2f}) mas "
                            f"{fw2} é mais cético ({scores[fw2]:.2f}) - diferença: {diff:.2f}"
                        )
                    else:
                        conflicts.append(
                            f"{fw2} aprova fortemente ({scores[fw2]:.2f}) mas "
                            f"{fw1} é mais cético ({scores[fw1]:.2f}) - diferença: {diff:.2f}"
                        )
        
        # Conflito especial: Kant aprova mas utilitarismo reprova
        # (ou vice-versa) - conflito filosófico profundo
        if kantian.score is not None and utilitarian.score is not None:
            if kantian.score > 0.7 and utilitarian.score < 0.4:
                conflicts.append(
                    "CONFLITO FILOSÓFICO PROFUNDO: Kant aprova (deontologia) mas "
                    "Mill reprova (consequencialismo) - ação é permissível mas não benéfica"
                )
            elif kantian.score < 0.4 and utilitarian.score > 0.7:
                conflicts.append(
                    "CONFLITO FILOSÓFICO PROFUNDO: Mill aprova (fins) mas "
                    "Kant reprova (meios) - ação é benéfica mas usa meios questionáveis"
                )
        
        return conflicts
    
    def _adjust_weights_by_context(
        self,
        plan: ActionPlan,
        conflicts: List[str]
    ) -> Dict[str, float]:
        """
        Ajusta pesos dos frameworks baseado em contexto do plano.
        
        Exemplos:
        - Emergência: utilitarismo ganha peso (consequências importam mais)
        - Vulneráveis: Kant ganha peso (proteger autonomia)
        - Ambiguidade: virtue ethics ganha peso (sabedoria prática)
        """
        weights = self.DEFAULT_WEIGHTS.copy()
        
        # CONTEXTO 1: Emergência
        if plan.urgency > 0.8:
            weights["utilitarian"] += 0.3  # Consequências são urgentes
            weights["virtue"] += 0.1  # Phronesis (sabedoria prática)
        
        # CONTEXTO 2: Vulneráveis envolvidos
        vulnerable_count = sum(
            1 for s in plan.stakeholders 
            if s.vulnerability_level > 0.7
        )
        if vulnerable_count > 0:
            weights["kantian"] += vulnerable_count * 0.15  # Proteger dignidade
            weights["principialism"] += vulnerable_count * 0.1  # Não-maleficência
        
        # CONTEXTO 3: Alto risco
        if plan.risk_level > 0.7:
            weights["kantian"] += 0.2  # Princípios em situações arriscadas
            weights["principialism"] += 0.15  # Não-maleficência crítica
        
        # CONTEXTO 4: Situação novel
        if plan.novel_situation:
            weights["virtue"] += 0.25  # Phronesis para situações sem precedente
        
        # CONTEXTO 5: Muitos conflitos
        if len(conflicts) > 2:
            weights["principialism"] += 0.2  # Balanceamento de princípios
        
        return weights
    
    def _aggregate_scores(
        self,
        kantian: FrameworkScore,
        utilitarian: FrameworkScore,
        virtue: FrameworkScore,
        principialism: FrameworkScore,
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calcula score agregado ponderado.
        
        Returns:
            Dict com 'score' e 'confidence'
        """
        # Coleta scores e confidences
        frameworks = {
            "kantian": (kantian.score, kantian.confidence, weights["kantian"]),
            "utilitarian": (utilitarian.score, utilitarian.confidence, weights["utilitarian"]),
            "virtue": (virtue.score, virtue.confidence, weights["virtue"]),
            "principialism": (principialism.score, principialism.confidence, weights["principialism"])
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        confidence_product = 1.0
        
        for fw_name, (score, confidence, weight) in frameworks.items():
            if score is not None:  # Ignora None (veto já tratado)
                weighted_sum += score * weight
                total_weight += weight
                confidence_product *= confidence  # Confidence agregada é produto
        
        aggregate_score = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Confidence agregada: produto das confidences individuais
        # Penaliza se há baixa confidence em algum framework
        aggregate_confidence = confidence_product ** (1/4)  # Média geométrica
        
        return {
            "score": aggregate_score,
            "confidence": aggregate_confidence,
            "weights_used": weights
        }
    
    def _make_decision(
        self,
        aggregate_score: float,
        confidence: float,
        conflicts: List[str],
        plan: ActionPlan
    ) -> Dict[str, Any]:
        """
        Aplica lógica de decisão baseada em score, confidence e contexto.
        
        Returns:
            Dict com 'status' e opcionalmente 'escalation_reason'
        """
        # REGRA: Confidence muito baixa → escala
        if confidence < 0.5:
            return {
                "status": VerdictStatus.ESCALATED,
                "escalation_reason": f"Confiança insuficiente ({confidence:.2f}) para decisão autônoma"
            }
        
        # REGRA: Situação novel + score ambíguo → escala
        if plan.novel_situation and (0.45 <= aggregate_score <= 0.70):
            return {
                "status": VerdictStatus.REQUIRES_HUMAN,
                "escalation_reason": "Situação sem precedente requer validação humana"
            }
        
        # REGRA: Muitos conflitos + score ambíguo → escala
        if len(conflicts) > 3 and (0.40 <= aggregate_score <= 0.65):
            return {
                "status": VerdictStatus.ESCALATED,
                "escalation_reason": f"Conflitos éticos múltiplos ({len(conflicts)}) impedem decisão clara"
            }
        
        # REGRA: Score alto + alta confidence → aprova
        if aggregate_score >= self.STRONG_APPROVAL_THRESHOLD and confidence >= 0.8:
            return {"status": VerdictStatus.APPROVED}
        
        # REGRA: Score moderado + confidence ok → aprova com cautela
        if aggregate_score >= self.APPROVAL_THRESHOLD and confidence >= 0.65:
            return {"status": VerdictStatus.APPROVED}
        
        # REGRA: Score baixo → rejeita
        if aggregate_score < self.REJECTION_THRESHOLD:
            return {"status": VerdictStatus.REJECTED}
        
        # ZONA DE AMBIGUIDADE (0.40 - 0.65): depende de confidence
        if confidence >= 0.75:
            # Alta confidence na ambiguidade → conservador (rejeita)
            return {
                "status": VerdictStatus.REJECTED,
                "escalation_reason": f"Score ambíguo ({aggregate_score:.2f}) - princípio da precaução"
            }
        else:
            # Baixa confidence → escala
            return {
                "status": VerdictStatus.ESCALATED,
                "escalation_reason": f"Score ambíguo ({aggregate_score:.2f}) + confidence moderada - requer revisão humana"
            }
    
    def _explain_kantian_veto(self, kantian: FrameworkScore) -> str:
        """Explica por que veto Kantiano foi acionado."""
        return (
            f"═══════════════════════════════════════════════\n"
            f"⛔ VETO KANTIANO ACIONADO ⛔\n"
            f"═══════════════════════════════════════════════\n"
            f"\n"
            f"Ação REJEITADA por violação categórica de princípios deontológicos.\n"
            f"\n"
            f"{kantian.reasoning}\n"
            f"\n"
            f"Este veto é ABSOLUTO e substitui qualquer consideração consequencialista.\n"
            f"Nenhuma quantidade de bem agregado pode justificar violação de princípios fundamentais.\n"
            f"\n"
            f"\"Aja de tal maneira que uses a humanidade, tanto na tua pessoa como\n"
            f"na pessoa de qualquer outro, sempre e simultaneamente como fim e nunca\n"
            f"simplesmente como meio.\" - Immanuel Kant\n"
            f"═══════════════════════════════════════════════"
        )
    
    def _generate_resolution_reasoning(
        self,
        kantian: FrameworkScore,
        utilitarian: FrameworkScore,
        virtue: FrameworkScore,
        principialism: FrameworkScore,
        weights: Dict[str, float],
        aggregate_result: Dict[str, Any],
        conflicts: List[str],
        decision: Dict[str, Any]
    ) -> str:
        """Gera explicação completa da resolução."""
        parts = [
            "═══════════════════════════════════════════════",
            "RESOLUÇÃO DE CONFLITOS ÉTICOS",
            "═══════════════════════════════════════════════",
            "",
            "SCORES DOS FRAMEWORKS:"
        ]
        
        # Lista scores
        parts.append(f"  • Kant (Deontologia):      {kantian.score if kantian.score else 'VETO':>6} [peso: {weights['kantian']:.2f}] [conf: {kantian.confidence:.2f}]")
        parts.append(f"  • Mill (Utilitarismo):     {utilitarian.score:>6.2f} [peso: {weights['utilitarian']:.2f}] [conf: {utilitarian.confidence:.2f}]")
        parts.append(f"  • Aristóteles (Virtudes):  {virtue.score:>6.2f} [peso: {weights['virtue']:.2f}] [conf: {virtue.confidence:.2f}]")
        parts.append(f"  • Principialismo (Bio):    {principialism.score:>6.2f} [peso: {weights['principialism']:.2f}] [conf: {principialism.confidence:.2f}]")
        
        parts.append("")
        parts.append(f"SCORE AGREGADO: {aggregate_result['score']:.3f}")
        parts.append(f"CONFIANÇA AGREGADA: {aggregate_result['confidence']:.3f}")
        
        # Conflitos
        if conflicts:
            parts.append("")
            parts.append("⚠️ CONFLITOS DETECTADOS:")
            for i, conflict in enumerate(conflicts, 1):
                parts.append(f"  {i}. {conflict}")
        
        # Ajustes de peso
        if any(w != self.DEFAULT_WEIGHTS[k] for k, w in weights.items()):
            parts.append("")
            parts.append("AJUSTES CONTEXTUAIS DE PESO APLICADOS:")
            for fw, weight in weights.items():
                default = self.DEFAULT_WEIGHTS[fw]
                if weight != default:
                    diff = weight - default
                    parts.append(f"  • {fw}: {default:.2f} → {weight:.2f} ({diff:+.2f})")
        
        # Decisão final
        parts.append("")
        parts.append("═══════════════════════════════════════════════")
        parts.append(f"DECISÃO FINAL: {decision['status'].value.upper()}")
        
        if decision.get("escalation_reason"):
            parts.append(f"RAZÃO: {decision['escalation_reason']}")
        
        parts.append("═══════════════════════════════════════════════")
        
        return "\n".join(parts)
