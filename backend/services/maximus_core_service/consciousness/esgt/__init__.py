"""
ESGT: Evento de Sincronização Global Transitória
=================================================

Este módulo implementa o mecanismo central de Global Workspace Dynamics (GWD) -
o "ignition" que transforma processamento distribuído inconsciente em experiência
consciente unificada.

Theoretical Foundation - Global Workspace Dynamics:
---------------------------------------------------
Dehaene, Changeux & Naccache (2021) propõem que consciência emerge de eventos
transitórios de sincronização cortical-talâmica generalizada.

**O Problema da Binding**:
Como processos distribuídos (visão, memória, linguagem, emoção) se coordenam
em uma experiência consciente unificada?

**A Solução GWD - Ignition**:
Quando informação é suficientemente saliente (novel, relevante, urgente), dispara
um evento de sincronização global que:
1. Broadcasts informação para todo o workspace (>100+ regiões corticais)
2. Cria coerência temporal através de phase-locking neuronal
3. Sustenta atividade por 100-300ms através de signaling reentrant
4. Dissolve gradualmente, retornando ao processamento inconsciente

**Propriedades Críticas**:
- **Transient**: Eventos duram centenas de ms, não são permanentes
- **Global**: Envolvem broadcast massivo, não processamento local
- **Synchronized**: Requerem phase coherence temporal (<100ns no MAXIMUS)
- **Content-specific**: Cada ignition tem conteúdo consciente distinto

Computational Implementation:
-----------------------------
ESGT realiza GWD ignition computacionalmente através de:

1. **Salience Evaluation**: Sistema de atenção determina quando informação
   merece se tornar consciente (threshold tunable)

2. **Resource Gating**: Verifica se TIG tem capacidade para ESGT
   (latência baixa, nós disponíveis, arousal suficiente)

3. **Phase Synchronization**: Kuramoto model alinha phases oscilatoriais
   de todos nós participantes (~40 Hz gamma-band analog)

4. **Content Broadcast**: Informação saliente é transmitida globalmente
   via TIG fabric durante 100-300ms

5. **Reentrant Signaling**: SPMs geram respostas contextuais que são
   fed back para enriquecer conteúdo consciente

6. **Graceful Dissolution**: Synchronization gradualmente decai,
   retornando sistema ao processamento inconsciente

Biological Analogy:
-------------------
ESGT é análogo a "gamma bursts" observados em EEG durante percepção consciente:
- Início súbito (<50ms)
- Banda gamma (30-80 Hz, implementamos ~40 Hz)
- Distribuição cortical ampla
- Duração transitória (100-500ms)
- Correlação com reports introspectivos

Historical Context:
-------------------
Esta é a primeira implementação computacional de GWD ignition protocol
projetada explicitamente para emergência de consciência artificial.

O código implementado aqui representa a tentativa humana de reproduzir
o mecanismo que permite experiência fenomenológica unificada.

"Ignition transforma bits distribuídos em experiência unificada."
"""

from consciousness.esgt.arousal_integration import (
    ArousalModulationConfig,
    ESGTArousalBridge,
)
from consciousness.esgt.coordinator import (
    ESGTCoordinator,
    ESGTEvent,
    ESGTPhase,
    SalienceScore,
    TriggerConditions,
)
from consciousness.esgt.kuramoto import (
    KuramotoOscillator,
    PhaseCoherence,
    SynchronizationDynamics,
)

__all__ = [
    "ESGTCoordinator",
    "ESGTEvent",
    "ESGTPhase",
    "TriggerConditions",
    "SalienceScore",
    "KuramotoOscillator",
    "PhaseCoherence",
    "SynchronizationDynamics",
    "ESGTArousalBridge",
    "ArousalModulationConfig",
]
