"""
Honeypot Manager
Coordinates all honeypots and integrates with honeytoken system
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base_honeypot import BaseHoneypot, AttackCapture
from .cowrie_ssh import CowrieSSHHoneypot
from .dvwa_web import DVWAWebHoneypot
from .postgres_honeypot import PostgreSQLHoneypot
from .honeytoken_manager import HoneytokenManager, Honeytoken

logger = logging.getLogger(__name__)

class HoneypotManager:
    """
    Central manager for all honeypots in Reactive Fabric

    Responsibilities:
    - Deploy and monitor honeypots
    - Coordinate honeytoken placement
    - Aggregate attack data
    - Provide unified interface for CANDI
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize honeypot manager

        Args:
            redis_url: Redis URL for honeytoken tracking
        """
        self.honeypots: Dict[str, BaseHoneypot] = {}
        self.honeytoken_manager = HoneytokenManager(redis_url)

        # Statistics
        self.stats = {
            "total_honeypots": 0,
            "active_honeypots": 0,
            "total_attacks_captured": 0,
            "honeytokens_triggered": 0,
            "active_sessions": 0
        }

        # Alert callbacks
        self._attack_callbacks: List[Any] = []

    async def initialize(self):
        """Initialize manager and honeytoken system"""
        await self.honeytoken_manager.initialize()

        # Register honeytoken trigger callback
        await self.honeytoken_manager.register_trigger_callback(
            self._on_honeytoken_triggered
        )

        logger.info("Honeypot Manager initialized")

    async def deploy_cowrie_ssh(self,
                                ssh_port: int = 2222,
                                telnet_port: int = 2223) -> CowrieSSHHoneypot:
        """
        Deploy Cowrie SSH/Telnet honeypot

        Args:
            ssh_port: SSH port
            telnet_port: Telnet port

        Returns:
            Deployed honeypot instance
        """
        honeypot = CowrieSSHHoneypot(
            honeypot_id="cowrie_ssh_01",
            ssh_port=ssh_port,
            telnet_port=telnet_port,
            layer=3
        )

        # Register attack callback
        honeypot.register_attack_callback(self._on_attack_captured)

        # Start honeypot
        success = await honeypot.start()

        if success:
            self.honeypots[honeypot.honeypot_id] = honeypot
            self.stats["total_honeypots"] += 1
            self.stats["active_honeypots"] += 1

            # Plant honeytokens
            await self._plant_honeytokens(honeypot.honeypot_id, "ssh")

            logger.info(f"Deployed Cowrie SSH honeypot on ports {ssh_port}/{telnet_port}")

        return honeypot

    async def deploy_dvwa_web(self,
                             http_port: int = 8080,
                             https_port: int = 8443) -> DVWAWebHoneypot:
        """
        Deploy DVWA web honeypot

        Args:
            http_port: HTTP port
            https_port: HTTPS port

        Returns:
            Deployed honeypot instance
        """
        honeypot = DVWAWebHoneypot(
            honeypot_id="dvwa_web_01",
            http_port=http_port,
            https_port=https_port,
            layer=3
        )

        # Register attack callback
        honeypot.register_attack_callback(self._on_attack_captured)

        # Start honeypot
        success = await honeypot.start()

        if success:
            self.honeypots[honeypot.honeypot_id] = honeypot
            self.stats["total_honeypots"] += 1
            self.stats["active_honeypots"] += 1

            # Plant honeytokens
            await self._plant_honeytokens(honeypot.honeypot_id, "web")

            logger.info(f"Deployed DVWA web honeypot on ports {http_port}/{https_port}")

        return honeypot

    async def deploy_postgres_db(self, port: int = 5433) -> PostgreSQLHoneypot:
        """
        Deploy PostgreSQL database honeypot

        Args:
            port: PostgreSQL port

        Returns:
            Deployed honeypot instance
        """
        honeypot = PostgreSQLHoneypot(
            honeypot_id="postgres_db_01",
            port=port,
            layer=3
        )

        # Register attack callback
        honeypot.register_attack_callback(self._on_attack_captured)

        # Start honeypot
        success = await honeypot.start()

        if success:
            self.honeypots[honeypot.honeypot_id] = honeypot
            self.stats["total_honeypots"] += 1
            self.stats["active_honeypots"] += 1

            # Plant honeytokens
            await self._plant_honeytokens(honeypot.honeypot_id, "database")

            logger.info(f"Deployed PostgreSQL honeypot on port {port}")

        return honeypot

    async def deploy_all_honeypots(self) -> Dict[str, BaseHoneypot]:
        """
        Deploy all honeypots in parallel

        Returns:
            Dictionary of deployed honeypots
        """
        logger.info("Deploying all honeypots...")

        # Deploy in parallel for speed
        tasks = [
            self.deploy_cowrie_ssh(),
            self.deploy_dvwa_web(),
            self.deploy_postgres_db()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        deployed = {}
        for result in results:
            if isinstance(result, BaseHoneypot):
                deployed[result.honeypot_id] = result
            elif isinstance(result, Exception):
                logger.error(f"Failed to deploy honeypot: {result}")

        logger.info(f"Successfully deployed {len(deployed)}/3 honeypots")
        return deployed

    async def _plant_honeytokens(self, honeypot_id: str, honeypot_type: str):
        """Plant honeytokens in a honeypot"""
        try:
            tokens = await self.honeytoken_manager.plant_tokens_in_honeypot(
                honeypot_id,
                honeypot_type
            )

            logger.info(f"Planted {len(tokens)} honeytokens in {honeypot_id}")

        except Exception as e:
            logger.error(f"Failed to plant honeytokens: {e}")

    def _on_attack_captured(self, attack: AttackCapture):
        """Callback when honeypot captures an attack"""
        self.stats["total_attacks_captured"] += 1

        logger.info(
            f"Attack captured: {attack.honeypot_id} from {attack.source_ip} "
            f"(threat: {attack.threat_score:.1f})"
        )

        # Forward to registered callbacks
        for callback in self._attack_callbacks:
            try:
                callback(attack)
            except Exception as e:
                logger.error(f"Attack callback error: {e}")

    async def _on_honeytoken_triggered(self,
                                       token: Honeytoken,
                                       source_ip: str,
                                       context: Dict):
        """Callback when a honeytoken is triggered"""
        self.stats["honeytokens_triggered"] += 1

        logger.critical(
            f"HONEYTOKEN TRIGGERED! Type: {token.token_type.value}, "
            f"Source: {source_ip}"
        )

        # This is a critical event - notify immediately
        await self._send_critical_alert({
            "alert_type": "HONEYTOKEN_TRIGGERED",
            "token_type": token.token_type.value,
            "token_id": token.token_id,
            "source_ip": source_ip,
            "context": context,
            "severity": "CRITICAL",
            "timestamp": datetime.now().isoformat()
        })

    async def _send_critical_alert(self, alert: Dict):
        """Send critical alert (to be integrated with alert system)"""
        # This will be integrated with the alert/notification system
        logger.critical(f"CRITICAL ALERT: {alert}")

    def register_attack_callback(self, callback):
        """Register callback for attack events"""
        self._attack_callbacks.append(callback)

    async def stop_all_honeypots(self):
        """Stop all running honeypots"""
        logger.info("Stopping all honeypots...")

        tasks = [
            honeypot.stop()
            for honeypot in self.honeypots.values()
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        self.stats["active_honeypots"] = 0
        logger.info("All honeypots stopped")

    async def stop_honeypot(self, honeypot_id: str) -> bool:
        """
        Stop a specific honeypot

        Args:
            honeypot_id: Honeypot to stop

        Returns:
            True if stopped successfully
        """
        if honeypot_id not in self.honeypots:
            logger.warning(f"Honeypot {honeypot_id} not found")
            return False

        honeypot = self.honeypots[honeypot_id]
        success = await honeypot.stop()

        if success:
            self.stats["active_honeypots"] -= 1
            logger.info(f"Stopped honeypot {honeypot_id}")

        return success

    def get_honeypot_status(self, honeypot_id: str) -> Optional[Dict]:
        """
        Get status of a specific honeypot

        Args:
            honeypot_id: Honeypot identifier

        Returns:
            Status dictionary or None
        """
        if honeypot_id not in self.honeypots:
            return None

        return self.honeypots[honeypot_id].get_status()

    def get_all_status(self) -> Dict:
        """Get status of all honeypots"""
        return {
            "manager_stats": self.stats,
            "honeytoken_stats": self.honeytoken_manager.get_stats(),
            "honeypots": {
                honeypot_id: honeypot.get_status()
                for honeypot_id, honeypot in self.honeypots.items()
            },
            "recent_triggers": self.honeytoken_manager.get_recent_triggers(10)
        }

    def get_aggregated_attacks(self, limit: int = 100) -> List[Dict]:
        """
        Get aggregated attack data from all honeypots

        Args:
            limit: Maximum number of attacks to return

        Returns:
            List of attack dictionaries
        """
        all_attacks = []

        for honeypot in self.honeypots.values():
            for attack in honeypot.captured_attacks[-limit:]:
                all_attacks.append({
                    "honeypot_id": honeypot.honeypot_id,
                    "honeypot_type": honeypot.honeypot_type.value,
                    "attack_id": attack.id,
                    "timestamp": attack.timestamp.isoformat(),
                    "source_ip": attack.source_ip,
                    "threat_score": attack.threat_score,
                    "attack_stage": attack.attack_stage.value,
                    "ttps": attack.ttps,
                    "iocs": attack.iocs
                })

        # Sort by timestamp (most recent first)
        all_attacks.sort(key=lambda x: x["timestamp"], reverse=True)

        return all_attacks[:limit]

    async def get_forensic_data(self,
                               honeypot_id: str,
                               attack_id: str) -> Optional[Dict]:
        """
        Get detailed forensic data for an attack

        Args:
            honeypot_id: Honeypot identifier
            attack_id: Attack identifier

        Returns:
            Forensic data dictionary or None
        """
        if honeypot_id not in self.honeypots:
            return None

        honeypot = self.honeypots[honeypot_id]
        return honeypot.get_forensic_data(attack_id)

    def get_honeypot_by_type(self, honeypot_type: str) -> List[BaseHoneypot]:
        """
        Get all honeypots of a specific type

        Args:
            honeypot_type: Type of honeypot (ssh, web, database)

        Returns:
            List of honeypots
        """
        return [
            honeypot for honeypot in self.honeypots.values()
            if honeypot.honeypot_type.value == honeypot_type
        ]

    async def health_check(self) -> Dict:
        """
        Perform health check on all honeypots

        Returns:
            Health status dictionary
        """
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "honeypots": {}
        }

        for honeypot_id, honeypot in self.honeypots.items():
            is_healthy = honeypot._running  # Check if honeypot is running

            health_status["honeypots"][honeypot_id] = {
                "status": "healthy" if is_healthy else "unhealthy",
                "running": is_healthy,
                "active_sessions": len(honeypot.active_sessions),
                "total_attacks": len(honeypot.captured_attacks)
            }

            if not is_healthy:
                health_status["overall_health"] = "degraded"

        return health_status