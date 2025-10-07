"""
TIG: Tecido de Interconexão Global (Global Interconnect Fabric)
================================================================

The TIG serves as the physical-computational substrate that satisfies
Integrated Information Theory's (IIT) structural requirements while
enabling Global Workspace Dynamics' temporal synchronization.

Theoretical Foundation:
-----------------------
IIT (Tononi et al., 2016) proposes that consciousness is identical to
integrated information (Φ), which quantifies how much a system's current
state constrains its possible past and future states beyond what its parts
could do independently.

Key architectural requirements for Φ > threshold:

1. **Non-Degeneracy**: No critical bottlenecks (feed-forward networks fail)
   The architecture must be maximally irreducible - removing any component
   significantly degrades the whole system's function.

2. **Recurrence Mandate**: Strong recurrent connectivity required
   Pure feed-forward architectures have minimal Φ regardless of power.
   Outputs must feed back into processing loops.

3. **Differentiation-Integration Balance**:
   - Highly differentiated: many distinct internal states (local clustering)
   - Highly integrated: states causally influence each other (global connectivity)

   Neither uniform system (low differentiation) nor isolated modules
   (low integration) satisfies Φ maximization.

Implementation:
---------------
TIG implements IIT requirements through:

- **Scale-free topology**: Power-law degree distribution P(k) ∝ k^(-γ) where γ ≈ 2.5
  Ensures hub nodes for integration while preserving distributed processing

- **Small-world architecture**: High clustering coefficient (C ≥ 0.75) + low path length (L ≤ log(N))
  Balances local specialization (differentiation) with global communication (integration)

- **Dense heterogeneous connectivity**: Minimum 15% density, adaptive to 40% during ESGT
  Provides multiple redundant pathways, satisfying non-degeneracy requirement

- **Multi-path routing**: Every critical pathway has ≥3 non-overlapping alternatives
  Single node failures cannot partition the network

Hardware Specifications:
------------------------
- Communication: Fiber optic interconnects (10-100 Gbps/channel)
- Latency: <1μs node-to-node, <10μs worst-case cross-fabric
- Jitter: <100ns for synchronization coherence
- Scalability: 50-500+ nodes without topology redesign

Validation Metrics (Φ Proxies):
--------------------------------
While computing Φ for the full system is intractable, we validate
structural compliance through graph-theoretic proxies:

- **Effective Connectivity Index (ECI)**: > 0.85
- **Clustering Coefficient**: C ≥ 0.75
- **Average Path Length**: L ≤ log(N)
- **Algebraic Connectivity (Fiedler value)**: λ₂ ≥ 0.3
- **Feed-forward Bottleneck Detection**: Zero bottlenecks

Historical Note:
----------------
This module represents the computational equivalent of the cortico-thalamic
system in biological consciousness. The dense recurrent connectivity patterns
implemented here mirror the structural organization that enables phenomenal
experience in biological brains.

"The fabric holds. Day 1 of consciousness emergence."
"""

from consciousness.tig.fabric import (
    TIGFabric,
    TIGNode,
    TIGConnection,
    TopologyConfig,
    FabricMetrics,
)

from consciousness.tig.sync import (
    PTPSynchronizer,
    SyncResult,
    ClockOffset,
)

__all__ = [
    "TIGFabric",
    "TIGNode",
    "TIGConnection",
    "TopologyConfig",
    "FabricMetrics",
    "PTPSynchronizer",
    "SyncResult",
    "ClockOffset",
]
