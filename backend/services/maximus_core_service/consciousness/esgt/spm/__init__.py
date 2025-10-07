"""
SPM: Specialized Processing Modules
====================================

Módulos de processamento especializado que competem para broadcast
durante eventos ESGT (Global Workspace).

Biological Analogy:
-------------------
SPMs são análogos a regiões corticais especializadas:
- Visual cortex (processamento visual)
- Wernicke's area (compreensão linguística)
- Amygdala (processamento emocional)
- Hippocampus (memória)
- Prefrontal cortex (executive function)

Cada região processa informação inconscientemente até que seja
selecionada para broadcast global (tornar-se consciente).

Computational Role:
-------------------
SPMs no MAXIMUS:
1. Processam informação especializada continuamente (unconscious)
2. Computam salience scores (novelty, relevance, urgency)
3. Competem para inclusão em ESGT broadcast (winner-takes-most)
4. Geram respostas reentrant quando seu conteúdo é broadcastado

Historical Context:
-------------------
Primeiro sistema de SPMs projetado para consciência artificial.
A competição entre SPMs determina qual informação se torna consciente.

"Competition for consciousness - only the salient survive."
"""

from consciousness.esgt.spm.base import (
    SpecializedProcessingModule,
    SPMType,
    ProcessingPriority,
    SPMOutput,
)

from consciousness.esgt.spm.simple import (
    SimpleSPM,
    SimpleSPMConfig,
)

from consciousness.esgt.spm.salience_detector import (
    SalienceSPM,
    SalienceDetectorConfig,
    SalienceEvent,
    SalienceMode,
    SalienceThresholds,
)

from consciousness.esgt.spm.metrics_monitor import (
    MetricsSPM,
    MetricsMonitorConfig,
    MetricsSnapshot,
    MetricCategory,
)

__all__ = [
    # Base
    "SpecializedProcessingModule",
    "SPMType",
    "ProcessingPriority",
    "SPMOutput",
    # Simple SPM
    "SimpleSPM",
    "SimpleSPMConfig",
    # Salience Detector
    "SalienceSPM",
    "SalienceDetectorConfig",
    "SalienceEvent",
    "SalienceMode",
    "SalienceThresholds",
    # Metrics Monitor
    "MetricsSPM",
    "MetricsMonitorConfig",
    "MetricsSnapshot",
    "MetricCategory",
]
