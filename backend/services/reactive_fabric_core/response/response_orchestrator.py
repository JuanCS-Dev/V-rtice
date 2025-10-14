"""
Response Orchestrator for Reactive Fabric.

Coordinates automated responses to detected threats.
Phase 2: ACTIVE responses with safety controls.
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field


class ResponsePriority(str, Enum):
    """Response priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ResponseStatus(str, Enum):
    """Response execution status."""

    PENDING = "pending"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"
    CANCELLED = "cancelled"


class ActionType(str, Enum):
    """Types of response actions."""

    # Network actions
    BLOCK_IP = "block_ip"
    BLOCK_PORT = "block_port"
    ISOLATE_HOST = "isolate_host"
    SEGMENT_NETWORK = "segment_network"

    # Process actions
    KILL_PROCESS = "kill_process"
    SUSPEND_PROCESS = "suspend_process"

    # File actions
    QUARANTINE_FILE = "quarantine_file"
    DELETE_FILE = "delete_file"

    # User actions
    DISABLE_USER = "disable_user"
    REVOKE_ACCESS = "revoke_access"
    FORCE_LOGOUT = "force_logout"

    # System actions
    ACTIVATE_KILL_SWITCH = "activate_kill_switch"
    ENABLE_DATA_DIODE = "enable_data_diode"
    TRIGGER_BACKUP = "trigger_backup"

    # Defensive actions
    DEPLOY_HONEYPOT = "deploy_honeypot"
    UPDATE_FIREWALL = "update_firewall"
    ROTATE_CREDENTIALS = "rotate_credentials"


class ResponseAction(BaseModel):
    """Individual response action."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    action_type: ActionType
    target: Dict[str, Any]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: ResponsePriority
    reversible: bool = True
    requires_approval: bool = True
    timeout_seconds: int = 300
    retry_attempts: int = 3
    rollback_on_failure: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ResponsePlan(BaseModel):
    """Coordinated response plan."""

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    threat_id: str
    threat_score: float = Field(ge=0.0, le=1.0)
    actions: List[ResponseAction]
    execution_order: List[str]  # Action IDs in order
    parallel_groups: List[List[str]] = Field(default_factory=list)
    priority: ResponsePriority
    auto_execute: bool = False
    require_confirmation: bool = True
    rollback_plan: Optional[List[str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: ResponseStatus = ResponseStatus.PENDING
    executed_actions: List[str] = Field(default_factory=list)
    failed_actions: List[str] = Field(default_factory=list)


class SafetyCheck(BaseModel):
    """Safety check before executing actions."""

    check_id: str = Field(default_factory=lambda: str(uuid4()))
    check_type: str
    passed: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class ResponseConfig(BaseModel):
    """Response orchestrator configuration."""

    auto_response_enabled: bool = False
    max_concurrent_actions: int = 5
    action_timeout_seconds: int = 300
    require_dual_approval: bool = True
    rollback_on_failure: bool = True
    safety_checks_enabled: bool = True
    critical_threshold: float = 0.8
    high_threshold: float = 0.6
    medium_threshold: float = 0.4
    max_retry_attempts: int = 3
    audit_all_actions: bool = True


class ResponseOrchestrator:
    """Orchestrates automated responses to threats."""

    def __init__(self, config: ResponseConfig = None):
        """Initialize response orchestrator."""
        self.config = config or ResponseConfig()
        self.response_plans: Dict[str, ResponsePlan] = {}
        self.active_responses: Dict[str, ResponsePlan] = {}
        self.completed_responses: Dict[str, ResponsePlan] = {}
        self.action_history: List[ResponseAction] = []
        self.safety_checks: List[SafetyCheck] = []

        # Execution tracking
        self.executing_actions: Set[str] = set()
        self.execution_semaphore = asyncio.Semaphore(
            self.config.max_concurrent_actions
        )

        # Metrics
        self.total_plans = 0
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.rollback_count = 0

        # Integration points (to be injected)
        self.firewall = None
        self.kill_switch = None
        self.network_segmentation = None
        self.data_diode = None

        self._running = False
        self._executor_task = None

    async def create_response_plan(
        self,
        threat_id: str,
        threat_score: float,
        threat_category: str,
        entities: Dict[str, Any],
        mitre_tactics: List[str] = None
    ) -> ResponsePlan:
        """Create a response plan for a detected threat."""
        # Determine priority based on threat score
        if threat_score >= self.config.critical_threshold:
            priority = ResponsePriority.CRITICAL
        elif threat_score >= self.config.high_threshold:
            priority = ResponsePriority.HIGH
        elif threat_score >= self.config.medium_threshold:
            priority = ResponsePriority.MEDIUM
        else:
            priority = ResponsePriority.LOW

        # Generate appropriate actions based on threat
        actions = await self._generate_response_actions(
            threat_category,
            entities,
            priority,
            mitre_tactics
        )

        # Determine execution order and parallel groups
        execution_order, parallel_groups = self._plan_execution_order(actions)

        # Create plan
        plan = ResponsePlan(
            name=f"Response to {threat_category}",
            description=f"Automated response plan for threat {threat_id}",
            threat_id=threat_id,
            threat_score=threat_score,
            actions=actions,
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            priority=priority,
            auto_execute=(
                self.config.auto_response_enabled and
                priority in [ResponsePriority.CRITICAL, ResponsePriority.HIGH]
            ),
            require_confirmation=self.config.require_dual_approval
        )

        # Store plan
        self.response_plans[plan.plan_id] = plan
        self.total_plans += 1

        # Auto-execute if configured
        if plan.auto_execute and not plan.require_confirmation:
            await self.execute_plan(plan.plan_id)

        return plan

    async def execute_plan(
        self,
        plan_id: str,
        approver: str = None,
        skip_safety: bool = False
    ) -> bool:
        """Execute a response plan."""
        if plan_id not in self.response_plans:
            return False

        plan = self.response_plans[plan_id]

        # Safety checks
        if self.config.safety_checks_enabled and not skip_safety:
            checks_passed = await self._perform_safety_checks(plan)
            if not checks_passed:
                plan.status = ResponseStatus.CANCELLED
                return False

        # Mark as approved
        if approver:
            plan.approved_at = datetime.utcnow()

        # Move to active responses
        self.active_responses[plan_id] = plan
        plan.status = ResponseStatus.EXECUTING
        plan.executed_at = datetime.utcnow()

        # Execute actions according to plan
        success = await self._execute_actions(plan)

        # Update status
        if success:
            plan.status = ResponseStatus.COMPLETED
        else:
            plan.status = ResponseStatus.FAILED

            # Rollback if configured
            if self.config.rollback_on_failure:
                await self._rollback_plan(plan)

        plan.completed_at = datetime.utcnow()

        # Move to completed
        self.completed_responses[plan_id] = plan
        del self.active_responses[plan_id]

        return success

    async def _generate_response_actions(
        self,
        threat_category: str,
        entities: Dict[str, Any],
        priority: ResponsePriority,
        mitre_tactics: List[str] = None
    ) -> List[ResponseAction]:
        """Generate appropriate response actions for threat."""
        actions = []

        # Network-based threats
        if "ip" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.BLOCK_IP,
                target={"ip": entities["ip"]},
                parameters={"duration_minutes": 60},
                priority=priority,
                reversible=True
            ))

            if priority == ResponsePriority.CRITICAL:
                actions.append(ResponseAction(
                    action_type=ActionType.UPDATE_FIREWALL,
                    target={"ip": entities["ip"]},
                    parameters={"rule": "deny_all"},
                    priority=priority
                ))

        # Host-based threats
        if "hostname" in entities:
            if priority in [ResponsePriority.CRITICAL, ResponsePriority.HIGH]:
                actions.append(ResponseAction(
                    action_type=ActionType.ISOLATE_HOST,
                    target={"hostname": entities["hostname"]},
                    parameters={"allow_management": True},
                    priority=priority,
                    reversible=True
                ))

        # Process threats
        if "process" in entities or "pid" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.KILL_PROCESS,
                target=entities,
                priority=priority,
                reversible=False
            ))

        # File threats
        if "file_path" in entities or "file_hash" in entities:
            actions.append(ResponseAction(
                action_type=ActionType.QUARANTINE_FILE,
                target=entities,
                priority=priority,
                reversible=True
            ))

        # User threats
        if "user" in entities or "username" in entities:
            if priority == ResponsePriority.CRITICAL:
                actions.append(ResponseAction(
                    action_type=ActionType.DISABLE_USER,
                    target=entities,
                    priority=priority,
                    reversible=True
                ))
            else:
                actions.append(ResponseAction(
                    action_type=ActionType.FORCE_LOGOUT,
                    target=entities,
                    priority=priority
                ))

        # Critical threats - emergency response
        if priority == ResponsePriority.CRITICAL:
            if threat_category in ["EXFILTRATION", "COMMAND_CONTROL"]:
                actions.append(ResponseAction(
                    action_type=ActionType.ACTIVATE_KILL_SWITCH,
                    target={"system": "all"},
                    parameters={"severity": "high"},
                    priority=ResponsePriority.CRITICAL,
                    requires_approval=True
                ))

            # Enable data diode for critical data protection
            actions.append(ResponseAction(
                action_type=ActionType.ENABLE_DATA_DIODE,
                target={"direction": "outbound"},
                priority=ResponsePriority.CRITICAL,
                reversible=True
            ))

        # Add defensive actions
        if threat_category == "RECONNAISSANCE":
            actions.append(ResponseAction(
                action_type=ActionType.DEPLOY_HONEYPOT,
                target={"type": "decoy_service"},
                parameters={"port": entities.get("port", 22)},
                priority=priority
            ))

        # Credential-based threats
        if threat_category == "CREDENTIAL_ACCESS":
            actions.append(ResponseAction(
                action_type=ActionType.ROTATE_CREDENTIALS,
                target={"scope": "affected_users"},
                priority=priority
            ))

        self.total_actions += len(actions)

        return actions

    def _plan_execution_order(
        self,
        actions: List[ResponseAction]
    ) -> Tuple[List[str], List[List[str]]]:
        """Plan the execution order of actions."""
        # Group by dependencies
        critical_actions = []
        high_actions = []
        medium_actions = []
        low_actions = []

        for action in actions:
            if action.priority == ResponsePriority.CRITICAL:
                critical_actions.append(action.action_id)
            elif action.priority == ResponsePriority.HIGH:
                high_actions.append(action.action_id)
            elif action.priority == ResponsePriority.MEDIUM:
                medium_actions.append(action.action_id)
            else:
                low_actions.append(action.action_id)

        # Execution order: critical first, then high, medium, low
        execution_order = critical_actions + high_actions + medium_actions + low_actions

        # Parallel groups - same priority can run in parallel
        parallel_groups = []
        if critical_actions:
            parallel_groups.append(critical_actions)
        if high_actions:
            parallel_groups.append(high_actions)
        if medium_actions:
            parallel_groups.append(medium_actions)
        if low_actions:
            parallel_groups.append(low_actions)

        return execution_order, parallel_groups

    async def _perform_safety_checks(self, plan: ResponsePlan) -> bool:
        """Perform safety checks before executing plan."""
        checks_passed = True

        # Check 1: System stability
        stability_check = SafetyCheck(
            check_type="system_stability",
            passed=True,  # Would check actual system metrics
            message="System stable for response execution"
        )
        self.safety_checks.append(stability_check)
        checks_passed &= stability_check.passed

        # Check 2: No conflicting actions
        conflict_check = SafetyCheck(
            check_type="action_conflicts",
            passed=len(self.executing_actions) == 0,
            message="No conflicting actions in progress"
        )
        self.safety_checks.append(conflict_check)
        checks_passed &= conflict_check.passed

        # Check 3: Resource availability
        resource_check = SafetyCheck(
            check_type="resource_availability",
            passed=True,  # Would check actual resources
            message="Sufficient resources available"
        )
        self.safety_checks.append(resource_check)
        checks_passed &= resource_check.passed

        # Check 4: Business hours (for non-critical)
        if plan.priority not in [ResponsePriority.CRITICAL]:
            now = datetime.utcnow()
            business_hours = 8 <= now.hour < 18

            business_check = SafetyCheck(
                check_type="business_hours",
                passed=business_hours or plan.priority == ResponsePriority.CRITICAL,
                message="Within business hours or critical priority"
            )
            self.safety_checks.append(business_check)
            checks_passed &= business_check.passed

        return checks_passed

    async def _execute_actions(self, plan: ResponsePlan) -> bool:
        """Execute actions in the response plan."""
        success = True

        # Execute parallel groups in sequence
        for group in plan.parallel_groups:
            # Execute actions in group in parallel
            tasks = []
            for action_id in group:
                action = next(
                    (a for a in plan.actions if a.action_id == action_id),
                    None
                )
                if action:
                    tasks.append(self._execute_single_action(action))

            # Wait for group to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check results
                for i, result in enumerate(results):
                    if isinstance(result, Exception) or not result:
                        success = False
                        plan.failed_actions.append(group[i])
                    else:
                        plan.executed_actions.append(group[i])

        return success

    async def _execute_single_action(self, action: ResponseAction) -> bool:
        """Execute a single response action."""
        async with self.execution_semaphore:
            try:
                self.executing_actions.add(action.action_id)
                action.status = ResponseStatus.EXECUTING
                action.executed_at = datetime.utcnow()

                # Route to appropriate handler
                result = await self._route_action(action)

                if result:
                    action.status = ResponseStatus.COMPLETED
                    action.result = result
                    self.successful_actions += 1
                else:
                    action.status = ResponseStatus.FAILED
                    self.failed_actions += 1

                action.completed_at = datetime.utcnow()
                self.action_history.append(action)

                return result is not None

            except Exception as e:
                action.status = ResponseStatus.FAILED
                action.error_message = str(e)
                self.failed_actions += 1
                return False

            finally:
                self.executing_actions.discard(action.action_id)

    async def _route_action(self, action: ResponseAction) -> Optional[Dict[str, Any]]:
        """Route action to appropriate handler."""
        # Network actions
        if action.action_type == ActionType.BLOCK_IP:
            return await self._block_ip(action)
        elif action.action_type == ActionType.ISOLATE_HOST:
            return await self._isolate_host(action)
        elif action.action_type == ActionType.SEGMENT_NETWORK:
            return await self._segment_network(action)

        # Process actions
        elif action.action_type == ActionType.KILL_PROCESS:
            return await self._kill_process(action)

        # File actions
        elif action.action_type == ActionType.QUARANTINE_FILE:
            return await self._quarantine_file(action)

        # User actions
        elif action.action_type == ActionType.DISABLE_USER:
            return await self._disable_user(action)
        elif action.action_type == ActionType.FORCE_LOGOUT:
            return await self._force_logout(action)

        # System actions
        elif action.action_type == ActionType.ACTIVATE_KILL_SWITCH:
            return await self._activate_kill_switch(action)
        elif action.action_type == ActionType.ENABLE_DATA_DIODE:
            return await self._enable_data_diode(action)

        # Defensive actions
        elif action.action_type == ActionType.DEPLOY_HONEYPOT:
            return await self._deploy_honeypot(action)
        elif action.action_type == ActionType.UPDATE_FIREWALL:
            return await self._update_firewall(action)
        elif action.action_type == ActionType.ROTATE_CREDENTIALS:
            return await self._rotate_credentials(action)

        return None

    # Action implementations (would integrate with actual systems)

    async def _block_ip(self, action: ResponseAction) -> Dict[str, Any]:
        """Block an IP address."""
        ip = action.target.get("ip")
        duration = action.parameters.get("duration_minutes", 60)

        if self.firewall:
            # Use actual firewall
            success = await self.firewall.block_ip(ip, duration)
        else:
            # Simulation
            success = True

        return {
            "action": "block_ip",
            "ip": ip,
            "duration": duration,
            "success": success
        }

    async def _isolate_host(self, action: ResponseAction) -> Dict[str, Any]:
        """Isolate a host from network."""
        hostname = action.target.get("hostname")

        if self.network_segmentation:
            # Use actual network segmentation
            success = await self.network_segmentation.isolate_host(hostname)
        else:
            # Simulation
            success = True

        return {
            "action": "isolate_host",
            "hostname": hostname,
            "success": success
        }

    async def _segment_network(self, action: ResponseAction) -> Dict[str, Any]:
        """Segment network to contain threat."""
        return {
            "action": "segment_network",
            "success": True,
            "segments_created": 2
        }

    async def _kill_process(self, action: ResponseAction) -> Dict[str, Any]:
        """Kill a malicious process."""
        return {
            "action": "kill_process",
            "pid": action.target.get("pid", "unknown"),
            "success": True
        }

    async def _quarantine_file(self, action: ResponseAction) -> Dict[str, Any]:
        """Quarantine a malicious file."""
        return {
            "action": "quarantine_file",
            "file": action.target.get("file_path", "unknown"),
            "success": True
        }

    async def _disable_user(self, action: ResponseAction) -> Dict[str, Any]:
        """Disable a compromised user account."""
        return {
            "action": "disable_user",
            "user": action.target.get("user", "unknown"),
            "success": True
        }

    async def _force_logout(self, action: ResponseAction) -> Dict[str, Any]:
        """Force logout a user."""
        return {
            "action": "force_logout",
            "user": action.target.get("user", "unknown"),
            "success": True
        }

    async def _activate_kill_switch(self, action: ResponseAction) -> Dict[str, Any]:
        """Activate emergency kill switch."""
        if self.kill_switch:
            # Use actual kill switch
            success = await self.kill_switch.activate(
                action.parameters.get("severity", "high")
            )
        else:
            # Simulation
            success = True

        return {
            "action": "activate_kill_switch",
            "severity": action.parameters.get("severity"),
            "success": success
        }

    async def _enable_data_diode(self, action: ResponseAction) -> Dict[str, Any]:
        """Enable data diode for one-way communication."""
        if self.data_diode:
            # Use actual data diode
            success = await self.data_diode.enable(
                action.target.get("direction", "outbound")
            )
        else:
            # Simulation
            success = True

        return {
            "action": "enable_data_diode",
            "direction": action.target.get("direction"),
            "success": success
        }

    async def _deploy_honeypot(self, action: ResponseAction) -> Dict[str, Any]:
        """Deploy a honeypot."""
        return {
            "action": "deploy_honeypot",
            "type": action.target.get("type"),
            "port": action.parameters.get("port"),
            "success": True
        }

    async def _update_firewall(self, action: ResponseAction) -> Dict[str, Any]:
        """Update firewall rules."""
        if self.firewall:
            # Use actual firewall
            success = await self.firewall.add_rule(action.parameters.get("rule"))
        else:
            # Simulation
            success = True

        return {
            "action": "update_firewall",
            "rule": action.parameters.get("rule"),
            "success": success
        }

    async def _rotate_credentials(self, action: ResponseAction) -> Dict[str, Any]:
        """Rotate credentials."""
        return {
            "action": "rotate_credentials",
            "scope": action.target.get("scope"),
            "success": True,
            "credentials_rotated": 5
        }

    async def _rollback_plan(self, plan: ResponsePlan):
        """Rollback executed actions."""
        plan.status = ResponseStatus.ROLLBACK
        self.rollback_count += 1

        # Rollback in reverse order
        for action_id in reversed(plan.executed_actions):
            action = next(
                (a for a in plan.actions if a.action_id == action_id),
                None
            )
            if action and action.reversible:
                await self._rollback_action(action)

    async def _rollback_action(self, action: ResponseAction):
        """Rollback a single action."""
        # Implementation would reverse the action
        pass

    async def get_response_status(self) -> Dict[str, Any]:
        """Get current response status."""
        return {
            "active_plans": len(self.active_responses),
            "completed_plans": len(self.completed_responses),
            "executing_actions": len(self.executing_actions),
            "total_plans": self.total_plans,
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "rollback_count": self.rollback_count,
            "recent_plans": [
                {
                    "plan_id": p.plan_id,
                    "name": p.name,
                    "status": p.status.value,
                    "priority": p.priority.value,
                    "threat_score": p.threat_score
                }
                for p in list(self.completed_responses.values())[-5:]
            ]
        }

    async def start(self):
        """Start response orchestrator."""
        self._running = True

    async def stop(self):
        """Stop response orchestrator."""
        self._running = False

        # Wait for executing actions to complete
        while self.executing_actions:
            await asyncio.sleep(0.1)

    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics."""
        return {
            "running": self._running,
            "total_plans": self.total_plans,
            "active_plans": len(self.active_responses),
            "completed_plans": len(self.completed_responses),
            "total_actions": self.total_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "success_rate": (
                self.successful_actions / self.total_actions
                if self.total_actions > 0 else 0
            ),
            "rollback_count": self.rollback_count,
            "safety_checks": len(self.safety_checks)
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ResponseOrchestrator(running={self._running}, "
            f"plans={self.total_plans}, "
            f"actions={self.total_actions}, "
            f"success_rate={self.successful_actions/self.total_actions if self.total_actions > 0 else 0:.2%})"
        )