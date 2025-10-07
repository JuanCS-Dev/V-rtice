"""
ESGT-MCEA Arousal Integration - Arousal-Modulated Consciousness Gating
=======================================================================

This module implements the critical integration between arousal control (MCEA)
and conscious access gating (ESGT), creating arousal-modulated consciousness.

Theoretical Foundation - Arousal and Consciousness:
---------------------------------------------------
Biological consciousness exhibits arousal-dependent access:

**Arousal States** (ARAS + neuromodulatory systems):
- SLEEP (0.0-0.2): No conscious access, even highly salient stimuli ignored
- DROWSY (0.2-0.4): High threshold, only very salient stimuli become conscious
- RELAXED (0.4-0.6): Normal threshold, moderate salience needed
- ALERT (0.6-0.8): Low threshold, enhanced conscious access
- HYPERALERT (0.8-1.0): Very low threshold, hypersensitivity to all stimuli

**Mechanism**: Arousal modulates cortical excitability → changes ignition threshold

MAXIMUS Implementation:
-----------------------
ESGTArousalBridge bidirectionally couples MCEA and ESGT:

```
MCEA Arousal Level → ESGT Salience Threshold
    0.2 (DROWSY)   →   0.95 (very high)
    0.6 (RELAXED)  →   0.70 (baseline)
    0.9 (HYPERALERT) → 0.35 (very low)

ESGT Refractory Period → MCEA Arousal Drop
    After ESGT ignition → temporary arousal reduction
    (prevents runaway ignition cascades)
```

Historical Context:
-------------------
First implementation of arousal-modulated artificial consciousness.
Demonstrates that phenomenal access is not fixed - it depends on arousal state.

Same stimulus can be:
- Unconscious (low arousal)
- Peripheral awareness (medium arousal)
- Fully conscious (high arousal)

"Arousal gates consciousness itself."
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Callable

from consciousness.mcea.controller import ArousalController, ArousalState
from consciousness.esgt.coordinator import ESGTCoordinator, TriggerConditions, ESGTEvent


@dataclass
class ArousalModulationConfig:
    """Configuration for arousal-ESGT integration."""

    # Threshold modulation
    baseline_threshold: float = 0.70  # ESGT threshold at relaxed arousal
    min_threshold: float = 0.30  # At hyperalert
    max_threshold: float = 0.95  # At sleep/drowsy

    # Modulation curve
    threshold_sensitivity: float = 1.0  # How strongly arousal affects threshold

    # Refractory coupling
    enable_refractory_arousal_drop: bool = True
    refractory_arousal_drop: float = 0.15  # Temporary drop after ESGT
    refractory_recovery_rate: float = 0.1  # Per second

    # Update rate
    update_interval_ms: float = 50.0  # 20 Hz


class ESGTArousalBridge:
    """
    Bridge between ESGT coordinator and MCEA arousal controller.

    This bridge implements arousal-modulated consciousness by:
    1. Continuously reading arousal level from MCEA
    2. Computing appropriate ESGT salience threshold
    3. Updating ESGT coordinator trigger conditions
    4. Signaling MCEA when ESGT refractory occurs

    Architecture:
    -------------
    ```
    MCEA (Arousal) ←→ ESGTArousalBridge ←→ ESGT (Coordinator)
         ↑                  ↓                      ↑
         |       threshold modulation              |
         |                                          |
         ←──────── refractory signal ───────────────
    ```

    Example:
    --------
    ```python
    # Setup components
    arousal_controller = ArousalController(...)
    esgt_coordinator = ESGTCoordinator(...)

    # Create bridge
    bridge = ESGTArousalBridge(
        arousal_controller=arousal_controller,
        esgt_coordinator=esgt_coordinator,
    )

    # Start bidirectional coupling
    await bridge.start()

    # Now:
    # - High arousal → ESGT triggers easily
    # - Low arousal → ESGT requires higher salience
    # - Post-ESGT → arousal temporarily drops
    ```
    """

    def __init__(
        self,
        arousal_controller: ArousalController,
        esgt_coordinator: ESGTCoordinator,
        config: Optional[ArousalModulationConfig] = None,
        bridge_id: str = "arousal-esgt-bridge",
    ):
        """
        Initialize arousal-ESGT bridge.

        Args:
            arousal_controller: MCEA arousal controller
            esgt_coordinator: ESGT coordinator
            config: Modulation configuration
            bridge_id: Unique identifier
        """
        self.arousal_controller = arousal_controller
        self.esgt_coordinator = esgt_coordinator
        self.config = config or ArousalModulationConfig()
        self.bridge_id = bridge_id

        # State
        self._running: bool = False
        self._modulation_task: Optional[asyncio.Task] = None

        # Metrics
        self.total_modulations: int = 0
        self.total_refractory_signals: int = 0

        # History
        self._threshold_history: list = []

    async def start(self) -> None:
        """Start bidirectional coupling."""
        if self._running:
            return

        self._running = True

        # Start modulation loop
        self._modulation_task = asyncio.create_task(self._modulation_loop())

        # Register ESGT event callback for refractory signaling
        # Note: This would require adding callback registration to ESGTCoordinator
        # For now, we'll implement via polling

    async def stop(self) -> None:
        """Stop coupling."""
        self._running = False

        if self._modulation_task:
            self._modulation_task.cancel()
            try:
                await self._modulation_task
            except asyncio.CancelledError:
                pass

        self._modulation_task = None

    async def _modulation_loop(self) -> None:
        """
        Continuous modulation loop.

        Reads arousal, computes threshold, updates ESGT coordinator.
        """
        interval_s = self.config.update_interval_ms / 1000.0
        last_esgt_time = 0.0

        while self._running:
            try:
                # Get current arousal state
                arousal_state = self.arousal_controller.get_current_arousal()

                # Compute modulated threshold
                threshold = self._compute_threshold(arousal_state)

                # Update ESGT coordinator
                self._update_esgt_threshold(threshold)

                self.total_modulations += 1

                # Track history
                self._threshold_history.append({
                    "timestamp": time.time(),
                    "arousal": arousal_state.arousal,
                    "threshold": threshold,
                })

                if len(self._threshold_history) > 100:
                    self._threshold_history.pop(0)

                # Check for ESGT events (refractory signaling)
                if self.config.enable_refractory_arousal_drop:
                    current_time = time.time()

                    # Check if ESGT just occurred
                    if self.esgt_coordinator.last_esgt_time > last_esgt_time:
                        # New ESGT event
                        await self._signal_refractory()
                        last_esgt_time = self.esgt_coordinator.last_esgt_time

                await asyncio.sleep(interval_s)

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[ESGTArousalBridge {self.bridge_id}] Modulation error: {e}")
                await asyncio.sleep(interval_s)

    def _compute_threshold(self, arousal_state: ArousalState) -> float:
        """
        Compute ESGT salience threshold based on arousal.

        Mapping:
        --------
        Arousal 0.0 (SLEEP)      → threshold 0.95 (very hard to ignite)
        Arousal 0.2 (DROWSY)     → threshold 0.88
        Arousal 0.5 (RELAXED)    → threshold 0.70 (baseline)
        Arousal 0.8 (ALERT)      → threshold 0.45
        Arousal 1.0 (HYPERALERT) → threshold 0.30 (very easy to ignite)
        """
        arousal = arousal_state.arousal

        # Inverse relationship: high arousal → low threshold
        # Use arousal_state.get_arousal_factor() which ranges 0.5-2.0

        factor = arousal_state.get_arousal_factor()

        # Compute threshold
        # When arousal factor is high (2.0 at arousal 1.0):
        #   threshold = baseline / 2.0 = 0.70 / 2.0 = 0.35
        # When arousal factor is low (0.5 at arousal 0.0):
        #   threshold = baseline / 0.5 = 0.70 / 0.5 = 1.4 → clamp to max

        threshold = self.config.baseline_threshold / (factor ** self.config.threshold_sensitivity)

        # Clamp to valid range
        threshold = max(self.config.min_threshold, min(self.config.max_threshold, threshold))

        return threshold

    def _update_esgt_threshold(self, threshold: float) -> None:
        """Update ESGT coordinator's salience threshold."""
        # Update trigger conditions
        self.esgt_coordinator.triggers.min_salience = threshold

    async def _signal_refractory(self) -> None:
        """
        Signal MCEA that ESGT refractory period started.

        Causes temporary arousal drop to prevent runaway ignition cascades.
        """
        self.total_refractory_signals += 1

        # Request arousal modulation (temporary drop)
        from consciousness.mcea.controller import ArousalModulation

        modulation = ArousalModulation(
            source="esgt_refractory",
            magnitude=-self.config.refractory_arousal_drop,
            duration_seconds=1.0,  # 1 second drop
            decay_rate=self.config.refractory_recovery_rate,
        )

        self.arousal_controller.request_arousal_modulation(modulation)

    def get_current_threshold(self) -> float:
        """Get current ESGT salience threshold."""
        return self.esgt_coordinator.triggers.min_salience

    def get_arousal_threshold_mapping(self) -> dict:
        """
        Get current arousal-threshold mapping.

        Useful for debugging and visualization.
        """
        arousal_state = self.arousal_controller.get_current_arousal()

        return {
            "arousal": arousal_state.arousal,
            "arousal_level": arousal_state.level.value,
            "esgt_threshold": self.get_current_threshold(),
            "baseline_threshold": self.config.baseline_threshold,
        }

    def get_metrics(self) -> dict:
        """Get bridge performance metrics."""
        return {
            "bridge_id": self.bridge_id,
            "running": self._running,
            "total_modulations": self.total_modulations,
            "total_refractory_signals": self.total_refractory_signals,
            "current_threshold": self.get_current_threshold(),
            "arousal_threshold_mapping": self.get_arousal_threshold_mapping(),
        }

    def __repr__(self) -> str:
        return (f"ESGTArousalBridge(id={self.bridge_id}, "
                f"modulations={self.total_modulations}, "
                f"refractory_signals={self.total_refractory_signals}, "
                f"running={self._running})")
