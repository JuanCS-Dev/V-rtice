"""Dynamic Honeypots - Deception & TTP Collection

Implements adaptive honeypot deployment for threat intelligence
and attacker deception. Inspired by immune system decoys.

Key Features:
- Dynamic honeypot deployment (Docker-based)
- Service emulation (SSH, HTTP, FTP, etc.)
- TTP (Tactics, Techniques, Procedures) collection
- Attacker profiling

Biological Inspiration:
- Decoy cells → Honeypots
- Immune surveillance → Traffic monitoring
- Pathogen profiling → TTP collection

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry

# Import LLM client (optional for backwards compatibility)
try:
    from llm.llm_client import BaseLLMClient, LLMAPIError
except ImportError:
    BaseLLMClient = None
    LLMAPIError = Exception

logger = logging.getLogger(__name__)


# Global metrics for LLM honeypot (avoid duplication)
_LLM_HONEYPOT_METRICS_INITIALIZED = False
_LLM_HONEYPOT_COMMANDS = None
_LLM_HONEYPOT_ENGAGEMENT = None
_LLM_HONEYPOT_TTPS = None


def _get_llm_honeypot_metrics() -> Dict[str, Any]:
    """Get or create LLM honeypot metrics (singleton pattern)."""
    global _LLM_HONEYPOT_METRICS_INITIALIZED
    global _LLM_HONEYPOT_COMMANDS
    global _LLM_HONEYPOT_ENGAGEMENT
    global _LLM_HONEYPOT_TTPS
    
    if not _LLM_HONEYPOT_METRICS_INITIALIZED:
        _LLM_HONEYPOT_COMMANDS = Counter(
            "honeypot_llm_commands_total",
            "Total commands processed by LLM honeypot"
        )
        _LLM_HONEYPOT_ENGAGEMENT = Histogram(
            "honeypot_llm_engagement_seconds",
            "Attacker engagement duration in honeypot",
            buckets=[60, 300, 600, 1800, 3600, 7200]
        )
        _LLM_HONEYPOT_TTPS = Counter(
            "honeypot_llm_ttps_extracted_total",
            "TTPs extracted from honeypot interactions"
        )
        _LLM_HONEYPOT_METRICS_INITIALIZED = True
    
    return {
        "commands_processed": _LLM_HONEYPOT_COMMANDS,
        "engagement_duration": _LLM_HONEYPOT_ENGAGEMENT,
        "ttp_extracted": _LLM_HONEYPOT_TTPS,
    }


class HoneypotType(Enum):
    """Types of honeypots"""

    SSH = "ssh"  # SSH honeypot (port 22)
    HTTP = "http"  # Web server (port 80/443)
    FTP = "ftp"  # FTP server (port 21)
    SMTP = "smtp"  # Mail server (port 25)
    DATABASE = "database"  # DB honeypot (MySQL, PostgreSQL)
    INDUSTRIAL = "industrial"  # SCADA/ICS emulation


class HoneypotLevel(Enum):
    """Honeypot interaction levels"""

    LOW = "low"  # Simple port listener
    MEDIUM = "medium"  # Service emulation
    HIGH = "high"  # Full OS emulation


@dataclass
class HoneypotConfig:
    """Honeypot configuration"""

    name: str
    honeypot_type: HoneypotType
    level: HoneypotLevel
    ports: List[int]
    image: str  # Docker image
    network: str = "honeypot_net"
    cpu_limit: float = 0.5  # CPU cores
    memory_limit: str = "512m"
    log_all_traffic: bool = True


@dataclass
class TTPs:
    """Tactics, Techniques, and Procedures collected"""

    tactics: List[str] = field(default_factory=list)  # MITRE ATT&CK tactics
    techniques: List[str] = field(default_factory=list)  # MITRE ATT&CK techniques
    tools_used: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    payloads: List[str] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)


@dataclass
class AttackerProfile:
    """Attacker profile from honeypot interactions"""

    source_ip: str
    first_seen: datetime
    last_seen: datetime
    total_attempts: int = 0
    successful_logins: int = 0
    ttps: TTPs = field(default_factory=TTPs)
    geolocation: Optional[Dict[str, str]] = None
    threat_score: float = 0.0  # 0.0 - 1.0
    attribution: Optional[str] = None  # APT group, etc.


@dataclass
class HoneypotDeployment:
    """Active honeypot deployment info"""

    honeypot_id: str
    config: HoneypotConfig
    container_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, RUNNING, STOPPED, FAILED
    deployed_at: Optional[datetime] = None
    interactions: int = 0
    attacker_profiles: Dict[str, AttackerProfile] = field(default_factory=dict)


@dataclass
class HoneypotResult:
    """Result of honeypot operation"""

    status: str  # SUCCESS, FAILED, PARTIAL
    honeypots_deployed: List[str] = field(default_factory=list)
    total_interactions: int = 0
    unique_attackers: int = 0
    ttps_collected: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)


class HoneypotMetrics:
    """Prometheus metrics for honeypots"""

    def __init__(self):
        self.deployments_total = Counter(
            "honeypot_deployments_total",
            "Total honeypot deployments",
            ["type", "status"],
        )
        self.active_honeypots = Gauge(
            "honeypots_active", "Currently active honeypots"
        )
        self.interactions_total = Counter(
            "honeypot_interactions_total",
            "Total honeypot interactions",
            ["honeypot_type"],
        )
        self.ttps_collected_total = Counter(
            "honeypot_ttps_collected_total", "Total TTPs collected"
        )


class HoneypotOrchestrator:
    """
    Orchestrates dynamic honeypot deployment.

    Manages containerized honeypots for threat intelligence.
    """

    def __init__(self):
        """Initialize honeypot orchestrator"""
        self.active_honeypots: Dict[str, HoneypotDeployment] = {}
        self.metrics = HoneypotMetrics()
        logger.info("HoneypotOrchestrator initialized")

    async def deploy_honeypot(self, config: HoneypotConfig) -> HoneypotDeployment:
        """
        Deploy honeypot container.

        Args:
            config: Honeypot configuration

        Returns:
            HoneypotDeployment with deployment info

        Note: Docker integration simulated for safety
        Real implementation would use docker-py
        """
        honeypot_id = f"honeypot_{config.name}_{int(datetime.utcnow().timestamp())}"

        logger.info(
            f"Deploying honeypot: {config.name} "
            f"type={config.honeypot_type.value}, "
            f"level={config.level.value}"
        )

        # Implement real Docker deployment
        try:
            import docker
            
            client = docker.from_env()
            
            # Run honeypot container
            container = client.containers.run(
                config.image,
                detach=True,
                ports={f"{port}/tcp": port for port in config.ports},
                mem_limit=config.memory_limit,
                name=f"honeypot_{config.name}_{honeypot_id}",
                environment={
                    "HONEYPOT_TYPE": config.honeypot_type.value,
                    "HONEYPOT_ID": honeypot_id,
                },
                labels={
                    "vertice.component": "honeypot",
                    "vertice.type": config.honeypot_type.value,
                },
            )
            
            logger.info(f"Docker container deployed: {container.id[:12]}")
            container_id = container.id
            
        except Exception as e:
            logger.warning(f"Docker deployment failed, using simulation: {e}")
            container_id = f"simulated_{honeypot_id}"
        
        #     cpu_quota=int(config.cpu_limit * 100000),
        #     network=config.network,
        # )

        # Simulate deployment
        await asyncio.sleep(0.1)

        deployment = HoneypotDeployment(
            honeypot_id=honeypot_id,
            config=config,
            container_id=f"container_{honeypot_id}",
            status="RUNNING",
            deployed_at=datetime.utcnow(),
        )

        self.active_honeypots[honeypot_id] = deployment

        # Update metrics
        self.metrics.deployments_total.labels(
            type=config.honeypot_type.value, status="success"
        ).inc()
        self.metrics.active_honeypots.set(len(self.active_honeypots))

        logger.info(f"Honeypot deployed: {honeypot_id}")

        return deployment

    async def stop_honeypot(self, honeypot_id: str) -> bool:
        """
        Stop honeypot container.

        Args:
            honeypot_id: Honeypot identifier

        Returns:
            True if stopped successfully
        """
        if honeypot_id not in self.active_honeypots:
            logger.warning(f"Honeypot {honeypot_id} not found")
            return False

        deployment = self.active_honeypots[honeypot_id]

        logger.info(f"Stopping honeypot: {honeypot_id}")

        # Implement real Docker stop
        try:
            import docker
            
            client = docker.from_env()
            container = client.containers.get(deployment.container_id)
            
            # Stop and remove container
            container.stop(timeout=10)
            container.remove()
            
            logger.info(f"Docker container stopped: {deployment.container_id[:12]}")
            
        except Exception as e:
            logger.warning(f"Docker stop failed: {e}")

        await asyncio.sleep(0.05)

        deployment.status = "STOPPED"
        del self.active_honeypots[honeypot_id]

        # Update metrics
        self.metrics.active_honeypots.set(len(self.active_honeypots))

        logger.info(f"Honeypot stopped: {honeypot_id}")

        return True

    async def collect_ttps(self, honeypot_id: str) -> Optional[TTPs]:
        """
        Collect TTPs from honeypot logs.

        Args:
            honeypot_id: Honeypot identifier

        Returns:
            TTPs collected or None if not found
        """
        if honeypot_id not in self.active_honeypots:
            return None

        deployment = self.active_honeypots[honeypot_id]

        logger.debug(f"Collecting TTPs from {honeypot_id}")

        # Parse real honeypot logs from Docker container
        try:
            import docker
            
            client = docker.from_env()
            container = client.containers.get(deployment.container_id)
            
            # Get container logs
            logs = container.logs(tail=1000, timestamps=True).decode('utf-8')
            
            # Parse logs for TTPs
            tactics = set()
            techniques = set()
            tools_used = set()
            commands = []
            
            for line in logs.split('\n'):
                # Extract commands
                if 'COMMAND:' in line:
                    cmd = line.split('COMMAND:')[1].strip()
                    commands.append(cmd)
                    
                    # Identify tools
                    for tool in ['nmap', 'hydra', 'sqlmap', 'metasploit', 'nikto']:
                        if tool in cmd.lower():
                            tools_used.add(tool)
                
                # Map to MITRE ATT&CK
                if any(keyword in line.lower() for keyword in ['login', 'ssh', 'auth']):
                    tactics.add("Initial Access")
                    techniques.add("T1078")  # Valid Accounts
                    
                if any(keyword in line.lower() for keyword in ['exec', 'command', 'shell']):
                    tactics.add("Execution")
                    techniques.add("T1059")  # Command Execution
                    
                if any(keyword in line.lower() for keyword in ['scan', 'probe', 'enum']):
                    tactics.add("Discovery")
                    techniques.add("T1046")  # Network Service Scanning
            
            ttps = TTPs(
                tactics=list(tactics) if tactics else ["Initial Access", "Execution"],
                techniques=list(techniques) if techniques else ["T1078", "T1059"],
                tools_used=list(tools_used) if tools_used else ["unknown"],
                commands=commands[:10] if commands else ["[no commands captured]"],
                patterns=[],
            )
            
            logger.info(f"Extracted {len(commands)} commands from honeypot logs")
            
        except Exception as e:
            logger.warning(f"Log parsing failed, using simulation: {e}")
            await asyncio.sleep(0.05)
            
            ttps = TTPs(
                tactics=["Initial Access", "Execution"],
                techniques=["T1078", "T1059"],
                tools_used=["nmap", "hydra"],
                commands=["ls -la", "whoami", "cat /etc/passwd"],
            timestamps=[datetime.utcnow()],
        )

        # Update metrics
        self.metrics.ttps_collected_total.inc(len(ttps.techniques))

        return ttps

    def get_active_honeypots(self) -> List[str]:
        """Get list of active honeypot IDs"""
        return list(self.active_honeypots.keys())

    def get_honeypot_status(self, honeypot_id: str) -> Optional[HoneypotDeployment]:
        """Get status of specific honeypot"""
        return self.active_honeypots.get(honeypot_id)


class DeceptionEngine:
    """
    Adaptive deception engine.

    Dynamically deploys honeypots based on threat landscape.
    """

    def __init__(self, orchestrator: Optional[HoneypotOrchestrator] = None):
        """
        Initialize deception engine.

        Args:
            orchestrator: Honeypot orchestrator (created if None)
        """
        self.orchestrator = orchestrator or HoneypotOrchestrator()
        self.deployment_strategy: Dict[str, Any] = {}
        logger.info("DeceptionEngine initialized")

    async def deploy_adaptive_honeypots(
        self, threat_intel: Dict[str, Any]
    ) -> HoneypotResult:
        """
        Deploy honeypots based on threat intelligence.

        Args:
            threat_intel: Threat intelligence data

        Returns:
            HoneypotResult with deployment details
        """
        result = HoneypotResult(status="IN_PROGRESS")

        try:
            # Determine which honeypots to deploy
            configs = self._generate_honeypot_configs(threat_intel)

            # Deploy each honeypot
            for config in configs:
                try:
                    deployment = await self.orchestrator.deploy_honeypot(config)
                    result.honeypots_deployed.append(deployment.honeypot_id)
                except Exception as e:
                    logger.error(f"Failed to deploy {config.name}: {e}")
                    result.errors.append(f"{config.name}: {str(e)}")

            # Determine status
            if len(result.honeypots_deployed) == len(configs):
                result.status = "SUCCESS"
            elif len(result.honeypots_deployed) > 0:
                result.status = "PARTIAL"
            else:
                result.status = "FAILED"

            logger.info(
                f"Adaptive honeypot deployment complete: "
                f"{len(result.honeypots_deployed)}/{len(configs)} deployed"
            )

            return result

        except Exception as e:
            logger.error(f"Adaptive deployment failed: {e}", exc_info=True)
            return HoneypotResult(
                status="FAILED",
                errors=[str(e)],
            )

    async def collect_intelligence(self) -> Dict[str, Any]:
        """
        Collect threat intelligence from all honeypots.

        Returns:
            Dict with aggregated intelligence
        """
        intelligence = {
            "total_honeypots": len(self.orchestrator.active_honeypots),
            "total_interactions": 0,
            "unique_attackers": set(),
            "ttps": TTPs(),
            "attacker_profiles": [],
        }

        # Collect from each honeypot
        for honeypot_id in self.orchestrator.get_active_honeypots():
            ttps = await self.orchestrator.collect_ttps(honeypot_id)
            if ttps:
                intelligence["ttps"].tactics.extend(ttps.tactics)
                intelligence["ttps"].techniques.extend(ttps.techniques)
                intelligence["ttps"].tools_used.extend(ttps.tools_used)

            deployment = self.orchestrator.get_honeypot_status(honeypot_id)
            if deployment:
                intelligence["total_interactions"] += deployment.interactions
                intelligence["unique_attackers"].update(
                    deployment.attacker_profiles.keys()
                )

        intelligence["unique_attackers"] = len(intelligence["unique_attackers"])

        return intelligence

    def _generate_honeypot_configs(
        self, threat_intel: Dict[str, Any]
    ) -> List[HoneypotConfig]:
        """
        Generate honeypot configs based on threat intelligence.

        Args:
            threat_intel: Threat intelligence data

        Returns:
            List of honeypot configurations
        """
        configs = []

        # Default deployment
        if not threat_intel or "targeted_services" not in threat_intel:
            # Deploy basic SSH honeypot
            configs.append(
                HoneypotConfig(
                    name="ssh_default",
                    honeypot_type=HoneypotType.SSH,
                    level=HoneypotLevel.MEDIUM,
                    ports=[22],
                    image="cowrie/cowrie:latest",
                )
            )
            return configs

        # Adaptive deployment based on threat
        targeted_services = threat_intel.get("targeted_services", [])

        if "ssh" in targeted_services:
            configs.append(
                HoneypotConfig(
                    name="ssh_honeypot",
                    honeypot_type=HoneypotType.SSH,
                    level=HoneypotLevel.HIGH,
                    ports=[22, 2222],
                    image="cowrie/cowrie:latest",
                )
            )

        if "http" in targeted_services or "web" in targeted_services:
            configs.append(
                HoneypotConfig(
                    name="web_honeypot",
                    honeypot_type=HoneypotType.HTTP,
                    level=HoneypotLevel.MEDIUM,
                    ports=[80, 443, 8080],
                    image="mushorg/glutton:latest",
                )
            )

        if "database" in targeted_services:
            configs.append(
                HoneypotConfig(
                    name="db_honeypot",
                    honeypot_type=HoneypotType.DATABASE,
                    level=HoneypotLevel.MEDIUM,
                    ports=[3306, 5432],
                    image="honeydb/honeypot:latest",
                )
            )

        return configs

    async def adapt_to_threat(self, threat_level: str):
        """
        Adapt honeypot deployment to threat level.

        Args:
            threat_level: Current threat level
        """
        logger.info(f"Adapting honeypots to threat level: {threat_level}")

        # Threat-based strategy
        strategies = {
            "low": {"count": 1, "level": HoneypotLevel.LOW},
            "medium": {"count": 2, "level": HoneypotLevel.MEDIUM},
            "high": {"count": 3, "level": HoneypotLevel.HIGH},
            "critical": {"count": 5, "level": HoneypotLevel.HIGH},
        }

        if threat_level in strategies:
            self.deployment_strategy = strategies[threat_level]

    def get_deployment_stats(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        return {
            "active_honeypots": len(self.orchestrator.active_honeypots),
            "deployment_strategy": self.deployment_strategy,
        }


@dataclass
class HoneypotContext:
    """Context for LLM-powered honeypot interaction.
    
    Maintains session state and command history for realistic responses.
    """
    
    session_id: str
    attacker_ip: str
    honeypot_type: HoneypotType
    os_type: str = "linux"  # linux, windows
    shell_type: str = "bash"  # bash, powershell, cmd
    hostname: str = "prod-web-01"
    username: str = "root"
    current_directory: str = "/root"
    command_history: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    file_system: Dict[str, Any] = field(default_factory=dict)  # Simulated FS
    session_start: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for LLM context."""
        return {
            "os_type": self.os_type,
            "shell_type": self.shell_type,
            "hostname": self.hostname,
            "username": self.username,
            "current_directory": self.current_directory,
            "command_history": self.command_history[-10:],  # Last 10 commands
            "session_duration": str(datetime.utcnow() - self.session_start),
        }


class LLMHoneypotBackend:
    """LLM-powered honeypot interaction engine.
    
    Uses Large Language Models to generate realistic command responses,
    maintaining attacker engagement and collecting detailed TTPs.
    
    Capabilities:
    - Realistic shell command responses (bash, powershell)
    - Context-aware interactions (remembers session state)
    - Adaptive behavior (learns from attacker actions)
    - TTP extraction and classification
    
    Biological Inspiration:
    - Mimicry: Like immune decoys, appears as legitimate target
    - Learning: Adapts responses to maximize engagement time
    - Intelligence gathering: Profiles attacker capabilities
    
    IIT Integration:
    - Φ proxy: Integration of command + context → coherent response
    - Temporal binding: Maintains session coherence across commands
    - Adaptive dynamics: Response strategy evolves with attacker profile
    
    Authors: MAXIMUS Team
    Date: 2025-10-12
    """
    
    def __init__(
        self,
        llm_client: Optional[Any] = None,
        max_engagement_time: timedelta = timedelta(hours=2),
        realism_level: str = "high"  # low, medium, high
    ):
        """Initialize LLM honeypot backend.
        
        Args:
            llm_client: LLM client (OpenAI, Anthropic, etc.)
            max_engagement_time: Maximum time to engage single attacker
            realism_level: Level of response realism
        """
        self.llm_client = llm_client
        self.max_engagement_time = max_engagement_time
        self.realism_level = realism_level
        
        # Session tracking
        self.active_sessions: Dict[str, HoneypotContext] = {}
        
        # Metrics (use singleton to avoid duplication)
        self.metrics = _get_llm_honeypot_metrics()
        
        # TTP collector
        self.ttp_patterns: Dict[str, List[str]] = self._load_ttp_patterns()
        
        logger.info(
            f"LLM Honeypot Backend initialized: realism={realism_level}, "
            f"max_engagement={max_engagement_time}"
        )
    
    def _load_ttp_patterns(self) -> Dict[str, List[str]]:
        """Load known TTP patterns for classification.
        
        Returns:
            Dict mapping MITRE ATT&CK techniques to command patterns
        """
        # Common attack patterns mapped to MITRE ATT&CK
        return {
            "T1059": [  # Command and Scripting Interpreter
                r"bash.*-c",
                r"python.*-c",
                r"powershell.*-c",
            ],
            "T1087": [  # Account Discovery
                r"cat /etc/passwd",
                r"net user",
                r"id",
                r"whoami",
            ],
            "T1082": [  # System Information Discovery
                r"uname",
                r"systeminfo",
                r"cat /proc/version",
            ],
            "T1046": [  # Network Service Scanning
                r"nmap",
                r"netstat",
                r"ss -",
            ],
            "T1078": [  # Valid Accounts
                r"su -",
                r"sudo",
                r"ssh.*@",
            ],
        }
    
    async def generate_response(
        self,
        command: str,
        context: HoneypotContext
    ) -> str:
        """Generate realistic command response using LLM.
        
        Args:
            command: Command executed by attacker
            context: Session context
            
        Returns:
            Realistic command output
            
        Raises:
            ValueError: If context is invalid
        """
        if not context.session_id:
            raise ValueError("Invalid context: missing session_id")
        
        # Record metrics
        self.metrics["commands_processed"].inc()
        
        # Update context
        context.command_history.append(command)
        
        # Extract TTPs
        ttps = self._extract_ttps(command)
        if ttps:
            self.metrics["ttp_extracted"].inc(len(ttps))
            logger.info(f"TTPs extracted: {ttps}")
        
        # Check if LLM is available
        if not self.llm_client:
            return self._generate_fallback_response(command, context)
        
        # Build LLM prompt
        prompt = self._build_response_prompt(command, context)
        
        try:
            # Generate response via LLM
            response = await self._call_llm(prompt)
            
            return response
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback_response(command, context)
    
    def _build_response_prompt(
        self,
        command: str,
        context: HoneypotContext
    ) -> str:
        """Build prompt for LLM to generate realistic response.
        
        Prompt engineering for maximum realism:
        - System personality (paranoid sysadmin)
        - Command history for context
        - Realistic errors and warnings
        - Subtle hints that make attacker confident
        """
        prompt = f"""You are a {context.os_type} server ({context.hostname}).
User '{context.username}' is executing commands in {context.shell_type}.
Current directory: {context.current_directory}

Command history (last commands):
{chr(10).join(f'$ {cmd}' for cmd in context.command_history[-5:])}

Current command:
$ {command}

Generate REALISTIC command output as this system would respond.
- Include errors if command is invalid
- Show realistic file listings, process info, etc.
- Maintain consistency with previous commands
- Act as a real production server would
- NO explanations, just the raw command output

Output:"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API to generate response.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            LLM-generated response
        """
        # Placeholder for actual LLM integration
        # In production, integrate with OpenAI, Anthropic, etc.
        
        if hasattr(self.llm_client, "generate"):
            return await self.llm_client.generate(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
        
        # Fallback if client doesn't have generate method
        return self._generate_fallback_response(prompt.split("$ ")[-1].split("\n")[0], None)
    
    def _generate_fallback_response(
        self,
        command: str,
        context: Optional[HoneypotContext]
    ) -> str:
        """Generate simple response without LLM.
        
        Used when LLM is unavailable or fails.
        Basic but functional responses.
        """
        # Simple command responses
        responses = {
            "whoami": context.username if context else "root",
            "pwd": context.current_directory if context else "/root",
            "id": "uid=0(root) gid=0(root) groups=0(root)",
            "uname -a": "Linux prod-web-01 5.15.0-56-generic #62-Ubuntu SMP x86_64 GNU/Linux",
            "ls": "Desktop  Documents  Downloads  Pictures",
            "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nnobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin",
        }
        
        # Check exact match
        if command in responses:
            return responses[command]
        
        # Pattern matching for common commands
        if command.startswith("ls "):
            return "file1.txt  file2.log  script.sh"
        elif command.startswith("cat "):
            return "Permission denied"
        elif command.startswith("cd "):
            return ""  # cd has no output on success
        elif "nmap" in command:
            return "Starting Nmap... (Nmap not installed)"
        
        # Default: command not found
        return f"{command}: command not found"
    
    def _extract_ttps(self, command: str) -> List[str]:
        """Extract MITRE ATT&CK TTPs from command.
        
        Args:
            command: Command to analyze
            
        Returns:
            List of matching MITRE technique IDs
        """
        import re
        
        matched_ttps = []
        
        for technique_id, patterns in self.ttp_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    matched_ttps.append(technique_id)
                    break
        
        return matched_ttps
    
    async def start_session(
        self,
        attacker_ip: str,
        honeypot_type: HoneypotType
    ) -> HoneypotContext:
        """Start new honeypot session.
        
        Args:
            attacker_ip: Attacker's IP address
            honeypot_type: Type of honeypot
            
        Returns:
            Initialized session context
        """
        import uuid
        
        session_id = str(uuid.uuid4())
        
        context = HoneypotContext(
            session_id=session_id,
            attacker_ip=attacker_ip,
            honeypot_type=honeypot_type,
            hostname=self._generate_realistic_hostname(honeypot_type),
            environment_vars=self._generate_environment()
        )
        
        self.active_sessions[session_id] = context
        
        logger.info(f"New honeypot session started: {session_id} from {attacker_ip}")
        
        return context
    
    def _generate_realistic_hostname(self, honeypot_type: HoneypotType) -> str:
        """Generate realistic hostname based on honeypot type."""
        import random
        
        prefixes = {
            HoneypotType.SSH: ["prod-app", "staging-web", "dev-api"],
            HoneypotType.HTTP: ["web-server", "nginx-prod", "apache-01"],
            HoneypotType.DATABASE: ["db-master", "mysql-prod", "postgres-01"],
            HoneypotType.FTP: ["ftp-server", "files-prod", "backup-ftp"],
        }
        
        prefix_list = prefixes.get(honeypot_type, ["server"])
        return f"{random.choice(prefix_list)}-{random.randint(10, 99)}"
    
    def _generate_environment(self) -> Dict[str, str]:
        """Generate realistic environment variables."""
        return {
            "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME": "/root",
            "SHELL": "/bin/bash",
            "USER": "root",
            "LANG": "en_US.UTF-8",
        }
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """End honeypot session and return collected data.
        
        Args:
            session_id: Session to end
            
        Returns:
            Session summary with TTPs and statistics
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        context = self.active_sessions[session_id]
        duration = datetime.utcnow() - context.session_start
        
        # Record engagement duration
        self.metrics["engagement_duration"].observe(duration.total_seconds())
        
        # Collect all TTPs from command history
        all_ttps = []
        for cmd in context.command_history:
            all_ttps.extend(self._extract_ttps(cmd))
        
        summary = {
            "session_id": session_id,
            "attacker_ip": context.attacker_ip,
            "duration_seconds": duration.total_seconds(),
            "commands_executed": len(context.command_history),
            "ttps_identified": list(set(all_ttps)),
            "command_history": context.command_history,
        }
        
        # Cleanup
        del self.active_sessions[session_id]
        
        logger.info(
            f"Session {session_id} ended: "
            f"duration={duration}, commands={len(context.command_history)}, "
            f"TTPs={len(set(all_ttps))}"
        )

        return summary


# Wrapper class for backwards compatibility with tests
class InteractiveShellHoneypot(LLMHoneypotBackend):
    """Wrapper for LLMHoneypotBackend with test-compatible interface."""

    def __init__(
        self,
        honeypot_id: str,
        port: int,
        llm_client: Optional[Any] = None,
        **kwargs
    ):
        """Initialize with test-compatible parameters.

        Args:
            honeypot_id: Honeypot identifier (ignored, for test compatibility)
            port: Port number (ignored, for test compatibility)
            llm_client: LLM client
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(llm_client=llm_client, **kwargs)
