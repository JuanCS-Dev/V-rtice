"""
Exemplo de integração do Memory Consolidation Engine e HSAS
Maximus AI 3.0

Este arquivo demonstra como usar os dois sistemas finais em conjunto.
"""

import asyncio
import time

import numpy as np

from hsas_service import (
    Action,
    HybridSkillAcquisitionSystem,
    LearningMode,
    SkillPrimitiveType,
    State,
    Transition,
)
from memory_consolidation_service import MemoryConsolidationEngine


async def example_workflow():
    """
    Exemplo de workflow completo:
    1. Criar instâncias dos sistemas
    2. Simular detecção de ameaça
    3. HSAS seleciona e executa ação
    4. MCE armazena experiência
    5. Consolidação periódica
    """
    print("=" * 70)
    print("MAXIMUS AI 3.0 - EXEMPLO DE INTEGRAÇÃO")
    print("=" * 70)
    print()

    # ========================================================================
    # INICIALIZAÇÃO
    # ========================================================================
    print("🚀 Inicializando sistemas...")

    # Memory Consolidation Engine
    mce = MemoryConsolidationEngine(
        replay_buffer_size=10000,
        consolidation_interval_hours=1.0,  # Consolidar a cada 1h
        replay_batch_size=100,
    )

    # Hybrid Skill Acquisition System
    hsas = HybridSkillAcquisitionSystem(state_dim=5, action_dim=20, default_mode=LearningMode.HYBRID)

    # Aprender skills compostos
    await hsas.learn_skill(
        name="Malware Incident Response",
        description="Resposta completa a incidente de malware",
        primitive_sequence=[
            "isolate_host",
            "quarantine_file",
            "snapshot_vm",
            "scan_host",
            "extract_iocs",
            "alert_analyst",
        ],
    )

    await hsas.learn_skill(
        name="DDoS Mitigation",
        description="Mitigação de ataque DDoS",
        primitive_sequence=[
            "block_ip",
            "network_capture",
            "collect_logs",
            "escalate_incident",
        ],
    )

    print("✅ Sistemas inicializados")
    print(f"   MCE: Modo {mce.operational_mode.value}")
    print(f"   HSAS: {len(hsas.skills)} skills aprendidas")
    print()

    # ========================================================================
    # SIMULAÇÃO DE INCIDENTES
    # ========================================================================
    print("🎯 Simulando incidentes de segurança...")
    print()

    for episode in range(3):
        print(f"--- Episódio {episode + 1}: Ataque de Malware ---")

        # Criar estado de ameaça
        state = State(
            state_id=f"threat_{episode}",
            timestamp=time.time(),
            threat_level=np.random.uniform(0.7, 0.95),
            num_alerts=np.random.randint(50, 200),
            severity="high" if np.random.random() > 0.5 else "critical",
            source_type="external",
            confidence=np.random.uniform(0.8, 0.98),
            attack_type="malware",
        )

        print("📊 Estado detectado:")
        print(f"   Threat Level: {state.threat_level:.2f}")
        print(f"   Alerts: {state.num_alerts}")
        print(f"   Severity: {state.severity}")
        print(f"   Confidence: {state.confidence:.2f}")

        # Definir ações disponíveis
        available_actions = [
            Action(
                action_id=f"action_isolate_{episode}",
                action_type="isolate_host",
                primitive_type=SkillPrimitiveType.ISOLATION,
                parameters={"host": f"workstation-{episode}"},
                cost=5.0,
                risk=0.2,
            ),
            Action(
                action_id=f"action_block_{episode}",
                action_type="block_ip",
                primitive_type=SkillPrimitiveType.BLOCKING,
                parameters={"ip_address": f"192.168.1.{100 + episode}"},
                cost=1.0,
                risk=0.1,
            ),
            Action(
                action_id=f"action_quarantine_{episode}",
                action_type="quarantine_file",
                primitive_type=SkillPrimitiveType.CONTAINMENT,
                parameters={
                    "file_path": "/tmp/malware.exe",
                    "host": f"workstation-{episode}",
                },
                cost=2.0,
                risk=0.05,
            ),
        ]

        # HSAS seleciona ação
        selected_action, mode_used = await hsas.select_action(state, available_actions)

        print("🤖 HSAS Decisão:")
        print(f"   Modo: {mode_used}")
        print(f"   Ação: {selected_action.action_type}")
        print(f"   Parâmetros: {selected_action.parameters}")

        # Executar ação
        result = await hsas.execute_action(selected_action)
        print(f"⚡ Execução: {result.value}")

        # Simular estado resultante
        next_state = State(
            state_id=f"threat_{episode}_after",
            timestamp=time.time(),
            threat_level=max(0.0, state.threat_level - 0.3),
            num_alerts=max(0, state.num_alerts - 50),
            severity="medium" if result.value == "success" else state.severity,
            source_type="external",
            confidence=min(1.0, state.confidence + 0.05),
            attack_type="malware",
        )

        # Calcular recompensa
        if result.value == "success":
            reward = 10.0 * state.threat_level  # Maior recompensa para ameaças maiores
        else:
            reward = -5.0

        # Calcular TD error (simplificado)
        td_error = abs(reward - selected_action.cost)

        print(f"💰 Recompensa: {reward:.2f}")
        print(f"📈 TD Error: {td_error:.2f}")

        # Adicionar experiência ao MCE
        experience = mce.add_experience(
            state={
                "threat_level": state.threat_level,
                "num_alerts": state.num_alerts,
                "severity": state.severity,
                "confidence": state.confidence,
            },
            action=selected_action.action_type,
            reward=reward,
            next_state={
                "threat_level": next_state.threat_level,
                "num_alerts": next_state.num_alerts,
                "severity": next_state.severity,
                "confidence": next_state.confidence,
            },
            done=True,
            td_error=td_error,
            metadata={"episode": episode, "result": result.value},
        )

        print(f"🧠 Experiência armazenada: {experience.experience_id}")
        print(f"   Prioridade: {experience.priority.name}")

        # HSAS aprende da transição
        transition = Transition(
            transition_id=f"trans_{episode}",
            timestamp=time.time(),
            state=state,
            action=selected_action,
            next_state=next_state,
            reward=reward,
            done=True,
        )

        await hsas.learn_from_transition(transition)
        print("📚 HSAS aprendeu da transição")
        print()

    # ========================================================================
    # CONSOLIDAÇÃO DE MEMÓRIA
    # ========================================================================
    print("=" * 70)
    print("💤 INICIANDO CONSOLIDAÇÃO DE MEMÓRIA")
    print("=" * 70)
    print()

    # Forçar consolidação (ignorando intervalo)
    mce.last_consolidation = 0

    metrics = await mce.consolidate()

    print()
    print("=" * 70)
    print("📊 RESULTADOS DA CONSOLIDAÇÃO")
    print("=" * 70)
    print(f"Session ID: {metrics.session_id}")
    print(f"Duração: {metrics.end_time - metrics.start_time:.2f}s")
    print()
    print(f"Experiências replayadas: {metrics.experiences_replayed}")
    print(f"Consolidadas para LTM: {metrics.experiences_consolidated}")
    print(f"Padrões extraídos: {metrics.patterns_extracted}")
    print(f"Experiências sintéticas: {metrics.consolidation_types.get('pseudo_rehearsal', 0)}")
    print(f"Memórias podadas: {metrics.experiences_pruned}")
    print()
    print(f"TD Error antes: {metrics.avg_td_error_before:.4f}")
    print(f"TD Error depois: {metrics.avg_td_error_after:.4f}")
    print(f"Melhoria: {metrics.model_performance_delta:.4f}")
    print()

    # ========================================================================
    # ESTATÍSTICAS FINAIS
    # ========================================================================
    print("=" * 70)
    print("📈 ESTATÍSTICAS FINAIS")
    print("=" * 70)
    print()

    mce_stats = mce.get_statistics()
    hsas_stats = hsas.get_statistics()

    print("🧠 Memory Consolidation Engine:")
    print(f"   Replay buffer: {mce_stats['buffer_stats']['replay_buffer_size']}")
    print(f"   Long-term memory: {mce_stats['buffer_stats']['long_term_memory_size']}")
    print(f"   Padrões extraídos: {mce_stats['experience_stats']['patterns_extracted']}")
    print(f"   Total consolidações: {mce_stats['consolidation_stats']['total_consolidations']}")
    print(f"   Memory usage: {mce_stats['memory_usage_mb']:.2f} MB")
    print()

    print("🎯 Hybrid Skill Acquisition System:")
    print(f"   Total ações: {hsas_stats['actions']['total']}")
    print(f"   Uso de modos: {hsas_stats['actions']['mode_usage']}")
    print(f"   Skills aprendidas: {hsas_stats['skills']['total_learned']}")
    print(f"   Taxa de sucesso: {hsas_stats['skills']['avg_success_rate']:.2%}")
    print(f"   Conhecimento do world model: {hsas_stats['learning']['world_model_knowledge']} transições")
    print()

    print("=" * 70)
    print("✅ INTEGRAÇÃO COMPLETA")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(example_workflow())
