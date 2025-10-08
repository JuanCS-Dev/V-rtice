"""Base Agent Class - PRODUCTION-READY

Abstract base class for all immune agents (Macrophages, NK Cells, Neutrophils).

Implements core lifecycle, communication, homeostasis, and ethical validation.

NO MOCKS, NO PLACEHOLDERS, NO TODOs - ALL PRODUCTION CODE.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from agents.models import AgenteState, AgentStatus, AgentType
from communication import CytokineMessenger, HormoneMessenger

logger = logging.getLogger(__name__)


class AgenteImunologicoBase(ABC):
    """
    Base class for all active immune agents.

    Implements:
    - Lifecycle management (iniciar, parar, apoptose)
    - Communication (cytokines via Kafka, hormones via Redis)
    - Homeostatic regulation (energy, temperature)
    - Ethical AI validation (PRODUCTION - real HTTP requests)
    - Memory creation (PRODUCTION - real HTTP requests)
    - Background loops (patrol, heartbeat, energy decay)
    - Graceful shutdown

    Subclasses MUST implement:
    - patrulhar() - Patrol logic
    - executar_investigacao() - Investigation logic
    - executar_neutralizacao() - Neutralization logic

    PRODUCTION-READY: Full error handling, logging, metrics integration.
    """

    def __init__(
        self,
        agent_id: Optional[str] = None,
        tipo: AgentType = AgentType.MACROFAGO,
        area_patrulha: str = "default",
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        ethical_ai_url: str = "http://localhost:8612",
        memory_service_url: str = "http://localhost:8019",
        rte_service_url: str = "http://localhost:8002",
        ip_intel_url: str = "http://localhost:8001",
    ):
        """
        Initialize immune agent.

        Args:
            agent_id: Agent UUID (auto-generated if None)
            tipo: Agent type (macrofago, nk_cell, neutrofilo)
            area_patrulha: Patrol area (subnet, AZ, etc.)
            kafka_bootstrap: Kafka bootstrap servers
            redis_url: Redis connection URL
            ethical_ai_url: Ethical AI service URL
            memory_service_url: Memory consolidation service URL
            rte_service_url: RTE service URL
            ip_intel_url: IP intelligence service URL
        """
        # State
        self.state = AgenteState(
            id=agent_id or str(uuid.uuid4()),
            tipo=tipo,
            area_patrulha=area_patrulha,
            localizacao_atual=area_patrulha,
        )

        # Communication
        self.kafka_bootstrap = kafka_bootstrap
        self.redis_url = redis_url
        self._cytokine_messenger: Optional[CytokineMessenger] = None
        self._hormone_messenger: Optional[HormoneMessenger] = None

        # External services
        self.ethical_ai_url = ethical_ai_url
        self.memory_service_url = memory_service_url
        self.rte_service_url = rte_service_url
        self.ip_intel_url = ip_intel_url

        # Runtime
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._http_session: Optional[aiohttp.ClientSession] = None

        # Metrics buffer
        self._metrics_buffer: List[Dict[str, Any]] = []

        logger.info(f"Initialized {self.state.tipo} agent {self.state.id} (patrol area: {area_patrulha})")

    # ==================== LIFECYCLE ====================

    async def iniciar(self) -> None:
        """Start agent lifecycle - PRODUCTION"""
        if self._running:
            logger.warning(f"Agent {self.state.id} already running")
            return

        logger.info(f"Starting agent {self.state.id}...")

        try:
            # Initialize communication
            self._cytokine_messenger = CytokineMessenger(
                bootstrap_servers=self.kafka_bootstrap,
                consumer_group_prefix=f"agent_{self.state.id}",
            )
            await self._cytokine_messenger.start()

            self._hormone_messenger = HormoneMessenger(redis_url=self.redis_url)
            await self._hormone_messenger.start()

            # Subscribe to hormones (global signals)
            await self._hormone_messenger.subscribe(
                hormone_types=["cortisol", "adrenalina", "melatonina"],
                callback=self._processar_hormonio,
                subscriber_id=f"agent_{self.state.id}",
            )

            # Subscribe to cytokines (local signals)
            await self._cytokine_messenger.subscribe(
                cytokine_types=["IL1", "IL6", "IL10", "TNF"],
                callback=self._processar_citocina,
                consumer_id=f"agent_{self.state.id}",
                area_filter=self.state.area_patrulha,
            )

            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self._http_session = aiohttp.ClientSession(timeout=timeout)

            # Update state
            self._running = True
            self.state.ativo = True
            self.state.status = AgentStatus.PATRULHANDO

            # Start background tasks
            self._tasks.append(asyncio.create_task(self._patrol_loop()))
            self._tasks.append(asyncio.create_task(self._heartbeat_loop()))
            self._tasks.append(asyncio.create_task(self._energy_decay_loop()))

            # Update metrics
            try:
                from main import agents_active, agents_total

                agents_active.labels(type=self.state.tipo, status="patrulhando").inc()
                agents_total.labels(type=self.state.tipo).inc()
            except ImportError:
                pass

            logger.info(f"Agent {self.state.id} started successfully")

        except Exception as e:
            logger.error(f"Failed to start agent {self.state.id}: {e}", exc_info=True)
            await self.parar()
            raise

    async def parar(self) -> None:
        """Stop agent gracefully - PRODUCTION"""
        if not self._running:
            return

        logger.info(f"Stopping agent {self.state.id}...")

        self._running = False
        self.state.ativo = False
        # Preserve APOPTOSE status if already set
        if self.state.status != AgentStatus.APOPTOSE:
            self.state.status = AgentStatus.DORMINDO

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()

        # Close communication
        if self._cytokine_messenger:
            try:
                await self._cytokine_messenger.stop()
            except Exception as e:
                logger.error(f"Error stopping cytokine messenger: {e}")

        if self._hormone_messenger:
            try:
                await self._hormone_messenger.stop()
            except Exception as e:
                logger.error(f"Error stopping hormone messenger: {e}")

        # Close HTTP session
        if self._http_session:
            try:
                await self._http_session.close()
            except Exception as e:
                logger.error(f"Error closing HTTP session: {e}")

        # Update metrics
        try:
            from main import agents_active

            agents_active.labels(type=self.state.tipo, status="patrulhando").dec()
        except ImportError:
            pass

        logger.info(f"Agent {self.state.id} stopped")

    async def apoptose(self, reason: str = "malfunction") -> None:
        """
        Programmed cell death (apoptosis) - PRODUCTION.

        Triggers when:
        - Energy depleted (<10%)
        - Ethical violation detected
        - Malfunction detected
        - Lifecycle complete

        Args:
            reason: Apoptosis reason
        """
        self.state.status = AgentStatus.APOPTOSE

        logger.warning(f"Agent {self.state.id} entering apoptosis: {reason}")

        # Report death to lymphnode via cytokine
        if self._cytokine_messenger and self._cytokine_messenger.is_running():
            try:
                await self._cytokine_messenger.send_cytokine(
                    tipo="IL10",  # Anti-inflammatory (death signal)
                    payload={
                        "evento": "apoptose",
                        "agente_id": self.state.id,
                        "reason": reason,
                        "metricas_finais": {
                            "deteccoes": self.state.deteccoes_total,
                            "neutralizacoes": self.state.neutralizacoes_total,
                            "falsos_positivos": self.state.falsos_positivos,
                            "tempo_vida_horas": self.state.tempo_vida.total_seconds() / 3600,
                        },
                    },
                    emissor_id=self.state.id,
                    prioridade=3,
                )
            except Exception as e:
                logger.error(f"Failed to send apoptosis cytokine: {e}")

        # Update metrics
        try:
            from main import agent_apoptosis_total

            agent_apoptosis_total.labels(reason=reason).inc()
        except ImportError:
            pass

        await self.parar()

    # ==================== PATROL ====================

    async def _patrol_loop(self) -> None:
        """Main patrol loop - calls abstract patrulhar() method"""
        logger.info(f"Agent {self.state.id} patrol loop started")

        while self._running:
            try:
                # Check energy
                if self.state.energia < 10.0:
                    logger.warning(
                        f"Agent {self.state.id} low energy ({self.state.energia:.1f}%), triggering apoptosis"
                    )
                    await self.apoptose(reason="energy_depleted")
                    break

                # Call subclass patrol logic
                await self.patrulhar()

                # Patrol interval based on homeostatic temperature
                interval = self._get_patrol_interval()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info(f"Patrol loop cancelled for {self.state.id}")
                break

            except Exception as e:
                logger.error(f"Patrol loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

        logger.info(f"Agent {self.state.id} patrol loop ended")

    def _get_patrol_interval(self) -> float:
        """Calculate patrol interval based on homeostatic temperature"""
        temp = self.state.temperatura_local

        if temp >= 39.0:  # Inflamação
            return 1.0  # Fast patrol (1s)
        elif temp >= 38.0:  # Atenção
            return 3.0
        elif temp >= 37.5:  # Vigilância
            return 10.0
        else:  # Repouso
            return 30.0

    @abstractmethod
    async def patrulhar(self) -> None:
        """
        Subclass-specific patrol logic.

        Must implement:
        - Scan area for threats
        - Check suspicious patterns
        - Decide on action (investigate/neutralize/ignore)
        """
        pass

    # ==================== DETECTION ====================

    async def investigar(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Investigate suspicious target - PRODUCTION.

        Args:
            alvo: Target metadata (ip, domain, process, etc.)

        Returns:
            Investigation result with threat assessment
        """
        old_status = self.state.status
        self.state.status = AgentStatus.INVESTIGANDO

        logger.info(f"Agent {self.state.id} investigating: {alvo.get('id', 'unknown')}")

        try:
            # Call subclass investigation logic
            resultado = await self.executar_investigacao(alvo)

            # Update metrics
            self.state.deteccoes_total += 1

            # If threat confirmed, trigger cytokine cascade
            if resultado.get("is_threat", False):
                threat_id = alvo.get("id", "unknown")
                self.state.ultimas_ameacas.append(threat_id)
                self.state.ultimas_ameacas = self.state.ultimas_ameacas[-10:]

                # Send IL1 (pro-inflammatory)
                if self._cytokine_messenger and self._cytokine_messenger.is_running():
                    await self._cytokine_messenger.send_cytokine(
                        tipo="IL1",
                        payload={
                            "evento": "ameaca_detectada",
                            "agente_id": self.state.id,
                            "alvo": alvo,
                            "resultado": resultado,
                        },
                        emissor_id=self.state.id,
                        prioridade=8,
                        area_alvo=self.state.area_patrulha,
                    )

                # Update metrics
                try:
                    from main import threats_detected_total

                    threats_detected_total.labels(agent_type=self.state.tipo).inc()
                except ImportError:
                    pass

            return resultado

        except Exception as e:
            logger.error(f"Investigation failed: {e}", exc_info=True)
            return {"error": str(e), "is_threat": False}

        finally:
            self.state.status = old_status

    @abstractmethod
    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Subclass-specific investigation logic.

        Must return:
            {
                "is_threat": bool,
                "threat_level": float (0-10),
                "details": {...}
            }
        """
        pass

    # ==================== NEUTRALIZATION ====================

    async def neutralizar(self, alvo: Dict[str, Any], metodo: str = "isolate") -> bool:
        """
        Neutralize confirmed threat - PRODUCTION with Ethical AI validation.

        Args:
            alvo: Threat target
            metodo: Neutralization method (isolate/block/kill)

        Returns:
            True if neutralization successful
        """
        old_status = self.state.status
        self.state.status = AgentStatus.NEUTRALIZANDO

        # ETHICAL AI CHECK - PRODUCTION (real HTTP request)
        if not await self._validate_ethical(alvo, metodo):
            logger.warning(f"Agent {self.state.id} action blocked by Ethical AI: {metodo} on {alvo.get('id')}")
            self.state.status = old_status
            return False

        logger.info(f"Agent {self.state.id} neutralizing: {alvo.get('id')} (method={metodo})")

        try:
            # Call subclass neutralization logic
            sucesso = await self.executar_neutralizacao(alvo, metodo)

            if sucesso:
                self.state.neutralizacoes_total += 1

                # Send IL6 (acute inflammation)
                if self._cytokine_messenger and self._cytokine_messenger.is_running():
                    await self._cytokine_messenger.send_cytokine(
                        tipo="IL6",
                        payload={
                            "evento": "neutralizacao_sucesso",
                            "agente_id": self.state.id,
                            "alvo": alvo,
                            "metodo": metodo,
                        },
                        emissor_id=self.state.id,
                        prioridade=9,
                        area_alvo=self.state.area_patrulha,
                    )

                # Create immunological memory
                await self._criar_memoria(alvo)

                # Update metrics
                try:
                    from main import threats_neutralized_total

                    threats_neutralized_total.labels(agent_type=self.state.tipo, method=metodo).inc()
                except ImportError:
                    pass

            return sucesso

        except Exception as e:
            logger.error(f"Neutralization failed: {e}", exc_info=True)
            return False

        finally:
            self.state.status = old_status

    @abstractmethod
    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Subclass-specific neutralization logic.

        Must return:
            True if successful, False otherwise
        """
        pass

    # ==================== MEMORY ====================

    async def _criar_memoria(self, ameaca: Dict[str, Any]) -> None:
        """
        Create immunological memory - PRODUCTION (real HTTP request).

        Integrates with Memory Consolidation Service (port 8019).
        """
        old_status = self.state.status
        self.state.status = AgentStatus.MEMORIA

        try:
            if not self._http_session:
                logger.warning("HTTP session not initialized, skipping memory creation")
                return

            async with self._http_session.post(
                f"{self.memory_service_url}/memory/short_term",
                json={
                    "tipo": "threat_neutralization",
                    "agente_id": self.state.id,
                    "ameaca": ameaca,
                    "timestamp": datetime.now().isoformat(),
                    "importancia": 0.8,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 201:
                    logger.info(f"Memory created for threat: {ameaca.get('id')}")
                else:
                    error_text = await response.text()
                    logger.warning(f"Memory creation failed ({response.status}): {error_text}")

        except aiohttp.ClientError as e:
            logger.warning(f"Memory service unavailable: {e}")

        except asyncio.TimeoutError:
            logger.warning("Memory creation timed out")

        except Exception as e:
            logger.error(f"Failed to create memory: {e}")

        finally:
            self.state.status = old_status

    # ==================== COMMUNICATION ====================

    async def _processar_citocina(self, citocina) -> None:
        """Process received cytokine - PRODUCTION"""
        tipo = citocina.tipo

        # Ignore own messages
        if citocina.emissor_id == self.state.id:
            return

        logger.debug(f"Agent {self.state.id} received cytokine {tipo}")

        # Pro-inflammatory cytokines increase temperature
        if tipo in ["IL1", "IL6", "TNF"]:
            self.state.temperatura_local += 0.5
            self.state.temperatura_local = min(self.state.temperatura_local, 42.0)

        # Anti-inflammatory cytokines decrease temperature
        elif tipo in ["IL10", "TGFbeta"]:
            self.state.temperatura_local -= 0.3
            self.state.temperatura_local = max(self.state.temperatura_local, 36.5)

    async def _processar_hormonio(self, hormonio) -> None:
        """Process global hormone signals - PRODUCTION"""
        tipo = hormonio.tipo
        nivel = hormonio.nivel

        logger.debug(f"Agent {self.state.id} received hormone {tipo} (nivel={nivel})")

        if tipo == "cortisol":
            # Suppress immune activity (stress response)
            self.state.sensibilidade *= 0.9
            self.state.sensibilidade = max(self.state.sensibilidade, 0.1)

        elif tipo == "adrenalina":
            # Increase aggressiveness (fight-or-flight)
            self.state.nivel_agressividade *= 1.2
            self.state.nivel_agressividade = min(self.state.nivel_agressividade, 1.0)

        elif tipo == "melatonina":
            # Circadian sleep signal (decrease activity)
            if nivel > 7.0:
                self.state.energia -= 10.0  # Drain energy faster
                self.state.energia = max(self.state.energia, 0.0)

    # ==================== HOMEOSTASIS ====================

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat to lymphnode via Redis - PRODUCTION"""
        while self._running:
            try:
                self.state.ultimo_heartbeat = datetime.now()
                self.state.tempo_vida = datetime.now() - self.state.criado_em

                # Update state in Redis (ephemeral storage)
                if self._hormone_messenger and self._hormone_messenger.is_running():
                    await self._hormone_messenger.set_agent_state(
                        agent_id=self.state.id,
                        state=self.state.model_dump(mode="json"),
                        ttl=60,
                    )

                await asyncio.sleep(30)  # Heartbeat every 30s

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(30)

    async def _energy_decay_loop(self) -> None:
        """Simulate energy consumption - PRODUCTION"""
        while self._running:
            try:
                # Energy decay rate based on activity
                if self.state.status == AgentStatus.DORMINDO:
                    decay = 0.1
                elif self.state.status == AgentStatus.PATRULHANDO:
                    decay = 0.5
                elif self.state.status == AgentStatus.NEUTRALIZANDO:
                    decay = 2.0
                else:
                    decay = 1.0

                self.state.energia -= decay
                self.state.energia = max(0.0, self.state.energia)

                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Energy decay error: {e}")

    # ==================== ETHICAL AI ====================

    async def _validate_ethical(self, alvo: Dict[str, Any], acao: str) -> bool:
        """
        Validate action with Ethical AI service - PRODUCTION (real HTTP request).

        FAIL-SAFE: Block action on error (never fail open).

        Args:
            alvo: Target
            acao: Action to validate

        Returns:
            True if approved, False if blocked
        """
        if not self._http_session:
            logger.error("HTTP session not initialized, blocking action (fail-safe)")
            return False

        try:
            async with self._http_session.post(
                f"{self.ethical_ai_url}/validate",
                json={
                    "agent": self.state.id,
                    "target": alvo.get("id"),
                    "action": acao,
                    "context": {
                        "tipo_agente": self.state.tipo,
                        "area": self.state.area_patrulha,
                        "temperatura": self.state.temperatura_local,
                    },
                },
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    approved = result.get("decisao") == "APROVADO"

                    if not approved:
                        logger.warning(f"Ethical AI blocked action: {result.get('justificativa')}")

                    return approved
                else:
                    error_text = await response.text()
                    logger.error(f"Ethical AI validation failed ({response.status}): {error_text}")
                    return False  # Fail-safe: block on error

        except aiohttp.ClientError as e:
            logger.warning(f"Ethical AI service unavailable: {e}, blocking action (fail-safe)")
            return False  # Fail-safe: block if service down

        except asyncio.TimeoutError:
            logger.warning("Ethical AI timeout, blocking action (fail-safe)")
            return False  # Fail-safe

        except Exception as e:
            logger.error(f"Ethical AI validation error: {e}", exc_info=True)
            return False  # Fail-safe

    # ==================== METRICS ====================

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics for Prometheus - PRODUCTION"""
        return {
            "agent_id": self.state.id,
            "agent_type": self.state.tipo,
            "status": self.state.status,
            "active": self.state.ativo,
            "energy": self.state.energia,
            "temperature": self.state.temperatura_local,
            "detections_total": self.state.deteccoes_total,
            "neutralizations_total": self.state.neutralizacoes_total,
            "false_positives": self.state.falsos_positivos,
            "uptime_hours": self.state.tempo_vida.total_seconds() / 3600,
            "area_patrulha": self.state.area_patrulha,
            "localizacao_atual": self.state.localizacao_atual,
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"<{self.__class__.__name__} "
            f"id={self.state.id[:8]}... "
            f"status={self.state.status} "
            f"energia={self.state.energia:.1f}%>"
        )
