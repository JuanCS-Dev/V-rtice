"""Digital Lymphnode - Regional Immune Coordination Hub

The Lymphnode implements regional coordination for immune agents:
1. Agent orchestration (creation, cloning, destruction)
2. Cytokine aggregation and filtering (noise reduction)
3. Pattern detection (attack chains, persistent threats)
4. Memory consolidation triggers
5. Homeostatic regulation (temperature-based activation)

Biological inspiration:
- Lymphnodes are regional hubs where immune cells congregate
- Antigen-presenting cells activate adaptive immunity
- Clonal expansion occurs in lymphnode germinal centers
- Memory B/T cells are formed and stored

Hierarchy:
- Local Lymphnode: 1 per subnet (handles 10-100 agents)
- Regional Lymphnode: 1 per availability zone (handles 100-1000 agents)
- Global Lymphnode: 1 per datacenter (MAXIMUS integration)

PRODUCTION-READY: Real Kafka, Redis, no mocks, graceful degradation.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as aioredis
from aiokafka import AIOKafkaConsumer

from agents import AgentFactory, AgentType
from agents.models import AgenteState
from coordination.agent_orchestrator import AgentOrchestrator
from coordination.cytokine_aggregator import CytokineAggregator
from coordination.exceptions import (
    AgentOrchestrationError,
    CytokineProcessingError,
    HormonePublishError,
    LymphnodeConnectionError,
    LymphnodeRateLimitError,
    LymphnodeResourceExhaustedError,
    PatternDetectionError,
)
from coordination.lymphnode_metrics import LymphnodeMetrics
from coordination.pattern_detector import PatternDetector
from coordination.rate_limiter import ClonalExpansionRateLimiter
from coordination.temperature_controller import HomeostaticState, TemperatureController
from coordination.thread_safe_structures import (
    ThreadSafeBuffer,
    ThreadSafeCounter,
)

logger = logging.getLogger(__name__)

# ESGT Integration (optional dependency - no path manipulation)
try:
    from consciousness.esgt.coordinator import ESGTEvent
    from consciousness.integration import ESGTSubscriber

    ESGT_AVAILABLE = True
except ImportError:
    ESGT_AVAILABLE = False
    ESGTSubscriber = None  # type: ignore
    ESGTEvent = None  # type: ignore
    logger.info("ESGT integration not available (consciousness module not found)")


class LinfonodoDigital:
    """
    Digital Lymphnode - Regional immune coordination hub.

    Responsibilities:
    - Agent orchestration (clone creation/destruction)
    - Cytokine aggregation and filtering
    - Pattern detection (attack chains)
    - Memory consolidation triggers
    - Homeostatic regulation

    Hierarchy:
    - Local Lymphnode: 1 per subnet
    - Regional Lymphnode: 1 per availability zone
    - Global Lymphnode: 1 per datacenter (MAXIMUS integration)
    """

    def __init__(
        self,
        lymphnode_id: str,
        nivel: str = "local",  # local, regional, global
        area_responsabilidade: str = "default",
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        agent_factory: Optional[AgentFactory] = None,
    ):
        """
        Initialize Digital Lymphnode.

        Args:
            lymphnode_id: Unique identifier
            nivel: Hierarchy level (local, regional, global)
            area_responsabilidade: Network area (subnet, zone, datacenter)
            kafka_bootstrap: Kafka broker for cytokines
            redis_url: Redis URL for hormones
            agent_factory: AgentFactory instance (creates new one if None)
        """
        self.id = lymphnode_id
        self.nivel = nivel
        self.area = area_responsabilidade

        self.kafka_bootstrap = kafka_bootstrap
        self.redis_url = redis_url

        # Agent factory (for cloning)
        self.factory = agent_factory or AgentFactory(
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
        )

        # Agent registry (track agents in this area)
        self.agentes_ativos: Dict[str, AgenteState] = {}
        self.agentes_dormindo: Set[str] = set()

        # Cytokine aggregation (THREAD-SAFE)
        self.cytokine_buffer = ThreadSafeBuffer[Dict[str, Any]](maxsize=1000)

        # Temperature controller (FASE 3 - Dependency Injection)
        self._temperature_controller = TemperatureController(
            lymphnode_id=self.id,
            initial_temp=37.0,
            min_temp=36.0,
            max_temp=42.0,
        )
        # Keep backward compatibility reference
        self.temperatura_regional = self._temperature_controller.temperature

        # Pattern detection (THREAD-SAFE)
        self.threat_detections = ThreadSafeCounter[str]()
        self.last_pattern_check: datetime = datetime.now()

        # Pattern detector (FASE 3 - Dependency Injection)
        self._pattern_detector = PatternDetector(
            persistent_threshold=5,
            coordinated_threshold=10,
            time_window_sec=60.0,
        )

        # Cytokine aggregator (FASE 3 - Dependency Injection)
        self._cytokine_aggregator = CytokineAggregator(
            area=self.area,
            nivel=self.nivel,
            escalation_priority_threshold=9,
        )

        # Agent orchestrator (FASE 3 - Dependency Injection)
        self._agent_orchestrator = AgentOrchestrator(
            lymphnode_id=self.id,
            area=self.area,
            factory=self.factory,
            rate_limiter=None,  # Will use AgentOrchestrator's internal rate limiter
            redis_client=None,  # Will be set later when Redis connects
        )

        # Lymphnode metrics (FASE 3 - Dependency Injection)
        self._lymphnode_metrics = LymphnodeMetrics(
            lymphnode_id=self.id,
        )
        # Keep backward compatibility references
        self.total_ameacas_detectadas = self._lymphnode_metrics.total_ameacas_detectadas
        self.total_neutralizacoes = self._lymphnode_metrics.total_neutralizacoes
        self.total_clones_criados = self._lymphnode_metrics.total_clones_criados
        self.total_clones_destruidos = self._lymphnode_metrics.total_clones_destruidos

        # Rate limiting
        self._clonal_limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # ESGT Integration (consciousness ignition)
        self.esgt_subscriber: Optional["ESGTSubscriber"] = None
        self.recent_ignitions: List["ESGTEvent"] = []
        self.max_ignition_history: int = 100

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False

        # Redis client
        self._redis_client: Optional[aioredis.Redis] = None

        logger.info(f"Lymphnode {self.id} ({self.nivel}) initialized for {self.area}")

    async def get_homeostatic_state(self) -> HomeostaticState:
        """
        Compute homeostatic state based on current temperature.

        REFACTORED (FASE 3): Delegates to TemperatureController.

        Returns:
            HomeostaticState enum value
        """
        return await self._temperature_controller.get_homeostatic_state()

    @property
    def homeostatic_state(self) -> HomeostaticState:
        """
        DEPRECATED: Synchronous property for backward compatibility.
        Use get_homeostatic_state() instead for accurate async access.

        Returns:
            HomeostaticState enum (may be stale if temperature changed recently)
        """
        # Try to get current temp, but fall back to last known value
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't block in running loop, return VIGILANCIA as safe default
                return HomeostaticState.VIGILANCIA
            else:
                temp = loop.run_until_complete(self.temperatura_regional.get())
        except:
            # Fallback
            temp = 37.0

        if temp >= 39.0:
            return HomeostaticState.INFLAMACAO
        elif temp >= 38.0:
            return HomeostaticState.ATIVACAO
        elif temp >= 37.5:
            return HomeostaticState.ATENCAO
        elif temp >= 37.0:
            return HomeostaticState.VIGILANCIA
        else:
            return HomeostaticState.REPOUSO

    # ==================== ESGT INTEGRATION ====================

    def set_esgt_subscriber(self, subscriber: "ESGTSubscriber") -> None:
        """
        Set ESGT subscriber for conscious ignition integration.

        Args:
            subscriber: ESGTSubscriber instance
        """
        if not ESGT_AVAILABLE:
            logger.warning("ESGT integration not available (module not found)")
            return

        self.esgt_subscriber = subscriber
        # Register handler for ESGT ignition events
        subscriber.on_ignition(self._handle_esgt_ignition)
        logger.info(f"Lymphnode {self.id} connected to ESGT (ignition response enabled)")

    async def _handle_esgt_ignition(self, event: "ESGTEvent") -> None:
        """
        Handle ESGT ignition event.

        High salience conscious events trigger coordinated immune response.

        Args:
            event: ESGT ignition event
        """
        # Store event
        self.recent_ignitions.append(event)
        if len(self.recent_ignitions) > self.max_ignition_history:
            self.recent_ignitions.pop(0)

        # Extract salience
        salience = event.salience.composite_score()

        logger.info(f"🧠 ESGT ignition detected (salience={salience:.2f}, event_id={event.id})")

        # High salience → Threat response
        if salience > 0.8:
            logger.warning(f"🚨 High salience ESGT ({salience:.2f}) → Triggering immune activation")

            # Increase temperature (inflammation)
            await self._adjust_temperature(delta=+1.0)

            # Broadcast pro-inflammatory cytokine
            await self._broadcast_hormone(
                hormone_type="IL-1",
                level=salience,
                source=f"esgt_ignition_{event.id}",
            )

            logger.info("Immune activation triggered by conscious event")

        # Medium salience → Increase vigilance
        elif salience > 0.6:
            logger.info(f"📊 Medium salience ESGT ({salience:.2f}) → Increasing vigilance")
            await self._adjust_temperature(delta=+0.5)

        # Low salience → No action
        else:
            logger.debug(f"Low salience ESGT ({salience:.2f}) → No immune action")

    async def _adjust_temperature(self, delta: float) -> None:
        """
        Adjust regional temperature.

        REFACTORED (FASE 3): Delegates to TemperatureController.

        Args:
            delta: Temperature change (positive = increase, negative = decrease)
        """
        await self._temperature_controller.adjust_temperature(delta)

    async def _broadcast_hormone(self, hormone_type: str, level: float, source: str) -> None:
        """
        Broadcast hormone signal via Redis (global).

        Args:
            hormone_type: Type of hormone (e.g., "IL-1", "IL-6")
            level: Hormone level (0-1)
            source: Source of signal
        """
        if not self._redis_client:
            logger.warning("Redis unavailable, cannot broadcast hormone")
            return

        try:
            message = {
                "lymphnode_id": self.id,
                "hormone_type": hormone_type,
                "level": level,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            }

            await self._redis_client.publish(f"immunis:hormones:{hormone_type}", json.dumps(message))

            logger.debug(f"Broadcast hormone {hormone_type} (level={level:.2f})")

        except (ConnectionError, TimeoutError) as e:
            raise HormonePublishError(f"Failed to broadcast hormone: {e}")
        except Exception as e:
            logger.error(f"Unexpected error broadcasting hormone: {e}")
            raise HormonePublishError(f"Unexpected hormone broadcast error: {e}")

    # ==================== LIFECYCLE ====================

    async def iniciar(self) -> None:
        """
        Start lymphnode operations.

        Starts background tasks:
        - Cytokine aggregation (Kafka consumer)
        - Temperature monitoring
        - Pattern detection
        - Homeostatic regulation
        """
        if self._running:
            logger.warning(f"Lymphnode {self.id} already running")
            return

        self._running = True

        # Initialize Redis client
        try:
            self._redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info(f"Lymphnode {self.id} connected to Redis")
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e} (graceful degradation)")
            self._redis_client = None
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            raise LymphnodeConnectionError(f"Redis initialization failed: {e}")

        # Start background tasks
        self._tasks.append(asyncio.create_task(self._aggregate_cytokines()))
        self._tasks.append(asyncio.create_task(self._monitor_temperature()))
        self._tasks.append(asyncio.create_task(self._detect_patterns()))
        self._tasks.append(asyncio.create_task(self._regulate_homeostasis()))

        logger.info(f"Lymphnode {self.id} started ({len(self._tasks)} background tasks)")

    async def parar(self) -> None:
        """
        Stop lymphnode gracefully.

        Cancels all background tasks and closes connections.
        """
        if not self._running:
            return

        logger.info(f"Stopping lymphnode {self.id}")

        self._running = False

        # Cancel all background tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Close Redis client
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

        logger.info(f"Lymphnode {self.id} stopped")

    # ==================== AGENT ORCHESTRATION ====================

    async def registrar_agente(self, agente_state: AgenteState) -> None:
        """
        Register agent with lymphnode.

        REFACTORED (FASE 3): Delegates to AgentOrchestrator.

        Args:
            agente_state: Agent state snapshot
        """
        await self._agent_orchestrator.register_agent(agente_state)
        # Keep local reference for backward compatibility
        self.agentes_ativos = self._agent_orchestrator.agentes_ativos

    async def remover_agente(self, agente_id: str) -> None:
        """
        Remove agent from lymphnode (apoptosis/migration).

        REFACTORED (FASE 3): Delegates to AgentOrchestrator.

        Args:
            agente_id: Agent UUID
        """
        await self._agent_orchestrator.remove_agent(agente_id)
        # Keep local reference for backward compatibility
        self.agentes_ativos = self._agent_orchestrator.agentes_ativos

    async def clonar_agente(
        self,
        tipo_base: AgentType,
        especializacao: str,
        quantidade: int = 5,
    ) -> List[str]:
        """
        Create specialized agent clones (clonal expansion) WITH RATE LIMITING.

        REFACTORED (FASE 3): Delegates to AgentOrchestrator.

        Args:
            tipo_base: Base agent type to clone
            especializacao: Specialization marker
            quantidade: Number of clones to create

        Returns:
            List of clone IDs

        Raises:
            LymphnodeRateLimitError: If rate limit exceeded
            LymphnodeResourceExhaustedError: If resource limit exceeded
            AgentOrchestrationError: If clone creation fails
        """
        # Delegate to AgentOrchestrator
        clone_ids = await self._agent_orchestrator.create_clones(
            tipo_base=tipo_base,
            especializacao=especializacao,
            quantidade=quantidade,
        )

        # Update local references
        self.agentes_ativos = self._agent_orchestrator.agentes_ativos
        stats = await self._agent_orchestrator.get_stats()

        # Update local metrics
        for _ in range(len(clone_ids)):
            await self.total_clones_criados.increment()

        return clone_ids

    async def destruir_clones(self, especializacao: str) -> int:
        """
        Destroy clones with specific specialization (apoptosis).

        REFACTORED (FASE 3): Delegates to AgentOrchestrator.

        Args:
            especializacao: Specialization marker

        Returns:
            Number of clones destroyed
        """
        # Delegate to AgentOrchestrator
        destruidos = await self._agent_orchestrator.destroy_clones(especializacao)

        # Update local references
        self.agentes_ativos = self._agent_orchestrator.agentes_ativos

        # Update local metrics
        for _ in range(destruidos):
            await self.total_clones_destruidos.increment()

        return destruidos

    async def _send_apoptosis_signal(self, agente_id: str) -> None:
        """
        Send apoptosis signal to agent via Redis.

        Args:
            agente_id: Agent UUID
        """
        if not self._redis_client:
            logger.debug("Redis client not available for apoptosis signal")
            return

        try:
            await self._redis_client.publish(
                f"agent:{agente_id}:apoptosis",
                json.dumps(
                    {
                        "lymphnode_id": self.id,
                        "reason": "lymphnode_directive",
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            )

            logger.debug(f"Apoptosis signal sent to agent {agente_id[:8]}")

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Failed to send apoptosis signal (Redis unavailable): {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending apoptosis signal: {e}")
            raise HormonePublishError(f"Failed to send apoptosis signal to {agente_id}: {e}")

    # ==================== CYTOKINE PROCESSING ====================

    async def _aggregate_cytokines(self) -> None:
        """
        Aggregate cytokines from Kafka (PRODUCTION).

        Consumes cytokines from all agents and processes them at regional level.
        """
        consumer = None

        try:
            consumer = AIOKafkaConsumer(
                "immunis.cytokines.IL1",
                "immunis.cytokines.IL6",
                "immunis.cytokines.IL8",
                "immunis.cytokines.IL10",
                "immunis.cytokines.IL12",
                "immunis.cytokines.TNF",
                "immunis.cytokines.IFNgamma",
                "immunis.cytokines.TGFbeta",
                bootstrap_servers=self.kafka_bootstrap,
                group_id=f"lymphnode_{self.id}",
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )

            await consumer.start()

            logger.info(f"Lymphnode {self.id} started cytokine aggregation")

            async for msg in consumer:
                if not self._running:
                    break

                citocina = msg.value

                # VALIDATION: Validate cytokine via CytokineAggregator (FASE 3)
                citocina_dict = await self._cytokine_aggregator.validate_and_parse(citocina)
                if not citokina_dict:
                    continue

                # Filter by area via CytokineAggregator (FASE 3)
                if await self._cytokine_aggregator.should_process_for_area(citocina_dict):
                    # Add to buffer (THREAD-SAFE)
                    await self.cytokine_buffer.append(citocina_dict)

                    # Process at regional level
                    await self._processar_citocina_regional(citocina_dict)

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Kafka connection error: {e}")
            raise LymphnodeConnectionError(f"Kafka consumer failed: {e}")
        except Exception as e:
            logger.error(f"Cytokine aggregation error: {e}")
            raise CytokineProcessingError(f"Failed to aggregate cytokines: {e}")

        finally:
            if consumer:
                await consumer.stop()

    async def _processar_citocina_regional(self, citocina: Dict[str, Any]) -> None:
        """
        Process cytokine at regional level.

        REFACTORED (FASE 3): Delegates to CytokineAggregator for processing logic.

        Updates:
        - Regional temperature (via CytokineAggregator)
        - Threat detection counts (via ProcessingResult)
        - Metrics (via ProcessingResult)

        Args:
            citocina: Cytokine message
        """
        # Process cytokine via CytokineAggregator (FASE 3)
        result = await self._cytokine_aggregator.process_cytokine(citocina)

        # Update regional temperature based on result
        if result.temperature_delta != 0.0:
            await self.temperatura_regional.adjust(result.temperature_delta)

        # Track threat detection
        if result.threat_detected:
            # ATOMIC INCREMENT
            await self.total_ameacas_detectadas.increment()

            # Track threat for pattern detection (THREAD-SAFE)
            if result.threat_id:
                await self.threat_detections.increment(result.threat_id)

        # Track neutralization
        elif result.neutralization:
            # ATOMIC INCREMENT
            await self.total_neutralizacoes.increment()

        # Escalate to global lymphnode if critical
        if result.should_escalate:
            await self._escalar_para_global(citocina)

        current_temp = await self.temperatura_regional.get()
        logger.debug(
            f"Lymphnode {self.id} processed cytokine: {result.metadata.get('tipo')} (temp={current_temp:.1f}°C)"
        )

    async def _escalar_para_global(self, citocina: Dict[str, Any]) -> None:
        """
        Escalate critical cytokine to global lymphnode (MAXIMUS).

        Uses hormones (Redis Pub/Sub) for global communication.

        Args:
            citocina: Critical cytokine message
        """
        if not self._redis_client:
            logger.debug("Redis client not available for escalation")
            return

        try:
            logger.warning(
                f"Lymphnode {self.id} escalating critical cytokine to MAXIMUS: "
                f"{citocina.get('tipo')} (priority={citocina.get('prioridade')})"
            )

            # Send via cortisol hormone (stress signal)
            await self._redis_client.publish(
                "hormonio:cortisol",
                json.dumps(
                    {
                        "origem": self.id,
                        "citocina": citocina,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            )

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Escalation failed (Redis unavailable): {e}")
        except Exception as e:
            logger.error(f"Unexpected escalation error: {e}")

    # ==================== PATTERN DETECTION ====================

    async def _detect_patterns(self) -> None:
        """
        Detect attack patterns from cytokine stream.

        Patterns detected:
        - Persistent threat (same threat_id detected 5+ times)
        - Coordinated attack (multiple threats in short time)
        - APT indicators (low-and-slow pattern)
        """
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Get buffer size (THREAD-SAFE)
                buffer_size = await self.cytokine_buffer.size()
                if buffer_size < 10:
                    continue

                # Analyze recent cytokines (last 100) - THREAD-SAFE
                recentes = await self.cytokine_buffer.get_recent(100)

                # Check for persistent threats
                await self._detect_persistent_threats()

                # Check for coordinated attacks
                await self._detect_coordinated_attacks(recentes)

                # Clear old threat detections (keep last hour)
                if (datetime.now() - self.last_pattern_check).total_seconds() > 3600:
                    await self.threat_detections.clear()
                    self.last_pattern_check = datetime.now()

            except asyncio.CancelledError:
                break

            except PatternDetectionError as e:
                logger.error(f"Pattern detection error: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in pattern detection: {e}")

    async def _detect_persistent_threats(self) -> None:
        """
        Detect threats that persist across multiple detections.

        If same threat detected 5+ times, trigger clonal expansion.

        REFACTORED (FASE 3): Delegates to PatternDetector.
        """
        # Get all threat counts (THREAD-SAFE)
        threat_items = await self.threat_detections.items()
        threat_counts_dict = dict(threat_items)

        # Use PatternDetector to identify persistent threats
        patterns = await self._pattern_detector.detect_persistent_threats(threat_counts_dict)

        for pattern in patterns:
            threat_id = pattern.threat_ids[0]  # Single threat per persistent pattern

            logger.warning(
                f"Lymphnode {self.id} detected PERSISTENT THREAT: {threat_id} "
                f"({pattern.detection_count} detections, confidence={pattern.confidence:.2f})"
            )

            try:
                # Trigger clonal expansion (Neutrophil swarm)
                await self.clonar_agente(
                    tipo_base=AgentType.NEUTROFILO,
                    especializacao=f"threat_{threat_id}",
                    quantidade=10,
                )

                # Clear count (avoid re-triggering) - set to 0
                current = await self.threat_detections.get(threat_id)
                if current > 0:
                    # Reset by decrement
                    await self.threat_detections.increment(threat_id, -current)

            except (LymphnodeRateLimitError, LymphnodeResourceExhaustedError) as e:
                logger.warning(f"Cannot trigger clonal expansion for persistent threat: {e}")
            except AgentOrchestrationError as e:
                logger.error(f"Clonal expansion failed for persistent threat: {e}")

    async def _detect_coordinated_attacks(self, cytokines: List[Dict[str, Any]]) -> None:
        """
        Detect coordinated attacks (multiple threats in short time).

        If 10+ threats detected in last minute, trigger mass response.

        REFACTORED (FASE 3): Delegates to PatternDetector.

        Args:
            cytokines: Recent cytokine messages
        """
        # Use PatternDetector to identify coordinated attacks
        patterns = await self._pattern_detector.detect_coordinated_attacks(cytokines)

        for pattern in patterns:
            logger.critical(
                f"Lymphnode {self.id} detected COORDINATED ATTACK: "
                f"{pattern.detection_count} threats in last {pattern.time_window_sec}s "
                f"(confidence={pattern.confidence:.2f}, "
                f"unique_threats={pattern.metadata.get('unique_threats', 0)})"
            )

            try:
                # Massive Neutrophil swarm
                await self.clonar_agente(
                    tipo_base=AgentType.NEUTROFILO,
                    especializacao="coordinated_attack_response",
                    quantidade=50,
                )
            except (LymphnodeRateLimitError, LymphnodeResourceExhaustedError) as e:
                logger.error(f"Cannot trigger mass response (rate limited): {e}")
            except AgentOrchestrationError as e:
                logger.error(f"Mass response clonal expansion failed: {e}")

    # ==================== HOMEOSTATIC REGULATION ====================

    async def _monitor_temperature(self) -> None:
        """
        Monitor regional temperature (decay over time).

        Temperature represents inflammatory state:
        - 36.5-37.0: Repouso (homeostasis)
        - 37.0-37.5: Vigilância
        - 37.5-38.0: Atenção
        - 38.0-39.0: Ativação
        - 39.0+: Inflamação (cytokine storm)
        """
        while self._running:
            try:
                await asyncio.sleep(30)

                # Temperature decay (anti-inflammatory drift) - REFACTORED (FASE 3)
                current_temp = await self._temperature_controller.apply_decay()

                logger.debug(
                    f"Lymphnode {self.id} temperature: {current_temp:.1f}°C (agents: {len(self.agentes_ativos)})"
                )

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Unexpected temperature monitoring error: {e}")

    async def _regulate_homeostasis(self) -> None:
        """
        Regulate homeostatic state based on temperature.

        Activation levels:
        - Repouso (36.5-37.0): 5% agents active
        - Vigilância (37.0-37.5): 15% agents active
        - Atenção (37.5-38.0): 30% agents active
        - Ativação (38.0-39.0): 50% agents active
        - Inflamação (39.0+): 80% agents active
        """
        while self._running:
            try:
                await asyncio.sleep(60)

                total_agents = len(self.agentes_ativos)

                if total_agents == 0:
                    continue

                # Get current temperature (THREAD-SAFE)
                current_temp = await self.temperatura_regional.get()

                # Determine target active percentage
                if current_temp >= 39.0:
                    target_percentage = 0.8  # Inflamação
                    state_name = "INFLAMAÇÃO"

                elif current_temp >= 38.0:
                    target_percentage = 0.5  # Ativação
                    state_name = "ATIVAÇÃO"

                elif current_temp >= 37.5:
                    target_percentage = 0.3  # Atenção
                    state_name = "ATENÇÃO"

                elif current_temp >= 37.0:
                    target_percentage = 0.15  # Vigilância
                    state_name = "VIGILÂNCIA"

                else:
                    target_percentage = 0.05  # Repouso
                    state_name = "REPOUSO"

                target_active = int(total_agents * target_percentage)

                logger.info(
                    f"Lymphnode {self.id} homeostatic state: {state_name} "
                    f"(temp={current_temp:.1f}°C, "
                    f"target_active={target_active}/{total_agents})"
                )

                # Send wake/sleep hormones via Redis
                await self._broadcast_activation_level(state_name, target_percentage)

            except asyncio.CancelledError:
                break

            except HormonePublishError as e:
                logger.warning(f"Hormone broadcast failed (non-critical): {e}")
            except Exception as e:
                logger.error(f"Unexpected homeostasis regulation error: {e}")

    async def _broadcast_activation_level(self, state_name: str, target_percentage: float) -> None:
        """
        Broadcast activation level to all agents via hormones.

        Args:
            state_name: Homeostatic state name
            target_percentage: Target percentage of agents that should be active
        """
        if not self._redis_client:
            logger.debug("Redis client not available for hormone broadcast")
            return

        try:
            current_temp = await self.temperatura_regional.get()

            # Broadcast via adrenaline hormone (activation signal)
            await self._redis_client.publish(
                "hormonio:adrenalina",
                json.dumps(
                    {
                        "lymphnode_id": self.id,
                        "state": state_name,
                        "target_activation": target_percentage,
                        "temperatura_regional": current_temp,
                        "timestamp": datetime.now().isoformat(),
                    }
                ),
            )

            logger.debug(f"Activation level broadcast: {state_name} ({target_percentage:.0%})")

        except (ConnectionError, TimeoutError) as e:
            raise HormonePublishError(f"Redis unavailable for hormone broadcast: {e}")
        except Exception as e:
            logger.error(f"Unexpected hormone broadcast error: {e}")
            raise HormonePublishError(f"Failed to broadcast activation level: {e}")

    # ==================== METRICS ====================

    async def get_lymphnode_metrics(self) -> Dict[str, Any]:
        """
        Get lymphnode statistics (ASYNC - thread-safe).

        REFACTORED (FASE 3): Aggregates stats from all extracted components.

        Returns:
            Dict with lymphnode metrics
        """
        # Get stats from extracted components (FASE 3)
        temp_stats = await self._temperature_controller.get_stats()
        metrics_stats = await self._lymphnode_metrics.get_stats()
        agent_stats = await self._agent_orchestrator.get_stats()
        pattern_stats = self._pattern_detector.get_stats()  # Sync method

        # Get local state
        buffer_size = await self.cytokine_buffer.size()
        threats_tracked = await self.threat_detections.size()

        return {
            # Identification
            "lymphnode_id": self.id,
            "nivel": self.nivel,
            "area": self.area,
            # Temperature & homeostasis (from TemperatureController)
            "temperatura_regional": temp_stats["current_temperature"],
            "homeostatic_state": temp_stats["homeostatic_state"],
            # Agent orchestration (from AgentOrchestrator)
            "agentes_total": agent_stats["active_agents"],
            "agentes_dormindo": agent_stats["sleeping_agents"],
            "total_clones_created_history": agent_stats["total_clones_created"],
            "total_clones_destroyed_history": agent_stats["total_clones_destroyed"],
            # Metrics (from LymphnodeMetrics)
            "ameacas_detectadas": metrics_stats["total_threats_detected"],
            "neutralizacoes": metrics_stats["total_neutralizations"],
            "clones_criados": metrics_stats["total_clones_created"],
            "clones_destruidos": metrics_stats["total_clones_destroyed"],
            "neutralization_rate": metrics_stats["neutralization_rate"],
            # Pattern detection (from PatternDetector)
            "persistent_threats_detected": pattern_stats["persistent_patterns"],
            "coordinated_attacks_detected": pattern_stats["coordinated_patterns"],
            # Local state
            "cytokine_buffer_size": buffer_size,
            "threats_being_tracked": threats_tracked,
            "rate_limiter_stats": self._clonal_limiter.get_stats(),
        }

    def __repr__(self) -> str:
        """String representation"""
        # Get temperature safely (blocking call acceptable for repr)
        try:
            temp = asyncio.get_event_loop().run_until_complete(self.temperatura_regional.get())
        except RuntimeError:
            temp = 37.0  # Fallback if no event loop

        return (
            f"LinfonodoDigital({self.id}|{self.nivel}|"
            f"area={self.area}|"
            f"agents={len(self.agentes_ativos)}|"
            f"temp={temp:.1f}°C)"
        )
