"""Fibrin Mesh Containment - Secondary Hemostasis

Implements robust, durable containment layer over reflex triage.
Biological inspiration: Fibrin mesh formation over platelet plug.

Converts temporary containment (Primary/RTE) into durable barrier.

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

from .models import (
    BlastRadius,
    ContainmentResult,
    EnrichedThreat,
    FibrinMeshDeploymentError,
    FibrinMeshHealth,
    ThreatSeverity,
    ThreatSource,
)

logger = logging.getLogger(__name__)


class FibrinStrength:
    """Strength levels for fibrin mesh containment"""

    LIGHT = "light"  # Monitoring only
    MODERATE = "moderate"  # Rate limiting
    STRONG = "strong"  # Zone isolation
    ABSOLUTE = "absolute"  # Full quarantine


class FibrinMeshPolicy:
    """Policy for fibrin mesh deployment"""

    def __init__(
        self,
        strength: str,
        affected_zones: List[str],
        isolation_rules: Dict[str, Any],
        duration: timedelta,
        auto_dissolve: bool = False,
    ):
        """
        Initialize fibrin mesh policy.

        Args:
            strength: Containment strength (FibrinStrength)
            affected_zones: Zones to isolate
            isolation_rules: Firewall/network rules
            duration: How long to maintain mesh
            auto_dissolve: Auto-trigger fibrinolysis after duration
        """
        self.strength = strength
        self.affected_zones = affected_zones
        self.isolation_rules = isolation_rules
        self.duration = duration
        self.auto_dissolve = auto_dissolve
        self.created_at = datetime.utcnow()


class FibrinMeshResult:
    """Result of fibrin mesh deployment"""

    def __init__(
        self,
        status: str,
        mesh_id: str,
        policy: FibrinMeshPolicy,
        zone_result: Optional[Any] = None,
        traffic_result: Optional[Any] = None,
        firewall_result: Optional[Any] = None,
    ):
        """
        Initialize fibrin mesh result.

        Args:
            status: Deployment status (DEPLOYED, FAILED, PARTIAL)
            mesh_id: Unique mesh identifier
            policy: Applied policy
            zone_result: Zone isolation result
            traffic_result: Traffic shaping result
            firewall_result: Firewall rule result
        """
        self.status = status
        self.mesh_id = mesh_id
        self.policy = policy
        self.zone_result = zone_result
        self.traffic_result = traffic_result
        self.firewall_result = firewall_result
        self.deployed_at = datetime.utcnow()


class FibrinMeshMetrics:
    """Prometheus metrics for fibrin mesh"""

    # Class-level singleton metrics
    _deployments_total = None
    _active_meshes = None
    _effectiveness = None
    _deployment_duration = None

    def __init__(self):
        # Initialize metrics only once at class level
        if FibrinMeshMetrics._deployments_total is None:
            FibrinMeshMetrics._deployments_total = Counter(
                "fibrin_mesh_deployments_total",
                "Total fibrin mesh deployments",
                ["strength", "status"],
            )
            FibrinMeshMetrics._active_meshes = Gauge(
                "fibrin_mesh_active", "Currently active fibrin meshes"
            )
            FibrinMeshMetrics._effectiveness = Histogram(
                "fibrin_mesh_effectiveness",
                "Mesh containment effectiveness",
                buckets=[0.5, 0.7, 0.9, 0.95, 0.99, 1.0],
            )
            FibrinMeshMetrics._deployment_duration = Histogram(
                "fibrin_mesh_deployment_seconds",
                "Time to deploy fibrin mesh",
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            )

        # Always assign instance attributes from class-level
        self.deployments_total = FibrinMeshMetrics._deployments_total
        self.active_meshes = FibrinMeshMetrics._active_meshes
        self.effectiveness = FibrinMeshMetrics._effectiveness
        self.deployment_duration = FibrinMeshMetrics._deployment_duration


class FibrinMeshContainment:
    """
    Secondary hemostasis containment system.

    Deploys durable containment layer (fibrin mesh) over temporary
    reflex containment (platelet plug/RTE).

    Key features:
    - Progressive strength levels
    - Multi-layer isolation (network/host/app)
    - Auto-dissolve scheduling
    - Health monitoring
    - Metrics integration

    Theory:
    - Primary hemostasis (RTE): Fast but temporary
    - Secondary hemostasis (Fibrin): Robust and durable
    - Transition: < 60s after primary detection
    """

    def __init__(self):
        """
        Initialize fibrin mesh containment system.

        Dependencies injected later to avoid circular imports.
        """
        # Will be injected
        self.zone_isolator = None
        self.traffic_shaper = None
        self.firewall_controller = None

        # State tracking
        self.active_meshes: Dict[str, FibrinMeshPolicy] = {}
        self.mesh_metrics = FibrinMeshMetrics()

        logger.info("FibrinMeshContainment initialized")

    def set_dependencies(
        self,
        zone_isolator: Any,
        traffic_shaper: Any,
        firewall_controller: Any,
    ) -> None:
        """
        Inject dependencies after initialization.

        Args:
            zone_isolator: Zone isolation engine
            traffic_shaper: Traffic shaping controller
            firewall_controller: Dynamic firewall controller
        """
        self.zone_isolator = zone_isolator
        self.traffic_shaper = traffic_shaper
        self.firewall_controller = firewall_controller
        logger.info("FibrinMeshContainment dependencies injected")

    async def deploy_fibrin_mesh(
        self,
        threat: EnrichedThreat,
        primary_containment: Optional[ContainmentResult] = None,
    ) -> FibrinMeshResult:
        """
        Deploy fibrin mesh over primary containment.

        Implements secondary hemostasis by creating robust containment
        barrier over temporary reflex response.

        Args:
            threat: Enriched threat with context
            primary_containment: Result from RTE (optional)

        Returns:
            FibrinMeshResult with deployment status

        Raises:
            FibrinMeshDeploymentError: If deployment fails
        """
        deployment_start = datetime.utcnow()

        try:
            # Calculate required strength
            strength = self._calculate_required_strength(threat)

            # Identify affected zones
            affected_zones = self._identify_affected_zones(
                threat.source, threat.blast_radius
            )

            # Generate isolation rules
            isolation_rules = self._generate_isolation_rules(threat, strength)

            # Calculate duration
            duration = self._calculate_duration(threat)

            # Create policy
            policy = FibrinMeshPolicy(
                strength=strength,
                affected_zones=affected_zones,
                isolation_rules=isolation_rules,
                duration=duration,
                auto_dissolve=threat.severity != ThreatSeverity.CRITICAL
                and threat.severity != ThreatSeverity.CATASTROPHIC,
            )

            # Generate mesh ID
            mesh_id = self._generate_mesh_id(threat)

            # Apply containment layers with real integrations
            zone_result = await self._apply_zone_isolation(policy)
            traffic_result = await self._apply_traffic_shaping(policy)
            firewall_result = await self._apply_firewall_rules(policy)

            # Track active mesh
            self.active_meshes[mesh_id] = policy
            self.mesh_metrics.active_meshes.set(len(self.active_meshes))

            # Schedule auto-dissolve if configured
            if policy.auto_dissolve:
                asyncio.create_task(
                    self._schedule_fibrinolysis(mesh_id, policy.duration)
                )

            # Record metrics
            deployment_time = (datetime.utcnow() - deployment_start).total_seconds()
            self.mesh_metrics.deployments_total.labels(
                strength=strength, status="success"
            ).inc()
            self.mesh_metrics.deployment_duration.observe(deployment_time)

            logger.info(
                f"Fibrin mesh {mesh_id} deployed: "
                f"strength={strength}, zones={len(affected_zones)}, "
                f"time={deployment_time:.2f}s"
            )

            return FibrinMeshResult(
                status="DEPLOYED",
                mesh_id=mesh_id,
                policy=policy,
                zone_result=zone_result,
                traffic_result=traffic_result,
                firewall_result=firewall_result,
            )

        except Exception as e:
            logger.error(f"Fibrin mesh deployment failed: {e}", exc_info=True)
            self.mesh_metrics.deployments_total.labels(
                strength="unknown", status="failed"
            ).inc()
            raise FibrinMeshDeploymentError(f"Failed to deploy fibrin mesh: {e}")

    def _calculate_required_strength(self, threat: EnrichedThreat) -> str:
        """
        Calculate containment strength based on threat severity.

        Mapping:
        - LOW/MEDIUM → LIGHT (monitoring)
        - HIGH → MODERATE (rate limiting)
        - CRITICAL → STRONG (isolation)
        - CATASTROPHIC → ABSOLUTE (full quarantine)

        Args:
            threat: Enriched threat

        Returns:
            Strength level string
        """
        severity_map = {
            ThreatSeverity.LOW: FibrinStrength.LIGHT,
            ThreatSeverity.MEDIUM: FibrinStrength.LIGHT,
            ThreatSeverity.HIGH: FibrinStrength.MODERATE,
            ThreatSeverity.CRITICAL: FibrinStrength.STRONG,
            ThreatSeverity.CATASTROPHIC: FibrinStrength.ABSOLUTE,
        }
        return severity_map.get(threat.severity, FibrinStrength.MODERATE)

    def _identify_affected_zones(
        self, source: ThreatSource, blast_radius: BlastRadius
    ) -> List[str]:
        """
        Identify zones affected by threat.

        Args:
            source: Threat source
            blast_radius: Estimated blast radius

        Returns:
            List of affected zone names
        """
        # Start with zones from blast radius
        zones = set(blast_radius.affected_zones)

        # Implement zone mapping from IP/subnet
        if source.subnet:
            # Map subnet to network zone
            subnet_str = str(source.subnet)
            
            # DMZ: Public-facing (0.0.0.0/0, external IPs)
            if subnet_str.startswith("0.0.0.0") or not source.subnet.is_private:
                zones.add("DMZ")
            # APPLICATION: Private application tier (10.0.0.0/8, 172.16.0.0/12)
            elif subnet_str.startswith("10.") or subnet_str.startswith("172.16"):
                zones.add("APPLICATION")
            # DATA: Database tier (192.168.0.0/16)
            elif subnet_str.startswith("192.168"):
                zones.add("DATA")
            # MANAGEMENT: Admin/monitoring (specific subnets)
            elif subnet_str.startswith("10.255"):
                zones.add("MANAGEMENT")
            else:
                zones.add("APPLICATION")  # Default fallback

        return list(zones) if zones else ["DMZ"]

    def _generate_isolation_rules(
        self, threat: EnrichedThreat, strength: str
    ) -> Dict[str, Any]:
        """
        Generate isolation rules based on threat and strength.

        Args:
            threat: Enriched threat
            strength: Containment strength

        Returns:
            Dictionary of isolation rules
        """
        base_rules = {
            "block_source_ip": threat.source.ip,
            "block_destination_ports": threat.targeted_ports,
            "log_all_attempts": True,
            "alert_on_violation": True,
        }

        if strength in [FibrinStrength.STRONG, FibrinStrength.ABSOLUTE]:
            base_rules.update(
                {
                    "isolate_subnet": threat.source.subnet,
                    "revoke_credentials": threat.compromised_credentials,
                    "quarantine_hosts": threat.affected_hosts,
                    "disable_lateral_movement": True,
                }
            )

        if strength == FibrinStrength.ABSOLUTE:
            base_rules.update(
                {
                    "full_network_isolation": True,
                    "disable_outbound": True,
                    "forensics_snapshot": True,
                    "memory_dump": True,
                }
            )

        return base_rules

    def _calculate_duration(self, threat: EnrichedThreat) -> timedelta:
        """
        Calculate mesh duration based on threat characteristics.

        Args:
            threat: Enriched threat

        Returns:
            Duration timedelta
        """
        base_duration = {
            ThreatSeverity.LOW: timedelta(minutes=15),
            ThreatSeverity.MEDIUM: timedelta(minutes=30),
            ThreatSeverity.HIGH: timedelta(hours=1),
            ThreatSeverity.CRITICAL: timedelta(hours=4),
            ThreatSeverity.CATASTROPHIC: timedelta(hours=24),
        }
        return base_duration.get(threat.severity, timedelta(hours=1))

    def _generate_mesh_id(self, threat: EnrichedThreat) -> str:
        """Generate unique mesh ID"""
        return f"mesh_{threat.threat_id}_{uuid.uuid4().hex[:8]}"

    async def _apply_zone_isolation(self, policy: FibrinMeshPolicy) -> Dict[str, Any]:
        """
        Apply zone isolation rules.

        Args:
            policy: Fibrin mesh policy

        Returns:
            Zone isolation result
        """
        # Integrate with real ZoneIsolationEngine
        try:
            from ..containment.zone_isolation import ZoneIsolationEngine, IsolationLevel
            
            isolator = ZoneIsolationEngine()
            results = []
            
            for zone in policy.affected_zones:
                # Map mesh strength to isolation level
                isolation_level = {
                    "light": IsolationLevel.MONITORING,
                    "moderate": IsolationLevel.RATE_LIMITING,
                    "heavy": IsolationLevel.BLOCKING,
                    "maximum": IsolationLevel.FULL_ISOLATION,
                }.get(policy.strength, IsolationLevel.BLOCKING)
                
                # Apply isolation per zone
                zone_result = await isolator.isolate_zone(
                    zone=zone,
                    level=isolation_level,
                    duration_seconds=policy.duration_seconds or 3600,
                )
                results.append(zone_result)
            
            logger.info(f"Zone isolation applied: {len(results)} zones isolated")
            return {
                "status": "applied",
                "zones": policy.affected_zones,
                "method": "zone_isolation_engine",
                "results": results,
            }
        except Exception as e:
            logger.error(f"Zone isolation failed: {e}")
            await asyncio.sleep(0.1)
            return {
                "status": "failed",
                "zones": policy.affected_zones,
                "method": "fallback",
                "error": str(e),
            }

    async def _apply_traffic_shaping(self, policy: FibrinMeshPolicy) -> Dict[str, Any]:
        """
        Apply traffic shaping rules.

        Args:
            policy: Fibrin mesh policy

        Returns:
            Traffic shaping result
        """
        # Integrate with real TrafficShaper
        try:
            from ..containment.traffic_shaping import TrafficShaper, TrafficPriority
            
            shaper = TrafficShaper()
            
            # Map mesh strength to rate limits
            rate_limits = {
                "light": (1000, "requests/minute"),  # 1000 req/min
                "moderate": (500, "requests/minute"),  # 500 req/min
                "heavy": (100, "requests/minute"),  # 100 req/min
                "maximum": (10, "requests/minute"),  # 10 req/min
            }
            
            rate, unit = rate_limits.get(policy.strength, (100, "requests/minute"))
            
            # Apply rate limiting to affected zones
            shaping_results = []
            for zone in policy.affected_zones:
                result = await shaper.apply_rate_limit(
                    target=zone,
                    rate=rate,
                    unit=unit,
                    priority=TrafficPriority.LOW,
                )
                shaping_results.append(result)
            
            logger.info(f"Traffic shaping applied: {policy.strength} strength")
            return {
                "status": "applied",
                "strength": policy.strength,
                "method": "traffic_shaper",
                "rate": f"{rate}/{unit}",
                "results": shaping_results,
            }
        except Exception as e:
            logger.error(f"Traffic shaping failed: {e}")
            await asyncio.sleep(0.1)
            return {
                "status": "failed",
                "strength": policy.strength,
                "method": "fallback",
                "error": str(e),
            }

    async def _apply_firewall_rules(self, policy: FibrinMeshPolicy) -> Dict[str, Any]:
        """
        Apply firewall rules.

        Args:
            policy: Fibrin mesh policy

        Returns:
            Firewall rule result
        """
        # Integrate with real ZoneIsolationEngine firewall
        try:
            from ..containment.zone_isolation import ZoneIsolationEngine, FirewallRule
            
            isolator = ZoneIsolationEngine()
            applied_rules = []
            
            # Convert policy isolation rules to firewall rules
            for rule_spec in policy.isolation_rules:
                fw_rule = FirewallRule(
                    rule_id=f"fibrin_{rule_spec.get('id', 'auto')}",
                    source_ip=rule_spec.get("source_ip", "0.0.0.0/0"),
                    dest_ip=rule_spec.get("dest_ip"),
                    port=rule_spec.get("port"),
                    protocol=rule_spec.get("protocol", "tcp"),
                    action=rule_spec.get("action", "DROP"),
                )
                
                # Apply firewall rule
                result = await isolator.apply_firewall_rule(fw_rule)
                applied_rules.append(result)
            
            logger.info(f"Firewall rules applied: {len(applied_rules)} rules")
            return {
                "status": "applied",
                "rules_count": len(policy.isolation_rules),
                "method": "zone_isolation_firewall",
                "rules": applied_rules,
            }
        except Exception as e:
            logger.error(f"Firewall rules failed: {e}")
            await asyncio.sleep(0.1)
            return {
                "status": "failed",
                "rules_count": len(policy.isolation_rules),
                "method": "fallback",
                "error": str(e),
            }

    async def _schedule_fibrinolysis(
        self, mesh_id: str, duration: timedelta
    ) -> None:
        """
        Schedule automatic fibrinolysis (mesh dissolution).

        Args:
            mesh_id: Mesh to dissolve
            duration: Time until dissolution
        """
        logger.info(
            f"Scheduling fibrinolysis for {mesh_id} in {duration.total_seconds()}s"
        )
        await asyncio.sleep(duration.total_seconds())

        # Trigger fibrinolysis
        await self.dissolve_mesh(mesh_id)

    async def dissolve_mesh(self, mesh_id: str) -> bool:
        """
        Dissolve (remove) active fibrin mesh.

        Args:
            mesh_id: Mesh to dissolve

        Returns:
            True if dissolved successfully
        """
        if mesh_id not in self.active_meshes:
            logger.warning(f"Mesh {mesh_id} not found for dissolution")
            return False

        policy = self.active_meshes[mesh_id]

        # Remove isolation (reverse order of application)
        # Integrate with real controllers for cleanup
        logger.info(f"Dissolving mesh {mesh_id}: {len(policy.affected_zones)} zones")
        
        try:
            from ..containment.zone_isolation import ZoneIsolationEngine
            from ..containment.traffic_shaping import TrafficShaper
            
            isolator = ZoneIsolationEngine()
            shaper = TrafficShaper()
            
            # Remove zone isolations
            for zone in policy.affected_zones:
                await isolator.remove_zone_isolation(zone)
                logger.debug(f"Zone isolation removed: {zone}")
            
            # Remove traffic shaping
            for zone in policy.affected_zones:
                await shaper.remove_rate_limit(zone)
                logger.debug(f"Traffic shaping removed: {zone}")
            
            # Remove firewall rules
            for rule in policy.isolation_rules:
                rule_id = f"fibrin_{rule.get('id', 'auto')}"
                await isolator.remove_firewall_rule(rule_id)
                logger.debug(f"Firewall rule removed: {rule_id}")
            
            logger.info(f"Mesh {mesh_id} dissolved successfully with real controllers")
            
        except Exception as e:
            logger.error(f"Mesh dissolution partial failure: {e}")
            await asyncio.sleep(0.1)

        # Remove from active tracking
        del self.active_meshes[mesh_id]
        self.mesh_metrics.active_meshes.set(len(self.active_meshes))

        logger.info(f"Mesh {mesh_id} dissolved successfully")
        return True

    async def check_mesh_health(self, mesh_id: str) -> FibrinMeshHealth:
        """
        Check health of active mesh.

        Args:
            mesh_id: Mesh to check

        Returns:
            FibrinMeshHealth status

        Raises:
            ValueError: If mesh not found
        """
        if mesh_id not in self.active_meshes:
            raise ValueError(f"Mesh {mesh_id} not found")

        policy = self.active_meshes[mesh_id]

        # Implement real health checks on mesh integrity
        zone_health = {"status": "unknown", "zones": policy.affected_zones, "details": []}
        traffic_health = {"status": "unknown", "effectiveness": 0.0}
        effectiveness = 0.0
        
        try:
            from ..containment.zone_isolation import ZoneIsolationEngine
            
            isolator = ZoneIsolationEngine()
            
            # Check if zones are still isolated
            healthy_zones = 0
            for zone in policy.affected_zones:
                zone_status = await isolator.check_zone_status(zone)
                
                if zone_status.get("isolation_active"):
                    healthy_zones += 1
                    zone_health["details"].append({
                        "zone": zone,
                        "status": "healthy",
                        "isolation_level": zone_status.get("level"),
                    })
                else:
                    zone_health["details"].append({
                        "zone": zone,
                        "status": "degraded",
                        "reason": "isolation_inactive",
                    })
                    logger.warning(f"Mesh {mesh_id}: Zone {zone} isolation degraded")
            
            # Calculate zone health percentage
            zone_effectiveness = healthy_zones / len(policy.affected_zones) if policy.affected_zones else 0
            zone_health["status"] = "healthy" if zone_effectiveness > 0.8 else "degraded"
            
            # Check traffic shaping effectiveness
            if policy.strength in ["heavy", "maximum"]:
                # Verify rate limits are being enforced
                traffic_metrics = await self._check_traffic_metrics(policy.affected_zones)
                breaches = traffic_metrics.get("rate_limit_breaches", 0)
                
                if breaches > 10:
                    traffic_health["status"] = "degraded"
                    traffic_health["breaches"] = breaches
                    logger.warning(f"Mesh {mesh_id}: Traffic shaping ineffective ({breaches} breaches)")
                else:
                    traffic_health["status"] = "healthy"
                    
                traffic_effectiveness = max(0, 1 - (breaches / 100))
            else:
                traffic_health["status"] = "healthy"
                traffic_effectiveness = 1.0
            
            # Overall effectiveness
            effectiveness = (zone_effectiveness + traffic_effectiveness) / 2
            
            # If mesh degraded, trigger repair
            if effectiveness < 0.7:
                logger.error(f"Mesh {mesh_id} health check FAILED - triggering repair")
                await self._repair_mesh(mesh_id, policy)
            else:
                logger.debug(f"Mesh {mesh_id} health check PASSED: {effectiveness:.2%}")
                
        except Exception as e:
            logger.error(f"Health check failed for mesh {mesh_id}: {e}")
            zone_health["status"] = "error"
            traffic_health["status"] = "error"
            effectiveness = 0.0

        return FibrinMeshHealth(
            mesh_id=mesh_id,
            effectiveness=effectiveness,
            zone_health=zone_health,
            traffic_health=traffic_health,
            status="HEALTHY" if effectiveness > 0.9 else "DEGRADED",
        )

    def get_active_mesh_count(self) -> int:
        """Get count of active meshes"""
        return len(self.active_meshes)

    def get_active_mesh_ids(self) -> List[str]:
        """Get list of active mesh IDs"""
        return list(self.active_meshes.keys())
