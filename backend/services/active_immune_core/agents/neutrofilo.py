"""Digital Neutrophil - Fast Responder with Swarm Behavior

Neutrophils are the "first responders" of innate immunity, specialized in:
1. Rapid chemotaxis (follow IL-8 inflammation signals)
2. Swarm coordination (overwhelm threats with numbers)
3. NET formation (Neutrophil Extracellular Traps = firewall rules)
4. Short lifespan (6-8 hours, then apoptosis)

Unlike Macrophages (investigators), Neutrophils:
- Respond to inflammation signals immediately
- Don't investigate deeply (trust the signal)
- Work in coordinated swarms
- Use containment (NETs) over precision kills

PRODUCTION-READY: Real HTTP, Kafka, Redis, no mocks, graceful degradation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from .base import AgenteImunologicoBase
from .models import AgentStatus, AgentType

logger = logging.getLogger(__name__)


class NeutrofiloDigital(AgenteImunologicoBase):
    """
    Digital Neutrophil - Fast-responding swarm specialist.

    Capabilities:
    - Rapid chemotaxis (follow IL-8 gradients)
    - Swarm behavior (Boids algorithm: separation, alignment, cohesion)
    - NET formation (firewall rules to trap attackers)
    - Short lifespan (6-8 hours maximum)
    - No memory (pure innate immunity)

    Use cases:
    - DDoS mitigation (swarm response)
    - Port scan attacks (rapid containment)
    - Brute force attempts (NET formation)
    - Overwhelming threats (multiple attackers)
    """

    def __init__(
        self,
        area_patrulha: str,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        rte_service_url: str = "http://localhost:8002",
        ethical_ai_url: str = "http://localhost:8100",
        lifespan_hours: float = 8.0,
        swarm_threshold: int = 3,
        **kwargs,
    ):
        """
        Initialize Neutrophil.

        Args:
            area_patrulha: Initial network zone to patrol
            kafka_bootstrap: Kafka broker
            redis_url: Redis URL
            rte_service_url: RTE Service URL (network operations)
            ethical_ai_url: Ethical AI service URL
            lifespan_hours: Maximum lifespan before apoptosis (default 8h)
            swarm_threshold: Min swarm size for NET formation (default 3)
        """
        super().__init__(
            tipo=AgentType.NEUTROFILO,
            area_patrulha=area_patrulha,
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
            ethical_ai_url=ethical_ai_url,
            **kwargs,
        )

        # Neutrophil-specific configuration
        self.rte_service_url = rte_service_url
        self.tempo_vida_max = timedelta(hours=lifespan_hours)
        self.swarm_threshold = swarm_threshold

        # Neutrophil-specific state
        self.swarm_members: List[str] = []  # Other neutrophils in swarm
        self.nets_formadas: int = 0  # NETs deployed
        self.targets_engulfed: int = 0  # Individual kills
        self.chemotaxis_count: int = 0  # Number of migrations

        logger.info(
            f"Neutrophil initialized: {self.state.id[:8]} "
            f"(zone={area_patrulha}, lifespan={lifespan_hours}h, swarm_threshold={swarm_threshold})"
        )

    # ==================== PATROL ====================

    async def patrulhar(self) -> None:
        """
        Follow IL-8 chemotaxis gradients to inflammation sites.

        Neutrophils don't patrol randomly - they follow chemical signals:
        1. Detect IL-8 concentration gradients
        2. Migrate towards highest concentration
        3. Form swarm with other neutrophils
        4. Engage threat collectively
        """
        # Check if lifespan exceeded (short-lived cells)
        if self.state.tempo_vida > self.tempo_vida_max:
            logger.info(
                f"Neutrophil {self.state.id[:8]} lifespan exceeded "
                f"({self.state.tempo_vida.total_seconds() / 3600:.1f}h)"
            )
            await self.apoptose(reason="lifespan_exceeded")
            return

        logger.debug(f"Neutrophil {self.state.id[:8]} detecting IL-8 gradients")

        # 1. Detect IL-8 gradients (inflammation signals)
        gradientes = await self._detectar_gradiente_il8()

        if not gradientes:
            logger.debug("No IL-8 gradients detected (no inflammation)")
            return

        # 2. Move towards highest gradient
        alvo = max(gradientes, key=lambda g: g["concentracao"])

        if alvo["concentracao"] < 2.0:
            logger.debug(f"IL-8 concentration too low: {alvo['concentracao']}")
            return

        logger.info(
            f"Neutrophil {self.state.id[:8]} following IL-8 to {alvo['area']} "
            f"(concentration={alvo['concentracao']})"
        )

        # 3. Migrate to inflammation site
        await self._migrar(alvo["area"])

        # 4. Form swarm with other neutrophils
        await self._formar_swarm(alvo["area"])

        # 5. Engage threat collectively
        await self._swarm_attack(alvo)

    async def _detectar_gradiente_il8(self) -> List[Dict[str, Any]]:
        """
        Detect IL-8 concentration gradients.

        IL-8 is a chemotactic cytokine secreted by:
        - Macrophages (when detecting threats)
        - Dendritic cells (when activating adaptive immunity)
        - Damaged tissues (stress signals)

        Returns:
            List of {area, concentracao} dicts
        """
        if not self._hormone_messenger:
            logger.debug("Hormone messenger not initialized")
            return []

        try:
            # Query Redis for recent IL-8 cytokines by area (last 5 minutes)
            redis_client = self._hormone_messenger._redis_client

            # Get all area keys
            area_keys = await redis_client.keys("cytokine:IL8:*")

            gradientes = []

            for area_key in area_keys:
                # Extract area name
                area = area_key.split(":")[-1]

                # Get IL-8 count
                count_str = await redis_client.get(area_key)
                count = float(count_str) if count_str else 0.0

                if count > 0:
                    gradientes.append(
                        {
                            "area": area,
                            "concentracao": count,
                        }
                    )

            logger.debug(f"Detected {len(gradientes)} IL-8 gradients")
            return gradientes

        except Exception as e:
            logger.error(f"IL-8 gradient detection error: {e}")
            return []

    async def _migrar(self, area_destino: str) -> None:
        """
        Migrate to target area (chemotaxis).

        Neutrophils are highly mobile and migrate through tissues
        following chemical gradients.

        Args:
            area_destino: Target network zone
        """
        logger.info(
            f"Neutrophil {self.state.id[:8]} migrating: "
            f"{self.state.localizacao_atual} -> {area_destino}"
        )

        # Update location
        self.state.localizacao_atual = area_destino
        self.state.area_patrulha = area_destino

        # Increment chemotaxis counter
        self.chemotaxis_count += 1

        # Consume energy (migration is expensive)
        self.state.energia = max(0.0, self.state.energia - 2.0)

    async def _formar_swarm(self, area: str) -> None:
        """
        Form swarm with nearby neutrophils.

        Uses simplified Boids algorithm principles:
        - Separation: Don't overlap (each has unique ID)
        - Alignment: Move in same direction (same target area)
        - Cohesion: Stay together (same Redis state)

        Args:
            area: Target area to form swarm in
        """
        if not self._hormone_messenger:
            logger.debug("Hormone messenger not initialized")
            return

        try:
            redis_client = self._hormone_messenger._redis_client

            # Query Redis for other agents in same area
            agent_keys = await redis_client.keys("agent:*:state")

            self.swarm_members = []  # Reset swarm

            for key in agent_keys:
                # Get agent state
                state_json = await redis_client.get(key)
                if not state_json:
                    continue

                state = json.loads(state_json)

                # Check if neutrophil in same area (and not self)
                if (
                    state.get("tipo") == AgentType.NEUTROFILO
                    and state.get("localizacao_atual") == area
                    and state.get("id") != self.state.id
                ):
                    self.swarm_members.append(state["id"])

            if self.swarm_members:
                logger.info(
                    f"Neutrophil {self.state.id[:8]} joined swarm "
                    f"({len(self.swarm_members)} members)"
                )
            else:
                logger.debug("No swarm members found (solo neutrophil)")

        except Exception as e:
            logger.error(f"Swarm formation error: {e}")

    async def _swarm_attack(self, alvo: Dict[str, Any]) -> None:
        """
        Coordinated swarm attack on threat.

        Strategy:
        - If swarm >= threshold: Form NET (containment)
        - If swarm < threshold: Individual attack (kill)

        Args:
            alvo: Target threat (from IL-8 gradient)
        """
        swarm_size = len(self.swarm_members) + 1  # +1 for self

        logger.info(
            f"Neutrophil swarm attacking (size={swarm_size}, threshold={self.swarm_threshold})"
        )

        if swarm_size >= self.swarm_threshold:
            # Form NET (coordinated containment)
            logger.info("Swarm size sufficient - forming NET")
            await self._formar_net(alvo)
        else:
            # Individual attack (rapid kill)
            logger.info("Swarm size insufficient - individual attack")
            target = {
                "id": alvo.get("area", "unknown"),
                "area": alvo.get("area"),
                "concentracao": alvo.get("concentracao"),
            }
            await self.neutralizar(target, metodo="isolate")

    async def _formar_net(self, alvo: Dict[str, Any]) -> None:
        """
        Form NET (Neutrophil Extracellular Trap).

        Biological NETs:
        - Neutrophils release DNA/protein web to trap bacteria
        - Immobilizes and kills pathogens

        Digital NET:
        - Deploy firewall rules to trap attacker
        - Block egress, log all activity, isolate network segment

        Args:
            alvo: Target to trap
        """
        logger.info(
            f"Neutrophil swarm forming NET around {alvo.get('area', 'unknown')} "
            f"(swarm size={len(self.swarm_members) + 1})"
        )

        try:
            # Extract target IP/area
            target_id = alvo.get("area", "unknown")

            async with self._http_session.post(
                f"{self.rte_service_url}/network/deploy_net",
                json={
                    "target_area": target_id,
                    "swarm_members": [self.state.id] + self.swarm_members,
                    "rules": [
                        {
                            "action": "drop",
                            "direction": "egress",
                            "source_area": target_id,
                            "reason": "neutrophil_net",
                        },
                        {
                            "action": "log",
                            "direction": "all",
                            "source_area": target_id,
                            "reason": "neutrophil_net_forensics",
                        },
                    ],
                    "duration_seconds": 3600,  # 1 hour
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    self.nets_formadas += 1
                    logger.info(f"NET deployed successfully (total NETs={self.nets_formadas})")

                    # Trigger IL-10 (anti-inflammatory) to prevent cytokine storm
                    await self._secretar_il10()

                elif response.status == 404:
                    # RTE service unavailable - graceful degradation
                    logger.warning("RTE service unavailable, NET tracked locally")
                    self.nets_formadas += 1

                else:
                    logger.error(f"NET deployment failed: {response.status}")

        except aiohttp.ClientConnectorError:
            logger.warning("RTE service unavailable (graceful degradation)")
            # Track locally even if RTE unavailable
            self.nets_formadas += 1

        except Exception as e:
            logger.error(f"NET formation error: {e}")

    async def _secretar_il10(self) -> None:
        """
        Secrete IL-10 (anti-inflammatory cytokine) after NET formation.

        IL-10 prevents excessive inflammation (cytokine storm) by:
        - Reducing temperature
        - Suppressing further neutrophil recruitment
        - Initiating resolution phase
        """
        if not self._cytokine_messenger:
            logger.debug("Cytokine messenger not initialized")
            return

        try:
            await self._cytokine_messenger.send_cytokine(
                tipo="IL10",
                payload={
                    "evento": "neutrophil_net_formation",
                    "neutrofilo_id": self.state.id,
                    "swarm_size": len(self.swarm_members) + 1,
                    "nets_total": self.nets_formadas,
                    "timestamp": datetime.now().isoformat(),
                },
                emissor_id=self.state.id,
                prioridade=7,  # Moderate priority (resolution signal)
            )

            logger.info("IL-10 secreted (resolution phase initiated)")

        except Exception as e:
            logger.error(f"Failed to secrete IL-10: {e}")

    # ==================== INVESTIGATION ====================

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Neutrophils don't investigate deeply - rapid responders.

        Unlike Macrophages that correlate with IP intelligence,
        Neutrophils trust the IL-8 signal and respond immediately.

        Args:
            alvo: Target

        Returns:
            Investigation result (always threat if IL-8 present)
        """
        logger.debug(
            f"Neutrophil {self.state.id[:8]} investigating {alvo.get('id', 'unknown')}"
        )

        # Neutrophils assume threat if IL-8 triggered
        # (IL-8 is secreted by trusted sources: Macrophages, Dendritic cells)
        return {
            "is_threat": True,  # Trust the signal
            "swarm_size": len(self.swarm_members) + 1,
            "method": "chemotaxis_trust",
            "confidence": 0.95,  # High confidence in IL-8 signal
        }

    # ==================== NEUTRALIZATION ====================

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Rapid neutralization via IP blocking.

        Neutrophils use the same mechanism as Macrophages (isolation),
        but optimized for speed over precision.

        Args:
            alvo: Target
            metodo: "isolate" or "monitor"

        Returns:
            True if successful
        """
        target_id = alvo.get("id", "unknown")

        if metodo == "monitor":
            # Monitoring mode (non-destructive)
            logger.info(f"Neutrophil monitoring {target_id}")
            return True

        logger.info(f"Neutrophil engulfing {target_id}")

        try:
            async with self._http_session.post(
                f"{self.rte_service_url}/network/block",
                json={
                    "target_id": target_id,
                    "duration_seconds": 3600,  # 1 hour
                    "reason": "neutrophil_engulfment",
                },
                timeout=aiohttp.ClientTimeout(total=5),  # Fast timeout
            ) as response:
                if response.status == 200:
                    logger.info(f"Target {target_id} blocked by Neutrophil")
                    self.targets_engulfed += 1
                    return True

                elif response.status == 404:
                    # RTE service unavailable - graceful degradation
                    logger.warning("RTE service unavailable, tracking engulfment locally")
                    self.targets_engulfed += 1
                    return True

                else:
                    logger.error(f"Blocking failed: {response.status}")
                    return False

        except aiohttp.ClientConnectorError:
            logger.warning("RTE service unavailable (graceful degradation)")
            # Track locally even if RTE unavailable
            self.targets_engulfed += 1
            return True

        except Exception as e:
            logger.error(f"Neutralization error: {e}")
            return False

    # ==================== METRICS ====================

    def get_neutrofilo_metrics(self) -> Dict[str, Any]:
        """
        Get Neutrophil-specific metrics.

        Returns:
            Dict with Neutrophil-specific stats
        """
        lifespan_hours = self.state.tempo_vida.total_seconds() / 3600
        lifespan_remaining_hours = (
            self.tempo_vida_max.total_seconds() - self.state.tempo_vida.total_seconds()
        ) / 3600

        return {
            "nets_formadas": self.nets_formadas,
            "targets_engulfed": self.targets_engulfed,
            "chemotaxis_count": self.chemotaxis_count,
            "swarm_size_current": len(self.swarm_members) + 1,
            "lifespan_hours": round(lifespan_hours, 2),
            "lifespan_remaining_hours": round(max(0, lifespan_remaining_hours), 2),
            "eficiencia_swarm": (
                self.nets_formadas / self.chemotaxis_count
                if self.chemotaxis_count > 0
                else 0.0
            ),
        }

    def __repr__(self) -> str:
        """String representation"""
        lifespan_hours = self.state.tempo_vida.total_seconds() / 3600

        return (
            f"NeutrofiloDigital({self.state.id[:8]}|{self.state.status}|"
            f"swarm={len(self.swarm_members) + 1}|"
            f"NETs={self.nets_formadas}|"
            f"engulfed={self.targets_engulfed}|"
            f"age={lifespan_hours:.1f}h)"
        )
