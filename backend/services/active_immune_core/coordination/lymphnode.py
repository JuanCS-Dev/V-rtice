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
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import redis.asyncio as aioredis
from aiokafka import AIOKafkaConsumer

from agents import AgentFactory, AgentType
from agents.models import AgenteState

logger = logging.getLogger(__name__)

# ESGT Integration (optional dependency)
try:
    import sys
    sys.path.insert(0, '/home/juan/vertice-dev/backend/services/maximus_core_service')
    from consciousness.integration import ESGTSubscriber
    from consciousness.esgt.coordinator import ESGTEvent
    ESGT_AVAILABLE = True
except ImportError:
    ESGT_AVAILABLE = False
    logger.warning("ESGT integration not available (consciousness module not found)")


class HomeostaticState(str, Enum):
    """Homeostatic states based on temperature."""
    REPOUSO = "REPOUSO"  # < 37.0°C
    VIGILANCIA = "VIGILÂNCIA"  # 37.0-37.5°C
    ATENCAO = "ATENÇÃO"  # 37.5-38.0°C
    ATIVACAO = "ATIVAÇÃO"  # 38.0-39.0°C
    INFLAMACAO = "INFLAMAÇÃO"  # >= 39.0°C


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

        # Cytokine aggregation
        self.cytokine_buffer: List[Dict[str, Any]] = []
        self.temperatura_regional: float = 37.0

        # Pattern detection
        self.threat_detections: Dict[str, int] = defaultdict(int)  # threat_id -> count
        self.last_pattern_check: datetime = datetime.now()

        # Metrics
        self.total_ameacas_detectadas: int = 0
        self.total_neutralizacoes: int = 0
        self.total_clones_criados: int = 0
        self.total_clones_destruidos: int = 0

        # ESGT Integration (consciousness ignition)
        self.esgt_subscriber: Optional['ESGTSubscriber'] = None
        self.recent_ignitions: List['ESGTEvent'] = []
        self.max_ignition_history: int = 100

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False

        # Redis client
        self._redis_client: Optional[aioredis.Redis] = None

        logger.info(
            f"Lymphnode {self.id} ({self.nivel}) initialized for {self.area}"
        )

    @property
    def homeostatic_state(self) -> HomeostaticState:
        """Compute homeostatic state based on current temperature."""
        if self.temperatura_regional >= 39.0:
            return HomeostaticState.INFLAMACAO
        elif self.temperatura_regional >= 38.0:
            return HomeostaticState.ATIVACAO
        elif self.temperatura_regional >= 37.5:
            return HomeostaticState.ATENCAO
        elif self.temperatura_regional >= 37.0:
            return HomeostaticState.VIGILANCIA
        else:
            return HomeostaticState.REPOUSO

    # ==================== ESGT INTEGRATION ====================

    def set_esgt_subscriber(self, subscriber: 'ESGTSubscriber') -> None:
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

    async def _handle_esgt_ignition(self, event: 'ESGTEvent') -> None:
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

        logger.info(
            f"🧠 ESGT ignition detected (salience={salience:.2f}, event_id={event.id})"
        )

        # High salience → Threat response
        if salience > 0.8:
            logger.warning(
                f"🚨 High salience ESGT ({salience:.2f}) → Triggering immune activation"
            )

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
            logger.info(
                f"📊 Medium salience ESGT ({salience:.2f}) → Increasing vigilance"
            )
            await self._adjust_temperature(delta=+0.5)

        # Low salience → No action
        else:
            logger.debug(f"Low salience ESGT ({salience:.2f}) → No immune action")

    async def _adjust_temperature(self, delta: float) -> None:
        """
        Adjust regional temperature.

        Args:
            delta: Temperature change (positive = increase, negative = decrease)
        """
        old_temp = self.temperatura_regional
        self.temperatura_regional = max(36.0, min(40.0, self.temperatura_regional + delta))

        logger.info(
            f"Lymphnode {self.id} temperature: {old_temp:.1f}°C → {self.temperatura_regional:.1f}°C "
            f"(state={self.homeostatic_state.value})"
        )

    async def _broadcast_hormone(
        self, hormone_type: str, level: float, source: str
    ) -> None:
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

            await self._redis_client.publish(
                f"immunis:hormones:{hormone_type}", json.dumps(message)
            )

            logger.debug(f"Broadcast hormone {hormone_type} (level={level:.2f})")

        except Exception as e:
            logger.warning(f"Failed to broadcast hormone: {e}")

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
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self._redis_client = None

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

        Args:
            agente_state: Agent state snapshot
        """
        self.agentes_ativos[agente_state.id] = agente_state

        logger.info(
            f"Agent {agente_state.id[:8]} ({agente_state.tipo}) registered "
            f"with lymphnode {self.id}"
        )

    async def remover_agente(self, agente_id: str) -> None:
        """
        Remove agent from lymphnode (apoptosis/migration).

        Args:
            agente_id: Agent UUID
        """
        if agente_id in self.agentes_ativos:
            agente_state = self.agentes_ativos[agente_id]
            del self.agentes_ativos[agente_id]

            logger.info(
                f"Agent {agente_id[:8]} ({agente_state.tipo}) removed "
                f"from lymphnode {self.id}"
            )

    async def clonar_agente(
        self,
        tipo_base: AgentType,
        especializacao: str,
        quantidade: int = 5,
    ) -> List[str]:
        """
        Create specialized agent clones (clonal expansion).

        Triggered by:
        - Persistent threat (pattern detection)
        - High cytokine concentration (inflammation)
        - MAXIMUS directive (manual intervention)

        Args:
            tipo_base: Base agent type to clone
            especializacao: Specialization marker
            quantidade: Number of clones to create

        Returns:
            List of clone IDs
        """
        logger.info(
            f"Lymphnode {self.id} initiating clonal expansion: "
            f"{quantidade} {tipo_base} agents (specialization={especializacao})"
        )

        clone_ids = []

        for i in range(quantidade):
            try:
                # Create agent via factory
                agente = await self.factory.create_agent(
                    tipo=tipo_base,
                    area_patrulha=self.area,
                )

                # Set specialization
                agente.state.especializacao = especializacao

                # Apply somatic hypermutation (variation in sensitivity/aggressiveness)
                mutation = (i * 0.04) - 0.1  # Range: -10% to +10%
                agente.state.sensibilidade = max(
                    0.0, min(1.0, agente.state.sensibilidade + mutation)
                )

                # Start agent
                await agente.iniciar()

                # Register with lymphnode
                await self.registrar_agente(agente.state)

                clone_ids.append(agente.state.id)

                self.total_clones_criados += 1

            except Exception as e:
                logger.error(f"Failed to create clone {i}: {e}")

        logger.info(
            f"Clonal expansion complete: {len(clone_ids)}/{quantidade} clones created"
        )

        return clone_ids

    async def destruir_clones(self, especializacao: str) -> int:
        """
        Destroy clones with specific specialization (apoptosis).

        Triggered by:
        - Threat eliminated
        - Resource constraints
        - Homeostatic regulation (too many agents)

        Args:
            especializacao: Specialization marker

        Returns:
            Number of clones destroyed
        """
        destruidos = 0

        for agente_id, state in list(self.agentes_ativos.items()):
            if state.especializacao == especializacao:
                # Send apoptosis signal via hormone (graceful shutdown)
                await self._send_apoptosis_signal(agente_id)

                # Remove from registry
                await self.remover_agente(agente_id)

                destruidos += 1
                self.total_clones_destruidos += 1

        logger.info(
            f"Lymphnode {self.id} destroyed {destruidos} clones ({especializacao})"
        )

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
                json.dumps({
                    "lymphnode_id": self.id,
                    "reason": "lymphnode_directive",
                    "timestamp": datetime.now().isoformat(),
                }),
            )

            logger.debug(f"Apoptosis signal sent to agent {agente_id[:8]}")

        except Exception as e:
            logger.error(f"Failed to send apoptosis signal: {e}")

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

                # Filter by area (only process cytokines from our area)
                if citocina.get("area_alvo") == self.area or self.nivel == "global":
                    # Add to buffer
                    self.cytokine_buffer.append(citocina)

                    # Process at regional level
                    await self._processar_citocina_regional(citocina)

        except Exception as e:
            logger.error(f"Cytokine aggregation error: {e}")

        finally:
            if consumer:
                await consumer.stop()

    async def _processar_citocina_regional(self, citocina: Dict[str, Any]) -> None:
        """
        Process cytokine at regional level.

        Updates:
        - Regional temperature
        - Threat detection counts
        - Metrics

        Args:
            citocina: Cytokine message
        """
        tipo = citocina.get("tipo")
        payload = citocina.get("payload", {})
        prioridade = citocina.get("prioridade", 0)

        # Update regional temperature (inflammatory/anti-inflammatory)
        if tipo in ["IL1", "IL6", "TNF", "IL8"]:
            # Pro-inflammatory
            self.temperatura_regional += 0.2
            self.temperatura_regional = min(self.temperatura_regional, 42.0)

        elif tipo in ["IL10", "TGFbeta"]:
            # Anti-inflammatory
            self.temperatura_regional -= 0.1
            self.temperatura_regional = max(self.temperatura_regional, 36.5)

        # Track metrics from payload
        evento = payload.get("evento")

        if evento == "ameaca_detectada" or payload.get("is_threat"):
            self.total_ameacas_detectadas += 1

            # Track threat for pattern detection
            threat_id = payload.get("alvo", {}).get("id") or payload.get("host_id")
            if threat_id:
                self.threat_detections[threat_id] += 1

        elif evento in ["neutralizacao_sucesso", "nk_cytotoxicity", "neutrophil_net_formation"]:
            self.total_neutralizacoes += 1

        # Escalate to global lymphnode if critical
        if prioridade >= 9 and self.nivel != "global":
            await self._escalar_para_global(citocina)

        logger.debug(
            f"Lymphnode {self.id} processed cytokine: {tipo} "
            f"(temp={self.temperatura_regional:.1f}°C)"
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
                json.dumps({
                    "origem": self.id,
                    "citocina": citocina,
                    "timestamp": datetime.now().isoformat(),
                }),
            )

        except Exception as e:
            logger.error(f"Escalation failed: {e}")

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

                if len(self.cytokine_buffer) < 10:
                    continue

                # Analyze recent cytokines (last 100)
                recentes = self.cytokine_buffer[-100:]

                # Check for persistent threats
                await self._detect_persistent_threats()

                # Check for coordinated attacks
                await self._detect_coordinated_attacks(recentes)

                # Clear old buffer (keep last 1000)
                if len(self.cytokine_buffer) > 1000:
                    self.cytokine_buffer = self.cytokine_buffer[-1000:]

                # Clear old threat detections (keep last hour)
                if (datetime.now() - self.last_pattern_check).total_seconds() > 3600:
                    self.threat_detections.clear()
                    self.last_pattern_check = datetime.now()

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Pattern detection error: {e}")

    async def _detect_persistent_threats(self) -> None:
        """
        Detect threats that persist across multiple detections.

        If same threat detected 5+ times, trigger clonal expansion.
        """
        for threat_id, count in list(self.threat_detections.items()):
            if count >= 5:
                logger.warning(
                    f"Lymphnode {self.id} detected PERSISTENT THREAT: {threat_id} "
                    f"({count} detections)"
                )

                # Trigger clonal expansion (Neutrophil swarm)
                await self.clonar_agente(
                    tipo_base=AgentType.NEUTROFILO,
                    especializacao=f"threat_{threat_id}",
                    quantidade=10,
                )

                # Clear count (avoid re-triggering)
                self.threat_detections[threat_id] = 0

    async def _detect_coordinated_attacks(self, cytokines: List[Dict[str, Any]]) -> None:
        """
        Detect coordinated attacks (multiple threats in short time).

        If 10+ threats detected in last minute, trigger mass response.

        Args:
            cytokines: Recent cytokine messages
        """
        # Count threats in last minute
        now = datetime.now()
        recent_threats = 0

        for citocina in cytokines:
            timestamp_str = citocina.get("timestamp")
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if (now - timestamp).total_seconds() < 60:
                    payload = citocina.get("payload", {})
                    if payload.get("evento") == "ameaca_detectada" or payload.get("is_threat"):
                        recent_threats += 1
            except Exception as e:
                logger.debug(f"Failed to parse cytokine timestamp '{timestamp_str}': {e}")

        # Trigger mass response if coordinated attack detected
        if recent_threats >= 10:
            logger.critical(
                f"Lymphnode {self.id} detected COORDINATED ATTACK: "
                f"{recent_threats} threats in last minute"
            )

            # Massive Neutrophil swarm
            await self.clonar_agente(
                tipo_base=AgentType.NEUTROFILO,
                especializacao="coordinated_attack_response",
                quantidade=50,
            )

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

                # Temperature decay (anti-inflammatory drift)
                self.temperatura_regional *= 0.98  # 2% decay every 30s
                self.temperatura_regional = max(36.5, self.temperatura_regional)

                logger.debug(
                    f"Lymphnode {self.id} temperature: {self.temperatura_regional:.1f}°C "
                    f"(agents: {len(self.agentes_ativos)})"
                )

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Temperature monitoring error: {e}")

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

                # Determine target active percentage
                if self.temperatura_regional >= 39.0:
                    target_percentage = 0.8  # Inflamação
                    state_name = "INFLAMAÇÃO"

                elif self.temperatura_regional >= 38.0:
                    target_percentage = 0.5  # Ativação
                    state_name = "ATIVAÇÃO"

                elif self.temperatura_regional >= 37.5:
                    target_percentage = 0.3  # Atenção
                    state_name = "ATENÇÃO"

                elif self.temperatura_regional >= 37.0:
                    target_percentage = 0.15  # Vigilância
                    state_name = "VIGILÂNCIA"

                else:
                    target_percentage = 0.05  # Repouso
                    state_name = "REPOUSO"

                target_active = int(total_agents * target_percentage)

                logger.info(
                    f"Lymphnode {self.id} homeostatic state: {state_name} "
                    f"(temp={self.temperatura_regional:.1f}°C, "
                    f"target_active={target_active}/{total_agents})"
                )

                # Send wake/sleep hormones via Redis
                await self._broadcast_activation_level(state_name, target_percentage)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Homeostasis regulation error: {e}")

    async def _broadcast_activation_level(
        self, state_name: str, target_percentage: float
    ) -> None:
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
            # Broadcast via adrenaline hormone (activation signal)
            await self._redis_client.publish(
                "hormonio:adrenalina",
                json.dumps({
                    "lymphnode_id": self.id,
                    "state": state_name,
                    "target_activation": target_percentage,
                    "temperatura_regional": self.temperatura_regional,
                    "timestamp": datetime.now().isoformat(),
                }),
            )

            logger.debug(f"Activation level broadcast: {state_name} ({target_percentage:.0%})")

        except Exception as e:
            logger.error(f"Hormone broadcast failed: {e}")

    # ==================== METRICS ====================

    def get_lymphnode_metrics(self) -> Dict[str, Any]:
        """
        Get lymphnode statistics.

        Returns:
            Dict with lymphnode metrics
        """
        return {
            "lymphnode_id": self.id,
            "nivel": self.nivel,
            "area": self.area,
            "temperatura_regional": self.temperatura_regional,
            "agentes_total": len(self.agentes_ativos),
            "agentes_dormindo": len(self.agentes_dormindo),
            "ameacas_detectadas": self.total_ameacas_detectadas,
            "neutralizacoes": self.total_neutralizacoes,
            "clones_criados": self.total_clones_criados,
            "clones_destruidos": self.total_clones_destruidos,
            "cytokine_buffer_size": len(self.cytokine_buffer),
            "threats_being_tracked": len(self.threat_detections),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"LinfonodoDigital({self.id}|{self.nivel}|"
            f"area={self.area}|"
            f"agents={len(self.agentes_ativos)}|"
            f"temp={self.temperatura_regional:.1f}°C)"
        )
