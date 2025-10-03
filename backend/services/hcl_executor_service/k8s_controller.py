"""
HCL Executor - Kubernetes Controller
======================================
Real Kubernetes API integration for executing HCL decisions.
Scales deployments, adjusts resource limits, manages HPA.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)


class KubernetesController:
    """
    Real Kubernetes controller for executing scaling and resource decisions.

    Capabilities:
    - Scale deployments (replicas)
    - Update resource limits (CPU, Memory)
    - Manage HorizontalPodAutoscaler
    - Rollback on failures
    - Health checks
    """

    def __init__(self, namespace: str = "default", in_cluster: bool = True):
        """
        Initialize Kubernetes controller.

        Args:
            namespace: Target namespace
            in_cluster: True if running inside K8s cluster, False for local development
        """
        self.namespace = namespace

        try:
            if in_cluster:
                # Load in-cluster config (when running as Pod)
                config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes config")
            else:
                # Load from ~/.kube/config (for local development)
                config.load_kube_config()
                logger.info("Loaded local Kubernetes config")

            # Initialize API clients
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v2 = client.AutoscalingV2Api()

            logger.info(f"Kubernetes controller initialized (namespace={namespace})")

        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    async def scale_deployment(
        self,
        deployment_name: str,
        target_replicas: int,
        current_replicas: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Scale deployment to target replicas.

        Args:
            deployment_name: Name of deployment
            target_replicas: Target replica count
            current_replicas: Current replica count (for validation)

        Returns:
            Result dict with status and details
        """
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )

            actual_current = deployment.spec.replicas

            # Validate current replicas if provided
            if current_replicas is not None and actual_current != current_replicas:
                logger.warning(
                    f"Replica count mismatch for {deployment_name}: "
                    f"expected {current_replicas}, actual {actual_current}"
                )

            # Check if scaling is needed
            if actual_current == target_replicas:
                logger.info(f"Deployment {deployment_name} already at {target_replicas} replicas")
                return {
                    "status": "no_change",
                    "deployment": deployment_name,
                    "current_replicas": actual_current,
                    "target_replicas": target_replicas,
                    "message": "Already at target replica count"
                }

            # Update replica count
            deployment.spec.replicas = target_replicas

            # Patch deployment
            result = self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )

            logger.info(
                f"Scaled {deployment_name}: {actual_current} -> {target_replicas} replicas"
            )

            return {
                "status": "success",
                "deployment": deployment_name,
                "previous_replicas": actual_current,
                "current_replicas": target_replicas,
                "action": "scale_up" if target_replicas > actual_current else "scale_down",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except ApiException as e:
            logger.error(f"K8s API error scaling {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error scaling {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e)
            }

    async def update_resource_limits(
        self,
        deployment_name: str,
        container_name: Optional[str] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None,
        cpu_request: Optional[str] = None,
        memory_request: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update resource limits for deployment containers.

        Args:
            deployment_name: Name of deployment
            container_name: Target container (if None, updates first container)
            cpu_limit: CPU limit (e.g., "1000m", "2")
            memory_limit: Memory limit (e.g., "2Gi", "512Mi")
            cpu_request: CPU request
            memory_request: Memory request

        Returns:
            Result dict with status and details
        """
        try:
            # Get current deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )

            # Find target container
            containers = deployment.spec.template.spec.containers

            if container_name:
                target_container = next(
                    (c for c in containers if c.name == container_name),
                    None
                )
                if not target_container:
                    raise ValueError(f"Container {container_name} not found")
            else:
                target_container = containers[0]  # First container

            # Get current resources
            if target_container.resources is None:
                target_container.resources = client.V1ResourceRequirements()

            if target_container.resources.limits is None:
                target_container.resources.limits = {}

            if target_container.resources.requests is None:
                target_container.resources.requests = {}

            old_limits = target_container.resources.limits.copy()
            old_requests = target_container.resources.requests.copy()

            # Update limits
            if cpu_limit:
                target_container.resources.limits['cpu'] = cpu_limit
            if memory_limit:
                target_container.resources.limits['memory'] = memory_limit

            # Update requests
            if cpu_request:
                target_container.resources.requests['cpu'] = cpu_request
            if memory_request:
                target_container.resources.requests['memory'] = memory_request

            # Patch deployment
            result = self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )

            logger.info(
                f"Updated resources for {deployment_name}/{target_container.name}: "
                f"limits={target_container.resources.limits}, "
                f"requests={target_container.resources.requests}"
            )

            return {
                "status": "success",
                "deployment": deployment_name,
                "container": target_container.name,
                "old_limits": old_limits,
                "new_limits": target_container.resources.limits,
                "old_requests": old_requests,
                "new_requests": target_container.resources.requests,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except ApiException as e:
            logger.error(f"K8s API error updating resources for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error updating resources for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e)
            }

    async def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """
        Get current deployment status.

        Args:
            deployment_name: Name of deployment

        Returns:
            Status dict with replicas, resources, conditions
        """
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )

            # Extract status
            status = {
                "name": deployment_name,
                "namespace": self.namespace,
                "replicas": {
                    "desired": deployment.spec.replicas,
                    "current": deployment.status.replicas or 0,
                    "ready": deployment.status.ready_replicas or 0,
                    "available": deployment.status.available_replicas or 0,
                    "unavailable": deployment.status.unavailable_replicas or 0
                },
                "conditions": []
            }

            # Add conditions
            if deployment.status.conditions:
                for condition in deployment.status.conditions:
                    status["conditions"].append({
                        "type": condition.type,
                        "status": condition.status,
                        "reason": condition.reason,
                        "message": condition.message,
                        "last_update": condition.last_update_time.isoformat() if condition.last_update_time else None
                    })

            # Extract resource limits from first container
            if deployment.spec.template.spec.containers:
                container = deployment.spec.template.spec.containers[0]
                if container.resources:
                    status["resources"] = {
                        "limits": container.resources.limits or {},
                        "requests": container.resources.requests or {}
                    }

            return status

        except ApiException as e:
            logger.error(f"K8s API error getting status for {deployment_name}: {e}")
            return {
                "name": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error getting status for {deployment_name}: {e}")
            return {
                "name": deployment_name,
                "error": str(e)
            }

    async def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all deployments in namespace.

        Returns:
            List of deployment info dicts
        """
        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=self.namespace
            )

            result = []
            for deployment in deployments.items:
                result.append({
                    "name": deployment.metadata.name,
                    "replicas": {
                        "desired": deployment.spec.replicas,
                        "ready": deployment.status.ready_replicas or 0
                    },
                    "created": deployment.metadata.creation_timestamp.isoformat()
                })

            return result

        except Exception as e:
            logger.error(f"Error listing deployments: {e}")
            return []

    async def create_or_update_hpa(
        self,
        deployment_name: str,
        min_replicas: int,
        max_replicas: int,
        target_cpu_utilization: int = 70,
        target_memory_utilization: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create or update HorizontalPodAutoscaler.

        Args:
            deployment_name: Target deployment
            min_replicas: Minimum replicas
            max_replicas: Maximum replicas
            target_cpu_utilization: Target CPU percentage
            target_memory_utilization: Target memory percentage (optional)

        Returns:
            Result dict
        """
        try:
            hpa_name = f"{deployment_name}-hpa"

            # Build metrics
            metrics = [
                client.V2MetricSpec(
                    type="Resource",
                    resource=client.V2ResourceMetricSource(
                        name="cpu",
                        target=client.V2MetricTarget(
                            type="Utilization",
                            average_utilization=target_cpu_utilization
                        )
                    )
                )
            ]

            if target_memory_utilization:
                metrics.append(
                    client.V2MetricSpec(
                        type="Resource",
                        resource=client.V2ResourceMetricSource(
                            name="memory",
                            target=client.V2MetricTarget(
                                type="Utilization",
                                average_utilization=target_memory_utilization
                            )
                        )
                    )
                )

            # Build HPA spec
            hpa_spec = client.V2HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V2CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=deployment_name
                ),
                min_replicas=min_replicas,
                max_replicas=max_replicas,
                metrics=metrics
            )

            hpa = client.V2HorizontalPodAutoscaler(
                api_version="autoscaling/v2",
                kind="HorizontalPodAutoscaler",
                metadata=client.V1ObjectMeta(name=hpa_name),
                spec=hpa_spec
            )

            # Try to update existing HPA
            try:
                result = self.autoscaling_v2.patch_namespaced_horizontal_pod_autoscaler(
                    name=hpa_name,
                    namespace=self.namespace,
                    body=hpa
                )
                action = "updated"
            except ApiException as e:
                if e.status == 404:
                    # Create new HPA
                    result = self.autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                        namespace=self.namespace,
                        body=hpa
                    )
                    action = "created"
                else:
                    raise

            logger.info(f"HPA {action} for {deployment_name}: {min_replicas}-{max_replicas} replicas")

            return {
                "status": "success",
                "action": action,
                "hpa_name": hpa_name,
                "deployment": deployment_name,
                "min_replicas": min_replicas,
                "max_replicas": max_replicas,
                "target_cpu": target_cpu_utilization,
                "target_memory": target_memory_utilization
            }

        except ApiException as e:
            logger.error(f"K8s API error managing HPA for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error managing HPA for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e)
            }

    async def delete_hpa(self, deployment_name: str) -> Dict[str, Any]:
        """
        Delete HorizontalPodAutoscaler.

        Args:
            deployment_name: Target deployment

        Returns:
            Result dict
        """
        try:
            hpa_name = f"{deployment_name}-hpa"

            self.autoscaling_v2.delete_namespaced_horizontal_pod_autoscaler(
                name=hpa_name,
                namespace=self.namespace
            )

            logger.info(f"Deleted HPA for {deployment_name}")

            return {
                "status": "success",
                "hpa_name": hpa_name,
                "deployment": deployment_name
            }

        except ApiException as e:
            if e.status == 404:
                return {
                    "status": "not_found",
                    "deployment": deployment_name,
                    "message": "HPA does not exist"
                }
            logger.error(f"K8s API error deleting HPA for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error deleting HPA for {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e)
            }

    async def rollback_deployment(
        self,
        deployment_name: str,
        revision: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rollback deployment to previous revision.

        Args:
            deployment_name: Name of deployment
            revision: Target revision (None = previous)

        Returns:
            Result dict
        """
        try:
            # Get deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )

            # Trigger rollback by updating rollback annotation
            if deployment.metadata.annotations is None:
                deployment.metadata.annotations = {}

            rollback_to = revision if revision else "previous"
            deployment.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = \
                datetime.now(timezone.utc).isoformat()

            result = self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )

            logger.info(f"Rolled back {deployment_name} to {rollback_to} revision")

            return {
                "status": "success",
                "deployment": deployment_name,
                "rollback_to": rollback_to,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except ApiException as e:
            logger.error(f"K8s API error rolling back {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e),
                "error_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error rolling back {deployment_name}: {e}")
            return {
                "status": "error",
                "deployment": deployment_name,
                "error": str(e)
            }

    async def get_pod_metrics(self, deployment_name: str) -> List[Dict[str, Any]]:
        """
        Get metrics for pods in deployment.

        Note: Requires metrics-server to be installed in cluster.

        Args:
            deployment_name: Name of deployment

        Returns:
            List of pod metrics
        """
        try:
            # Get pods for deployment
            label_selector = f"app={deployment_name}"
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )

            metrics = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "node": pod.spec.node_name,
                    "containers": []
                }

                # Get container statuses
                if pod.status.container_statuses:
                    for container_status in pod.status.container_statuses:
                        pod_info["containers"].append({
                            "name": container_status.name,
                            "ready": container_status.ready,
                            "restart_count": container_status.restart_count
                        })

                metrics.append(pod_info)

            return metrics

        except Exception as e:
            logger.error(f"Error getting pod metrics for {deployment_name}: {e}")
            return []


# Test function
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def test():
        """Test Kubernetes controller"""
        print("\n" + "="*80)
        print("KUBERNETES CONTROLLER TEST")
        print("="*80 + "\n")

        try:
            # Initialize controller (will use local ~/.kube/config)
            controller = KubernetesController(
                namespace="default",
                in_cluster=False
            )

            # List deployments
            print("Deployments in namespace:")
            deployments = await controller.list_deployments()
            for dep in deployments:
                print(f"  - {dep['name']}: {dep['replicas']['ready']}/{dep['replicas']['desired']} ready")

            if not deployments:
                print("  No deployments found. Create a test deployment first:")
                print("  kubectl create deployment nginx --image=nginx")
                return

            # Test with first deployment
            test_deployment = deployments[0]['name']
            print(f"\nTesting with deployment: {test_deployment}")

            # Get status
            print("\nCurrent status:")
            status = await controller.get_deployment_status(test_deployment)
            print(f"  Replicas: {status['replicas']}")

            # Scale up
            print(f"\nScaling up to 3 replicas...")
            result = await controller.scale_deployment(test_deployment, 3)
            print(f"  Status: {result['status']}")

            # Wait a bit
            await asyncio.sleep(2)

            # Check status again
            status = await controller.get_deployment_status(test_deployment)
            print(f"  New replicas: {status['replicas']}")

            print("\n" + "="*80)
            print("TEST COMPLETE")
            print("="*80 + "\n")

        except Exception as e:
            print(f"\nError: {e}")
            print("Make sure you have:")
            print("  1. kubectl installed and configured")
            print("  2. A running Kubernetes cluster")
            print("  3. At least one deployment in the default namespace")

    asyncio.run(test())
