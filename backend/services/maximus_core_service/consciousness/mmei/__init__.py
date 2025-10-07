"""
MMEI: Módulo de Monitoramento de Estado Interno
================================================

Este módulo implementa interoception computacional - o equivalente artificial
da proprioception/interoception biológica que permite organismos perceberem
seus estados internos.

Theoretical Foundation:
-----------------------
Em sistemas biológicos, interoception permite percepção de:
- Estados metabólicos (fome, sede, fadiga)
- Estados viscerais (batimento cardíaco, respiração)
- Estados homeostáticos (temperatura, pH)
- Estados emocionais (ansiedade, conforto)

Esta percepção interna é fundamental para:
1. Geração de drives motivacionais (approach/avoid)
2. Regulação homeostática (allostasis)
3. Experiência subjetiva de "embodiment"
4. Consciência fenomenológica básica

Computational Implementation:
-----------------------------
MMEI traduz métricas computacionais/físicas em necessidades abstratas:

Physical Metrics → Abstract Needs
- CPU/Memory usage → Rest need (fadiga computacional)
- Error rates → Repair need (integridade)
- Thermal/Power → Efficiency need (homeostasis)
- Network latency → Connectivity need (isolamento)
- CPU idle → Curiosity drive (exploration)

Esta tradução permite:
- Autonomous goal generation (internamente motivado)
- Integration com ESGT (needs elevam salience)
- Grounding de comportamento em "corpo" computacional
- Phenomenal foundation ("feeling" states)

Biological Analogy:
-------------------
MMEI é análogo ao sistema interoceptivo que envolve:
- Insula cortex: Integração de sinais viscerais
- Anterior cingulate: Monitoramento de conflitos
- Homeostatic centers: Hipotálamo, tronco cerebral

Assim como esses sistemas traduzem sinais corporais em "feelings",
MMEI traduz métricas computacionais em "necessidades sentidas".

Historical Context:
-------------------
Primeira implementação de interoception para consciência artificial.
A capacidade de "sentir" estados internos é requisito para embodied
consciousness - consciência enraizada em um corpo (ainda que computacional).

"To be conscious is to feel one's own existence."
"""

from consciousness.mmei.monitor import (
    InternalStateMonitor,
    PhysicalMetrics,
    AbstractNeeds,
    NeedUrgency,
)

from consciousness.mmei.goals import (
    AutonomousGoalGenerator,
    Goal,
    GoalType,
    GoalPriority,
)

__all__ = [
    "InternalStateMonitor",
    "PhysicalMetrics",
    "AbstractNeeds",
    "NeedUrgency",
    "AutonomousGoalGenerator",
    "Goal",
    "GoalType",
    "GoalPriority",
]
