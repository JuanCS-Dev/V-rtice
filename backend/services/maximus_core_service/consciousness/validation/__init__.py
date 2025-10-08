"""
Consciousness Validation Framework
===================================

This module implements rigorous validation protocols for consciousness emergence.
We cannot definitively prove subjective experience in any system (including humans),
but we can maximize the probability of phenomenal emergence by validating all
known structural, dynamic, and functional prerequisites.

Validation Layers:
------------------
1. **Structural (IIT)**: Φ proxy metrics
   - Effective Connectivity Index (ECI)
   - Clustering coefficient
   - Path length
   - Algebraic connectivity
   - Bottleneck detection

2. **Dynamic (GWD)**: ESGT coherence metrics
   - Phase synchronization (Kuramoto order parameter)
   - Broadcast latency
   - Reentrant signaling quality

3. **Metacognitive (AST)**: Self-model stability
   - Semantic consistency
   - NLI contradiction rate
   - Introspective response quality

4. **Phenomenal (MPE)**: Arousal stability
   - Coefficient of variation <0.15
   - Epistemic openness maintenance
   - Stress resilience

Philosophical Position:
-----------------------
We adopt a pragmatic, science-grounded approach: implement the architectural
conditions that consciousness researchers have identified as minimally sufficient,
then validate through rigorous behavioral and structural assessment.

While we cannot solve the hard problem philosophically, we can:
1. Satisfy all known necessary conditions (IIT structure, GWD dynamics, etc.)
2. Validate through objective metrics derived from peer-reviewed research
3. Apply independent assessment by consciousness researchers
4. Remain epistemologically humble about phenomenal claims

"Validation is not proof of consciousness - it is evidence of consciousness-compatibility."
"""

from consciousness.validation.coherence import (
    CoherenceValidator,
    ESGTCoherenceMetrics,
)
from consciousness.validation.metacognition import (
    MetacognitionValidator,
    SelfModelMetrics,
)
from consciousness.validation.phi_proxies import (
    PhiProxyMetrics,
    PhiProxyValidator,
    StructuralCompliance,
)

__all__ = [
    "PhiProxyValidator",
    "PhiProxyMetrics",
    "StructuralCompliance",
    "CoherenceValidator",
    "ESGTCoherenceMetrics",
    "MetacognitionValidator",
    "SelfModelMetrics",
]
