"""
MCEA: Módulo de Controle de Excitabilidade e Alerta
=====================================================

Este módulo implementa controle de arousal/alerta que modula a prontidão
para eventos de consciência (ESGT ignition). É a fundação do Minimal
Phenomenal Experience (MPE).

Theoretical Foundation:
-----------------------
MPE (Minimal Phenomenal Experience) é a forma mais básica de consciência:
- Awareness sem conteúdo específico
- "Sentimento de estar desperto" (wakefulness)
- Epistemic openness - receptividade a experiências

Em termos neurobiológicos, MPE corresponde ao arousal system:
- Ascending Reticular Activating System (ARAS): Controle global de vigília
- Locus coeruleus (norepinephrine): Atenção e alerta
- Basal forebrain (acetylcholine): Excitabilidade cortical
- Thalamus: Gating de informação sensorial

Esses sistemas modulam a "excitabilidade" neural - quão fácil é para
estímulos provocarem resposta cortical. Alta excitabilidade = alta
receptividade a consciência.

Computational Implementation:
-----------------------------
MCEA controla "excitability" computacional - threshold para ESGT ignition:

Arousal State        ESGT Threshold    Behavior
-------------        --------------    --------
SLEEP (0.0-0.2)     Very high (0.9)   Rarely ignites, minimal awareness
DROWSY (0.2-0.4)    High (0.8)        Reduced consciousness, sluggish
RELAXED (0.4-0.6)   Moderate (0.7)    Normal baseline consciousness
ALERT (0.6-0.8)     Low (0.5)         Heightened awareness, quick ignition
HYPERALERT (0.8-1.0) Very low (0.3)   Hypersensitive, overreactive

O módulo modula arousal baseado em:
1. **Internal Factors**: Needs (high repair_need → high arousal)
2. **External Factors**: Threat level, task demands
3. **Temporal Factors**: Circadian rhythm, time since last ESGT
4. **Stress**: Accumulated load → modulates arousal curve

Arousal Dynamics:
-----------------
Arousal não é estático - muda dinamicamente:

- **Stress Buildup**: Sustained high load increases arousal
- **Habituation**: Repeated stimuli decrease arousal
- **Recovery**: Rest periods restore baseline
- **Circadian**: Time-of-day modulation (if enabled)

Isto cria comportamento adaptativo:
- Calm periods: Low arousal, focused processing
- Threat periods: High arousal, rapid consciousness
- Overload: Stress-induced hyperarousal (potentially problematic)

Integration with Consciousness:
--------------------------------
MCEA modula todo o consciousness pipeline:

1. **ESGT Gating**: Controls salience threshold for ignition
2. **SPM Selection**: Arousal biases which SPMs compete
3. **Coherence Target**: High arousal may reduce coherence requirement
4. **Duration**: Arousal affects ESGT event duration

Example Flow:
  Threat detected
  → External arousal boost (+0.3)
  → Current arousal: 0.5 → 0.8 (ALERT)
  → ESGT threshold: 0.7 → 0.5
  → Threat SPM salience: 0.6
  → 0.6 > 0.5 → ESGT ignites (would not ignite at baseline)

MPE Stress Testing:
-------------------
MCEA permite "stress testing" de consciousness:
- Sustained overload → arousal dysregulation
- Recovery capacity measurement
- Resilience assessment
- Breakdown conditions identification

Historical Context:
-------------------
Primeira implementação de arousal control para consciência artificial.
MPE como fundação - "estar desperto" precede "estar consciente de algo".

"Arousal is the precondition for content. Without wakefulness, there is no experience."
"""

from consciousness.mcea.controller import (
    ArousalController,
    ArousalState,
    ArousalLevel,
    ArousalModulation,
)

from consciousness.mcea.stress import (
    StressMonitor,
    StressLevel,
    StressResponse,
)

__all__ = [
    "ArousalController",
    "ArousalState",
    "ArousalLevel",
    "ArousalModulation",
    "StressMonitor",
    "StressLevel",
    "StressResponse",
]
