"""
Base Honeypot Implementation
Abstract base class for all honeypot types
"""

import asyncio
import hashlib
import json
import logging
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

class HoneypotType(Enum):
    """Types of honeypots"""
    SSH = "ssh"
    WEB = "web"
    DATABASE = "database"
    SMTP = "smtp"
    FTP = "ftp"
    TELNET = "telnet"
    RDP = "rdp"
    SCADA = "scada"

class AttackStage(Enum):
    """Stages of an attack"""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"

@dataclass
class AttackCapture:
    """Captured attack information"""
    id: str
    honeypot_id: str
    honeypot_type: HoneypotType
    timestamp: datetime
    source_ip: str
    source_port: int
    destination_port: int
    protocol: str
    attack_stage: AttackStage
    commands: List[str] = field(default_factory=list)
    files_uploaded: List[str] = field(default_factory=list)
    files_downloaded: List[str] = field(default_factory=list)
    credentials_used: Dict[str, str] = field(default_factory=dict)
    session_duration: float = 0.0
    bytes_transferred: int = 0
    threat_score: float = 0.0
    iocs: List[str] = field(default_factory=list)  # Indicators of Compromise
    ttps: List[str] = field(default_factory=list)  # Tactics, Techniques, Procedures
    raw_logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseHoneypot(ABC):
    """
    Abstract base class for honeypot implementations
    Provides common functionality for all honeypot types
    """

    def __init__(self,
                 honeypot_id: str,
                 honeypot_type: HoneypotType,
                 port: int,
                 layer: int = 3,  # Default to Layer 3 (Sacrifice Island)
                 log_path: Optional[Path] = None):
        """
        Initialize base honeypot

        Args:
            honeypot_id: Unique identifier for this honeypot
            honeypot_type: Type of honeypot
            port: Port to listen on
            layer: Network layer (1, 2, or 3)
            log_path: Path for honeypot logs
        """
        self.honeypot_id = honeypot_id
        self.honeypot_type = honeypot_type
        self.port = port
        self.layer = layer
        self.log_path = log_path or Path(f"/var/log/reactive_fabric/honeypots/{honeypot_id}")

        # Container management
        self.container_id: Optional[str] = None
        self.container_name = f"honeypot_{honeypot_id}"
        self._running = False

        # Attack tracking
        self.active_sessions: Dict[str, AttackCapture] = {}
        self.captured_attacks: List[AttackCapture] = []

        # Callbacks
        self._attack_callbacks: List[Callable] = []

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "attacks_captured": 0,
            "files_captured": 0,
            "credentials_captured": 0,
            "bytes_logged": 0
        }

        # Ensure log directory exists
        self.log_path.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def start(self) -> bool:
        """Start the honeypot"""
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """Stop the honeypot"""
        pass

    @abstractmethod
    def get_docker_config(self) -> Dict[str, Any]:
        """Get Docker configuration for this honeypot"""
        pass

    async def deploy(self) -> bool:
        """
        Deploy honeypot as Docker container
        Common deployment logic for all honeypots
        """
        if self._running:
            logger.warning(f"Honeypot {self.honeypot_id} already running")
            return False

        try:
            # Get specific configuration
            config = self.get_docker_config()

            # Build Docker run command
            cmd = self._build_docker_command(config)

            # Run container
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to start honeypot: {result.stderr}")
                return False

            # Get container ID
            self.container_id = result.stdout.strip()

            # Connect to appropriate network layer
            await self._connect_to_network()

            self._running = True
            logger.info(f"Honeypot {self.honeypot_id} deployed on port {self.port}")

            # Start monitoring
            asyncio.create_task(self._monitor_honeypot())

            return True

        except Exception as e:
            logger.error(f"Failed to deploy honeypot {self.honeypot_id}: {e}")
            return False

    def _build_docker_command(self, config: Dict) -> List[str]:
        """Build Docker run command from config"""
        cmd = [
            "docker", "run", "-d",
            "--name", self.container_name,
            "--hostname", config.get("hostname", self.honeypot_id),
            "-p", f"{self.port}:{config.get('internal_port', self.port)}",
            "--memory", config.get("memory", "512m"),
            "--cpus", config.get("cpus", "0.5"),
            "--restart", "unless-stopped"
        ]

        # Add environment variables
        for key, value in config.get("environment", {}).items():
            cmd.extend(["-e", f"{key}={value}"])

        # Add volumes
        for volume in config.get("volumes", []):
            cmd.extend(["-v", volume])

        # Add labels
        labels = {
            "reactive_fabric": "true",
            "honeypot_type": self.honeypot_type.value,
            "honeypot_id": self.honeypot_id,
            "layer": str(self.layer)
        }
        for key, value in labels.items():
            cmd.extend(["--label", f"{key}={value}"])

        # Add image
        cmd.append(config["image"])

        # Add command if specified
        if "command" in config:
            cmd.extend(config["command"])

        return cmd

    async def _connect_to_network(self):
        """Connect honeypot to appropriate network layer"""
        network_name = f"reactive_fabric_layer{self.layer}"

        cmd = ["docker", "network", "connect", network_name, self.container_id]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.warning(f"Could not connect to network: {result.stderr}")

    async def _monitor_honeypot(self):
        """Monitor honeypot for attacks and activity"""
        while self._running:
            try:
                # Check container health
                if not await self._is_healthy():
                    logger.warning(f"Honeypot {self.honeypot_id} unhealthy")
                    await self._restart_if_needed()

                # Process logs
                await self._process_logs()

                # Update statistics
                self._update_stats()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Monitor error for {self.honeypot_id}: {e}")

    async def _is_healthy(self) -> bool:
        """Check if honeypot container is healthy"""
        if not self.container_id:
            return False

        cmd = ["docker", "inspect", self.container_id, "--format", "{{.State.Running}}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        return result.returncode == 0 and "true" in result.stdout.lower()

    async def _restart_if_needed(self):
        """Restart honeypot if it crashed"""
        if self.stats["active_connections"] == 0:  # Only restart if no active connections
            logger.info(f"Restarting honeypot {self.honeypot_id}")

            # Stop cleanly
            await self.stop()

            # Wait a moment
            await asyncio.sleep(5)

            # Restart
            await self.start()

    @abstractmethod
    async def _process_logs(self):
        """Process honeypot logs for attack detection"""
        pass

    def _update_stats(self):
        """Update honeypot statistics"""
        # Get container stats
        if self.container_id:
            cmd = ["docker", "stats", self.container_id, "--no-stream", "--format",
                   "{{.MemUsage}} {{.CPUPerc}} {{.NetIO}}"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Parse and log stats
                logger.debug(f"Container stats for {self.honeypot_id}: {result.stdout.strip()}")

    def capture_attack(self, source_ip: str, source_port: int, **kwargs) -> AttackCapture:
        """
        Capture an attack

        Args:
            source_ip: Attacker's IP address
            source_port: Attacker's source port
            **kwargs: Additional attack details

        Returns:
            AttackCapture object
        """
        # Generate attack ID
        attack_id = hashlib.sha256(
            f"{self.honeypot_id}{source_ip}{datetime.now()}".encode()
        ).hexdigest()[:16]

        attack = AttackCapture(
            id=attack_id,
            honeypot_id=self.honeypot_id,
            honeypot_type=self.honeypot_type,
            timestamp=datetime.now(),
            source_ip=source_ip,
            source_port=source_port,
            destination_port=self.port,
            protocol=kwargs.get("protocol", "tcp"),
            attack_stage=kwargs.get("attack_stage", AttackStage.INITIAL_ACCESS),
            **{k: v for k, v in kwargs.items() if k not in ["protocol", "attack_stage"]}
        )

        self.captured_attacks.append(attack)
        self.stats["attacks_captured"] += 1

        # Notify callbacks
        for callback in self._attack_callbacks:
            try:
                callback(attack)
            except Exception as e:
                logger.error(f"Attack callback error: {e}")

        # Log attack
        self._log_attack(attack)

        return attack

    def _log_attack(self, attack: AttackCapture):
        """Log attack to file"""
        attack_log = {
            "timestamp": attack.timestamp.isoformat(),
            "id": attack.id,
            "source": f"{attack.source_ip}:{attack.source_port}",
            "stage": attack.attack_stage.value,
            "commands": attack.commands,
            "files": {
                "uploaded": attack.files_uploaded,
                "downloaded": attack.files_downloaded
            },
            "iocs": attack.iocs,
            "ttps": attack.ttps,
            "threat_score": attack.threat_score
        }

        log_file = self.log_path / f"attacks_{datetime.now().strftime('%Y%m%d')}.jsonl"

        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(attack_log) + "\n")
        except Exception as e:
            logger.error(f"Failed to log attack: {e}")

    def register_attack_callback(self, callback: Callable):
        """Register callback for attack notifications"""
        self._attack_callbacks.append(callback)

    async def shutdown(self):
        """Gracefully shutdown honeypot"""
        logger.info(f"Shutting down honeypot {self.honeypot_id}")

        # Stop monitoring
        self._running = False

        # Wait for active sessions to complete (max 30 seconds)
        timeout = 30
        start_time = asyncio.get_event_loop().time()

        while self.active_sessions and (asyncio.get_event_loop().time() - start_time) < timeout:
            await asyncio.sleep(1)

        # Force stop container
        if self.container_id:
            cmd = ["docker", "stop", self.container_id]
            subprocess.run(cmd, capture_output=True)

            # Remove container
            cmd = ["docker", "rm", self.container_id]
            subprocess.run(cmd, capture_output=True)

        logger.info(f"Honeypot {self.honeypot_id} shutdown complete")

    def get_status(self) -> Dict:
        """Get honeypot status"""
        return {
            "id": self.honeypot_id,
            "type": self.honeypot_type.value,
            "port": self.port,
            "layer": self.layer,
            "running": self._running,
            "container_id": self.container_id,
            "active_sessions": len(self.active_sessions),
            "stats": self.stats,
            "recent_attacks": [
                {
                    "id": attack.id,
                    "timestamp": attack.timestamp.isoformat(),
                    "source": attack.source_ip,
                    "stage": attack.attack_stage.value
                }
                for attack in self.captured_attacks[-5:]  # Last 5 attacks
            ]
        }

    def get_forensic_data(self, attack_id: str) -> Optional[Dict]:
        """
        Get detailed forensic data for an attack

        Args:
            attack_id: Attack ID to retrieve

        Returns:
            Forensic data dictionary or None
        """
        for attack in self.captured_attacks:
            if attack.id == attack_id:
                return {
                    "attack": attack.__dict__,
                    "logs": self._get_attack_logs(attack_id),
                    "pcap": self._get_attack_pcap(attack_id),
                    "memory": self._get_attack_memory(attack_id)
                }

        return None

    def _get_attack_logs(self, attack_id: str) -> List[str]:
        """Get logs for specific attack"""
        # Implementation would retrieve logs from log files
        return []

    def _get_attack_pcap(self, attack_id: str) -> Optional[str]:
        """Get PCAP file path for attack"""
        pcap_file = self.log_path / f"pcap/{attack_id}.pcap"
        return str(pcap_file) if pcap_file.exists() else None

    def _get_attack_memory(self, attack_id: str) -> Optional[str]:
        """Get memory dump for attack"""
        mem_file = self.log_path / f"memory/{attack_id}.mem"
        return str(mem_file) if mem_file.exists() else None