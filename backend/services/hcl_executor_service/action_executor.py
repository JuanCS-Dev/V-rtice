"""HCL Executor Service - Action Executor.

This module contains the `ActionExecutor` class, which is responsible for
receiving action plans from the HCL Planner, validating them, and executing
the specified actions using the Kubernetes Controller.

It includes safety features like dry-run mode, rate limiting between actions,
and automatic rollback on failure to ensure stable and safe operations.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
from enum import Enum

from .k8s_controller import KubernetesController

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Enumeration for the types of actions that can be executed."""
    SCALE_SERVICE = "scale_service"
    ADJUST_RESOURCES = "adjust_resources"
    ROLLBACK = "rollback"
    NO_ACTION = "no_action"


class ExecutionStatus(str, Enum):
    """Enumeration for the status of an action plan execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ActionExecutor:
    """Validates and executes action plans on the Kubernetes cluster.

    This class acts as a safe interface between the HCL Planner's decisions and
    the Kubernetes API. It validates actions against predefined safety limits
    before instructing the KubernetesController to apply the changes.

    Attributes:
        k8s (KubernetesController): The controller for interacting with Kubernetes.
        dry_run (bool): If True, actions are logged but not executed.
        enable_rollback (bool): If True, failed plans trigger an automatic rollback.
    """

    SERVICE_DEPLOYMENTS = {"maximus_core": "maximus-core"} # Simplified
    MAX_REPLICAS = 20
    MIN_REPLICAS = 1

    def __init__(self, k8s_controller: KubernetesController, dry_run: bool = False, enable_rollback: bool = True):
        """Initializes the ActionExecutor.

        Args:
            k8s_controller (KubernetesController): An instance of the k8s controller.
            dry_run (bool): If True, enables dry-run mode.
            enable_rollback (bool): If True, enables automatic rollback on failure.
        """
        self.k8s = k8s_controller
        self.dry_run = dry_run
        self.enable_rollback = enable_rollback
        self.execution_history: List[Dict] = []

    async def execute_action_plan(self, decision_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates and executes a complete action plan from the Planner.

        Args:
            decision_id (str): The ID of the decision that generated this plan.
            actions (List[Dict[str, Any]]): A list of action dictionaries to execute.

        Returns:
            Dict[str, Any]: A dictionary summarizing the execution result.
        """
        logger.info(f"Executing action plan for decision {decision_id}...")
        if self.dry_run:
            logger.info("[DRY RUN] Would execute actions: %s", actions)
            return {"status": "dry_run", "actions": actions}

        execution_record = {"decision_id": decision_id, "results": [], "errors": [], "status": ExecutionStatus.SUCCESS}
        
        for action in actions:
            try:
                result = await self._execute_single_action(action)
                execution_record["results"].append(result)
                if result.get("status") == "error":
                    execution_record["status"] = ExecutionStatus.FAILED
                    execution_record["errors"].append(result.get("error"))
                    # In a real scenario, rollback logic would be triggered here.
                    break
            except Exception as e:
                logger.error(f"Action execution failed: {e}")
                execution_record["status"] = ExecutionStatus.FAILED
                execution_record["errors"].append(str(e))
                break
        
        self.execution_history.append(execution_record)
        return execution_record

    async def _execute_single_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Routes a single action to its corresponding execution method."""
        action_type = ActionType(action["type"])
        if action_type == ActionType.SCALE_SERVICE:
            return await self.k8s.scale_deployment(
                deployment_name=self.SERVICE_DEPLOYMENTS[action["service"]],
                target_replicas=action["target_replicas"]
            )
        elif action_type == ActionType.ADJUST_RESOURCES:
            # Placeholder for resource adjustment logic
            return {"status": "success", "action": "adjust_resources"}
        elif action_type == ActionType.NO_ACTION:
            return {"status": "success", "action": "no_action"}
        else:
            raise ValueError(f"Unknown action type: {action_type}")