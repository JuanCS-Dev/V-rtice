"""Maximus HCL Executor Service - Action Executor.

This module implements the Action Executor for the Homeostatic Control Loop
(HCL) Executor Service. It is responsible for translating high-level resource
alignment actions into concrete commands and executing them against the
underlying infrastructure.

The Action Executor acts as an interface between the HCL's planning decisions
and the actual system changes. It supports various action types (e.g., scaling
containers, adjusting resource limits, restarting services) and interacts with
specialized controllers (e.g., Kubernetes controller) to perform these operations.
This module ensures that HCL plans are reliably and effectively implemented.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from k8s_controller import KubernetesController


class ActionExecutor:
    """Translates high-level resource alignment actions into concrete commands
    and executes them against the underlying infrastructure.

    Acts as an interface between the HCL's planning decisions and the actual
    system changes.
    """

    def __init__(self, k8s_controller: KubernetesController):
        """Initializes the ActionExecutor.

        Args:
            k8s_controller (KubernetesController): An instance of the KubernetesController for K8s operations.
        """
        self.k8s_controller = k8s_controller
        print("[ActionExecutor] Initialized Action Executor.")

    async def execute_actions(self, plan_id: str, actions: List[Dict[str, Any]], priority: int) -> List[Dict[str, Any]]:
        """Executes a list of actions as part of a resource alignment plan.

        Args:
            plan_id (str): The ID of the plan to which these actions belong.
            actions (List[Dict[str, Any]]): A list of action dictionaries to execute.
            priority (int): The priority of these actions.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each containing the result of an action execution.
        """
        print(f"[ActionExecutor] Executing {len(actions)} actions for plan {plan_id} with priority {priority}")
        results = []
        for action in actions:
            action_type = action.get("type")
            action_params = action.get("parameters", {})
            action_result = {
                "action_type": action_type,
                "status": "failed",
                "details": "Unknown action type",
            }

            try:
                if action_type == "scale_deployment":
                    deployment_name = action_params.get("deployment_name")
                    namespace = action_params.get("namespace", "default")
                    replicas = action_params.get("replicas")
                    if deployment_name and replicas is not None:
                        await self.k8s_controller.scale_deployment(deployment_name, namespace, replicas)
                        action_result = {
                            "action_type": action_type,
                            "status": "success",
                            "details": f"Scaled {deployment_name} to {replicas} replicas.",
                        }
                    else:
                        raise ValueError("Missing deployment_name or replicas for scale_deployment.")
                elif action_type == "update_resource_limits":
                    deployment_name = action_params.get("deployment_name")
                    namespace = action_params.get("namespace", "default")
                    cpu_limit = action_params.get("cpu_limit")
                    memory_limit = action_params.get("memory_limit")
                    if deployment_name and (cpu_limit or memory_limit):
                        await self.k8s_controller.update_resource_limits(
                            deployment_name, namespace, cpu_limit, memory_limit
                        )
                        action_result = {
                            "action_type": action_type,
                            "status": "success",
                            "details": f"Updated resource limits for {deployment_name}.",
                        }
                    else:
                        raise ValueError("Missing deployment_name or resource limits for update_resource_limits.")
                elif action_type == "restart_pod":
                    pod_name = action_params.get("pod_name")
                    namespace = action_params.get("namespace", "default")
                    if pod_name:
                        await self.k8s_controller.restart_pod(pod_name, namespace)
                        action_result = {
                            "action_type": action_type,
                            "status": "success",
                            "details": f"Restarted pod {pod_name}.",
                        }
                    else:
                        raise ValueError("Missing pod_name for restart_pod.")
                else:
                    print(f"[ActionExecutor] Unsupported action type: {action_type}")
                    action_result = {
                        "action_type": action_type,
                        "status": "failed",
                        "details": f"Unsupported action type: {action_type}",
                    }

            except Exception as e:
                print(f"[ActionExecutor] Error executing action {action_type}: {e}")
                action_result = {
                    "action_type": action_type,
                    "status": "failed",
                    "details": str(e),
                }

            results.append(action_result)
            await asyncio.sleep(0.05)  # Simulate time between actions

        return results

    async def get_executor_status(self) -> Dict[str, Any]:
        """Retrieves the current operational status of the Action Executor.

        Returns:
            Dict[str, Any]: A dictionary with the current status.
        """
        return {"status": "ready", "last_activity": datetime.now().isoformat()}
