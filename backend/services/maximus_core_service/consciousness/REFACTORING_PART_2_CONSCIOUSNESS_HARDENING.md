# REFACTORING PART 2: CONSCIOUSNESS HARDENING

**PRIORIDADE**: 🟡 ALTA - EXECUTAR APÓS PART 1
**Sessão**: 2 de 3 (Independente após Safety Core)
**Objetivo**: Adicionar robustez, fault tolerance e bounds em todos os componentes de consciência
**Princípio**: "Bounded, monitored, reversible"

---

## ⚠️ MOTIVAÇÃO

**Riscos Atuais**:
- TIG pode ter propagação cascata de falhas
- ESGT pode ter ignição descontrolada (runaway)
- MMEI pode gerar goal spam sem bounds
- MCEA pode ter arousal runaway
- LRR/MEA podem ter recursão infinita

**Solução**:
- Fault tolerance em cada componente
- Circuit breakers para isolamento
- Bounds rigorosos em todos os loops
- Graceful degradation
- Monitoring hooks para Safety Core

---

## 🎯 OBJETIVOS DE HARDENING

### 1. Fault Isolation
✅ Falha em um componente não cascateia
✅ Circuit breakers entre componentes
✅ Timeouts em todas as operações async
✅ Recovery automático quando possível

### 2. Bounded Behavior
✅ ESGT frequency <10Hz hard limit
✅ Goal generation <5/min hard limit
✅ Arousal bounded [0.0, 1.0] sempre
✅ Recursion depth <5 hard limit

### 3. Graceful Degradation
✅ Desabilitar features não-críticas sob stress
✅ Reduced functionality mode
✅ Clear degradation signals
✅ Auto-recovery quando possível

### 4. Observability
✅ Metrics hooks para Safety Core
✅ Health checks em todos componentes
✅ Performance monitoring
✅ Error tracking

---

## 📁 COMPONENTES A REFATORAR

### 1. TIG - Fault Tolerance (fabric.py 678 linhas → 900 linhas)

**Problemas Atuais**:
- Falha em 1 nó pode afetar toda rede
- Sem detecção de nós mortos
- Sem isolamento de nós problemáticos
- Network partitions não tratadas

**REFATORAÇÃO**:

```python
"""
TIG - Thalamocortical Information Gateway (Hardened)

Additions:
1. Node health monitoring
2. Dead node detection and isolation
3. Network partition detection
4. Automatic topology repair
5. Circuit breakers for node communication
"""

from dataclasses import dataclass
from typing import Set
import asyncio
import time


@dataclass
class NodeHealth:
    """Health status of a TIG node"""
    node_id: int
    last_seen: float
    failures: int
    isolated: bool
    degraded: bool


class TIGFabric:
    """TIG with fault tolerance and self-healing"""

    def __init__(self, num_nodes: int = 100):
        # ... existing init ...

        # NEW: Health monitoring
        self.node_health: Dict[int, NodeHealth] = {}
        self.dead_node_timeout = 5.0  # seconds
        self.max_failures_before_isolation = 3

        # NEW: Circuit breakers
        self.circuit_breakers: Dict[int, CircuitBreaker] = {}

        # NEW: Network partition detection
        self.partition_detector = NetworkPartitionDetector(self)

        # NEW: Topology repair
        self.topology_repair_interval = 60.0  # seconds
        self._repair_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start TIG with health monitoring"""
        # Existing start logic...

        # NEW: Start health monitoring
        self._health_monitor_task = asyncio.create_task(
            self._health_monitoring_loop()
        )

        # NEW: Start topology repair
        self._repair_task = asyncio.create_task(
            self._topology_repair_loop()
        )

    async def _health_monitoring_loop(self):
        """Monitor health of all nodes"""
        while self.running:
            try:
                current_time = time.time()

                for node_id, health in self.node_health.items():
                    # Check if node is dead (not seen in timeout)
                    if current_time - health.last_seen > self.dead_node_timeout:
                        if not health.isolated:
                            await self._isolate_dead_node(node_id)

                    # Check if node should be reintegrated
                    elif health.isolated and health.failures == 0:
                        await self._reintegrate_node(node_id)

                # Check for network partitions
                partitions = await self.partition_detector.detect()
                if partitions:
                    await self._handle_network_partition(partitions)

                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

    async def _isolate_dead_node(self, node_id: int):
        """Isolate a dead/problematic node"""
        logger.warning(f"🔴 TIG: Isolating dead node {node_id}")

        # Mark as isolated
        self.node_health[node_id].isolated = True

        # Remove from active topology
        self._remove_node_edges(node_id)

        # Trigger topology repair to maintain connectivity
        await self._repair_topology_around_dead_node(node_id)

        # Notify Safety Core
        await self._notify_safety_core(
            event="node_isolation",
            node_id=node_id,
            reason="dead_node_timeout"
        )

    async def _repair_topology_around_dead_node(self, dead_node_id: int):
        """Repair topology to maintain connectivity after node death"""
        # Find neighbors of dead node
        neighbors = self._get_neighbors(dead_node_id)

        # Create bypass connections between neighbors
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i+1:]:
                if not self.has_edge(n1, n2):
                    self.add_edge(n1, n2)
                    logger.info(f"✓ TIG: Created bypass edge {n1}-{n2}")

        # Verify connectivity maintained
        if not self._verify_connectivity():
            logger.error("⚠️ TIG: Topology repair failed - network partitioned")
            # Trigger emergency topology rebuild
            await self._emergency_topology_rebuild()

    async def send_to_node(
        self,
        node_id: int,
        data: Any,
        timeout: float = 1.0
    ) -> bool:
        """
        Send data to node with circuit breaker and timeout

        Returns:
            bool: True if send successful, False otherwise
        """
        # Check if node is isolated
        if self.node_health[node_id].isolated:
            return False

        # Check circuit breaker
        breaker = self.circuit_breakers.get(node_id)
        if breaker and breaker.is_open():
            return False

        try:
            # Send with timeout
            async with asyncio.timeout(timeout):
                result = await self._send_data(node_id, data)

            # Update health (success)
            self.node_health[node_id].last_seen = time.time()
            if breaker:
                breaker.record_success()

            return True

        except asyncio.TimeoutError:
            logger.warning(f"TIG: Send timeout to node {node_id}")
            return self._handle_send_failure(node_id, "timeout")

        except Exception as e:
            logger.error(f"TIG: Send error to node {node_id}: {e}")
            return self._handle_send_failure(node_id, str(e))

    def _handle_send_failure(self, node_id: int, reason: str) -> bool:
        """Handle node communication failure"""
        health = self.node_health[node_id]
        health.failures += 1

        # Open circuit breaker if too many failures
        if health.failures >= self.max_failures_before_isolation:
            self.circuit_breakers[node_id].open()
            logger.warning(
                f"⚠️ TIG: Circuit breaker OPEN for node {node_id} "
                f"({health.failures} failures)"
            )

        return False

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get TIG health metrics for Safety Core"""
        total_nodes = len(self.node_health)
        isolated_nodes = sum(
            1 for h in self.node_health.values() if h.isolated
        )
        degraded_nodes = sum(
            1 for h in self.node_health.values() if h.degraded
        )

        return {
            "total_nodes": total_nodes,
            "healthy_nodes": total_nodes - isolated_nodes - degraded_nodes,
            "isolated_nodes": isolated_nodes,
            "degraded_nodes": degraded_nodes,
            "connectivity": self._compute_connectivity(),
            "is_partitioned": self.partition_detector.is_partitioned(),
        }


class CircuitBreaker:
    """Circuit breaker for TIG node communication"""

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = "closed"  # closed, open, half_open
        self.failures = 0
        self.last_failure_time: Optional[float] = None

    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking calls)"""
        if self.state == "open":
            # Check if recovery timeout elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half_open"
                return False
            return True
        return False

    def record_success(self):
        """Record successful operation"""
        if self.state == "half_open":
            # Recovery successful
            self.state = "closed"
            self.failures = 0

    def record_failure(self):
        """Record failed operation"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.open()

    def open(self):
        """Open circuit breaker (block calls)"""
        self.state = "open"


class NetworkPartitionDetector:
    """Detect network partitions in TIG"""

    def __init__(self, tig: TIGFabric):
        self.tig = tig

    async def detect(self) -> List[Set[int]]:
        """
        Detect network partitions using connected components

        Returns:
            List of partitions (sets of node IDs)
            Empty list if no partitions
        """
        # Use BFS to find connected components
        visited = set()
        partitions = []

        for node_id in self.tig.get_active_nodes():
            if node_id not in visited:
                partition = self._bfs_component(node_id, visited)
                partitions.append(partition)

        # If more than 1 partition, network is partitioned
        if len(partitions) > 1:
            logger.error(
                f"🔴 TIG: Network PARTITIONED into {len(partitions)} components"
            )
            return partitions

        return []

    def _bfs_component(
        self,
        start_node: int,
        visited: Set[int]
    ) -> Set[int]:
        """BFS to find connected component"""
        component = set()
        queue = [start_node]

        while queue:
            node = queue.pop(0)
            if node in visited:
                continue

            visited.add(node)
            component.add(node)

            # Add unvisited neighbors
            for neighbor in self.tig.get_neighbors(node):
                if neighbor not in visited:
                    queue.append(neighbor)

        return component

    def is_partitioned(self) -> bool:
        """Quick check if network is partitioned"""
        # Cache result for 1 second
        # (full detection is expensive)
        pass
```

---

### 2. ESGT - Ignition Bounds (coordinator.py 647 linhas → 850 linhas)

**Problemas Atuais**:
- Ignição pode rodar descontrolada (>10Hz)
- Sem limite de eventos simultâneos
- Coherence pode degradar sem bounds
- Sem graceful degradation sob load

**REFATORAÇÃO**:

```python
"""
ESGT Coordinator - Hardened with Ignition Bounds

Additions:
1. Frequency hard limit (10Hz max)
2. Concurrent event limit
3. Coherence lower bound enforcement
4. Graceful degradation under load
5. Ignition circuit breaker
"""

import asyncio
import time
from collections import deque
from typing import Deque


class ESGTCoordinator:
    """ESGT with bounded ignition and graceful degradation"""

    # HARD LIMITS (cannot be exceeded)
    MAX_FREQUENCY_HZ = 10.0
    MAX_CONCURRENT_EVENTS = 3
    MIN_COHERENCE_THRESHOLD = 0.50
    DEGRADED_MODE_THRESHOLD = 0.65

    def __init__(self):
        # ... existing init ...

        # NEW: Frequency tracking
        self.ignition_timestamps: Deque[float] = deque(maxlen=100)
        self.frequency_limiter = FrequencyLimiter(self.MAX_FREQUENCY_HZ)

        # NEW: Concurrent event tracking
        self.active_events: Set[str] = set()
        self.max_concurrent = self.MAX_CONCURRENT_EVENTS

        # NEW: Coherence monitoring
        self.coherence_history: Deque[float] = deque(maxlen=10)
        self.degraded_mode = False

        # NEW: Circuit breaker for ignition
        self.ignition_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=10.0
        )

    async def ignite(self, salience_pattern: Dict[str, float]) -> Optional[str]:
        """
        Trigger global ignition with hard bounds

        Returns:
            event_id if ignition successful, None if blocked
        """
        # Check 1: Frequency limiter (HARD LIMIT)
        if not await self.frequency_limiter.allow():
            logger.warning("🛑 ESGT: Ignition BLOCKED by frequency limiter")
            await self._notify_safety_core(
                event="ignition_blocked",
                reason="frequency_limit_exceeded"
            )
            return None

        # Check 2: Concurrent event limit (HARD LIMIT)
        if len(self.active_events) >= self.max_concurrent:
            logger.warning(
                f"🛑 ESGT: Ignition BLOCKED - "
                f"{len(self.active_events)} concurrent events"
            )
            return None

        # Check 3: Circuit breaker
        if self.ignition_breaker.is_open():
            logger.warning("🛑 ESGT: Ignition BLOCKED by circuit breaker")
            return None

        # Check 4: Degraded mode (reduce ignition threshold)
        if self.degraded_mode:
            # In degraded mode, only high-salience patterns ignite
            max_salience = max(salience_pattern.values())
            if max_salience < 0.85:  # Higher threshold
                logger.debug(f"ESGT: Low salience {max_salience:.2f} in degraded mode")
                return None

        try:
            # Attempt ignition with timeout
            async with asyncio.timeout(2.0):  # 2s timeout
                event_id = await self._do_ignition(salience_pattern)

            # Record successful ignition
            self.ignition_timestamps.append(time.time())
            self.active_events.add(event_id)
            self.ignition_breaker.record_success()

            return event_id

        except asyncio.TimeoutError:
            logger.error("⚠️ ESGT: Ignition TIMEOUT (>2s)")
            self.ignition_breaker.record_failure()
            return None

        except Exception as e:
            logger.error(f"⚠️ ESGT: Ignition ERROR: {e}")
            self.ignition_breaker.record_failure()
            return None

    async def _monitor_event_coherence(self, event_id: str):
        """Monitor coherence during event - enforce lower bound"""
        coherence_samples = []

        while event_id in self.active_events:
            try:
                coherence = await self._measure_coherence(event_id)
                coherence_samples.append(coherence)

                # Enforce coherence lower bound (HARD LIMIT)
                if coherence < self.MIN_COHERENCE_THRESHOLD:
                    logger.warning(
                        f"⚠️ ESGT: Coherence {coherence:.2f} below minimum "
                        f"{self.MIN_COHERENCE_THRESHOLD} - ABORTING event {event_id}"
                    )
                    await self._abort_event(event_id, reason="low_coherence")
                    break

                # Check for degraded mode
                if coherence < self.DEGRADED_MODE_THRESHOLD:
                    if not self.degraded_mode:
                        self._enter_degraded_mode()

                await asyncio.sleep(0.01)  # 100Hz sampling

            except Exception as e:
                logger.error(f"Coherence monitoring error: {e}")
                break

        # Record coherence history
        if coherence_samples:
            mean_coherence = sum(coherence_samples) / len(coherence_samples)
            self.coherence_history.append(mean_coherence)

            # Check if can exit degraded mode
            if self.degraded_mode and mean_coherence > 0.80:
                self._exit_degraded_mode()

    def _enter_degraded_mode(self):
        """Enter degraded mode - reduce ignition rate"""
        self.degraded_mode = True
        self.max_concurrent = 1  # Only 1 event at a time

        logger.warning(
            "⚠️ ESGT: Entering DEGRADED MODE - "
            "reducing ignition rate due to low coherence"
        )

        # Notify Safety Core
        asyncio.create_task(self._notify_safety_core(
            event="degraded_mode_entered",
            reason="low_coherence"
        ))

    def _exit_degraded_mode(self):
        """Exit degraded mode - restore normal operation"""
        self.degraded_mode = False
        self.max_concurrent = self.MAX_CONCURRENT_EVENTS

        logger.info("✓ ESGT: Exiting DEGRADED MODE - coherence restored")

    async def _abort_event(self, event_id: str, reason: str):
        """Abort an ongoing ESGT event"""
        logger.warning(f"🛑 ESGT: ABORTING event {event_id} - {reason}")

        # Stop event
        if event_id in self.active_events:
            self.active_events.remove(event_id)

        # Clean up resources
        await self._cleanup_event(event_id)

        # Notify Safety Core
        await self._notify_safety_core(
            event="event_aborted",
            event_id=event_id,
            reason=reason
        )

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get ESGT health metrics for Safety Core"""
        # Compute current frequency
        now = time.time()
        recent_ignitions = [
            t for t in self.ignition_timestamps
            if now - t < 1.0  # Last second
        ]
        current_frequency = len(recent_ignitions)

        # Compute average coherence
        avg_coherence = (
            sum(self.coherence_history) / len(self.coherence_history)
            if self.coherence_history else 0.0
        )

        return {
            "frequency_hz": current_frequency,
            "active_events": len(self.active_events),
            "degraded_mode": self.degraded_mode,
            "average_coherence": avg_coherence,
            "circuit_breaker_state": self.ignition_breaker.state,
        }


class FrequencyLimiter:
    """Hard frequency limiter using token bucket algorithm"""

    def __init__(self, max_frequency_hz: float):
        self.max_frequency = max_frequency_hz
        self.tokens = max_frequency_hz
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def allow(self) -> bool:
        """
        Check if operation is allowed (token available)

        Returns:
            True if allowed, False if rate limit exceeded
        """
        async with self.lock:
            now = time.time()

            # Refill tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_frequency,
                self.tokens + elapsed * self.max_frequency
            )
            self.last_update = now

            # Check if token available
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True

            return False
```

---

### 3. MMEI - Goal Spam Prevention (monitor.py 661 linhas → 800 linhas)

**Problemas Atuais**:
- Goal generation sem bounds
- Pode criar goal spam (centenas de goals)
- Need overflow sem tratamento
- Sem priorização de goals sob load

**REFATORAÇÃO**:

```python
"""
MMEI Monitor - Hardened with Goal Spam Prevention

Additions:
1. Goal generation rate limiting
2. Goal queue with max size
3. Need overflow protection
4. Priority-based goal pruning under load
5. Goal deduplication
"""


class MMEIMonitor:
    """MMEI with goal spam prevention and bounded queues"""

    # HARD LIMITS
    MAX_GOALS_PER_MINUTE = 5
    MAX_ACTIVE_GOALS = 10
    MAX_GOAL_QUEUE_SIZE = 20
    NEED_OVERFLOW_THRESHOLD = 0.95

    def __init__(self):
        # ... existing init ...

        # NEW: Goal rate limiting
        self.goal_rate_limiter = RateLimiter(
            max_per_minute=self.MAX_GOALS_PER_MINUTE
        )

        # NEW: Goal queue with max size
        self.goal_queue: Deque[Goal] = deque(maxlen=self.MAX_GOAL_QUEUE_SIZE)

        # NEW: Goal deduplication
        self.recent_goals: Set[str] = set()  # goal hashes
        self.dedup_window = 60.0  # seconds

        # NEW: Need overflow protection
        self.need_overflow_detected = False

    async def generate_goal(self, need_type: str, need_value: float) -> Optional[Goal]:
        """
        Generate goal with spam prevention

        Returns:
            Goal if generated, None if rate-limited
        """
        # Check 1: Rate limiter (HARD LIMIT)
        if not await self.goal_rate_limiter.allow():
            logger.warning("🛑 MMEI: Goal generation BLOCKED by rate limiter")
            return None

        # Check 2: Active goal limit (HARD LIMIT)
        if len(self._active_goals) >= self.MAX_ACTIVE_GOALS:
            logger.warning(
                f"🛑 MMEI: Max active goals ({self.MAX_ACTIVE_GOALS}) reached"
            )
            # Prune lowest priority goals
            await self._prune_low_priority_goals()

        # Check 3: Need overflow protection
        if need_value > self.NEED_OVERFLOW_THRESHOLD:
            if not self.need_overflow_detected:
                self._handle_need_overflow(need_type, need_value)
            # Allow goal generation in overflow (important)

        # Generate goal
        goal = Goal(
            goal_type=self._need_to_goal_type(need_type),
            source_need=need_type,
            need_value=need_value,
            target_need_value=self._compute_target(need_value),
            priority=self._compute_priority(need_value),
            timestamp=time.time()
        )

        # Check 4: Deduplication
        goal_hash = self._hash_goal(goal)
        if goal_hash in self.recent_goals:
            logger.debug(f"MMEI: Duplicate goal detected - skipping")
            return None

        # Add to active goals and tracking
        self._active_goals.append(goal)
        self.recent_goals.add(goal_hash)
        self.goal_queue.append(goal)

        # Cleanup old hashes (after dedup window)
        asyncio.create_task(self._cleanup_goal_hash(goal_hash))

        return goal

    async def _prune_low_priority_goals(self):
        """Prune lowest priority goals when at capacity"""
        if not self._active_goals:
            return

        # Sort by priority
        sorted_goals = sorted(
            self._active_goals,
            key=lambda g: g.priority
        )

        # Remove lowest priority goal
        lowest = sorted_goals[0]
        self._active_goals.remove(lowest)

        logger.info(
            f"MMEI: Pruned low-priority goal {lowest.goal_type.value} "
            f"(priority {lowest.priority:.2f})"
        )

    def _handle_need_overflow(self, need_type: str, need_value: float):
        """Handle need overflow condition"""
        self.need_overflow_detected = True

        logger.warning(
            f"⚠️ MMEI: NEED OVERFLOW detected - "
            f"{need_type}={need_value:.2f} > {self.NEED_OVERFLOW_THRESHOLD}"
        )

        # Notify Safety Core
        asyncio.create_task(self._notify_safety_core(
            event="need_overflow",
            need_type=need_type,
            need_value=need_value
        ))

    def _hash_goal(self, goal: Goal) -> str:
        """Compute hash for goal deduplication"""
        return f"{goal.goal_type.value}:{goal.source_need}:{goal.need_value:.2f}"

    async def _cleanup_goal_hash(self, goal_hash: str):
        """Remove goal hash after dedup window"""
        await asyncio.sleep(self.dedup_window)
        self.recent_goals.discard(goal_hash)

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get MMEI health metrics for Safety Core"""
        return {
            "active_goals": len(self._active_goals),
            "goal_queue_size": len(self.goal_queue),
            "need_overflow_detected": self.need_overflow_detected,
            "goals_per_minute": self.goal_rate_limiter.get_rate(),
        }


class RateLimiter:
    """Simple rate limiter for goal generation"""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.timestamps: Deque[float] = deque(maxlen=max_per_minute)

    async def allow(self) -> bool:
        """Check if operation is allowed"""
        now = time.time()

        # Remove old timestamps (outside 1 minute window)
        while self.timestamps and now - self.timestamps[0] > 60.0:
            self.timestamps.popleft()

        # Check if under limit
        if len(self.timestamps) < self.max_per_minute:
            self.timestamps.append(now)
            return True

        return False

    def get_rate(self) -> float:
        """Get current rate (goals per minute)"""
        now = time.time()
        recent = [t for t in self.timestamps if now - t < 60.0]
        return len(recent)
```

---

### 4. MCEA - Arousal Bounds (controller.py 649 linhas → 750 linhas)

**Problemas Atuais**:
- Arousal pode ultrapassar [0,1] com modulations múltiplas
- Arousal runaway sem detecção
- Modulation conflicts sem resolução

**REFATORAÇÃO**:

```python
"""
MCEA Arousal Controller - Hardened with Strict Bounds

Additions:
1. Arousal hard clamping [0.0, 1.0]
2. Arousal runaway detection
3. Modulation conflict resolution
4. Arousal change rate limiting
"""


class ArousalController:
    """MCEA with arousal bounds and runaway detection"""

    # HARD LIMITS
    AROUSAL_MIN = 0.0
    AROUSAL_MAX = 1.0
    MAX_AROUSAL_CHANGE_PER_SECOND = 0.5
    RUNAWAY_THRESHOLD = 0.90
    RUNAWAY_DURATION_THRESHOLD = 5.0  # seconds

    def __init__(self):
        # ... existing init ...

        # HARDENED: Arousal strictly bounded
        self._arousal = 0.60

        # NEW: Change rate limiting
        self.last_arousal_update = time.time()
        self.arousal_history: Deque[Tuple[float, float]] = deque(maxlen=100)

        # NEW: Runaway detection
        self.high_arousal_start: Optional[float] = None

    def modulate_arousal(self, delta: float, source: str):
        """
        Modulate arousal with strict bounds

        Args:
            delta: Change in arousal (can be negative)
            source: Source of modulation (for logging)
        """
        now = time.time()
        elapsed = now - self.last_arousal_update

        # Rate limit arousal change
        max_delta = self.MAX_AROUSAL_CHANGE_PER_SECOND * elapsed
        if abs(delta) > max_delta:
            logger.warning(
                f"MCEA: Arousal change {delta:.2f} exceeds rate limit "
                f"{max_delta:.2f} - clamping"
            )
            delta = max(-max_delta, min(max_delta, delta))

        # Apply modulation
        old_arousal = self._arousal
        self._arousal += delta

        # HARD CLAMP to [0, 1]
        self._arousal = max(
            self.AROUSAL_MIN,
            min(self.AROUSAL_MAX, self._arousal)
        )

        # Record change
        self.arousal_history.append((now, self._arousal))
        self.last_arousal_update = now

        # Log significant changes
        if abs(self._arousal - old_arousal) > 0.1:
            logger.info(
                f"MCEA: Arousal {old_arousal:.2f} → {self._arousal:.2f} "
                f"(source: {source})"
            )

        # Check for runaway
        self._check_arousal_runaway()

    def _check_arousal_runaway(self):
        """Detect arousal runaway condition"""
        if self._arousal > self.RUNAWAY_THRESHOLD:
            if self.high_arousal_start is None:
                self.high_arousal_start = time.time()
            elif time.time() - self.high_arousal_start > self.RUNAWAY_DURATION_THRESHOLD:
                # RUNAWAY DETECTED
                logger.critical(
                    f"🔴 MCEA: AROUSAL RUNAWAY DETECTED - "
                    f"sustained at {self._arousal:.2f} for "
                    f"{self.RUNAWAY_DURATION_THRESHOLD}s"
                )

                # Notify Safety Core (may trigger kill switch)
                asyncio.create_task(self._notify_safety_core(
                    event="arousal_runaway",
                    arousal=self._arousal,
                    duration=time.time() - self.high_arousal_start
                ))
        else:
            self.high_arousal_start = None

    def get_current_arousal(self) -> float:
        """Get current arousal (always in [0, 1])"""
        # Double-check bounds (paranoid)
        assert self.AROUSAL_MIN <= self._arousal <= self.AROUSAL_MAX, \
            f"Arousal {self._arousal} outside bounds!"
        return self._arousal

    def get_health_metrics(self) -> Dict[str, Any]:
        """Get MCEA health metrics for Safety Core"""
        # Compute arousal stability (CV)
        if len(self.arousal_history) > 10:
            recent_arousal = [a for t, a in self.arousal_history[-10:]]
            mean_arousal = sum(recent_arousal) / len(recent_arousal)
            std_arousal = (
                sum((a - mean_arousal)**2 for a in recent_arousal) / len(recent_arousal)
            ) ** 0.5
            cv = std_arousal / mean_arousal if mean_arousal > 0 else 0
        else:
            cv = 0.0

        return {
            "arousal": self._arousal,
            "arousal_stability_cv": cv,
            "runaway_detected": self.high_arousal_start is not None,
        }
```

---

### 5. LRR - Recursion Limits (NOVO - ~600 linhas)

**REFATORAÇÃO** (preview):

```python
"""
LRR - Recursive Reasoning Loop (Production-Hardened)

CRITICAL BOUNDS:
1. Max recursion depth: 5 (HARD LIMIT)
2. Max reasoning time: 10s per thought
3. Contradiction overflow protection
4. Stack overflow prevention
"""


class RecursiveReasoningLoop:
    """LRR with strict recursion bounds"""

    MAX_RECURSION_DEPTH = 5
    MAX_REASONING_TIME_SECONDS = 10.0
    MAX_CONTRADICTIONS_PER_THOUGHT = 10

    async def reflect(
        self,
        thought: Any,
        current_depth: int = 0
    ) -> ReflectionResult:
        """
        Recursive reflection with hard bounds

        Raises:
            RecursionLimitError: If depth exceeds MAX_RECURSION_DEPTH
            TimeoutError: If reasoning exceeds MAX_REASONING_TIME_SECONDS
        """
        # HARD LIMIT: Check recursion depth
        if current_depth >= self.MAX_RECURSION_DEPTH:
            raise RecursionLimitError(
                f"Max recursion depth {self.MAX_RECURSION_DEPTH} exceeded"
            )

        # HARD LIMIT: Reasoning timeout
        async with asyncio.timeout(self.MAX_REASONING_TIME_SECONDS):
            # ... reflection logic ...
            pass
```

---

## 🧪 TESTING REQUIREMENTS

### Coverage Target: ≥95% para todos os componentes

**Test Files** (total ~2000 linhas):

1. `test_tig_hardening.py` (400 linhas)
2. `test_esgt_hardening.py` (400 linhas)
3. `test_mmei_hardening.py` (400 linhas)
4. `test_mcea_hardening.py` (400 linhas)
5. `test_lrr_bounds.py` (400 linhas)

---

## 📊 VALIDAÇÃO

### Critérios de Aceitação

✅ TIG survives 10% node failures without partition
✅ ESGT never exceeds 10Hz (tested under load)
✅ MMEI never generates >5 goals/min
✅ MCEA arousal always in [0, 1]
✅ LRR never exceeds depth 5
✅ All components have graceful degradation
✅ Health metrics exposed to Safety Core
✅ Circuit breakers functional

---

## 🔗 INTEGRATION COM PART 1

**Safety Core Integration Points**:

```python
# Each component exposes health metrics
tig_metrics = tig.get_health_metrics()
esgt_metrics = esgt.get_health_metrics()
mmei_metrics = mmei.get_health_metrics()
mcea_metrics = mcea.get_health_metrics()

# Safety Core monitors all metrics
safety_protocol.monitor_component_health({
    "tig": tig_metrics,
    "esgt": esgt_metrics,
    "mmei": mmei_metrics,
    "mcea": mcea_metrics,
})

# If critical violations detected → Kill Switch
```

---

**CONCLUSÃO**: Esta refatoração adiciona camadas robustas de proteção em TODOS os componentes de consciência, garantindo bounds rigorosos e fail-safes.

**DEPLOY**: Somente após PART 1 (Safety Core) estar 100% validado.
