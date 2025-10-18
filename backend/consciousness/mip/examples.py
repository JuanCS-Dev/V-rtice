"""
MIP Usage Examples - Demonstra como usar o Motor de Integridade Processual
"""

from .core import ProcessIntegrityEngine
from .models import (
    ActionPlan,
    ActionStep,
    Stakeholder,
    ActionCategory,
    StakeholderType,
    Effect,
    Precondition
)


def example_1_simple_defensive_action():
    """
    EXEMPLO 1: Ação defensiva simples - deve ser APROVADA
    Cenário: Bloquear ataque DDoS
    """
    print("\n" + "="*60)
    print("EXEMPLO 1: Ação Defensiva (Bloquear DDoS)")
    print("="*60)
    
    # Cria stakeholders
    attacker = Stakeholder(
        id="attacker-001",
        type=StakeholderType.HUMAN_INDIVIDUAL,
        description="Atacante DDoS",
        impact_magnitude=-0.3,  # Levemente prejudicado (bloqueado)
        autonomy_respected=True,  # Não invadimos sistema dele
        vulnerability_level=0.1
    )
    
    protected_users = Stakeholder(
        id="users-001",
        type=StakeholderType.HUMAN_GROUP,
        description="Usuários do serviço protegido",
        impact_magnitude=0.9,  # Altamente beneficiados
        autonomy_respected=True,
        vulnerability_level=0.6  # Dependem do serviço
    )
    
    # Cria steps
    step1 = ActionStep(
        sequence_number=1,
        description="Identificar source IPs do ataque",
        action_type="analysis",
        preconditions=[
            Precondition(
                description="Tráfego anômalo detectado",
                required=True,
                current_state=True
            )
        ],
        effects=[
            Effect(
                description="IPs maliciosos identificados",
                probability=0.95,
                magnitude=0.5,
                duration_seconds=3600,
                reversible=True,
                affected_stakeholders=["attacker-001"]
            )
        ],
        treats_as_means_only=False,
        respects_autonomy=True
    )
    
    step2 = ActionStep(
        sequence_number=2,
        description="Aplicar firewall rules para bloquear IPs",
        action_type="defensive",
        effects=[
            Effect(
                description="Tráfego malicioso bloqueado",
                probability=0.98,
                magnitude=0.9,
                duration_seconds=86400,  # 24h
                reversible=True,
                affected_stakeholders=["users-001"]
            ),
            Effect(
                description="Atacante não consegue alcançar target",
                probability=0.98,
                magnitude=-0.3,
                duration_seconds=86400,
                reversible=True,
                affected_stakeholders=["attacker-001"]
            )
        ],
        treats_as_means_only=False,
        respects_autonomy=True
    )
    
    # Cria plano
    plan = ActionPlan(
        name="Block DDoS Attack",
        description="Identificar e bloquear source de ataque DDoS para proteger serviço",
        category=ActionCategory.DEFENSIVE,
        steps=[step1, step2],
        stakeholders=[attacker, protected_users],
        urgency=0.8,  # Alta urgência
        risk_level=0.3,  # Baixo risco
        reversibility=True,
        novel_situation=False,
        agent_justification="Ataque em andamento ameaça disponibilidade do serviço",
        expected_benefit="Restaurar disponibilidade e proteger usuários legítimos"
    )
    
    # Avalia
    engine = ProcessIntegrityEngine()
    verdict = engine.evaluate(plan)
    
    print(f"\n{verdict.detailed_reasoning}")
    print(f"\nSUMMARY: {verdict.summary}")
    
    return verdict


def example_2_paternalistic_intervention():
    """
    EXEMPLO 2: Intervenção paternalista - deve ser REJEITADA ou ESCALADA
    Cenário: Forçar backup de dados "pelo bem do usuário" sem consentimento
    """
    print("\n" + "="*60)
    print("EXEMPLO 2: Intervenção Paternalista (CONFLITO ÉTICO)")
    print("="*60)
    
    # Stakeholder com autonomia violada
    user = Stakeholder(
        id="user-001",
        type=StakeholderType.HUMAN_INDIVIDUAL,
        description="Usuário que não quer backup automático",
        impact_magnitude=0.6,  # Benefício potencial
        autonomy_respected=False,  # ⚠️ AUTONOMIA VIOLADA
        vulnerability_level=0.3
    )
    
    # Step que força ação
    step = ActionStep(
        sequence_number=1,
        description="Forçar backup de dados do usuário sem consentimento",
        action_type="intervention",
        treats_as_means_only=False,  # Intenção é boa
        respects_autonomy=False,  # ⚠️ MAS NÃO RESPEITA AUTONOMIA
        effects=[
            Effect(
                description="Dados protegidos contra perda",
                probability=0.95,
                magnitude=0.6,
                duration_seconds=31536000,  # 1 ano
                reversible=True,
                affected_stakeholders=["user-001"]
            )
        ]
    )
    
    plan = ActionPlan(
        name="Force User Backup",
        description="Forçar backup de dados para proteger usuário",
        category=ActionCategory.INTERVENTION,
        steps=[step],
        stakeholders=[user],
        urgency=0.3,
        risk_level=0.2,
        reversibility=True,
        novel_situation=False,
        agent_justification="Usuário não faz backups e pode perder dados importantes",
        expected_benefit="Proteger dados do usuário contra perda"
    )
    
    engine = ProcessIntegrityEngine()
    verdict = engine.evaluate(plan)
    
    print(f"\n{verdict.detailed_reasoning}")
    print(f"\nSUMMARY: {verdict.summary}")
    
    return verdict


def example_3_utilitarian_dilemma():
    """
    EXEMPLO 3: Dilema utilitário - beneficia muitos mas prejudica poucos
    Cenário: Redirecionar recursos de usuários premium para manter serviço gratuito
    """
    print("\n" + "="*60)
    print("EXEMPLO 3: Dilema Utilitário (Trolley Problem)")
    print("="*60)
    
    # Muitos beneficiados
    free_users = Stakeholder(
        id="free-users",
        type=StakeholderType.HUMAN_GROUP,
        description="1000 usuários gratuitos (servico mantido)",
        impact_magnitude=0.7,
        autonomy_respected=True,
        vulnerability_level=0.8  # Dependem do serviço gratuito
    )
    
    # Poucos prejudicados
    premium_users = Stakeholder(
        id="premium-users",
        type=StakeholderType.HUMAN_GROUP,
        description="10 usuários premium (performance degradada)",
        impact_magnitude=-0.6,  # Prejudicados significativamente
        autonomy_respected=True,  # Mas foi informado (termos de serviço)
        vulnerability_level=0.2
    )
    
    step = ActionStep(
        sequence_number=1,
        description="Realocar recursos de premium para gratuito temporariamente",
        action_type="reallocation",
        effects=[
            Effect(
                description="Serviço gratuito mantido estável",
                probability=0.95,
                magnitude=0.7,
                duration_seconds=86400,
                reversible=True,
                affected_stakeholders=["free-users"]
            ),
            Effect(
                description="Performance premium degradada",
                probability=0.98,
                magnitude=-0.6,
                duration_seconds=86400,
                reversible=True,
                affected_stakeholders=["premium-users"]
            )
        ],
        treats_as_means_only=False,
        respects_autonomy=True
    )
    
    plan = ActionPlan(
        name="Resource Reallocation for Greater Good",
        description="Sacrificar QoS de poucos premium para manter serviço de muitos gratuitos",
        category=ActionCategory.PROACTIVE,
        steps=[step],
        stakeholders=[free_users, premium_users],
        urgency=0.7,
        risk_level=0.5,
        reversibility=True,
        novel_situation=False,
        agent_justification="Maximizar bem-estar total: 1000 beneficiados vs 10 prejudicados",
        expected_benefit="Maior felicidade agregada"
    )
    
    engine = ProcessIntegrityEngine()
    verdict = engine.evaluate(plan)
    
    print(f"\n{verdict.detailed_reasoning}")
    print(f"\nSUMMARY: {verdict.summary}")
    
    return verdict


def example_4_kantian_veto():
    """
    EXEMPLO 4: Violação Kantiana clara - deve receber VETO
    Cenário: Usar pessoa como isca sem consentimento
    """
    print("\n" + "="*60)
    print("EXEMPLO 4: Violação Kantiana (VETO ESPERADO)")
    print("="*60)
    
    # Pessoa instrumentalizada
    bait = Stakeholder(
        id="bait-001",
        type=StakeholderType.HUMAN_INDIVIDUAL,
        description="Pessoa usada como isca sem saber",
        impact_magnitude=-0.8,  # Muito prejudicada
        autonomy_respected=False,  # ⚠️ SEM CONSENTIMENTO
        vulnerability_level=0.9  # Alta vulnerabilidade
    )
    
    criminals = Stakeholder(
        id="criminals",
        type=StakeholderType.HUMAN_GROUP,
        description="Criminosos a serem capturados",
        impact_magnitude=-0.5,
        autonomy_respected=True,
        vulnerability_level=0.1
    )
    
    step = ActionStep(
        sequence_number=1,
        description="Expor pessoa vulnerável a criminosos para rastreá-los",
        action_type="deception",
        treats_as_means_only=True,  # ⚠️ TRATADA APENAS COMO MEIO
        respects_autonomy=False,  # ⚠️ SEM AUTONOMIA
        effects=[
            Effect(
                description="Pessoa exposta a perigo",
                probability=0.9,
                magnitude=-0.8,
                duration_seconds=3600,
                reversible=False,  # Trauma não reversível
                affected_stakeholders=["bait-001"]
            )
        ]
    )
    
    plan = ActionPlan(
        name="Use Human Bait",
        description="Usar pessoa como isca (sem consentimento) para capturar criminosos",
        category=ActionCategory.PROACTIVE,
        steps=[step],
        stakeholders=[bait, criminals],
        urgency=0.5,
        risk_level=0.9,
        reversibility=False,
        novel_situation=False,
        agent_justification="Capturar criminosos perigosos",
        expected_benefit="Sociedade mais segura"
    )
    
    engine = ProcessIntegrityEngine()
    verdict = engine.evaluate(plan)
    
    print(f"\n{verdict.detailed_reasoning}")
    print(f"\nSUMMARY: {verdict.summary}")
    
    return verdict


def run_all_examples():
    """Executa todos os exemplos."""
    print("\n" + "#"*60)
    print("# MIP - MOTOR DE INTEGRIDADE PROCESSUAL")
    print("# Demonstração de Casos de Uso")
    print("#"*60)
    
    verdicts = []
    
    # Exemplo 1: Aprovação esperada
    v1 = example_1_simple_defensive_action()
    verdicts.append(("Defesa DDoS", v1))
    
    # Exemplo 2: Conflito ético
    v2 = example_2_paternalistic_intervention()
    verdicts.append(("Paternalismo", v2))
    
    # Exemplo 3: Dilema utilitário
    v3 = example_3_utilitarian_dilemma()
    verdicts.append(("Dilema Utilitário", v3))
    
    # Exemplo 4: Veto Kantiano
    v4 = example_4_kantian_veto()
    verdicts.append(("Violação Kantiana", v4))
    
    # Summary
    print("\n" + "="*60)
    print("RESUMO DOS VEREDITOS")
    print("="*60)
    for name, v in verdicts:
        status_emoji = {
            "approved": "✅",
            "rejected": "❌",
            "escalated": "⚠️",
            "requires_human": "👤"
        }
        emoji = status_emoji.get(v.status.value, "❓")
        score_str = f"{v.aggregate_score:.2f}" if v.aggregate_score else "N/A"
        print(f"{emoji} {name:30} | Status: {v.status.value:15} | Score: {score_str}")
    
    print("\n" + "#"*60)


if __name__ == "__main__":
    run_all_examples()
