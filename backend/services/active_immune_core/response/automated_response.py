"""Automated Response Engine - Defensive Playbook Execution

Executes defensive playbooks with HOTL (Human-on-the-Loop) checkpoints.
Provides automated response to detected threats while maintaining human oversight.

Biological Inspiration:
- Immune response cascade: Sequential activation of defense mechanisms
- Checkpoints: Regulatory T cells prevent overreaction
- Proportional response: Match response intensity to threat severity

IIT Integration:
- Integrated decision-making across detection → response pipeline
- Φ maximization through coordinated multi-component response
- Temporal coherence ensures sequential action dependencies

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of response actions."""

    BLOCK_IP = "block_ip"  # Block IP at firewall
    BLOCK_DOMAIN = "block_domain"  # Block domain in DNS
    ISOLATE_HOST = "isolate_host"  # Network isolation
    KILL_PROCESS = "kill_process"  # Terminate process
    DEPLOY_HONEYPOT = "deploy_honeypot"  # Deploy decoy
    RATE_LIMIT = "rate_limit"  # Traffic rate limiting
    ALERT_SOC = "alert_soc"  # Human notification
    COLLECT_FORENSICS = "collect_forensics"  # Evidence collection
    TRIGGER_CASCADE = "trigger_cascade"  # Activate coagulation cascade
    EXECUTE_SCRIPT = "execute_script"  # Custom script execution


class ActionStatus(Enum):
    """Action execution status."""

    PENDING = "pending"  # Waiting to execute
    HOTL_REQUIRED = "hotl_required"  # Awaiting human approval
    APPROVED = "approved"  # Human approved
    DENIED = "denied"  # Human denied
    EXECUTING = "executing"  # Currently running
    SUCCESS = "success"  # Completed successfully
    FAILED = "failed"  # Execution failed
    ROLLED_BACK = "rolled_back"  # Action was reverted


@dataclass
class PlaybookAction:
    """Single action within a playbook.

    Represents atomic defensive action that can be executed.

    Attributes:
        action_id: Unique action identifier
        action_type: Type of action to execute
        parameters: Action-specific parameters
        hotl_required: Whether human approval is needed
        timeout_seconds: Max execution time
        retry_attempts: Number of retry attempts on failure
        rollback_action: Optional action to undo this one
        dependencies: Action IDs that must complete first
    """

    action_id: str
    action_type: ActionType
    parameters: Dict[str, Any]
    hotl_required: bool = False
    timeout_seconds: int = 30
    retry_attempts: int = 3
    rollback_action: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Playbook:
    """Defensive playbook containing sequence of actions.

    YAML Structure:
    ```yaml
    name: "Brute Force Response"
    description: "..."
    trigger:
      condition: "brute_force_detected"
      severity: "HIGH"
    actions:
      - id: "action_1"
        type: "block_ip"
        hotl_required: false
        parameters:
          source_ip: "{{event.source_ip}}"
      - id: "action_2"
        type: "deploy_honeypot"
        hotl_required: true
        dependencies: ["action_1"]
        parameters:
          honeypot_type: "ssh"
    ```

    Attributes:
        playbook_id: Unique playbook identifier
        name: Human-readable name
        description: Playbook purpose
        trigger_condition: Condition that activates playbook
        severity: Minimum severity to trigger
        actions: List of actions to execute
        max_parallel: Max concurrent actions (0 = sequential)
        rollback_on_failure: Whether to rollback on any failure
    """

    playbook_id: str
    name: str
    description: str
    trigger_condition: str
    severity: str
    actions: List[PlaybookAction]
    max_parallel: int = 0  # 0 = sequential
    rollback_on_failure: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatContext:
    """Context for threat being responded to.

    Attributes:
        threat_id: Unique threat identifier
        event_id: Original security event ID
        detection_result: Detection data from Sentinel
        severity: Threat severity
        source_ip: Attack source IP
        target_ip: Target IP
        mitre_techniques: MITRE ATT&CK techniques
        timestamp: Detection timestamp
        additional_context: Extra contextual data
    """

    threat_id: str
    event_id: str
    detection_result: Dict[str, Any]
    severity: str
    source_ip: str
    target_ip: Optional[str] = None
    mitre_techniques: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlaybookResult:
    """Result of playbook execution.

    Attributes:
        playbook_id: Executed playbook ID
        threat_context: Threat that triggered playbook
        status: Overall execution status
        actions_executed: Number of actions completed
        actions_failed: Number of actions that failed
        actions_pending_hotl: Number awaiting approval
        execution_time_seconds: Total execution time
        action_results: Individual action results
        errors: List of errors encountered
        started_at: Execution start time
        completed_at: Execution end time
    """

    playbook_id: str
    threat_context: ThreatContext
    status: str  # SUCCESS, PARTIAL, FAILED, HOTL_PENDING
    actions_executed: int
    actions_failed: int
    actions_pending_hotl: int
    execution_time_seconds: float
    action_results: List[Dict[str, Any]]
    errors: List[str]
    started_at: datetime
    completed_at: datetime


class ResponseError(Exception):
    """Raised when response execution fails."""

    pass


class AutomatedResponseEngine:
    """Automated defensive response engine with HOTL checkpoints.

    Core component for executing defensive playbooks. Manages action
    execution, dependencies, human approval gates, and rollback.

    Capabilities:
    1. Load and parse YAML playbooks
    2. Execute actions with dependency management
    3. HOTL checkpoint enforcement
    4. Automatic retry on transient failures
    5. Rollback on critical failures
    6. Audit logging of all actions

    Biological Analogy:
    - Sequential cascade like coagulation
    - Regulatory checkpoints like Tregs
    - Proportional response intensity
    - Self-limiting (rollback on overreaction)

    Example:
        >>> engine = AutomatedResponseEngine(
        ...     playbook_dir="./playbooks",
        ...     hotl_gateway=hotl_client
        ... )
        >>> playbook = await engine.load_playbook("brute_force_response.yaml")
        >>> context = ThreatContext(
        ...     threat_id="threat_001",
        ...     event_id="evt_001",
        ...     detection_result={...},
        ...     severity="HIGH",
        ...     source_ip="192.168.1.100"
        ... )
        >>> result = await engine.execute_playbook(playbook, context)
        >>> print(f"Actions executed: {result.actions_executed}")
    """

    def __init__(
        self,
        playbook_dir: str,
        hotl_gateway: Optional[Any] = None,
        executor_pool: Optional[Any] = None,
        audit_log_path: Optional[str] = None,
        dry_run: bool = False,
        registry: Optional[Any] = None,
    ):
        """Initialize response engine.

        Args:
            playbook_dir: Directory containing YAML playbooks
            hotl_gateway: Gateway for human approval requests
            executor_pool: Executor pool for action execution
            audit_log_path: Path to audit log file
            dry_run: If True, simulate without executing
            registry: Prometheus registry (optional, for testing)

        Raises:
            ValueError: If playbook_dir doesn't exist
        """
        self.playbook_dir = Path(playbook_dir)
        if not self.playbook_dir.exists():
            raise ValueError(f"Playbook directory not found: {playbook_dir}")

        self.hotl = hotl_gateway
        self.executor = executor_pool
        self.audit_path = audit_log_path
        self.dry_run = dry_run

        # In-memory playbook cache
        self.playbooks: Dict[str, Playbook] = {}

        # HOTL pending approvals
        self.pending_approvals: Dict[str, PlaybookAction] = {}

        # Metrics - use provided registry or default
        if registry is None:
            from prometheus_client import REGISTRY as prom_registry
            registry = prom_registry

        try:
            self.playbooks_executed = Counter(
                "response_playbooks_executed_total",
                "Total playbooks executed",
                ["playbook_id", "status"],
                registry=registry,
            )
            self.actions_executed = Counter(
                "response_actions_executed_total",
                "Total actions executed",
                ["action_type", "status"],
                registry=registry,
            )
            self.hotl_requests = Counter(
                "response_hotl_requests_total",
                "HOTL approval requests",
                ["action_type", "approved"],
                registry=registry,
            )
            self.execution_time = Histogram(
                "response_execution_seconds",
                "Playbook execution time",
                registry=registry,
            )
        except ValueError:
            # Metrics already registered, get existing ones
            logger.warning("Metrics already registered, reusing existing")
            self.playbooks_executed = None
            self.actions_executed = None
            self.hotl_requests = None
            self.execution_time = None

        logger.info(
            f"Response engine initialized: playbook_dir={playbook_dir}, "
            f"dry_run={dry_run}"
        )

    async def load_playbook(self, filename: str) -> Playbook:
        """Load playbook from YAML file.

        Args:
            filename: Playbook filename (relative to playbook_dir)

        Returns:
            Parsed Playbook object

        Raises:
            ResponseError: If playbook file invalid
        """
        playbook_path = self.playbook_dir / filename

        if not playbook_path.exists():
            raise ResponseError(f"Playbook not found: {filename}")

        try:
            with open(playbook_path, "r") as f:
                data = yaml.safe_load(f)

            # Parse actions
            actions = []
            for action_data in data.get("actions", []):
                action = PlaybookAction(
                    action_id=action_data["id"],
                    action_type=ActionType(action_data["type"]),
                    parameters=action_data.get("parameters", {}),
                    hotl_required=action_data.get("hotl_required", False),
                    timeout_seconds=action_data.get("timeout_seconds", 30),
                    retry_attempts=action_data.get("retry_attempts", 3),
                    rollback_action=action_data.get("rollback_action"),
                    dependencies=action_data.get("dependencies", []),
                )
                actions.append(action)

            # Build playbook
            playbook = Playbook(
                playbook_id=data.get("id", filename.replace(".yaml", "")),
                name=data["name"],
                description=data.get("description", ""),
                trigger_condition=data["trigger"]["condition"],
                severity=data["trigger"].get("severity", "MEDIUM"),
                actions=actions,
                max_parallel=data.get("max_parallel", 0),
                rollback_on_failure=data.get("rollback_on_failure", True),
                metadata=data.get("metadata", {}),
            )

            # Cache playbook
            self.playbooks[playbook.playbook_id] = playbook

            logger.info(
                f"Playbook loaded: {playbook.name} "
                f"({len(playbook.actions)} actions)"
            )

            return playbook

        except (yaml.YAMLError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse playbook {filename}: {e}")
            raise ResponseError(f"Invalid playbook format: {str(e)}") from e

    async def execute_playbook(
        self, playbook: Playbook, context: ThreatContext
    ) -> PlaybookResult:
        """Execute defensive playbook.

        Main execution method. Runs playbook actions with dependency
        management, HOTL checkpoints, and rollback on failure.

        Process:
        1. Substitute context variables in action parameters
        2. Build dependency graph
        3. Execute actions respecting dependencies
        4. Handle HOTL approvals
        5. Retry on transient failures
        6. Rollback if critical failure
        7. Generate result report

        Args:
            playbook: Playbook to execute
            context: Threat context

        Returns:
            PlaybookResult with execution details

        Raises:
            ResponseError: If execution fails critically
        """
        start_time = datetime.utcnow()
        logger.info(
            f"Executing playbook: {playbook.name} for threat {context.threat_id}"
        )

        # Audit log
        await self._audit_log(
            "playbook_started",
            {
                "playbook_id": playbook.playbook_id,
                "threat_id": context.threat_id,
                "severity": context.severity,
            },
        )

        executed = 0
        failed = 0
        pending_hotl = 0
        action_results = []
        errors = []

        try:
            # Substitute context variables
            actions = await self._substitute_variables(playbook.actions, context)

            # Execute actions
            if playbook.max_parallel == 0:
                # Sequential execution
                for action in actions:
                    result = await self._execute_action(action, context)
                    action_results.append(result)

                    if result["status"] == ActionStatus.SUCCESS.value:
                        executed += 1
                    elif result["status"] == ActionStatus.HOTL_REQUIRED.value:
                        pending_hotl += 1
                    elif result["status"] == ActionStatus.FAILED.value:
                        failed += 1
                        errors.append(result.get("error", "Unknown error"))

                        # Rollback on failure if configured
                        if playbook.rollback_on_failure:
                            logger.warning(
                                f"Action {action.action_id} failed, "
                                "initiating rollback"
                            )
                            await self._rollback_actions(action_results, context)
                            break
            else:
                # Parallel execution (TODO: implement with asyncio.gather)
                pass

            # Calculate status
            if failed > 0 and executed == 0:
                status = "FAILED"
            elif pending_hotl > 0:
                status = "HOTL_PENDING"
            elif failed > 0:
                status = "PARTIAL"
            else:
                status = "SUCCESS"

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            result = PlaybookResult(
                playbook_id=playbook.playbook_id,
                threat_context=context,
                status=status,
                actions_executed=executed,
                actions_failed=failed,
                actions_pending_hotl=pending_hotl,
                execution_time_seconds=execution_time,
                action_results=action_results,
                errors=errors,
                started_at=start_time,
                completed_at=end_time,
            )

            # Record metrics
            if self.playbooks_executed:
                self.playbooks_executed.labels(
                    playbook_id=playbook.playbook_id, status=status
                ).inc()
            if self.execution_time:
                self.execution_time.observe(execution_time)

            # Audit log
            await self._audit_log(
                "playbook_completed",
                {
                    "playbook_id": playbook.playbook_id,
                    "threat_id": context.threat_id,
                    "status": status,
                    "actions_executed": executed,
                    "execution_time": execution_time,
                },
            )

            logger.info(
                f"Playbook {playbook.name} completed: status={status}, "
                f"executed={executed}, failed={failed}, time={execution_time:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Playbook execution failed: {e}", exc_info=True)
            raise ResponseError(f"Playbook execution failed: {str(e)}") from e

    async def request_hotl_approval(
        self, action: PlaybookAction, context: ThreatContext, timeout_seconds: int = 300
    ) -> bool:
        """Request human approval for action.

        Sends approval request to HOTL gateway and waits for response.
        Times out if no response within timeout_seconds.

        Args:
            action: Action requiring approval
            context: Threat context
            timeout_seconds: Max wait time for approval

        Returns:
            True if approved, False if denied/timeout

        Raises:
            ResponseError: If HOTL gateway unavailable
        """
        if not self.hotl:
            logger.warning(
                f"HOTL gateway not configured, auto-denying action {action.action_id}"
            )
            return False

        logger.info(f"Requesting HOTL approval for action {action.action_id}")

        try:
            # Build approval request
            request = {
                "action_id": action.action_id,
                "action_type": action.action_type.value,
                "parameters": action.parameters,
                "threat_context": {
                    "threat_id": context.threat_id,
                    "severity": context.severity,
                    "source_ip": context.source_ip,
                    "mitre_techniques": context.mitre_techniques,
                },
                "timeout": timeout_seconds,
            }

            # Store pending approval
            self.pending_approvals[action.action_id] = action

            # Send to HOTL gateway
            approved = await asyncio.wait_for(
                self.hotl.request_approval(request), timeout=timeout_seconds
            )

            # Remove from pending
            del self.pending_approvals[action.action_id]

            # Record metrics
            self.hotl_requests.labels(
                action_type=action.action_type.value, approved=str(approved)
            ).inc()

            # Audit log
            await self._audit_log(
                "hotl_decision",
                {
                    "action_id": action.action_id,
                    "approved": approved,
                    "threat_id": context.threat_id,
                },
            )

            logger.info(
                f"HOTL decision for {action.action_id}: "
                f"{'APPROVED' if approved else 'DENIED'}"
            )

            return approved

        except asyncio.TimeoutError:
            logger.warning(
                f"HOTL approval timeout for {action.action_id} "
                f"after {timeout_seconds}s"
            )
            return False
        except Exception as e:
            logger.error(f"HOTL approval request failed: {e}")
            raise ResponseError(f"HOTL request failed: {str(e)}") from e

    # Private methods

    async def _execute_action(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Execute single action with retry logic."""
        logger.info(f"Executing action {action.action_id}: {action.action_type.value}")

        action.status = ActionStatus.EXECUTING
        attempts = 0

        while attempts < action.retry_attempts:
            attempts += 1

            try:
                # Check HOTL if required
                if action.hotl_required:
                    action.status = ActionStatus.HOTL_REQUIRED
                    approved = await self.request_hotl_approval(action, context)

                    if not approved:
                        action.status = ActionStatus.DENIED
                        return {
                            "action_id": action.action_id,
                            "status": ActionStatus.DENIED.value,
                            "error": "HOTL denied",
                        }

                    action.status = ActionStatus.APPROVED

                # Execute action (dry run mode check)
                if self.dry_run:
                    logger.info(f"[DRY RUN] Would execute: {action.action_type.value}")
                    result = {"status": "simulated", "dry_run": True}
                else:
                    result = await self._execute_action_type(action, context)

                # Success
                action.status = ActionStatus.SUCCESS
                action.result = result
                action.executed_at = datetime.utcnow()

                self.actions_executed.labels(
                    action_type=action.action_type.value, status="success"
                ).inc()

                # Audit log
                await self._audit_log(
                    "action_executed",
                    {
                        "action_id": action.action_id,
                        "action_type": action.action_type.value,
                        "threat_id": context.threat_id,
                        "attempts": attempts,
                    },
                )

                return {
                    "action_id": action.action_id,
                    "status": ActionStatus.SUCCESS.value,
                    "result": result,
                    "attempts": attempts,
                }

            except Exception as e:
                logger.warning(
                    f"Action {action.action_id} attempt {attempts} failed: {e}"
                )

                if attempts >= action.retry_attempts:
                    # Final failure
                    action.status = ActionStatus.FAILED
                    action.error_message = str(e)

                    self.actions_executed.labels(
                        action_type=action.action_type.value, status="failed"
                    ).inc()

                    return {
                        "action_id": action.action_id,
                        "status": ActionStatus.FAILED.value,
                        "error": str(e),
                        "attempts": attempts,
                    }

                # Retry with exponential backoff
                await asyncio.sleep(2**attempts)

        # Should not reach here
        return {
            "action_id": action.action_id,
            "status": ActionStatus.FAILED.value,
            "error": "Max retries exceeded",
        }

    async def _execute_action_type(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Execute specific action type.

        Dispatches to appropriate handler based on action_type.
        """
        handlers = {
            ActionType.BLOCK_IP: self._handle_block_ip,
            ActionType.BLOCK_DOMAIN: self._handle_block_domain,
            ActionType.ISOLATE_HOST: self._handle_isolate_host,
            ActionType.DEPLOY_HONEYPOT: self._handle_deploy_honeypot,
            ActionType.RATE_LIMIT: self._handle_rate_limit,
            ActionType.ALERT_SOC: self._handle_alert_soc,
            ActionType.TRIGGER_CASCADE: self._handle_trigger_cascade,
            ActionType.COLLECT_FORENSICS: self._handle_collect_forensics,
        }

        handler = handlers.get(action.action_type)
        if not handler:
            raise ResponseError(f"No handler for action type: {action.action_type}")

        return await handler(action, context)

    # Action handlers (implementation stubs - integrate with real systems)

    async def _handle_block_ip(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Block IP at firewall."""
        ip = action.parameters.get("source_ip")
        duration = action.parameters.get("duration_seconds", 3600)

        logger.info(f"Blocking IP {ip} for {duration}s")

        from ..containment.zone_isolation import ZoneIsolationEngine, IsolationLevel
        
        isolator = ZoneIsolationEngine()
        result = await isolator.isolate_ip(ip, level=IsolationLevel.BLOCKING, duration_seconds=duration)

        return {"blocked_ip": ip, "duration": duration, "method": "firewall_rule", "rules_applied": result}

    async def _handle_block_domain(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Block domain in DNS."""
        domain = action.parameters.get("domain")

        logger.info(f"Blocking domain {domain}")

        # Implement DNS sinkhole via /etc/hosts or DNS resolver
        sinkhole_ip = "0.0.0.0"  # Black hole address
        dns_entry = f"{sinkhole_ip} {domain}"
        
        # Log for audit trail
        logger.warning(f"DNS BLOCK: {domain} → {sinkhole_ip}")
        
        # In production, integrate with DNS resolver (BIND/dnsmasq/etc)
        # For now, return structured result for testing
        return {
            "blocked_domain": domain,
            "method": "dns_sinkhole",
            "sinkhole_ip": sinkhole_ip,
            "dns_entry": dns_entry,
        }

    async def _handle_isolate_host(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Isolate host from network."""
        host_ip = action.parameters.get("host_ip")

        logger.info(f"Isolating host {host_ip}")

        from ..containment.zone_isolation import ZoneIsolationEngine, IsolationLevel
        
        isolator = ZoneIsolationEngine()
        result = await isolator.isolate_ip(host_ip, level=IsolationLevel.FULL_ISOLATION, duration_seconds=7200)

        return {"isolated_host": host_ip, "method": "vlan_isolation", "isolation_result": result}

    async def _handle_deploy_honeypot(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Deploy honeypot."""
        honeypot_type = action.parameters.get("honeypot_type", "ssh")

        logger.info(f"Deploying {honeypot_type} honeypot")

        from ..containment.honeypots import HoneypotOrchestrator, HoneypotType
        
        orchestrator = HoneypotOrchestrator()
        honeypot_type_enum = (
            HoneypotType[honeypot_type.upper()]
            if honeypot_type.upper() in HoneypotType.__members__
            else HoneypotType.SSH
        )
        result = await orchestrator.deploy_honeypot(honeypot_type_enum)

        return {
            "honeypot_type": honeypot_type,
            "status": "deployed",
            "honeypot_id": result.honeypot_id,
        }

    async def _handle_rate_limit(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Apply rate limiting."""
        target = action.parameters.get("target")
        rate = action.parameters.get("rate", "10/minute")

        logger.info(f"Rate limiting {target} to {rate}")

        from ..containment.traffic_shaping import TrafficShaper, TrafficPriority
        
        shaper = TrafficShaper()
        rate_value, rate_unit = rate.split("/") if "/" in rate else (rate, "minute")
        result = await shaper.apply_rate_limit(target, int(rate_value), rate_unit, TrafficPriority.LOW)

        return {"target": target, "rate": rate, "method": "traffic_shaping", "shaping_result": result}

    async def _handle_alert_soc(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Send alert to SOC."""
        severity = action.parameters.get("severity", context.severity)
        message = action.parameters.get("message", "Threat detected")

        logger.info(f"Alerting SOC: {message} (severity: {severity})")

        # Implement multi-channel SOC notification
        notification_channels = []
        timestamp = datetime.now().isoformat()
        
        # 1. Log to centralized logging (always)
        logger.critical(f"SOC_ALERT | Severity: {severity} | Message: {message} | Context: {context.threat_id}")
        notification_channels.append("syslog")
        
        # 2. File-based alert queue (for external consumption)
        alert_payload = {
            "timestamp": timestamp,
            "severity": severity,
            "message": message,
            "threat_id": context.threat_id,
            "source_ip": context.source_ip,
            "threat_type": context.threat_type,
        }
        
        # Write to alert queue file
        alert_file = Path("/var/log/vertice/soc_alerts.jsonl")
        alert_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(alert_file, "a") as f:
                f.write(json.dumps(alert_payload) + "\n")
            notification_channels.append("file_queue")
        except Exception as e:
            logger.error(f"Failed to write SOC alert to file: {e}")
        
        return {
            "notified": True,
            "severity": severity,
            "message": message,
            "channels": notification_channels,
            "alert_id": f"SOC-{context.threat_id}-{int(datetime.now().timestamp())}",
        }

    async def _handle_trigger_cascade(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Trigger coagulation cascade."""
        zone = action.parameters.get("zone", "default")
        strength = action.parameters.get("strength", "moderate")

        logger.info(f"Triggering cascade in zone {zone} with strength {strength}")

        from ..coagulation.cascade import CoagulationCascade
        from ..coagulation.models import EnrichedThreat, ThreatSeverity
        
        cascade = CoagulationCascade()
        threat_severity = (
            ThreatSeverity[context.severity.upper()]
            if hasattr(ThreatSeverity, context.severity.upper())
            else ThreatSeverity.MEDIUM
        )
        threat = EnrichedThreat(
            threat_id=context.threat_id,
            source_ip=context.source_ip,
            threat_type=context.threat_type,
            severity=threat_severity,
            confidence=0.8,
            timestamp=datetime.now()
        )
        result = await cascade.execute_cascade(threat, zone=zone)

        return {
            "zone": zone,
            "strength": strength,
            "status": "activated",
            "cascade_result": result,
        }

    async def _handle_collect_forensics(
        self, action: PlaybookAction, context: ThreatContext
    ) -> Dict[str, Any]:
        """Collect forensic evidence."""
        target = action.parameters.get("target")
        artifact_types = action.parameters.get("artifacts", ["logs", "memory"])

        logger.info(f"Collecting forensics from {target}: {artifact_types}")

        # Implement forensic evidence collection
        forensics_data = {
            "collection_id": f"FORENSICS-{context.threat_id}-{int(datetime.now().timestamp())}",
            "target": target,
            "artifacts": {},
            "collected_at": datetime.now().isoformat(),
        }
        
        # Collect requested artifacts
        for artifact_type in artifact_types:
            if artifact_type == "logs":
                # Collect system logs for target
                forensics_data["artifacts"]["logs"] = {
                    "syslog": f"/var/log/vertice/forensics/{target}/syslog.txt",
                    "auth": f"/var/log/vertice/forensics/{target}/auth.log",
                    "network": f"/var/log/vertice/forensics/{target}/network.pcap",
                }
            elif artifact_type == "memory":
                # Memory dump placeholder
                forensics_data["artifacts"]["memory"] = {
                    "dump_path": f"/var/log/vertice/forensics/{target}/memory.dump",
                    "size_mb": 0,  # Placeholder
                }
            elif artifact_type == "network":
                # Network packet capture
                forensics_data["artifacts"]["network"] = {
                    "pcap_path": f"/var/log/vertice/forensics/{target}/capture.pcap",
                    "duration_seconds": 300,
                }
        
        # Write forensics manifest
        forensics_dir = Path(f"/var/log/vertice/forensics/{target}")
        forensics_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_file = forensics_dir / "manifest.json"
        try:
            with open(manifest_file, "w") as f:
                json.dumps(forensics_data, f, indent=2)
            logger.info(f"Forensics manifest written: {manifest_file}")
        except Exception as e:
            logger.error(f"Failed to write forensics manifest: {e}")

        return forensics_data

    async def _substitute_variables(
        self, actions: List[PlaybookAction], context: ThreatContext
    ) -> List[PlaybookAction]:
        """Substitute {{variable}} placeholders in action parameters."""
        import copy

        substituted = []

        for action in actions:
            # Deep copy to avoid modifying original
            new_action = copy.deepcopy(action)

            # Substitute in parameters
            for key, value in new_action.parameters.items():
                if isinstance(value, str) and "{{" in value:
                    # Simple variable substitution
                    value = value.replace("{{event.source_ip}}", context.source_ip)
                    value = value.replace("{{event.target_ip}}", context.target_ip or "")
                    value = value.replace("{{threat.id}}", context.threat_id)
                    value = value.replace("{{threat.severity}}", context.severity)

                    new_action.parameters[key] = value

            substituted.append(new_action)

        return substituted

    async def _rollback_actions(
        self, action_results: List[Dict[str, Any]], context: ThreatContext
    ):
        """Rollback successfully executed actions."""
        logger.warning(f"Rolling back {len(action_results)} actions")

        for result in reversed(action_results):
            if result["status"] == ActionStatus.SUCCESS.value:
                # Implement rollback execution
                action_type = result.get("action_type")
                action_id = result["action_id"]
                
                logger.info(f"Rolling back action {action_id} of type {action_type}")
                
                # Execute type-specific rollback
                if action_type == "block_ip":
                    from ..containment.zone_isolation import ZoneIsolationEngine
                    isolator = ZoneIsolationEngine()
                    await isolator.remove_isolation(result.get("blocked_ip"))
                elif action_type == "isolate_host":
                    from ..containment.zone_isolation import ZoneIsolationEngine
                    isolator = ZoneIsolationEngine()
                    await isolator.remove_isolation(result.get("isolated_host"))
                elif action_type == "deploy_honeypot":
                    from ..containment.honeypots import HoneypotOrchestrator
                    orchestrator = HoneypotOrchestrator()
                    honeypot_id = result.get("honeypot_id")
                    if honeypot_id:
                        await orchestrator.stop_honeypot(honeypot_id)

                # Audit log
                await self._audit_log(
                    "action_rolled_back",
                    {
                        "action_id": action_id,
                        "action_type": action_type,
                        "threat_id": context.threat_id,
                    },
                )

    async def _audit_log(self, event_type: str, data: Dict[str, Any]):
        """Write to audit log."""
        if not self.audit_path:
            return

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data,
        }

        try:
            with open(self.audit_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")


import json
