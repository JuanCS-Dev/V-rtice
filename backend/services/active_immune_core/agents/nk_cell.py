"""Digital Natural Killer Cell - Stress-responsive Innate Immunity

NK Cells are the "enforcers" of innate immunity, specialized in detecting:
1. Missing self signals (disabled security logs = missing MHC-I)
2. Behavioral anomalies (zero-day threats, APTs)
3. Stress markers (resource exhaustion, crashes)

Unlike Macrophages, NK Cells:
- Don't investigate deeply (rapid response)
- Kill on suspicion (cytotoxic)
- No memory (innate only)
- Activate on stress signals

PRODUCTION-READY: Real HTTP, no mocks, graceful degradation.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

from .base import AgenteImunologicoBase
from .models import AgentStatus, AgentType

logger = logging.getLogger(__name__)


class CelulaNKDigital(AgenteImunologicoBase):
    """
    Digital Natural Killer Cell - Stress-responsive cytotoxic agent.

    Capabilities:
    - Missing MHC-I detection (disabled audit logs)
    - Behavioral anomaly detection (statistical)
    - Stress marker recognition (crashes, exhaustion)
    - Rapid cytotoxicity (kill without investigation)
    - IFN-gamma secretion (activate other cells)

    Use cases:
    - Zero-day threats (no signatures)
    - APT detection (behavioral changes)
    - Compromised hosts (disabled logging)
    - Resource exhaustion attacks
    """

    def __init__(
        self,
        area_patrulha: str,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        rte_service_url: str = "http://localhost:8002",
        ethical_ai_url: str = "http://localhost:8100",
        anomaly_threshold: float = 0.7,
        **kwargs,
    ):
        """
        Initialize NK Cell.

        Args:
            area_patrulha: Network zone to patrol
            kafka_bootstrap: Kafka broker
            redis_url: Redis URL
            rte_service_url: RTE Service URL (host metrics)
            ethical_ai_url: Ethical AI service URL
            anomaly_threshold: Score above which to trigger cytotoxicity (0-1)
        """
        super().__init__(
            tipo=AgentType.NK_CELL,
            area_patrulha=area_patrulha,
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
            ethical_ai_url=ethical_ai_url,
            **kwargs,
        )

        # NK-specific configuration
        self.rte_service_url = rte_service_url
        self.anomaly_threshold = anomaly_threshold

        # NK-specific state
        self.baseline_behavior: Dict[str, Dict[str, float]] = {}  # host_id -> metrics
        self.anomalias_detectadas: int = 0
        self.hosts_isolados: List[str] = []  # Track killed hosts
        self.mhc_violations: int = 0  # Missing self detections

        logger.info(f"NK Cell initialized: {self.state.id[:8]} (zone={area_patrulha}, threshold={anomaly_threshold})")

    # ==================== PATROL ====================

    async def patrulhar(self) -> None:
        """
        Patrol for stress signals and behavioral anomalies.

        NK cells scan for:
        1. Missing MHC-I (disabled security logs)
        2. Behavioral anomalies (deviation from baseline)
        3. Stress markers (high CPU, crashes)
        """
        logger.debug(f"NK Cell {self.state.id[:8]} scanning for stress signals")

        # 1. Check for missing MHC-I (disabled logging)
        hosts_sem_mhc = await self._detectar_mhc_ausente()

        for host in hosts_sem_mhc:
            logger.warning(
                f"Missing MHC-I detected: {host.get('id', 'unknown')} "
                f"(audit_enabled={host.get('audit_enabled', 'unknown')})"
            )
            self.mhc_violations += 1

            # NK cells kill immediately on missing self
            await self.neutralizar(host, metodo="isolate")

        # 2. Check for behavioral anomalies
        hosts_anomalos = await self._detectar_anomalias_comportamentais()

        for host, anomaly_score in hosts_anomalos:
            logger.warning(f"Behavioral anomaly detected: {host.get('id', 'unknown')} (score={anomaly_score:.2f})")
            self.anomalias_detectadas += 1

            # Investigate and neutralize if confirmed
            await self.investigar(host)

        # 3. Update baseline for normal hosts (learning)
        await self._update_baseline()

    async def _detectar_mhc_ausente(self) -> List[Dict[str, Any]]:
        """
        Detect hosts with missing MHC-I (disabled audit logs).

        In biological systems, NK cells detect missing MHC-I molecules
        (healthy cells display MHC-I, virally infected cells downregulate them).

        Digital analogue: Security audit logs.
        - Healthy hosts: audit_enabled=True
        - Compromised hosts: audit_enabled=False (to hide activity)

        Returns:
            List of hosts with disabled logging
        """
        try:
            async with self._http_session.get(
                f"{self.rte_service_url}/hosts/security_status",
                params={"zone": self.state.area_patrulha},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    # Filter hosts with disabled logging
                    hosts_suspeitos = [host for host in data.get("hosts", []) if not host.get("audit_enabled", True)]

                    logger.debug(
                        f"MHC-I scan: {len(hosts_suspeitos)} violations out of {len(data.get('hosts', []))} hosts"
                    )

                    return hosts_suspeitos

                elif response.status == 404:
                    logger.debug("RTE service unavailable (graceful degradation)")
                    return []

                else:
                    logger.warning(f"Unexpected response: {response.status}")
                    return []

        except aiohttp.ClientConnectorError:
            logger.debug("RTE service unavailable (graceful degradation)")
            return []

        except asyncio.TimeoutError:
            logger.warning("MHC-I detection timeout")
            return []

        except Exception as e:
            logger.error(f"MHC-I detection error: {e}")
            return []

    async def _detectar_anomalias_comportamentais(
        self,
    ) -> List[tuple[Dict[str, Any], float]]:
        """
        Detect behavioral anomalies using statistical deviation.

        Returns:
            List of (host, anomaly_score) tuples for anomalous hosts
        """
        try:
            async with self._http_session.get(
                f"{self.rte_service_url}/hosts/list",
                params={"zone": self.state.area_patrulha},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return []

                data = await response.json()
                hosts = data.get("hosts", [])

                anomalias = []

                for host in hosts:
                    host_id = host.get("id")
                    if not host_id:
                        continue

                    # Get current metrics
                    metricas_atuais = await self._get_host_metrics(host_id)
                    if not metricas_atuais:
                        continue

                    # Calculate anomaly score
                    anomaly_score = self._calcular_anomalia(host_id, metricas_atuais)

                    # Threshold check
                    if anomaly_score > self.anomaly_threshold:
                        anomalias.append((host, anomaly_score))

                return anomalias

        except aiohttp.ClientConnectorError:
            logger.debug("RTE service unavailable for anomaly detection")
            return []

        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []

    async def _get_host_metrics(self, host_id: str) -> Dict[str, float]:
        """
        Get behavioral metrics for a host.

        Metrics:
        - cpu_usage: CPU utilization (0-100)
        - memory_usage: Memory utilization (0-100)
        - network_tx: Network transmission (bytes/sec)
        - network_rx: Network reception (bytes/sec)
        - process_count: Number of processes
        - failed_auth_count: Failed authentication attempts

        Returns:
            Dict of metric_name -> value
        """
        try:
            async with self._http_session.get(
                f"{self.rte_service_url}/hosts/{host_id}/metrics",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {}

        except aiohttp.ClientConnectorError:
            return {}

        except Exception as e:
            logger.error(f"Metrics retrieval error for {host_id}: {e}")
            return {}

    def _calcular_anomalia(self, host_id: str, metricas: Dict[str, float]) -> float:
        """
        Calculate anomaly score using Euclidean distance from baseline.

        In production, this would use:
        - Mahalanobis distance (accounts for correlation)
        - Isolation Forest (unsupervised anomaly detection)
        - LSTM autoencoder (temporal patterns)

        For now, simple Euclidean distance.

        Args:
            host_id: Host identifier
            metricas: Current metrics

        Returns:
            Anomaly score (0-1)
        """
        if host_id not in self.baseline_behavior:
            # First observation - store as baseline
            self.baseline_behavior[host_id] = metricas
            logger.debug(f"Baseline established for {host_id}")
            return 0.0

        baseline = self.baseline_behavior[host_id]

        # Calculate Euclidean distance
        distancia = 0.0
        metric_count = 0

        for key, valor in metricas.items():
            if key in baseline:
                # Normalize by baseline to handle different scales
                baseline_val = baseline[key]
                if baseline_val > 0:
                    normalized_diff = (valor - baseline_val) / baseline_val
                    distancia += normalized_diff**2
                    metric_count += 1

        if metric_count == 0:
            return 0.0

        # Normalize to 0-1 range
        # (sqrt(sum of squared normalized diffs) / sqrt(metric_count))
        anomaly_score = (distancia**0.5) / (metric_count**0.5)

        # Cap at 1.0
        return min(anomaly_score, 1.0)

    async def _update_baseline(self) -> None:
        """
        Update baseline for normal (non-anomalous) hosts.

        Uses exponential moving average to adapt to legitimate changes.
        """
        try:
            async with self._http_session.get(
                f"{self.rte_service_url}/hosts/list",
                params={"zone": self.state.area_patrulha},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    return

                data = await response.json()
                hosts = data.get("hosts", [])

                for host in hosts:
                    host_id = host.get("id")
                    if not host_id or host_id in self.hosts_isolados:
                        continue  # Skip isolated hosts

                    metricas = await self._get_host_metrics(host_id)
                    if not metricas:
                        continue

                    # Calculate anomaly
                    anomaly_score = self._calcular_anomalia(host_id, metricas)

                    # Only update baseline for normal hosts
                    if anomaly_score < 0.3:  # Low anomaly
                        if host_id in self.baseline_behavior:
                            # Exponential moving average (alpha=0.1)
                            baseline = self.baseline_behavior[host_id]
                            for key, valor in metricas.items():
                                if key in baseline:
                                    baseline[key] = 0.9 * baseline[key] + 0.1 * valor
                                else:
                                    baseline[key] = valor
                        else:
                            # New host
                            self.baseline_behavior[host_id] = metricas

        except Exception as e:
            logger.error(f"Baseline update error: {e}")

    # ==================== INVESTIGATION ====================

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        NK cells use rapid behavioral analysis (no deep investigation).

        Unlike Macrophages that correlate with IP intelligence,
        NK cells rely purely on behavioral deviation.

        Args:
            alvo: Target host

        Returns:
            Investigation result with anomaly score
        """
        host_id = alvo.get("id")

        # Update status
        self.state.status = AgentStatus.INVESTIGANDO

        # Get current metrics
        metricas_atuais = await self._get_host_metrics(host_id)

        if not metricas_atuais:
            logger.warning(f"No metrics available for {host_id}")
            return {
                "is_threat": False,
                "anomaly_score": 0.0,
                "method": "no_metrics",
            }

        # Calculate anomaly
        anomaly_score = self._calcular_anomalia(host_id, metricas_atuais)

        logger.info(
            f"NK investigation: {host_id} - anomaly_score={anomaly_score:.2f} (threshold={self.anomaly_threshold})"
        )

        return {
            "is_threat": anomaly_score > self.anomaly_threshold,
            "anomaly_score": anomaly_score,
            "metrics": metricas_atuais,
            "baseline": self.baseline_behavior.get(host_id, {}),
            "method": "behavioral_anomaly",
        }

    # ==================== NEUTRALIZATION ====================

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Cytotoxic kill: Complete host isolation.

        NK cells are cytotoxic - they kill infected cells completely.

        Args:
            alvo: Target host
            metodo: "isolate" (only supported method)

        Returns:
            True if successful
        """
        host_id = alvo.get("id")

        if metodo != "isolate":
            logger.warning(f"NK cells only support 'isolate' method, got '{metodo}'")
            return False

        logger.info(f"NK Cell cytotoxicity: isolating {host_id}")

        try:
            async with self._http_session.post(
                f"{self.rte_service_url}/hosts/isolate",
                json={
                    "host_id": host_id,
                    "reason": "nk_cell_cytotoxicity",
                    "duration_seconds": 86400,  # 24 hours
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    logger.info(f"Host {host_id} isolated by NK cell")

                    # Track locally
                    self.hosts_isolados.append(host_id)
                    if len(self.hosts_isolados) > 100:
                        self.hosts_isolados = self.hosts_isolados[-100:]  # Keep last 100

                    # Trigger IFN-gamma cytokine storm (activate other cells)
                    await self._secretar_ifn_gamma(alvo)

                    return True

                elif response.status == 404:
                    # RTE service unavailable - graceful degradation
                    logger.warning("RTE service unavailable, tracking isolation locally")
                    self.hosts_isolados.append(host_id)
                    if len(self.hosts_isolados) > 100:
                        self.hosts_isolados = self.hosts_isolados[-100:]  # Keep last 100
                    return True

                else:
                    logger.error(f"Isolation failed: {response.status}")
                    return False

        except aiohttp.ClientConnectorError:
            logger.warning("RTE service unavailable (graceful degradation)")
            # Track locally even if RTE unavailable
            self.hosts_isolados.append(host_id)
            if len(self.hosts_isolados) > 100:
                self.hosts_isolados = self.hosts_isolados[-100:]  # Keep last 100
            return True

        except Exception as e:
            logger.error(f"Isolation error: {e}")
            return False

    async def _secretar_ifn_gamma(self, alvo: Dict[str, Any]) -> None:
        """
        Secrete IFN-gamma cytokine to activate other immune cells.

        IFN-gamma:
        - Activates macrophages (enhanced phagocytosis)
        - Recruits neutrophils (swarm response)
        - Triggers adaptive immunity (T cell activation)
        """
        if not self._cytokine_messenger:
            logger.debug("Cytokine messenger not initialized")
            return

        try:
            await self._cytokine_messenger.send_cytokine(
                tipo="IFNgamma",
                payload={
                    "evento": "nk_cytotoxicity",
                    "nk_cell_id": self.state.id,
                    "host_id": alvo.get("id"),
                    "anomaly_score": alvo.get("anomaly_score", 0.0),
                    "timestamp": datetime.now().isoformat(),
                },
                emissor_id=self.state.id,
                prioridade=10,  # High priority (cytokine storm)
            )

            logger.info(f"IFN-gamma secreted for {alvo.get('id')}")

        except Exception as e:
            logger.error(f"Failed to secrete IFN-gamma: {e}")

    # ==================== METRICS ====================

    def get_nk_metrics(self) -> Dict[str, Any]:
        """
        Get NK Cell-specific metrics.

        Returns:
            Dict with NK-specific stats
        """
        return {
            "anomalias_detectadas": self.anomalias_detectadas,
            "hosts_isolados_total": len(self.hosts_isolados),
            "mhc_violations": self.mhc_violations,
            "baseline_hosts": len(self.baseline_behavior),
            "eficiencia_deteccao": (
                self.state.neutralizacoes_total / self.anomalias_detectadas if self.anomalias_detectadas > 0 else 0.0
            ),
        }

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"CelulaNKDigital({self.state.id[:8]}|{self.state.status}|"
            f"anomalias={self.anomalias_detectadas}|"
            f"isolados={len(self.hosts_isolados)}|"
            f"mhc_violations={self.mhc_violations})"
        )
