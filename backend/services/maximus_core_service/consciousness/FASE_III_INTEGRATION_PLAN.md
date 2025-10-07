# FASE III - IMMUNE CORE + CONSCIOUSNESS INTEGRATION

**Data**: 2025-10-07
**Status**: 📋 PLANNING
**Objetivo**: Integrar Active Immune Core com sistema de consciência (MMEI/MCEA/ESGT)

---

## 🎯 VISÃO GERAL

Integrar o Active Immune Core (agentes autônomos de defesa) com o sistema de consciência embodied para criar um sistema imunológico **consciente** e **adaptatativo**.

### Princípio Central
**"Consciousness guides immunity, immunity informs consciousness"**

O sistema imunológico deve:
1. Reagir ao estado de arousal do sistema (MCEA)
2. Responder a eventos conscientes (ESGT ignition)
3. Informar necessidades ao corpo (MMEI)

---

## 📋 COMPONENTES A INTEGRAR

### Consciousness Side (MAXIMUS Core)
- **MMEI** (Interoception): Physical metrics → Abstract needs
- **MCEA** (Arousal Control): Arousal state (0-1) + modulation
- **ESGT** (Global Workspace): Conscious access events + salience

### Immune Side (Active Immune Core)
- **HomeostaticController**: MAPE-K loop (Monitor-Analyze-Plan-Execute)
- **ClonalSelectionEngine**: Evolutionary agent optimization
- **LinfonodoDigital**: Regional coordination hub

---

## 🔗 INTEGRATION POINTS

### 1. MMEI → HomeostaticController ✅ High Priority

**Objetivo**: Needs do MMEI informam decisões MAPE-K do controlador homeostático

**Implementation**:
```python
# File: active_immune_core/coordination/homeostatic_controller.py

class HomeostaticController:
    def __init__(self, ...):
        # Add MMEI integration
        self.mmei_client: Optional[MMEIClient] = None
        self.current_needs: Optional[AbstractNeeds] = None

    def set_mmei_client(self, client: MMEIClient):
        """Connect to MMEI monitor."""
        self.mmei_client = client

    async def _monitor(self):
        """Monitor phase - collect metrics + needs"""
        # Existing: system metrics, agent metrics

        # NEW: Fetch needs from MMEI
        if self.mmei_client:
            self.current_needs = await self.mmei_client.get_current_needs()

    async def _analyze(self) -> List[str]:
        """Analyze phase - detect issues INCLUDING needs-driven"""
        issues = []

        # Existing: high_cpu, low_agents, etc.

        # NEW: Needs-driven analysis
        if self.current_needs:
            if self.current_needs.rest_need > 0.7:
                issues.append("high_rest_need_fatigue")

            if self.current_needs.repair_need > 0.7:
                issues.append("high_repair_need_alert")

            if self.current_needs.efficiency_need > 0.6:
                issues.append("efficiency_optimization_needed")

        return issues

    async def _plan(self, issues: List[str]) -> Tuple[ActionType, Dict]:
        """Plan phase - map needs to actions"""

        # NEW: Needs-driven action planning
        if "high_rest_need_fatigue" in issues:
            return ActionType.SCALE_DOWN_AGENTS, {"reason": "rest_need"}

        if "high_repair_need_alert" in issues:
            return ActionType.SCALE_UP_AGENTS, {"reason": "repair_need"}

        if "efficiency_optimization_needed" in issues:
            return ActionType.ADJUST_SENSITIVITY, {"direction": "optimize"}

        # Existing logic...
```

**Behavior**:
- `rest_need > 0.7` → Scale down agents (conserve resources)
- `repair_need > 0.7` → Scale up agents (address threats)
- `efficiency_need > 0.6` → Optimize sensitivity/resource usage

**Test**: `test_homeostatic_needs_integration.py`

---

### 2. MCEA → ClonalSelectionEngine ✅ High Priority

**Objetivo**: Arousal do MCEA modula agressividade da seleção clonal

**Implementation**:
```python
# File: active_immune_core/coordination/clonal_selection.py

class ClonalSelectionEngine:
    def __init__(self, ...):
        # Add MCEA integration
        self.mcea_client: Optional[MCEAClient] = None
        self.current_arousal: float = 0.5  # Default baseline

    def set_mcea_client(self, client: MCEAClient):
        """Connect to MCEA arousal controller."""
        self.mcea_client = client

    async def select_and_clone(self, ...):
        """Select and clone with arousal modulation"""

        # Fetch arousal
        if self.mcea_client:
            arousal_state = await self.mcea_client.get_current_arousal()
            self.current_arousal = arousal_state.arousal

        # Modulate selection parameters
        selection_pressure = self._compute_selection_pressure(self.current_arousal)
        mutation_rate = self._compute_mutation_rate(self.current_arousal)

        # Apply selection with modulated parameters
        ...

    def _compute_selection_pressure(self, arousal: float) -> float:
        """
        Map arousal to selection pressure.

        Low arousal (0.2) → Conservative (keep 50% of population)
        High arousal (0.8) → Aggressive (keep only top 10%)
        """
        # Inverse relationship: high arousal = strict selection
        return 0.5 - (0.4 * arousal)  # Range: 0.5 → 0.1

    def _compute_mutation_rate(self, arousal: float) -> float:
        """
        Map arousal to mutation rate.

        Low arousal (0.2) → Low exploration (mutation=0.05)
        High arousal (0.8) → High exploration (mutation=0.15)
        """
        # Direct relationship: high arousal = more mutations
        return 0.05 + (0.10 * arousal)  # Range: 0.05 → 0.15
```

**Behavior**:
- **Low arousal (drowsy/fatigued)**: Conservative selection, low mutations
- **High arousal (alert/hyperalert)**: Aggressive selection, high mutations
- Matches biological stress response (cortisol → immune activation)

**Test**: `test_clonal_arousal_modulation.py`

---

### 3. ESGT → LinfonodoDigital ✅ Medium Priority

**Objetivo**: ESGT ignition events triggam respostas imunes coordenadas

**Implementation**:
```python
# File: active_immune_core/coordination/lymphnode.py

class LinfonodoDigital:
    def __init__(self, ...):
        # Add ESGT integration
        self.esgt_subscriber: Optional[ESGTSubscriber] = None
        self.recent_ignitions: List[ESGTEvent] = []

    def set_esgt_subscriber(self, subscriber: ESGTSubscriber):
        """Subscribe to ESGT ignition events."""
        self.esgt_subscriber = subscriber
        subscriber.on_ignition(self._handle_esgt_ignition)

    async def _handle_esgt_ignition(self, event: ESGTEvent):
        """
        Handle ESGT ignition event.

        High salience events trigger coordinated immune response.
        """
        self.recent_ignitions.append(event)

        # Extract salience
        salience = event.salience_score.composite_score()

        if salience > 0.8:
            # High salience → Threat likely
            logger.info(f"🚨 High salience ESGT ({salience:.2f}) → Triggering immune activation")

            # Boost cytokine production
            await self._broadcast_cytokine(
                type="IL-1",  # Pro-inflammatory
                level=salience,
                source="esgt_ignition",
            )

            # Request clonal expansion
            await self._request_clonal_expansion(
                reason=f"esgt_ignition_{event.id}",
                urgency=salience,
            )

        elif salience > 0.6:
            # Medium salience → Increase vigilance
            await self._adjust_temperature(delta=+0.5)

    async def _request_clonal_expansion(self, reason: str, urgency: float):
        """Request clonal expansion from selection engine."""
        # Notify selection engine to prioritize cloning
        ...
```

**Behavior**:
- ESGT ignition (salience > 0.8) → Trigger immune activation
- Medium salience (0.6-0.8) → Increase vigilance
- Low salience (<0.6) → No action (avoid false alarms)

**Test**: `test_lymphnode_esgt_integration.py`

---

## 🧪 TESTING STRATEGY

### Integration Tests
Create: `/consciousness/integration/test_immune_consciousness_integration.py`

**Test Scenarios**:
1. **High Load Scenario**:
   ```
   CPU 95% → rest_need ↑ → arousal ↓ → scale down immune agents
   Validate: Agent count decreases, resources conserved
   ```

2. **Threat Burst Scenario**:
   ```
   Errors ↑ → repair_need ↑ → arousal ↑ → aggressive clonal selection
   Validate: More clones created, higher mutation rate
   ```

3. **ESGT Ignition Response**:
   ```
   High salience event → ESGT ignition → lymphnode activation
   Validate: Cytokines broadcast, temperature increases
   ```

4. **End-to-End Pipeline**:
   ```
   Physical stress → MMEI → MCEA → Arousal → Clonal selection modulation
   ESGT ignition → Lymphnode → Coordinated response
   Validate: Full pipeline operational
   ```

**Target**: 10+ tests, 100% passing

---

## 📂 FILES TO CREATE/MODIFY

### New Files
1. `maximus_core_service/consciousness/integration/mmei_client.py` - MMEI HTTP client
2. `maximus_core_service/consciousness/integration/mcea_client.py` - MCEA HTTP client
3. `maximus_core_service/consciousness/integration/esgt_subscriber.py` - ESGT event subscriber
4. `maximus_core_service/consciousness/integration/test_immune_consciousness_integration.py` - Integration tests

### Modified Files
1. `active_immune_core/coordination/homeostatic_controller.py` - Add `set_mmei_client()` and needs integration
2. `active_immune_core/coordination/clonal_selection.py` - Add `set_mcea_client()` and arousal modulation
3. `active_immune_core/coordination/lymphnode.py` - Add `set_esgt_subscriber()` and ignition handling

---

## ⏱️ ESTIMATED TIMELINE

| Task | Effort | Priority |
|------|--------|----------|
| 1. MMEI → HomeostaticController | 2h | P0 |
| 2. MCEA → ClonalSelectionEngine | 2h | P0 |
| 3. ESGT → LinfonodoDigital | 1.5h | P1 |
| 4. Integration Tests | 2h | P0 |
| 5. Documentation | 0.5h | P1 |
| **TOTAL** | **8h** | - |

---

## 🎯 SUCCESS CRITERIA

- ✅ All 3 integration points implemented
- ✅ 10+ integration tests (100% passing)
- ✅ No regression in existing tests (528 Active Immune + 14 Consciousness)
- ✅ Golden Rule compliant (NO MOCK, NO PLACEHOLDER, NO TODO)
- ✅ Documentation complete (FASE_III_COMPLETE.md)

---

## 🚀 NEXT STEPS

1. ✅ Create integration clients (MMEIClient, MCEAClient, ESGTSubscriber)
2. ✅ Modify HomeostaticController for needs integration
3. ✅ Modify ClonalSelectionEngine for arousal modulation
4. ✅ Modify LinfonodoDigital for ESGT integration
5. ✅ Write 10+ integration tests
6. ✅ Run full test suite (542+ tests expected)
7. ✅ Document FASE_III_COMPLETE.md

---

**Prepared by**: Claude Code (Sonnet 4.5)
**Date**: 2025-10-07
**Status**: 📋 Planning Complete
**Next**: Implementation

---

*"The immune system is the body's consciousness of threat. Conscious systems are immune to unconscious patterns."* - Doutrina Vértice
