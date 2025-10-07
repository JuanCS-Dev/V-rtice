"""Docker Actuator - Container Management via Docker SDK"""

import logging
from typing import Any, Dict, List, Optional

import docker
from docker.errors import APIError, DockerException

logger = logging.getLogger(__name__)


class DockerActuator:
    """Execute container lifecycle operations via Docker SDK."""

    def __init__(self, dry_run_mode: bool = True):
        self.dry_run_mode = dry_run_mode
        self.action_log = []

        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client connected successfully")
        except DockerException as e:
            logger.error(f"Docker connection failed: {e}")
            self.client = None

    def scale_service(self, service_name: str, replicas: int) -> Dict:
        """Scale Docker Swarm service or compose service."""
        if not self.client:
            return {"success": False, "error": "Docker client unavailable"}

        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Scale {service_name} to {replicas} replicas")
            self.action_log.append(
                {
                    "action": "scale_service",
                    "service": service_name,
                    "replicas": replicas,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            # Try Docker Swarm first
            service = self.client.services.get(service_name)
            service.scale(replicas)

            self.action_log.append(
                {
                    "action": "scale_service",
                    "service": service_name,
                    "replicas": replicas,
                    "executed": True,
                    "success": True,
                }
            )

            return {
                "success": True,
                "service": service_name,
                "replicas": replicas,
                "mode": "swarm",
            }

        except APIError as e:
            if "service" in str(e).lower() and "not found" in str(e).lower():
                # Fallback to compose (restart with env var for scaling)
                logger.warning(
                    f"Service {service_name} not in Swarm, attempting compose scaling"
                )
                return self._scale_compose_service(service_name, replicas)

            logger.error(f"Docker scale error: {e}")
            return {"success": False, "error": str(e)}

    def _scale_compose_service(self, service_name: str, replicas: int) -> Dict:
        """Scale Docker Compose service by container count."""
        try:
            containers = self.client.containers.list(
                filters={"label": f"com.docker.compose.service={service_name}"}
            )

            current_count = len(containers)

            if current_count == replicas:
                return {
                    "success": True,
                    "replicas": replicas,
                    "mode": "compose",
                    "action": "no-op",
                }

            if current_count < replicas:
                # Scale up: create new containers
                base_container = containers[0] if containers else None
                if not base_container:
                    return {"success": False, "error": "No base container found"}

                for i in range(replicas - current_count):
                    self.client.containers.run(
                        base_container.image.tags[0],
                        detach=True,
                        labels=base_container.labels,
                        environment=base_container.attrs["Config"]["Env"],
                    )
            else:
                # Scale down: remove excess containers
                for container in containers[replicas:]:
                    container.stop(timeout=10)
                    container.remove()

            return {
                "success": True,
                "service": service_name,
                "replicas": replicas,
                "mode": "compose",
            }

        except Exception as e:
            logger.error(f"Compose scaling error: {e}")
            return {"success": False, "error": str(e)}

    def update_resource_limits(
        self,
        container_name: str,
        cpu_limit: Optional[float] = None,
        memory_limit: Optional[str] = None,
    ) -> Dict:
        """Update container resource limits (CPU cores, memory)."""
        if not self.client:
            return {"success": False, "error": "Docker client unavailable"}

        if self.dry_run_mode:
            logger.info(
                f"DRY-RUN: Update {container_name} limits - CPU: {cpu_limit}, Memory: {memory_limit}"
            )
            self.action_log.append(
                {
                    "action": "update_limits",
                    "container": container_name,
                    "cpu_limit": cpu_limit,
                    "memory_limit": memory_limit,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            container = self.client.containers.get(container_name)

            # Convert CPU limit (cores) to nano CPUs (1 core = 1e9 nano CPUs)
            nano_cpus = int(cpu_limit * 1e9) if cpu_limit else None

            # Parse memory limit (e.g., "512m" -> bytes)
            mem_bytes = self._parse_memory(memory_limit) if memory_limit else None

            update_config = {}
            if nano_cpus:
                update_config["nano_cpus"] = nano_cpus
            if mem_bytes:
                update_config["mem_limit"] = mem_bytes

            container.update(**update_config)

            self.action_log.append(
                {
                    "action": "update_limits",
                    "container": container_name,
                    "cpu_limit": cpu_limit,
                    "memory_limit": memory_limit,
                    "executed": True,
                    "success": True,
                }
            )

            return {
                "success": True,
                "container": container_name,
                "cpu_limit": cpu_limit,
                "memory_limit": memory_limit,
            }

        except Exception as e:
            logger.error(f"Resource limit update error: {e}")
            return {"success": False, "error": str(e)}

    def restart_container(self, container_name: str, timeout: int = 10) -> Dict:
        """Gracefully restart container."""
        if not self.client:
            return {"success": False, "error": "Docker client unavailable"}

        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Restart {container_name}")
            self.action_log.append(
                {
                    "action": "restart",
                    "container": container_name,
                    "executed": False,
                    "dry_run": True,
                }
            )
            return {"success": True, "dry_run": True}

        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=timeout)

            self.action_log.append(
                {
                    "action": "restart",
                    "container": container_name,
                    "executed": True,
                    "success": True,
                }
            )

            return {
                "success": True,
                "container": container_name,
                "status": container.status,
            }

        except Exception as e:
            logger.error(f"Container restart error: {e}")
            return {"success": False, "error": str(e)}

    def get_container_stats(self, container_name: str) -> Dict:
        """Get real-time container statistics."""
        if not self.client:
            return {"success": False, "error": "Docker client unavailable"}

        try:
            container = self.client.containers.get(container_name)
            stats = container.stats(stream=False)

            # Parse CPU usage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            )

            # Parse memory usage
            mem_usage = stats["memory_stats"]["usage"]
            mem_limit = stats["memory_stats"]["limit"]
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0

            return {
                "success": True,
                "container": container_name,
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(mem_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(mem_limit / (1024 * 1024), 2),
                "memory_percent": round(mem_percent, 2),
                "network_rx_bytes": (
                    stats["networks"]["eth0"]["rx_bytes"]
                    if "eth0" in stats.get("networks", {})
                    else 0
                ),
                "network_tx_bytes": (
                    stats["networks"]["eth0"]["tx_bytes"]
                    if "eth0" in stats.get("networks", {})
                    else 0
                ),
            }

        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {"success": False, "error": str(e)}

    def _parse_memory(self, mem_str: str) -> int:
        """Parse memory string (e.g., '512m', '2g') to bytes."""
        units = {"k": 1024, "m": 1024**2, "g": 1024**3}

        mem_str = mem_str.lower().strip()
        if mem_str[-1] in units:
            return int(float(mem_str[:-1]) * units[mem_str[-1]])
        return int(mem_str)  # Assume bytes if no unit

    def get_action_log(self) -> List[Dict]:
        """Return action history for audit."""
        return self.action_log
