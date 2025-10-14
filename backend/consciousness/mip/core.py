"""
Process Integrity Engine - Core do MIP
Orquestra validação ética multi-framework
"""

import time
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from .models import (
    ActionPlan,
    EthicalVerdict,
    VerdictStatus,
    FrameworkScore,
    AuditTrailEntry
)
from .frameworks import (
    KantianDeontology,
    UtilitarianCalculus,
    VirtueEthics,
    Principialism
)
from .resolver import ConflictResolver


class ProcessIntegrityEngine:
    """
    Motor de Integridade Processual - Coração do Sistema Ético MAXIMUS.
    
    RESPONSABILIDADE:
    Validar TODOS os planos de ação contra múltiplos frameworks éticos
    antes de permitir execução.
    
    FILOSOFIA:
    "O caminho importa tanto quanto o destino."
    Não basta alcançar bons resultados - os MEIOS devem ser éticos.
    
    PROCESSO:
    1. Recebe ActionPlan
    2. Avalia em paralelo: Kant, Mill, Aristóteles, Principialismo
    3. Resolve conflitos via ConflictResolver
    4. Emite EthicalVerdict vinculante
    5. Registra tudo em AuditTrail
    """
    
    def __init__(self):
        """Inicializa engine e frameworks."""
        # Instancia frameworks
        self.kantian = KantianDeontology()
        self.utilitarian = UtilitarianCalculus()
        self.virtue = VirtueEthics()
        self.principialism = Principialism()
        
        # Resolver de conflitos
        self.resolver = ConflictResolver()
        
        # Audit trail (em produção, seria persistido)
        self.audit_trail: List[AuditTrailEntry] = []
        
        # Estatísticas
        self.stats = {
            "total_evaluations": 0,
            "approved": 0,
            "rejected": 0,
            "escalated": 0,
            "vetoed": 0
        }
    
    def evaluate(self, plan: ActionPlan) -> EthicalVerdict:
        """
        Avalia um plano de ação completo.
        
        Este é o ponto de entrada principal do MIP.
        TODO plano de ação gerado por MAXIMUS deve passar por aqui.
        
        Args:
            plan: ActionPlan a ser validado
            
        Returns:
            EthicalVerdict com decisão vinculante
            
        Raises:
            ValueError: se plano é inválido
        """
        start_time = time.time()
        
        # Valida plano básico
        self._validate_plan_structure(plan)
        
        # Cria veredito base
        verdict = EthicalVerdict(
            plan_id=plan.id,
            evaluated_at=datetime.utcnow()
        )
        
        try:
            # FASE 1: Avaliação por cada framework
            print(f"[MIP] Avaliando plano '{plan.name}' (ID: {plan.id})")
            
            # Kant (deontologia - pode vetar)
            print("[MIP]   → Kant (Deontologia)...")
            verdict.kantian_score = self.kantian.evaluate(plan)
            
            # Se Kant vetou, interrompe aqui
            if verdict.kantian_score.veto:
                verdict.status = VerdictStatus.REJECTED
                verdict.summary = "Plano rejeitado por veto Kantiano"
                verdict.detailed_reasoning = verdict.kantian_score.reasoning
                self.stats["vetoed"] += 1
                self.stats["rejected"] += 1
                self._finalize_verdict(verdict, start_time, plan)
                return verdict
            
            # Mill (utilitarismo)
            print("[MIP]   → Mill (Utilitarismo)...")
            verdict.utilitarian_score = self.utilitarian.evaluate(plan)
            
            # Aristóteles (virtudes)
            print("[MIP]   → Aristóteles (Virtudes)...")
            verdict.virtue_score = self.virtue.evaluate(plan)
            
            # Principialismo (bioética)
            print("[MIP]   → Principialismo (Bioética)...")
            verdict.principialism_score = self.principialism.evaluate(plan)
            
            # FASE 2: Resolução de conflitos
            print("[MIP]   → Resolvendo conflitos...")
            resolution = self.resolver.resolve(
                plan,
                verdict.kantian_score,
                verdict.utilitarian_score,
                verdict.virtue_score,
                verdict.principialism_score
            )
            
            # FASE 3: Finaliza veredito
            verdict.status = resolution["status"]
            verdict.aggregate_score = resolution["aggregate_score"]
            verdict.confidence = resolution["confidence"]
            verdict.conflicts_detected = resolution["conflicts"]
            verdict.detailed_reasoning = resolution["reasoning"]
            
            # Summary baseado no status
            verdict.summary = self._generate_summary(verdict, resolution)
            
            # Se escalado, marca para revisão humana
            if verdict.status in [VerdictStatus.ESCALATED, VerdictStatus.REQUIRES_HUMAN]:
                verdict.requires_human_review = True
                verdict.escalation_reason = resolution.get("escalation_reason")
                self.stats["escalated"] += 1
            elif verdict.status == VerdictStatus.APPROVED:
                self.stats["approved"] += 1
            else:
                self.stats["rejected"] += 1
            
            self._finalize_verdict(verdict, start_time, plan)
            
        except Exception as e:
            # Em caso de erro, escala para humano por segurança
            verdict.status = VerdictStatus.ESCALATED
            verdict.requires_human_review = True
            verdict.escalation_reason = f"Erro durante avaliação: {str(e)}"
            verdict.summary = "Erro interno - requer revisão humana"
            self.stats["escalated"] += 1
            
            self._finalize_verdict(verdict, start_time, plan)
            
            print(f"[MIP] ⚠️ ERRO durante avaliação: {e}")
        
        return verdict
    
    def _validate_plan_structure(self, plan: ActionPlan) -> None:
        """
        Valida estrutura básica do plano.
        
        Raises:
            ValueError: se plano inválido
        """
        if not plan.steps:
            raise ValueError("ActionPlan deve ter pelo menos um step")
        
        if not plan.name:
            raise ValueError("ActionPlan deve ter nome")
        
        if not plan.description:
            raise ValueError("ActionPlan deve ter descrição")
        
        # Valida IDs únicos
        step_ids = [s.id for s in plan.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("ActionPlan contém steps com IDs duplicados")
    
    def _finalize_verdict(
        self,
        verdict: EthicalVerdict,
        start_time: float,
        plan: ActionPlan
    ) -> None:
        """Finaliza veredito com metadata e audit trail."""
        # Timing
        duration_ms = (time.time() - start_time) * 1000
        verdict.evaluation_duration_ms = duration_ms
        
        # Estatísticas
        self.stats["total_evaluations"] += 1
        
        # Audit trail
        audit_entry = AuditTrailEntry(
            plan_id=plan.id,
            verdict_id=verdict.id,
            plan_snapshot=self._plan_to_dict(plan),
            verdict_snapshot=verdict.to_dict(),
            frameworks_used=[
                self.kantian.name,
                self.utilitarian.name,
                self.virtue.name,
                self.principialism.name
            ]
        )
        self.audit_trail.append(audit_entry)
        
        # Log
        status_emoji = {
            VerdictStatus.APPROVED: "✅",
            VerdictStatus.REJECTED: "❌",
            VerdictStatus.ESCALATED: "⚠️",
            VerdictStatus.REQUIRES_HUMAN: "👤"
        }
        emoji = status_emoji.get(verdict.status, "❓")
        
        print(f"[MIP] {emoji} VEREDITO: {verdict.status.value.upper()}")
        score_str = f"{verdict.aggregate_score:.3f}" if verdict.aggregate_score is not None else "N/A"
        print(f"[MIP]    Score: {score_str}")
        print(f"[MIP]    Confidence: {verdict.confidence:.3f}")
        print(f"[MIP]    Duração: {duration_ms:.1f}ms")
        
        if verdict.conflicts_detected:
            print(f"[MIP]    Conflitos: {len(verdict.conflicts_detected)}")
    
    def _generate_summary(
        self,
        verdict: EthicalVerdict,
        resolution: dict
    ) -> str:
        """Gera summary human-readable do veredito."""
        if verdict.status == VerdictStatus.APPROVED:
            return (
                f"Plano APROVADO (score: {verdict.aggregate_score:.2f}, "
                f"confidence: {verdict.confidence:.2f}). "
                f"Todos os frameworks éticos concordam ou conflitos resolvidos satisfatoriamente."
            )
        elif verdict.status == VerdictStatus.REJECTED:
            if verdict.kantian_score and verdict.kantian_score.veto:
                return "Plano REJEITADO por veto Kantiano (violação categórica)."
            else:
                return (
                    f"Plano REJEITADO (score: {verdict.aggregate_score:.2f}). "
                    f"Frameworks éticos identificaram problemas significativos."
                )
        elif verdict.status in [VerdictStatus.ESCALATED, VerdictStatus.REQUIRES_HUMAN]:
            reason = resolution.get("escalation_reason", "Motivo não especificado")
            return f"Plano ESCALADO para revisão humana. Razão: {reason}"
        else:
            return "Status desconhecido"
    
    def _plan_to_dict(self, plan: ActionPlan) -> dict:
        """Serializa plano para audit trail."""
        return {
            "id": str(plan.id),
            "name": plan.name,
            "description": plan.description,
            "category": plan.category.value,
            "steps": [
                {
                    "id": str(s.id),
                    "sequence": s.sequence_number,
                    "description": s.description,
                    "action_type": s.action_type
                }
                for s in plan.steps
            ],
            "stakeholders": [
                {
                    "id": s.id,
                    "type": s.type.value,
                    "impact": s.impact_magnitude,
                    "autonomy_respected": s.autonomy_respected,
                    "vulnerability": s.vulnerability_level
                }
                for s in plan.stakeholders
            ],
            "urgency": plan.urgency,
            "risk_level": plan.risk_level,
            "novel_situation": plan.novel_situation,
            "created_at": plan.created_at.isoformat()
        }
    
    def get_statistics(self) -> dict:
        """Retorna estatísticas de uso do MIP."""
        total = self.stats["total_evaluations"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "approval_rate": self.stats["approved"] / total,
            "rejection_rate": self.stats["rejected"] / total,
            "escalation_rate": self.stats["escalated"] / total,
            "veto_rate": self.stats["vetoed"] / total
        }
    
    def get_audit_trail(self, plan_id: Optional[str] = None) -> List[AuditTrailEntry]:
        """
        Retorna audit trail completo ou filtrado por plano.
        
        Args:
            plan_id: Se especificado, retorna apenas entries deste plano
            
        Returns:
            Lista de AuditTrailEntry
        """
        if plan_id is None:
            return self.audit_trail
        
        return [
            entry for entry in self.audit_trail
            if str(entry.plan_id) == plan_id
        ]
