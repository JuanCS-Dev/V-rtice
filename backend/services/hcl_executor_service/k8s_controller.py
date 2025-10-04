"""HCL Executor Service - Kubernetes Controller.

This module provides a real Kubernetes API client for executing decisions made
by the HCL Planner. It is responsible for interacting with the Kubernetes API
server to perform actions like scaling deployments, updating resource limits,
and managing Horizontal Pod Autoscalers (HPAs).

This is a production-ready implementation using the official `kubernetes` Python client.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesController:
    """A controller for interacting with the Kubernetes API.

    This class wraps the `kubernetes` client library to provide high-level
    functions for managing deployments and other resources within a specified
    namespace.

    Attributes:
        namespace (str): The Kubernetes namespace this controller operates in.
        apps_v1 (client.AppsV1Api): The API client for Apps V1 resources (e.g., Deployments).
        core_v1 (client.CoreV1Api): The API client for Core V1 resources (e.g., Pods).
        autoscaling_v2 (client.AutoscalingV2Api): The API client for HPA resources.
    """

    def __init__(self, namespace: str = "default", in_cluster: bool = True):
        """Initializes the KubernetesController.

        Args:
            namespace (str): The target Kubernetes namespace.
            in_cluster (bool): If True, loads the in-cluster configuration. Otherwise,
                loads the local kubeconfig file.
        """
        self.namespace = namespace
        try:
            config.load_incluster_config() if in_cluster else config.load_kube_config()
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()
            logger.info(f"Kubernetes controller initialized for namespace '{namespace}'.")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def scale_deployment(self, deployment_name: str, target_replicas: int) -> Dict[str, Any]:
        """Scales a deployment to the specified number of replicas.

        Args:
            deployment_name (str): The name of the deployment to scale.
            target_replicas (int): The desired number of replicas.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            body = {"spec": {"replicas": target_replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(deployment_name, self.namespace, body)
            logger.info(f"Successfully scaled deployment '{deployment_name}' to {target_replicas} replicas.")
            return {"status": "success", "deployment": deployment_name, "replicas": target_replicas}
        except ApiException as e:
            logger.error(f"API error scaling deployment {deployment_name}: {e}")
            return {"status": "error", "error": e.reason}

    async def update_resource_limits(self, deployment_name: str, cpu_limit: str, memory_limit: str) -> Dict[str, Any]:
        """Updates the resource limits for a deployment's container(s).

        Args:
            deployment_name (str): The name of the deployment to update.
            cpu_limit (str): The new CPU limit (e.g., "500m").
            memory_limit (str): The new memory limit (e.g., "1Gi").

        Returns:
            Dict[str, Any]: A dictionary containing the result of the operation.
        """
        try:
            body = {"spec": {"template": {"spec": {"containers": [{"name": deployment_name, "resources": {"limits": {"cpu": cpu_limit, "memory": memory_limit}}}]}}}}
            self.apps_v1.patch_namespaced_deployment(deployment_name, self.namespace, body)
            logger.info(f"Updated resource limits for '{deployment_name}'.")
            return {"status": "success", "deployment": deployment_name}
        except ApiException as e:
            logger.error(f"API error updating resources for {deployment_name}: {e}")
            return {"status": "error", "error": e.reason}

    async def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Retrieves the current status of a deployment.

        Args:
            deployment_name (str): The name of the deployment.

        Returns:
            Dict[str, Any]: A dictionary with the deployment's status details.
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment_status(deployment_name, self.namespace)
            return {
                "replicas": deployment.status.replicas,
                "ready_replicas": deployment.status.ready_replicas,
                "available_replicas": deployment.status.available_replicas,
            }
        except ApiException as e:
            logger.error(f"API error getting status for {deployment_name}: {e}")
            return {"error": e.reason}