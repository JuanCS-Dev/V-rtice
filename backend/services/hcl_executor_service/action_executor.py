"""
HCL Executor - Action Executor
================================
Executes actions from HCL Planner with validation and rollback.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum

from k8s_controller import KubernetesController

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Action types"""
    SCALE_SERVICE = "scale_service"
    ADJUST_RESOURCES = "adjust_resources"
    CREATE_HPA = "create_hpa"
    DELETE_HPA = "delete_hpa"
    ROLLBACK = "rollback"
    NO_ACTION = "no_action"


class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionExecutor:
    """
    Executes HCL actions on Kubernetes cluster.

    Features:
    - Action validation before execution
    - Safety checks (rate limiting, bounds checking)
    - Automatic rollback on failure
    - Execution history tracking
    - Dry-run mode
    """

    # Service name mapping
    SERVICE_DEPLOYMENTS = {
        "maximus_core": "maximus-core",
        "threat_intel": "threat-intel-service",
        "malware_analysis": "malware-analysis-service",
        "malware": "malware-analysis-service",  # Alias
        "monitor": "hcl-monitor",
        "analyzer": "hcl-analyzer",
        "planner": "hcl-planner"
    }

    # Safety limits
    MAX_REPLICAS = 20
    MIN_REPLICAS = 1
    MAX_SCALE_DELTA = 5  # Max change per action
    MAX_RESOURCE_MULTIPLIER = 3.0
    MIN_RESOURCE_MULTIPLIER = 0.3

    # Rate limiting
    MIN_ACTION_INTERVAL = 30  # Seconds between actions on same deployment

    def __init__(
        self,
        k8s_controller: KubernetesController,
        dry_run: bool = False,
        enable_rollback: bool = True
    ):
        """
        Initialize action executor.

        Args:
            k8s_controller: Kubernetes controller instance
            dry_run: If True, validate but don't execute
            enable_rollback: If True, rollback on failure
        """
        self.k8s = k8s_controller
        self.dry_run = dry_run
        self.enable_rollback = enable_rollback

        # Execution tracking
        self.execution_history: List[Dict] = []
        self.last_action_time: Dict[str, datetime] = {}
        self.in_progress: Dict[str, bool] = {}

        logger.info(
            f"Action executor initialized (dry_run={dry_run}, rollback={enable_rollback})"
        )

    async def execute_action_plan(
        self,
        decision_id: str,
        actions: List[Dict[str, Any]],
        operational_mode: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Execute complete action plan from Planner.

        Args:
            decision_id: Decision ID for tracking
            actions: List of actions to execute
            operational_mode: Operational mode (for validation)
            confidence: Decision confidence (for safety checks)

        Returns:
            Execution result with details
        """
        execution_id = f"exec_{datetime.now(timezone.utc).timestamp()}"

        logger.info(
            f"Executing action plan {decision_id} "
            f"(mode={operational_mode}, actions={len(actions)})"
        )

        # Initialize execution record
        execution_record = {
            "execution_id": execution_id,
            "decision_id": decision_id,
            "operational_mode": operational_mode,
            "confidence": confidence,
            "actions": actions,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": ExecutionStatus.RUNNING,
            "results": [],
            "errors": [],
            "rollback_performed": False
        }

        # Validate action plan
        validation = await self._validate_action_plan(actions, confidence)
        if not validation["valid"]:
            execution_record["status"] = ExecutionStatus.FAILED
            execution_record["errors"] = validation["errors"]
            execution_record["end_time"] = datetime.now(timezone.utc).isoformat()
            self.execution_history.append(execution_record)

            logger.error(f"Action plan validation failed: {validation['errors']}")
            return execution_record

        # Execute actions sequentially
        successful_actions = []
        failed = False

        for i, action in enumerate(actions):
            action_type = action.get("type")

            logger.info(f"Executing action {i+1}/{len(actions)}: {action_type}")

            try:
                result = await self._execute_single_action(action)
                execution_record["results"].append(result)

                if result["status"] == "success":
                    successful_actions.append((action, result))
                elif result["status"] == "error":
                    failed = True
                    execution_record["errors"].append(result.get("error", "Unknown error"))
                    break

            except Exception as e:
                logger.error(f"Exception executing action {i+1}: {e}")
                execution_record["errors"].append(str(e))
                failed = True
                break

        # Handle failure with rollback
        if failed and self.enable_rollback and successful_actions:
            logger.warning("Execution failed, attempting rollback...")
            rollback_result = await self._rollback_actions(successful_actions)
            execution_record["rollback_performed"] = True
            execution_record["rollback_result"] = rollback_result
            execution_record["status"] = ExecutionStatus.ROLLED_BACK
        elif failed:
            execution_record["status"] = ExecutionStatus.FAILED
        else:
            execution_record["status"] = ExecutionStatus.SUCCESS

        # Finalize record
        execution_record["end_time"] = datetime.now(timezone.utc).isoformat()
        self.execution_history.append(execution_record)

        # Keep last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

        logger.info(
            f"Action plan execution complete: {execution_record['status']} "
            f"(success={len(successful_actions)}, errors={len(execution_record['errors'])})"
        )

        return execution_record

    async def _validate_action_plan(
        self,
        actions: List[Dict[str, Any]],
        confidence: float
    ) -> Dict[str, Any]:
        """
        Validate action plan before execution.

        Args:
            actions: List of actions
            confidence: Decision confidence

        Returns:
            Validation result
        """
        errors = []

        # Check confidence threshold
        if confidence < 0.3:
            errors.append(f"Confidence too low: {confidence:.2f} < 0.3")

        # Validate each action
        for i, action in enumerate(actions):
            action_type = action.get("type")

            if not action_type:
                errors.append(f"Action {i}: Missing 'type' field")
                continue

            # Type-specific validation
            if action_type == ActionType.SCALE_SERVICE:
                service = action.get("service")
                target_replicas = action.get("target_replicas")
                delta = action.get("delta")

                if not service:
                    errors.append(f"Action {i}: Missing 'service' field")
                elif service not in self.SERVICE_DEPLOYMENTS:
                    errors.append(f"Action {i}: Unknown service '{service}'")

                if target_replicas is None:
                    errors.append(f"Action {i}: Missing 'target_replicas' field")
                elif not (self.MIN_REPLICAS <= target_replicas <= self.MAX_REPLICAS):
                    errors.append(
                        f"Action {i}: target_replicas={target_replicas} out of bounds "
                        f"[{self.MIN_REPLICAS}, {self.MAX_REPLICAS}]"
                    )

                if delta and abs(delta) > self.MAX_SCALE_DELTA:
                    errors.append(
                        f"Action {i}: delta={delta} exceeds max {self.MAX_SCALE_DELTA}"
                    )

            elif action_type == ActionType.ADJUST_RESOURCES:
                multiplier = action.get("multiplier")

                if multiplier is None:
                    errors.append(f"Action {i}: Missing 'multiplier' field")
                elif not (self.MIN_RESOURCE_MULTIPLIER <= multiplier <= self.MAX_RESOURCE_MULTIPLIER):
                    errors.append(
                        f"Action {i}: multiplier={multiplier} out of bounds "
                        f"[{self.MIN_RESOURCE_MULTIPLIER}, {self.MAX_RESOURCE_MULTIPLIER}]"
                    )

            elif action_type == ActionType.NO_ACTION:
                pass  # Always valid

            else:
                errors.append(f"Action {i}: Unknown action type '{action_type}'")

        # Check rate limiting
        for action in actions:
            if action.get("type") == ActionType.SCALE_SERVICE:
                service = action.get("service")
                if service:
                    deployment = self.SERVICE_DEPLOYMENTS.get(service)
                    if deployment and deployment in self.last_action_time:
                        last_time = self.last_action_time[deployment]
                        elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
                        if elapsed < self.MIN_ACTION_INTERVAL:
                            errors.append(
                                f"Rate limit: {deployment} was modified {elapsed:.0f}s ago "
                                f"(min interval: {self.MIN_ACTION_INTERVAL}s)"
                            )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    async def _execute_single_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute single action.

        Args:
            action: Action dict

        Returns:
            Execution result
        """
        action_type = action.get("type")

        if self.dry_run:
            logger.info(f"DRY RUN: Would execute {action_type} with {action}")
            return {
                "status": "success",
                "action_type": action_type,
                "dry_run": True,
                "message": "Dry run - no changes made"
            }

        # Route to appropriate handler
        if action_type == ActionType.SCALE_SERVICE:
            return await self._execute_scale_service(action)

        elif action_type == ActionType.ADJUST_RESOURCES:
            return await self._execute_adjust_resources(action)

        elif action_type == ActionType.CREATE_HPA:
            return await self._execute_create_hpa(action)

        elif action_type == ActionType.DELETE_HPA:
            return await self._execute_delete_hpa(action)

        elif action_type == ActionType.ROLLBACK:
            return await self._execute_rollback(action)

        elif action_type == ActionType.NO_ACTION:
            return {
                "status": "success",
                "action_type": action_type,
                "message": "No action required"
            }

        else:
            return {
                "status": "error",
                "action_type": action_type,
                "error": f"Unknown action type: {action_type}"
            }

    async def _execute_scale_service(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scale_service action"""
        service = action["service"]
        target_replicas = action["target_replicas"]
        current_replicas = action.get("current_replicas")

        deployment_name = self.SERVICE_DEPLOYMENTS[service]

        # Execute scaling
        result = await self.k8s.scale_deployment(
            deployment_name=deployment_name,
            target_replicas=target_replicas,
            current_replicas=current_replicas
        )

        # Update tracking
        if result["status"] == "success":
            self.last_action_time[deployment_name] = datetime.now(timezone.utc)

        result["action_type"] = ActionType.SCALE_SERVICE
        result["service"] = service
        return result

    async def _execute_adjust_resources(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute adjust_resources action"""
        multiplier = action["multiplier"]
        services = action.get("services", list(self.SERVICE_DEPLOYMENTS.keys()))

        results = []

        for service in services:
            deployment_name = self.SERVICE_DEPLOYMENTS.get(service)
            if not deployment_name:
                continue

            # Apply multiplier to default resource values
            cpu_limit = action.get("cpu_limit", f"{int(1000 * multiplier)}m")
            memory_limit = action.get("memory_limit", f"{int(2048 * multiplier)}Mi")

            result = await self.k8s.update_resource_limits(
                deployment_name=deployment_name,
                cpu_limit=cpu_limit,
                memory_limit=memory_limit
            )

            results.append(result)

        # Aggregate results
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = len(results) - success_count

        return {
            "status": "success" if error_count == 0 else "partial",
            "action_type": ActionType.ADJUST_RESOURCES,
            "multiplier": multiplier,
            "services_updated": success_count,
            "errors": error_count,
            "details": results
        }

    async def _execute_create_hpa(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_hpa action"""
        service = action["service"]
        deployment_name = self.SERVICE_DEPLOYMENTS[service]

        result = await self.k8s.create_or_update_hpa(
            deployment_name=deployment_name,
            min_replicas=action.get("min_replicas", 1),
            max_replicas=action.get("max_replicas", 10),
            target_cpu_utilization=action.get("target_cpu", 70),
            target_memory_utilization=action.get("target_memory")
        )

        result["action_type"] = ActionType.CREATE_HPA
        result["service"] = service
        return result

    async def _execute_delete_hpa(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delete_hpa action"""
        service = action["service"]
        deployment_name = self.SERVICE_DEPLOYMENTS[service]

        result = await self.k8s.delete_hpa(deployment_name)

        result["action_type"] = ActionType.DELETE_HPA
        result["service"] = service
        return result

    async def _execute_rollback(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback action"""
        service = action["service"]
        deployment_name = self.SERVICE_DEPLOYMENTS[service]
        revision = action.get("revision")

        result = await self.k8s.rollback_deployment(
            deployment_name=deployment_name,
            revision=revision
        )

        result["action_type"] = ActionType.ROLLBACK
        result["service"] = service
        return result

    async def _rollback_actions(
        self,
        successful_actions: List[tuple]
    ) -> Dict[str, Any]:
        """
        Rollback successfully executed actions.

        Args:
            successful_actions: List of (action, result) tuples

        Returns:
            Rollback result
        """
        logger.info(f"Rolling back {len(successful_actions)} actions...")

        rollback_results = []

        # Reverse order for rollback
        for action, original_result in reversed(successful_actions):
            action_type = action.get("type")

            try:
                if action_type == ActionType.SCALE_SERVICE:
                    # Scale back to previous replicas
                    service = action["service"]
                    deployment_name = self.SERVICE_DEPLOYMENTS[service]
                    previous_replicas = original_result.get("previous_replicas")

                    if previous_replicas is not None:
                        result = await self.k8s.scale_deployment(
                            deployment_name=deployment_name,
                            target_replicas=previous_replicas
                        )
                        rollback_results.append({
                            "action": "scale_service",
                            "service": service,
                            "status": result["status"]
                        })

                elif action_type == ActionType.ADJUST_RESOURCES:
                    # Restore previous resource limits
                    for detail in original_result.get("details", []):
                        if detail["status"] == "success":
                            deployment_name = detail["deployment"]
                            old_limits = detail.get("old_limits", {})

                            if old_limits:
                                result = await self.k8s.update_resource_limits(
                                    deployment_name=deployment_name,
                                    cpu_limit=old_limits.get("cpu"),
                                    memory_limit=old_limits.get("memory")
                                )
                                rollback_results.append({
                                    "action": "adjust_resources",
                                    "deployment": deployment_name,
                                    "status": result["status"]
                                })

                # Other action types don't need rollback or have their own mechanisms

            except Exception as e:
                logger.error(f"Error rolling back action: {e}")
                rollback_results.append({
                    "action": action_type,
                    "status": "error",
                    "error": str(e)
                })

        success_count = sum(1 for r in rollback_results if r.get("status") == "success")

        return {
            "total_actions": len(rollback_results),
            "successful_rollbacks": success_count,
            "failed_rollbacks": len(rollback_results) - success_count,
            "details": rollback_results
        }

    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.execution_history[-limit:]

    def get_service_last_action(self, service: str) -> Optional[datetime]:
        """Get last action time for service"""
        deployment = self.SERVICE_DEPLOYMENTS.get(service)
        if deployment:
            return self.last_action_time.get(deployment)
        return None
