"""Digital Twin Environment - Ambiente Isolado para Validação de Patches.

Implementa validação segura de patches usando containers Docker isolados.
Cada patch é testado em um "gêmeo digital" antes de ser aplicado em produção.

Fundamento Bíblico: Provérbios 14:15
"O simples crê em tudo, mas o prudente atenta para os seus passos."

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import io
import json
import logging
from pathlib import Path
import tarfile
import time
from typing import Any
from uuid import uuid4

from docker.models.containers import Container
from docker.models.networks import Network

import docker

logger = logging.getLogger(__name__)


class DigitalTwinEnvironment:
    """Docker-based digital twin for safe patch validation.

    Creates isolated copy of target service, applies patch,
    runs tests, monitors for regressions.

    Architecture:
    1. Creates isolated Docker network (no external access)
    2. Launches service container from latest image
    3. Applies patch inside container
    4. Runs test suite
    5. Monitors metrics for N seconds
    6. Destroys twin and cleans up

    Biblical Principle: Test everything, hold fast to what is good (1 Thess 5:21)
    """

    def __init__(self, docker_client: docker.DockerClient | None = None):
        """Initialize Digital Twin Environment.

        Args:
            docker_client: Docker client instance (auto-created if None)
        """
        self.docker = docker_client or docker.from_env()
        self.twins: dict[str, dict[str, Any]] = {}  # twin_id -> {container, network}

    async def create_twin(self, service_name: str) -> str:
        """Create digital twin of service.

        Creates isolated Docker container running the service image.
        Container is on isolated network with no external access.

        Args:
            service_name: Name of service (e.g., "penelope_service")

        Returns:
            twin_id: Unique identifier for this twin

        Raises:
            docker.errors.ImageNotFound: If service image doesn't exist
            docker.errors.APIError: If Docker API fails
        """
        try:
            # Determine service image
            service_image = f"vertice/{service_name}:latest"

            # Check if image exists, if not use generic python base
            try:
                self.docker.images.get(service_image)
            except docker.errors.ImageNotFound:
                logger.warning(
                    f"Image {service_image} not found, using python:3.11-slim"
                )
                service_image = "python:3.11-slim"

            # Create isolated network
            network_name = f"twin_{service_name}_{uuid4().hex[:8]}"
            network = self.docker.networks.create(
                network_name,
                driver="bridge",
                internal=True,  # No external access
                labels={
                    "penelope.digital_twin": "true",
                    "penelope.service": service_name,
                },
            )

            # Create container with service dependencies
            container = self.docker.containers.run(
                service_image,
                name=f"twin_{service_name}_{uuid4().hex[:8]}",
                network=network.name,
                detach=True,
                environment={
                    "ENVIRONMENT": "digital_twin",
                    "PENELOPE_MODE": "validation",
                    "PYTHONUNBUFFERED": "1",
                },
                labels={
                    "penelope.twin": "true",
                    "penelope.service": service_name,
                    "penelope.created_at": str(time.time()),
                },
                # Security constraints
                mem_limit="1g",
                memswap_limit="1g",
                cpu_quota=50000,  # 0.5 CPU
                read_only=False,  # Need write for patch application
                tmpfs={"/tmp": "size=256m,mode=1777"},
            )

            twin_id = container.id[:12]  # Short ID
            self.twins[twin_id] = {
                "container": container,
                "network": network,
                "service": service_name,
                "created_at": time.time(),
            }

            logger.info(f"✅ Created digital twin {twin_id} for {service_name}")
            return twin_id

        except docker.errors.ImageNotFound as e:
            logger.error(f"Service image not found: {e}")
            raise
        except docker.errors.APIError as e:
            logger.error(f"Docker API error creating twin: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create digital twin: {e}")
            raise

    async def apply_patch(self, twin_id: str, patch: str) -> bool:
        """Apply patch to digital twin.

        Copies patch content into container and applies it using git apply.

        Args:
            twin_id: Twin container ID
            patch: Git-style patch content (unified diff format)

        Returns:
            success: True if patch applied cleanly

        Raises:
            KeyError: If twin_id not found
        """
        if twin_id not in self.twins:
            raise KeyError(f"Twin {twin_id} not found")

        container = self.twins[twin_id]["container"]

        try:
            # Create patch file content
            patch_filename = f"penelope_patch_{uuid4().hex[:8]}.patch"

            # Create tar archive with patch file
            tar_stream = self._create_tar_archive({patch_filename: patch.encode()})

            # Copy patch to container /tmp
            container.put_archive("/tmp", tar_stream)

            # First, check if patch can be applied
            exit_code, output = container.exec_run(
                f"git apply --check /tmp/{patch_filename}",
                workdir="/app",
            )

            if exit_code != 0:
                logger.error(
                    f"Patch validation failed: {output.decode(errors='ignore')}"
                )
                return False

            # Apply patch
            exit_code, output = container.exec_run(
                f"git apply /tmp/{patch_filename}",
                workdir="/app",
            )

            if exit_code == 0:
                logger.info(f"✅ Patch applied successfully to twin {twin_id}")
                return True
            else:
                logger.error(
                    f"Patch application failed: {output.decode(errors='ignore')}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to apply patch to twin {twin_id}: {e}")
            return False

    async def run_tests(self, twin_id: str) -> dict[str, Any]:
        """Run test suite in digital twin.

        Executes pytest with coverage inside the container and extracts results.

        Args:
            twin_id: Twin container ID

        Returns:
            test_results: Dict with passed, failed, coverage, exit_code

        Raises:
            KeyError: If twin_id not found
        """
        if twin_id not in self.twins:
            raise KeyError(f"Twin {twin_id} not found")

        container = self.twins[twin_id]["container"]

        try:
            # Run pytest with coverage and JSON report
            exit_code, output = container.exec_run(
                "pytest --cov=. --cov-report=json --json-report "
                "--json-report-file=/tmp/test_report.json -q",
                workdir="/app",
            )

            # Extract test report
            test_report = {}
            try:
                bits, stat = container.get_archive("/tmp/test_report.json")
                test_report_tar = b"".join(bits)
                test_report = self._extract_from_tar(
                    test_report_tar, "test_report.json"
                )
            except Exception as e:
                logger.warning(f"Failed to extract test report: {e}")

            # Extract coverage
            coverage = {}
            try:
                bits, stat = container.get_archive("/tmp/coverage.json")
                coverage_tar = b"".join(bits)
                coverage = self._extract_from_tar(coverage_tar, "coverage.json")
            except Exception as e:
                logger.warning(f"Failed to extract coverage: {e}")

            # Parse results
            result = {
                "tests_passed": test_report.get("summary", {}).get("passed", 0),
                "tests_failed": test_report.get("summary", {}).get("failed", 0),
                "tests_total": test_report.get("summary", {}).get("total", 0),
                "coverage": coverage.get("totals", {}).get("percent_covered", 0.0),
                "exit_code": exit_code,
                "success": exit_code == 0,
            }

            logger.info(
                f"Tests in twin {twin_id}: "
                f"{result['tests_passed']} passed, {result['tests_failed']} failed, "
                f"coverage: {result['coverage']:.1f}%"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to run tests in twin {twin_id}: {e}")
            return {
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_total": 0,
                "coverage": 0.0,
                "exit_code": -1,
                "success": False,
                "error": str(e),
            }

    async def monitor_metrics(
        self, twin_id: str, duration_seconds: int = 60
    ) -> dict[str, Any]:
        """Monitor digital twin metrics for regressions.

        Samples container stats (CPU, memory) over time period.

        Args:
            twin_id: Twin container ID
            duration_seconds: How long to monitor (default: 60s)

        Returns:
            metrics: Dict with cpu_avg, memory_avg, samples

        Raises:
            KeyError: If twin_id not found
        """
        if twin_id not in self.twins:
            raise KeyError(f"Twin {twin_id} not found")

        container = self.twins[twin_id]["container"]

        try:
            metrics = {"cpu_avg": 0.0, "memory_avg": 0.0, "errors": 0, "samples": []}

            samples = []
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                try:
                    stats = container.stats(stream=False)

                    # Calculate CPU percentage
                    cpu_delta = (
                        stats["cpu_stats"]["cpu_usage"]["total_usage"]
                        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                        stats["cpu_stats"]["system_cpu_usage"]
                        - stats["precpu_stats"]["system_cpu_usage"]
                    )

                    cpu_percent = 0.0
                    if system_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * 100.0

                    # Calculate memory usage percentage
                    memory_usage = (
                        stats["memory_stats"]["usage"] / stats["memory_stats"]["limit"]
                    ) * 100.0

                    samples.append(
                        {
                            "cpu": cpu_percent,
                            "memory": memory_usage,
                            "timestamp": time.time(),
                        }
                    )

                except Exception as e:
                    logger.debug(f"Failed to get stats sample: {e}")
                    metrics["errors"] += 1

                await asyncio.sleep(5)  # Sample every 5 seconds

            # Aggregate metrics
            if samples:
                metrics["cpu_avg"] = sum(s["cpu"] for s in samples) / len(samples)
                metrics["memory_avg"] = sum(s["memory"] for s in samples) / len(samples)
                metrics["samples"] = len(samples)

            logger.info(
                f"Monitored twin {twin_id} for {duration_seconds}s: "
                f"CPU avg: {metrics['cpu_avg']:.1f}%, "
                f"Memory avg: {metrics['memory_avg']:.1f}%"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to monitor twin {twin_id}: {e}")
            return {
                "cpu_avg": 0.0,
                "memory_avg": 0.0,
                "errors": 1,
                "samples": 0,
                "error": str(e),
            }

    async def destroy_twin(self, twin_id: str) -> None:
        """Destroy digital twin and clean up resources.

        Stops container, removes it, and removes the isolated network.

        Args:
            twin_id: Twin container ID

        Raises:
            KeyError: If twin_id not found
        """
        if twin_id not in self.twins:
            raise KeyError(f"Twin {twin_id} not found")

        try:
            twin = self.twins[twin_id]
            container = twin["container"]
            network = twin["network"]

            # Stop and remove container
            try:
                container.stop(timeout=10)
                container.remove(force=True)
            except Exception as e:
                logger.warning(f"Error stopping/removing container: {e}")

            # Remove network
            try:
                network.remove()
            except Exception as e:
                logger.warning(f"Error removing network: {e}")

            # Remove from tracking
            del self.twins[twin_id]

            logger.info(f"✅ Destroyed digital twin {twin_id}")

        except Exception as e:
            logger.error(f"Failed to destroy twin {twin_id}: {e}")
            raise

    # Helper methods

    def _create_tar_archive(self, files: dict[str, bytes]) -> bytes:
        """Create tar archive from files dict.

        Args:
            files: Dict of {filename: content_bytes}

        Returns:
            tar_bytes: Tar archive as bytes
        """
        tar_stream = io.BytesIO()
        tar = tarfile.open(fileobj=tar_stream, mode="w")

        for filename, content in files.items():
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(content)
            tarinfo.mode = 0o644
            tar.addfile(tarinfo, io.BytesIO(content))

        tar.close()
        tar_stream.seek(0)
        return tar_stream.read()

    def _extract_from_tar(self, tar_bytes: bytes, filename: str) -> dict[str, Any]:
        """Extract JSON file from tar archive.

        Args:
            tar_bytes: Tar archive as bytes
            filename: Name of file to extract

        Returns:
            parsed_json: Parsed JSON content

        Raises:
            KeyError: If file not found in archive
            json.JSONDecodeError: If file is not valid JSON
        """
        tar_stream = io.BytesIO(tar_bytes)
        tar = tarfile.open(fileobj=tar_stream, mode="r")

        try:
            member = tar.getmember(filename)
            file_content = tar.extractfile(member).read()
            return json.loads(file_content)
        finally:
            tar.close()
